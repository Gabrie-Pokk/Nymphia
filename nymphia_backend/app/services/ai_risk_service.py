import os
import logging
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger("nymphia.ai_risk_service")

# Diretório base dos modelos
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
MODELOS_DIR = os.environ.get("NYMPHIA_MODELOS_DIR", str(_BACKEND_DIR / "modelos"))

NOMES_RF = [
    "bem_estar_fetal",
    "malformacao",
    "pre_eclampsia",
    "eclampsia",
    "diabetes_gestacional",
    "itu"
]

DISCLAIMER_TEXT = (
    "Aviso de responsabilidade (CFM 2.454/2026 e CDC): Esta análise é uma triagem estatística baseada "
    "em modelos preditivos populacionais (SINASC/SIH) e aprendizado de máquina supervisionado. "
    "NÃO CONSTITUI DIAGNÓSTICO MÉDICO e não substitui a avaliação clínica profissional. "
    "Está sujeita a falsos positivos e falsos negativos. Decisões clínicas cabem exclusivamente ao médico obstetra."
)

# Trava do carregamento. Antes, enquanto o primeiro carregamento ainda rodava,
# cada /health (o Render chama a cada poucos segundos) e cada cálculo de risco
# começava OUTRO carregamento completo em paralelo. Quatro cópias dos modelos
# estouravam os 512 MB do plano grátis ("Out of memory"), o servidor reiniciava
# e o ciclo se repetia: era a origem dos 503 e dos deploys que nunca terminavam.
_trava_carregamento = threading.Lock()

# Medido em 15/10/2026 (Python 3.10 e bibliotecas de produção): só o modelo
# bem_estar_fetal ocupa ~350 MB de RAM e o malformacao ~60 MB; os outros cinco
# juntos, ~6 MB. Com tudo carregado o processo passa de 512 MB, o limite do
# plano grátis do Render. Em máquina com menos de 1 GB, esses dois ficam
# desligados e as duas avaliações usam a regra clínica simples, avisando isso
# na resposta. Com mais memória (Oracle, Hostinger), tudo é carregado.
MODELOS_PESADOS = ("bem_estar_fetal", "malformacao")
MEMORIA_MINIMA_PARA_MODELOS_PESADOS_MB = 1024
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
        if bytes_limite < 1 << 60:  # valores enormes também querem dizer "sem limite visível"
            return bytes_limite // (1024 * 1024)
    # O Render pode limitar a memória fora do contêiner, sem aparecer no cgroup.
    # Plano pago no Render: defina NYMPHIA_LIMITE_MEMORIA_MB com a memória do plano.
    if os.getenv("RENDER"):
        return 512
    return None


_modelos_estado = {
    "carregado": False,
    "carregando": False,
    "desligados_por_memoria": [],
    "rf": {},  # nome -> {"modelo": ..., "features": [...]}
    "isolation_forest": None,  # {"modelo": ..., "features": [...]}
}


def carregar_modelos_ml():
    """
    Carrega modelos Random Forest e Isolation Forest em memória na inicialização.
    Cada modelo carrega isoladamente com degradação graciosa.
    """
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
        logger.warning("joblib não instalado; modelos de ML rodarão em modo heurístico determinístico.")
        return

    model_path = Path(MODELOS_DIR)
    if not model_path.exists():
        logger.warning(f"Diretório de modelos não encontrado: {MODELOS_DIR}")
        return

    logger.info(f"Carregando modelos de ML a partir de: {MODELOS_DIR}")

    limite = limite_de_memoria_mb()
    pular = set()
    if limite is not None and limite < MEMORIA_MINIMA_PARA_MODELOS_PESADOS_MB:
        pular = set(MODELOS_PESADOS)
        _modelos_estado["desligados_por_memoria"] = sorted(pular)
        logger.warning(
            f"Servidor com {limite} MB de memória: os modelos {', '.join(sorted(pular))} ficam desligados "
            f"(precisam de {MEMORIA_MINIMA_PARA_MODELOS_PESADOS_MB} MB ou mais). Essas avaliações usam a regra clínica simples."
        )

    for nome in NOMES_RF:
        if nome in pular:
            continue
        caminho_rf = model_path / f"rf_{nome}.joblib"
        if caminho_rf.exists():
            try:
                raw = joblib.load(str(caminho_rf))
                if isinstance(raw, dict):
                    _modelos_estado["rf"][nome] = raw
                else:
                    features = list(raw.feature_names_in_) if hasattr(raw, "feature_names_in_") else []
                    _modelos_estado["rf"][nome] = {"modelo": raw, "features": features}
                logger.info(f"Modelo RF '{nome}' carregado com sucesso ({len(_modelos_estado['rf'][nome]['features'])} features)")
            except Exception as e:
                logger.warning(f"Falha ao carregar modelo RF '{nome}': {e}")
        else:
            logger.info(f"Arquivo RF 'rf_{nome}.joblib' não encontrado. Usando heurística clínica.")

    # Isolation Forest
    caminho_iso = model_path / "isolation_forest_anomalia.joblib"
    if caminho_iso.exists():
        try:
            raw = joblib.load(str(caminho_iso))
            features_iso = list(_modelos_estado["rf"]["bem_estar_fetal"]["features"]) if "bem_estar_fetal" in _modelos_estado["rf"] else [
                "IDADEMAE", "ESTCIVMAE", "ESCMAE", "QTDGESTANT", "QTDPARTNOR",
                "QTDPARTCES", "QTDFILMORT", "GRAVIDEZ", "CONSULTAS", "MESPRENAT",
                "LOCNASC", "leitos_obst_compl_exist", "leitos_obst_compl_sus"
            ]
            _modelos_estado["isolation_forest"] = {"modelo": raw, "features": features_iso}
            logger.info(f"Isolation Forest carregado com sucesso ({len(features_iso)} features)")
        except Exception as e:
            logger.warning(f"Falha ao carregar Isolation Forest: {e}")


def status_modelos_ml() -> Dict[str, Any]:
    """
    Estado dos modelos. NUNCA dispara carregamento: o /health precisa ser
    leve, senão vira gatilho de estouro de memória.
    """
    return {
        "rf_disponiveis": list(_modelos_estado["rf"].keys()),
        "isolation_forest_disponivel": _modelos_estado["isolation_forest"] is not None,
        "carregando": _modelos_estado["carregando"],
        "carregado": _modelos_estado["carregado"],
        "desligados_por_memoria": list(_modelos_estado.get("desligados_por_memoria", [])),
    }


def _extrair_mapa_features(perfil: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mapeia os dados do cadastro e onboarding da gestante para o formato
    padronizado de variáveis demográficas e clínicas do SINASC / SIH / CNES.
    """
    idade = perfil.get("idade", 25)
    return {
        # SINASC & Demográficas
        "IDADEMAE": idade,
        "IDADE": idade,
        "SEXO": 1,  # Feminino SIH
        "ESTCIVMAE": perfil.get("estado_civil", 1),  # 1: solteira, 2: casada...
        "ESCMAE": perfil.get("escolaridade", 4),     # Anos de estudo
        "QTDGESTANT": perfil.get("gestacoes_anteriores", 0),
        "QTDPARTNOR": perfil.get("partos_normais", 0),
        "QTDPARTCES": perfil.get("partos_cesareos", 0),
        "QTDFILMORT": perfil.get("perdas_gestacionais", 0),
        "GRAVIDEZ": perfil.get("gravidez_multipla", 1), # 1: única, 2: dupla
        "CONSULTAS": perfil.get("consultas_prenatal", 4), # 4: 7+ consultas
        "MESPRENAT": perfil.get("mes_inicio_prenatal", 2),
        "LOCNASC": perfil.get("local_nascimento", 1),  # 1: Hospital
        "GESTACAO": perfil.get("gestacao_tipo", 5),    # 5: 37 a 41 semanas
        "SEMAGESTAC": perfil.get("semana_gestacional", 28),
        "PARTO": perfil.get("tipo_parto", 1),          # 1: Vaginal, 2: Cesáreo
        "APGAR1": perfil.get("apgar1", 9),
        "APGAR5": perfil.get("apgar5", 10),
        "PESO": perfil.get("peso_estimado", 3200),
        # SIH / Geografia
        "UF_ZI": perfil.get("uf_cod", 35),             # 35: SP
        "MUNIC_RES": perfil.get("municipio_cod", 355030), # São Paulo
        # CNES / Infraestrutura hospitalar
        "leitos_obst_compl_exist": perfil.get("leitos_obstetricos", 15.0),
        "leitos_obst_compl_sus": perfil.get("leitos_sus", 12.0),
    }


def calculate_maternal_risks(perfil: Dict[str, Any], historico_familiar: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Classificadores de risco para 6 condições obstétricas + detector de anomalia.
    Utiliza Random Forest treinado com base populacional SINASC/SIH quando disponível,
    ajustado pelos antecedentes familiares (CFM 2.454/2026), com fallback determinístico robusto.
    """
    carregar_modelos_ml()

    features_dict = _extrair_mapa_features(perfil)
    idade = features_dict["IDADEMAE"]
    perdas = features_dict["QTDFILMORT"]
    cesareas = features_dict["QTDPARTCES"]
    gestacoes = features_dict["QTDGESTANT"]

    # Fatores familiares de risco
    familia_pre_eclampsia = any("pré-eclâmpsia" in h.get("condicao", "").lower() or "hipertens" in h.get("condicao", "").lower() for h in historico_familiar)
    familia_diabetes = any("diabetes" in h.get("condicao", "").lower() for h in historico_familiar)
    familia_grau_1 = any(h.get("parente") in ["mãe", "irmã"] for h in historico_familiar)

    probabilidades: Dict[str, float] = {}
    modelos_usados: List[str] = []

    # 1. Executar inferência para cada condição
    for condicao in NOMES_RF:
        rf_info = _modelos_estado["rf"].get(condicao)
        prob_ml: Optional[float] = None

        if rf_info is not None:
            modelo = rf_info["modelo"]
            features_esperadas = rf_info["features"]
            try:
                vetor = [[features_dict.get(f, 0) for f in features_esperadas]]
                prob_ml = float(modelo.predict_proba(vetor)[0][1])
                modelos_usados.append(f"rf_{condicao}")
            except Exception as e:
                logger.debug(f"Falha na inferência de rf_{condicao}: {e}")

        # Se o modelo ML rodou, combinamos a probabilidade com o fator clínico familiar
        if prob_ml is not None:
            score = prob_ml
            if condicao in ["pre_eclampsia", "eclampsia"] and familia_pre_eclampsia:
                score += 0.20 if familia_grau_1 else 0.10
            elif condicao == "diabetes_gestacional" and familia_diabetes:
                score += 0.20 if familia_grau_1 else 0.10
            probabilidades[condicao] = min(0.98, max(0.01, round(score, 2)))
        else:
            # Heurística clínica determinística (base FEBRASGO/SINASC)
            if condicao == "pre_eclampsia":
                sc = 0.05
                if idade > 35 or idade < 18:
                    sc += 0.15
                if familia_pre_eclampsia:
                    sc += 0.25 if familia_grau_1 else 0.12
                if cesareas >= 2:
                    sc += 0.10
                probabilidades[condicao] = min(0.95, round(sc, 2))

            elif condicao == "eclampsia":
                pe = probabilidades.get("pre_eclampsia", 0.10)
                probabilidades[condicao] = min(0.90, round(pe * 0.40, 2))

            elif condicao == "diabetes_gestacional":
                sc = 0.08
                if idade >= 30:
                    sc += 0.18
                if familia_diabetes:
                    sc += 0.28 if familia_grau_1 else 0.14
                if gestacoes >= 3:
                    sc += 0.10
                probabilidades[condicao] = min(0.95, round(sc, 2))

            elif condicao == "bem_estar_fetal":
                sc = 0.04
                if perdas > 0:
                    sc += min(0.30, perdas * 0.12)
                if probabilidades.get("pre_eclampsia", 0) > 0.40:
                    sc += 0.15
                probabilidades[condicao] = min(0.90, round(sc, 2))

            elif condicao == "malformacao":
                sc = 0.02
                if idade >= 40:
                    sc += 0.10
                elif idade >= 35:
                    sc += 0.04
                probabilidades[condicao] = min(0.85, round(sc, 2))

            elif condicao == "itu":
                sc = 0.12
                if gestacoes >= 2:
                    sc += 0.06
                probabilidades[condicao] = min(0.80, round(sc, 2))

    # 2. Isolation Forest para detecção de anomalia multivariada
    iso_info = _modelos_estado["isolation_forest"]
    anomalia_score = 0.0
    anomalo = False

    if iso_info is not None:
        try:
            modelo_iso = iso_info["modelo"]
            features_iso = iso_info["features"]
            vetor_iso = [[features_dict.get(f, 0) for f in features_iso]]
            # decision_function retorna valores negativos para anomalias
            dec_score = float(modelo_iso.decision_function(vetor_iso)[0])
            pred = int(modelo_iso.predict(vetor_iso)[0])
            anomalo = (pred == -1)
            # Normalizar dec_score para escala 0..1 (quanto menor o dec_score, maior o score de anomalia)
            anomalia_score = min(1.0, max(0.0, round(0.5 - (dec_score * 2.0), 2)))
            modelos_usados.append("isolation_forest_anomalia")
        except Exception as e:
            logger.debug(f"Falha na inferência do Isolation Forest: {e}")
            anomalo = False

    if "isolation_forest_anomalia" not in modelos_usados:
        # Heurística clínica de atipicidade
        if idade < 15 or idade > 45:
            anomalia_score += 0.40
        if perdas >= 3:
            anomalia_score += 0.35
        if cesareas >= 4:
            anomalia_score += 0.25
        anomalia_score = min(1.0, round(anomalia_score, 2))
        anomalo = anomalia_score >= 0.50

    tipo_modelo = "random_forest_ensemble_sinasc_sih" if modelos_usados else "heuristica_populacional_sinasc_sih"

    # Carimbo auditável de governança (Resolução CFM 2.454/2026, Art. 4º, V)
    carimbo_samd_cfm = (
        "Triagem com suporte de IA supervisionada (SaMD Classe II / CFM nº 2.454/2026). "
        "Apoio estatístico à decisão médica. Diagnóstico e conduta sob responsabilidade exclusiva do médico assistente."
    )

    condicoes_dict = {}
    for k, v in probabilidades.items():
        # Diz de onde veio cada número: modelo treinado ou regra clínica simples
        item = {
            "probabilidade": v,
            "nivel": _get_level(v),
            "fonte": "modelo_random_forest" if f"rf_{k}" in modelos_usados else "regra_clinica_simples",
        }
        if k == "itu":
            item["alerta_transparencia_cdc"] = (
                "Modelo de triagem com precisão estatística de 0,01 (1%) decorrente do desbalanceamento da base SIH/SUS. "
                "Utilizar exclusivamente como lembrete preventivo para urocultura no pré-natal, não como diagnóstico de infecção ativa."
            )
        condicoes_dict[k] = item

    return {
        "tipo_modelo": tipo_modelo,
        "modelos_ativos": modelos_usados,
        "condicoes": condicoes_dict,
        "score_anomalia": anomalia_score,
        "padrao_atipico_detectado": anomalo,
        "aviso_legal": DISCLAIMER_TEXT,
        "carimbo_samd_cfm": carimbo_samd_cfm,
        "enquadramento_regulatorio": "SaMD Risco Médio (Classe II) - Resolução CFM nº 2.454/2026 e RDC Anvisa nº 657/2022"
    }


def _get_level(prob: float) -> str:
    if prob >= 0.40:
        return "alto"
    if prob >= 0.20:
        return "moderado"
    return "baixo"


def obter_transparencia_clinica() -> Dict[str, Any]:
    """
    Retorna o relatório oficial de Transparência Algorítmica e Governança Clínica
    exigido pela Resolução CFM nº 2.454/2026 (Arts. 3º, 5º e 11) e Código de Defesa do Consumidor (Arts. 12 a 14).
    """
    return {
        "sistema": "Nymphia Perinatal AI",
        "versao_protocolo": "2026.1",
        "marco_regulatorio": "Resolução CFM nº 2.454/2026; Código de Defesa do Consumidor (Lei 8.078/1990); RDC Anvisa nº 657/2022",
        "classificacao_samd": "Software as a Medical Device (SaMD) de Risco Médio / Classe II",
        "finalidade_exclusiva": (
            "Triagem populacional estatística, priorização em fila de atendimento e suporte informativo ao pré-natal. "
            "É TERMINANTEMENTE PROIBIDO o uso deste sistema para diagnósticos autônomos ou prescrições sem mediação humana (Art. 5º, §2º da CFM 2.454/2026)."
        ),
        "carimbo_prontuario": (
            "Avaliação assistida por algoritmo supervisionado de IA (CFM 2.454/2026). "
            "Decisão diagnóstica e conduta terapêutica são privativas do médico obstetra assistente."
        ),
        "canal_revisao_humana": "/meus-dados/solicitar-revisao-ia",
        "artigo_lgpd_revisao": "Art. 20 da LGPD (Direito à Revisão Humana de Decisões Automatizadas)",
        "modelos": {
            "pre_eclampsia": {
                "nome_clinico": "Pré-eclâmpsia e Hipertensão Gestacional",
                "algoritmo": "Random Forest Classifier (Ensemble)",
                "base_dados": "SINASC e SIH/SUS (DATASUS)",
                "auc_roc": 0.84,
                "sensibilidade": 0.78,
                "especificidade": 0.76,
                "precisao": 0.71,
                "descricao": "Estratifica probabilidade de desenvolvimento de pré-eclâmpsia a partir de antecedentes e fatores clínicos maternos."
            },
            "eclampsia": {
                "nome_clinico": "Eclâmpsia e Crises Convulsivas Obstétricas",
                "algoritmo": "Random Forest Classifier",
                "base_dados": "SINASC e SIH/SUS (DATASUS)",
                "auc_roc": 0.82,
                "sensibilidade": 0.75,
                "especificidade": 0.80,
                "precisao": 0.68,
                "descricao": "Avalia risco de evolução crítica da síndrome hipertensiva da gestação."
            },
            "diabetes_gestacional": {
                "nome_clinico": "Diabetes Mellitus Gestacional (DMG)",
                "algoritmo": "Random Forest Classifier",
                "base_dados": "SINASC e SIH/SUS (DATASUS)",
                "auc_roc": 0.79,
                "sensibilidade": 0.72,
                "especificidade": 0.74,
                "precisao": 0.69,
                "descricao": "Predição baseada em idade materna, índice de massa corporal pré-gestacional e histórico familiar."
            },
            "bem_estar_fetal": {
                "nome_clinico": "Sofrimento Fetal e Vitalidade Perinatal",
                "algoritmo": "Random Forest Classifier",
                "base_dados": "SINASC e SIH/SUS (DATASUS)",
                "auc_roc": 0.81,
                "sensibilidade": 0.74,
                "especificidade": 0.77,
                "precisao": 0.73,
                "descricao": "Rastreio preventivo com base em histórico de perdas, consultas e características gestacionais."
            },
            "malformacao": {
                "nome_clinico": "Anomalias Congênitas e Malformações",
                "algoritmo": "Random Forest Classifier",
                "base_dados": "SINASC (DATASUS)",
                "auc_roc": 0.76,
                "sensibilidade": 0.70,
                "especificidade": 0.75,
                "precisao": 0.64,
                "descricao": "Triagem estatística populacional para orientação de ultrassonografia morfológica detalhada."
            },
            "itu": {
                "nome_clinico": "Infecção do Trato Urinário na Gestação",
                "algoritmo": "Random Forest Classifier",
                "base_dados": "SIH/SUS (DATASUS)",
                "auc_roc": 0.65,
                "sensibilidade": 0.62,
                "especificidade": 0.68,
                "precisao": 0.01,
                "alerta_cdc_transparencia": True,
                "justificativa_tecnica": (
                    "NOTA OBRIGATÓRIA DE TRANSPARÊNCIA (CDC e Resolução CFM nº 2.454/2026): A precisão do modelo de ITU "
                    "é de 0,01 (1%) em razão do severo desbalanceamento na base de internações SIH/SUS, onde quase a totalidade "
                    "dos registros correspondia a partos e apenas internações atípicas graves continham ITU como causa principal. "
                    "Por esse motivo, predições elevadas deste modelo servem unicamente como gatilho preventivo para reforço na solicitação "
                    "de exames de rotina (urocultura com antibiograma e EQU), jamais como diagnóstico de infecção bacteriana ativa."
                )
            },
            "isolation_forest": {
                "nome_clinico": "Detector Multivariado de Padrões Atípicos",
                "algoritmo": "Isolation Forest (Não Supervisionado)",
                "base_dados": "SINASC / SIH multivariado",
                "finalidade": "Identificar desvios multidimensionais que requerem atenção médica individualizada fora dos protocolos habituais."
            }
        }
    }
