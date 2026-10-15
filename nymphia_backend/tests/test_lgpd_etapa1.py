import pytest
import uuid
from datetime import datetime
from app.models.governance import ObservacaoProfissional, CustodiaProntuario
from app.models.auth import Gestante

def test_consultar_politica_e_termos_publicos(client):
    # Política de Privacidade
    res_pol = client.get("/politica-privacidade")
    assert res_pol.status_code == 200
    data_pol = res_pol.json()
    assert "encarregado_dpo" in data_pol
    assert data_pol["encarregado_dpo"]["email_contato"] == "privacidade@nymphia.com.br"
    assert "recorte_guarda_prontuario" in data_pol
    assert "1.821/2007" in data_pol["recorte_guarda_prontuario"]

    # Termos de Uso
    res_term = client.get("/termos-de-uso")
    assert res_term.status_code == 200
    data_term = res_term.json()
    assert "natureza_do_servico" in data_term
    assert any("SAMU 192" in s for s in data_term["natureza_do_servico"])

    # Canal DPO
    res_dpo = client.get("/meus-dados/dpo")
    assert res_dpo.status_code == 200
    assert res_dpo.json()["email_contato"] == "privacidade@nymphia.com.br"


def test_cadastro_gestante_rejeita_sem_aceite_termos_ou_consentimento_saude(client):
    # Sem aceitar termos
    res_recusa_termos = client.post("/auth/gestante/cadastro", json={
        "nome": "Mariana Falha",
        "email": f"mariana_termos_{uuid.uuid4().hex[:6]}@teste.com",
        "senha": "senhaSegura123",
        "aceite_termos": False,
        "consentimento_dados_saude": True
    })
    assert res_recusa_termos.status_code == 422
    assert "obrigatório aceitar os Termos" in res_recusa_termos.text

    # Sem consentimento de dados sensíveis de saúde
    res_recusa_saude = client.post("/auth/gestante/cadastro", json={
        "nome": "Mariana SemSaude",
        "email": f"mariana_saude_{uuid.uuid4().hex[:6]}@teste.com",
        "senha": "senhaSegura123",
        "aceite_termos": True,
        "consentimento_dados_saude": False
    })
    assert res_recusa_saude.status_code == 422
    assert "consentir com o tratamento de dados pessoais sensíveis" in res_recusa_saude.text


def test_cadastro_gestante_registra_termos_e_consentimento_auditaveis(client):
    email = f"gestante_audit_{uuid.uuid4().hex[:6]}@teste.com"
    res = client.post("/auth/gestante/cadastro", json={
        "nome": "Laura Conformidade",
        "email": email,
        "senha": "senhaSegura123",
        "aceite_termos": True,
        "consentimento_dados_saude": True,
        "termos_versao": "1.0-2026"
    })
    assert res.status_code == 201
    token = res.json()["token"]
    user_id = res.json()["id"]

    # Consulta exportação de dados para verificar dados do titular
    res_exp = client.get("/meus-dados/exportar?formato=json", headers={"Authorization": f"Bearer {token}"})
    assert res_exp.status_code == 200
    assert res_exp.json()["titular"]["email"] == email


def test_solicitar_revisao_humana_decisao_ia(client):
    reg = client.post("/auth/gestante/cadastro", json={
        "aceite_termos": True,
        "consentimento_dados_saude": True,
        "nome": "Beatriz Revisao",
        "email": f"beatriz_{uuid.uuid4().hex[:6]}@teste.com",
        "senha": "senhaSegura123"
    })
    token = reg.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Solicita revisão de decisão algorítmica (Art. 20 LGPD)
    res_rev = client.post("/meus-dados/solicitar-revisao-ia", json={
        "motivo": "Discordo do escore moderado atribuído e gostaria de reanálise médica humana dos critérios.",
        "recurso_analisado": "escore_pre_eclampsia"
    }, headers=headers)
    assert res_rev.status_code == 201
    rev_data = res_rev.json()
    assert rev_data["status"] == "pendente"
    assert rev_data["recurso_analisado"] == "escore_pre_eclampsia"

    # Lista minhas revisões
    res_list = client.get("/meus-dados/minhas-revisoes", headers=headers)
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1
    assert res_list.json()[0]["id"] == rev_data["id"]


def test_exclusao_preserva_custodia_medica_prontuario(client, db_session, aprovar_profissional):
    # 1. Cadastra médico
    res_prof = client.post("/auth/profissional/cadastro", json={
        "aceite_termos": True,
        "nome": "Dr. Custodio",
        "email": f"custodio_{uuid.uuid4().hex[:6]}@med.com",
        "senha": "senhaSegura123",
        "registro_tipo": "CRM",
        "registro_numero": "45678",
        "registro_uf": "SP"
    })

    token_prof = res_prof.json()["token"]
    prof_id = res_prof.json()["id"]
    aprovar_profissional(prof_id)
    headers_prof = {"Authorization": f"Bearer {token_prof}"}

    # Gera convite
    convite = client.post("/vinculo/convite/gerar", headers=headers_prof).json()["codigo"]

    # 2. Cadastra gestante e ativa vínculo
    reg_gest = client.post("/auth/gestante/cadastro", json={
        "aceite_termos": True,
        "consentimento_dados_saude": True,
        "nome": "Valeria Paciente",
        "email": f"valeria_{uuid.uuid4().hex[:6]}@teste.com",
        "senha": "senhaSegura123"
    })
    token_gest = reg_gest.json()["token"]
    gest_id = reg_gest.json()["id"]
    headers_gest = {"Authorization": f"Bearer {token_gest}"}

    client.post("/vinculo/convite/usar", json={"codigo": convite}, headers=headers_gest)

    # 3. Médico insere uma observação clínica formal no prontuário
    client.post(f"/vinculo/paciente/{gest_id}/observacao", json={
        "observacao": "Paciente orientada quanto ao repouso e aferição diária da pressão arterial."
    }, headers=headers_prof)

    # 4. Gestante solicita exclusão definitiva de conta
    res_del = client.delete("/minha-conta", headers=headers_gest)
    assert res_del.status_code == 200
    assert "excluida" in res_del.json()["status"]
    assert "1.821/2007" in res_del.json()["mensagem"]

    # 5. Verifica se o prontuário foi preservado em arquivo de custódia médica
    custodia = db_session.query(CustodiaProntuario).filter(
        CustodiaProntuario.profissional_id == prof_id
    ).all()
    assert len(custodia) >= 1
    assert "pressão arterial" in custodia[0].observacao
