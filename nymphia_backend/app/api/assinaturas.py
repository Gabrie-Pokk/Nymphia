from typing import List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth import Gestante
from app.schemas.all_schemas import (
    PlanoInfo, AssinaturaOut, CheckoutAssinaturaRequest,
    CheckoutAssinaturaResponse, SimularWebhookRequest
)
from app.security.jwt_auth import get_current_gestante
from app.services.payment_service import (
    PLANOS_NYMPHIA, obter_ou_criar_assinatura,
    criar_checkout_mercado_pago, processar_webhook_mercado_pago,
    verificar_acesso_recurso
)

router = APIRouter(tags=["Planos e Assinaturas (Mercado Pago)"])

@router.get("/assinatura/planos", response_model=List[PlanoInfo])
def listar_planos():
    """Retorna os planos oficiais da Nymphia com preços e recursos."""
    return [PlanoInfo(**p) for p in PLANOS_NYMPHIA.values()]

@router.get("/assinatura/minha-assinatura", response_model=AssinaturaOut)
def obter_minha_assinatura(
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """Consulta os dados da assinatura atual da gestante e seus recursos disponíveis."""
    sub = obter_ou_criar_assinatura(gestante.id, db)
    plano_info = PLANOS_NYMPHIA.get(sub.plano, PLANOS_NYMPHIA["free"])

    return AssinaturaOut(
        plano=sub.plano,
        status=sub.status,
        valor_mensal=sub.valor_mensal,
        forma_pagamento=sub.forma_pagamento,
        iniciada_em=sub.iniciada_em,
        expira_em=sub.expira_em,
        proxima_cobranca=sub.proxima_cobranca,
        recursos_liberados=plano_info["recursos"]
    )

@router.post("/assinatura/checkout", response_model=CheckoutAssinaturaResponse)
def iniciar_checkout_assinatura(
    payload: CheckoutAssinaturaRequest,
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """Gera uma sessão de pagamento ou cobrança recorrente no Mercado Pago."""
    try:
        dados_checkout = criar_checkout_mercado_pago(
            gestante=gestante,
            plano_id=payload.plano,
            metodo=payload.forma_pagamento,
            db=db
        )
        return CheckoutAssinaturaResponse(**dados_checkout)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/assinatura/cancelar")
def cancelar_assinatura(
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """Cancela a renovação automática da assinatura, mantendo o acesso até o fim do ciclo."""
    sub = obter_ou_criar_assinatura(gestante.id, db)
    sub.status = "cancelada"
    sub.cancelada_em = datetime.utcnow()
    db.commit()
    return {"status": "cancelada", "mensagem": "Renovação automática cancelada. Seu acesso aos recursos essenciais de emergência permanece sempre ativo."}

@router.post("/pagamentos/webhook", status_code=status.HTTP_200_OK)
async def webhook_mercado_pago(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Webhook do Mercado Pago de alta resiliência.
    Recebe notificações de pagamento e atualiza status de forma assíncrona.
    Sempre retorna 200 OK para evitar reenvios desnecessários pelo Mercado Pago.
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    query_params = dict(request.query_params)
    sucesso, msg = processar_webhook_mercado_pago(body, query_params, db)
    return {"recebido": True, "processado": sucesso, "mensagem": msg}

@router.post("/assinatura/simular-webhook")
def simular_webhook_desenvolvimento(
    payload: SimularWebhookRequest,
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """Endpoint de teste para simular aprovação ou recusa de pagamento em ambiente de testes."""
    uid = payload.usuario_id or gestante.id
    webhook_data = {
        "type": "payment",
        "usuario_id": uid,
        "subscription_id": payload.subscription_id,
        "status": payload.status,
        "data": {"id": "SIMULATED_TEST_PAYMENT_123"}
    }
    sucesso, msg = processar_webhook_mercado_pago(webhook_data, {}, db)
    return {"status": "simulado", "sucesso": sucesso, "detalhe": msg}
