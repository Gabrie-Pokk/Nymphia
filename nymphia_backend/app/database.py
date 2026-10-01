from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

db_url = settings.NYMPHIA_DATABASE_URL
# Normaliza URLs geradas por provedores de nuvem (Render/Heroku usam postgres://, mas SQLAlchemy exige postgresql://)
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

connect_args = {}
engine_kwargs = {"echo": False}

if db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
else:
    # Boas práticas para PostgreSQL em produção
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 300

engine = create_engine(
    db_url,
    connect_args=connect_args,
    **engine_kwargs
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

import logging
from sqlalchemy import inspect, text

logger = logging.getLogger("nymphia.database")

def executar_migracoes_automaticas():
    """
    Executa migrações idempotentes de schema para garantir que novas colunas
    existam no PostgreSQL ou SQLite sem requerer migração manual externa.
    """
    try:
        inspector = inspect(engine)
        tabelas = inspector.get_table_names()

        if "perfis_clinicos" in tabelas:
            colunas = [c["name"] for c in inspector.get_columns("perfis_clinicos")]
            with engine.begin() as conn:
                if "altura_cm" not in colunas:
                    logger.info("Migração: Adicionando coluna altura_cm em perfis_clinicos...")
                    conn.execute(text("ALTER TABLE perfis_clinicos ADD COLUMN altura_cm FLOAT;"))
                if "peso_pre_gestacional" not in colunas:
                    logger.info("Migração: Adicionando coluna peso_pre_gestacional em perfis_clinicos...")
                    conn.execute(text("ALTER TABLE perfis_clinicos ADD COLUMN peso_pre_gestacional FLOAT;"))
                if "maternidade_latitude" not in colunas:
                    conn.execute(text("ALTER TABLE perfis_clinicos ADD COLUMN maternidade_latitude FLOAT;"))
                if "maternidade_longitude" not in colunas:
                    conn.execute(text("ALTER TABLE perfis_clinicos ADD COLUMN maternidade_longitude FLOAT;"))
                if "dpp_editada_manualmente" not in colunas:
                    conn.execute(text("ALTER TABLE perfis_clinicos ADD COLUMN dpp_editada_manualmente BOOLEAN DEFAULT FALSE;"))
        logger.info("Migrações automáticas de schema concluídas com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao executar migrações automáticas: {e}")

