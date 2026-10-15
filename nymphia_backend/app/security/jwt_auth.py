import bcrypt
import time
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.auth import Gestante, Profissional, Parceiro

security_bearer = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    # Trunca em 72 bytes conforme especificação nativa do algoritmo bcrypt
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Cria um token de SESSÃO. Todo token emitido aqui leva "typ": "access"."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    # iat com fração de segundo: permite revogar sessões emitidas até um instante antes da troca de senha
    to_encode.update({"exp": expire, "iat": round(time.time(), 6), "typ": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.NYMPHIA_SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def _token_invalido() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

def decode_access_token(token: str) -> dict:
    """
    Valida um token de SESSÃO.

    Recusa qualquer token que não seja de sessão: tokens com "tipo_acao"
    (os antigos tokens de redefinição de senha) e tokens cujo "typ" não seja
    "access". Tokens de sessão antigos, emitidos antes do campo "typ", continuam
    aceitos até expirar, para ninguém ser deslogado.
    """
    try:
        payload = jwt.decode(
            token, settings.NYMPHIA_SECRET_KEY, algorithms=[settings.ALGORITHM], leeway=10
        )
    except jwt.PyJWTError:
        raise _token_invalido()

    if "tipo_acao" in payload:
        raise _token_invalido()
    if payload.get("typ", "access") != "access":
        raise _token_invalido()
    if not payload.get("sub") or not payload.get("perfil"):
        raise _token_invalido()
    return payload

def sessao_revogada(usuario, payload: dict) -> bool:
    """
    True quando o token foi emitido antes de usuario.sessoes_validas_desde
    (por exemplo, antes de a pessoa redefinir a senha). Assim, quem roubou
    um token perde o acesso no momento em que a dona da conta troca a senha.
    """
    limite = getattr(usuario, "sessoes_validas_desde", None)
    if not limite:
        return False
    emitido_em = payload.get("iat")
    if emitido_em is None:
        return True
    try:
        return float(emitido_em) < limite.replace(tzinfo=timezone.utc).timestamp()
    except (TypeError, ValueError):
        return True


def get_current_user_payload(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer)
) -> dict:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credencial de autenticação não fornecida",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_access_token(credentials.credentials)

def get_current_gestante(
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
) -> Gestante:
    if payload.get("perfil") != "gestante":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a gestantes"
        )
    gestante_id = payload.get("sub")
    gestante = db.query(Gestante).filter(Gestante.id == gestante_id).first()
    if not gestante:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Gestante não encontrada ou conta removida"
        )
    if sessao_revogada(gestante, payload):
        raise _token_invalido()
    return gestante

def get_current_profissional(
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
) -> Profissional:
    if payload.get("perfil") != "profissional":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a profissionais de saúde"
        )
    profissional_id = payload.get("sub")
    prof = db.query(Profissional).filter(Profissional.id == profissional_id).first()
    if not prof:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Profissional não encontrado"
        )
    if sessao_revogada(prof, payload):
        raise _token_invalido()
    if prof.status_verificacao == "rejeitado":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cadastro profissional rejeitado"
        )
    return prof

def get_current_profissional_aprovado(
    prof: Profissional = Depends(get_current_profissional)
) -> Profissional:
    """
    Só deixa passar profissional com registro conferido pela equipe.
    Profissional pendente consegue entrar no app, mas não vê nem convida paciente.
    """
    if prof.status_verificacao != "aprovado":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seu registro profissional está em conferência pela equipe Nymphia. "
                   "O acesso a pacientes é liberado depois da aprovação."
        )
    return prof

def get_current_parceiro(
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
) -> Parceiro:
    if payload.get("perfil") != "parceiro":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a parceiros"
        )
    parceiro_id = payload.get("sub")
    parceiro = db.query(Parceiro).filter(Parceiro.id == parceiro_id).first()
    if not parceiro:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Parceiro não encontrado"
        )
    if sessao_revogada(parceiro, payload):
        raise _token_invalido()
    return parceiro

_MODELO_POR_PERFIL = {"gestante": Gestante, "profissional": Profissional, "parceiro": Parceiro}


def get_current_any_user(
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
) -> dict:
    """Qualquer perfil logado. Confere se a conta existe e se a sessão não foi revogada."""
    modelo = _MODELO_POR_PERFIL.get(payload.get("perfil"))
    if modelo is None:
        raise _token_invalido()
    usuario = db.query(modelo).filter(modelo.id == payload.get("sub")).first()
    if not usuario or sessao_revogada(usuario, payload):
        raise _token_invalido()
    if modelo is Profissional and usuario.status_verificacao == "rejeitado":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cadastro profissional rejeitado"
        )
    return payload
