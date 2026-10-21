#!/usr/bin/env python3
"""
Base sintética v3 da Nymphia (15/10/2026).

Para que serve: juntar nos modelos os fatores clínicos que o app pergunta e que
o DATASUS não registra (IMC antes da gravidez, pressão alta e diabetes de antes
da gravidez, pré-eclâmpsia anterior, casos na família), usando o tamanho do
efeito publicado em estudos.

O que ela NÃO é: dado de paciente. As gestantes são fictícias. O modelo treinado
nela devolve os efeitos que entraram no gerador; a AUC medida na própria base
sintética não é desempenho clínico e não deve ser apresentada como tal.

Como é montada, em três camadas:
  1. Perfil real: cada gestante fictícia parte de um registro real do SINASC
     (idade, estado civil, escolaridade, gestações, partos, perdas, número de
     bebês, mês de início do pré-natal). A região é sorteada pela distribuição
     dos partos normais do SIH 2022.
  2. Fatores clínicos sorteados com prevalências brasileiras publicadas.
  3. Desfechos:
     - Prematuridade/baixo peso/Apgar baixo: o desfecho é o REAL do registro do
       SINASC. Os fatores (hipertensão e diabetes prévios) são sorteados já
       sabendo o desfecho, pela regra de Bayes, de modo que a chance real por
       perfil continua a mesma e quem tem o fator fica com o efeito publicado.
     - Pré-eclâmpsia, eclâmpsia e diabetes gestacional: simulados. O risco por
       idade e região vem dos modelos v2 (dados reais do SIH); a incidência
       média vem de fontes brasileiras; os fatores entram com o efeito
       publicado. Em cada combinação de idade e região, o risco médio da base
       sintética é igual ao dos dados reais: os fatores só redistribuem esse
       risco entre quem tem e quem não tem cada fator.
     - Malformação: sem fator clínico com fonte conferida nesta versão; continua
       o modelo v2.

Suposições (estão no relatório e na tela de transparência):
  - Os fatores atuam de forma independente na escala de chance (odds). Estudos
    com ajuste mútuo mostram efeitos menores, então quem tem vários fatores ao
    mesmo tempo pode ficar com o risco superestimado.
  - Riscos relativos de desfechos raros (pré-eclâmpsia, cerca de 3%) foram
    usados como razão de chances; nos desfechos comuns o RR foi convertido.
  - Os fatores são sorteados independentes entre si (exceto pré-eclâmpsia
    anterior, que depende do número de partos).

Saída (pasta pipeline_data):
  base_sintetica_v3.parquet          base completa (não vai para o Git; o script a refaz igual)
  sinasc_reserva_v3.parquet          registros reais do SINASC que NÃO entraram na base,
                                     para conferir o modelo em dado real
  base_sintetica_v3_amostra.csv      amostra de 20 mil linhas (vai para o Git)
  base_sintetica_v3_parametros.json  todos os parâmetros, com fonte, e as conferências

Uso:  python scripts/gerar_base_sintetica.py
"""
import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import treinar_modelos_v2 as v2  # noqa: E402  (reaproveita a leitura dos dados reais)

DADOS = RAIZ / "pipeline_data"
MODELOS_V2 = RAIZ / "nymphia_backend" / "modelos" / "v2"
SEMENTE = 20261015
TAMANHO = 1_200_000
FRACAO_RESERVA = 0.2

# ---------------------------------------------------------------------------
# Parâmetros, cada um com a fonte
# ---------------------------------------------------------------------------
FONTES = {
    "marano2014": ("Marano D, Gama SGN, Domingues RMSM, Souza Júnior PRB. Prevalência e fatores associados aos desvios "
                   "nutricionais em mulheres na fase pré-gestacional em dois municípios do Estado do Rio de Janeiro. "
                   "Rev Bras Epidemiol 2014;17(1):45-58 (gestantes do SUS no 1º trimestre, n = 1.535, 2007-2008)"),
    "dode2009": ("Dode MASO, Santos IS. Fatores de risco para diabetes mellitus gestacional na coorte de nascimentos de "
                 "Pelotas, 2004. Cad Saúde Pública 2009;25(5):1141-52 (n = 4.243)"),
    "ayorinde2017": ("Ayorinde AA, Bhattacharya S. Inherited predisposition to preeclampsia: analysis of the Aberdeen "
                     "intergenerational cohort. Pregnancy Hypertens 2017"),
    "febrasgo2018": ("Peraçoli JC et al. Pré-eclâmpsia/eclâmpsia. Protocolo FEBRASGO de Obstetrícia nº 8, 2018 "
                     "(pré-eclâmpsia em 2% a 5% da população geral)"),
    "bartsch2016": "Bartsch E et al. Clinical risk factors for pre-eclampsia determined in early pregnancy. BMJ 2016;353:i1753",
    "duckitt2005": "Duckitt K, Harrington D. Risk factors for pre-eclampsia at antenatal booking. BMJ 2005;330:565",
    "zhang2024": ("Zhang Y et al. Influence of maternal body mass index on pregnancy complications and outcomes: a "
                  "systematic review and meta-analysis. Front Endocrinol 2024;15:1280692"),
    "zhang2021": "Zhang Y et al. Factors associated with gestational diabetes mellitus: a meta-analysis. J Diabetes Res 2021;2021:6692695",
    "mocellin2024": ("Mocellin LP et al. Gestational diabetes mellitus prevalence in Brazil: a systematic review and "
                     "meta-analysis. Cad Saúde Pública 2024;40(8):e00064919"),
    "bramham2014": "Bramham K et al. Chronic hypertension and pregnancy outcomes: systematic review and meta-analysis. BMJ 2014;348:g2301",
    "yu2017": ("Yu L et al. Quantitative assessment of the effect of pre-gestational diabetes and risk of adverse maternal, "
               "perinatal and neonatal outcomes. Oncotarget 2017;8:61048-56"),
    "sih2022": "SIH/SUS 2022, internações em leito obstétrico (dados reais do projeto, pasta pipeline_data)",
}

# Prevalências
PREV_IMC = {1: 0.10, 2: 0.61, 3: 0.18, 4: 0.11}  # baixo peso, adequado, sobrepeso, obesidade (marano2014)
PREV_HIPERTENSAO = 0.072   # 110 de 1.526, hipertensão antes da gestação, autorrelato (marano2014)
PREV_DIABETES = 0.010      # 15 de 1.523, diabetes antes da gestação (marano2014)
PREV_FAMILIA_DM = 0.32     # parente de 1º ou 2º grau com diabetes (dode2009)
PREV_FAMILIA_PE = 0.025    # mãe com pré-eclâmpsia (ayorinde2017); o app aceita mãe ou irmã
INCIDENCIA_PE_POR_GESTACAO = 0.03  # meio da faixa de 2% a 5% (febrasgo2018); também usada para pré-eclâmpsia anterior

# Desfechos simulados: incidência média
INCIDENCIA_PE = 0.03       # pré-eclâmpsia ou eclâmpsia (febrasgo2018)
PREVALENCIA_DMG = 0.14     # 14% (11% a 16%) no Brasil (mocellin2024)

# Efeitos (razão de chances na escala de odds)
EFEITOS = {
    "pre_eclampsia": {
        "pre_eclampsia_previa": (8.4, "bartsch2016", "RR 8,4 usado como razão de chances (desfecho raro)"),
        "hipertensao_cronica": (5.1, "bartsch2016", "RR 5,1 usado como razão de chances"),
        "diabetes_previo": (3.7, "bartsch2016", "RR 3,7 usado como razão de chances"),
        "imc_baixo_peso": (0.69, "zhang2024", "OR"),
        "imc_sobrepeso": (1.70, "zhang2024", "OR"),
        "imc_obesidade": (2.82, "zhang2024", "OR; igual ao RR de IMC > 30 de bartsch2016 (2,8)"),
        "gemeos": (2.93, "duckitt2005", "RR usado como razão de chances"),
        "nuliparidade": (2.91, "duckitt2005", "RR usado como razão de chances"),
        "historico_familiar_pe": (2.90, "duckitt2005", "RR usado como razão de chances"),
    },
    "diabetes_gestacional": {
        "imc_baixo_peso": (0.63, "zhang2024", "OR"),
        "imc_sobrepeso": (2.20, "zhang2024", "OR da discussão do artigo; a tabela traz 2,92 com intervalo que não o contém"),
        "imc_obesidade": (3.46, "zhang2024", "OR"),
        "historico_familiar_dm": (1.89, "dode2009", "OR ajustado, coorte brasileira"),
        "primigesta": (0.752, "zhang2021", "OR (primeira gestação protege)"),
    },
    "bem_estar_fetal": {
        # O desfecho composto (prematuro, baixo peso ou Apgar baixo) é dominado pela prematuridade
        "hipertensao_cronica": (3.53, "bramham2014", "RR 2,7 de prematuridade convertido em OR com a base de 12,2% do estudo"),
        "diabetes_previo": (3.48, "yu2017", "OR de prematuridade"),
    },
}


def _logit(p):
    p = np.clip(p, 1e-9, 1 - 1e-9)
    return np.log(p / (1 - p))


def _expit(z):
    return 1.0 / (1.0 + np.exp(-z))


def _resolver_intercepto_por_grupo(grupos, s, alvo_por_linha, iteracoes=40):
    """
    Para cada grupo g, acha b_g tal que a média de expit(b_g + s_i) no grupo
    seja igual ao alvo do grupo. Assim o risco médio por grupo fica igual ao real.
    """
    codigos, inverso = np.unique(grupos, return_inverse=True)
    n = np.bincount(inverso).astype(float)
    alvo = np.bincount(inverso, weights=alvo_por_linha) / n
    media_exp = np.bincount(inverso, weights=np.exp(s)) / n
    b = _logit(alvo) - np.log(media_exp)
    for _ in range(iteracoes):
        p = _expit(b[inverso] + s)
        f = np.bincount(inverso, weights=p) / n - alvo
        d = np.bincount(inverso, weights=p * (1 - p)) / n
        b = b - f / np.maximum(d, 1e-12)
    return b[inverso]


def _prever_v2(nome, x):
    pacote = joblib.load(MODELOS_V2 / f"risco_{nome}.joblib")
    tabela = x[pacote["features"]].astype(float).copy()
    for coluna in pacote.get("categoricas", []):
        tabela[coluna] = pd.Categorical(tabela[coluna], categories=pacote["categorias"][coluna])
    return pacote["modelo"].predict_proba(tabela)[:, 1]


def carregar_sinasc():
    bruto = pd.read_parquet(DADOS / "df_risco.parquet")
    x = pd.DataFrame({
        "idade": v2._numero(bruto["IDADEMAE"], 10, 55, ausentes=("", "99")),
        "estado_civil": v2._numero(bruto["ESTCIVMAE"], 1, 5),
        "escolaridade": v2._numero(bruto["ESCMAE"], 1, 5),
        "gestacoes_anteriores": v2._numero(bruto["QTDGESTANT"], 0, 30, ausentes=("", "99")),
        "partos_normais": v2._numero(bruto["QTDPARTNOR"], 0, 30, ausentes=("", "99")),
        "partos_cesareos": v2._numero(bruto["QTDPARTCES"], 0, 30, ausentes=("", "99")),
        "perdas_anteriores": v2._numero(bruto["QTDFILMORT"], 0, 30, ausentes=("", "99")),
        "fetos": v2._numero(bruto["GRAVIDEZ"], 1, 3),
        "mes_inicio_prenatal": v2._numero(bruto["MESPRENAT"], 1, 9, ausentes=("", "99")),
    })
    semanas = v2._numero(bruto["SEMAGESTAC"], 20, 45, ausentes=("", "99"))
    peso = v2._numero(bruto["PESO"], 300, 6500, ausentes=("", "9999"))
    apgar5 = v2._numero(bruto["APGAR5"], 0, 10, ausentes=("", "99"))
    sabido = semanas.notna() | peso.notna() | apgar5.notna()
    x["bem_estar_fetal"] = np.where(sabido, ((semanas < 37) | (peso < 2500) | (apgar5 < 7)).astype(float), np.nan)
    return x[sabido].reset_index(drop=True)


def distribuicao_regioes():
    bruto = pd.read_parquet(DADOS / "sih_condicoes.parquet", columns=["ESPEC", "COD_IDADE", "DIAG_PRINC", "MUNIC_RES"])
    obst = bruto[(bruto["ESPEC"].astype(str) == "02") & (bruto["COD_IDADE"].astype(str) == "4")]
    controle = obst["DIAG_PRINC"].astype(str).str.strip().str.upper().str.startswith("O80")
    regiao = pd.to_numeric(obst.loc[controle, "MUNIC_RES"].astype(str).str[:1], errors="coerce").dropna()
    regiao = regiao[regiao.between(1, 5)]
    return (regiao.value_counts(normalize=True).sort_index()).to_dict()


def modelo_fracao_eclampsia():
    """Entre as internações do espectro (pré-eclâmpsia ou eclâmpsia), a chance de ser eclâmpsia, por idade e região."""
    from sklearn.linear_model import LogisticRegression
    sih = v2.preparar_sih()
    x_pe, y_pe = sih["pre_eclampsia"]
    x_ec, y_ec = sih["eclampsia"]
    casos = pd.concat([x_pe[y_pe == 1].assign(ecl=0), x_ec[y_ec == 1].assign(ecl=1)], ignore_index=True).dropna()

    def matriz(x):
        idade = x["idade"].clip(12, 50).to_numpy()
        colunas = [(idade - 27) / 7, ((idade - 27) / 7) ** 2]
        colunas += [(x["regiao"].to_numpy() == r).astype(float) for r in (1, 2, 4, 5)]  # Sudeste é a referência
        return np.column_stack(colunas)

    modelo = LogisticRegression(max_iter=1000).fit(matriz(casos), casos["ecl"])
    return modelo, matriz, float(casos["ecl"].mean()), int(len(casos))


def main():
    inicio = time.time()
    rng = np.random.default_rng(SEMENTE)
    print("Lendo SINASC...", flush=True)
    sinasc = carregar_sinasc()
    ordem = rng.permutation(len(sinasc))
    n_reserva = int(len(sinasc) * FRACAO_RESERVA)
    reserva = sinasc.iloc[ordem[:n_reserva]].reset_index(drop=True)
    base = sinasc.iloc[ordem[n_reserva:n_reserva + TAMANHO]].reset_index(drop=True)
    n = len(base)
    print(f"  {len(sinasc):,} registros; {n:,} na base sintética, {n_reserva:,} reservados para conferência", flush=True)

    # Região: distribuição real dos partos normais do SIH 2022
    regioes = distribuicao_regioes()
    base["regiao"] = rng.choice([float(r) for r in regioes], size=n, p=list(regioes.values()))

    # ---------------------------------------------------------------- fatores
    base["imc_categoria"] = rng.choice(list(PREV_IMC), size=n, p=list(PREV_IMC.values())).astype(float)
    base["historico_familiar_pe"] = (rng.random(n) < PREV_FAMILIA_PE).astype(float)
    base["historico_familiar_dm"] = (rng.random(n) < PREV_FAMILIA_DM).astype(float)
    partos = base["partos_normais"].fillna(0) + base["partos_cesareos"].fillna(0)
    partos_conhecidos = base["partos_normais"].notna() & base["partos_cesareos"].notna()
    partos = np.where(partos_conhecidos, partos, base["gestacoes_anteriores"].fillna(0)).clip(0, 10)
    chance_pe_previa = 1 - (1 - INCIDENCIA_PE_POR_GESTACAO) ** partos
    base["pre_eclampsia_previa"] = (rng.random(n) < chance_pe_previa).astype(float)

    # Hipertensão e diabetes de antes da gravidez: sorteio condicionado ao desfecho real (Bayes)
    print("Sorteando hipertensão e diabetes condicionados ao desfecho real...", flush=True)
    pi = _prever_v2("bem_estar_fetal", base)
    combinacoes = [(0, 0), (1, 0), (0, 1), (1, 1)]
    peso_prior = np.array([(PREV_HIPERTENSAO if h else 1 - PREV_HIPERTENSAO) * (PREV_DIABETES if d else 1 - PREV_DIABETES)
                           for h, d in combinacoes])
    efeito = EFEITOS["bem_estar_fetal"]
    s_comb = np.array([h * np.log(efeito["hipertensao_cronica"][0]) + d * np.log(efeito["diabetes_previo"][0])
                       for h, d in combinacoes])
    b = _logit(pi) - np.log((peso_prior * np.exp(s_comb)).sum())
    for _ in range(40):
        p = _expit(b[:, None] + s_comb[None, :])
        f = (p * peso_prior).sum(axis=1) - pi
        d = (p * (1 - p) * peso_prior).sum(axis=1)
        b = b - f / np.maximum(d, 1e-12)
    p = _expit(b[:, None] + s_comb[None, :])
    y = base["bem_estar_fetal"].to_numpy()
    posterior = peso_prior * np.where(y[:, None] == 1, p, 1 - p)
    posterior /= posterior.sum(axis=1, keepdims=True)
    sorteio = (posterior.cumsum(axis=1) > rng.random(n)[:, None]).argmax(axis=1)
    base["hipertensao_cronica"] = np.array([c[0] for c in combinacoes], dtype=float)[sorteio]
    base["diabetes_previo"] = np.array([c[1] for c in combinacoes], dtype=float)[sorteio]

    # ---------------------------------------------------------------- pré-eclâmpsia e eclâmpsia
    print("Simulando pré-eclâmpsia, eclâmpsia e diabetes gestacional...", flush=True)
    grupo = base["idade"].fillna(-1).astype(int) * 10 + base["regiao"].astype(int)
    p_cc = _prever_v2("pre_eclampsia", base)              # risco relativo por idade e região (SIH real)
    deslocamento = 0.0
    for _ in range(60):  # corrige o intercepto do caso-controle para a incidência média escolhida
        media = _expit(_logit(p_cc) + deslocamento).mean()
        deslocamento += _logit(INCIDENCIA_PE) - _logit(media)
    alvo_pe = _expit(_logit(p_cc) + deslocamento)
    e = EFEITOS["pre_eclampsia"]
    imc = base["imc_categoria"].to_numpy()
    nulipara = (partos_conhecidos.to_numpy() & (partos == 0))
    gemeos = (base["fetos"].fillna(1).to_numpy() >= 2)
    s_pe = (base["pre_eclampsia_previa"].to_numpy() * np.log(e["pre_eclampsia_previa"][0])
            + base["hipertensao_cronica"].to_numpy() * np.log(e["hipertensao_cronica"][0])
            + base["diabetes_previo"].to_numpy() * np.log(e["diabetes_previo"][0])
            + (imc == 1) * np.log(e["imc_baixo_peso"][0]) + (imc == 3) * np.log(e["imc_sobrepeso"][0])
            + (imc == 4) * np.log(e["imc_obesidade"][0])
            + gemeos * np.log(e["gemeos"][0]) + nulipara * np.log(e["nuliparidade"][0])
            + base["historico_familiar_pe"].to_numpy() * np.log(e["historico_familiar_pe"][0]))
    p_pe = _expit(_resolver_intercepto_por_grupo(grupo.to_numpy(), s_pe, alvo_pe) + s_pe)
    base["pre_eclampsia"] = (rng.random(n) < p_pe).astype(float)

    modelo_ecl, matriz_ecl, fracao_ecl_media, n_casos_sih = modelo_fracao_eclampsia()
    tem_idade = base["idade"].notna()
    q = np.full(n, fracao_ecl_media)
    q[tem_idade.to_numpy()] = modelo_ecl.predict_proba(matriz_ecl(base.loc[tem_idade, ["idade", "regiao"]]))[:, 1]
    base["eclampsia"] = ((base["pre_eclampsia"].to_numpy() == 1) & (rng.random(n) < q)).astype(float)

    # ---------------------------------------------------------------- diabetes gestacional
    sem_dm_previo = base["diabetes_previo"].to_numpy() == 0
    p_cc_dmg = _prever_v2("diabetes_gestacional", base)
    deslocamento = 0.0
    for _ in range(60):
        media = _expit(_logit(p_cc_dmg[sem_dm_previo]) + deslocamento).mean()
        deslocamento += _logit(PREVALENCIA_DMG) - _logit(media)
    alvo_dmg = _expit(_logit(p_cc_dmg) + deslocamento)
    e = EFEITOS["diabetes_gestacional"]
    primigesta = (base["gestacoes_anteriores"].to_numpy() == 0)
    s_dmg = ((imc == 1) * np.log(e["imc_baixo_peso"][0]) + (imc == 3) * np.log(e["imc_sobrepeso"][0])
             + (imc == 4) * np.log(e["imc_obesidade"][0])
             + base["historico_familiar_dm"].to_numpy() * np.log(e["historico_familiar_dm"][0])
             + primigesta * np.log(e["primigesta"][0]))
    p_dmg = np.full(n, np.nan)
    p_dmg[sem_dm_previo] = _expit(_resolver_intercepto_por_grupo(grupo.to_numpy()[sem_dm_previo], s_dmg[sem_dm_previo],
                                                                 alvo_dmg[sem_dm_previo]) + s_dmg[sem_dm_previo])
    dmg = np.full(n, np.nan)
    dmg[sem_dm_previo] = (rng.random(int(sem_dm_previo.sum())) < p_dmg[sem_dm_previo]).astype(float)
    base["diabetes_gestacional"] = dmg  # quem já tinha diabetes não entra: diabetes gestacional não se aplica

    # ---------------------------------------------------------------- conferências
    def rr_bruto(coluna, desfecho, filtro=None):
        f = np.ones(n, dtype=bool) if filtro is None else filtro
        com = base.loc[f & (base[coluna] == 1), desfecho].mean()
        sem = base.loc[f & (base[coluna] == 0), desfecho].mean()
        return round(float(com / sem), 2) if sem else None

    conferencias = {
        "prevalencias_na_base": {
            "imc_categoria": {str(k): round(float((imc == k).mean()), 4) for k in PREV_IMC},
            "hipertensao_cronica": round(float(base["hipertensao_cronica"].mean()), 4),
            "diabetes_previo": round(float(base["diabetes_previo"].mean()), 4),
            "pre_eclampsia_previa_entre_quem_ja_teve_parto": round(float(base.loc[partos > 0, "pre_eclampsia_previa"].mean()), 4),
            "historico_familiar_pe": round(float(base["historico_familiar_pe"].mean()), 4),
            "historico_familiar_dm": round(float(base["historico_familiar_dm"].mean()), 4),
        },
        "desfechos_na_base": {
            "bem_estar_fetal_real": round(float(base["bem_estar_fetal"].mean()), 4),
            "pre_eclampsia": round(float(base["pre_eclampsia"].mean()), 4),
            "eclampsia": round(float(base["eclampsia"].mean()), 5),
            "diabetes_gestacional": round(float(np.nanmean(base["diabetes_gestacional"])), 4),
        },
        "taxa_de_pre_eclampsia_com_o_fator_na_base": {
            "pre_eclampsia_previa": round(float(base.loc[base["pre_eclampsia_previa"] == 1, "pre_eclampsia"].mean()), 4),
            "hipertensao_cronica": round(float(base.loc[base["hipertensao_cronica"] == 1, "pre_eclampsia"].mean()), 4),
            "diabetes_previo": round(float(base.loc[base["diabetes_previo"] == 1, "pre_eclampsia"].mean()), 4),
            "imc_obesidade": round(float(base.loc[imc == 4, "pre_eclampsia"].mean()), 4),
            "comparacao_bartsch2016": "taxas agrupadas no estudo: pré-eclâmpsia anterior 12,0%, hipertensão 16,0%, diabetes 11,0%, IMC > 30 7,1%",
        },
        "risco_relativo_bruto_na_base": {
            "bem_estar_fetal_hipertensao": rr_bruto("hipertensao_cronica", "bem_estar_fetal"),
            "bem_estar_fetal_diabetes": rr_bruto("diabetes_previo", "bem_estar_fetal"),
            "pre_eclampsia_hipertensao": rr_bruto("hipertensao_cronica", "pre_eclampsia"),
            "pre_eclampsia_historico_familiar": rr_bruto("historico_familiar_pe", "pre_eclampsia"),
            "diabetes_gestacional_historico_familiar": rr_bruto("historico_familiar_dm", "diabetes_gestacional"),
        },
        "eclampsia_entre_internacoes_do_espectro_no_sih": {"fracao_media": round(fracao_ecl_media, 4), "casos": n_casos_sih},
        "distribuicao_de_regioes_usada": {str(int(k)): round(float(v), 4) for k, v in regioes.items()},
    }

    # Risco médio por idade e região: a base sintética precisa repetir o alvo tirado dos dados reais
    por_grupo = pd.DataFrame({"g": grupo, "alvo": alvo_pe, "obs": p_pe}).groupby("g").mean()
    conferencias["pre_eclampsia_maior_diferenca_entre_alvo_e_base_por_grupo"] = round(float((por_grupo["alvo"] - por_grupo["obs"]).abs().max()), 6)

    parametros = {
        "versao": "3.0",
        "gerado_em": time.strftime("%Y-%m-%d %H:%M"),
        "semente": SEMENTE,
        "linhas": n,
        "fontes": FONTES,
        "prevalencias": {
            "imc_categoria": {"valores": PREV_IMC, "rotulos": {1: "baixo peso", 2: "adequado", 3: "sobrepeso", 4: "obesidade"},
                              "fonte": "marano2014"},
            "hipertensao_cronica": {"valor": PREV_HIPERTENSAO, "fonte": "marano2014", "nota": "autorrelato"},
            "diabetes_previo": {"valor": PREV_DIABETES, "fonte": "marano2014"},
            "historico_familiar_dm": {"valor": PREV_FAMILIA_DM, "fonte": "dode2009"},
            "historico_familiar_pe": {"valor": PREV_FAMILIA_PE, "fonte": "ayorinde2017", "nota": "só mãe"},
            "pre_eclampsia_previa": {"regra": "1 - (1 - 0,03) elevado ao número de partos", "fonte": "febrasgo2018"},
            "regiao": {"fonte": "sih2022", "nota": "distribuição dos partos normais; alguns estados vieram incompletos"},
        },
        "incidencias": {
            "pre_eclampsia": {"valor": INCIDENCIA_PE, "fonte": "febrasgo2018", "nota": "pré-eclâmpsia ou eclâmpsia"},
            "eclampsia": {"regra": "fração do espectro que é eclâmpsia, por idade e região", "fonte": "sih2022"},
            "diabetes_gestacional": {"valor": PREVALENCIA_DMG, "fonte": "mocellin2024"},
            "bem_estar_fetal": {"regra": "desfecho real do SINASC"},
        },
        "efeitos": {cond: {k: {"razao_de_chances": v[0], "fonte": v[1], "nota": v[2]} for k, v in efs.items()}
                    for cond, efs in EFEITOS.items()},
        "suposicoes": [
            "Fatores independentes entre si, exceto pré-eclâmpsia anterior, que depende do número de partos.",
            "Efeitos multiplicam a chance (odds); quem tem vários fatores pode ficar com risco superestimado.",
            "Em cada idade e região, o risco médio da base é igual ao dos dados reais.",
            "Malformação não recebe fatores nesta versão (sem fonte conferida).",
        ],
        "conferencias": conferencias,
    }

    DADOS.mkdir(exist_ok=True)
    base.to_parquet(DADOS / "base_sintetica_v3.parquet", index=False)
    reserva.to_parquet(DADOS / "sinasc_reserva_v3.parquet", index=False)
    base.sample(20_000, random_state=SEMENTE).to_csv(DADOS / "base_sintetica_v3_amostra.csv", index=False)
    with open(DADOS / "base_sintetica_v3_parametros.json", "w", encoding="utf-8") as arquivo:
        json.dump(parametros, arquivo, ensure_ascii=False, indent=2, default=str)
    print(json.dumps(conferencias, ensure_ascii=False, indent=2), flush=True)
    print(f"Pronto em {time.time() - inicio:.0f} s.", flush=True)


if __name__ == "__main__":
    sys.exit(main())
