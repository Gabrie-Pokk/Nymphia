"""
Nymphia -- Autenticação

Senha nunca é salva em texto puro -- só o hash bcrypt. Sessão usa JWT,
que carrega o id da conta e o tipo de perfil (gestante ou profissional),
assinado com uma chave secreta.

ATENÇÃO pra produção: troque SECRET_KEY por uma variável de ambiente
de verdade antes de publicar. O valor abaixo serve só pra desenvolvimento.
"""
import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Header, HTTPException

SECRET_KEY = os.environ.get("NYMPHIA_SECRET_KEY", "troque-isso-antes-de-publicar-de-verdade")
ALGORITMO = "HS256"
VALIDADE_TOKEN_HORAS = 24 * 30  # 30 dias -- app móvel não deve pedir login toda hora


def hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_senha(senha: str, hash_salvo: str) -> bool:
    return bcrypt.checkpw(senha.encode("utf-8"), hash_salvo.encode("utf-8"))


def criar_token(id_conta: str, perfil: str) -> str:
    """perfil: 'gestante' ou 'profissional' -- vai dentro do token, e cada
    endpoint confere se é o perfil certo antes de deixar passar."""
    payload = {
        "sub": id_conta,
        "perfil": perfil,
        "exp": datetime.now(timezone.utc) + timedelta(hours=VALIDADE_TOKEN_HORAS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITMO)


def decodificar_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITMO])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Sessão expirada, faça login novamente.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido.")


def _extrair_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Cabeçalho Authorization ausente ou mal formatado.")
    return authorization.removeprefix("Bearer ").strip()


def exigir_gestante(authorization: str | None = Header(default=None)) -> str:
    """Dependency do FastAPI -- garante que quem chamou é uma gestante
    autenticada, e devolve o id dela. Usar em qualquer endpoint que só
    a gestante pode acessar."""
    payload = decodificar_token(_extrair_token(authorization))
    if payload.get("perfil") != "gestante":
        raise HTTPException(status_code=403, detail="Este recurso é exclusivo do perfil gestante.")
    return payload["sub"]


def exigir_profissional(authorization: str | None = Header(default=None)) -> str:
    """Mesma ideia, só que exige perfil profissional."""
    payload = decodificar_token(_extrair_token(authorization))
    if payload.get("perfil") != "profissional":
        raise HTTPException(status_code=403, detail="Este recurso é exclusivo do perfil profissional.")
    return payload["sub"]
