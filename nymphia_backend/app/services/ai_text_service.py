"""
Classificação do texto livre da gestante por palavras-chave.

Lê o texto do check-in e da conversa e marca categorias (ansiedade, tristeza,
estresse, medo, sintoma físico, bem-estar) quando aparece alguma palavra da
lista, com tolerância a erros de digitação. Não é modelo de IA: o BERTimbau
foi retirado em 16/10/2026 porque nunca rodou no servidor (precisava de mais
memória do que o plano tem). Os sinais de urgência ficam no motor de regras
(app/services/rules_engine.py), que não depende deste arquivo.
"""
import re
import difflib
import unicodedata
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger("nymphia.ai_text_service")

def remover_acentos(texto: str) -> str:
    """Remove diacríticos e acentos da língua portuguesa."""
    nfkd = unicodedata.normalize('NFKD', texto)
    return u"".join([c for c in nfkd if not unicodedata.combining(c)])

def normalizar_grafia_ptbr(texto: str) -> str:
    """
    Normaliza erros ortográficos comuns, variações fonéticas e gírias
    usadas por gestantes no Brasil (ex: 'enjouo' -> 'enjoo', 'mau' -> 'mal', 'bariga' -> 'barriga').
    """
    if not texto:
        return ""
    
    t = remover_acentos(texto.lower().strip())

    # Reduz repetições exageradas de caracteres (ex: 'enjoooo' -> 'enjoo')
    t = re.sub(r'([a-z])\1{2,}', r'\1\1', t)

    # 1. Variações fonéticas de enjoo e náuseas
    t = re.sub(r'\benjouo\b', 'enjoo', t)
    t = re.sub(r'\benjoada\b', 'enjoo', t)
    t = re.sub(r'\benjoando\b', 'enjoo', t)
    t = re.sub(r'\benjoo[us]?\b', 'enjoo', t)
    t = re.sub(r'\bnauze[as]?\b', 'nausea', t)
    t = re.sub(r'\banseia\b', 'ansia', t)
    t = re.sub(r'\bancia\b', 'ansia', t)

    # 2. Variações de mal / mau estar ("sentindo mau" -> "sentindo mal")
    t = re.sub(r'\b(sentindo|passando|estou|to|tô|ficando|corpo)\s+mau\b', r'\1 mal', t)
    t = re.sub(r'\bme\s+sinto\s+mau\b', 'me sinto mal', t)
    t = re.sub(r'\bto\s+mal\b', 'estou mal', t)

    # 3. Variações anatômicas e de dores
    t = re.sub(r'\bduendo\b', 'doendo', t)
    t = re.sub(r'\bbariga\b', 'barriga', t)
    t = re.sub(r'\bmecher\b', 'mexer', t)
    t = re.sub(r'\bmecheu\b', 'mexeu', t)
    t = re.sub(r'\binxad[ao]s?\b', 'inchado', t)
    t = re.sub(r'\bprecao\b', 'pressao', t)
    t = re.sub(r'\bcolic[as]?\b', 'colica', t)
    t = re.sub(r'\bvomitei\b', 'vomito', t)
    t = re.sub(r'\bvomitando\b', 'vomito', t)
    t = re.sub(r'\bremedio[s]?\b', 'medicamento', t)
    t = re.sub(r'\bramedio[s]?\b', 'medicamento', t)

    return t

def termo_contido_fuzzy(texto_normalizado: str, termos_referencia: List[str], limiar: float = 0.82) -> bool:
    """
    Verifica se o texto contém algum dos termos de referência, tolerando
    pequenos erros de digitação (distância de Levenshtein/similaridade de sequência).
    """
    palavras = re.findall(r'[a-z]+', texto_normalizado)
    for ref in termos_referencia:
        ref_norm = remover_acentos(ref.lower())
        # 1. Match direto como substring
        if ref_norm in texto_normalizado:
            return True
        # 2. Match difuso por palavra
        for p in palavras:
            if len(p) >= 4 and len(ref_norm) >= 4:
                sim = difflib.SequenceMatcher(None, p, ref_norm).ratio()
                if sim >= limiar:
                    return True
    return False

EMOTION_KEYWORDS = {
    "ansiedade": [
        "ansios", "angusti", "nervos", "preocupad", "inquiet", "afli", "coracao acelerado", 
        "panico", "palpitacao", "crise", "agoniada"
    ],
    "tristeza_desanimo": [
        "trist", "chor", "desanim", "deprim", "abatid", "desolad", "sem vontade", "sem energia",
        "pra baixo", "angustia", "vontade de sumir", "desesper"
    ],
    "estresse_sobrecarga": [
        "estress", "cansad", "esgotad", "sobrecarreg", "irritad", "nao aguento mais", "pressao demais",
        "sem paciencia", "exaust"
    ],
    "medo_inseguranca": [
        "medo", "pavor", "assustad", "insegur", "temor", "com receio", "perigo", "sera que e normal"
    ],
    "sintoma_fisico": [
        "dor", "sangrament", "nausea", "enjoo", "tontur", "incha", "colica", "queima", "azia",
        "falta de ar", "visao", "mexer", "vomito", "sentindo mal", "passando mal", "indispost",
        "fraca", "moleza", "febre", "dor de cabeca", "lombar", "estomago"
    ],
    "bem_estar": [
        "me sinto otima", "muito bem", "estou bem", "feliz", "alegr", "tranquil", "animad",
        "calm", "paz", "tudo certo", "grata", "maravilhosa", "dia maravilhoso"
    ]
}

def classify_text_emotions(text: str) -> Tuple[Dict[str, float], List[str]]:
    """
    Marca as categorias citadas no texto, tolerando erros de escrita.

    Devolve (marcas, categorias): em marcas, 1.0 quando alguma palavra da
    categoria apareceu e 0.0 quando não. Não é probabilidade: antes o valor
    subia com o número de palavras (0,55 + 0,15 por palavra) e parecia saída
    de modelo.
    """
    if not text:
        return {}, []

    text_normalizado = normalizar_grafia_ptbr(text)
    scores: Dict[str, float] = {}
    active_categories: List[str] = []

    # Checa negações de bem-estar (ex: "não estou bem", "nada bem", "mal")
    tem_negacao_bem_estar = bool(re.search(r'\b(nao|nada|nem um pouco)\s+(estou|to|me sinto)?\s*bem\b', text_normalizado))
    tem_mal_estar = bool(re.search(r'\b(mal|ruim|pessim[ao]|indispost[ao]|frac[ao]|moleza)\b', text_normalizado))

    for category, patterns in EMOTION_KEYWORDS.items():
        if category == "bem_estar" and (tem_negacao_bem_estar or tem_mal_estar):
            scores[category] = 0.0
            continue

        matches = 0
        for pattern in patterns:
            pat_norm = remover_acentos(pattern.lower())
            if re.search(pat_norm, text_normalizado):
                matches += 1
            elif termo_contido_fuzzy(text_normalizado, [pat_norm], limiar=0.82):
                matches += 1

        if matches > 0:
            scores[category] = 1.0
            active_categories.append(category)
        else:
            scores[category] = 0.0

    # Se a gestante relatou mal-estar expresso e sintoma_fisico não pontuou, garante ativação
    if tem_mal_estar and "sintoma_fisico" not in active_categories:
        scores["sintoma_fisico"] = 1.0
        active_categories.append("sintoma_fisico")

    # Se nada pontuou, o estado é neutro: nunca marcar "bem_estar" por padrão
    if not active_categories:
        active_categories = ["neutro"]

    return scores, active_categories

