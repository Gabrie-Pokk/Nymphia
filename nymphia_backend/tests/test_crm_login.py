import pytest

def test_consulta_crm_online_valido(client):
    res = client.get("/auth/profissional/validar-crm?crm=123456&uf=SP")
    assert res.status_code == 200
    data = res.json()
    assert data["valido"] is True
    assert data["situacao"] == "ATIVO"
    assert "Carlos" in data["nome_medico"] or "CRM-SP" in data["conselho"]

def test_consulta_crm_online_formato_invalido(client):
    res = client.get("/auth/profissional/validar-crm?crm=000000&uf=SP")
    assert res.status_code == 200
    data = res.json()
    assert data["valido"] is False
    assert data["situacao"] in ["FORMATO_INVALIDO", "NAO_ENCONTRADO"]

def test_consulta_crm_uf_invalida(client):
    res = client.get("/auth/profissional/validar-crm?crm=123456&uf=XX")
    assert res.status_code == 200
    data = res.json()
    assert data["valido"] is False

def test_login_profissional_com_crm_valido(client):
    # Cadastra médico
    res_cad = client.post("/auth/profissional/cadastro", json={
        "nome": "Dra. Roberta Santos",
        "email": "roberta@clinica.com",
        "senha": "senhaSegura123",
        "registro_tipo": "CRM",
        "registro_numero": "45678",
        "registro_uf": "SP"
    })
    assert res_cad.status_code == 201

    # Login unificado fornecendo CRM
    res_login = client.post("/auth/login", json={
        "email": "roberta@clinica.com",
        "senha": "senhaSegura123",
        "crm": "45678",
        "crm_uf": "SP",
        "perfil": "profissional"
    })
    assert res_login.status_code == 200
    data = res_login.json()
    assert data["perfil"] == "profissional"
    assert "token" in data

def test_login_profissional_com_crm_divergente_rejeita(client):
    # Cadastra médico
    client.post("/auth/profissional/cadastro", json={
        "nome": "Dr. Fernando Paiva",
        "email": "fernando@clinica.com",
        "senha": "senhaSegura123",
        "registro_tipo": "CRM",
        "registro_numero": "78910",
        "registro_uf": "MG"
    })

    # Tenta login com CRM divergente do cadastro
    res = client.post("/auth/login", json={
        "email": "fernando@clinica.com",
        "senha": "senhaSegura123",
        "crm": "123456",
        "crm_uf": "SP",
        "perfil": "profissional"
    })
    assert res.status_code == 401
    assert "não confere" in res.json()["detail"].lower()

def test_login_profissional_direto_por_crm_sem_digitar_email(client):
    # Cadastra médico para garantir existência na sessão isolada de teste
    client.post("/auth/profissional/cadastro", json={
        "nome": "Dr. Carlos Silva",
        "email": "carlos.crm@clinica.com",
        "senha": "senhaMaternidade123",
        "registro_tipo": "CRM",
        "registro_numero": "123456",
        "registro_uf": "SP"
    })

    # Login fornecendo apenas CRM, UF e senha (sem email)
    res = client.post("/auth/login", json={
        "senha": "senhaMaternidade123",
        "crm": "123456",
        "crm_uf": "SP",
        "perfil": "profissional"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["perfil"] == "profissional"
    assert "token" in data
    assert data["nome"] == "Dr. Carlos Silva"

def test_cadastro_profissional_crm_inativo_rejeitado(client):
    # CRM 145892/SP é real no CREMESP, mas consta com situação INATIVO
    res = client.post("/auth/profissional/cadastro", json={
        "nome": "Dra. Inativa Teste",
        "email": "inativa@clinica.com",
        "senha": "senhaSegura123",
        "registro_tipo": "CRM",
        "registro_numero": "145892",
        "registro_uf": "SP"
    })
    assert res.status_code == 400
    assert "inativo" in res.json()["detail"].lower() or "não foi possível validar" in res.json()["detail"].lower()

def test_cadastro_profissional_crm_inexistente_rejeitado(client):
    # CRM 99999999/SP não existe no cadastro oficial
    res = client.post("/auth/profissional/cadastro", json={
        "nome": "Dr. Fantasma",
        "email": "fantasma@clinica.com",
        "senha": "senhaSegura123",
        "registro_tipo": "CRM",
        "registro_numero": "99999999",
        "registro_uf": "SP"
    })
    assert res.status_code == 400
    assert "não foi localizado" in res.json()["detail"].lower() or "não foi possível validar" in res.json()["detail"].lower()

