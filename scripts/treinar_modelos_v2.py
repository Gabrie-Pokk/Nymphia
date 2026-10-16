#!/usr/bin/env python3
"""
Treino v2 dos modelos de risco da Nymphia (15/10/2026).

Por que v2: os modelos de julho de 2026 usavam informação que só existe depois do
parto (Apgar, peso ao nascer, semanas no parto, tipo e local do parto, número
total de consultas) e, nos modelos do SIH, só idade, sexo, estado e município
como número. No app, sem esses dados, o servidor inventava valores (Apgar 9/10,
3.200 g, São Paulo para todo mundo) e o "risco" dependia só da idade.

Regras deste treino:
  1. Só entra o que se sabe DURANTE a gestação e que o app pergunta.
  2. Valor desconhecido fica desconhecido (NaN). O modelo aprende a lidar com
     falta de dado; o app nunca mais inventa valor.
  3. Treino, calibração e teste em partes separadas (60/20/20, estratificado).
  4. Probabilidade calibrada (isotônica) e conferida por faixas.
  5. Relatório honesto: AUC, AUC-PR, Brier, calibração, sensibilidade e
     especificidade num ponto que prioriza não deixar passar casos (FN), e a
     comparação com um modelo só com idade, para mostrar o que as outras
     variáveis acrescentam.

Dados (pasta pipeline_data):
  df_risco.parquet       SINASC, nascidos vivos (3,83 milhões de registros)
  sih_condicoes.parquet  SIH/SUS 2022, internações; usamos só leito obstétrico (ESPEC 02)

Saída (nymphia_backend/modelos/v2):
  risco_<condicao>.joblib, atipicidade.joblib, metricas_modelos_v2.json

Uso:  python scripts/treinar_modelos_v2.py            (tudo)
      python scripts/treinar_modelos_v2.py sih        (só os do SIH)
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
from sklearn.ensemble import HistGradientBoostingClassifier, IsolationForest, RandomForestClassifier
from sklearn.frozen import FrozenEstimator
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import train_test_split

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "pipeline_data"
# Desde a v3 (base sintética), os pacotes v2 ficam em modelos/v2: o app usa os da v3 onde existem
SAIDA = RAIZ / "nymphia_backend" / "modelos" / "v2"
SEMENTE = 42
SENSIBILIDADE_ALVO = 0.80  # ponto de corte que prioriza não deixar passar casos

# ---------------------------------------------------------------------------
# Variáveis (nomes iguais aos que o app monta em ai_risk_service.py)
# ---------------------------------------------------------------------------
VARIAVEIS_SINASC = [
    "idade",                 # anos
    "estado_civil",          # categórica SINASC: 1 solteira, 2 casada, 3 viúva, 4 separada, 5 união estável
    "escolaridade",          # ordinal SINASC: 1 nenhuma, 2 1-3 anos, 3 4-7, 4 8-11, 5 12 ou mais
    "gestacoes_anteriores",
    "partos_normais",
    "partos_cesareos",
    "perdas_anteriores",     # filhos mortos (perdas fetais e abortos)
    "fetos",                 # 1 única, 2 gêmeos, 3 trigêmeos ou mais
    "mes_inicio_prenatal",   # mês da gestação em que o pré-natal começou
]
CATEGORICAS_SINASC = ["estado_civil"]

VARIAVEIS_SIH = [
    "idade",   # anos
    "regiao",  # categórica: 1 Norte, 2 Nordeste, 3 Sudeste, 4 Sul, 5 Centro-Oeste (1º dígito do código IBGE do estado)
]
CATEGORICAS_SIH = ["regiao"]

# Por que cada coisa ficou de fora (vai para o relatório)
EXCLUIDAS = {
    "SINASC": {
        "APGAR1, APGAR5, PESO, SEMAGESTAC, GESTACAO": "medidos no parto; são o próprio desfecho",
        "PARTO, LOCNASC, CODESTAB e leitos do CNES": "dizem como e onde o bebê nasceu, só se sabe no parto",
        "CONSULTAS": "número total de consultas; quem nasce antes tem menos consultas, o modelo aprenderia a resposta",
    },
    "SIH": {
        "SEXO": "sempre feminino em leito obstétrico; não informa nada",
        "MUNIC_RES como número": "código de município tratado como quantidade não tem sentido; virou estado (categoria)",
        "diagnósticos secundários": "preenchidos em menos de 1% das internações; não sustentam um modelo",
        "estado (UF) em vez de região": ("subia a AUC (pré-eclâmpsia 0,66 para 0,70; diabetes 0,68 para 0,75), mas o "
                                         "ganho vinha de diferenças entre estados na forma de registrar a internação; "
                                         "a região guarda a diferença real, como a pré-eclâmpsia mais frequente no Nordeste"),
        "raça/cor": ("o ganho vinha de a raça faltar mais nos casos (30%) do que nos controles (21%), um efeito do "
                     "registro do hospital; entre os registros preenchidos não havia diferença"),
    },
}


def _numero(serie, minimo=None, maximo=None, ausentes=("", "9", "99")):
    texto = serie.astype(str).str.strip()
    valores = pd.to_numeric(texto.where(~texto.isin(ausentes)), errors="coerce")
    if minimo is not None:
        valores = valores.where(valores >= minimo)
    if maximo is not None:
        valores = valores.where(valores <= maximo)
    return valores


def preparar_sinasc():
    bruto = pd.read_parquet(DADOS / "df_risco.parquet")
    x = pd.DataFrame({
        "idade": _numero(bruto["IDADEMAE"], 10, 55, ausentes=("", "99")),
        "estado_civil": _numero(bruto["ESTCIVMAE"], 1, 5),
        "escolaridade": _numero(bruto["ESCMAE"], 1, 5),
        "gestacoes_anteriores": _numero(bruto["QTDGESTANT"], 0, 30, ausentes=("", "99")),
        "partos_normais": _numero(bruto["QTDPARTNOR"], 0, 30, ausentes=("", "99")),
        "partos_cesareos": _numero(bruto["QTDPARTCES"], 0, 30, ausentes=("", "99")),
        "perdas_anteriores": _numero(bruto["QTDFILMORT"], 0, 30, ausentes=("", "99")),
        "fetos": _numero(bruto["GRAVIDEZ"], 1, 3),
        "mes_inicio_prenatal": _numero(bruto["MESPRENAT"], 1, 9, ausentes=("", "99")),
    })
    semanas = _numero(bruto["SEMAGESTAC"], 20, 45, ausentes=("", "99"))
    peso = _numero(bruto["PESO"], 300, 6500, ausentes=("", "9999"))
    apgar5 = _numero(bruto["APGAR5"], 0, 10, ausentes=("", "99"))
    # Desfecho neonatal adverso: prematuro (< 37 semanas), baixo peso (< 2.500 g) ou Apgar 5 < 7
    sabido = semanas.notna() | peso.notna() | apgar5.notna()
    adverso = ((semanas < 37) | (peso < 2500) | (apgar5 < 7)).astype(int)
    anomalia = bruto["IDANOMAL"].astype(str).str.strip()
    return {
        "bem_estar_fetal": (x[sabido].reset_index(drop=True), adverso[sabido].reset_index(drop=True)),
        "malformacao": (x[anomalia.isin(["1", "2"])].reset_index(drop=True),
                        (anomalia[anomalia.isin(["1", "2"])] == "1").astype(int).reset_index(drop=True)),
    }


def preparar_sih():
    bruto = pd.read_parquet(DADOS / "sih_condicoes.parquet")
    obst = bruto[(bruto["ESPEC"].astype(str) == "02") & (bruto["COD_IDADE"].astype(str) == "4")].copy()
    cid = obst["DIAG_PRINC"].astype(str).str.strip().str.upper()
    x = pd.DataFrame({
        "idade": _numero(obst["IDADE"], 10, 55, ausentes=("",)),
        "regiao": _numero(obst["MUNIC_RES"].astype(str).str[:1], 1, 5, ausentes=("",)),
    }).reset_index(drop=True)
    cid = cid.reset_index(drop=True)
    controle = cid.str.startswith("O80")  # parto normal sem complicação
    casos = {
        "pre_eclampsia": cid.str.startswith("O14") | cid.str.startswith("O11"),
        "eclampsia": cid.str.startswith("O15"),
        # Só diabetes gestacional (O24.4); diabetes de antes da gravidez é outra condição
        "diabetes_gestacional": cid.str.startswith("O244"),
        # Infecção urinária na gestação deveria vir de O23; esta base só tem N39 (92 casos)
        "itu": cid.str.startswith("N39"),
    }
    saida = {}
    for nome, caso in casos.items():
        usar = caso | controle
        saida[nome] = (x[usar].reset_index(drop=True), caso[usar].astype(int).reset_index(drop=True))
    return saida


def _como_categoria(x, categoricas):
    x = x.copy()
    for coluna in categoricas:
        x[coluna] = x[coluna].astype("category")
    return x


def _ece(y, p, faixas=10):
    """Erro de calibração esperado: diferença média entre o previsto e o observado, por faixa."""
    ordem = np.argsort(p)
    total = 0.0
    for parte in np.array_split(ordem, faixas):
        if len(parte):
            total += len(parte) * abs(p[parte].mean() - y[parte].mean())
    return total / len(p)


def _tabela_calibracao(y, p, faixas=10):
    ordem = np.argsort(p)
    linhas = []
    for parte in np.array_split(ordem, faixas):
        linhas.append({"previsto": round(float(p[parte].mean()), 4), "observado": round(float(y[parte].mean()), 4),
                       "n": int(len(parte))})
    return linhas


def _ponto_de_corte(y, p, sensibilidade_alvo):
    """Maior limiar que ainda alcança a sensibilidade alvo, e o que acontece nele."""
    positivos = np.sort(p[y == 1])[::-1]
    k = int(np.ceil(sensibilidade_alvo * len(positivos))) - 1
    limiar = float(positivos[max(0, min(k, len(positivos) - 1))])
    previsto = p >= limiar
    vp = int((previsto & (y == 1)).sum()); fn = int((~previsto & (y == 1)).sum())
    fp = int((previsto & (y == 0)).sum()); vn = int((~previsto & (y == 0)).sum())
    return {
        "limiar": round(limiar, 5), "sensibilidade": round(vp / max(1, vp + fn), 4),
        "especificidade": round(vn / max(1, vn + fp), 4), "valor_preditivo_positivo": round(vp / max(1, vp + fp), 4),
        "valor_preditivo_negativo": round(vn / max(1, vn + fn), 4), "fracao_sinalizada": round(float(previsto.mean()), 4),
        "matriz": {"verdadeiro_positivo": vp, "falso_negativo": fn, "falso_positivo": fp, "verdadeiro_negativo": vn},
    }


def treinar(nome, x, y, categoricas, base, folha_minima):
    inicio = time.time()
    x = _como_categoria(x, categoricas)
    x_treino, x_resto, y_treino, y_resto = train_test_split(x, y, test_size=0.4, stratify=y, random_state=SEMENTE)
    x_calib, x_teste, y_calib, y_teste = train_test_split(x_resto, y_resto, test_size=0.5, stratify=y_resto,
                                                          random_state=SEMENTE)

    candidatos = {
        "gradient_boosting": HistGradientBoostingClassifier(
            max_iter=400, learning_rate=0.06, max_leaf_nodes=31, min_samples_leaf=folha_minima,
            l2_regularization=1.0, categorical_features="from_dtype", early_stopping=True,
            validation_fraction=0.1, n_iter_no_change=20, random_state=SEMENTE,
        ),
    }
    resultados = {}
    melhor_nome, melhor_auc, melhor_modelo = None, -1.0, None
    for algoritmo, modelo in candidatos.items():
        modelo.fit(x_treino, y_treino)
        auc_calib = roc_auc_score(y_calib, modelo.predict_proba(x_calib)[:, 1])
        resultados[algoritmo] = round(float(auc_calib), 4)
        if auc_calib > melhor_auc:
            melhor_nome, melhor_auc, melhor_modelo = algoritmo, auc_calib, modelo

    # Floresta aleatória, como na v1, para comparar (sem as variáveis indevidas). Amostra para caber no tempo.
    amostra = min(len(x_treino), 400_000)
    x_rf = x_treino.sample(amostra, random_state=SEMENTE) if amostra < len(x_treino) else x_treino
    rf = RandomForestClassifier(n_estimators=150, max_depth=10, min_samples_leaf=folha_minima, n_jobs=-1,
                                random_state=SEMENTE)
    rf.fit(x_rf.astype(float).fillna(-1), y_treino.loc[x_rf.index])
    auc_rf = roc_auc_score(y_calib, rf.predict_proba(x_calib.astype(float).fillna(-1))[:, 1])
    resultados["random_forest_comparacao"] = round(float(auc_rf), 4)

    calibrado = CalibratedClassifierCV(FrozenEstimator(melhor_modelo), method="isotonic")
    calibrado.fit(x_calib, y_calib)

    p = calibrado.predict_proba(x_teste)[:, 1]
    yt = y_teste.to_numpy()
    # Só idade, para mostrar o que as outras variáveis acrescentam
    so_idade = HistGradientBoostingClassifier(max_iter=200, min_samples_leaf=folha_minima, random_state=SEMENTE)
    so_idade.fit(x_treino[["idade"]], y_treino)
    auc_so_idade = roc_auc_score(y_teste, so_idade.predict_proba(x_teste[["idade"]])[:, 1])

    media = float(p.mean())
    metricas = {
        "condicao": nome,
        "base": base,
        "algoritmo_escolhido": melhor_nome,
        "auc_validacao_por_algoritmo": resultados,
        "variaveis": list(x.columns),
        "n_treino": int(len(y_treino)), "n_calibracao": int(len(y_calib)), "n_teste": int(len(y_teste)),
        "casos_teste": int(yt.sum()), "prevalencia_teste": round(float(yt.mean()), 5),
        "auc_roc": round(float(roc_auc_score(yt, p)), 4),
        "auc_roc_so_idade": round(float(auc_so_idade), 4),
        "auc_pr": round(float(average_precision_score(yt, p)), 4),
        "brier": round(float(brier_score_loss(yt, p)), 5),
        "erro_calibracao_esperado": round(float(_ece(yt, p)), 5),
        "probabilidade_media_prevista": round(media, 5),
        "ponto_fn_primeiro": _ponto_de_corte(yt, p, SENSIBILIDADE_ALVO),
        "calibracao_por_decil": _tabela_calibracao(yt, p),
        "segundos": round(time.time() - inicio, 1),
    }
    pacote = {
        "versao": "2.0",
        "condicao": nome,
        "base": base,
        "modelo": calibrado,
        "features": list(x.columns),
        "categoricas": categoricas,
        "categorias": {c: [float(v) for v in x[c].cat.categories] for c in categoricas},
        "media_referencia": media,
        "tipo_saida": "probabilidade" if base.startswith("SINASC") else "risco_relativo",
        "metricas": {k: metricas[k] for k in ("auc_roc", "auc_pr", "brier", "prevalencia_teste", "n_treino",
                                               "casos_teste", "auc_roc_so_idade")},
        "treinado_em": time.strftime("%Y-%m-%d"),
        "sklearn": sklearn.__version__,
    }
    return pacote, metricas


def treinar_atipicidade(x):
    """Atipicidade do perfil obstétrico, com as mesmas variáveis da gestação (sem nada do parto)."""
    amostra = x.sample(min(len(x), 300_000), random_state=SEMENTE)
    preenchido = amostra.fillna(amostra.median(numeric_only=True))
    modelo = IsolationForest(n_estimators=200, contamination=0.05, random_state=SEMENTE, n_jobs=-1)
    modelo.fit(preenchido)
    return {
        "versao": "2.0", "modelo": modelo, "features": list(x.columns),
        "medianas": {k: float(v) for k, v in amostra.median(numeric_only=True).items()},
        "contaminacao": 0.05, "treinado_em": time.strftime("%Y-%m-%d"), "sklearn": sklearn.__version__,
    }


def main():
    grupos = set(sys.argv[1:]) or {"sinasc", "sih"}
    SAIDA.mkdir(parents=True, exist_ok=True)
    arquivo_metricas = SAIDA / "metricas_modelos_v2.json"
    anteriores = json.loads(arquivo_metricas.read_text(encoding="utf-8")) if arquivo_metricas.exists() else {}
    todas = {"gerado_em": time.strftime("%Y-%m-%d %H:%M"), "sklearn": sklearn.__version__,
             "variaveis_excluidas": EXCLUIDAS, "sensibilidade_alvo": SENSIBILIDADE_ALVO,
             "modelos": dict(anteriores.get("modelos", {}))}

    if "sinasc" in grupos:
        treinar_sinasc(todas)
    if "sih" in grupos:
        treinar_sih(todas)

    with open(arquivo_metricas, "w", encoding="utf-8") as arquivo:
        json.dump(todas, arquivo, ensure_ascii=False, indent=2)
    print("Pronto.", flush=True)


def treinar_sinasc(todas):
    print("Lendo SINASC...", flush=True)
    sinasc = preparar_sinasc()
    for nome, (x, y) in sinasc.items():
        print(f"Treinando {nome} ({len(y):,} registros, {y.mean():.2%} positivos)...", flush=True)
        pacote, metricas = treinar(nome, x[VARIAVEIS_SINASC], y, CATEGORICAS_SINASC,
                                   "SINASC (coorte de nascidos vivos)", folha_minima=200)
        joblib.dump(pacote, SAIDA / f"risco_{nome}.joblib", compress=3)
        todas["modelos"][nome] = metricas
        print(f"  AUC {metricas['auc_roc']} (só idade {metricas['auc_roc_so_idade']}), "
              f"Brier {metricas['brier']}, ECE {metricas['erro_calibracao_esperado']}", flush=True)

    print("Treinando atipicidade...", flush=True)
    joblib.dump(treinar_atipicidade(sinasc["bem_estar_fetal"][0][VARIAVEIS_SINASC]), SAIDA / "atipicidade.joblib",
                compress=3)



def treinar_sih(todas):
    print("Lendo SIH...", flush=True)
    for nome, (x, y) in preparar_sih().items():
        print(f"Treinando {nome} ({len(y):,} registros, {int(y.sum()):,} casos)...", flush=True)
        pacote, metricas = treinar(nome, x[VARIAVEIS_SIH], y, CATEGORICAS_SIH,
                                   "SIH/SUS 2022 (caso-controle: internação pela condição x parto normal)",
                                   folha_minima=50)
        if nome == "itu":
            pacote["confiavel"] = False
            metricas["aviso"] = ("Só 92 casos (N39 em leito obstétrico). Infecção urinária na gestação é registrada "
                                 "como O23, que não veio nesta base. Não usar até treinar com O23.")
        joblib.dump(pacote, SAIDA / f"risco_{nome}.joblib", compress=3)
        todas["modelos"][nome] = metricas
        print(f"  AUC {metricas['auc_roc']} (só idade {metricas['auc_roc_so_idade']}), "
              f"Brier {metricas['brier']}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
