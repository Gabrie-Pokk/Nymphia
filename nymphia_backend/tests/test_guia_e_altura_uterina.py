"""
Altura uterina com a tabela publicada do INTERGROWTH-21st e guia de nutrição
sem afirmações erradas (revisão de 15/10/2026).
"""
import json
from types import SimpleNamespace

from app.services import anthropometry_service as antropo


def _biomarcador(valores, id_):
    exames = [SimpleNamespace(valores_extraidos=valores)]
    resultado = antropo.processar_nutricao_baseada_em_exames(exames)
    return next(b for b in resultado["biomarcadores"] if b["id"] == id_)


# ---------------------------------------------------------------- altura uterina

def test_altura_uterina_usa_os_valores_publicados():
    # Tabela oficial do INTERGROWTH-21st (Papageorghiou et al., BMJ 2016)
    assert antropo.CURVA_ALTURA_UTERINA[20] == (17.8, 19.8, 21.7)
    assert antropo.CURVA_ALTURA_UTERINA[30] == (27.3, 29.6, 31.8)
    assert antropo.CURVA_ALTURA_UTERINA[40] == (35.4, 38.0, 40.5)
    assert set(antropo.CURVA_ALTURA_UTERINA) == set(range(16, 41))


def test_altura_uterina_classifica_pela_faixa():
    assert antropo.avaliar_altura_uterina(30, 26.0)["status"].startswith("Abaixo")
    dentro = antropo.avaliar_altura_uterina(30, 29.5)
    assert dentro["status"].startswith("Dentro") and dentro["p10"] == 27.3 and dentro["p90"] == 31.8
    assert antropo.avaliar_altura_uterina(30, 33.0)["status"].startswith("Acima")
    assert "INTERGROWTH-21st" in dentro["referencia"]


def test_antes_de_16_semanas_a_medida_nao_e_classificada():
    resultado = antropo.avaliar_altura_uterina(14, 12.0)
    assert resultado["p10"] is None and resultado["p90"] is None
    assert "16" in resultado["status"]


def test_depois_de_40_semanas_vale_a_faixa_da_40a():
    resultado = antropo.avaliar_altura_uterina(41, 36.0)
    assert resultado["semana_referencia"] == 40 and resultado["semana"] == 41
    assert resultado["status"].startswith("Dentro")


def test_sem_semana_ou_sem_medida_nao_ha_avaliacao():
    assert antropo.avaliar_altura_uterina(None, 25.0) is None
    assert antropo.avaliar_altura_uterina(25, None) is None


# ---------------------------------------------------------------- exames

def test_ferritina_baixa_sozinha_nao_e_chamada_de_anemia():
    bio = _biomarcador({"hemoglobina": 12.1, "ferritina": 18}, "ferro_hemoglobina")
    assert "anemia" not in bio["status"].lower()
    assert "estoque de ferro baixo" in bio["status"]


def test_hemoglobina_abaixo_de_11_e_compativel_com_anemia():
    bio = _biomarcador({"hemoglobina": 10.2}, "ferro_hemoglobina")
    assert "anemia" in bio["status"].lower()


def test_glicemia_de_jejum_segue_o_criterio_brasileiro():
    assert "abaixo de 92" in _biomarcador({"glicemia": 85}, "glicemia")["status"]
    faixa_dmg = _biomarcador({"glicemia": 95}, "glicemia")["status"]
    assert "92 e 125" in faixa_dmg and "limítrofe" not in faixa_dmg.lower()
    assert "126" in _biomarcador({"glicemia": 130}, "glicemia")["status"]


def test_vitamina_d_usa_a_referencia_das_sociedades_brasileiras():
    assert "deficiência" in _biomarcador({"vitamina_d": 15}, "vitamina_d")["status"]
    assert "abaixo de 30" in _biomarcador({"vitamina_d": 25}, "vitamina_d")["status"]
    assert "dentro do recomendado" in _biomarcador({"vitamina_d": 35}, "vitamina_d")["status"]


def test_tsh_nao_recebe_faixa_inventada():
    status = _biomarcador({"tsh": 3.4}, "tsh_tireoide")["status"]
    assert "equipe" in status and "trimestre" in status


def test_guia_nao_manda_tomar_sol_sem_protetor_nem_parar_acido_folico_na_12a_semana():
    texto = json.dumps(antropo.obter_guia_educativo_antropometria([]), ensure_ascii=False).lower()
    assert "sem protetor" not in texto
    assert "até a 12ª semana" not in texto
    assert chr(0x2014) not in texto and chr(0x2013) not in texto  # sem travessão
