import re
from typing import Tuple, Dict, Any, List
from app.services.rules_engine import analyze_urgency

CLINICAL_KNOWLEDGE_BASE = {
    "toxoplasmose": (
        "TOXOPLASMOSE GESTACIONAL (Protocolo FEBRASGO/MS): "
        "A toxoplasmose congênita pode causar complicações coriorretinianas e neurológicas no feto. "
        "Medidas preventivas essenciais: consumir apenas carnes bem passadas (>66°C), higienizar rigorosamente "
        "frutas e vegetais com hipoclorito de sódio, não manusear caixas de areia de gatos (ou usar luvas e lavar as mãos), "
        "e beber apenas água filtrada ou fervida. Caso apresente sorologia IgM positiva ou linfadenopatia cervical, "
        "é indispensável investigação imediata e eventual introdução precoce de espiramicina pelo obstetra."
    ),
    "hipertensao": (
        "DOENÇAS HIPERTENSIVAS NA GESTAÇÃO (FEBRASGO): "
        "A hipertensão gestacional e a pré-eclâmpsia caracterizam-se por pressão arterial >= 140x90 mmHg. "
        "Sinais de iminência de eclâmpsia incluem cefaleia frontal intensa e persistente, alterações visuais (escotomas, visão turva), "
        "dor epigástrica intensa ou no hipocôndrio direito, e edema súbito de face e mãos. "
        "Qualquer um desses sinais exige aferição imediata da pressão e ida a uma maternidade."
    ),
    "diabetes": (
        "DIABETES MELLITUS GESTACIONAL (MS/OMS): "
        "Alterações na glicemia de jejum (>= 92 mg/dL no 1º trimestre) ou no TOTG 75g indicam necessidade "
        "de acompanhamento nutricional estrito e automonitorização da glicemia capilar. O controle glicêmico adequado "
        "previne macrossomia fetal e polidrâmnio."
    ),
    "infeccoes": (
        "INFECÇÕES NA GESTAÇÃO (MS): "
        "Infecções urinárias (mesmo bacteriúria assintomática) aumentam o risco de contrações precoces e parto prematuro. "
        "Sintomas como ardência ao urinar, urina escura ou com odor forte exigem urocultura e antibióticoterapia prescrita pelo médico."
    ),
    "hemorragias": (
        "HEMORRAGIAS OBSTÉTRICAS (FEBRASGO): "
        "Qualquer perda sanguínea por via vaginal durante a gravidez é considerada anormal até que seja avaliada por profissional. "
        "No 1º trimestre pode indicar ameaça de abortamento ou gestação ectópica; no 3º trimestre, descolamento prematuro de placenta "
        "ou placenta prévia. Requer atendimento médico imediato."
    ),
    "trabalho_parto": (
        "TRABALHO DE PARTO PREMATURO (OMS): "
        "Contrações regulares e dolorosas (mais de 2 a 3 em 10 minutos que não cedem com repouso), cólicas semelhantes às menstruais "
        "ou perda do tampão mucoso/líquido antes de 37 semanas exigem avaliação tocoginecológica imediata."
    ),
    "saude_mental": (
        "SAÚDE MENTAL PERINATAL (MS/OMS): "
        "Ansiedade severa, insônia persistente, tristeza profunda e sentimento de desamparo são comuns e tratáveis. "
        "Não hesite em compartilhar seus sentimentos com sua equipe de saúde ou buscar acolhimento psicológico."
    ),
    "tireoide": (
        "DISFUNÇÕES DA TIREOIDE NA GESTAÇÃO: "
        "Hipotireoidismo não compensado (TSH elevado) pode afetar o desenvolvimento cognitivo fetal. O acompanhamento laboratorial "
        "periódico e o ajuste da dose de levotiroxina pelo especialista são fundamentais."
    ),
    "sinais_gerais": (
        "SINAIS DE ALERTA GERAIS (Caderneta da Gestante / MS): "
        "Febre alta, vômitos incoercíveis com desidratação, dor em baixo ventre intensa ou ausência de movimentos do bebê por mais de "
        "12 horas (no 3º trimestre) são motivos para procurar o pronto atendimento."
    )
}

def generate_chat_response(message: str, recusa_ia: bool = False) -> Tuple[str, bool, str]:
    """
    Gera resposta conversacional segura.
    Regra 1: Se detectar urgência física, responde IMEDIATAMENTE sem LLM.
    Regra 2: Nunca diagnostica; aponta padrão e orienta avaliação clínica.
    Regra 3: Consulta base curada FEBRASGO/MS/OMS.
    """
    is_urgent, alerts, urgency_guidance = analyze_urgency(message)
    if is_urgent:
        return urgency_guidance, True, "regras_urgencia"

    msg_lower = message.lower()

    # Special check for Toxoplasmosis
    if "toxoplasmose" in msg_lower or "gato" in msg_lower or "carne crua" in msg_lower or "areia do gato" in msg_lower:
        response = (
            f"{CLINICAL_KNOWLEDGE_BASE['toxoplasmose']}\n\n"
            "Orientação de cuidado: Caso tenha dúvidas sobre exames sorológicos recentes (IgG e IgM), "
            "leve os resultados para o seu obstetra na próxima consulta."
        )
        return response, False, "base_clinica_ia"

    # Match topic in knowledge base
    for topic, text in CLINICAL_KNOWLEDGE_BASE.items():
        if topic == "toxoplasmose":
            continue
        keywords = {
            "hipertensao": ["pressao", "pressão", "pre-eclampsia", "dor de cabeça", "inchaco", "inchaço"],
            "diabetes": ["glicose", "glicemia", "acucar", "açúcar", "diabetes", "doce"],
            "infeccoes": ["urina", "ardencia", "queimacao ao urinar", "xixi", "infeccao", "infecção"],
            "hemorragias": ["sangue", "sangramento", "corrimento escuro", "borra de cafe"],
            "trabalho_parto": ["contracao", "contração", "colica", "cólica", "barriga dura", "parto"],
            "saude_mental": ["triste", "ansiosa", "medo", "choro", "angustia", "desespero"],
            "tireoide": ["tireoide", "tsh", "t4", "hipotireoidismo"],
            "sinais_gerais": ["febre", "vomito", "vômito", "movimento", "chute"]
        }
        if any(kw in msg_lower for kw in keywords.get(topic, [])):
            response = (
                f"{text}\n\n"
                "Lembre-se: Este é um suporte informativo baseado nas diretrizes clínicas de saúde gestacional. "
                "Qualquer sintoma novo ou persistente deve ser reportado ao seu médico na consulta de pré-natal."
            )
            return response, False, "base_clinica_ia"

    # Default supportive response
    default_resp = (
        "Olá! Estou aqui para acompanhar sua jornada e esclarecer dúvidas com base nas diretrizes do Ministério da Saúde "
        "e da FEBRASGO. Você pode me contar como está se sentindo fisicamente, compartilhar dúvidas sobre alimentação, vacinas "
        "ou exames de rotina. "
        "\n\nImportante: Cada gestação é única. Minhas respostas têm propósito de orientação e apoio, "
        "não substituindo as orientações e diagnósticos do seu profissional de saúde."
    )
    return default_resp, False, "base_clinica_ia"
