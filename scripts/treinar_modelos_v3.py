#!/usr/bin/env python3
"""
Treino v3 dos modelos de risco da Nymphia (15/10/2026).

Entrada: pipeline_data/base_sintetica_v3.parquet, feita por
scripts/gerar_base_sintetica.py (perfis reais do SINASC + fatores clínicos com
prevalências brasileiras e efeitos publicados; fontes no arquivo de parâmetros).

O que este treino faz:
  1. Treina na base sintética: prematuridade/baixo peso (desfecho real do
     SINASC, fatores simulados), pré-eclâmpsia e diabetes gestacional
     (desfechos simulados). Eclâmpsia sai da pré-eclâmpsia vezes a fração de
     eclâmpsia por idade e região do SIH real, a mesma regra do gerador.
  2. Malformação: mesmos dados reais da v2 (sem fator simulado), retreinada só
     para lidar com "não sei". ITU e atipicidade continuam na v2.
  3. Esconde parte das respostas no treino (35% de cada fator clínico, 20% de
     cada variável do perfil), para "não sei" virar a média de quem respondeu,
     e não um padrão de registro incompleto do DATASUS.
  4. Calibra a probabilidade (isotônica) numa parte separada.
  5. Confere em DADOS REAIS que não entraram no treino, com os fatores
     desconhecidos (o DATASUS não os registra), comparando com a v2 nas mesmas
     gestantes ou internações.
  6. Confere a construção: o efeito que o modelo devolve para cada fator,
     comparado com o efeito publicado que entrou no gerador.

O que NÃO sai daqui: AUC na própria base sintética. Ela mediria as regras que
nós escrevemos, não o desempenho em gestantes reais.

Saída (nymphia_backend/modelos):
  risco_<condicao>.joblib (v3) e metricas_modelos_v3.json

Uso:  python scripts/treinar_modelos_v3.py
"""
import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.frozen import FrozenEstimator
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import train_test_split

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import gerar_base_sintetica as gerador  # noqa: E402
import treinar_modelos_v2 as v2  # noqa: E402

DADOS = RAIZ / "pipeline_data"
SAIDA = RAIZ / "nymphia_backend" / "modelos"
MODELOS_V2 = SAIDA / "v2"
SEMENTE = 42
FRACAO_FATOR = 0.35   # parte de cada fator clínico escondida no treino
FRACAO_PERFIL = 0.20  # parte de cada variável do perfil escondida no treino
SENSIBILIDADE_ALVO = 0.80

FATORES = ["pre_eclampsia_previa", "hipertensao_cronica", "diabetes_previo", "imc_categoria",
           "historico_familiar_pe", "historico_familiar_dm"]

GRUPOS_SINASC = [["estado_civil"], ["escolaridade"], ["gestacoes_anteriores"], ["partos_normais", "partos_cesareos"],
                 ["perdas_anteriores"], ["fetos"], ["mes_inicio_prenatal"]]

# Variáveis de cada modelo: o perfil que o desfecho usa de verdade e os fatores com efeito publicado.
# A região entra só onde vem de dado real (SIH); na base sintética ela foi sorteada para os desfechos do SINASC.
MODELOS = {
    "bem_estar_fetal": {
        "variaveis": v2.VARIAVEIS_SINASC + ["hipertensao_cronica", "diabetes_previo"],
        "categoricas": ["estado_civil"],
        "grupos_do_perfil": GRUPOS_SINASC,
        "desfecho": "real (SINASC); só os fatores clínicos são simulados",
    },
    "pre_eclampsia": {
        "variaveis": ["idade", "regiao", "fetos", "partos_normais", "partos_cesareos", "pre_eclampsia_previa",
                      "hipertensao_cronica", "diabetes_previo", "imc_categoria", "historico_familiar_pe"],
        "categoricas": ["regiao", "imc_categoria"],
        "grupos_do_perfil": [["regiao"], ["partos_normais", "partos_cesareos"], ["fetos"]],
        "desfecho": "simulado: risco por idade e região do SIH real, incidência média de 3% e efeitos publicados",
    },
    "diabetes_gestacional": {
        "variaveis": ["idade", "regiao", "gestacoes_anteriores", "imc_categoria", "historico_familiar_dm"],
        "categoricas": ["regiao", "imc_categoria"],
        "grupos_do_perfil": [["regiao"], ["gestacoes_anteriores"]],
        "desfecho": "simulado: risco por idade e região do SIH real, prevalência média de 14% e efeitos publicados",
    },
}

# Efeito que deve voltar do modelo, para a conferência de construção: (coluna, valor com, valor sem)
CONFERIR_EFEITOS = {
    "bem_estar_fetal": {"hipertensao_cronica": ("hipertensao_cronica", 1, 0), "diabetes_previo": ("diabetes_previo", 1, 0)},
    "pre_eclampsia": {
        "pre_eclampsia_previa": ("pre_eclampsia_previa", 1, 0), "hipertensao_cronica": ("hipertensao_cronica", 1, 0),
        "diabetes_previo": ("diabetes_previo", 1, 0), "imc_baixo_peso": ("imc_categoria", 1, 2),
        "imc_sobrepeso": ("imc_categoria", 3, 2), "imc_obesidade": ("imc_categoria", 4, 2),
        "gemeos": ("fetos", 2, 1), "historico_familiar_pe": ("historico_familiar_pe", 1, 0),
    },
    "diabetes_gestacional": {
        "imc_baixo_peso": ("imc_categoria", 1, 2), "imc_sobrepeso": ("imc_categoria", 3, 2),
        "imc_obesidade": ("imc_categoria", 4, 2), "historico_familiar_dm": ("historico_familiar_dm", 1, 0),
    },
}


# ---------------------------------------------------------------------------
# Ferramentas
# ---------------------------------------------------------------------------
def _como_categoria(x, categoricas, categorias=None):
    x = x.copy()
    for coluna in categoricas:
        if categorias is not None:
            x[coluna] = pd.Categorical(x[coluna], categories=categorias[coluna])
        else:
            x[coluna] = x[coluna].astype("category")
    return x


def _esconder(x, rng, grupos=()):
    """Esconde parte das respostas: o modelo aprende que "não sei" é a média de quem respondeu."""
    x = x.copy()
    for coluna in FATORES:
        if coluna in x.columns:
            x.loc[rng.random(len(x)) < FRACAO_FATOR, coluna] = np.nan
    for grupo in grupos:
        x.loc[rng.random(len(x)) < FRACAO_PERFIL, list(grupo)] = np.nan
    return x


def _prever(pacote, x):
    tabela = x.reindex(columns=pacote["features"]).astype(float)
    tabela = _como_categoria(tabela, pacote.get("categoricas", []), pacote.get("categorias"))
    return pacote["modelo"].predict_proba(tabela)[:, 1]


def _treinar_calibrado(x_treino, y_treino, x_calib, y_calib, categoricas):
    x_treino_c = _como_categoria(x_treino, categoricas)
    categorias = {c: [float(v) for v in x_treino_c[c].cat.categories] for c in categoricas}
    modelo = HistGradientBoostingClassifier(
        max_iter=400, learning_rate=0.06, max_leaf_nodes=31, min_samples_leaf=200, l2_regularization=1.0,
        categorical_features="from_dtype", early_stopping=True, validation_fraction=0.1, n_iter_no_change=20,
        random_state=SEMENTE,
    )
    modelo.fit(x_treino_c, y_treino)
    calibrado = CalibratedClassifierCV(FrozenEstimator(modelo), method="isotonic")
    calibrado.fit(_como_categoria(x_calib, categoricas, categorias), y_calib)
    return calibrado, categorias


def _dividir(x, y):
    """60/20/20 estratificado, semente 42 (a mesma divisão da v2 quando os dados são os mesmos)."""
    x_treino, x_resto, y_treino, y_resto = train_test_split(x, y, test_size=0.4, stratify=y, random_state=SEMENTE)
    x_calib, x_teste, y_calib, y_teste = train_test_split(x_resto, y_resto, test_size=0.5, stratify=y_resto,
                                                          random_state=SEMENTE)
    return x_treino, y_treino, x_calib, y_calib, x_teste, y_teste


def _indices_teste_v2(y):
    indices = np.arange(len(y))
    _, resto, _, y_resto = train_test_split(indices, y, test_size=0.4, stratify=y, random_state=SEMENTE)
    _, teste, _, _ = train_test_split(resto, y_resto, test_size=0.5, stratify=y_resto, random_state=SEMENTE)
    return teste


def _resumo_real(y, p):
    return {
        "n": int(len(y)), "casos": int(y.sum()),
        "auc_roc": round(float(roc_auc_score(y, p)), 4),
        "brier": round(float(brier_score_loss(y, p)), 5),
        "erro_calibracao_esperado": round(float(v2._ece(y, p)), 5),
        "probabilidade_media_prevista": round(float(p.mean()), 5),
        "frequencia_observada": round(float(y.mean()), 5),
    }


def _so_idade(x):
    """Mesmas gestantes, mas com tudo desconhecido menos a idade: a média tem de continuar perto da real."""
    vazio = x.copy()
    for coluna in vazio.columns:
        if coluna != "idade":
            vazio[coluna] = np.nan
    return vazio


def _efeitos_recuperados(pacote, x_teste, nome, efeitos_publicados):
    """Razão de chances que o modelo devolve (mediana entre gestantes), comparada com a que entrou no gerador."""
    resultado = {}
    for fator, (coluna, com, sem) in CONFERIR_EFEITOS.get(nome, {}).items():
        x = x_teste
        if fator == "pre_eclampsia_previa":  # só faz sentido para quem já teve parto
            x = x_teste[(x_teste["partos_normais"].fillna(0) + x_teste["partos_cesareos"].fillna(0)) > 0]
        amostra = x.sample(min(len(x), 40_000), random_state=SEMENTE)
        a = amostra.copy(); a[coluna] = com
        b = amostra.copy(); b[coluna] = sem
        p1 = np.clip(_prever(pacote, a), 1e-6, 1 - 1e-6)
        p0 = np.clip(_prever(pacote, b), 1e-6, 1 - 1e-6)
        razao = (p1 / (1 - p1)) / (p0 / (1 - p0))
        publicado = efeitos_publicados.get(fator, {})
        resultado[fator] = {
            "razao_de_chances_publicada": publicado.get("razao_de_chances"),
            "fonte": publicado.get("fonte"),
            "razao_de_chances_no_modelo": round(float(np.median(razao)), 2),
            "risco_relativo_no_modelo": round(float(np.median(p1 / p0)), 2),
        }
    return resultado


# ---------------------------------------------------------------------------
# Eclâmpsia: pré-eclâmpsia vezes a fração de eclâmpsia por idade e região (SIH real)
# ---------------------------------------------------------------------------
def fracao_eclampsia():
    modelo, _, fracao_media, casos = gerador.modelo_fracao_eclampsia()
    coef = [float(c) for c in modelo.coef_[0]]
    return {
        "intercepto": float(modelo.intercept_[0]),
        "idade_centro": 27.0, "idade_escala": 7.0, "idade_min": 12.0, "idade_max": 50.0,
        "coef_idade": coef[0], "coef_idade2": coef[1],
        "coef_regiao": {"1": coef[2], "2": coef[3], "4": coef[4], "5": coef[5]},  # Sudeste (3) é a referência
        "pesos_regiao": {str(int(k)): float(v) for k, v in gerador.distribuicao_regioes().items()},
        "fracao_media": float(fracao_media),
        "casos_sih": int(casos),
    }


def prever_fracao(fr, x):
    """Mesma conta do app (ai_risk_service._fracao_eclampsia), em vetor."""
    n = len(x)
    idade = x["idade"].to_numpy(dtype=float) if "idade" in x else np.full(n, np.nan)
    regiao = x["regiao"].to_numpy(dtype=float) if "regiao" in x else np.full(n, np.nan)
    z = (np.clip(idade, fr["idade_min"], fr["idade_max"]) - fr["idade_centro"]) / fr["idade_escala"]

    def q_para(reg):
        logit = fr["intercepto"] + fr["coef_idade"] * z + fr["coef_idade2"] * z ** 2
        for r, c in fr["coef_regiao"].items():
            logit = logit + c * (reg == float(r))
        return 1.0 / (1.0 + np.exp(-logit))

    media_regioes = sum(w * q_para(np.full(n, float(r))) for r, w in fr["pesos_regiao"].items())
    q = np.where(np.isnan(regiao), media_regioes, q_para(regiao))
    return np.where(np.isnan(idade), fr["fracao_media"], q)


def prever_eclampsia(pacote_ecl, pacote_pe, x):
    return _prever(pacote_pe, x) * prever_fracao(pacote_ecl["fracao"], x)


# ---------------------------------------------------------------------------
# Conferências em dados reais
# ---------------------------------------------------------------------------
def conferir_sinasc(pacote_v3, sinasc):
    """Prematuridade/baixo peso em registros reais que nem a v2 nem a v3 viram no treino."""
    x, y = sinasc["bem_estar_fetal"]
    y = y.to_numpy()
    rng = np.random.default_rng(gerador.SEMENTE)
    reserva = rng.permutation(len(x))[: int(len(x) * gerador.FRACAO_RESERVA)]  # mesma reserva do gerador
    comum = np.intersect1d(reserva, _indices_teste_v2(y))
    pacote_v2 = joblib.load(MODELOS_V2 / "risco_bem_estar_fetal.joblib")
    x_comum, y_comum = x.iloc[comum], y[comum]
    p3, p2 = _prever(pacote_v3, x_comum), _prever(pacote_v2, x_comum)
    return {
        "dados": "SINASC real: registros fora do treino da v3 e da v2 (os fatores clínicos ficam desconhecidos)",
        "v3": {**_resumo_real(y_comum, p3), "ponto_fn_primeiro": v2._ponto_de_corte(y_comum, p3, SENSIBILIDADE_ALVO),
               "calibracao_por_decil": v2._tabela_calibracao(y_comum, p3)},
        "v2_nas_mesmas_gestantes": _resumo_real(y_comum, p2),
        "so_com_a_idade": {
            "v3_media_prevista": round(float(_prever(pacote_v3, _so_idade(x_comum)).mean()), 5),
            "v2_media_prevista": round(float(_prever(pacote_v2, _so_idade(x_comum)).mean()), 5),
            "frequencia_observada": round(float(y_comum.mean()), 5),
        },
    }


def conferir_sih(nome, prever_v3):
    """Na mesma parte de teste real do SIH usada na v2 (só idade e região; fatores desconhecidos)."""
    x, y = v2.preparar_sih()[nome]
    y = y.to_numpy()
    teste = _indices_teste_v2(y)
    pacote_v2 = joblib.load(MODELOS_V2 / f"risco_{nome}.joblib")
    x_teste, y_teste = x.iloc[teste], y[teste]
    p3, p2 = prever_v3(x_teste), _prever(pacote_v2, x_teste)
    return {
        "dados": ("SIH 2022 real, mesma parte de teste da v2 (caso-controle: só a ordenação vale, a "
                  "porcentagem não; os fatores clínicos ficam desconhecidos)"),
        "v3": {"n": int(len(y_teste)), "casos": int(y_teste.sum()), "auc_roc": round(float(roc_auc_score(y_teste, p3)), 4),
               "ponto_fn_primeiro": {k: v for k, v in v2._ponto_de_corte(y_teste, p3, SENSIBILIDADE_ALVO).items()
                                     if k in ("limiar", "sensibilidade", "especificidade")}},
        "v2_nas_mesmas_internacoes": {"auc_roc": round(float(roc_auc_score(y_teste, p2)), 4)},
    }


# ---------------------------------------------------------------------------
# Treinos
# ---------------------------------------------------------------------------
def treinar_sintetico(nome, base, parametros, sinasc):
    inicio = time.time()
    cfg = MODELOS[nome]
    dados = base[base[nome].notna()]
    x_treino, y_treino, x_calib, y_calib, x_teste, _ = _dividir(dados[cfg["variaveis"]], dados[nome].astype(int))
    rng = np.random.default_rng(SEMENTE)
    x_treino = _esconder(x_treino, rng, cfg["grupos_do_perfil"])
    x_calib = _esconder(x_calib, rng, cfg["grupos_do_perfil"])
    calibrado, categorias = _treinar_calibrado(x_treino, y_treino, x_calib, y_calib, cfg["categoricas"])
    pacote = {
        "versao": "3.0", "condicao": nome,
        "base": "Base sintética v3 (perfis reais do SINASC e fatores clínicos com efeitos publicados)",
        "simulado": True, "desfecho": cfg["desfecho"], "modelo": calibrado,
        "features": cfg["variaveis"], "categoricas": cfg["categoricas"], "categorias": categorias,
        "tipo_saida": "probabilidade", "treinado_em": time.strftime("%Y-%m-%d"), "sklearn": sklearn.__version__,
    }
    pacote["media_referencia"] = float(_prever(pacote, x_calib).mean())
    metricas = {
        "condicao": nome, "variaveis": cfg["variaveis"], "desfecho": cfg["desfecho"],
        "n_treino": int(len(y_treino)), "n_calibracao": int(len(y_calib)),
        "fracao_escondida_no_treino": {"fatores_clinicos": FRACAO_FATOR, "perfil": FRACAO_PERFIL},
        "media_referencia": round(pacote["media_referencia"], 5),
        "efeitos_recuperados": _efeitos_recuperados(pacote, x_teste, nome, parametros["efeitos"].get(nome, {})),
    }
    if nome == "bem_estar_fetal":
        metricas["conferencia_em_dados_reais"] = conferir_sinasc(pacote, sinasc)
    else:
        metricas["conferencia_em_dados_reais"] = conferir_sih(nome, lambda x: _prever(pacote, x))
    metricas["segundos"] = round(time.time() - inicio, 1)
    pacote["metricas"] = {"auc_roc": metricas["conferencia_em_dados_reais"]["v3"]["auc_roc"]}
    return pacote, metricas, x_calib


def montar_eclampsia(pacote_pe, x_calib_pe):
    fr = fracao_eclampsia()
    pacote = {
        "versao": "3.0", "condicao": "eclampsia",
        "base": "Pré-eclâmpsia v3 vezes a fração de eclâmpsia por idade e região (SIH 2022 real)",
        "simulado": True,
        "desfecho": "simulado: parte das pré-eclâmpsias, na proporção por idade e região do SIH real",
        "derivado_de": "pre_eclampsia", "fracao": fr,
        "features": pacote_pe["features"], "tipo_saida": "probabilidade",
        "treinado_em": time.strftime("%Y-%m-%d"), "sklearn": sklearn.__version__,
    }
    pacote["media_referencia"] = float(prever_eclampsia(pacote, pacote_pe, x_calib_pe).mean())
    metricas = {
        "condicao": "eclampsia", "variaveis": pacote_pe["features"], "desfecho": pacote["desfecho"],
        "regra": "probabilidade de pré-eclâmpsia (v3) vezes a fração de eclâmpsia por idade e região",
        "fracao_media_no_sih": round(fr["fracao_media"], 4), "casos_no_sih": fr["casos_sih"],
        "media_referencia": round(pacote["media_referencia"], 6),
        "conferencia_em_dados_reais": conferir_sih("eclampsia", lambda x: prever_eclampsia(pacote, pacote_pe, x)),
    }
    pacote["metricas"] = {"auc_roc": metricas["conferencia_em_dados_reais"]["v3"]["auc_roc"]}
    return pacote, metricas


def treinar_malformacao(sinasc):
    """Mesmos dados reais da v2; a única mudança é aprender "não sei" escondendo respostas no treino."""
    inicio = time.time()
    x, y = sinasc["malformacao"]
    x_treino, y_treino, x_calib, y_calib, x_teste, y_teste = _dividir(x[v2.VARIAVEIS_SINASC], y.astype(int))
    rng = np.random.default_rng(SEMENTE)
    x_treino, x_calib = _esconder(x_treino, rng, GRUPOS_SINASC), _esconder(x_calib, rng, GRUPOS_SINASC)
    calibrado, categorias = _treinar_calibrado(x_treino, y_treino, x_calib, y_calib, ["estado_civil"])
    pacote = {
        "versao": "3.0", "condicao": "malformacao", "base": "SINASC (coorte de nascidos vivos)", "simulado": False,
        "desfecho": "real (SINASC)", "modelo": calibrado, "features": v2.VARIAVEIS_SINASC,
        "categoricas": ["estado_civil"], "categorias": categorias, "tipo_saida": "probabilidade",
        "treinado_em": time.strftime("%Y-%m-%d"), "sklearn": sklearn.__version__,
    }
    pacote["media_referencia"] = float(_prever(pacote, x_calib).mean())
    yt = y_teste.to_numpy()
    p3 = _prever(pacote, x_teste)
    pacote_v2 = joblib.load(MODELOS_V2 / "risco_malformacao.joblib")
    p2 = _prever(pacote_v2, x_teste)
    metricas = {
        "condicao": "malformacao", "variaveis": v2.VARIAVEIS_SINASC, "desfecho": "real (SINASC)",
        "n_treino": int(len(y_treino)), "n_calibracao": int(len(y_calib)),
        "fracao_escondida_no_treino": {"perfil": FRACAO_PERFIL},
        "media_referencia": round(pacote["media_referencia"], 5),
        "conferencia_em_dados_reais": {
            "dados": "SINASC real, mesma parte de teste da v2",
            "v3": {**_resumo_real(yt, p3), "ponto_fn_primeiro": v2._ponto_de_corte(yt, p3, SENSIBILIDADE_ALVO)},
            "v2_nas_mesmas_gestantes": _resumo_real(yt, p2),
            "so_com_a_idade": {
                "v3_media_prevista": round(float(_prever(pacote, _so_idade(x_teste)).mean()), 5),
                "v2_media_prevista": round(float(_prever(pacote_v2, _so_idade(x_teste)).mean()), 5),
                "frequencia_observada": round(float(yt.mean()), 5),
            },
        },
        "segundos": round(time.time() - inicio, 1),
    }
    pacote["metricas"] = {"auc_roc": metricas["conferencia_em_dados_reais"]["v3"]["auc_roc"]}
    return pacote, metricas


def _mostrar(nome, metricas):
    real = metricas["conferencia_em_dados_reais"]
    v2_real = real.get("v2_nas_mesmas_gestantes") or real.get("v2_nas_mesmas_internacoes")
    print(f"  {nome}: dados reais AUC v3 {real['v3']['auc_roc']} x v2 {v2_real['auc_roc']}", flush=True)
    if "so_com_a_idade" in real:
        s = real["so_com_a_idade"]
        print(f"    só com a idade: v3 {s['v3_media_prevista']} v2 {s['v2_media_prevista']} real {s['frequencia_observada']}",
              flush=True)
    for fator, e in metricas.get("efeitos_recuperados", {}).items():
        print(f"    {fator}: publicado {e['razao_de_chances_publicada']}, modelo {e['razao_de_chances_no_modelo']}",
              flush=True)


def main():
    parametros = json.loads((DADOS / "base_sintetica_v3_parametros.json").read_text(encoding="utf-8"))
    print("Lendo a base sintética e o SINASC real...", flush=True)
    base = pd.read_parquet(DADOS / "base_sintetica_v3.parquet")
    sinasc = v2.preparar_sinasc()
    todas = {
        "gerado_em": time.strftime("%Y-%m-%d %H:%M"),
        "sklearn": sklearn.__version__,
        "base_sintetica": {
            "versao": parametros["versao"], "linhas": parametros["linhas"], "semente": parametros["semente"],
            "fontes": parametros["fontes"], "prevalencias": parametros["prevalencias"],
            "incidencias": parametros["incidencias"], "efeitos": parametros["efeitos"],
            "suposicoes": parametros["suposicoes"],
        },
        "aviso": ("Os modelos v3 aprendem os efeitos publicados que entraram no gerador. A AUC na própria base "
                  "sintética não foi calculada de propósito: mediria as nossas regras, não o desempenho em "
                  "gestantes reais. O desempenho real é o da conferência em dados reais, com os fatores desconhecidos."),
        "modelos": {},
        "continuam_na_v2": ["itu", "atipicidade"],
    }
    pacotes = {}
    for nome in MODELOS:
        print(f"Treinando {nome}...", flush=True)
        pacote, metricas, x_calib = treinar_sintetico(nome, base, parametros, sinasc)
        pacotes[nome] = (pacote, x_calib)
        joblib.dump(pacote, SAIDA / f"risco_{nome}.joblib", compress=3)
        todas["modelos"][nome] = metricas
        _mostrar(nome, metricas)

    print("Montando eclampsia...", flush=True)
    pacote, metricas = montar_eclampsia(*pacotes["pre_eclampsia"])
    joblib.dump(pacote, SAIDA / "risco_eclampsia.joblib", compress=3)
    todas["modelos"]["eclampsia"] = metricas
    _mostrar("eclampsia", metricas)

    print("Treinando malformacao...", flush=True)
    pacote, metricas = treinar_malformacao(sinasc)
    joblib.dump(pacote, SAIDA / "risco_malformacao.joblib", compress=3)
    todas["modelos"]["malformacao"] = metricas
    _mostrar("malformacao", metricas)

    with open(SAIDA / "metricas_modelos_v3.json", "w", encoding="utf-8") as arquivo:
        json.dump(todas, arquivo, ensure_ascii=False, indent=2)
    print("Pronto.", flush=True)


if __name__ == "__main__":
    sys.exit(main())
