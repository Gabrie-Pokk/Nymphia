"""
Testes de regras clínicas obstétricas, segurança de senha (bcrypt 72 bytes)
e fluxo completo de assinaturas / pagamentos (Mercado Pago).
"""
import uuid
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, date, timedelta
from app.main import app
from app.services.payment_service import CATALOGO_PLANOS, PaymentService
from app.models.subscription import PlanoTipo, StatusAssinatura

client = TestClient(app)

def test_bcrypt_72_bytes_limit_on_registration():
    """Garante que senhas com mais de 72 bytes (ou caracteres multibyte) sejam rejeitadas com 422."""
    # 73 caracteres ASCII
    senha_longa = "A" * 73
    payload = {
        "email": f"test_bcrypt_{uuid.uuid4().hex[:6]}@exemplo.com",
        "nome": "Maria Teste",
        "senha": senha_longa
    }
    resp = client.post("/auth/gestante/cadastro", json=payload)
    assert resp.status_code == 422
    assert "72" in resp.text

    # Teste com caracteres multibyte (UTF-8) que excedem 72 bytes mesmo com menos de 72 caracteres
    # Cada caractere 'ç' tem 2 bytes em UTF-8. 40 caracteres 'ç' = 80 bytes!
    senha_multibyte = "ç" * 40  # 40 chars, 80 bytes
    payload["senha"] = senha_multibyte
    payload["email"] = f"test_multi_{uuid.uuid4().hex[:6]}@exemplo.com"
    resp = client.post("/auth/gestante/cadastro", json=payload)
    assert resp.status_code == 422
    assert "72 bytes" in resp.text


def test_obstetric_cross_validation_rejects_impossible_history():
    """
    A validação cruzada obstétrica deve rejeitar se a soma de
    partos normais + cesáreos + perdas for maior que gestações anteriores.
    Exemplo: 2 gestações e 3 partos = IMPOSSÍVEL.
    """
    # 1. Registrar gestante válida
    email = f"gestante_obstetrica_{uuid.uuid4().hex[:6]}@exemplo.com"
    reg_resp = client.post("/auth/gestante/cadastro", json={
        "email": email,
        "nome": "Carla Obstetrica",
        "senha": "SenhaSegura123!"
    })
    assert reg_resp.status_code == 201, reg_resp.text
    token = reg_resp.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Data da última menstruação (16 semanas atrás) e DPP (24 semanas à frente)
    dum_valida = (date.today() - timedelta(weeks=16)).isoformat()
    dpp_valida = (date.today() + timedelta(weeks=24)).isoformat()

    # Tentativa de cadastro de perfil com histórico impossível:
    # 2 gestações anteriores, 2 partos normais + 1 cesáreo = 3 partos (> 2 gestações)
    perfil_invalido = {
        "idade": 28,
        "dum": dum_valida,
        "dpp": dpp_valida,
        "gestacoes_anteriores": 2,
        "partos_normais": 2,
        "partos_cesareos": 1,
        "perdas_gestacionais": 0,
        "peso_pre_gestacional": 60.0,
        "altura_cm": 165.0,
        "pressao_arterial_sistolica_base": 110,
        "pressao_arterial_diastolica_base": 70,
        "maternidade_referencia_nome": "Hospital Maternidade Central",
        "maternidade_latitude": -23.5505,
        "maternidade_longitude": -46.6333
    }
    resp = client.post("/perfil-clinico", json=perfil_invalido, headers=headers)
    assert resp.status_code == 422
    assert "inconsist" in resp.text.lower() or "não pode ser maior" in resp.text or "menor ou igual" in resp.text

    # Tentativa com perdas também estourando o total:
    # 1 gestação anterior, 1 parto normal + 1 aborto = 2 desfechos (> 1 gestação)
    perfil_invalido_perdas = {
        "idade": 28,
        "dum": dum_valida,
        "dpp": dpp_valida,
        "gestacoes_anteriores": 1,
        "partos_normais": 1,
        "partos_cesareos": 0,
        "perdas_gestacionais": 1,
        "peso_pre_gestacional": 60.0,
        "altura_cm": 165.0
    }
    resp = client.post("/perfil-clinico", json=perfil_invalido_perdas, headers=headers)
    assert resp.status_code == 422
    assert "inconsist" in resp.text.lower() or "não pode ser maior" in resp.text or "menor ou igual" in resp.text

    # Caso válido: 2 gestações anteriores, 1 normal + 1 cesáreo = 2 (válido)
    perfil_valido = {
        "idade": 28,
        "dum": dum_valida,
        "dpp": dpp_valida,
        "gestacoes_anteriores": 2,
        "partos_normais": 1,
        "partos_cesareos": 1,
        "perdas_gestacionais": 0,
        "peso_pre_gestacional": 60.0,
        "altura_cm": 165.0,
        "pressao_arterial_sistolica_base": 110,
        "pressao_arterial_diastolica_base": 70,
        "maternidade_referencia_nome": "Hospital Santa Cruz",
        "maternidade_referencia_endereco": "Rua das Flores, 100",
        "maternidade_referencia_telefone": "(11) 98765-4321",
        "maternidade_latitude": -23.5505,
        "maternidade_longitude": -46.6333
    }
    resp_ok = client.post("/perfil-clinico", json=perfil_valido, headers=headers)
    assert resp_ok.status_code in (200, 201)
    dados = resp_ok.json()
    assert dados["gestacoes_anteriores"] == 2
    assert dados["maternidade_latitude"] == -23.5505


def test_catalogo_planos_assinatura():
    """Verifica se os planos oficiais estão disponíveis para consulta pública."""
    resp = client.get("/assinatura/planos")
    assert resp.status_code == 200
    planos = resp.json()
    assert len(planos) == 4
    
    nomes = [p["id"] for p in planos]
    assert "free" in nomes
    assert "premium" in nomes
    assert "premium_plus" in nomes
    assert "clinica" in nomes

    # Verificar se as features éticas de emergência estão descritas no Free
    free_plan = next(p for p in planos if p["id"] == "free")
    assert any("Emergência" in f for f in free_plan["recursos"])
    assert any("SAMU 192" in f for f in free_plan["recursos"])


def test_fluxo_checkout_e_webhook_mercado_pago():
    """
    Testa o fluxo completo de checkout Pix/Cartão e recebimento
    do webhook do Mercado Pago para ativação imediata.
    """
    # 1. Cria usuário
    email = f"assinante_mp_{uuid.uuid4().hex[:6]}@exemplo.com"
    reg_resp = client.post("/auth/gestante/cadastro", json={
        "email": email,
        "nome": "Juliana Assinante",
        "senha": "SenhaForte123!"
    })
    assert reg_resp.status_code == 201, reg_resp.text
    token = reg_resp.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Consulta assinatura atual (deve ser Free)
    sub_resp = client.get("/assinatura/minha-assinatura", headers=headers)
    assert sub_resp.status_code == 200
    assert sub_resp.json()["plano"] == "free"

    # 3. Cria checkout para Premium via Pix
    checkout_req = {
        "plano": "premium",
        "metodo_pagamento": "pix"
    }
    checkout_resp = client.post("/assinatura/checkout", json=checkout_req, headers=headers)
    assert checkout_resp.status_code == 200
    checkout_data = checkout_resp.json()
    assert "pix_copia_cola" in checkout_data
    assert "pix_qrcode" in checkout_data
    assert "mercado_pago_id" in checkout_data
    payment_id = checkout_data["mercado_pago_id"]

    # 4. Simula o webhook do Mercado Pago com aprovação
    webhook_payload = {
        "action": "payment.updated",
        "subscription_id": payment_id,
        "status": "approved",
        "data": {
            "id": payment_id
        }
    }
    webhook_resp = client.post("/pagamentos/webhook", json=webhook_payload)
    assert webhook_resp.status_code == 200
    assert webhook_resp.json()["recebido"] is True
    assert webhook_resp.json()["processado"] is True

    # 5. Verifica se o plano foi atualizado para Premium ativo
    sub_updated = client.get("/assinatura/minha-assinatura", headers=headers)
    assert sub_updated.status_code == 200
    assert sub_updated.json()["plano"] == "premium"
    assert sub_updated.json()["status"] == "ativa"


def test_emergencia_nunca_bloqueada_mesmo_inadimplente():
    """
    Regra Ética Inviolável: Emergência obstétrica, SAMU 192 e alerta ao parceiro
    NUNCA podem ser bloqueados por falta de pagamento ou assinatura inadimplente.
    """
    # 1. Cria usuário
    email = f"inadimplente_segura_{uuid.uuid4().hex[:6]}@exemplo.com"
    reg_resp = client.post("/auth/gestante/cadastro", json={
        "email": email,
        "nome": "Patricia Protegida",
        "senha": "SenhaForte123!"
    })
    assert reg_resp.status_code == 201, reg_resp.text
    token = reg_resp.json()["token"]
    user_id = reg_resp.json()["id"]
    headers = {"Authorization": f"Bearer {token}"}

    dum_valida = (date.today() - timedelta(weeks=32)).isoformat()
    dpp_valida = (date.today() + timedelta(weeks=8)).isoformat()

    # 2. Configura perfil clínico com contato de emergência
    client.post("/perfil-clinico", json={
        "idade": 30,
        "dum": dum_valida,
        "dpp": dpp_valida,
        "gestacoes_anteriores": 0,
        "partos_normais": 0,
        "partos_cesareos": 0,
        "perdas_gestacionais": 0,
        "peso_pre_gestacional": 65.0,
        "altura_cm": 168.0,
        "pressao_arterial_sistolica_base": 115,
        "pressao_arterial_diastolica_base": 75,
        "nome_contato_emergencia": "Esposo Carlos",
        "telefone_contato_emergencia": "(11) 99999-8888",
        "maternidade_referencia_nome": "Maternidade Pro Matre",
        "maternidade_latitude": -23.565,
        "maternidade_longitude": -46.651
    }, headers=headers)

    # 3. Testa permissão no PaymentService diretamente para 'emergencia_sos' com status inadimplente
    from app.database import SessionLocal
    from app.models.subscription import Assinatura
    from datetime import datetime
    
    db = SessionLocal()
    try:
        # Inserir ou forçar assinatura inadimplente
        sub = db.query(Assinatura).filter(Assinatura.usuario_id == user_id).first()
        if not sub:
            sub = Assinatura(
                usuario_id=user_id,
                plano=PlanoTipo.PREMIUM,
                status=StatusAssinatura.INADIMPLENTE,
                inadimplente_desde=datetime.utcnow()
            )
            db.add(sub)
        else:
            sub.status = StatusAssinatura.INADIMPLENTE
            sub.inadimplente_desde = datetime.utcnow()
        db.commit()

        # Verifica liberação incondicional de emergência e sinais de alerta
        permitido_emergencia = PaymentService.verificar_acesso_recurso(db, user_id, "emergencia_sos")
        assert permitido_emergencia is True, "Emergência SOS JAMAIS pode ser bloqueada!"

        permitido_sinais = PaymentService.verificar_acesso_recurso(db, user_id, "sinais_alerta")
        assert permitido_sinais is True, "Sinais de Alerta JAMAIS podem ser bloqueados!"
    finally:
        db.close()

    # 4. Acionar endpoint de emergência
    resp_emergencia = client.post("/emergencia/notificar", json={
        "mensagem_personalizada": "Dor de cabeça súbita intensa com escotomas",
        "latitude": -23.565,
        "longitude": -46.651
    }, headers=headers)
    assert resp_emergencia.status_code == 200
    assert "emergencia" in resp_emergencia.json()["status"] or "alerta" in resp_emergencia.json()["status"]
