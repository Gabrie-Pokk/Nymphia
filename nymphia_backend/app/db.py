"""
Nymphia -- Configuração do banco de dados

Por padrão, usa SQLite num arquivo local (nymphia.db) -- funciona sem
nenhuma instalação extra, direto no seu PC. Quando o PostgreSQL estiver
configurado, troca só a variável de ambiente DATABASE_URL, sem mudar
nenhum código -- o SQLAlchemy abstrai a diferença.

Exemplo de URL do Postgres, quando chegar a hora:
  postgresql://usuario:senha@localhost:5432/nymphia
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ.get("NYMPHIA_DATABASE_URL", "sqlite:///./nymphia.db")

# connect_args só é necessário pro SQLite (permite uso entre threads,
# que é como o FastAPI opera por padrão). Não faz sentido pro Postgres,
# então só aplica condicionalmente.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency do FastAPI -- abre uma sessão por requisição e garante
    que ela fecha no final, mesmo se der erro no meio."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def criar_tabelas():
    """Roda uma vez, na subida do servidor -- cria as tabelas que ainda
    não existem. Não apaga nem recria as que já existem."""
    Base.metadata.create_all(bind=engine)
