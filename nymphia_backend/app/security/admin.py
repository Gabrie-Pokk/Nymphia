"""
Nymphia -- Acesso da equipe (área administrativa).

A área administrativa é usada pela equipe para conferir e aprovar o registro
de profissionais. Ela só funciona quando a variável de ambiente
NYMPHIA_ADMIN_TOKEN existe e tem 32 caracteres ou mais. Sem isso, toda rota
administrativa responde 503 e nada fica exposto.

Cada pedido manda o cabeçalho X-Admin-Token. A comparação é feita com
hmac.compare_digest, que leva o mesmo tempo acerte ou erre, para não vazar o
token por medição de tempo. O cabeçalho opcional X-Admin-Nome identifica quem
da equipe tomou a decisão, para a trilha de auditoria.

Para gerar um token forte:
    python -c "import secrets; print(secrets.token_urlsafe(48))"
"""
import hmac
import os
from typing import Optional

from fastapi import Header, HTTPException, status

TAMANHO_MINIMO_TOKEN_ADMIN = 32


def exigir_admin(
    x_admin_token: Optional[str] = Header(None),
    x_admin_nome: Optional[str] = Header(None),
) -> str:
    """Libera a rota só para a equipe. Devolve o nome de quem fez o pedido."""
    esperado = os.getenv("NYMPHIA_ADMIN_TOKEN", "")
    if len(esperado) < TAMANHO_MINIMO_TOKEN_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Área administrativa desativada neste servidor."
        )
    if not x_admin_token or not hmac.compare_digest(
        x_admin_token.encode("utf-8"), esperado.encode("utf-8")
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token administrativo inválido."
        )
    nome = (x_admin_nome or "equipe").strip()[:80] or "equipe"
    return nome
