"""
Nymphia Backend -- Carregamento de modelos

Carrega os modelos treinados (Random Forest x6, Isolation Forest,
BERTimbau) a partir de arquivos locais. Se um arquivo não existir, o
serviço não trava -- registra como indisponível e o endpoint
correspondente avisa isso na resposta, em vez de dar erro 500 sem
explicação.

CAMINHOS ESPERADOS (ajuste MODELOS_DIR se necessário):
  modelos/rf_bem_estar_fetal.joblib
  modelos/rf_malformacao.joblib
  modelos/rf_pre_eclampsia.joblib
  modelos/rf_eclampsia.joblib
  modelos/rf_diabetes_gestacional.joblib
  modelos/rf_itu.joblib
  modelos/isolation_forest_anomalia.joblib
  modelos/bertimbau_nymphia/          <- pasta salva por trainer.save_model()
"""
import os
import logging
from pathlib import Path

logger = logging.getLogger("nymphia.modelos")

# Resolve relativo à localização deste arquivo (app/modelos.py), não ao
# diretório de onde o comando foi executado -- evita o bug de "lista vazia
# sem erro" quando o servidor sobe de um lugar diferente do esperado.
_RAIZ_BACKEND = Path(__file__).resolve().parent.parent
MODELOS_DIR = os.environ.get("NYMPHIA_MODELOS_DIR", str(_RAIZ_BACKEND / "modelos"))

NOMES_RF = [
    "bem_estar_fetal", "malformacao",
    "pre_eclampsia", "eclampsia", "diabetes_gestacional", "itu",
]

_estado = {
    "rf": {},          # nome -> {"modelo":..., "features":[...]}
    "isolation_forest": None,
    "bertimbau_tokenizer": None,
    "bertimbau_modelo": None,
    "bertimbau_categorias": ["ansiedade", "tristeza_desanimo", "estresse_sobrecarga",
                              "medo_inseguranca", "bem_estar", "sintoma_fisico"],
}


def carregar_todos():
    """Roda uma vez, na subida do servidor. Cada modelo falha
    isoladamente -- um .joblib ausente não impede os outros de carregar."""
    import joblib

    logger.info(f"Procurando modelos em: {MODELOS_DIR}")
    if os.path.isdir(MODELOS_DIR):
        logger.info(f"Conteúdo encontrado: {os.listdir(MODELOS_DIR)}")
    else:
        logger.warning(f"A pasta {MODELOS_DIR} NÃO existe -- confira se os arquivos foram colocados no lugar certo")

    for nome in NOMES_RF:
        caminho = os.path.join(MODELOS_DIR, f"rf_{nome}.joblib")
        try:
            raw = joblib.load(caminho)
            if isinstance(raw, dict):
                _estado["rf"][nome] = raw
            else:
                _estado["rf"][nome] = {"modelo": raw, "features": list(raw.feature_names_in_)}
            logger.info(f"Modelo RF '{nome}' carregado de {caminho}")
        except FileNotFoundError:
            logger.warning(f"Modelo RF '{nome}' NÃO encontrado em {caminho} -- endpoint vai reportar indisponível")
        except Exception as e:
            logger.warning(f"Modelo RF '{nome}' falhou ao carregar: {e}")

    caminho_iso = os.path.join(MODELOS_DIR, "isolation_forest_anomalia.joblib")
    try:
        raw = joblib.load(caminho_iso)
        if isinstance(raw, dict):
            _estado["isolation_forest"] = raw
        else:
            # IsolationForest não persiste feature_names_in_ -- usa as mesmas 13
            # features do onboarding que o modelo recebeu no treino
            features_iso = list(_estado["rf"]["bem_estar_fetal"]["features"]) if "bem_estar_fetal" in _estado["rf"] else []
            _estado["isolation_forest"] = {"modelo": raw, "features": features_iso}
        logger.info(f"Isolation Forest carregado de {caminho_iso}")
    except FileNotFoundError:
        logger.warning(f"Isolation Forest NÃO encontrado em {caminho_iso}")
    except Exception as e:
        logger.warning(f"Isolation Forest falhou ao carregar: {e}")

    caminho_bert = os.path.join(MODELOS_DIR, "bertimbau_nymphia", "modelo_final")
    if os.path.isdir(caminho_bert):
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            _estado["bertimbau_tokenizer"] = AutoTokenizer.from_pretrained(caminho_bert)
            _estado["bertimbau_modelo"] = AutoModelForSequenceClassification.from_pretrained(caminho_bert)
            _estado["bertimbau_modelo"].eval()
            logger.info(f"BERTimbau carregado de {caminho_bert}")
        except Exception as e:
            logger.warning(f"BERTimbau NÃO carregado ({caminho_bert} existe mas falhou: {e}) -- check-in usa só regras")
    else:
        logger.warning(f"Pasta do BERTimbau não encontrada em {caminho_bert} -- check-in usa só regras")


def modelos_rf_disponiveis():
    return list(_estado["rf"].keys())


def prever_rf(nome_modelo, valores_features):
    """valores_features: dict {nome_da_feature: valor}. Retorna
    probabilidade da classe positiva, ou None se o modelo não estiver
    carregado ou faltar alguma feature obrigatória."""
    entrada = _estado["rf"].get(nome_modelo)
    if entrada is None:
        return None
    modelo, features_esperadas = entrada["modelo"], entrada["features"]
    try:
        vetor = [[valores_features[f] for f in features_esperadas]]
    except KeyError as e:
        logger.warning(f"Feature ausente pra rf_{nome_modelo}: {e}")
        return None
    return float(modelo.predict_proba(vetor)[0][1])


def prever_anomalia(valores_features):
    entrada = _estado["isolation_forest"]
    if entrada is None:
        return None
    modelo, features_esperadas = entrada["modelo"], entrada["features"]
    try:
        vetor = [[valores_features[f] for f in features_esperadas]]
    except KeyError as e:
        logger.warning(f"Feature ausente pro isolation forest: {e}")
        return None
    score = float(modelo.decision_function(vetor)[0])
    anomalo = bool(modelo.predict(vetor)[0] == -1)
    return {"score": score, "anomalo": anomalo}


def bertimbau_disponivel():
    return _estado["bertimbau_modelo"] is not None


def prever_bertimbau(texto):
    """Retorna dict {categoria: probabilidade} ou None se indisponível."""
    if not bertimbau_disponivel():
        return None
    import torch
    tok = _estado["bertimbau_tokenizer"]
    modelo = _estado["bertimbau_modelo"]
    entrada = tok(texto, return_tensors="pt", truncation=True, max_length=96)
    with torch.no_grad():
        saida = modelo(**entrada)
    probs = torch.sigmoid(saida.logits)[0].tolist()
    return dict(zip(_estado["bertimbau_categorias"], probs))
