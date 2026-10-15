from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth import Gestante, Profissional
from app.models.clinical import Exame
from app.models.relations import Vinculo, LogAcesso
from app.schemas.all_schemas import ExameOut
from app.security.jwt_auth import get_current_gestante, get_current_any_user
from app.storage.object_storage import save_uploaded_file

router = APIRouter(prefix="/exames", tags=["Exames e Laudos"])

# Até 15/10/2026 havia aqui uma função "simulate_ocr_extraction" que devolvia
# resultados INVENTADOS conforme o nome do exame (ex.: toda glicemia virava
# 84 mg/dL "normal"). Esses números apareciam na tela como se tivessem sido
# lidos do laudo e alimentavam o guia nutricional. Isso foi removido: até
# existir leitura automática validada, nenhum valor é extraído do arquivo.

@router.post("/upload", response_model=ExameOut, status_code=status.HTTP_201_CREATED)
async def upload_exame(
    tipo: str = Form(...),
    data_realizacao: date = Form(...),
    observacoes: Optional[str] = Form(None),
    arquivo: UploadFile = File(...),
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """
    Upload de exame com gravação em armazenamento protegido (nome aleatório).
    O arquivo NUNCA é salvo no banco. Não há leitura automática dos valores.
    """
    saved_url = await save_uploaded_file(arquivo, prefix=f"exame_{gestante.id[:8]}")
    valores_extraidos = None

    novo_exame = Exame(
        gestante_id=gestante.id,
        tipo=tipo.strip(),
        data_realizacao=data_realizacao,
        arquivo_url=saved_url,
        valores_extraidos=valores_extraidos,
        observacoes=observacoes,
        criado_em=datetime.utcnow()
    )
    db.add(novo_exame)
    db.commit()
    db.refresh(novo_exame)
    return novo_exame

@router.get("", response_model=List[ExameOut])
def listar_meus_exames(
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    return db.query(Exame).filter(Exame.gestante_id == gestante.id).order_by(Exame.data_realizacao.desc()).all()

@router.get("/{id}", response_model=ExameOut)
def obter_exame_por_id(
    id: int,
    user_payload: dict = Depends(get_current_any_user),
    db: Session = Depends(get_db)
):
    exame = db.query(Exame).filter(Exame.id == id).first()
    if not exame:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exame não encontrado")

    user_id = user_payload.get("sub")
    perfil = user_payload.get("perfil")

    if perfil == "gestante":
        if exame.gestante_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado a exame de outra gestante")
    elif perfil == "profissional":
        prof = db.query(Profissional).filter(Profissional.id == user_id).first()
        if not prof or prof.status_verificacao != "aprovado":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seu registro profissional está em conferência pela equipe Nymphia. "
                       "O acesso a pacientes é liberado depois da aprovação."
            )
        vinculo = db.query(Vinculo).filter(
            Vinculo.profissional_id == user_id,
            Vinculo.gestante_id == exame.gestante_id,
            Vinculo.status == "ativo"
        ).first()
        if not vinculo:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem vínculo ativo com a gestante")
        
        # Auditoria LGPD
        db.add(LogAcesso(
            gestante_id=exame.gestante_id,
            acessado_por_id=user_id,
            acessado_por_tipo="profissional",
            recurso=f"exame_{exame.id}_{exame.tipo}",
            data_hora=datetime.utcnow()
        ))
        db.commit()
    else:
        # Parceiro NUNCA acessa exames
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Parceiro não possui permissão para acessar exames clínicos")

    return exame
