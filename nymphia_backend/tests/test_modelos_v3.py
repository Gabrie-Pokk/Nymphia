"""
Modelos v3 (15/10/2026): fatores clínicos que o DATASUS não registra entram por
simulação, com efeitos publicados (scripts/gerar_base_sintetica.py e
scripts/treinar_modelos_v3.py). O app declara a simulação e nunca inventa dado.
"""
import math
import uuid
from datetime import date, timedelta

import pytest

from app.services import ai_risk_service as risco


@pytest.fixture(scope="module", autouse=True)
def modelos_reais():
    risco._modelos_estado.update({"carregado": False, "modelos": {}, "atipicidade": None, "metricas": None,
                                  "metricas_v3": None})
    risco.carregar_modelos_ml()
    yield


BASE = {
    "idade": 30, "estado_civil": "Casada / União Estável", "escolaridade": "Médio Completo",
    "gestacoes_anteriores": 1, "partos_normais": 1, "partos_cesareos": 0, "perdas_gestacionais": 0,
    "numero_fetos": 1, "mes_inicio_prenatal": 2, "uf_residencia": 35,
    "pre_eclampsia_previa": False, "hipertensao_cronica": False, "diabetes_previo": False,
    "historico_familiar_pe": False, "historico_familiar_dm": False, "imc_pre_gestacional": 22.0,
}


def _cond(perfil, nome, historico=None):
    return risco.calculate_maternal_risks(perfil, historico or [])["condicoes"][nome]


def test_versoes_carregadas():
    modelos = risco._modelos_estado["modelos"]
    for nome in ("bem_estar_fetal", "pre_eclampsia", "eclampsia", "diabetes_gestacional"):
        assert modelos[nome]["versao"] == "3.0" and modelos[nome]["simulado"] is True
    assert modelos["malformacao"]["versao"] == "3.0" and modelos["malformacao"]["simulado"] is False
    assert modelos["eclampsia"]["derivado_de"] == "pre_eclampsia"
    assert modelos["itu"]["confiavel"] is False


def test_pressao_alta_de_antes_aumenta_a_pre_eclampsia_como_nos_estudos():
    sem = _cond(BASE, "pre_eclampsia")["probabilidade"]
    com = _cond({**BASE, "hipertensao_cronica": True}, "pre_eclampsia")["probabilidade"]
    # Bartsch 2016: 5,1 vezes; o modelo devolve perto disso
    assert 3.5 < com / sem < 7


def test_fator_alto_nunca_aparece_como_risco_habitual():
    pe = _cond({**BASE, "hipertensao_cronica": True}, "pre_eclampsia")
    assert pe["nivel"] == "alto"
    assert pe["motivo_nivel"] in ("diretriz", "modelo")


def test_dois_fatores_moderados_dao_risco_aumentado():
    pe = _cond({**BASE, "idade": 36, "gestacoes_anteriores": 0, "partos_normais": 0}, "pre_eclampsia")
    assert pe["nivel"] in ("moderado", "alto")


def test_nao_sei_vira_media_e_nao_risco_alto():
    resultado = risco.calculate_maternal_risks({"idade": 30}, [])
    assert all(c["nivel"] in (None, "baixo") for c in resultado["condicoes"].values())
    bem_estar = resultado["condicoes"]["bem_estar_fetal"]
    assert 0.10 < bem_estar["probabilidade"] < 0.22  # média real do SINASC: 15,6%
    assert "pressão alta antes da gravidez" in bem_estar["dados_faltantes"]


def test_sem_idade_nenhuma_estimativa():
    resultado = risco.calculate_maternal_risks({"uf_residencia": 35}, [])
    for c in resultado["condicoes"].values():
        assert c["probabilidade"] is None


def test_diabetes_gestacional_nao_se_aplica_a_quem_ja_tinha_diabetes():
    dmg = _cond({**BASE, "diabetes_previo": True}, "diabetes_gestacional")
    assert dmg["fonte"] == "nao_se_aplica" and dmg["probabilidade"] is None


def test_eclampsia_e_uma_parte_da_pre_eclampsia():
    resultado = risco.calculate_maternal_risks({**BASE, "pre_eclampsia_previa": True}, [])
    pe = resultado["condicoes"]["pre_eclampsia"]["probabilidade"]
    ecl = resultado["condicoes"]["eclampsia"]["probabilidade"]
    assert 0.02 < ecl / pe < 0.4


def test_historico_familiar_sim_nao_e_nao_sei():
    assert risco.montar_variaveis({**BASE, "historico_familiar_dm": True})["historico_familiar_dm"] == 1.0
    assert risco.montar_variaveis({**BASE, "historico_familiar_dm": False})["historico_familiar_dm"] == 0.0
    assert math.isnan(risco.montar_variaveis({"idade": 30})["historico_familiar_dm"])
    # A lista do histórico familiar só confirma o sim
    hist = [{"parente": "mãe", "condicao": "Pré-eclâmpsia"}, {"parente": "avó materna", "condicao": "Diabetes tipo 2"}]
    variaveis = risco.montar_variaveis({"idade": 30}, hist)
    assert variaveis["historico_familiar_pe"] == 1.0 and variaveis["historico_familiar_dm"] == 1.0


def test_categoria_do_imc():
    assert [risco.categoria_imc(v) for v in (17.9, 22, 27, 31)] == [1.0, 2.0, 3.0, 4.0]
    assert math.isnan(risco.categoria_imc(None))


def test_transparencia_declara_a_simulacao_e_mostra_so_desempenho_real():
    t = risco.obter_transparencia_clinica()
    assert t["versao_modelos"] == "3.0"
    pe = t["modelos"]["pre_eclampsia"]
    assert pe["simulado"] is True and pe["efeitos_dos_fatores"]["hipertensao_cronica"]["fonte"] == "bartsch2016"
    real = risco._modelos_estado["metricas_v3"]["modelos"]["pre_eclampsia"]["conferencia_em_dados_reais"]
    assert pe["auc_roc"] == real["v3"]["auc_roc"]
    assert t["modelos"]["malformacao"]["simulado"] is False
    assert t["simulacao"]["fontes"]["bartsch2016"].startswith("Bartsch")


def test_cadastro_salva_as_respostas_de_historico_familiar(client):
    cad = client.post("/auth/gestante/cadastro", json={
        "nome": "Gestante Familia", "email": f"familia_{uuid.uuid4().hex[:8]}@teste.com", "senha": "senhaSegura123",
        "aceite_termos": True, "consentimento_dados_saude": True,
    })
    headers = {"Authorization": f"Bearer {cad.json()['token']}"}
    dum = date.today() - timedelta(days=12 * 7)
    criado = client.post("/perfil-clinico", headers=headers, json={
        "idade": 29, "gestacoes_anteriores": 0, "partos_normais": 0, "partos_cesareos": 0, "perdas_gestacionais": 0,
        "dum": dum.isoformat(), "dpp": (dum + timedelta(days=280)).isoformat(), "historico_familiar_pe": True,
    })
    assert criado.status_code == 201, criado.text
    assert criado.json()["historico_familiar_pe"] is True
    alterado = client.put("/perfil-clinico", headers=headers, json={"historico_familiar_dm": False})
    assert alterado.status_code == 200 and alterado.json()["historico_familiar_dm"] is False
    resultado = client.get("/risco/meu-risco", headers=headers).json()
    assert any(f["fator"] == "Mãe ou irmã com pré-eclâmpsia" for f in resultado["fatores_clinicos"])
