"""
Modelos de risco da Nymphia, versão 2 (15/10/2026).

O que mudou em relação à versão de julho de 2026 (detalhes em
scripts/treinar_modelos_v2.py e em modelos/metricas_modelos_v2.json):

- Os modelos só recebem o que se sabe DURANTE a gestação. Antes, o de
  malformação usava Apgar, peso ao nascer e semanas no parto, e o servidor
  inventava esses valores (Apgar 9/10, 3.200 g) para todas as gestantes.
- Valor que a gestante não informou fica desconhecido. Antes viravam
  São Paulo, 25 anos, "casada", 7 consultas e assim por diante.
- As probabilidades são calibradas. Antes, com o treino que dava peso extra
  aos casos raros, um risco real de 6% aparecia como 40% a 60%.
- Pré-eclâmpsia, eclâmpsia e diabetes vêm do SIH, onde casos e controles são
  internações (caso-controle): a chance absoluta não é estimável, então a
  saída é o risco relativo à média ("1,4 vez a média"), não uma porcentagem.
- Infecção urinária fica indisponível: a base só tinha 92 casos (N39); o
  registro certo na gestação é O23, que não veio nos dados.
- Os fatores clínicos mais fortes (pré-eclâmpsia anterior, hipertensão e
  diabetes de antes da gravidez, IMC 30 ou mais, gêmeos) não existem nas bases
  do DATASUS. Eles aparecem ao lado, com o tamanho do efeito publicado.
"""
import json
import logging
import math
import os
import threading
from itertools import product
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nymphia.ai_risk_service")

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
MODELOS_DIR = os.environ.get("NYMPHIA_MODELOS_DIR", str(_BACKEND_DIR / "modelos"))

NOMES_MODELOS = [
    "bem_estar_fetal",
    "malformacao",
    "pre_eclampsia",
    "eclampsia",
    "diabetes_gestacional",
    "itu",
]
NOMES_RF = NOMES_MODELOS  # nome antigo, mantido para quem ainda importa

DISCLAIMER_TEXT = (
    "Aviso de responsabilidade (CFM 2.454/2026 e CDC): esta análise é uma estimativa estatística populacional, "
    "feita com dados do DATASUS (SINASC e SIH) e aprendizado de máquina. NÃO CONSTITUI DIAGNÓSTICO MÉDICO e "
    "não substitui a avaliação clínica. Está sujeita a falsos positivos e falsos negativos. Decisões clínicas "
    "cabem exclusivamente à equipe de saúde."
)

DESCRICOES = {
    "bem_estar_fetal": {
        "titulo": "Prematuridade, baixo peso ou Apgar baixo",
        "estima": "Chance de o bebê nascer antes de 37 semanas, com menos de 2,5 kg ou com Apgar de 5º minuto abaixo de 7.",
    },
    "malformacao": {
        "titulo": "Malformação congênita",
        "estima": "Chance de uma malformação ser registrada ao nascer. Não substitui o ultrassom morfológico.",
    },
    "pre_eclampsia": {
        "titulo": "Pré-eclâmpsia",
        "estima": "Risco de internação por pré-eclâmpsia, comparado à média das gestantes.",
    },
    "eclampsia": {
        "titulo": "Eclâmpsia",
        "estima": "Risco de internação por eclâmpsia, comparado à média das gestantes.",
    },
    "diabetes_gestacional": {
        "titulo": "Diabetes gestacional",
        "estima": "Risco de internação com diabetes gestacional, comparado à média. A triagem por exame é para todas.",
    },
    "itu": {
        "titulo": "Infecção urinária",
        "estima": "Sem modelo confiável ainda. A urocultura do pré-natal continua sendo o caminho.",
    },
}

# Risco relativo à média que separa os níveis mostrados na tela
NIVEL_AUMENTADO = 1.25
NIVEL_ALTO = 2.0

_trava_carregamento = threading.Lock()

# Os modelos v2 têm menos de 1 MB cada: cabem até no plano grátis do Render.
# A leitura do limite de memória fica para o /health e para modelos futuros.
MODELOS_PESADOS: tuple = ()
CAMINHOS_LIMITE_CGROUP = ("/sys/fs/cgroup/memory.max", "/sys/fs/cgroup/memory/memory.limit_in_bytes")


def limite_de_memoria_mb() -> Optional[int]:
    """
    Memória disponível para o processo, em MB, ou None se não houver limite
    conhecido. NYMPHIA_LIMITE_MEMORIA_MB vence; depois, o limite do contêiner
    (cgroup); no Render sem limite legível, assume os 512 MB do plano grátis.
    """
    definido = os.getenv("NYMPHIA_LIMITE_MEMORIA_MB", "").strip()
    if definido.isdigit():
        return int(definido)
    for caminho in CAMINHOS_LIMITE_CGROUP:
        try:
            with open(caminho) as arquivo:
                valor = arquivo.read().strip()
        except OSError:
            continue
        try:
            bytes_limite = int(valor)
        except ValueError:
            continue  # "max": o contêiner não mostra limite
        if bytes_limite < 1 << 60:
            return bytes_limite // (1024 * 1024)
    if os.getenv("RENDER"):
        return 512
    return None


_modelos_estado: Dict[str, Any] = {
    "carregado": False,
    "carregando": False,
    "desligados_por_memoria": [],
    "modelos": {},        # nome -> pacote salvo pelo treino v2
    "atipicidade": None,  # pacote do Isolation Forest v2
    "metricas": None,     # conteúdo de metricas_modelos_v2.json
}


def carregar_modelos_ml():
    """Carrega os modelos uma vez por processo, mesmo com vários pedidos ao mesmo tempo."""
    if _modelos_estado["carregado"]:
        return
    with _trava_carregamento:
        if _modelos_estado["carregado"]:
            return
        _modelos_estado["carregando"] = True
        try:
            _carregar_modelos_sem_trava()
        finally:
            _modelos_estado["carregando"] = False
            _modelos_estado["carregado"] = True


def _carregar_modelos_sem_trava():
    try:
        import joblib
    except ImportError:
        logger.warning("joblib não instalado; as estimativas por modelo ficam indisponíveis.")
        return
    pasta = Path(MODELOS_DIR)
    if not pasta.exists():
        logger.warning(f"Pasta de modelos não encontrada: {MODELOS_DIR}")
        return
    logger.info(f"Carregando modelos de risco v2 de {MODELOS_DIR}")
    for nome in NOMES_MODELOS:
        caminho = pasta / f"risco_{nome}.joblib"
        if not caminho.exists():
            logger.warning(f"Modelo {caminho.name} não encontrado; essa estimativa fica indisponível.")
            continue
        try:
            _modelos_estado["modelos"][nome] = joblib.load(str(caminho))
            logger.info(f"Modelo '{nome}' carregado")
        except Exception as erro:
            logger.warning(f"Falha ao carregar o modelo '{nome}': {erro}")
    caminho_atip = pasta / "atipicidade.joblib"
    if caminho_atip.exists():
        try:
            _modelos_estado["atipicidade"] = joblib.load(str(caminho_atip))
            logger.info("Isolation Forest carregado com sucesso (atipicidade do perfil obstétrico)")
        except Exception as erro:
            logger.warning(f"Falha ao carregar a atipicidade: {erro}")
    caminho_metricas = pasta / "metricas_modelos_v2.json"
    if caminho_metricas.exists():
        try:
            _modelos_estado["metricas"] = json.loads(caminho_metricas.read_text(encoding="utf-8"))
        except Exception as erro:
            logger.warning(f"Falha ao ler as métricas dos modelos: {erro}")


def status_modelos_ml() -> Dict[str, Any]:
    """Estado dos modelos. NUNCA dispara carregamento: o /health precisa ser leve."""
    disponiveis = [n for n, p in _modelos_estado["modelos"].items() if p.get("confiavel", True)]
    return {
        "rf_disponiveis": disponiveis,  # nome antigo do campo, mantido no /health
        "modelos_disponiveis": disponiveis,
        "isolation_forest_disponivel": _modelos_estado["atipicidade"] is not None,
        "carregando": _modelos_estado["carregando"],
        "carregado": _modelos_estado["carregado"],
        "desligados_por_memoria": list(_modelos_estado.get("desligados_por_memoria", [])),
    }


# ---------------------------------------------------------------------------
# Do cadastro da gestante para as variáveis dos modelos
# ---------------------------------------------------------------------------
_NAN = float("nan")

# Códigos do SINASC. Opção do app que junta duas categorias do SINASC vira as
# duas, e a estimativa é a média entre elas (em vez de escolher uma no chute).
_ESTADO_CIVIL = {
    "solteira": [1.0], "casada": [2.0], "casada / união estável": [2.0, 5.0], "união estável": [5.0],
    "uniao estavel": [5.0], "viúva": [3.0], "viuva": [3.0], "divorciada / separada": [4.0],
    "divorciada": [4.0], "separada": [4.0],
}
# Anos de estudo do SINASC: 1 nenhum, 2 de 1 a 3, 3 de 4 a 7, 4 de 8 a 11, 5 doze ou mais
_ESCOLARIDADE = {
    "nenhuma": [1.0], "sem escolaridade": [1.0], "fundamental incompleto": [2.0, 3.0],
    "fundamental completo": [4.0], "médio incompleto": [4.0], "medio incompleto": [4.0],
    "médio completo": [4.0, 5.0], "medio completo": [4.0, 5.0], "superior incompleto": [5.0],
    "superior completo": [5.0], "pós-graduação": [5.0], "pos-graduacao": [5.0],
}

ROTULOS_VARIAVEIS = {
    "idade": "idade", "estado_civil": "estado civil", "escolaridade": "escolaridade",
    "gestacoes_anteriores": "gestações anteriores", "partos_normais": "partos normais",
    "partos_cesareos": "cesáreas", "perdas_anteriores": "perdas anteriores", "fetos": "número de bebês",
    "mes_inicio_prenatal": "mês em que começou o pré-natal", "regiao": "estado onde mora",
}


def _numero(valor, minimo=None, maximo=None) -> float:
    if valor is None or isinstance(valor, bool):
        return _NAN
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return _NAN
    if math.isnan(numero) or (minimo is not None and numero < minimo) or (maximo is not None and numero > maximo):
        return _NAN
    return numero


def _opcoes(valor, tabela) -> List[float]:
    if valor is None or valor == "":
        return [_NAN]
    texto = str(valor).strip().lower()
    if texto.isdigit():  # rotas antigas mandam o código do SINASC direto (1 a 5)
        codigo = float(texto)
        return [codigo] if 1 <= codigo <= 5 else [_NAN]
    return tabela.get(texto, [_NAN])


def montar_variaveis(perfil: Dict[str, Any]) -> Dict[str, Any]:
    """
    Variáveis dos modelos a partir do cadastro. O que não foi informado fica NaN
    (desconhecido); nada é inventado. Campos com mais de um código possível vêm
    como lista e viram uma média de estimativas.
    """
    uf = _numero(perfil.get("uf_residencia", perfil.get("uf_cod")), 11, 53)
    fetos = perfil.get("numero_fetos")
    if fetos is None and perfil.get("gravidez_multipla") is not None:  # rotas antigas: 1 única, 2 dupla, 3 tripla
        fetos = perfil.get("gravidez_multipla")
    return {
        "idade": _numero(perfil.get("idade"), 10, 55),
        "estado_civil": _opcoes(perfil.get("estado_civil"), _ESTADO_CIVIL),
        "escolaridade": _opcoes(perfil.get("escolaridade"), _ESCOLARIDADE),
        "gestacoes_anteriores": _numero(perfil.get("gestacoes_anteriores"), 0, 30),
        "partos_normais": _numero(perfil.get("partos_normais"), 0, 30),
        "partos_cesareos": _numero(perfil.get("partos_cesareos"), 0, 30),
        "perdas_anteriores": _numero(perfil.get("perdas_gestacionais"), 0, 30),
        "fetos": _numero(fetos, 1, 3),
        "mes_inicio_prenatal": _numero(perfil.get("mes_inicio_prenatal"), 1, 9),
        "regiao": float(int(uf) // 10) if not math.isnan(uf) else _NAN,
    }


def _linhas(variaveis: Dict[str, Any], features: List[str]) -> List[Dict[str, float]]:
    listas = [v if isinstance(v, list) else [v] for v in (variaveis[f] for f in features)]
    return [dict(zip(features, combinacao)) for combinacao in product(*listas)]


def _prever(pacote: Dict[str, Any], variaveis: Dict[str, Any]) -> float:
    import pandas as pd
    features = pacote["features"]
    tabela = pd.DataFrame(_linhas(variaveis, features), columns=features).astype(float)
    for coluna in pacote.get("categoricas", []):
        tabela[coluna] = pd.Categorical(tabela[coluna], categories=pacote["categorias"][coluna])
    return float(pacote["modelo"].predict_proba(tabela)[:, 1].mean())


def _faltantes(variaveis: Dict[str, Any], features: List[str]) -> List[str]:
    faltam = []
    for f in features:
        valor = variaveis[f]
        valores = valor if isinstance(valor, list) else [valor]
        if all(isinstance(v, float) and math.isnan(v) for v in valores):
            faltam.append(ROTULOS_VARIAVEIS.get(f, f))
    return faltam


def _nivel(risco_relativo: float) -> str:
    if risco_relativo >= NIVEL_ALTO:
        return "alto"
    if risco_relativo >= NIVEL_AUMENTADO:
        return "moderado"
    return "baixo"


def _estimar(nome: str, variaveis: Dict[str, Any]) -> Dict[str, Any]:
    pacote = _modelos_estado["modelos"].get(nome)
    base = {"condicao": nome, "nome": DESCRICOES[nome]["titulo"], "o_que_estima": DESCRICOES[nome]["estima"]}
    if pacote is None or not pacote.get("confiavel", True):
        motivo = (
            "Modelo em revisão: a base de treino tinha poucos casos (92). Infecção urinária na gestação é "
            "registrada como O23 no DATASUS e precisa de um novo download para treinar."
            if nome == "itu" else "Modelo não carregado neste servidor."
        )
        return {**base, "fonte": "indisponivel", "tipo_saida": None, "probabilidade": None,
                "risco_relativo": None, "nivel": None, "motivo": motivo}
    try:
        p = _prever(pacote, variaveis)
    except Exception as erro:
        logger.warning(f"Falha ao estimar '{nome}': {erro}")
        return {**base, "fonte": "indisponivel", "tipo_saida": None, "probabilidade": None,
                "risco_relativo": None, "nivel": None, "motivo": "Falha ao calcular."}
    media = float(pacote.get("media_referencia") or p or 1e-9)
    relativo = round(p / media, 2) if media > 0 else None
    absoluta = pacote.get("tipo_saida") == "probabilidade"
    metricas = pacote.get("metricas", {})
    return {
        **base,
        "fonte": "modelo_v2",
        "tipo_saida": "probabilidade" if absoluta else "risco_relativo",
        "probabilidade": round(p, 4) if absoluta else None,
        "media_populacional": round(media, 4) if absoluta else None,
        "risco_relativo": relativo,
        "nivel": _nivel(relativo or 0.0),
        "auc": metricas.get("auc_roc"),
        "base": pacote.get("base"),
        "dados_faltantes": _faltantes(variaveis, pacote["features"]),
    }


# ---------------------------------------------------------------------------
# Fatores clínicos que as bases do DATASUS não registram
# ---------------------------------------------------------------------------
_BARTSCH = "Bartsch E et al., BMJ 2016;353:i1753"
_DUCKITT = "Duckitt K, Harrington D, BMJ 2005;330:565"


def _parente_proximo(h: Dict[str, str]) -> bool:
    return (h.get("parente") or "").strip().lower() in ("mãe", "irmã")


def fatores_clinicos(perfil: Dict[str, Any], historico_familiar: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """Fatores informados pela gestante, com o efeito publicado quando há número confiável."""
    fatores: List[Dict[str, Any]] = []

    def pe(fator, rr, fonte, peso):
        fatores.append({"condicao": "pre_eclampsia", "fator": fator, "risco_relativo_publicado": rr,
                        "fonte": fonte, "peso_diretriz": peso})

    if perfil.get("pre_eclampsia_previa"):
        pe("Pré-eclâmpsia em gestação anterior", 8.4, _BARTSCH, "alto")
    if perfil.get("hipertensao_cronica"):
        pe("Pressão alta desde antes da gravidez", 5.1, _BARTSCH, "alto")
    if perfil.get("diabetes_previo"):
        pe("Diabetes desde antes da gravidez", 3.7, _BARTSCH, "alto")
    fetos = _numero(perfil.get("numero_fetos"), 1, 3)
    if not math.isnan(fetos) and fetos >= 2:
        pe("Gestação de gêmeos ou mais", 2.93, _DUCKITT, "alto")
    imc = _numero(perfil.get("imc_pre_gestacional"), 10, 80)
    if not math.isnan(imc) and imc >= 30:
        pe("IMC de 30 ou mais antes da gravidez", 2.8, _BARTSCH, "moderado")
    partos = [_numero(perfil.get("partos_normais"), 0, 30), _numero(perfil.get("partos_cesareos"), 0, 30)]
    if all(not math.isnan(v) for v in partos) and sum(partos) == 0:
        pe("Primeiro parto (nenhum parto anterior)", 2.91, _DUCKITT, "moderado")
    if any(_parente_proximo(h) and any(t in (h.get("condicao") or "").lower() for t in ("pré-eclâmpsia", "pre-eclampsia", "pré eclâmpsia", "eclâmpsia", "eclampsia"))
           for h in historico_familiar):
        pe("Mãe ou irmã com pré-eclâmpsia", 2.90, _DUCKITT, "moderado")
    idade = _numero(perfil.get("idade"), 10, 55)
    if not math.isnan(idade) and idade >= 35:
        pe("35 anos ou mais", None, "fator moderado nas diretrizes; o efeito da idade já entra no modelo", "moderado")

    if any(_parente_proximo(h) and "diabetes" in (h.get("condicao") or "").lower() for h in historico_familiar):
        fatores.append({"condicao": "diabetes_gestacional", "fator": "Mãe ou irmã com diabetes",
                        "risco_relativo_publicado": None, "fonte": "fator de risco reconhecido", "peso_diretriz": None})
    if not math.isnan(imc) and imc >= 30:
        fatores.append({"condicao": "diabetes_gestacional", "fator": "IMC de 30 ou mais antes da gravidez",
                        "risco_relativo_publicado": None, "fonte": "fator de risco reconhecido", "peso_diretriz": None})
    return fatores


def resumo_prevencao_pre_eclampsia(fatores: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Um fator alto ou dois moderados: critério usado nas diretrizes para conversar sobre prevenção."""
    de_pe = [f for f in fatores if f["condicao"] == "pre_eclampsia"]
    altos = sum(1 for f in de_pe if f["peso_diretriz"] == "alto")
    moderados = sum(1 for f in de_pe if f["peso_diretriz"] == "moderado")
    if altos >= 1 or moderados >= 2:
        return {
            "altos": altos, "moderados": moderados,
            "mensagem": ("Pelos critérios usados nas diretrizes de pré-natal (um fator alto ou dois moderados), "
                         "vale levar esses fatores para a sua equipe: eles mudam o cuidado, por exemplo com a "
                         "prevenção com AAS em dose baixa, que só a equipe pode indicar."),
        }
    return None


def _atipicidade(variaveis: Dict[str, Any]) -> Dict[str, Any]:
    pacote = _modelos_estado["atipicidade"]
    if pacote is None:
        return {"score": 0.0, "anomalo": False, "disponivel": False}
    try:
        import pandas as pd
        linha = {}
        for f in pacote["features"]:
            valor = variaveis.get(f)
            valor = valor[0] if isinstance(valor, list) else valor
            if valor is None or (isinstance(valor, float) and math.isnan(valor)):
                valor = pacote["medianas"].get(f, 0.0)
            linha[f] = float(valor)
        tabela = pd.DataFrame([linha], columns=pacote["features"])
        decisao = float(pacote["modelo"].decision_function(tabela)[0])
        anomalo = int(pacote["modelo"].predict(tabela)[0]) == -1
        return {"score": min(1.0, max(0.0, round(0.5 - decisao * 2.0, 2))), "anomalo": anomalo, "disponivel": True}
    except Exception as erro:
        logger.debug(f"Falha na atipicidade: {erro}")
        return {"score": 0.0, "anomalo": False, "disponivel": False}


def perfil_para_modelos(perfil_clinico: Any, imc_pre: Optional[float] = None) -> Dict[str, Any]:
    """Dicionário do cadastro clínico salvo, sem completar nada com valores inventados."""
    if perfil_clinico is None:
        return {}
    campos = ("idade", "estado_civil", "escolaridade", "gestacoes_anteriores", "partos_normais", "partos_cesareos",
              "perdas_gestacionais", "numero_fetos", "mes_inicio_prenatal", "uf_residencia",
              "pre_eclampsia_previa", "hipertensao_cronica", "diabetes_previo")
    dados = {c: getattr(perfil_clinico, c, None) for c in campos}
    if imc_pre is None:
        altura = getattr(perfil_clinico, "altura_cm", None)
        peso = getattr(perfil_clinico, "peso_pre_gestacional", None)
        if altura and peso:
            imc_pre = round(peso / ((altura / 100.0) ** 2), 1)
    dados["imc_pre_gestacional"] = imc_pre
    return dados


def calculate_maternal_risks(perfil: Dict[str, Any], historico_familiar: List[Dict[str, str]]) -> Dict[str, Any]:
    """Estimativas dos seis modelos v2, fatores clínicos e atipicidade do perfil."""
    carregar_modelos_ml()
    variaveis = montar_variaveis(perfil or {})
    condicoes = {nome: _estimar(nome, variaveis) for nome in NOMES_MODELOS}
    fatores = fatores_clinicos(perfil or {}, historico_familiar or [])
    atip = _atipicidade(variaveis)

    ordem = {"alto": 2, "moderado": 1, "baixo": 0}
    niveis = [c["nivel"] for c in condicoes.values() if c["nivel"]]
    pior = max(niveis, key=lambda n: ordem[n]) if niveis else None
    modelos_usados = [f"risco_{n}" for n, c in condicoes.items() if c["fonte"] == "modelo_v2"]
    if atip["disponivel"]:
        modelos_usados.append("atipicidade")

    return {
        "versao_modelos": "2.0",
        "tipo_modelo": "gradient_boosting_calibrado_sinasc_sih" if modelos_usados else "indisponivel",
        "modelos_ativos": modelos_usados,
        "condicoes": condicoes,
        "fatores_clinicos": fatores,
        "prevencao_pre_eclampsia": resumo_prevencao_pre_eclampsia(fatores),
        "nivel_risco_global": {"alto": "ALTO", "moderado": "MODERADO", "baixo": "HABITUAL"}.get(pior),
        "score_anomalia": atip["score"],
        "padrao_atipico_detectado": atip["anomalo"],
        "aviso_legal": DISCLAIMER_TEXT,
        "carimbo_samd_cfm": (
            "Triagem com suporte de IA supervisionada (SaMD Classe II / CFM nº 2.454/2026). "
            "Apoio estatístico à decisão médica. Diagnóstico e conduta sob responsabilidade exclusiva do médico assistente."
        ),
        "enquadramento_regulatorio": "SaMD Risco Médio (Classe II) - Resolução CFM nº 2.454/2026 e RDC Anvisa nº 657/2022",
    }


def obter_transparencia_clinica() -> Dict[str, Any]:
    """
    Relatório público de transparência (CFM 2.454/2026 e CDC) com as métricas
    REAIS do treino v2, lidas de metricas_modelos_v2.json. Até 15/10/2026 este
    relatório publicava números que não eram os do treino (ex.: AUC 0,84).
    """
    carregar_modelos_ml()
    metricas = (_modelos_estado.get("metricas") or {}).get("modelos", {})
    modelos = {}
    for nome in NOMES_MODELOS:
        m = metricas.get(nome, {})
        ponto = m.get("ponto_fn_primeiro", {})
        modelos[nome] = {
            "nome_clinico": DESCRICOES[nome]["titulo"],
            "o_que_estima": DESCRICOES[nome]["estima"],
            "algoritmo": "Gradient boosting (HistGradientBoosting, scikit-learn) com calibração isotônica",
            "base_dados": m.get("base"),
            "variaveis": [ROTULOS_VARIAVEIS.get(v, v) for v in m.get("variaveis", [])],
            "auc_roc": m.get("auc_roc"),
            "auc_roc_so_com_idade": m.get("auc_roc_so_idade"),
            "auc_pr": m.get("auc_pr"),
            "brier": m.get("brier"),
            "prevalencia_no_teste": m.get("prevalencia_teste"),
            "casos_no_teste": m.get("casos_teste"),
            "sensibilidade": ponto.get("sensibilidade"),
            "especificidade": ponto.get("especificidade"),
            "precisao": ponto.get("valor_preditivo_positivo"),
            "fracao_sinalizada_no_ponto": ponto.get("fracao_sinalizada"),
            "aviso": m.get("aviso"),
        }
    return {
        "sistema": "Nymphia Perinatal AI",
        "versao_protocolo": "2026.2",
        "versao_modelos": "2.0",
        "marco_regulatorio": "Resolução CFM nº 2.454/2026; Código de Defesa do Consumidor (Lei 8.078/1990); RDC Anvisa nº 657/2022",
        "classificacao_samd": "Software as a Medical Device (SaMD) de Risco Médio / Classe II",
        "finalidade_exclusiva": (
            "Estimativa estatística populacional e suporte informativo ao pré-natal. É PROIBIDO usar este sistema "
            "para diagnóstico ou prescrição sem a equipe de saúde (Art. 5º, §2º da CFM 2.454/2026)."
        ),
        "como_ler": (
            "Sensibilidade e especificidade estão no ponto de corte que pega 80% dos casos (prioridade de não deixar "
            "passar). AUC de 0,5 é acaso e de 1,0 é perfeito. Os modelos do SIH comparam internações (caso-controle), "
            "por isso mostram risco relativo à média, não porcentagem."
        ),
        "variaveis_excluidas": (_modelos_estado.get("metricas") or {}).get("variaveis_excluidas"),
        "carimbo_prontuario": (
            "Avaliação assistida por algoritmo supervisionado de IA (CFM 2.454/2026). "
            "Decisão diagnóstica e conduta terapêutica são privativas do médico obstetra assistente."
        ),
        "canal_revisao_humana": "/meus-dados/solicitar-revisao-ia",
        "artigo_lgpd_revisao": "Art. 20 da LGPD (Direito à Revisão Humana de Decisões Automatizadas)",
        "modelos": modelos,
    }
