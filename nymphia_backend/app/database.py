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
    # Boas práticas para PostgreSQL em produção (conexões resilientes com healthcheck e timeout curto)
    connect_args["connect_timeout"] = 5
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

# Colunas que podem faltar em bancos criados por versões antigas.
# Cada entrada: (tabela, coluna, tipo SQL). "{DATA}" vira o tipo de data certo
# para cada banco: TIMESTAMP no PostgreSQL, DATETIME no SQLite. (O PostgreSQL
# não tem o tipo DATETIME; usar DATETIME nele fazia a migração falhar.)
COLUNAS_ADICIONADAS_DEPOIS = [
    ("perfis_clinicos", "altura_cm", "FLOAT"),
    ("perfis_clinicos", "peso_pre_gestacional", "FLOAT"),
    ("perfis_clinicos", "maternidade_latitude", "FLOAT"),
    ("perfis_clinicos", "maternidade_longitude", "FLOAT"),
    ("perfis_clinicos", "dpp_editada_manualmente", "BOOLEAN DEFAULT FALSE"),
    ("gestantes", "termos_aceitos_em", "{DATA}"),
    ("gestantes", "termos_versao", "VARCHAR(20) DEFAULT '1.0-2026'"),
    ("gestantes", "consentimento_dados_saude", "BOOLEAN DEFAULT FALSE"),
    ("gestantes", "consentimento_dados_saude_em", "{DATA}"),
    ("gestantes", "sessoes_validas_desde", "{DATA}"),
    ("profissionais", "termos_aceitos_em", "{DATA}"),
    ("profissionais", "termos_versao", "VARCHAR(20) DEFAULT '1.0-2026'"),
    ("profissionais", "sessoes_validas_desde", "{DATA}"),
    ("parceiros", "termos_aceitos_em", "{DATA}"),
    ("parceiros", "termos_versao", "VARCHAR(20) DEFAULT '1.0-2026'"),
    ("parceiros", "sessoes_validas_desde", "{DATA}"),
    ("posts_comunidade", "ocultado", "BOOLEAN DEFAULT FALSE"),
    ("posts_comunidade", "motivo_ocultacao", "VARCHAR(255)"),
    ("comentarios_comunidade", "ocultado", "BOOLEAN DEFAULT FALSE"),
    ("checkin_registros", "sinais_atencao", "JSON"),
]


def _tipo_data() -> str:
    return "DATETIME" if db_url.startswith("sqlite") else "TIMESTAMP"


def executar_migracoes_automaticas():
    """
    Migrações idempotentes de schema, rodadas a cada inicialização.

    Cada coluna é tentada separadamente: se uma falhar, as outras continuam
    (antes, um único erro interrompia todas as migrações seguintes).
    """
    try:
        inspector = inspect(engine)
        tabelas = set(inspector.get_table_names())
    except Exception as e:
        logger.error(f"Migrações: não foi possível ler o schema do banco: {e}")
        return

    colunas_por_tabela = {}
    for tabela, coluna, tipo in COLUNAS_ADICIONADAS_DEPOIS:
        if tabela not in tabelas:
            continue
        if tabela not in colunas_por_tabela:
            colunas_por_tabela[tabela] = {c["name"] for c in inspector.get_columns(tabela)}
        if coluna in colunas_por_tabela[tabela]:
            continue
        tipo_sql = tipo.replace("{DATA}", _tipo_data())
        try:
            with engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {tipo_sql};"))
            colunas_por_tabela[tabela].add(coluna)
            logger.info(f"Migração: coluna {coluna} adicionada em {tabela}.")
        except Exception as e:
            logger.error(f"Migração: falha ao adicionar {coluna} em {tabela}: {e}")

    # Emergência anônima: gestante_id precisa aceitar NULL
    try:
        if "eventos_emergencia" in tabelas:
            col_emerg = {c["name"]: c for c in inspector.get_columns("eventos_emergencia")}
            if "gestante_id" in col_emerg and not col_emerg["gestante_id"]["nullable"]:
                with engine.begin() as conn:
                    logger.info("Migração: Permitindo gestante_id NULL em eventos_emergencia para chamadas anônimas...")
                    if not db_url.startswith("sqlite"):
                        conn.execute(text("ALTER TABLE eventos_emergencia ALTER COLUMN gestante_id DROP NOT NULL;"))
                    else:
                        # Em SQLite, recria a tabela preservando os dados para remover NOT NULL de gestante_id
                        conn.execute(text("CREATE TABLE eventos_emergencia_migracao (id INTEGER PRIMARY KEY AUTOINCREMENT, gestante_id VARCHAR(36), data_hora DATETIME NOT NULL, latitude FLOAT, longitude FLOAT, contexto JSON, profissional_notificado BOOLEAN DEFAULT 0);"))
                        conn.execute(text("INSERT INTO eventos_emergencia_migracao (id, gestante_id, data_hora, latitude, longitude, contexto, profissional_notificado) SELECT id, gestante_id, data_hora, latitude, longitude, contexto, profissional_notificado FROM eventos_emergencia;"))
                        conn.execute(text("DROP TABLE eventos_emergencia;"))
                        conn.execute(text("ALTER TABLE eventos_emergencia_migracao RENAME TO eventos_emergencia;"))
    except Exception as e:
        logger.error(f"Migração de eventos_emergencia falhou: {e}")

    try:
        # Garante que novas tabelas declaradas sejam criadas
        Base.metadata.create_all(bind=engine)
        logger.info("Migrações automáticas de schema concluídas.")
    except Exception as e:
        logger.error(f"Erro ao criar tabelas novas: {e}")

    # Manutenções que precisam rodar uma única vez por banco
    _executar_uma_vez("rotacao_senha_vazada_2026_10_08", rotacionar_credenciais_vazadas_automaticamente)
    _executar_uma_vez("remover_ocr_simulado_2026_10_15", _remover_valores_de_ocr_simulado)


def _remover_valores_de_ocr_simulado() -> None:
    """
    Todo valor em exames.valores_extraidos foi gerado pela simulação de OCR
    (números inventados). Nenhum veio de leitura real do laudo. Apaga todos.
    """
    with engine.begin() as conn:
        if "exames" in inspect(engine).get_table_names():
            conn.execute(text("UPDATE exames SET valores_extraidos = NULL"))


def _executar_uma_vez(nome: str, funcao) -> None:
    """
    Roda uma manutenção uma única vez por banco e anota na tabela
    manutencoes_executadas. A rotação de senha vazada, por exemplo, testava o
    bcrypt de TODAS as contas a cada inicialização, o que deixava o servidor
    cada vez mais lento para ligar conforme a base crescia.
    """
    try:
        with engine.begin() as conn:
            conn.execute(text(
                "CREATE TABLE IF NOT EXISTS manutencoes_executadas ("
                "nome VARCHAR(100) PRIMARY KEY, executada_em VARCHAR(40) NOT NULL)"
            ))
            ja_rodou = conn.execute(
                text("SELECT 1 FROM manutencoes_executadas WHERE nome = :n"), {"n": nome}
            ).first()
        if ja_rodou:
            return
        funcao()
        from datetime import datetime as _dt
        with engine.begin() as conn:
            conn.execute(
                text("INSERT INTO manutencoes_executadas (nome, executada_em) VALUES (:n, :e)"),
                {"n": nome, "e": _dt.utcnow().isoformat()}
            )
        logger.info(f"Manutenção única concluída: {nome}")
    except Exception as e:
        logger.error(f"Manutenção única {nome} falhou e será tentada de novo na próxima inicialização: {e}")


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
        # Propaga o erro para a manutenção não ser marcada como concluída
        raise
    finally:
        if deve_fechar:
            db.close()


