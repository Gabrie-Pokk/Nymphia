#!/usr/bin/env python3
"""
SCRIPT DE RETROCOMPATIBILIDADE DE IDENTIFICADORES DE CHECK-IN (Nymphia)
========================================================================

Contexto (Seção 31.5 da Documentação):
Registros antigos do aplicativo móvel salvavam check-ins sob um identificador anônimo
gerado no aparelho (ex: 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx') antes da existência
de contas autenticadas. Como o painel do profissional busca pelo ID da conta
(gestantes.id), esses registros antigos não são contabilizados, mantendo a contagem
de alertas em zero.

IMPORTANTE (REGRA 2 DE SEGURANÇA):
Este script NÃO deve ser executado automaticamente. Ele analisa a base de dados,
identifica mapeamentos inequívocos entre IDs de aparelho e contas cadastradas,
isola e lista os casos ambíguos sem alterá-los, e aguarda confirmação explícita do Gabriel.

COMO EXECUTAR:
1. Modo Simulação / Auditoria (Padrão e Seguro — Apenas gera relatório):
   python scripts/retrocompat_checkin_device_id.py --dry-run

2. Execução Real (Requer flag explícita do Gabriel):
   python scripts/retrocompat_checkin_device_id.py --confirmar-execucao
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configuração de Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("retrocompat-checkin")


def analisar_e_reconciliar_checkins(database_url: str, dry_run: bool = True):
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    engine = create_engine(database_url, connect_args=connect_args)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 1. Busca todos os gestante_id distintos em checkin_registros que NÃO existem na tabela gestantes
        query_orfãos = text("""
            SELECT DISTINCT gestante_id 
            FROM checkin_registros 
            WHERE gestante_id NOT IN (SELECT id FROM gestantes);
        """)
        ids_aparelho = [row[0] for row in session.execute(query_orfãos).fetchall()]

        logger.info(f"Identificadores de aparelho anônimos encontrados na base: {len(ids_aparelho)}")

        if not ids_aparelho:
            logger.info("Nenhum registro órfão de check-in encontrado. Todos os check-ins já pertencem a contas válidas!")
            return

        # 2. Busca contas cadastradas e seus perfis clínicos para correlação
        query_gestantes = text("""
            SELECT g.id, g.nome, g.email, g.criado_em, p.dum, p.dpp
            FROM gestantes g
            LEFT JOIN perfis_clinicos p ON p.gestante_id = g.id;
        """)
        gestantes = session.execute(query_gestantes).mappings().all()

        mapeamentos_inequivocos = []
        casos_ambiguos = []

        for dev_id in ids_aparelho:
            # Coleta check-ins deste aparelho
            query_checks = text("""
                SELECT id, data_hora, semana_gestacional, sintomas, descricao 
                FROM checkin_registros 
                WHERE gestante_id = :dev_id 
                ORDER BY data_hora ASC;
            """)
            checks = session.execute(query_checks, {"dev_id": dev_id}).mappings().all()
            qtd_checks = len(checks)
            data_primeiro_check = checks[0]["data_hora"]
            data_ultimo_check = checks[-1]["data_hora"]

            # Candidatos a match clínico
            candidatos = []
            for g in gestantes:
                # Critério A: Compatibilidade temporal (conta criada próximo ou antes do check-in)
                dt_conta = g["criado_em"]
                # Tolerância de 14 dias entre o primeiro check-in no aparelho e a criação formal da conta
                if abs((data_primeiro_check - dt_conta).days) <= 14 or (dt_conta <= data_ultimo_check + timedelta(days=7)):
                    # Critério B: Idade gestacional coerente se houver DUM
                    if g["dum"] and checks[0]["semana_gestacional"]:
                        semana_esperada = max(1, (data_primeiro_check.date() - g["dum"]).days // 7)
                        semana_registrada = checks[0]["semana_gestacional"]
                        if abs(semana_esperada - semana_registrada) <= 2:
                            candidatos.append(g)
                    else:
                        candidatos.append(g)

            # Avaliação de Ambiguidade
            if len(candidatos) == 1:
                # MATCH INEQUÍVOCO: exatamente uma conta candidata com correlação clínica e temporal
                match_gestante = candidatos[0]
                mapeamentos_inequivocos.append({
                    "device_id": dev_id,
                    "gestante_id_alvo": match_gestante["id"],
                    "gestante_nome": match_gestante["nome"],
                    "gestante_email": match_gestante["email"],
                    "quantidade_checkins": qtd_checks,
                    "periodo": f"{data_primeiro_check} até {data_ultimo_check}"
                })
            else:
                # CASO AMBÍGUO (0 candidatos ou mais de 1 candidato possível)
                casos_ambiguos.append({
                    "device_id": dev_id,
                    "quantidade_checkins": qtd_checks,
                    "primeiro_checkin": str(data_primeiro_check),
                    "ultimo_checkin": str(data_ultimo_check),
                    "motivo_ambiguidade": "Nenhuma conta correspondente no intervalo" if len(candidatos) == 0 else f"Múltiplas contas concorrentes ({len(candidatos)})",
                    "candidatos_ids": [c["id"] for c in candidatos]
                })

        # 3. Exibição dos Resultados da Auditoria
        logger.info("\n" + "="*70)
        logger.info(f"RESULTADO DA AUDITORIA DE CHECK-INS ANTIGOS:")
        logger.info(f"- Mapeamentos Inequívocos (Seguros para migração): {len(mapeamentos_inequivocos)}")
        logger.info(f"- Casos Ambíguos (ISOLADOS e PRESERVADOS sem alteração): {len(casos_ambiguos)}")
        logger.info("="*70)

        for m in mapeamentos_inequivocos:
            logger.info(f"[INEQUÍVOCO] Aparelho {m['device_id'][:12]}... -> Conta {m['gestante_nome']} ({m['gestante_id_alvo'][:8]}...) | {m['quantidade_checkins']} check-ins")

        for a in casos_ambiguos:
            logger.warning(f"[AMBÍGUO - NÃO TOCAR] Aparelho {a['device_id']} | Motivo: {a['motivo_ambiguidade']} | {a['quantidade_checkins']} check-ins")

        # Salva relatório JSON auditável
        relatorio_path = "scripts/relatorio_auditoria_checkins_ambiguos.json"
        with open(relatorio_path, "w", encoding="utf-8") as f:
            json.dump({
                "auditado_em": datetime.utcnow().isoformat(),
                "total_inequivocos": len(mapeamentos_inequivocos),
                "total_ambiguos": len(casos_ambiguos),
                "inequivocos": mapeamentos_inequivocos,
                "ambiguos": casos_ambiguos
            }, f, indent=2, ensure_ascii=False)
        logger.info(f"Relatório detalhado salvo em: {relatorio_path}")

        # 4. Execução (se não for dry-run e houver mapeamentos)
        if not dry_run and mapeamentos_inequivocos:
            logger.info("Aplicando migração dos casos inequívocos no banco de dados...")
            total_atualizados = 0
            for m in mapeamentos_inequivocos:
                res = session.execute(
                    text("UPDATE checkin_registros SET gestante_id = :conta_id WHERE gestante_id = :dev_id"),
                    {"conta_id": m["gestante_id_alvo"], "dev_id": m["device_id"]}
                )
                total_atualizados += res.rowcount
            session.commit()
            logger.info(f"Migração concluída com sucesso! Total de {total_atualizados} registros atualizados.")
        else:
            logger.info("Modo Dry-run ou nenhum registro alterado. O banco de dados permanece INTACTO.")

    finally:
        session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Retrocompatibilidade de IDs de Check-in (Nymphia)")
    parser.add_argument("--db-url", default=os.getenv("DATABASE_URL") or os.getenv("NYMPHIA_DATABASE_URL") or "sqlite:///nymphia.db")
    parser.add_argument("--dry-run", action="store_true", default=False, help="Executa apenas simulação sem alterar nada")
    parser.add_argument("--confirmar-execucao", action="store_true", help="Autorização expressa para aplicar alterações nos casos inequívocos")

    args = parser.parse_args()

    if not args.confirmar_execucao and not args.dry_run:
        print("\n[ALERTA DE SEGURANÇA - REGRA 2]")
        print("Você não especificou --dry-run nem --confirmar-execucao.")
        print("Para auditar com segurança: python scripts/retrocompat_checkin_device_id.py --dry-run\n")
        sys.exit(0)

    is_dry_run = args.dry_run or (not args.confirmar_execucao)
    analisar_e_reconciliar_checkins(args.db_url, dry_run=is_dry_run)
