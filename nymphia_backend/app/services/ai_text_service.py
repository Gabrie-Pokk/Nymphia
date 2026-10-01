import os
import re
import difflib
import unicodedata
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger("nymphia.ai_text_service")

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
MODELOS_DIR = os.environ.get("NYMPHIA_MODELOS_DIR", str(_BACKEND_DIR / "modelos"))
BERTIMBAU_DIR = Path(MODELOS_DIR) / "bertimbau_nymphia" / "modelo_final"

BERTIMBAU_CATEGORIAS = [
    "ansiedade",
    "tristeza_desanimo",
    "estresse_sobrecarga",
    "medo_inseguranca",
    "bem_estar",
    "sintoma_fisico"
]

_bert_estado = {
    "tentado": False,
    "disponivel": False,
    "tokenizer": None,
    "modelo": None,
}

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

def carregar_bertimbau():
    """Tenta carregar o modelo BERTimbau ajustado localmente ou baixa via URL."""
    if _bert_estado["tentado"]:
        return

    _bert_estado["tentado"] = True

    # 1. Garante que os pesos foram baixados ou descompactados no disco
    try:
        from app.services.model_downloader import garantir_bertimbau_presente
        garantir_bertimbau_presente()
    except Exception as e:
        logger.warning(f"Verificação de download do BERTimbau retornou: {e}")

    if not BERTIMBAU_DIR.exists():
        logger.info(f"Pasta do BERTimbau não encontrada em {BERTIMBAU_DIR}. Operando com motor de regras regex.")
        return

    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        import torch
        logger.info(f"Carregando BERTimbau a partir de: {BERTIMBAU_DIR}")
        _bert_estado["tokenizer"] = AutoTokenizer.from_pretrained(str(BERTIMBAU_DIR))
        raw_model = AutoModelForSequenceClassification.from_pretrained(str(BERTIMBAU_DIR))

        # Quantização dinâmica INT8: reduz memória de ~800MB para ~180MB (essencial para não estourar RAM no Render)
        try:
            _bert_estado["modelo"] = torch.quantization.quantize_dynamic(
                raw_model, {torch.nn.Linear}, dtype=torch.qint8
            )
            logger.info("Quantização dinâmica int8 aplicada ao BERTimbau (inferência leve em CPU).")
        except Exception as q_err:
            logger.warning(f"Quantização dinâmica int8 não pôde ser aplicada ({q_err}); usando modelo original.")
            _bert_estado["modelo"] = raw_model

        _bert_estado["modelo"].eval()
        _bert_estado["disponivel"] = True
        logger.info("BERTimbau carregado com sucesso para inferência em CPU.")
    except Exception as e:
        logger.warning(f"Não foi possível inicializar BERTimbau ({e}). Usando fallback de regras determinísticas.")


def bertimbau_disponivel() -> bool:
    carregar_bertimbau()
    return _bert_estado["disponivel"]


def classify_text_emotions(text: str) -> Tuple[Dict[str, float], List[str]]:
    """
    Classificador de conteúdo emocional e sintomas com tolerância ortográfica
    e margem de erro na escrita da gestante.
    """
    if not text:
        return {}, []

    carregar_bertimbau()

    # 1. Inferência com BERTimbau se disponível
    if _bert_estado["disponivel"] and _bert_estado["tokenizer"] and _bert_estado["modelo"]:
        try:
            import torch
            tok = _bert_estado["tokenizer"]
            model = _bert_estado["modelo"]
            inputs = tok(text, return_tensors="pt", truncation=True, max_length=96)
            with torch.no_grad():
                saida = model(**inputs)
            probs = torch.sigmoid(saida.logits)[0].tolist()
            scores = {cat: round(float(p), 3) for cat, p in zip(BERTIMBAU_CATEGORIAS, probs)}
            active = [cat for cat, p in scores.items() if p >= 0.35]
            if not active:
                active = ["neutro"]
            return scores, active
        except Exception as e:
            logger.warning(f"Falha na inferência do BERTimbau ({e}), usando motor de regras difusas.")

    # 2. Motor determinístico enriquecido com tolerância a erros e ortografia fonética
    text_normalizado = normalizar_grafia_ptbr(text)
    scores: Dict[str, float] = {}
    active_categories: List[str] = []

    # Checa negações de bem-estar (ex: "não estou bem", "nada bem", "mal")
    tem_negacao_bem_estar = bool(re.search(r'\b(nao|nada|nem um pouco)\s+(estou|to|me sinto)?\s*bem\b', text_normalizado))
    tem_mal_estar = bool(re.search(r'\b(mal|ruim|pessim[ao]|indispost[ao]|frac[ao]|moleza)\b', text_normalizado))

    for category, patterns in EMOTION_KEYWORDS.items():
        if category == "bem_estar" and (tem_negacao_bem_estar or tem_mal_estar):
            scores[category] = 0.05
            continue

        matches = 0
        for pattern in patterns:
            pat_norm = remover_acentos(pattern.lower())
            if re.search(pat_norm, text_normalizado):
                matches += 1
            elif termo_contido_fuzzy(text_normalizado, [pat_norm], limiar=0.82):
                matches += 1

        if matches > 0:
            prob = min(0.99, 0.55 + (matches * 0.15))
            scores[category] = round(prob, 2)
            active_categories.append(category)
        else:
            scores[category] = 0.05

    # Se a gestante relatou mal-estar expresso e sintoma_fisico não pontuou, garante ativação
    if tem_mal_estar and "sintoma_fisico" not in active_categories:
        scores["sintoma_fisico"] = 0.75
        active_categories.append("sintoma_fisico")

    # CRUCIAL: Se nada pontuou, o estado é neutro/dúvida — NUNCA forçar "bem_estar" automaticamente!
    if not active_categories:
        scores["bem_estar"] = 0.05
        active_categories = ["neutro"]

    return scores, active_categories

