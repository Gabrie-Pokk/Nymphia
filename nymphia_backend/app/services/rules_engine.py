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

def analyze_urgency(text: str) -> Tuple[bool, List[str], str]:
    """
    Deterministic clinical urgency rule engine.
    Runs in 0ms without external dependencies.
    Never formulates output as a diagnosis.
    """
    if not text:
        return False, [], ""

    text_lower = text.lower()
    alerts: List[str] = []

    for pattern, description in URGENCY_PATTERNS:
        if re.search(pattern, text_lower):
            alerts.append(description)

    is_urgent = len(alerts) > 0
    guidance = ""

    if is_urgent:
        alerts_text = "; ".join(alerts)
        guidance = (
            f"ALERTA CLÍNICO DE URGÊNCIA: Foram identificados sinais que requerem avaliação imediata "
            f"({alerts_text}). Isto não é um diagnóstico, mas um indicativo de que você deve buscar "
            f"imediatamente o pronto atendimento obstétrico de sua maternidade ou acionar o SAMU pelo número 192."
        )

    return is_urgent, alerts, guidance
