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

import os
import json
from app.config import settings
from app.models.subscription import TransacaoPagamento
from app.services.payment_service import (
    PLANOS_NYMPHIA, obter_ou_criar_assinatura,
    criar_checkout_mercado_pago, processar_webhook_mercado_pago,
    validar_assinatura_mercado_pago,
    verificar_acesso_recurso
)

def is_dev_env() -> bool:
    env = (os.getenv("ENVIRONMENT") or os.getenv("ENV") or settings.ENVIRONMENT or "").lower()
    return env in ["development", "dev", "local"]

@router.post("/pagamentos/webhook", status_code=status.HTTP_200_OK)
async def webhook_mercado_pago(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Webhook do Mercado Pago com validação criptográfica obrigatória de assinatura (HMAC-SHA256)
    e idempotência garantida por identificador de evento para evitar dupla ativação/crédito.
    """
    try:
        body_bytes = await request.body()
        body = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
    except Exception:
        body_bytes = b""
        body = {}

    query_params = dict(request.query_params)
    data_id = (
        body.get("data", {}).get("id")
        or body.get("id")
        or query_params.get("id")
        or query_params.get("data.id")
    )

    # 1. Validação obrigatória da assinatura do webhook (rejeita com 401 se inválida)
    valida = validar_assinatura_mercado_pago(
        headers=dict(request.headers),
        raw_body=body_bytes,
        data_id=str(data_id) if data_id else None
    )
    if not valida:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Assinatura do webhook inválida ou ausente."
        )

    # 2. Idempotência por identificador único de evento
    event_id = str(data_id or body.get("mercado_pago_id") or request.headers.get("x-request-id") or "")
    if event_id:
        transacao_existente = db.query(TransacaoPagamento).filter(
            TransacaoPagamento.mercado_pago_payment_id == event_id
        ).first()
        if transacao_existente:
            return {
                "recebido": True,
                "processado": False,
                "idempotente": True,
                "mensagem": "Evento já processado anteriormente. Nenhuma duplicação realizada."
            }

    sucesso, msg = processar_webhook_mercado_pago(body, query_params, db, event_id=event_id)
    return {"recebido": True, "processado": sucesso, "mensagem": msg, "idempotente": False}


@router.post("/assinatura/simular-webhook")
def simular_webhook_desenvolvimento(
    payload: SimularWebhookRequest,
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """
    Endpoint de teste restrito EXCLUSIVAMENTE a ambientes de desenvolvimento/staging.
    Em produção, retorna 404 (inexistente) para mitigar qualquer risco de fraude financeira.
    """
    if not is_dev_env():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not Found"
        )

    # Restringe a simulação estritamente à conta da gestante autenticada
    uid = gestante.id
    webhook_data = {
        "type": "payment",
        "usuario_id": uid,
        "subscription_id": payload.subscription_id,
        "status": payload.status,
        "data": {"id": f"SIMULATED_TEST_{uid[:8]}"}
    }
    sucesso, msg = processar_webhook_mercado_pago(webhook_data, {}, db)
    return {"status": "simulado", "sucesso": sucesso, "detalhe": msg}
