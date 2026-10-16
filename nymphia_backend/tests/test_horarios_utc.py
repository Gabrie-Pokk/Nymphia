"""
Horários na resposta da API (16/10/2026).

O banco guarda UTC sem fuso. Sem o "Z" na resposta, o navegador lia o horário
como local e a ficha da profissional mostrava check-ins, mensagens e
observações 3 horas adiantados.
"""
import random
import uuid
from datetime import datetime, timedelta, timezone


def _instante(texto):
    """Lê o horário como o navegador lê: exige fuso explícito."""
    assert texto.endswith("Z") or "+" in texto[10:], f"horário sem fuso: {texto}"
    return datetime.fromisoformat(texto.replace("Z", "+00:00"))


def _perto_de_agora(texto):
    return abs(_instante(texto) - datetime.now(timezone.utc)) < timedelta(minutes=5)


def _gestante_e_profissional(client, aprovar_profissional):
    cad = client.post("/auth/gestante/cadastro", json={
        "nome": "Gestante Horario", "email": f"hora_{uuid.uuid4().hex[:8]}@teste.com", "senha": "senhaSegura123",
        "aceite_termos": True, "consentimento_dados_saude": True,
    })
    assert cad.status_code == 201, cad.text
    gestante_id = cad.json()["id"]
    headers = {"Authorization": f"Bearer {cad.json()['token']}"}
    prof = client.post("/auth/profissional/cadastro", json={
        "aceite_termos": True, "nome": "Dra. Teste Horario", "email": f"hora_{uuid.uuid4().hex[:6]}@clinica.com",
        "senha": "senhaSegura123", "registro_tipo": "CRM", "registro_numero": str(random.randint(100000, 999999)),
        "registro_uf": "SP",
    })
    assert prof.status_code == 201, prof.text
    aprovar_profissional(prof.json()["id"])
    headers_prof = {"Authorization": f"Bearer {prof.json()['token']}"}
    codigo = client.post("/vinculo/convite/gerar", headers=headers_prof).json()["codigo"]
    assert client.post("/vinculo/convite/usar", json={"codigo": codigo}, headers=headers).status_code == 201
    return gestante_id, headers, headers_prof


def test_ficha_da_profissional_manda_os_horarios_em_utc(client, aprovar_profissional):
    gestante_id, headers, headers_prof = _gestante_e_profissional(client, aprovar_profissional)
    dum_data = datetime.now(timezone.utc).date() - timedelta(days=10 * 7)
    dum = dum_data.isoformat()
    perfil = client.post("/perfil-clinico", headers=headers, json={
        "idade": 28, "gestacoes_anteriores": 0, "partos_normais": 0, "partos_cesareos": 0, "perdas_gestacionais": 0,
        "dum": dum, "dpp": (dum_data + timedelta(days=280)).isoformat(),
    })
    assert perfil.status_code == 201, perfil.text

    checkin = client.post("/checkin/registrar", headers=headers,
                          json={"humor": 4, "descricao": "Dia tranquilo", "sintomas": []})
    assert checkin.status_code == 201, checkin.text
    assert _perto_de_agora(checkin.json()["data_hora"])

    client.post("/conversa/enviar", headers=headers, json={"texto": "Posso comer queijo coalho?"})
    mensagem = client.get("/conversa/historico", headers=headers).json()[0]
    assert client.post(f"/conversa/{mensagem['id']}/autorizar-compartilhamento", headers=headers).status_code == 200

    obs = client.post(f"/vinculo/paciente/{gestante_id}/observacao", headers=headers_prof,
                      json={"observacao": "Retorno em 15 dias."})
    assert obs.status_code == 201, obs.text
    assert _perto_de_agora(obs.json()["criado_em"])

    ficha = client.get(f"/vinculo/paciente/{gestante_id}/ficha", headers=headers_prof)
    assert ficha.status_code == 200, ficha.text
    ficha = ficha.json()
    assert _perto_de_agora(ficha["checkins"][0]["data_hora"])
    assert _perto_de_agora(ficha["mensagens_autorizadas"][0]["data_hora"])
    assert _perto_de_agora(ficha["observacoes_medicas"][0]["criado_em"])
    assert _perto_de_agora(ficha["perfil_clinico"]["atualizado_em"])
    # Datas sem hora continuam só data (a tela soma o meio-dia)
    assert ficha["perfil_clinico"]["dum"] == dum
    # Os campos do check-in continuam os mesmos de antes
    assert ficha["checkins"][0]["descricao"] == "Dia tranquilo" and ficha["checkins"][0]["humor"] == 4

    painel = client.get("/vinculo/minhas-gestantes", headers=headers_prof).json()
    assert _perto_de_agora(painel[0]["ultimo_checkin"])


def test_registros_da_gestante_saem_com_fuso(client, aprovar_profissional):
    gestante_id, headers, headers_prof = _gestante_e_profissional(client, aprovar_profissional)
    assert client.get(f"/vinculo/paciente/{gestante_id}/ficha", headers=headers_prof).status_code == 200
    logs = client.get("/meus-dados/log-acesso", headers=headers)
    assert logs.status_code == 200, logs.text
    assert logs.json() and all(_perto_de_agora(l["data_hora"]) for l in logs.json())
    vinculos = client.get("/vinculo/meus-profissionais", headers=headers)
    assert vinculos.status_code == 200, vinculos.text
    assert _perto_de_agora(vinculos.json()[0]["criado_em"])
