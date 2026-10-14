#!/usr/bin/env python3
"""
SCRIPT DE MIGRAÇÃO: SQLite para PostgreSQL (Nymphia)
=====================================================

IMPORTANTE (REGRA 2 DE SEGURANÇA):
Este script NÃO deve ser executado automaticamente. Ele foi desenvolvido para
que o Gabriel (fundador) revise os parâmetros de conexão e execute manualmente
quando o banco PostgreSQL de produção no Render (ou outro provedor) estiver provisionado.

COMO EXECUTAR:
1. Modo Simulação (Dry-run — Apenas inspeciona e conta os registros sem alterar nada):
   python scripts/migrar_sqlite_para_postgres.py --dry-run

2. Execução Real (Requer flag explícita e DATABASE_URL configurada):
   export TARGET_DATABASE_URL="postgresql://nymphia_admin:SUA_SENHA@dpg-xxx-a.oregon-postgres.render.com/nymphia"
   python scripts/migrar_sqlite_para_postgres.py --confirmar-execucao

ORDEM DE MIGRAÇÃO (Respeitando Integridade Referencial e Chaves Estrangeiras):
1. Usuários e Perfis Base (gestantes, profissionais, parceiros)
2. Dados Clínicos e Obstétricos (perfis_clinicos, historico_familiar)
3. Interações e Diários (checkins, mensagens, eventos_agenda, eventos_emergencia)
4. Vínculos e Segurança (vinculos, codigos_convite, vinculos_parceiro, logs_acesso)
5. Exames e Comunidade (exames, posts_comunidade, comentarios_comunidade)
6. Telemetria e Governança SAMD (medicoes_dispositivos, observacoes_profissionais, calibracoes_clinicas, integracoes_laboratoriais)
7. Assinaturas e Transações (assinaturas, transacoes_pagamento)
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any

from sqlalchemy import create_engine, MetaData, Table, inspect, select, text
from sqlalchemy.orm import sessionmaker

# Configuração de Logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("migracao-nymphia")

# Tabelas em ordem topológica de dependência (pais antes de filhos)
TABELAS_ORDEM_MIGRACAO = [
    "gestantes",
    "profissionais",
    "parceiros",
    "perfis_clinicos",
    "historico_familiar",
    "checkins",
    "mensagens",
    "eventos_agenda",
    "eventos_emergencia",
    "vinculos",
    "codigos_convite",
    "vinculos_parceiro",
    "logs_acesso",
    "exames",
    "posts_comunidade",
    "comentarios_comunidade",
    "medicoes_dispositivos",
    "observacoes_profissionais",
    "calibracoes_clinicas",
    "integracoes_laboratoriais",
    "assinaturas",
    "transacoes_pagamento"
]

def verificar_integridade_e_contagens(engine_origem, engine_destino, tabelas: List[str]):
    """Compara as contagens de linhas entre a origem e o destino."""
    logger.info("=== AUDITORIA DE INTEGRIDADE: ORIGEM (SQLite) vs DESTINO (PostgreSQL) ===")
    discrepancias = 0
    with engine_origem.connect() as conn_src, engine_destino.connect() as conn_dst:
        for tab in tabelas:
            try:
                qtd_src = conn_src.execute(text(f"SELECT COUNT(*) FROM {tab}")).scalar()
            except Exception:
                qtd_src = 0
            try:
                qtd_dst = conn_dst.execute(text(f"SELECT COUNT(*) FROM {tab}")).scalar()
            except Exception:
                qtd_dst = 0

            status = "OK" if qtd_src == qtd_dst else "DISCREPÂNCIA"
            if status != "OK":
                discrepancias += 1
            logger.info(f"Tabela: {tab:<28} | SQLite: {qtd_src:<6} | PostgreSQL: {qtd_dst:<6} | Status: {status}")

    return discrepancias == 0


def migrar_dados(sqlite_path: str, postgres_url: str, dry_run: bool = True):
    if not os.path.exists(sqlite_path):
        logger.error(f"Arquivo SQLite de origem não encontrado em: {sqlite_path}")
        sys.exit(1)

    sqlite_url = f"sqlite:///{sqlite_path}"
    engine_sqlite = create_engine(sqlite_url, connect_args={"check_same_thread": False})
    
    # Normalização de URL PostgreSQL
    if postgres_url.startswith("postgres://"):
        postgres_url = postgres_url.replace("postgres://", "postgresql://", 1)
    
    engine_pg = create_engine(postgres_url, pool_pre_ping=True)

    meta_sqlite = MetaData()
    meta_sqlite.reflect(bind=engine_sqlite)

    logger.info(f"Conectado ao SQLite de origem: {sqlite_path}")
    logger.info(f"Conectado ao PostgreSQL de destino: {postgres_url.split('@')[-1] if '@' in postgres_url else 'localhost'}")

    if dry_run:
        logger.info(">>> MODO SIMULAÇÃO ATIVO (--dry-run). Nenhuma linha será escrita no PostgreSQL. <<<")

    total_registros_migrados = 0

    with engine_sqlite.connect() as conn_sqlite, engine_pg.begin() as conn_pg:
        # Se PostgreSQL, podemos desabilitar temporariamente triggers e constraints para carga em lote
        for tabela_nome in TABELAS_ORDEM_MIGRACAO:
            if tabela_nome not in meta_sqlite.tables:
                logger.warning(f"Tabela '{tabela_nome}' não encontrada no SQLite de origem. Pulando...")
                continue

            tabela_sqlite = meta_sqlite.tables[tabela_nome]
            registros = conn_sqlite.execute(select(tabela_sqlite)).mappings().all()
            qtd = len(registros)

            logger.info(f"Processando tabela '{tabela_nome}': {qtd} registros encontrados.")

            if not dry_run and qtd > 0:
                tabela_pg = Table(tabela_nome, MetaData(), autoload_with=engine_pg)
                # Inserção em lotes de 100 registros
                lote_tamanho = 100
                for i in range(0, qtd, lote_tamanho):
                    lote = [dict(r) for r in registros[i:i + lote_tamanho]]
                    conn_pg.execute(tabela_pg.insert(), lote)
                total_registros_migrados += qtd

    if dry_run:
        logger.info("=== SIMULAÇÃO CONCLUÍDA COM SUCESSO ===")
        logger.info("Para executar a migração de fato, utilize a flag --confirmar-execucao.")
    else:
        logger.info(f"=== MIGRAÇÃO CONCLUÍDA: {total_registros_migrados} registros migrados com sucesso ===")
        verificar_integridade_e_contagens(engine_sqlite, engine_pg, TABELAS_ORDEM_MIGRACAO)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrador de Dados SQLite -> PostgreSQL para Nymphia")
    parser.add_argument("--sqlite-path", default="nymphia.db", help="Caminho do arquivo nymphia.db local")
    parser.add_argument("--postgres-url", default=os.getenv("TARGET_DATABASE_URL") or os.getenv("DATABASE_URL"), help="URL de conexão PostgreSQL")
    parser.add_argument("--dry-run", action="store_true", default=False, help="Executa apenas simulação de leitura")
    parser.add_argument("--confirmar-execucao", action="store_true", help="Confirmação mandatória para execução real")

    args = parser.parse_args()

    if not args.confirmar_execucao and not args.dry_run:
        print("\n[ALERTA DE SEGURANÇA - REGRA 2]")
        print("Você não especificou --dry-run nem --confirmar-execucao.")
        print("Para simular com segurança: python scripts/migrar_sqlite_para_postgres.py --dry-run")
        print("Para migrar de fato: python scripts/migrar_sqlite_para_postgres.py --confirmar-execucao\n")
        sys.exit(0)

    is_dry_run = args.dry_run or (not args.confirmar_execucao)

    if not is_dry_run and not args.postgres_url:
        logger.error("TARGET_DATABASE_URL ou DATABASE_URL não definida no ambiente para execução real.")
        sys.exit(1)

    migrar_dados(
        sqlite_path=args.sqlite_path,
        postgres_url=args.postgres_url or "postgresql://fake:fake@localhost:5432/nymphia",
        dry_run=is_dry_run
    )
