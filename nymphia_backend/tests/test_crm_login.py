"""
Conferência de CRM e login de profissional (reescrito em 15/10/2026).

Regras que estes testes garantem:
- Nenhum CRM é aprovado automaticamente. Todo cadastro entra "pendente".
- Não existe mais lista interna de "médicos homologados".
- O CREMESP (só SP) pode bloquear registro inativo, mas nunca aprova.
- Sem resposta do CREMESP, o cadastro segue para conferência manual.
- O número do registro é guardado só com dígitos: "45.678" e "45678" são o mesmo.
Nenhum teste fala com a internet: a consulta ao CREMESP é simulada.
"""
import pytest

from app.services import crm_service


def _cadastro(client, **extras):
    dados = {
        "aceite_termos": True,
        "nome": "Dra. Roberta Santos",
        "email": "roberta@clinica.com",
        "senha": "senhaSegura123",
        "registro_tipo": "CRM",
        "registro_numero": "45678",
        "registro_uf": "SP",
    }
    dados.update(extras)
    return client.post("/auth/profissional/cadastro", json=dados)


def _cremesp(monkeypatch, situacao, nome="Fulana de Tal"):
    """Simula a resposta do CREMESP: 'A' ativo, 'I' inativo."""
    def _falso(crm_limpo):
        if situacao == "A":
            return {"valido": True, "situacao": "ENCONTRADO_NO_CREMESP", "nome_medico": nome,
                    "especialidade": None, "mensagem": "Registro encontrado como ativo no CREMESP."}
        return {"valido": False, "situacao": "INATIVO_NO_CREMESP", "nome_medico": nome,
                "especialidade": None, "mensagem": "O CREMESP mostra este registro como inativo ou com restrição."}
    monkeypatch.setattr(crm_service, "_consultar_cremesp", _falso)


# --- Consulta pública /auth/profissional/validar-crm ---

def test_formato_invalido_e_recusado(client):
    data = client.get("/auth/profissional/validar-crm?crm=000000&uf=SP").json()
    assert data["valido"] is False
    assert data["situacao"] == "FORMATO_INVALIDO"


def test_uf_invalida_e_recusada(client):
    data = client.get("/auth/profissional/validar-crm?crm=123456&uf=XX").json()
    assert data["valido"] is False
    assert data["situacao"] == "FORMATO_INVALIDO"


def test_sem_resposta_do_cremesp_vira_conferencia_manual(client):
    data = client.get("/auth/profissional/validar-crm?crm=123456&uf=SP").json()
    assert data["valido"] is True
    assert data["situacao"] == "VERIFICACAO_MANUAL_PENDENTE"
    # Não existe mais nome inventado para CRM nenhum
    assert data["nome_medico"] is None


def test_lista_falsa_de_medicos_foi_removida():
    for nome in ("MEDICOS_HOMOLOGADOS_CFM", "MEDICOS_HOMOLOGADOS"):
        assert not hasattr(crm_service, nome)


def test_fora_de_sp_nao_consulta_cremesp(client, monkeypatch):
    chamadas = []
    monkeypatch.setattr(crm_service, "_consultar_cremesp", lambda crm: chamadas.append(crm))
    data = client.get("/auth/profissional/validar-crm?crm=78910&uf=MG").json()
    assert data["situacao"] == "VERIFICACAO_MANUAL_PENDENTE"
    assert chamadas == []


def test_coren_nao_consulta_cremesp():
    resultado = crm_service.consultar_situacao_crm("123456", "SP", registro_tipo="COREN")
    assert resultado["situacao"] == "VERIFICACAO_MANUAL_PENDENTE"
    assert resultado["conselho"] == "COREN-SP"


def test_cremesp_ativo_preenche_nome_mas_nao_aprova(client, monkeypatch):
    _cremesp(monkeypatch, "A", nome="Roberta Santos")
    data = client.get("/auth/profissional/validar-crm?crm=45678&uf=SP").json()
    assert data["valido"] is True
    assert data["situacao"] == "ENCONTRADO_NO_CREMESP"
    assert data["nome_medico"] == "Roberta Santos"

    res = _cadastro(client)
    assert res.status_code == 201
    assert res.json()["status_verificacao"] == "pendente"


# --- Cadastro ---

def test_cadastro_entra_sempre_pendente(client):
    res = _cadastro(client)
    assert res.status_code == 201, res.text
    assert res.json()["status_verificacao"] == "pendente"


def test_cadastro_crm_inativo_no_cremesp_e_recusado(client, monkeypatch):
    _cremesp(monkeypatch, "I")
    res = _cadastro(client, email="inativa@clinica.com", registro_numero="145892")
    assert res.status_code == 400
    assert "inativo" in res.json()["detail"].lower()


def test_cadastro_normaliza_numero_com_ponto(client):
    res = _cadastro(client, registro_numero="45.678")
    assert res.status_code == 201, res.text
    login = client.post("/auth/login", json={
        "senha": "senhaSegura123", "crm": "45678", "crm_uf": "SP", "perfil": "profissional"
    })
    assert login.status_code == 200


def test_mesmo_registro_nao_cria_duas_contas(client):
    assert _cadastro(client).status_code == 201
    res = _cadastro(client, email="outra@clinica.com", registro_numero="45.678")
    assert res.status_code == 409


def test_cadastro_sem_aceite_dos_termos_e_recusado(client):
    dados = {
        "nome": "Dr. Sem Aceite",
        "email": "semaceite@clinica.com",
        "senha": "senhaSegura123",
        "registro_tipo": "CRM",
        "registro_numero": "55555",
        "registro_uf": "RJ",
    }
    assert client.post("/auth/profissional/cadastro", json=dados).status_code == 422


# --- Login ---

def test_login_com_crm_valido(client):
    assert _cadastro(client).status_code == 201
    res = client.post("/auth/login", json={
        "email": "roberta@clinica.com",
        "senha": "senhaSegura123",
        "crm": "45678",
        "crm_uf": "SP",
        "perfil": "profissional"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["perfil"] == "profissional"
    assert data["status_verificacao"] == "pendente"
    assert "token" in data


def test_login_com_crm_digitado_com_ponto(client):
    assert _cadastro(client).status_code == 201
    res = client.post("/auth/login", json={
        "email": "roberta@clinica.com", "senha": "senhaSegura123",
        "crm": "45.678", "crm_uf": "SP", "perfil": "profissional"
    })
    assert res.status_code == 200


def test_login_com_crm_divergente_rejeita(client):
    _cadastro(client, nome="Dr. Fernando Paiva", email="fernando@clinica.com",
              registro_numero="78910", registro_uf="MG")
    res = client.post("/auth/login", json={
        "email": "fernando@clinica.com",
        "senha": "senhaSegura123",
        "crm": "123456",
        "crm_uf": "SP",
        "perfil": "profissional"
    })
    assert res.status_code == 401
    assert "não confere" in res.json()["detail"].lower()


def test_login_direto_por_crm_sem_email(client):
    _cadastro(client, nome="Dr. Carlos Silva", email="carlos.crm@clinica.com",
              senha="SenhaForteCRM2026!", registro_numero="123456")
    res = client.post("/auth/login", json={
        "senha": "SenhaForteCRM2026!",
        "crm": "123456",
        "crm_uf": "SP",
        "perfil": "profissional"
    })
    assert res.status_code == 200
    assert res.json()["nome"] == "Dr. Carlos Silva"


# --- Acesso a pacientes depende de aprovação manual ---

def test_pendente_nao_acessa_pacientes_ate_aprovacao(client, aprovar_profissional):
    res = _cadastro(client)
    headers = {"Authorization": f"Bearer {res.json()['token']}"}

    assert client.post("/vinculo/convite/gerar", headers=headers).status_code == 403
    assert client.get("/vinculo/minhas-gestantes", headers=headers).status_code == 403

    aprovar_profissional(res.json()["id"])

    assert client.post("/vinculo/convite/gerar", headers=headers).status_code == 200
    assert client.get("/vinculo/minhas-gestantes", headers=headers).status_code == 200


def test_rejeitado_perde_acesso(client, admin_headers):
    res = _cadastro(client)
    prof_id = res.json()["id"]
    headers = {"Authorization": f"Bearer {res.json()['token']}"}

    rej = client.post(f"/admin/profissionais/{prof_id}/rejeitar",
                      json={"motivo": "Registro não encontrado no portal do CFM"},
                      headers=admin_headers)
    assert rej.status_code == 200
    assert rej.json()["status_verificacao"] == "rejeitado"
    assert client.post("/vinculo/convite/gerar", headers=headers).status_code == 403
    login = client.post("/auth/login", json={
        "email": "roberta@clinica.com", "senha": "senhaSegura123",
        "crm": "45678", "crm_uf": "SP", "perfil": "profissional"
    })
    assert login.status_code == 403
