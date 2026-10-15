"""
Nymphia -- Revisão dos profissionais aprovados automaticamente.

Até 15/10/2026, o cadastro aprovava sozinho qualquer CRM com formato válido,
porque a "validação" não consultava o Conselho de verdade. Este script:

  1. normaliza o número de registro de todos os profissionais (só dígitos),
     para o login por CRM funcionar com "123.456" ou "123456";
  2. aponta registros duplicados (o mesmo CRM/UF em mais de uma conta);
  3. move para "pendente" todo profissional que está "aprovado", para a
     equipe conferir um por um pela área administrativa.

Uso (rodar no servidor, com a mesma DATABASE_URL da aplicação):
  python scripts/revisar_profissionais_aprovados.py            só mostra (padrão)
  python scripts/revisar_profissionais_aprovados.py --executar grava no banco

Nada é apagado. Quem já foi conferido pela equipe é aprovado de novo na
página /equipe do site (ou com scripts/admin_profissionais.py).

Observação: a versão de 15/10/2026 faz os passos 1 e 3 sozinha, uma única vez,
quando o servidor liga (app/database.py, profissionais_para_conferencia_manual).
Este script continua útil para ver a lista antes, num banco de cópia.
"""
import argparse
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal  # noqa: E402
from app.models.auth import Profissional  # noqa: E402
from app.services.crm_service import normalizar_registro  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Revisa profissionais aprovados automaticamente.")
    parser.add_argument("--executar", action="store_true", help="grava as mudanças (sem isso, só mostra)")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        profissionais = db.query(Profissional).all()
        print(f"Profissionais no banco: {len(profissionais)}")

        normalizados = 0
        for prof in profissionais:
            limpo = normalizar_registro(prof.registro_numero)
            if limpo and limpo != prof.registro_numero:
                print(f"  normalizar {prof.registro_numero!r} -> {limpo!r} ({prof.email})")
                prof.registro_numero = limpo
                normalizados += 1

        grupos = defaultdict(list)
        for prof in profissionais:
            chave = (prof.registro_tipo, normalizar_registro(prof.registro_numero), prof.registro_uf)
            grupos[chave].append(prof)
        duplicados = {k: v for k, v in grupos.items() if len(v) > 1}
        for (tipo, numero, uf), contas in duplicados.items():
            emails = ", ".join(p.email for p in contas)
            print(f"  ATENÇÃO: {tipo} {numero}/{uf} aparece em {len(contas)} contas: {emails}")

        movidos = 0
        for prof in profissionais:
            if prof.status_verificacao == "aprovado":
                print(f"  aprovado -> pendente: {prof.nome} <{prof.email}> "
                      f"{prof.registro_tipo} {normalizar_registro(prof.registro_numero)}/{prof.registro_uf}")
                prof.status_verificacao = "pendente"
                movidos += 1

        print()
        print(f"Registros normalizados: {normalizados}")
        print(f"Registros duplicados:   {len(duplicados)}")
        print(f"Movidos para pendente:  {movidos}")

        if args.executar:
            db.commit()
            print("Mudanças gravadas.")
        else:
            db.rollback()
            print("Nada foi gravado. Rode de novo com --executar para aplicar.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
