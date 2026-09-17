import pytest
from datetime import datetime, timedelta, date

# ==========================================
# 1. TESTES DE AUTENTICAÇÃO
# ==========================================
def test_cadastro_gestante_cria_conta_e_retorna_token(client):
    res = client.post("/auth/gestante/cadastro", json={
        "nome": "Maria Silva",
        "email": "maria@teste.com",
        "senha": "senhaSegura123"
    })
    assert res.status_code == 201
    data = res.json()
    assert "token" in data
    assert data["perfil"] == "gestante"
    assert data["nome"] == "Maria Silva"

def test_login_com_senha_errada_retorna_401(client):
    client.post("/auth/gestante/cadastro", json={
        "nome": "Carla Dias",
        "email": "carla@teste.com",
        "senha": "senhaCorreta123"
    })
    res = client.post("/auth/gestante/login", json={
        "email": "carla@teste.com",
        "senha": "senhaErrada999"
    })
    assert res.status_code == 401

def test_cadastro_com_email_repetido_retorna_409(client):
    client.post("/auth/gestante/cadastro", json={
        "nome": "Ana Lima",
        "email": "ana@teste.com",
        "senha": "senhaSegura123"
    })
    res = client.post("/auth/gestante/cadastro", json={
        "nome": "Ana Lima 2",
        "email": "ana@teste.com",
        "senha": "outraSenha456"
    })
    assert res.status_code == 409

def test_conta_profissional_nao_acessa_rota_gestante(client):
    res_prof = client.post("/auth/profissional/cadastro", json={
        "nome": "Dr. Lucas",
        "email": "lucas@med.com",
        "senha": "senhaMed123",
        "registro_tipo": "CRM",
        "registro_numero": "123456",
        "registro_uf": "SP"
    })
    token_prof = res_prof.json()["token"]

    # Tentativa de acessar rota exclusiva de gestante com token de profissional
    res_rota = client.get("/perfil-clinico", headers={"Authorization": f"Bearer {token_prof}"})
    assert res_rota.status_code == 403

# ==========================================
# 2. TESTES DE ONBOARDING CLÍNICO
# ==========================================
def test_onboarding_dum_dpp_e_historico_familiar(client):
    reg = client.post("/auth/gestante/cadastro", json={
        "nome": "Juliana Santos",
        "email": "juliana@teste.com",
        "senha": "senhaSegura123"
    })
    token = reg.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Cria perfil clínico com DUM e DPP calculada
    res_perfil = client.post("/perfil-clinico", json={
        "idade": 28,
        "dum": "2026-01-01",
        "dpp": "2026-10-08",
        "dpp_editada_manualmente": False,
        "maternidade_nome": "Hospital e Maternidade São Paulo",
        "maternidade_telefone": "11988887777"
    }, headers=headers)
    assert res_perfil.status_code == 201
    perfil_data = res_perfil.json()
    assert perfil_data["dum"] == "2026-01-01"
    assert perfil_data["dpp"] == "2026-10-08"

    # 2. Edição manual de DPP preservada
    res_edit = client.put("/perfil-clinico", json={
        "dpp": "2026-10-15",
        "dpp_editada_manualmente": True
    }, headers=headers)
    assert res_edit.status_code == 200
    assert res_edit.json()["dpp"] == "2026-10-15"
    assert res_edit.json()["dpp_editada_manualmente"] is True

    # 3. Histórico familiar dinâmico (múltiplas entradas)
    res_h1 = client.post("/historico-familiar", json={
        "parente": "mãe",
        "condicao": "hipertensão"
    }, headers=headers)
    assert res_h1.status_code == 201
    id1 = res_h1.json()["id"]

    res_h2 = client.post("/historico-familiar", json={
        "parente": "avó materna",
        "condicao": "diabetes"
    }, headers=headers)
    assert res_h2.status_code == 201
    id2 = res_h2.json()["id"]

    # Listar histórico
    res_list = client.get("/historico-familiar", headers=headers)
    assert len(res_list.json()) == 2

    # Remover apenas uma entrada
    res_del = client.delete(f"/historico-familiar/{id1}", headers=headers)
    assert res_del.status_code == 204

    # Verificar que restou apenas a segunda entrada
    res_list_after = client.get("/historico-familiar", headers=headers)
    assert len(res_list_after.json()) == 1
    assert res_list_after.json()[0]["id"] == id2

# ==========================================
# 3. TESTES DE CHECK-IN E IA
# ==========================================
def test_checkin_timestamp_servidor_e_alerta_urgencia(client):
    reg = client.post("/auth/gestante/cadastro", json={
        "nome": "Patricia Oliveira",
        "email": "patricia@teste.com",
        "senha": "senhaSegura123"
    })
    token = reg.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Check-in normal
    res1 = client.post("/checkin/registrar", json={
        "humor": 4,
        "descricao": "Hoje me sinto muito bem e disposta.",
        "sintomas": [],
        "movimentos_bebe": 8
    }, headers=headers)
    assert res1.status_code == 201
    c1 = res1.json()
    assert "data_hora" in c1
    assert len(c1["alerta_sintoma_fisico"]) == 0

    # Check-in com sintoma de urgência física (sangramento genital ativo)
    res2 = client.post("/checkin/registrar", json={
        "humor": 1,
        "descricao": "Notei um sangramento vermelho vivo agora de manhã com dor forte.",
        "sintomas": ["sangramento", "dor de cabeca forte"],
        "movimentos_bebe": 1
    }, headers=headers)
    assert res2.status_code == 201
    c2 = res2.json()
    assert len(c2["alerta_sintoma_fisico"]) > 0
    assert "ALERTA CLÍNICO DE URGÊNCIA" in c2["recomendacao"]
    assert "192" in c2["recomendacao"]

    # Ordenação do histórico: mais recente para o mais antigo
    res_hist = client.get("/checkin/historico", headers=headers)
    assert res_hist.status_code == 200
    hist = res_hist.json()
    assert len(hist) == 2
    # hist[0] deve ser o mais recente (c2)
    assert hist[0]["id"] == c2["id"]
    assert hist[1]["id"] == c1["id"]

def test_isolamento_checkin_entre_gestantes(client):
    regA = client.post("/auth/gestante/cadastro", json={
        "nome": "Gestante A",
        "email": "gestanteA@teste.com",
        "senha": "senhaSegura123"
    })
    tokenA = regA.json()["token"]

    regB = client.post("/auth/gestante/cadastro", json={
        "nome": "Gestante B",
        "email": "gestanteB@teste.com",
        "senha": "senhaSegura123"
    })
    tokenB = regB.json()["token"]

    # A faz checkin
    client.post("/checkin/registrar", json={"humor": 5, "descricao": "Tudo otimo", "sintomas": []}, headers={"Authorization": f"Bearer {tokenA}"})

    # B busca histórico
    resB = client.get("/checkin/historico", headers={"Authorization": f"Bearer {tokenB}"})
    assert len(resB.json()) == 0

# ==========================================
# 4. TESTES DE CONVERSA COM A IA
# ==========================================
def test_conversa_urgencia_imediata_e_persistencia(client):
    reg = client.post("/auth/gestante/cadastro", json={
        "nome": "Fernanda Costa",
        "email": "fernanda@teste.com",
        "senha": "senhaSegura123"
    })
    token = reg.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Mensagem de urgência física responde imediatamente com fonte regras_urgencia
    res_urgente = client.post("/conversa/enviar", json={
        "texto": "Estou com sangramento e dor de cabeca insuportavel com pontos brilhantes"
    }, headers=headers)
    assert res_urgente.status_code == 200
    data_urg = res_urgente.json()
    assert data_urg["alerta_emergencia"] is True
    assert data_urg["fonte"] == "regras_urgencia"
    assert "192" in data_urg["resposta"]

    # 2. Pergunta clínica de rotina (toxoplasmose)
    res_toxo = client.post("/conversa/enviar", json={
        "texto": "Tenho dúvidas sobre como prevenir toxoplasmose e os gatos"
    }, headers=headers)
    assert res_toxo.status_code == 200
    assert "TOXOPLASMOSE GESTACIONAL" in res_toxo.json()["resposta"]

    # 3. Histórico persiste
    res_hist = client.get("/conversa/historico", headers=headers)
    assert len(res_hist.json()) == 4  # 2 do usuário + 2 da IA

# ==========================================
# 5. TESTES DE AGENDA
# ==========================================
def test_agenda_filtro_futuros_e_conclusao(client):
    reg = client.post("/auth/gestante/cadastro", json={
        "nome": "Bianca Rangel",
        "email": "bianca@teste.com",
        "senha": "senhaSegura123"
    })
    token = reg.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Evento no passado
    passado = (datetime.utcnow() - timedelta(days=2)).isoformat()
    client.post("/agenda/eventos", json={
        "tipo": "consulta",
        "titulo": "Consulta Mês Passado",
        "data_hora": passado
    }, headers=headers)

    # Evento no futuro
    futuro = (datetime.utcnow() + timedelta(days=5)).isoformat()
    res_fut = client.post("/agenda/eventos", json={
        "tipo": "exame",
        "titulo": "Ultrassom Morfológico",
        "data_hora": futuro
    }, headers=headers)
    id_futuro = res_fut.json()["id"]

    # 1. Listagem padrão (apenas futuros)
    res_padrao = client.get("/agenda/eventos", headers=headers)
    assert len(res_padrao.json()) == 1
    assert res_padrao.json()[0]["titulo"] == "Ultrassom Morfológico"

    # 2. Listagem com filtro desligado (mostra todos)
    res_todos = client.get("/agenda/eventos?apenas_futuros=false", headers=headers)
    assert len(res_todos.json()) == 2

    # 3. Concluir evento
    res_conc = client.patch(f"/agenda/eventos/{id_futuro}/concluir", headers=headers)
    assert res_conc.status_code == 200
    assert res_conc.json()["concluido"] is True

    # 4. Concluir evento inexistente retorna 404 (nunca 500)
    res_err = client.patch("/agenda/eventos/99999/concluir", headers=headers)
    assert res_err.status_code == 404

# ==========================================
# 6. TESTES DE VÍNCULO E PAINEL DO MÉDICO
# ==========================================
def test_vinculo_codigo_e_ordenacao_painel_urgencia(client):
    # Cadastra profissional
    res_prof = client.post("/auth/profissional/cadastro", json={
        "nome": "Dra. Helena",
        "email": "helena@med.com",
        "senha": "senhaMed123",
        "registro_tipo": "CRM",
        "registro_numero": "654321",
        "registro_uf": "RJ"
    })
    token_prof = res_prof.json()["token"]
    headers_prof = {"Authorization": f"Bearer {token_prof}"}

    # 1. Profissional gera código de convite (NÃO cria vínculo ainda)
    res_cod = client.post("/vinculo/convite/gerar", headers=headers_prof)
    assert res_cod.status_code == 200
    codigo = res_cod.json()["codigo"]
    assert len(codigo) == 8

    # Verifica que painel ainda está vazio
    res_painel_vazio = client.get("/vinculo/minhas-gestantes", headers=headers_prof)
    assert len(res_painel_vazio.json()) == 0

    # 2. Cadastra Gestante 1 e Gestante 2
    regG1 = client.post("/auth/gestante/cadastro", json={
        "nome": "Zilda Alertas",
        "email": "zilda@teste.com",
        "senha": "senhaSegura123"
    })
    tokenG1 = regG1.json()["token"]
    headersG1 = {"Authorization": f"Bearer {tokenG1}"}

    regG2 = client.post("/auth/gestante/cadastro", json={
        "nome": "Alice SemCheckin",
        "email": "alice@teste.com",
        "senha": "senhaSegura123"
    })
    tokenG2 = regG2.json()["token"]
    headersG2 = {"Authorization": f"Bearer {tokenG2}"}

    # G1 usa o código gerado
    res_uso = client.post("/vinculo/convite/usar", json={"codigo": codigo}, headers=headersG1)
    assert res_uso.status_code == 201
    vinculo_id = res_uso.json()["id"]

    # Código já usado é rejeitado (409)
    res_reuso = client.post("/vinculo/convite/usar", json={"codigo": codigo}, headers=headersG2)
    assert res_reuso.status_code == 409

    # Gera segundo código para G2
    res_cod2 = client.post("/vinculo/convite/gerar", headers=headers_prof)
    codigo2 = res_cod2.json()["codigo"]
    client.post("/vinculo/convite/usar", json={"codigo": codigo2}, headers=headersG2)

    # G1 registra checkin com sintoma de urgência (recebe alerta)
    client.post("/checkin/registrar", json={
        "humor": 1,
        "descricao": "Muita dor de cabeca e sangramento",
        "sintomas": ["sangramento"]
    }, headers=headersG1)

    # G2 NUNCA fez checkin

    # 3. Painel do Médico: Ordenado por prioridade de URGÊNCIA
    # Zilda (com alertas) DEVE VIR ANTES de Alice (sem alertas e sem checkin)
    res_painel = client.get("/vinculo/minhas-gestantes", headers=headers_prof)
    assert res_painel.status_code == 200
    pacientes = res_painel.json()
    assert len(pacientes) == 2
    assert pacientes[0]["nome"] == "Zilda Alertas"
    assert pacientes[0]["total_alertas_30d"] > 0
    assert pacientes[1]["nome"] == "Alice SemCheckin"
    assert pacientes[1]["ultimo_checkin_relativo"] == "nunca realizou"

    # 4. Revogação de vínculo pela gestante
    res_revogar = client.post(f"/vinculo/{vinculo_id}/revogar", headers=headersG1)
    assert res_revogar.status_code == 200

    # Após revogação, profissional NÃO vê mais Zilda
    res_painel_pos = client.get("/vinculo/minhas-gestantes", headers=headers_prof)
    nomes_restantes = [p["nome"] for p in res_painel_pos.json()]
    assert "Zilda Alertas" not in nomes_restantes

# ==========================================
# 7. TESTES DE EMERGÊNCIA
# ==========================================
def test_emergencia_notificar_responde_com_samu(client):
    # Acessível com ou sem login
    res = client.post("/emergencia/notificar", json={
        "latitude": -23.5505,
        "longitude": -46.6333
    })
    assert res.status_code == 200
    data = res.json()
    assert "192" in data["orientacao_samu"]

# ==========================================
# 8. TESTES DE CONFORMIDADE LGPD
# ==========================================
def test_conformidade_lgpd_exportacao_e_exclusao(client):
    reg = client.post("/auth/gestante/cadastro", json={
        "nome": "Camila LGPD",
        "email": "camila@teste.com",
        "senha": "senhaSegura123"
    })
    token = reg.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Exportação JSON
    res_json = client.get("/meus-dados/exportar?formato=json", headers=headers)
    assert res_json.status_code == 200
    assert res_json.json()["titular"]["email"] == "camila@teste.com"

    # 2. Exportação PDF
    res_pdf = client.get("/meus-dados/exportar?formato=pdf", headers=headers)
    assert res_pdf.status_code == 200
    assert res_pdf.headers["content-type"] == "application/pdf"
    assert len(res_pdf.content) > 1000

    # 3. Consentimento de IA e direito de recusa (CFM 2.454/2026)
    res_ia = client.put("/meus-dados/consentimento-ia?recusa_ia=true", headers=headers)
    assert res_ia.status_code == 200
    assert res_ia.json()["recusa_ia"] is True

    # 4. Exclusão de conta
    res_del = client.delete("/minha-conta", headers=headers)
    assert res_del.status_code == 200

    # Login subsequente retorna 401
    res_login = client.post("/auth/gestante/login", json={
        "email": "camila@teste.com",
        "senha": "senhaSegura123"
    })
    assert res_login.status_code == 401
