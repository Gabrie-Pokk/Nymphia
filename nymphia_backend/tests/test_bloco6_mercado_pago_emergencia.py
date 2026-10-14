import os
import hmac
import hashlib
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.database import get_db
from app.models.auth import Gestante
from app.models.subscription import Assinatura, TransacaoPagamento
from app.services.payment_service import verificar_acesso_recurso, PaymentService
from app.security.jwt_auth import create_access_token

SECRET_TEST = "nymphia_super_secret_production_ready_key_change_me_in_prod_12345"

def gerar_assinatura_valida(raw_body: bytes) -> str:
    h = hmac.new(SECRET_TEST.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return f"sha256={h}"

@pytest.fixture
def gestante_teste(db_session: Session):
    g = db_session.query(Gestante).filter(Gestante.email == "gestante_pagamento_teste@nymphia.app").first()
    if not g:
        g = Gestante(
            nome="Gestante Teste Pagamento",
            email="gestante_pagamento_teste@nymphia.app",
            senha_hash="hash_teste_seguro"
        )
        db_session.add(g)
        db_session.commit()
        db_session.refresh(g)
    return g

def test_checkout_mercado_pago_sandbox(client, gestante_teste, db_session: Session):
    token = create_access_token(data={"sub": gestante_teste.id, "perfil": "gestante"})
    headers = {"Authorization": f"Bearer {token}"}
    
    resp = client.post(
        "/assinatura/checkout",
        json={"plano": "premium", "forma_pagamento": "pix"},
        headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "pendente"
    assert data["plano"] == "premium"
    assert data["valor"] == 29.90
    assert "checkout_url" in data
    assert "pix_copia_cola" in data
    assert "sandbox.mercadopago.com.br" in data["checkout_url"]

def test_webhook_assinatura_invalida_rejeitada_401(client):
    body = json.dumps({"type": "payment", "id": "TEST_INVALID_SIG"}).encode("utf-8")
    resp = client.post(
        "/pagamentos/webhook",
        content=body,
        headers={"Content-Type": "application/json", "x-signature": "sha256=invalid_signature_hash_123"}
    )
    assert resp.status_code == 401
    assert "Assinatura do webhook inválida" in resp.json()["detail"]

def test_webhook_idempotencia_nao_duplica_credito(client, gestante_teste, db_session: Session):
    from app.services.payment_service import obter_ou_criar_assinatura
    sub = obter_ou_criar_assinatura(gestante_teste.id, db_session)
    sub.plano = "premium"
    db_session.commit()

    event_id = "EVT_TEST_IDEMPOTENCIA_12345"
    body_dict = {
        "type": "payment",
        "status": "approved",
        "usuario_id": gestante_teste.id,
        "data": {"id": event_id}
    }
    body_bytes = json.dumps(body_dict).encode("utf-8")
    sig = gerar_assinatura_valida(body_bytes)
    
    # 1ª chamada: deve processar e aprovar
    resp1 = client.post(
        "/pagamentos/webhook",
        content=body_bytes,
        headers={"Content-Type": "application/json", "x-signature": sig}
    )
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["recebido"] is True
    assert data1["processado"] is True
    assert data1["idempotente"] is False
    
    # 2ª chamada: replay idêntico do mesmo evento
    resp2 = client.post(
        "/pagamentos/webhook",
        content=body_bytes,
        headers={"Content-Type": "application/json", "x-signature": sig}
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["recebido"] is True
    assert data2["processado"] is False
    assert data2["idempotente"] is True
    assert "Evento já processado anteriormente" in data2["mensagem"]
    
    # Verifica que não duplicou registro de transação
    transacoes = db_session.query(TransacaoPagamento).filter(
        TransacaoPagamento.mercado_pago_payment_id == event_id
    ).all()
    assert len(transacoes) == 1

def test_webhook_falha_cobranca_marca_inadimplente(client, gestante_teste, db_session: Session):
    from app.services.payment_service import obter_ou_criar_assinatura
    sub = obter_ou_criar_assinatura(gestante_teste.id, db_session)
    sub.status = "ativa"
    db_session.commit()

    event_id = "EVT_TEST_FALHA_COBRANCA_999"
    body_dict = {
        "type": "payment",
        "status": "rejected",
        "usuario_id": gestante_teste.id,
        "data": {"id": event_id}
    }
    body_bytes = json.dumps(body_dict).encode("utf-8")
    sig = gerar_assinatura_valida(body_bytes)
    
    resp = client.post(
        "/pagamentos/webhook",
        content=body_bytes,
        headers={"Content-Type": "application/json", "x-signature": sig}
    )
    assert resp.status_code == 200
    
    # Verifica que a assinatura da gestante foi marcada como inadimplente
    sub_atualizada = db_session.query(Assinatura).filter(Assinatura.usuario_id == gestante_teste.id).first()
    assert sub_atualizada is not None
    assert sub_atualizada.status == "inadimplente"

def test_inadimplencia_nunca_bloqueia_emergencia_notificar(client, gestante_teste, db_session: Session):
    """
    REGRA INVIOLÁVEL 3:
    Mesmo com a assinatura marcada como 'inadimplente', a rota de emergência
    /emergencia/notificar continua respondendo HTTP 200 sem nenhum bloqueio.
    """
    from app.services.payment_service import obter_ou_criar_assinatura
    sub = obter_ou_criar_assinatura(gestante_teste.id, db_session)
    sub.status = "inadimplente"
    db_session.commit()
    
    token = create_access_token(data={"sub": gestante_teste.id, "perfil": "gestante"})
    headers = {"Authorization": f"Bearer {token}"}
    
    resp = client.post(
        "/emergencia/notificar",
        json={"latitude": -23.5505, "longitude": -46.6333},
        headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ["emergencia_registrada_em_paralelo", "emergencia_publica_acionada"]
    assert "SAMU" in data["orientacao_samu"]

def test_emergencia_anonima_publica_nunca_bloqueia(client):
    """
    Rota de emergência sem autenticação (pública de propósito, Seção 31.3).
    """
    resp = client.post(
        "/emergencia/notificar",
        json={"latitude": -23.5505, "longitude": -46.6333}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "emergencia_publica_acionada"
    assert "192" in data["orientacao_samu"]

def test_verificar_acesso_recursos_emergencia_imunes_a_cobranca():
    """
    Testa que a matriz de autorização PaymentService.verificar_acesso_recurso
    libera emergência irrestritamente, mas bloqueia recursos premium na inadimplência.
    """
    recursos_emergencia = ["emergencia", "emergencia_sos", "samu_192", "sinais_alerta", "alerta_parceiro_emergencia"]
    
    # Para planos inadimplentes ou cancelados:
    for rec in recursos_emergencia:
        assert verificar_acesso_recurso("premium", "inadimplente", rec) is True
        assert verificar_acesso_recurso("premium_plus", "cancelada", rec) is True
        assert verificar_acesso_recurso("free", "ativa", rec) is True
        
    # Recursos avançados pagos devem ser bloqueados quando inadimplente
    assert verificar_acesso_recurso("premium", "inadimplente", "ai_chat") is False
    assert verificar_acesso_recurso("premium_plus", "inadimplente", "modo_parceiro_completo") is False
    # Mas liberados quando ativa
    assert verificar_acesso_recurso("premium", "ativa", "ai_chat") is True
