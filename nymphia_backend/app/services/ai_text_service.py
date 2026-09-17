import os
import re
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

EMOTION_KEYWORDS = {
    "ansiedade": [r"ansios", r"angusti", r"nervos", r"preocupad", r"inquiet", r"afli", r"coração acelerado"],
    "tristeza_desanimo": [r"trist", r"chor", r"desanim", r"deprim", r"abatid", r"desolad", r"sem vontade", r"sem energia"],
    "estresse_sobrecarga": [r"estress", r"cansad", r"esgotad", r"sobrecarreg", r"irritad", r"não aguento mais", r"pressão demais"],
    "medo_inseguranca": [r"medo", r"pavor", r"assustad", r"insegur", r"temor", r"com receio"],
    "bem_estar": [r"bem", r"otim", r"feliz", r"alegr", r"tranquil", r"animad", r"calm", r"paz", r"tudo certo", r"grata"],
    "sintoma_fisico": [r"dor", r"sangrament", r"nause", r"enjoo", r"tontur", r"incha", r"colic", r"queima", r"azia", r"falta de ar", r"visão", r"mexer"]
}


def carregar_bertimbau():
    """Tenta carregar o modelo BERTimbau ajustado localmente."""
    if _bert_estado["tentado"]:
        return

    _bert_estado["tentado"] = True

    if not BERTIMBAU_DIR.exists():
        logger.info(f"Pasta do BERTimbau não encontrada em {BERTIMBAU_DIR}. Operando com motor de regras regex.")
        return

    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        import torch
        logger.info(f"Carregando BERTimbau a partir de: {BERTIMBAU_DIR}")
        _bert_estado["tokenizer"] = AutoTokenizer.from_pretrained(str(BERTIMBAU_DIR))
        _bert_estado["modelo"] = AutoModelForSequenceClassification.from_pretrained(str(BERTIMBAU_DIR))
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
    Classificador de conteúdo emocional e sintomas do check-in diário.
    Utiliza BERTimbau treinado se disponível; caso contrário, utiliza
    motor regex determinístico com rotulagem FEBRASGO.
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
                active = ["bem_estar" if scores.get("bem_estar", 0) > 0.2 else "neutro"]
            return scores, active
        except Exception as e:
            logger.warning(f"Falha na inferência do BERTimbau ({e}), usando motor de regras.")

    # 2. Fallback determinístico baseado em padrões de palavras-chave
    text_lower = text.lower()
    scores: Dict[str, float] = {}
    active_categories: List[str] = []

    for category, patterns in EMOTION_KEYWORDS.items():
        matches = 0
        for pattern in patterns:
            if re.search(pattern, text_lower):
                matches += 1

        if matches > 0:
            prob = min(0.99, 0.55 + (matches * 0.15))
            scores[category] = round(prob, 2)
            active_categories.append(category)
        else:
            scores[category] = 0.05

    if not active_categories or (len(active_categories) == 1 and "bem_estar" in active_categories):
        scores["bem_estar"] = 0.80
        if "bem_estar" not in active_categories:
            active_categories.append("bem_estar")

    return scores, active_categories
