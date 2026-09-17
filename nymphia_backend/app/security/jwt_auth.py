import bcrypt
from datetime import datetime, timedelta
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
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.NYMPHIA_SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.NYMPHIA_SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

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
    if prof.status_verificacao == "rejeitado":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cadastro profissional rejeitado"
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
    return parceiro

def get_current_any_user(
    payload: dict = Depends(get_current_user_payload)
) -> dict:
    return payload
