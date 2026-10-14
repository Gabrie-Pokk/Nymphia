"""
Nymphia — Script de Rotação Imediata de Credenciais Comprometidas
Localiza e invalida senhas 'senhaMaternidade123' em contas de gestantes, médicos e parceiros.
Gera senhas aleatórias de alta entropia com hash bcrypt e salva registro local não versionado.
"""
import os
import sys
import secrets
from pathlib import Path

# Adiciona o diretório do backend ao sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.database import SessionLocal
from app.models.auth import Gestante, Profissional, Parceiro
from app.security.jwt_auth import verify_password, hash_password

def rotacionar_senhas():
    print("=" * 70)
    print("🔒 NYMPHIA — ROTAÇÃO DE CREDENCIAIS COMPROMETIDAS")
    print("=" * 70)

    db = SessionLocal()
    credenciais_novas = []
    total_rotacionadas = 0

    try:
        contas_alvo = [
            ("Gestante", Gestante),
            ("Profissional", Profissional),
            ("Parceiro", Parceiro)
        ]

        for rotulo, ModelCls in contas_alvo:
            usuarios = db.query(ModelCls).all()
            for u in usuarios:
                if u.senha_hash and verify_password("senhaMaternidade123", u.senha_hash):
                    nova_senha = secrets.token_urlsafe(20) + "!N26"
                    u.senha_hash = hash_password(nova_senha)
                    total_rotacionadas += 1
                    credenciais_novas.append({
                        "perfil": rotulo,
                        "nome": u.nome,
                        "email": u.email,
                        "nova_senha": nova_senha
                    })
                    print(f"[✓] {rotulo:12} | {u.email:30} -> Senha antiga REVOGADA com sucesso!")

        if total_rotacionadas > 0:
            db.commit()
            print("-" * 70)
            print(f"Sucesso: {total_rotacionadas} conta(s) rotacionada(s) e protegidas no banco.")
            
            # Salvar de forma segura em arquivo local ignorado pelo git
            output_path = backend_dir / ".env.credenciais_rotacionadas"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("# Credenciais de contingência geradas localmente pelo script de segurança\n")
                f.write("# NUNCA COMMITE ESTE ARQUIVO\n\n")
                for c in credenciais_novas:
                    f.write(f"[{c['perfil'].upper()}]\n")
                    f.write(f"NOME={c['nome']}\n")
                    f.write(f"EMAIL={c['email']}\n")
                    f.write(f"NOVA_SENHA={c['nova_senha']}\n\n")
            print(f"[ARQUIVO SEGURO] Novas credenciais registradas em: {output_path.name}")
        else:
            print("[INFO] Nenhuma conta com a senha comprometida 'senhaMaternidade123' foi encontrada.")
            print("[✓] O banco já está protegido contra este vetor de ataque.")

    except Exception as e:
        db.rollback()
        print(f"[ERRO] Falha ao rotacionar credenciais: {e}")
        sys.exit(1)
    finally:
        db.close()
    print("=" * 70)

if __name__ == "__main__":
    rotacionar_senhas()
