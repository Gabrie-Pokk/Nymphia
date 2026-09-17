import pytest
from datetime import date, timedelta

def test_nome_com_numeros_rejeitado(client):
    # Gestante
    res = client.post("/auth/gestante/cadastro", json={
        "nome": "Maria123",
        "email": "maria123@teste.com",
        "senha": "senhaSegura123"
    })
    assert res.status_code == 422
    assert "nome" in res.text.lower()

    # Profissional
    res_prof = client.post("/auth/profissional/cadastro", json={
        "nome": "Dr. Lucas 2",
        "email": "lucas2@med.com",
        "senha": "senhaMed123",
        "registro_tipo": "CRM",
        "registro_numero": "12345",
        "registro_uf": "SP"
    })
    assert res_prof.status_code == 422

    # Parceiro
    res_parc = client.post("/auth/parceiro/cadastro", json={
        "nome": "Carlos 99",
        "email": "carlos99@teste.com",
        "senha": "senhaSegura123"
    })
    assert res_parc.status_code == 422

def test_onboarding_inconsistencia_obstetrica_rejeitada(client):
    # Cadastra gestante válida
    res = client.post("/auth/gestante/cadastro", json={
        "nome": "Carla Mendes",
        "email": "carla.mendes@teste.com",
        "senha": "senhaSegura123"
    })
    token = res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Tentativa com mais partos do que gestações (ex: 1 gestação anterior, mas 2 partos normais + 1 cesárea = 3)
    res_invalido = client.post("/perfil-clinico", headers=headers, json={
        "idade": 29,
        "gestacoes_anteriores": 1,
        "partos_normais": 2,
        "partos_cesareos": 1,
        "perdas_gestacionais": 0,
        "dum": str(date.today() - timedelta(days=60)),
        "dpp": str(date.today() + timedelta(days=220))
    })
    assert res_invalido.status_code == 422
    assert "inconsistência obstétrica" in res_invalido.text.lower()

def test_onboarding_limites_idade_e_dum_futura_rejeitados(client):
    res = client.post("/auth/gestante/cadastro", json={
        "nome": "Fernanda Souza",
        "email": "fernanda.souza@teste.com",
        "senha": "senhaSegura123"
    })
    token = res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Idade absurda (ex: 150 anos)
    res_idade = client.post("/perfil-clinico", headers=headers, json={
        "idade": 150,
        "gestacoes_anteriores": 0,
        "partos_normais": 0,
        "partos_cesareos": 0,
        "perdas_gestacionais": 0,
        "dum": str(date.today() - timedelta(days=30)),
        "dpp": str(date.today() + timedelta(days=250))
    })
    assert res_idade.status_code == 422

    # DUM no futuro
    res_dum = client.post("/perfil-clinico", headers=headers, json={
        "idade": 28,
        "gestacoes_anteriores": 0,
        "partos_normais": 0,
        "partos_cesareos": 0,
        "perdas_gestacionais": 0,
        "dum": str(date.today() + timedelta(days=5)),
        "dpp": str(date.today() + timedelta(days=280))
    })
    assert res_dum.status_code == 422

def test_checkin_limites_fisiologicos(client):
    res = client.post("/auth/gestante/cadastro", json={
        "nome": "Mariana Dias",
        "email": "mariana.dias@teste.com",
        "senha": "senhaSegura123"
    })
    token = res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Humor inválido (ex: 9)
    res_humor = client.post("/checkin/registrar", headers=headers, json={
        "humor": 9,
        "sintomas": [],
        "movimentos_bebe": 5
    })
    assert res_humor.status_code == 422

    # Chutes absurdos (ex: 500)
    res_chutes = client.post("/checkin/registrar", headers=headers, json={
        "humor": 4,
        "sintomas": [],
        "movimentos_bebe": 500
    })
    assert res_chutes.status_code == 422

def test_dispositivos_pressao_sistolica_menor_que_diastolica_rejeitada(client):
    res = client.post("/auth/gestante/cadastro", json={
        "nome": "Juliana Prado",
        "email": "juliana.prado@teste.com",
        "senha": "senhaSegura123"
    })
    token = res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Sistólica (80) <= Diastólica (120)
    res_pa = client.post("/dispositivos/medicao", headers=headers, json={
        "tipo": "pressao_arterial",
        "sistolica": 80,
        "diastolica": 120
    })
    assert res_pa.status_code == 422

    # Glicemia absurda (ex: 5 mg/dL ou 900 mg/dL)
    res_glic = client.post("/dispositivos/medicao", headers=headers, json={
        "tipo": "glicemia",
        "glicemia": 950.0
    })
    assert res_glic.status_code == 422

def test_cinta_bpm_limites_fisiologicos(client):
    res = client.post("/auth/gestante/cadastro", json={
        "nome": "Renata Lima",
        "email": "renata.lima@teste.com",
        "senha": "senhaSegura123"
    })
    token = res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # BPM absurdo (ex: 350 bpm)
    res_bpm = client.post("/cinta/telemetria", headers=headers, json={
        "bpm": 350
    })
    assert res_bpm.status_code == 422

def test_chat_mensagem_vazia_rejeitada(client):
    res = client.post("/auth/gestante/cadastro", json={
        "nome": "Paula Costa",
        "email": "paula.costa@teste.com",
        "senha": "senhaSegura123"
    })
    token = res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Mensagem de espaços em branco
    res_chat = client.post("/conversa/enviar", headers=headers, json={
        "texto": "    "
    })
    assert res_chat.status_code == 422

def test_codigo_convite_formato_invalido_rejeitado(client):
    res = client.post("/auth/gestante/cadastro", json={
        "nome": "Larissa Rocha",
        "email": "larissa.rocha@teste.com",
        "senha": "senhaSegura123"
    })
    token = res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Código muito curto ou com caracteres proibidos
    res_cod = client.post("/vinculo/convite/usar", headers=headers, json={
        "codigo": "123"
    })
    assert res_cod.status_code == 422
