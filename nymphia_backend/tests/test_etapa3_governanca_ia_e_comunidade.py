import pytest
from fastapi.testclient import TestClient

def test_transparencia_clinica_cfm_2454_e_cdc(client: TestClient):
    """
    Verifica a publicação obrigatória das métricas dos modelos de IA,
    classificação SaMD e justificativa do desbalanceamento de ITU (CFM 2.454/2026 e CDC).
    """
    res = client.get("/modelos/transparencia-clinica")
    assert res.status_code == 200
    data = res.json()

    assert "CFM nº 2.454/2026" in data["marco_regulatorio"]
    assert "SaMD" in data["classificacao_samd"]
    assert "PROIBIDO" in data["finalidade_exclusiva"]
    assert "modelos" in data

    modelos = data["modelos"]
    assert "pre_eclampsia" in modelos
    assert "eclampsia" in modelos
    assert "diabetes_gestacional" in modelos
    assert "bem_estar_fetal" in modelos
    assert "malformacao" in modelos
    assert "itu" in modelos

    # Validação do modelo de ITU com transparência sobre precisão 0.01 / 1%
    itu = modelos["itu"]
    assert itu["precisao"] == 0.01
    assert itu["alerta_cdc_transparencia"] is True
    assert "desbalanceamento" in itu["justificativa_tecnica"].lower()
    assert "SIH/SUS" in itu["justificativa_tecnica"]

    # Rota alternativa /risco/transparencia-clinica
    res_alt = client.get("/risco/transparencia-clinica")
    assert res_alt.status_code == 200


def test_carimbo_samd_em_calculo_de_risco(client: TestClient):
    """
    Verifica se a resposta de cálculo de risco carrega o carimbo auditável SaMD (CFM 2.454/2026, Art. 4º, V).
    """
    payload = {
        "idade": 28,
        "gestacoes_anteriores": 1,
        "partos_normais": 1,
        "partos_cesareos": 0,
        "perdas_gestacionais": 0
    }
    res = client.post("/risco/gestante", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert "carimbo_samd_cfm" in data
    assert "CFM nº 2.454/2026" in data["carimbo_samd_cfm"]
    assert "alerta_transparencia_cdc" in data["condicoes"]["itu"]


def test_diretrizes_comunidade_stf_tema_987(client: TestClient):
    """
    Verifica a exposição das diretrizes da comunidade conforme o Marco Civil e STF Tema 987.
    """
    res = client.get("/comunidade/diretrizes")
    assert res.status_code == 200
    data = res.json()

    assert "STF Tema 987" in data["fundamento_legal"]
    assert len(data["regras"]) >= 4
    topicos = [r["topico"] for r in data["regras"]]
    assert any("Automedicação" in t for t in topicos)
    assert any("Recurso" in t for t in topicos)
    assert any("CVV 188" in t for t in topicos)


def test_denuncia_estruturada_e_protocolo_cvv_188(client: TestClient):
    """
    Testa o fluxo de denúncia de conteúdo:
    1. Cria post na comunidade
    2. Denúncia por automutilação/suicídio aciona ocultação imediata preventiva e protocolo CVV 188
    3. Post deixa de aparecer na listagem pública
    """
    # Cria gestante 1 (autora)
    reg_res = client.post("/auth/gestante/cadastro", json={
        "nome": "Usuária Comunitária",
        "email": "autora.comunidade@teste.com",
        "senha": "senhaSegura123",
        "aceite_termos": True,
        "consentimento_dados_saude": True
    })
    token = reg_res.json()["token"]
    auth_header = {"Authorization": f"Bearer {token}"}

    # Cria post
    post_res = client.post("/comunidade/posts", headers=auth_header, json={
        "grupo": "Primeiro Trimestre",
        "conteudo": "Compartilhando minha experiência sobre as primeiras semanas."
    })
    assert post_res.status_code == 201
    post_id = post_res.json()["id"]

    # Denúncia por ideação / automutilação
    denuncia_res = client.post(f"/comunidade/posts/{post_id}/denunciar", json={
        "motivo": "automutilacao_suicidio",
        "detalhes": "Mensagem expressando sofrimento mental agudo que requer suporte urgente."
    })
    assert denuncia_res.status_code == 200
    denuncia_data = denuncia_res.json()

    assert denuncia_data["acao_imediata"] == "ocultacao_preventiva"
    assert denuncia_data["protocolo_acolhimento"] is not None
    assert denuncia_data["protocolo_acolhimento"]["cvv"] == "188"
    assert "Centro de Valorização da Vida" in denuncia_data["protocolo_acolhimento"]["cvv_titulo"]
    assert denuncia_data["protocolo_acolhimento"]["samu"] == "192"

    # Verifica que o post NÃO aparece mais na listagem pública da comunidade
    feed_res = client.get("/comunidade/posts?grupo=Primeiro+Trimestre", headers=auth_header)
    assert feed_res.status_code == 200
    feed_ids = [p["id"] for p in feed_res.json()]
    assert post_id not in feed_ids


def test_recurso_moderacao_stf_tema_987(client: TestClient):
    """
    Testa o direito ao contraditório e recurso de moderação (STF Tema 987):
    - Autora consulta conteúdos moderados
    - Submete recurso fundamentado
    - Terceiro é impedido de recorrer de post alheio (403)
    """
    # Gestante A (autora)
    reg_a = client.post("/auth/gestante/cadastro", json={
        "nome": "Gestante Moderada",
        "email": "gestante.moderada@teste.com",
        "senha": "senhaSegura123",
        "aceite_termos": True,
        "consentimento_dados_saude": True
    })
    token_a = reg_a.json()["token"]
    header_a = {"Authorization": f"Bearer {token_a}"}

    # Gestante B (outra usuária)
    reg_b = client.post("/auth/gestante/cadastro", json={
        "nome": "Gestante Terceira",
        "email": "gestante.terceira@teste.com",
        "senha": "senhaSegura123",
        "aceite_termos": True,
        "consentimento_dados_saude": True
    })
    token_b = reg_b.json()["token"]
    header_b = {"Authorization": f"Bearer {token_b}"}

    # Post de A
    post_res = client.post("/comunidade/posts", headers=header_a, json={
        "grupo": "Segundo Trimestre",
        "conteudo": "Gostaria de relatar um desconforto moderado para saber se alguém já sentiu."
    })
    post_id = post_res.json()["id"]

    # Post sofre denúncia e sinalização
    client.post(f"/comunidade/posts/{post_id}/denunciar", json={
        "motivo": "desinformacao_saude",
        "detalhes": "Sintoma que pode necessitar orientação obstétrica."
    })

    # Gestante B tenta recorrer do post de A -> Deve ser bloqueada (403)
    recurso_invalido = client.post(f"/comunidade/posts/{post_id}/recorrer", headers=header_b, json={
        "justificativa": "Quero defender a publicação alheia."
    })
    assert recurso_invalido.status_code == 403

    # Gestante A consulta suas moderações
    minhas_mod = client.get("/comunidade/minhas-moderacoes", headers=header_a)
    assert minhas_mod.status_code == 200
    mod_items = minhas_mod.json()
    assert any(m["id"] == post_id for m in mod_items)

    # Gestante A submete recurso válido
    recurso_valido = client.post(f"/comunidade/posts/{post_id}/recorrer", headers=header_a, json={
        "justificativa": "Meu relato descreve uma dúvida legítima sem intenção de automedicação ou desinformação."
    })
    assert recurso_valido.status_code == 201
    assert recurso_valido.json()["status"] == "pendente"

    # Tentar recorrer de novo enquanto pendente -> 409 Conflict
    recurso_duplicado = client.post(f"/comunidade/posts/{post_id}/recorrer", headers=header_a, json={
        "justificativa": "Enviando novamente recurso."
    })
    assert recurso_duplicado.status_code == 409
