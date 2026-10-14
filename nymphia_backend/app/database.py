import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

raw_url = (
    os.getenv("DATABASE_URL")
    or os.getenv("NYMPHIA_DATABASE_URL")
    or settings.DATABASE_URL
    or settings.NYMPHIA_DATABASE_URL
    or "sqlite:///./nymphia.db"
)

# Normaliza URLs geradas por provedores de nuvem (Render/Heroku usam postgres://, mas SQLAlchemy exige postgresql://)
if raw_url.startswith("postgres://"):
    db_url = raw_url.replace("postgres://", "postgresql://", 1)
else:
    db_url = raw_url

connect_args = {}
engine_kwargs = {"echo": False}

if db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
else:
    # Boas práticas para PostgreSQL em produção (conexões resilientes com healthcheck)
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

        # Migrações LGPD / CFM para Gestantes
        if "gestantes" in tabelas:
            colunas_gest = [c["name"] for c in inspector.get_columns("gestantes")]
            with engine.begin() as conn:
                if "termos_aceitos_em" not in colunas_gest:
                    logger.info("Migração: Adicionando coluna termos_aceitos_em em gestantes...")
                    conn.execute(text("ALTER TABLE gestantes ADD COLUMN termos_aceitos_em DATETIME;"))
                if "termos_versao" not in colunas_gest:
                    logger.info("Migração: Adicionando coluna termos_versao em gestantes...")
                    conn.execute(text("ALTER TABLE gestantes ADD COLUMN termos_versao VARCHAR(20) DEFAULT '1.0-2026';"))
                if "consentimento_dados_saude" not in colunas_gest:
                    logger.info("Migração: Adicionando coluna consentimento_dados_saude em gestantes...")
                    conn.execute(text("ALTER TABLE gestantes ADD COLUMN consentimento_dados_saude BOOLEAN DEFAULT FALSE;"))
                if "consentimento_dados_saude_em" not in colunas_gest:
                    logger.info("Migração: Adicionando coluna consentimento_dados_saude_em em gestantes...")
                    conn.execute(text("ALTER TABLE gestantes ADD COLUMN consentimento_dados_saude_em DATETIME;"))

        # Migrações Termos para Profissionais
        if "profissionais" in tabelas:
            colunas_prof = [c["name"] for c in inspector.get_columns("profissionais")]
            with engine.begin() as conn:
                if "termos_aceitos_em" not in colunas_prof:
                    logger.info("Migração: Adicionando coluna termos_aceitos_em em profissionais...")
                    conn.execute(text("ALTER TABLE profissionais ADD COLUMN termos_aceitos_em DATETIME;"))
                if "termos_versao" not in colunas_prof:
                    logger.info("Migração: Adicionando coluna termos_versao em profissionais...")
                    conn.execute(text("ALTER TABLE profissionais ADD COLUMN termos_versao VARCHAR(20) DEFAULT '1.0-2026';"))

        # Migrações Termos para Parceiros
        if "parceiros" in tabelas:
            colunas_parc = [c["name"] for c in inspector.get_columns("parceiros")]
            with engine.begin() as conn:
                if "termos_aceitos_em" not in colunas_parc:
                    logger.info("Migração: Adicionando coluna termos_aceitos_em em parceiros...")
                    conn.execute(text("ALTER TABLE parceiros ADD COLUMN termos_aceitos_em DATETIME;"))
                if "termos_versao" not in colunas_parc:
                    logger.info("Migração: Adicionando coluna termos_versao em parceiros...")
                    conn.execute(text("ALTER TABLE parceiros ADD COLUMN termos_versao VARCHAR(20) DEFAULT '1.0-2026';"))

        # Migrações Moderação Comunidade Segura (STF Tema 987)
        if "posts_comunidade" in tabelas:
            colunas_posts = [c["name"] for c in inspector.get_columns("posts_comunidade")]
            with engine.begin() as conn:
                if "ocultado" not in colunas_posts:
                    logger.info("Migração: Adicionando coluna ocultado em posts_comunidade...")
                    conn.execute(text("ALTER TABLE posts_comunidade ADD COLUMN ocultado BOOLEAN DEFAULT FALSE;"))
                if "motivo_ocultacao" not in colunas_posts:
                    logger.info("Migração: Adicionando coluna motivo_ocultacao em posts_comunidade...")
                    conn.execute(text("ALTER TABLE posts_comunidade ADD COLUMN motivo_ocultacao VARCHAR(255);"))

        if "comentarios_comunidade" in tabelas:
            colunas_coments = [c["name"] for c in inspector.get_columns("comentarios_comunidade")]
            with engine.begin() as conn:
                if "ocultado" not in colunas_coments:
                    logger.info("Migração: Adicionando coluna ocultado em comentarios_comunidade...")
                    conn.execute(text("ALTER TABLE comentarios_comunidade ADD COLUMN ocultado BOOLEAN DEFAULT FALSE;"))

        # Migração Crítica Emergência: Permitir chamadas anônimas sem violação de FK
        if "eventos_emergencia" in tabelas:
            col_emerg = {c["name"]: c for c in inspector.get_columns("eventos_emergencia")}
            if "gestante_id" in col_emerg and not col_emerg["gestante_id"]["nullable"]:
                with engine.begin() as conn:
                    logger.info("Migração: Permitindo gestante_id NULL em eventos_emergencia para chamadas anônimas...")
                    if not db_url.startswith("sqlite"):
                        conn.execute(text("ALTER TABLE eventos_emergencia ALTER COLUMN gestante_id DROP NOT NULL;"))

        # Garante que novas tabelas declaradas sejam criadas
        Base.metadata.create_all(bind=engine)
        logger.info("Migrações automáticas de schema concluídas com sucesso.")

        # Rotaciona automaticamente credenciais que ainda utilizem a senha exposta
        rotacionar_credenciais_vazadas_automaticamente()
    except Exception as e:
        logger.error(f"Erro ao executar migrações automáticas: {e}")


def rotacionar_credenciais_vazadas_automaticamente(db_session=None):
    """
    Varre as contas e rotaciona qualquer usuário que ainda utilize a senha pública 'senhaMaternidade123',
    exposta no commit histórico do deploy de 8 de outubro. Substitui imediatamente o hash por uma senha aleatória
    de alta entropia, neutralizando o vetor de ataque contra a API.
    """
    import secrets
    from app.models.auth import Gestante, Profissional, Parceiro
    from app.security.jwt_auth import verify_password, hash_password

    deve_fechar = False
    if db_session is None:
        db = SessionLocal()
        deve_fechar = True
    else:
        db = db_session

    try:
        contas_alteradas = 0
        for ModelCls in [Gestante, Profissional, Parceiro]:
            users = db.query(ModelCls).all()
            for u in users:
                if u.senha_hash and verify_password("senhaMaternidade123", u.senha_hash):
                    nova_senha = secrets.token_urlsafe(32)
                    u.senha_hash = hash_password(nova_senha)
                    contas_alteradas += 1
                    logger.warning(f"[SEGURANÇA] Credencial comprometida detectada e rotacionada com sucesso para: {u.email}")
        if contas_alteradas > 0:
            db.commit()
            logger.info(f"[SEGURANÇA] {contas_alteradas} conta(s) com senha exposta foram protegidas com novas credenciais aleatórias.")
    except Exception as e:
        logger.error(f"Erro ao rotacionar credenciais comprometidas: {e}")
        db.rollback()
    finally:
        if deve_fechar:
            db.close()


