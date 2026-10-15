from fastapi import APIRouter
from app.services.ai_risk_service import status_modelos_ml
from app.services.ai_text_service import bertimbau_disponivel, bertimbau_diagnostico

router = APIRouter(tags=["Saúde do Sistema"])

@router.get("/health")
def health_check():
    """
    Endpoint de monitoramento, chamado pelo Render a cada poucos segundos.
    Só informa o estado: não carrega modelo nenhum. (Antes, qualquer pessoa
    podia chamar /health?recarregar_ia=true e forçar o download e o
    carregamento do BERTimbau, de 2,3 GB, derrubando o servidor.)
    """
    ml_status = status_modelos_ml()
    bert_ok = bertimbau_disponivel()

    return {
        "status": "online",
        "sistema": "Nymphia Backend",
        "versao": "2.3.0-2027ready",
        "modelos_rf_disponiveis": ml_status["rf_disponiveis"],
        "isolation_forest_disponivel": ml_status["isolation_forest_disponivel"],
        "modelos_carregando": ml_status["carregando"],
        "modelos_desligados_por_memoria": ml_status["desligados_por_memoria"],
        "bertimbau_disponivel": bert_ok,
        "bertimbau_status": bertimbau_diagnostico(),
        "sistema_regras_urgencia": "ativo_deterministico_febrasgo",
        "degradacao_graciosa": True
    }

