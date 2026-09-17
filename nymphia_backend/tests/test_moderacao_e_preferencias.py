import pytest
from app.services.moderation_service import moderate_community_content
from app.services.ai_chat_service import generate_chat_response

def test_moderacao_bloqueia_ofensas_e_toxidade():
    # Palavras de ofensa grave ou tóxicas
    bloqueado, motivo, aviso = moderate_community_content("Você é uma idiota e incompetente")
    assert bloqueado is True
    assert "Diretrizes de Respeito" in motivo

def test_moderacao_bloqueia_automedicacao_perigosa():
    # Prescrição de dosagem e medicamentos perigosos
    bloqueado, motivo, aviso = moderate_community_content("Toma 500mg de diclofenaco para passar a dor")
    assert bloqueado is True
    assert "não é permitido indicar dosagens" in motivo

def test_moderacao_permite_com_aviso_clinico():
    # Discussão de exames laboratoriais
    bloqueado, motivo, aviso = moderate_community_content("Minha glicemia deu 95 no exame de sangue, será que tá alta?")
    assert bloqueado is False
    assert aviso is True

def test_chat_ia_saudacao_acolhedora():
    resp, alerta, fonte = generate_chat_response("Oi, como você funciona?")
    assert alerta is False
    assert fonte == "assistente_nymphia"
    assert "FEBRASGO" in resp
    assert "CFM 2.454/2026" in resp

def test_chat_ia_orientacao_azia():
    resp, alerta, fonte = generate_chat_response("Estou com muita azia e queimação hoje")
    assert alerta is False
    assert fonte == "base_clinica_ia"
    assert "refluxo" in resp.lower()

def test_chat_ia_alerta_emergencia():
    resp, alerta, fonte = generate_chat_response("Estou tendo um sangramento vermelho vivo muito forte")
    assert alerta is True
    assert fonte == "regras_urgencia"
    assert "192" in resp

def test_preferencias_comunidade_api(client):
    reg = client.post("/auth/gestante/cadastro", json={
        "nome": "Marina Silva",
        "email": "marina.comunidade@teste.com",
        "senha": "senhaSegura123"
    })
    token = reg.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Salva questionário de preferências
    payload = {
        "experiencia": "Primeira gestação",
        "preferencia_parto": "Parto normal humanizado",
        "interesses": ["Nutrição & Receitas Gestacionais", "Yoga, Exercícios & Bem-Estar"],
        "estilo_vida": "Tranquila e Conectada"
    }
    res_salvar = client.post("/comunidade/preferencias", json=payload, headers=headers)
    assert res_salvar.status_code == 200
    data = res_salvar.json()
    assert "Mães de Primeira Viagem" in data["grupos_recomendados"]
    assert "Parto Humanizado & Preparação" in data["grupos_recomendados"]
    assert "Nutrição & Receitas Gestacionais" in data["grupos_recomendados"]

    # Postagem bloqueada por automedicação
    res_post_bloqueado = client.post("/comunidade/posts", json={
        "grupo": "Mães de Primeira Viagem",
        "conteudo": "Recomendo tomar 10 gotas de remédio para enjoo de hora em hora"
    }, headers=headers)
    assert res_post_bloqueado.status_code == 400
    assert "não é permitido indicar dosagens" in res_post_bloqueado.json()["detail"]

    # Postagem válida
    res_post_ok = client.post("/comunidade/posts", json={
        "grupo": "Mães de Primeira Viagem",
        "conteudo": "Alguém mais ansiosa com a chegada do ultrassom morfológico?"
    }, headers=headers)
    assert res_post_ok.status_code == 201
