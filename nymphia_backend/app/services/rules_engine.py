import re
from typing import List, Tuple

# Pre-compiled urgency patterns (accents handled or stripped)
URGENCY_PATTERNS = [
    (r"(sangra|sangue|hemorragia)", "Sangramento genital ativo"),
    (r"(dor.*cabec.*(forte|intensa|insuportavel)|cefaleia.*(forte|intensa)|escotoma|pontos.*brilhante|visao.*(turva|embacada))", "Sinais neurológicos / suspeita de pré-eclâmpsia grave"),
    (r"(dor.*(estomago|boca do estomago|barra|epigastr))", "Dor epigástrica / em barra (alerta pré-eclâmpsia)"),
    (r"(bolsa.*romp|perda.*liquido|liquido.*(escorr|escorrendo|saindo))", "Ruptura de membranas / amniorrexe prematura"),
    (r"(bebe.*(nao|parou).*mex|pouco.*movimento|parou.*mexer|sem.*movimento)", "Diminuição ou ausência de movimentação fetal"),
    (r"(febre.*(alta|38|39)|calafrio.*intenso)", "Pirexia / suspeita de infecção aguda"),
    (r"(pressao.*(14|15|16|17|18|alta|muito alta))", "Pico hipertensivo"),
    (r"(convuls|desmai|perda.*conscienc)", "Crise convulsiva / síncope")
]

# Exclusões seguras para termos que contêm 'sangue' em contexto não hemorrágico
EXCLUSOES_SANGUE = [
    r"exame\s+(de\s+)?sangue",
    r"coleta\s+(de\s+)?sangue",
    r"amostra\s+(de\s+)?sangue",
    r"tipo\s+(sangu[ií]neo|de\s+sangue)",
    r"tubo\s+de\s+sangue",
    r"press[aã]o\s+do\s+sangue"
]

def analyze_urgency(text: str) -> Tuple[bool, List[str], str]:
    """
    Deterministic clinical urgency rule engine.
    Runs in 0ms without external dependencies.
    Never formulates output as a diagnosis.
    """
    if not text:
        return False, [], ""

    text_lower = text.lower()

    # Normaliza exclusões laboratoriais para evitar falso positivo em exames de rotina
    text_analise = text_lower
    for exc in EXCLUSOES_SANGUE:
        text_analise = re.sub(exc, "exame_laboratorial", text_analise)

    alerts: List[str] = []

    for pattern, description in URGENCY_PATTERNS:
        if re.search(pattern, text_analise):
            alerts.append(description)

    is_urgent = len(alerts) > 0

    guidance = ""
    if is_urgent:
        guidance = (
            f"ALERTA CLÍNICO DE URGÊNCIA: Foram identificados sinais que requerem avaliação imediata "
            f"({', '.join(alerts)}). Isto não é um diagnóstico. Dirija-se imediatamente à emergência "
            f"obstétrica mais próxima ou acione o SAMU 192."
        )

    return is_urgent, alerts, guidance
