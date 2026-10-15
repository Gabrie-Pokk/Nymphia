"""
Triagem emocional com a EPDS (15/10/2026).

O texto das perguntas não está no repositório: os testes usam um arquivo com
textos de mentira e a chave de pontuação verdadeira da escala.
"""
import json
import random
import uuid

import pytest

from app.services import epds_service

CHAVE = {n: ([0, 1, 2, 3] if n in (1, 2, 4) else [3, 2, 1, 0]) for n in range(1, 11)}


def _arquivo(chave=CHAVE, licenca="Autorização de teste"):
    return {
        "versao": "EPDS de teste",
        "licenca": licenca,
        "instrucao": "Instrução de teste",
        "itens": [
            {"numero": n, "texto": f"Pergunta de teste {n}",
             "opcoes": [{"texto": f"Resposta {i + 1}", "pontos": p} for i, p in enumerate(chave[n])]}
            for n in range(1, 11)
        ],
    }


@pytest.fixture
def com_questionario(tmp_path, monkeypatch):
    caminho = tmp_path / "epds.json"
    caminho.write_text(json.dumps(_arquivo()), encoding="utf-8")
    monkeypatch.delenv("NYMPHIA_EPDS_JSON", raising=False)
    monkeypatch.setenv("NYMPHIA_EPDS_ARQUIVO", str(caminho))
    epds_service.recarregar()
    yield caminho
    epds_service.recarregar()


@pytest.fixture
def sem_questionario(tmp_path, monkeypatch):
    monkeypatch.delenv("NYMPHIA_EPDS_JSON", raising=False)
    monkeypatch.setenv("NYMPHIA_EPDS_ARQUIVO", str(tmp_path / "nao_existe.json"))
    epds_service.recarregar()
    yield
    epds_service.recarregar()


def _gestante(client, dum=None):
    cad = client.post("/auth/gestante/cadastro", json={
        "nome": "Gestante EPDS", "email": f"epds_{uuid.uuid4().hex[:8]}@teste.com", "senha": "senhaSegura123",
        "aceite_termos": True, "consentimento_dados_saude": True,
    })
    assert cad.status_code == 201, cad.text
    return cad.json()["id"], {"Authorization": f"Bearer {cad.json()['token']}"}


def _profissional_vinculado(client, aprovar_profissional, headers_gestante):
    prof = client.post("/auth/profissional/cadastro", json={
        "aceite_termos": True, "nome": "Dra. Teste EPDS", "email": f"dra_{uuid.uuid4().hex[:6]}@clinica.com",
        "senha": "senhaSegura123", "registro_tipo": "CRM", "registro_numero": str(random.randint(100000, 999999)),
        "registro_uf": "SP",
    })
    assert prof.status_code == 201, prof.text
    aprovar_profissional(prof.json()["id"])
    headers_prof = {"Authorization": f"Bearer {prof.json()['token']}"}
    codigo = client.post("/vinculo/convite/gerar", headers=headers_prof).json()["codigo"]
    assert client.post("/vinculo/convite/usar", json={"codigo": codigo}, headers=headers_gestante).status_code == 201
    return headers_prof


# ---------------------------------------------------------------- pontuação

def test_chave_da_escala_inverte_as_perguntas_3_e_5_a_10():
    primeira_em_todas = epds_service.pontuar([0] * 10)
    assert primeira_em_todas["pontos_por_item"] == [0, 0, 3, 0, 3, 3, 3, 3, 3, 3]
    assert primeira_em_todas["pontuacao"] == 21
    ultima_em_todas = epds_service.pontuar([3] * 10)
    assert ultima_em_todas["pontos_por_item"] == [3, 3, 0, 3, 0, 0, 0, 0, 0, 0]
    assert ultima_em_todas["pontuacao"] == 9


def test_corte_de_triagem_e_10():
    assert epds_service.classificar(9, 0) == "sem_sinais"
    assert epds_service.classificar(10, 0) == "atencao"


def test_qualquer_pontuacao_na_pergunta_10_e_urgente():
    respostas = [0, 0, 3, 0, 3, 3, 3, 3, 3, 2]  # tudo com 0 ponto, menos a pergunta 10 (1 ponto)
    resultado = epds_service.pontuar(respostas)
    assert resultado["pontuacao"] == 1
    assert resultado["nivel"] == "urgente"
    assert "188" in resultado["mensagem"] and "192" in resultado["mensagem"]


def test_resposta_fora_da_faixa_e_recusada():
    with pytest.raises(ValueError):
        epds_service.pontuar([0] * 9)
    with pytest.raises(ValueError):
        epds_service.pontuar([0] * 9 + [4])


# ---------------------------------------------------------------- arquivo do texto

def test_sem_arquivo_a_triagem_fica_desligada(client, sem_questionario):
    _, headers = _gestante(client)
    assert client.get("/epds/status", headers=headers).json()["disponivel"] is False
    q = client.get("/epds/questionario", headers=headers).json()
    assert q["disponivel"] is False and "texto validado" in q["motivo"]
    assert client.post("/epds/respostas", json={"respostas": [3] * 10}, headers=headers).status_code == 503


def test_arquivo_com_pontos_trocados_e_recusado(tmp_path, monkeypatch):
    chave_errada = dict(CHAVE)
    chave_errada[3] = [0, 1, 2, 3]  # pergunta 3 é invertida na escala
    caminho = tmp_path / "errado.json"
    caminho.write_text(json.dumps(_arquivo(chave_errada)), encoding="utf-8")
    monkeypatch.setenv("NYMPHIA_EPDS_ARQUIVO", str(caminho))
    epds_service.recarregar()
    try:
        questionario, motivo = epds_service.questionario()
        assert questionario is None and "pergunta 3" in motivo
    finally:
        epds_service.recarregar()


def test_arquivo_sem_licenca_e_recusado(tmp_path, monkeypatch):
    monkeypatch.setenv("NYMPHIA_EPDS_JSON", json.dumps(_arquivo(licenca="")))
    epds_service.recarregar()
    try:
        questionario, motivo = epds_service.questionario()
        assert questionario is None and "licenca" in motivo
    finally:
        epds_service.recarregar()


def test_modelo_do_repositorio_nao_liga_a_triagem():
    import pathlib
    modelo = pathlib.Path(epds_service.ARQUIVO_PADRAO).with_name("epds_ptbr.exemplo.json")
    dados = json.loads(modelo.read_text(encoding="utf-8"))
    with pytest.raises(epds_service.QuestionarioIndisponivel):
        epds_service._validar(dados)  # licença vazia
    # Os pontos do modelo seguem a chave da escala
    for item in dados["itens"]:
        assert [o["pontos"] for o in item["opcoes"]] == CHAVE[item["numero"]]


# ---------------------------------------------------------------- rotas

def test_questionario_vai_sem_os_pontos(client, com_questionario):
    _, headers = _gestante(client)
    q = client.get("/epds/questionario", headers=headers).json()
    assert q["disponivel"] is True and len(q["itens"]) == 10
    assert q["itens"][0]["opcoes"] == ["Resposta 1", "Resposta 2", "Resposta 3", "Resposta 4"]
    assert "pontos" not in json.dumps(q)


def test_registro_sem_sinais_e_historico(client, com_questionario):
    _, headers = _gestante(client)
    res = client.post("/epds/respostas", json={"respostas": [3] * 10}, headers=headers)
    assert res.status_code == 201, res.text
    corpo = res.json()
    assert corpo["pontuacao"] == 9 and corpo["nivel"] == "sem_sinais" and corpo["contatos"] == []
    historico = client.get("/epds/minhas", headers=headers).json()
    assert len(historico) == 1 and historico[0]["pontuacao"] == 9
    assert client.get("/epds/status", headers=headers).json()["ultima"]["nivel"] == "sem_sinais"


def test_pensamento_de_se_machucar_avisa_a_equipe_por_email(client, com_questionario, aprovar_profissional, monkeypatch):
    enviados = []
    import app.services.notificacao_equipe as notificacao
    monkeypatch.setattr(notificacao, "enviar_email", lambda d, a, c: enviados.append((d, a, c)) or True)

    gestante_id, headers = _gestante(client)
    headers_prof = _profissional_vinculado(client, aprovar_profissional, headers)

    res = client.post("/epds/respostas", json={"respostas": [3] * 9 + [2]}, headers=headers)
    corpo = res.json()
    assert corpo["nivel"] == "urgente" and corpo["pensamento_de_se_machucar"] is True
    assert {"188", "192"} <= {c["telefone"] for c in corpo["contatos"]}
    assert corpo["equipe_vinculada"] is True

    # O e-mail não leva nome nem resposta
    assert len(enviados) == 1
    assert "Gestante EPDS" not in enviados[0][2]
    assert client.get("/epds/minhas", headers=headers).json()[0]["profissional_notificado"] is True

    # O profissional vê na ficha e a paciente sobe no painel
    ficha = client.get(f"/vinculo/paciente/{gestante_id}/ficha", headers=headers_prof).json()
    assert ficha["triagens_epds"][0]["nivel"] == "urgente"
    painel = client.get("/vinculo/minhas-gestantes", headers=headers_prof).json()
    assert painel[0]["gestante_id"] == gestante_id and painel[0]["total_alertas_30d"] >= 1


def test_sem_smtp_nao_finge_que_avisou(client, com_questionario, aprovar_profissional, monkeypatch):
    monkeypatch.delenv("SMTP_HOST", raising=False)
    _, headers = _gestante(client)
    _profissional_vinculado(client, aprovar_profissional, headers)
    client.post("/epds/respostas", json={"respostas": [3] * 9 + [0]}, headers=headers)  # pergunta 10: 3 pontos
    assert client.get("/epds/minhas", headers=headers).json()[0]["profissional_notificado"] is False


def test_parceiro_e_profissional_nao_respondem_pela_gestante(client, com_questionario, aprovar_profissional):
    _, headers = _gestante(client)
    headers_prof = _profissional_vinculado(client, aprovar_profissional, headers)
    assert client.post("/epds/respostas", json={"respostas": [3] * 10}, headers=headers_prof).status_code == 403
    assert client.get("/epds/minhas", headers=headers_prof).status_code == 403


def test_exportacao_lgpd_inclui_a_triagem(client, com_questionario):
    _, headers = _gestante(client)
    client.post("/epds/respostas", json={"respostas": [0] * 10}, headers=headers)
    exportado = client.get("/meus-dados/exportar", headers=headers).json()
    assert exportado["triagens_epds"][0]["pontuacao"] == 21
    assert "registros_antropometricos" in exportado


def test_excluir_a_conta_apaga_a_triagem(client, com_questionario, db_session):
    from app.models.clinical import TriagemEPDS
    gestante_id, headers = _gestante(client)
    client.post("/epds/respostas", json={"respostas": [0] * 10}, headers=headers)
    assert db_session.query(TriagemEPDS).filter_by(gestante_id=gestante_id).count() == 1
    assert client.delete("/minha-conta", headers=headers).status_code == 200
    assert db_session.query(TriagemEPDS).filter_by(gestante_id=gestante_id).count() == 0


# ---------------------------------------------------------------- emergência

def test_emergencia_nao_diz_que_avisou_sem_ter_enviado(client, aprovar_profissional, monkeypatch):
    monkeypatch.delenv("SMTP_HOST", raising=False)
    _, headers = _gestante(client)
    _profissional_vinculado(client, aprovar_profissional, headers)
    corpo = client.post("/emergencia/notificar", json={}, headers=headers).json()
    assert corpo["equipe_vinculada"] is True
    assert corpo["profissional_notificado"] is False


def test_emergencia_avisa_quando_o_email_sai(client, aprovar_profissional, monkeypatch):
    import app.services.notificacao_equipe as notificacao
    monkeypatch.setattr(notificacao, "enviar_email", lambda d, a, c: True)
    _, headers = _gestante(client)
    _profissional_vinculado(client, aprovar_profissional, headers)
    corpo = client.post("/emergencia/notificar", json={}, headers=headers).json()
    assert corpo["profissional_notificado"] is True
