import os
import hmac
import hashlib
import json
import pytest
from app.config import settings
from app.security.rate_limiter import auth_rate_limiter

def test_1_1_openapi_e_docs_desativados_em_producao(monkeypatch, client):
    """
    1.1 Aceite: requisição a /openapi.json em produção retorna 404.
    A app só expõe /docs, /redoc e /openapi.json quando o ambiente indicar desenvolvimento.
    """
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("ENV", "production")
    
    # Requisições a endpoints de documentação retornam 404 em produção
    res_openapi = client.get("/openapi.json")
    assert res_openapi.status_code == 404

    res_docs = client.get("/docs")
    assert res_docs.status_code == 404

    res_redoc = client.get("/redoc")
    assert res_redoc.status_code == 404


def test_1_2_cabecalhos_seguranca_especificados(client):
    """
    1.2 Valida os cabeçalhos de segurança obrigatórios conforme auditoria:
    - Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
    - X-Content-Type-Options: nosniff
    - Referrer-Policy: strict-origin-when-cross-origin
    - Permissions-Policy: geolocation=(self), camera=(), microphone=()
    - Content-Security-Policy-Report-Only com diretrizes solicitadas
    - Ausência de x-render-origin-server
    """
    res = client.get("/health")
    assert res.status_code == 200

    assert res.headers.get("Strict-Transport-Security") == "max-age=63072000; includeSubDomains; preload"
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert res.headers.get("Permissions-Policy") == "geolocation=(self), camera=(), microphone=()"

    csp_ro = res.headers.get("Content-Security-Policy-Report-Only", "")
    assert "default-src 'self'" in csp_ro
    assert "frame-ancestors 'none'" in csp_ro
    assert "base-uri 'self'" in csp_ro
    assert "object-src 'none'" in csp_ro
    assert "img-src 'self' data: blob:" in csp_ro

    assert "x-render-origin-server" not in res.headers
    assert "server" not in res.headers


def test_1_3_simular_webhook_retorna_404_em_producao(monkeypatch, client):
    """
    1.3 Aceite: POST /assinatura/simular-webhook retorna 404 em produção.
    """
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("ENV", "production")

    # Autentica gestante para ter credencial válida
    reg = client.post("/auth/gestante/cadastro", json={
        "nome": "Gestante Producao Simular",
        "email": "gestante.prod.simular@teste.com",
        "senha": "senhaValida123"
    })
    token = reg.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "subscription_id": "SUB-TEST-PROD",
        "status": "approved"
    }

    res = client.post("/assinatura/simular-webhook", json=payload, headers=headers)
    assert res.status_code == 404


def test_1_4_webhook_mercado_pago_valida_assinatura_e_idempotencia(client, monkeypatch):
    """
    1.4 Aceite: webhook com assinatura inválida é rejeitado com 401, e evento
    repetido não credita assinatura duas vezes.
    """
    secret = "chave_secreta_webhook_teste_123"
    monkeypatch.setenv("MP_WEBHOOK_SECRET", secret)

    # Cadastra gestante e inicia checkout para haver assinatura correspondente
    reg = client.post("/auth/gestante/cadastro", json={
        "nome": "Gestante Webhook Pagamento",
        "email": "gestante.webhook.pag@teste.com",
        "senha": "senhaValida123"
    })
    user_id = reg.json()["id"]
    token = reg.json()["token"]
    client.post(
        "/assinatura/checkout",
        json={"plano": "premium", "forma_pagamento": "pix"},
        headers={"Authorization": f"Bearer {token}"}
    )

    # 1. Requisição sem assinatura -> 401
    payload = {
        "type": "payment",
        "usuario_id": user_id,
        "data": {"id": "EVT-PAY-1001", "status": "approved"}
    }
    res_sem_sig = client.post("/pagamentos/webhook", json=payload)
    assert res_sem_sig.status_code == 401

    # 2. Requisição com assinatura inválida -> 401
    res_sig_invalida = client.post(
        "/pagamentos/webhook",
        json=payload,
        headers={"x-signature": "ts=1700000000,v1=invalido123"}
    )
    assert res_sig_invalida.status_code == 401

    # 3. Requisição com assinatura válida (HMAC do corpo)
    raw_bytes = json.dumps(payload).encode("utf-8")
    sig_valida = hmac.new(secret.encode("utf-8"), raw_bytes, hashlib.sha256).hexdigest()

    res_sucesso = client.post(
        "/pagamentos/webhook",
        content=raw_bytes,
        headers={
            "content-type": "application/json",
            "x-signature": f"v1={sig_valida}"
        }
    )
    assert res_sucesso.status_code == 200
    dados = res_sucesso.json()
    assert dados["recebido"] is True
    assert dados["processado"] is True

    # 4. Envio repetido com o mesmo identificador de evento (Idempotência estrita)
    res_repetido = client.post(
        "/pagamentos/webhook",
        content=raw_bytes,
        headers={
            "content-type": "application/json",
            "x-signature": f"v1={sig_valida}"
        }
    )
    assert res_repetido.status_code == 200
    dados_rep = res_repetido.json()
    assert dados_rep["recebido"] is True
    assert dados_rep["idempotente"] is True
    assert dados_rep["processado"] is False


def test_1_5_limitacao_de_taxa_auth_bloqueia_apos_n_tentativas(client):
    """
    1.5 Aceite: teste que comprova bloqueio após N tentativas na mesma origem.
    Endpoints /auth/*/login e /auth/*/cadastro devem retornar 429 após atingir o limite.
    """
    auth_rate_limiter.reset()

    # O limitador padrão é 10 requisições por janela
    ip_origem = "192.168.10.50"
    headers = {"X-Forwarded-For": ip_origem}

    status_codes = []
    for i in range(12):
        res = client.post(
            "/auth/gestante/login",
            json={"email": f"tentativa_{i}@teste.com", "senha": "senhaErrada123"},
            headers=headers
        )
        status_codes.append(res.status_code)

    # As primeiras 10 tentativas são processadas pelo bcrypt (401 por credencial inválida)
    for i in range(10):
        assert status_codes[i] == 401

    # Tentativas após o limite de 10 devem ser bloqueadas com HTTP 429
    assert status_codes[10] == 429
    assert status_codes[11] == 429

    auth_rate_limiter.reset()
