import re
from typing import Tuple, Optional
from app.services.rules_engine import analyze_urgency

# 1. Termos Proibidos Estritos (Ofensas graves, assédio, calúnias, termos chulos e linguagem tóxica)
TERMOS_PROIBIDOS = [
    r"\b(vadi[ao]|put[ao]|vagabund[ao]|desgra[çc][ao]|merda|porra|caralho|idiota|imbecil|burr[ao]|arrombado|fdp|filh[ao] da puta|vai se foder|chupa)\b",
    r"\b(abortar|abortivo|cytotec|misoprostol|ch[aá] de canela para descer|mifepristone|agulha para abortar)\b",
    r"\b(maconha|coca[ií]na|droga|entorpecente|beck|erva|ecstasy|crack|loló|lança perfume)\b",
    r"\b(compre remedio|venda de receita|comprar receita|sem receita medica|vendo tarja preta)\b",
]

# 2. Padrões de Automedicação Perigosa na Gravidez (contraindicados pela FEBRASGO e MS)
PADROES_AUTOMEDICACAO = [
    r"(toma|tome|usa|use|tomar)\s+[\w\s]{1,25}\s*(mg|comprimido|comprimidos|gotas|dose|pomada|injet[aá]vel)",
    r"(indico|recomendo|aconselho)\s+(tomar|usar)\s+(rem[eé]dio|medicamento|anti-inflamat[oó]rio|antibi[oó]tico|calmante|antidepressivo)",
    r"(aspirina|ibuprofeno|nimesulida|diclofenaco|dipirona|paracetamol)\s+(em dose alta|de hora em hora|para dor|faz bem|pode tomar sem medo)",
    r"(mistura|misture)\s+[\w\s]{1,20}\s*(com dipirona|com paracetamol|com calmante)",
]

# 3. Padrões que requerem AVISO CLÍNICO oficial em rodapé (sem bloquear a postagem)
PADROES_AVISO_CLINICO = [
    r"(exame|hemograma|ultrassom|laudo|press[aã]o|glicemia|totg|urocultura|leuc[oó]citos)",
    r"(m[eé]dico me passou|obstetra disse|prescri[çc][aã]o|receita do posto)",
    r"(minha press[aã]o deu|meu exame deu|taxa de)",
]

def moderate_community_content(texto: str) -> Tuple[bool, Optional[str], bool]:
    """
    Moderação de segurança clínica e comunitária em 3 camadas:
    Retorna: (bloqueado: bool, motivo: Optional[str], sinalizado_aviso: bool)
    - bloqueado = True: conteúdo completamente proibido (ofensas, abortivos ilegais, drogas, prescrições de automedicação perigosa).
    - sinalizado_aviso = True: conteúdo permitido, mas recebe chancela educativa de rodapé.
    """
    if not texto:
        return False, None, False

    texto_lower = texto.lower()

    # Checagem de Emergência Médica Crítica
    # Se uma usuária relata emergência com risco de vida no fórum comunitário,
    # devemos orientá-la a buscar socorro imediato ao invés de postar e esperar resposta.
    is_urgent, alerts, _ = analyze_urgency(texto)
    if is_urgent:
        motivo_alerta = ", ".join(alerts) if alerts else "sintoma agudo"
        return (
            True,
            f"Alerta de Segurança: Seu relato indica sinais que necessitam de atendimento médico imediato ({motivo_alerta}). Por favor, dirija-se à maternidade mais próxima ou ligue 192 (SAMU) imediatamente.",
            False
        )

    # 1. Termos Proibidos (ofensas, toxidade, substâncias ilícitas, abortivos clandestinos)
    for pattern in TERMOS_PROIBIDOS:
        if re.search(pattern, texto_lower, re.IGNORECASE):
            return (
                True,
                "A publicação contém termos impróprios, substâncias não permitidas ou linguagem contrária às Diretrizes de Respeito e Segurança da Comunidade Nymphia.",
                False
            )

    # 2. Automedicação Perigosa
    for pattern in PADROES_AUTOMEDICACAO:
        if re.search(pattern, texto_lower, re.IGNORECASE):
            return (
                True,
                "Por segurança de mães e bebês, não é permitido indicar dosagens, prescrever medicamentos ou sugerir automedicação a outras gestantes na comunidade.",
                False
            )

    # 3. Padrões de aviso clínico educativo
    for pattern in PADROES_AVISO_CLINICO:
        if re.search(pattern, texto_lower, re.IGNORECASE):
            return False, None, True

    return False, None, False
