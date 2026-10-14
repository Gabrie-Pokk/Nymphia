import uuid
import pytest

def test_fluxo_completo_vinculo_parceiro_sem_hardcode(client):
    # 1. Cadastra gestante real
    email_gest = f"gestante_{uuid.uuid4().hex[:6]}@teste.com"
    res_g = client.post("/auth/gestante/cadastro", json={
        "nome": "Juliana Alencar",
        "email": email_gest,
        "senha": "senhaSegura123",
        "aceite_termos": True
    })
    assert res_g.status_code == 201
    token_g = res_g.json()["token"]
    headers_g = {"Authorization": f"Bearer {token_g}"}

    # 2. Gestante consulta seu status de parceiro
    res_vinculo_g = client.get("/parceiro/meu-vinculo", headers=headers_g)
    assert res_vinculo_g.status_code == 200
    dados_g = res_vinculo_g.json()
    assert dados_g["conectado"] is False
    assert dados_g["codigo"].startswith("PARC-")
    codigo_convite = dados_g["codigo"]

    # 3. Cadastra parceiro real
    email_parc = f"parceiro_{uuid.uuid4().hex[:6]}@teste.com"
    res_p = client.post("/auth/parceiro/cadastro", json={
        "nome": "Rafael Oliveira",
        "email": email_parc,
        "senha": "senhaSegura123",
        "aceite_termos": True
    })
    assert res_p.status_code == 201
    token_p = res_p.json()["token"]
    headers_p = {"Authorization": f"Bearer {token_p}"}

    # 4. Parceiro consulta gestante conectada (deve ser False antes do código)
    res_g_conectada = client.get("/parceiro/gestante-conectada", headers=headers_p)
    assert res_g_conectada.status_code == 200
    assert res_g_conectada.json()["conectado"] is False

    # 5. Parceiro usa o código da gestante Juliana
    res_usar = client.post("/parceiro/convite/usar", json={"codigo": codigo_convite}, headers=headers_p)
    assert res_usar.status_code == 201

    # 6. Parceiro agora está conectado a Juliana
    res_g_conectada_pos = client.get("/parceiro/gestante-conectada", headers=headers_p)
    assert res_g_conectada_pos.status_code == 200
    dados_parc_pos = res_g_conectada_pos.json()
    assert dados_parc_pos["conectado"] is True
    assert dados_parc_pos["gestante_nome"] == "Juliana Alencar"

    # 7. Gestante agora vê Rafael conectado
    res_vinculo_g_pos = client.get("/parceiro/meu-vinculo", headers=headers_g)
    assert res_vinculo_g_pos.status_code == 200
    dados_g_pos = res_vinculo_g_pos.json()
    assert dados_g_pos["conectado"] is True
    assert dados_g_pos["parceiro"]["nome"] == "Rafael Oliveira"
