import os
import pytest
from fastapi import Request
from app.models.interaction import EventoEmergencia
from app.models.auth import Gestante, Profissional
from app.security.jwt_auth import hash_password, verify_password

def test_emergencia_notificar_anonima_sem_login_responde_200_e_persiste_gestante_id_null(client, db_session):
    """
    Garante que chamadas deslogadas na rota de emergência:
    1. Retornam HTTP 200 (nunca 500 por foreign key violation).
    2. Persistem evento com gestante_id=None e profissional_notificado=False.
    """
    res = client.post("/emergencia/notificar", json={
        "latitude": -23.5505,
        "longitude": -46.6333
    })
    assert res.status_code == 200
    data = res.json()
    assert data["profissional_notificado"] is False
    assert "192" in data["orientacao_samu"]

    # Verifica persistência no banco com gestante_id nulo
    evento = db_session.query(EventoEmergencia).filter_by(id=data["evento_id"]).first()
    assert evento is not None
    assert evento.gestante_id is None
    assert evento.profissional_notificado is False

def test_emergencia_notificar_gestante_autenticada(client, db_session):
    """
    Garante que gestante logada consegue acionar a rota normalmente.
    """
    res_cad = client.post("/auth/gestante/cadastro", json={
        "nome": "Carla Oliveira",
        "email": "carla.emerg@teste.com",
        "senha": "SenhaForteSegura123!"
    })
    assert res_cad.status_code == 201
    token = res_cad.json()["token"]

    res_emerg = client.post(
        "/emergencia/notificar",
        headers={"Authorization": f"Bearer {token}"},
        json={"latitude": -23.55, "longitude": -46.63}
    )
    assert res_emerg.status_code == 200
    data = res_emerg.json()
    assert data["status"] == "emergencia_registrada_em_paralelo"

def test_global_exception_handler_sanitiza_em_producao_sem_vazar_sql(client, monkeypatch):
    """
    Garante que em produção erros 500 não vazam queries SQL, nomes de colunas ou tracebacks.
    """
    monkeypatch.setenv("ENVIRONMENT", "production")

    # Dispara uma rota de teste que force um erro ou simula chamada com handler
    from app.main import app, global_exception_handler
    import asyncio

    class DummyRequest:
        url = type("URL", (), {"path": "/rota-critica-teste"})()

    dummy_exc = Exception("SELECT * FROM gestantes WHERE id = 'teste_leak' syntax error near table")
    resp = asyncio.run(global_exception_handler(DummyRequest(), dummy_exc))

    assert resp.status_code == 500
    import json
    corpo = json.loads(resp.body.decode("utf-8"))
    assert corpo["erro"] == "Falha interna no processamento"
    assert "SELECT" not in corpo["detalhe"]
    assert "syntax error" not in corpo["detalhe"]
    assert "instabilidade interna momentânea" in corpo["detalhe"]

def test_recuperacao_senha_completa_gestante(client, db_session):
    """
    Testa o ciclo completo de recuperação de senha:
    1. Cadastro de usuário com senha A.
    2. Solicitação de /auth/esqueci-senha -> gera token.
    3. Envio de /auth/redefinir-senha com nova senha B.
    4. Login com senha A falha (401).
    5. Login com senha B tem sucesso (200).
    """
    email = "recupera.gestante@teste.com"
    client.post("/auth/gestante/cadastro", json={
        "nome": "Bruna Teste",
        "email": email,
        "senha": "SenhaOriginal123!"
    })

    # 1. Esqueci senha
    res_esq = client.post("/auth/esqueci-senha", json={"email": email, "perfil": "gestante"})
    assert res_esq.status_code == 200
    dados_esq = res_esq.json()
    assert dados_esq["sucesso"] is True
    token_reset = dados_esq["reset_token"]
    assert token_reset is not None

    # 2. Redefinir com senha curta deve ser rejeitado
    res_curta = client.post("/auth/redefinir-senha", json={
        "token": token_reset,
        "nova_senha": "curta"
    })
    assert res_curta.status_code == 422

    # 3. Redefinir com senha forte
    res_redef = client.post("/auth/redefinir-senha", json={
        "token": token_reset,
        "nova_senha": "NovaSenhaSegura456!"
    })
    assert res_redef.status_code == 200
    assert res_redef.json()["sucesso"] is True

    # 4. Senha antiga não deve mais autenticar
    res_login_antigo = client.post("/auth/gestante/login", json={
        "email": email,
        "senha": "SenhaOriginal123!"
    })
    assert res_login_antigo.status_code == 401

    # 5. Nova senha autentica normalmente
    res_login_novo = client.post("/auth/gestante/login", json={
        "email": email,
        "senha": "NovaSenhaSegura456!"
    })
    assert res_login_novo.status_code == 200
    assert "token" in res_login_novo.json()

def test_rotacao_automatica_invalida_senha_vazada(db_session):
    """
    Garante que a rotina rotacionar_credenciais_vazadas_automaticamente()
    detecta qualquer usuário com 'senhaMaternidade123' e o protege com hash aleatório.
    """
    from app.database import rotacionar_credenciais_vazadas_automaticamente

    # Cria usuário com a senha vazada
    usuario = Gestante(
        nome="Alvo Vazamento",
        email="vazamento.alvo@teste.com",
        senha_hash=hash_password("senhaMaternidade123")
    )
    db_session.add(usuario)
    db_session.commit()

    # Confirma que a senha antiga conferia
    assert verify_password("senhaMaternidade123", usuario.senha_hash) is True

    # Roda a função de auto-rotação de credenciais comprometidas
    rotacionar_credenciais_vazadas_automaticamente(db_session=db_session)

    # Atualiza sessão
    db_session.refresh(usuario)

    # A senha antiga agora DEVE ser rejeitada
    assert verify_password("senhaMaternidade123", usuario.senha_hash) is False
