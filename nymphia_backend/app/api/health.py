from fastapi import APIRouter
from app.services.ai_risk_service import status_modelos_ml
from app.services.ai_text_service import bertimbau_disponivel

router = APIRouter(tags=["Saúde do Sistema"])

@router.get("/health")
def health_check():
    """
    Endpoint de monitoramento de saúde e degradação graciosa.
    Informa a disponibilidade exata dos modelos supervisionados de IA
    e do motor de regras clínicas.
    """
    ml_status = status_modelos_ml()
    bert_ok = bertimbau_disponivel()

    return {
        "status": "online",
        "sistema": "Nymphia Backend",
        "versao": "2.1.0-2027ready",
        "modelos_rf_disponiveis": ml_status["rf_disponiveis"],
        "isolation_forest_disponivel": ml_status["isolation_forest_disponivel"],
        "bertimbau_disponivel": bert_ok,
        "sistema_regras_urgencia": "ativo_deterministico_febrasgo",
        "degradacao_graciosa": True
    }
