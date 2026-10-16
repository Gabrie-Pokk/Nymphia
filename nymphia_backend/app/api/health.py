from fastapi import APIRouter
from app.services.ai_risk_service import status_modelos_ml

router = APIRouter(tags=["Saúde do Sistema"])

@router.get("/health")
def health_check():
    """
    Endpoint de monitoramento, chamado pelo Render a cada poucos segundos.
    Só informa o estado: não carrega modelo nenhum.
    """
    ml_status = status_modelos_ml()

    return {
        "status": "online",
        "sistema": "Nymphia Backend",
        "versao": "2.3.0-2027ready",
        "modelos_rf_disponiveis": ml_status["rf_disponiveis"],
        "isolation_forest_disponivel": ml_status["isolation_forest_disponivel"],
        "modelos_carregando": ml_status["carregando"],
        "modelos_desligados_por_memoria": ml_status["desligados_por_memoria"],
        "classificador_de_texto": "palavras_chave",
        "sistema_regras_urgencia": "ativo_deterministico_febrasgo",
        "degradacao_graciosa": True
    }

