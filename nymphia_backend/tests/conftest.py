import threading

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

# Banco SQLite em memória isolado para testes
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(autouse=True)
def reset_rate_limiter():
    from app.security.rate_limiter import auth_rate_limiter, admin_rate_limiter
    auth_rate_limiter.reset()
    admin_rate_limiter.reset()
    yield
    auth_rate_limiter.reset()
    admin_rate_limiter.reset()

@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    # Ao ligar, o servidor carrega os modelos numa linha de execução separada.
    # Espera terminar, para ela não mexer no estado dos modelos do teste seguinte.
    for linha in threading.enumerate():
        if linha.name == "ml-warmup":
            linha.join(timeout=120)


# --- Fixtures adicionadas em 15/10/2026 ---

TOKEN_ADMIN_TESTE = "token-admin-de-teste-com-mais-de-32-caracteres"


@pytest.fixture(autouse=True)
def cremesp_sem_rede(monkeypatch):
    """
    Nenhum teste fala com o CREMESP de verdade. Por padrão a consulta "não
    responde" (o caso mais comum na vida real). Um teste que precise simular
    registro ativo ou inativo troca a função de novo com monkeypatch.
    """
    from app.services import crm_service
    crm_service._CACHE_CREMESP.clear()
    monkeypatch.setattr(crm_service, "_consultar_cremesp", lambda crm_limpo: None)
    yield
    crm_service._CACHE_CREMESP.clear()


@pytest.fixture
def emails_enviados(monkeypatch):
    """Captura os e-mails em vez de enviar. Cada item: (destinatario, assunto, corpo)."""
    caixa = []

    def _falso_envio(destinatario, assunto, corpo_texto):
        caixa.append((destinatario, assunto, corpo_texto))
        return True

    import app.api.auth as rotas_auth
    import app.api.admin as rotas_admin
    monkeypatch.setattr(rotas_auth, "enviar_email", _falso_envio)
    monkeypatch.setattr(rotas_admin, "enviar_email", _falso_envio)
    return caixa


@pytest.fixture
def admin_headers(monkeypatch):
    monkeypatch.setenv("NYMPHIA_ADMIN_TOKEN", TOKEN_ADMIN_TESTE)
    return {"X-Admin-Token": TOKEN_ADMIN_TESTE, "X-Admin-Nome": "Equipe de teste"}


@pytest.fixture
def aprovar_profissional(client, admin_headers):
    """Aprova um profissional pelo caminho real: a rota da equipe."""
    def _aprovar(profissional_id):
        res = client.post(f"/admin/profissionais/{profissional_id}/aprovar", headers=admin_headers)
        assert res.status_code == 200, res.text
        return res.json()
    return _aprovar
