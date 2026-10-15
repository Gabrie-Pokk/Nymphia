"""
Modelos de risco v2 (15/10/2026): só o que se sabe na gestação, nada inventado,
probabilidade calibrada e risco relativo para os modelos de caso-controle do SIH.
"""
import uuid
from datetime import date, timedelta

import pytest

from app.services import ai_risk_service as risco


@pytest.fixture(scope="module", autouse=True)
def modelos_reais():
    risco._modelos_estado.update({"carregado": False, "modelos": {}, "atipicidade": None, "metricas": None})
    risco.carregar_modelos_ml()
    assert set(risco._modelos_estado["modelos"]) == set(risco.NOMES_MODELOS)
    yield


PERFIL_COMUM = {
    "idade": 27, "estado_civil": "Casada / União Estável", "escolaridade": "Médio Completo",
    "gestacoes_anteriores": 1, "partos_normais": 1, "partos_cesareos": 0, "perdas_gestacionais": 0,
    "numero_fetos": 1, "mes_inicio_prenatal": 2, "uf_residencia": 35,
}


def test_nada_do_parto_entra_nos_modelos():
    proibidas = {"APGAR1", "APGAR5", "PESO", "SEMAGESTAC", "GESTACAO", "PARTO", "LOCNASC", "CONSULTAS", "SEXO",
                 "MUNIC_RES", "leitos_obst_compl_exist", "leitos_obst_compl_sus"}
    for pacote in risco._modelos_estado["modelos"].values():
        assert not proibidas & set(pacote["features"])


def test_perfil_comum_fica_perto_da_media():
    resultado = risco.calculate_maternal_risks(PERFIL_COMUM, [])
    bem_estar = resultado["condicoes"]["bem_estar_fetal"]
    assert bem_estar["tipo_saida"] == "probabilidade"
    assert 0.08 < bem_estar["probabilidade"] < 0.25  # média do SINASC: 15,5%
    assert bem_estar["dados_faltantes"] == []


def test_gemeos_aumentam_a_chance_de_prematuridade():
    unico = risco.calculate_maternal_risks(PERFIL_COMUM, [])["condicoes"]["bem_estar_fetal"]["probabilidade"]
    gemeos = risco.calculate_maternal_risks({**PERFIL_COMUM, "numero_fetos": 2}, [])
    assert gemeos["condicoes"]["bem_estar_fetal"]["probabilidade"] > 2 * unico
    assert gemeos["condicoes"]["bem_estar_fetal"]["nivel"] == "alto"


def test_modelos_do_sih_mostram_risco_relativo_e_nao_porcentagem():
    pe = risco.calculate_maternal_risks(PERFIL_COMUM, [])["condicoes"]["pre_eclampsia"]
    assert pe["tipo_saida"] == "risco_relativo"
    assert pe["probabilidade"] is None
    assert pe["risco_relativo"] > 0


def test_dado_nao_informado_fica_desconhecido_e_e_avisado():
    resultado = risco.calculate_maternal_risks({"idade": 30}, [])
    faltam = resultado["condicoes"]["bem_estar_fetal"]["dados_faltantes"]
    assert "número de bebês" in faltam and "mês em que começou o pré-natal" in faltam
    assert resultado["condicoes"]["pre_eclampsia"]["dados_faltantes"] == ["estado onde mora"]


def test_itu_fica_indisponivel_com_o_motivo():
    itu = risco.calculate_maternal_risks(PERFIL_COMUM, [])["condicoes"]["itu"]
    assert itu["fonte"] == "indisponivel" and itu["nivel"] is None
    assert "O23" in itu["motivo"]


def test_fatores_clinicos_com_efeito_publicado():
    perfil = {**PERFIL_COMUM, "hipertensao_cronica": True, "imc_pre_gestacional": 31.2}
    historico = [{"parente": "mãe", "condicao": "Pré-eclâmpsia"}]
    resultado = risco.calculate_maternal_risks(perfil, historico)
    por_fator = {f["fator"]: f for f in resultado["fatores_clinicos"]}
    assert por_fator["Pressão alta desde antes da gravidez"]["risco_relativo_publicado"] == 5.1
    assert por_fator["Mãe ou irmã com pré-eclâmpsia"]["risco_relativo_publicado"] == 2.90
    assert resultado["prevencao_pre_eclampsia"]["altos"] == 1
    assert "AAS" in resultado["prevencao_pre_eclampsia"]["mensagem"]


def test_sem_fatores_nao_ha_mensagem_de_prevencao():
    assert risco.calculate_maternal_risks(PERFIL_COMUM, [])["prevencao_pre_eclampsia"] is None


def test_meu_risco_usa_o_cadastro_completo(client):
    cad = client.post("/auth/gestante/cadastro", json={
        "nome": "Gestante Modelos", "email": f"modelos_{uuid.uuid4().hex[:8]}@teste.com", "senha": "senhaSegura123",
        "aceite_termos": True, "consentimento_dados_saude": True,
    })
    headers = {"Authorization": f"Bearer {cad.json()['token']}"}
    dum = date.today() - timedelta(days=20 * 7)
    res = client.post("/perfil-clinico", headers=headers, json={
        "idade": 31, "estado_civil": "Solteira", "escolaridade": "Superior Completo",
        "gestacoes_anteriores": 0, "partos_normais": 0, "partos_cesareos": 0, "perdas_gestacionais": 0,
        "numero_fetos": 1, "mes_inicio_prenatal": 2, "uf_residencia": 29, "pre_eclampsia_previa": False,
        "dum": dum.isoformat(), "dpp": (dum + timedelta(days=280)).isoformat(),
    })
    assert res.status_code == 201, res.text
    resultado = client.get("/risco/meu-risco", headers=headers).json()
    assert resultado["versao_modelos"] == "2.0"
    assert resultado["condicoes"]["bem_estar_fetal"]["dados_faltantes"] == []
    assert any(f["fator"].startswith("Primeiro parto") for f in resultado["fatores_clinicos"])


def test_sem_cadastro_clinico_nada_e_inventado(client):
    cad = client.post("/auth/gestante/cadastro", json={
        "nome": "Gestante Sem Cadastro", "email": f"sem_{uuid.uuid4().hex[:8]}@teste.com", "senha": "senhaSegura123",
        "aceite_termos": True, "consentimento_dados_saude": True,
    })
    headers = {"Authorization": f"Bearer {cad.json()['token']}"}
    resultado = client.get("/risco/meu-risco", headers=headers).json()
    assert resultado["cadastro_clinico_completo"] is False
    assert "idade" in resultado["condicoes"]["pre_eclampsia"]["dados_faltantes"]
