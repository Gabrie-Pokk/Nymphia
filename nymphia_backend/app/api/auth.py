from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth import Gestante, Profissional, Parceiro
from app.schemas.all_schemas import (
    GestanteRegister, GestanteLogin,
    ProfissionalRegister, ProfissionalLogin,
    ParceiroRegister, ParceiroLogin,
    AuthResponse
)
from app.security.jwt_auth import (
    hash_password, verify_password, create_access_token,
    get_current_profissional
)
from app.storage.object_storage import save_uploaded_file

router = APIRouter(prefix="/auth", tags=["Autenticação"])

# --- GESTANTE ---
@router.post("/gestante/cadastro", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def cadastrar_gestante(payload: GestanteRegister, db: Session = Depends(get_db)):
    existente = db.query(Gestante).filter(Gestante.email == payload.email.lower()).first()
    if existente:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="E-mail já cadastrado no sistema")

    gestante = Gestante(
        nome=payload.nome.strip(),
        email=payload.email.lower(),
        senha_hash=hash_password(payload.senha),
        recusa_ia=payload.recusa_ia
    )
    db.add(gestante)
    db.commit()
    db.refresh(gestante)

    token = create_access_token(data={"sub": gestante.id, "perfil": "gestante"})
    return AuthResponse(
        token=token,
        perfil="gestante",
        id=gestante.id,
        nome=gestante.nome,
        recusa_ia=gestante.recusa_ia
    )

@router.post("/gestante/login", response_model=AuthResponse)
def login_gestante(payload: GestanteLogin, db: Session = Depends(get_db)):
    gestante = db.query(Gestante).filter(Gestante.email == payload.email.lower()).first()
    if not gestante or not verify_password(payload.senha, gestante.senha_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou senha incorretos")

    token = create_access_token(data={"sub": gestante.id, "perfil": "gestante"})
    return AuthResponse(
        token=token,
        perfil="gestante",
        id=gestante.id,
        nome=gestante.nome,
        recusa_ia=gestante.recusa_ia
    )

# --- PROFISSIONAL ---
@router.post("/profissional/cadastro", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def cadastrar_profissional(payload: ProfissionalRegister, db: Session = Depends(get_db)):
    existente = db.query(Profissional).filter(Profissional.email == payload.email.lower()).first()
    if existente:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="E-mail já cadastrado no sistema")

    prof = Profissional(
        nome=payload.nome.strip(),
        email=payload.email.lower(),
        senha_hash=hash_password(payload.senha),
        registro_tipo=payload.registro_tipo.upper(),
        registro_numero=payload.registro_numero.strip(),
        registro_uf=payload.registro_uf.upper(),
        status_verificacao="pendente"
    )
    db.add(prof)
    db.commit()
    db.refresh(prof)

    token = create_access_token(data={"sub": prof.id, "perfil": "profissional"})
    return AuthResponse(
        token=token,
        perfil="profissional",
        id=prof.id,
        nome=prof.nome,
        status_verificacao=prof.status_verificacao
    )

@router.post("/profissional/login", response_model=AuthResponse)
def login_profissional(payload: ProfissionalLogin, db: Session = Depends(get_db)):
    prof = db.query(Profissional).filter(Profissional.email == payload.email.lower()).first()
    if not prof or not verify_password(payload.senha, prof.senha_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou senha incorretos")

    if prof.status_verificacao == "rejeitado":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cadastro profissional rejeitado pela moderação médica"
        )

    token = create_access_token(data={"sub": prof.id, "perfil": "profissional"})
    return AuthResponse(
        token=token,
        perfil="profissional",
        id=prof.id,
        nome=prof.nome,
        status_verificacao=prof.status_verificacao
    )

@router.post("/profissional/upload-documento")
async def upload_documento_profissional(
    arquivo: UploadFile = File(...),
    prof: Profissional = Depends(get_current_profissional),
    db: Session = Depends(get_db)
):
    saved_url = await save_uploaded_file(arquivo, prefix=f"prof_{prof.id}")
    prof.documento_comprovante_path = saved_url
    db.commit()
    return {"status": "documento_recebido", "caminho": saved_url}

# --- PARCEIRO ---
@router.post("/parceiro/cadastro", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def cadastrar_parceiro(payload: ParceiroRegister, db: Session = Depends(get_db)):
    existente = db.query(Parceiro).filter(Parceiro.email == payload.email.lower()).first()
    if existente:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="E-mail já cadastrado no sistema")

    parceiro = Parceiro(
        nome=payload.nome.strip(),
        email=payload.email.lower(),
        senha_hash=hash_password(payload.senha)
    )
    db.add(parceiro)
    db.commit()
    db.refresh(parceiro)

    token = create_access_token(data={"sub": parceiro.id, "perfil": "parceiro"})
    return AuthResponse(
        token=token,
        perfil="parceiro",
        id=parceiro.id,
        nome=parceiro.nome
    )

@router.post("/parceiro/login", response_model=AuthResponse)
def login_parceiro(payload: ParceiroLogin, db: Session = Depends(get_db)):
    parceiro = db.query(Parceiro).filter(Parceiro.email == payload.email.lower()).first()
    if not parceiro or not verify_password(payload.senha, parceiro.senha_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou senha incorretos")

    token = create_access_token(data={"sub": parceiro.id, "perfil": "parceiro"})
    return AuthResponse(
        token=token,
        perfil="parceiro",
        id=parceiro.id,
        nome=parceiro.nome
    )
