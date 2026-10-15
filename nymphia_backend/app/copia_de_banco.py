"""
Cópia única de um banco antigo para o banco atual.

Para que serve: o Postgres grátis do Render expira 30 dias depois de criado
(o da Nymphia expira em 19/10/2026) e depois é apagado. Para trocar de banco
sem baixar nada para o computador de ninguém:

  1. crie o banco novo, vazio (Neon, Coolify, o que for);
  2. no serviço, ponha o endereço do banco ATUAL em NYMPHIA_DATABASE_URL_ANTIGO
     e o do banco NOVO em NYMPHIA_DATABASE_URL (ou DATABASE_URL);
  3. salve. Na inicialização o servidor copia todas as tabelas, uma vez.

Garantias:
  - só copia se o banco novo não tiver nenhuma conta (gestante, profissional
    ou parceiro). Depois da cópia, a variável pode ficar: nada é copiado de novo;
  - tudo acontece numa transação só: se algo falhar, o banco novo fica como
    estava e a inicialização PARA. No Render, a versão anterior continua no ar,
    ligada ao banco antigo, até a cópia dar certo;
  - os dados vão de servidor para servidor. O log mostra só nomes de tabelas
    e quantidades, nunca endereços, senhas ou dados de pacientes.
"""
import logging
import os
from typing import Dict, Optional

from sqlalchemy import MetaData, Text, cast, create_engine, inspect, select, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.sql import sqltypes
from sqlalchemy.types import TypeDecorator

logger = logging.getLogger("nymphia.copia_de_banco")

VARIAVEL_BANCO_ANTIGO = "NYMPHIA_DATABASE_URL_ANTIGO"
TABELAS_DE_CONTAS = ("gestantes", "profissionais", "parceiros")
TAMANHO_DO_LOTE = 500


def _mesmo_banco(url_a, url_b) -> bool:
    a, b = make_url(str(url_a)), url_b
    return (
        a.get_backend_name() == b.get_backend_name()
        and (a.host or "") == (b.host or "")
        and (a.port or 0) == (b.port or 0)
        and (a.database or "") == (b.database or "")
    )


def banco_tem_contas(engine: Engine) -> bool:
    nomes = set(inspect(engine).get_table_names())
    with engine.connect() as conn:
        for tabela in TABELAS_DE_CONTAS:
            if tabela in nomes and conn.execute(text(f"SELECT 1 FROM {tabela} LIMIT 1")).first():
                return True
    return False


def _primeira_linha_do_erro(erro: Exception) -> str:
    # Só a primeira linha: as seguintes costumam trazer valores das linhas
    # (e-mails, nomes) e o comando SQL com parâmetros, que não vão para o log.
    original = getattr(erro, "orig", None) or erro
    linhas = str(original).strip().splitlines()
    return f"{type(original).__name__}: {linhas[0] if linhas else ''}"[:300]


class _JsonComoEstava(TypeDecorator):
    """
    Colunas JSON passam como texto, exatamente como estavam no banco antigo.
    Se o valor fosse lido e gravado de novo pelo tipo JSON, um NULL e um JSON
    'null' virariam a mesma coisa, e uma coluna obrigatória poderia recusar a linha.
    """
    impl = Text
    cache_ok = False

    def __init__(self, tipo_json, converter_no_banco: bool):
        super().__init__()
        self.tipo_json = tipo_json
        self.converter_no_banco = converter_no_banco

    def bind_expression(self, valor):
        # No PostgreSQL o texto vira JSON dentro do próprio banco
        return cast(valor, self.tipo_json) if self.converter_no_banco else valor


def _preparar_colunas_json(tabela, no_postgres: bool) -> set:
    nomes = set()
    for coluna in tabela.columns:
        if isinstance(coluna.type, sqltypes.JSON):
            coluna.type = _JsonComoEstava(coluna.type, no_postgres)
            nomes.add(coluna.name)
    return nomes


def _acertar_sequencias(conn, metadados: MetaData) -> None:
    """No PostgreSQL, faz os contadores de id continuarem depois do maior id copiado."""
    preparador = conn.dialect.identifier_preparer
    for tabela in metadados.sorted_tables:
        for coluna in tabela.primary_key.columns:
            if not isinstance(coluna.type, sqltypes.Integer):
                continue
            sequencia = conn.execute(
                text("SELECT pg_get_serial_sequence(:t, :c)"),
                {"t": preparador.quote(tabela.name), "c": coluna.name},
            ).scalar()
            if not sequencia:
                continue
            nome_coluna = preparador.quote(coluna.name)
            nome_tabela = preparador.quote(tabela.name)
            conn.execute(
                text(
                    f"SELECT setval(CAST(:s AS regclass), "
                    f"COALESCE((SELECT MAX({nome_coluna}) FROM {nome_tabela}), 0) + 1, false)"
                ),
                {"s": sequencia},
            )


def copiar_banco_antigo_se_preciso(destino: Optional[Engine] = None, url_origem: Optional[str] = None) -> Optional[Dict]:
    """
    Copia o banco de NYMPHIA_DATABASE_URL_ANTIGO para o banco atual, se fizer
    sentido. Devolve None quando a variável não existe; um resumo quando
    decide não copiar ou quando copia. Levanta RuntimeError se a cópia falhar.
    """
    if url_origem is None:
        url_origem = os.getenv(VARIAVEL_BANCO_ANTIGO, "")
    if not (url_origem or "").strip():
        return None

    if destino is None:
        from app.database import engine as destino

    from app.config import limpar_endereco_do_banco
    try:
        url_origem = limpar_endereco_do_banco(url_origem)
        mesmo = _mesmo_banco(url_origem, destino.url)
    except Exception:
        raise RuntimeError(
            f"{VARIAVEL_BANCO_ANTIGO} não é um endereço de banco válido. "
            "Copie o endereço inteiro do banco antigo (começa com postgresql:// ou postgres://)."
        ) from None
    if mesmo:
        logger.warning(
            f"{VARIAVEL_BANCO_ANTIGO} aponta para o mesmo banco que o servidor já usa. "
            "Nada foi copiado. Coloque o endereço do banco NOVO em NYMPHIA_DATABASE_URL."
        )
        return {"copiado": False, "motivo": "mesmo_banco"}

    if banco_tem_contas(destino):
        logger.info(
            "Cópia do banco antigo: o banco atual já tem contas, então nada foi copiado. "
            f"Se a cópia já foi feita, {VARIAVEL_BANCO_ANTIGO} pode ser apagada."
        )
        return {"copiado": False, "motivo": "destino_com_contas"}

    argumentos = {}
    if url_origem.startswith("postgresql"):
        argumentos["connect_args"] = {"connect_timeout": 15}
    origem = None
    tabela_atual = "(lendo a estrutura do banco antigo)"
    try:
        origem = create_engine(url_origem, pool_pre_ping=True, **argumentos)
        meta_origem = MetaData()
        meta_origem.reflect(bind=origem)

        # Tabelas que só existem no banco antigo (manutenções já feitas, chave
        # dos logins) são criadas no novo com a mesma estrutura.
        existentes = set(inspect(destino).get_table_names())
        faltando = [t for t in meta_origem.sorted_tables if t.name not in existentes]
        if faltando:
            meta_origem.create_all(bind=destino, tables=faltando)

        meta_destino = MetaData()
        meta_destino.reflect(bind=destino)
        destino_postgres = destino.dialect.name == "postgresql"
        colunas_json = {
            nome: _preparar_colunas_json(tabela, destino_postgres) for nome, tabela in meta_destino.tables.items()
        }

        resumo: Dict[str, int] = {}
        with destino.begin() as conn_destino, origem.connect() as conn_origem:
            # O banco novo não tem contas; o que houver nele (chave criada na
            # primeira inicialização, manutenções anotadas) dá lugar ao do antigo.
            for tabela in reversed(meta_destino.sorted_tables):
                if tabela.name in meta_origem.tables:
                    tabela_atual = tabela.name
                    conn_destino.execute(tabela.delete())

            for tabela_origem in meta_origem.sorted_tables:
                tabela_destino = meta_destino.tables.get(tabela_origem.name)
                if tabela_destino is None:
                    continue
                tabela_atual = tabela_origem.name
                colunas = [c.name for c in tabela_origem.columns if c.name in tabela_destino.columns]
                # Em ordem de id: se uma linha aponta para outra da mesma tabela
                # (resposta de comentário, por exemplo), a de cima entra antes.
                json_aqui = colunas_json.get(tabela_origem.name, set())
                consulta = (
                    select(*[
                        cast(tabela_origem.c[nome], Text).label(nome) if nome in json_aqui else tabela_origem.c[nome]
                        for nome in colunas
                    ])
                    .order_by(*tabela_origem.primary_key.columns)
                    .execution_options(yield_per=TAMANHO_DO_LOTE)
                )
                resultado = conn_origem.execute(consulta)
                copiadas = 0
                for lote in resultado.mappings().partitions():
                    conn_destino.execute(tabela_destino.insert(), [dict(linha) for linha in lote])
                    copiadas += len(lote)
                resumo[tabela_origem.name] = copiadas

            if conn_destino.dialect.name == "postgresql":
                tabela_atual = "(acertando os contadores de id)"
                _acertar_sequencias(conn_destino, meta_destino)
    except Exception as erro:
        logger.error(f"Cópia do banco antigo FALHOU na tabela {tabela_atual}: {_primeira_linha_do_erro(erro)}")
        raise RuntimeError(
            "A cópia do banco antigo falhou e o banco novo ficou como estava. "
            f"Veja o erro acima. Para ligar sem copiar, apague {VARIAVEL_BANCO_ANTIGO}."
        ) from None
    finally:
        if origem is not None:
            origem.dispose()

    total = sum(resumo.values())
    principais = ", ".join(f"{t}: {resumo[t]}" for t in TABELAS_DE_CONTAS if t in resumo)
    logger.warning(
        f"Cópia do banco antigo concluída: {total} linhas em {len(resumo)} tabelas ({principais}). "
        f"Confira o site e depois apague {VARIAVEL_BANCO_ANTIGO}."
    )
    return {"copiado": True, "linhas": total, "tabelas": resumo}
