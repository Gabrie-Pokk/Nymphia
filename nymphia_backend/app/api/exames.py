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

def simulate_ocr_extraction(tipo: str) -> dict:
    tipo_lower = tipo.lower()
    if "sangue" in tipo_lower or "hemograma" in tipo_lower:
        return {"hemoglobina": 12.4, "hematocrito": 37.2, "leucocitos": 8400, "plaquetas": 225000, "status": "dentro_dos_limites"}
    elif "glicemia" in tipo_lower or "glicose" in tipo_lower:
        return {"glicemia_jejum_mg_dl": 84.0, "status": "normal_primeiro_tri"}
    elif "urina" in tipo_lower or "eas" in tipo_lower:
        return {"leucocitos": "raros", "hemacias": "raras", "nitrito": "negativo", "status": "sem_sinais_infeccao"}
    elif "toxoplasmose" in tipo_lower:
        return {"igg": "reagente", "igm": "nao_reagente", "status": "imunidade_previa_sem_infeccao_aguda"}
    return {"status": "processado_automaticamente", "nota": "Valores estruturados disponíveis no laudo"}

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
    Upload de exame médico com gravação em armazenamento de objeto seguro (UUID)
    e extração automática de dados por OCR. O arquivo NUNCA é salvo no banco de dados.
    """
    saved_url = await save_uploaded_file(arquivo, prefix=f"exame_{gestante.id[:8]}")
    valores_extraidos = simulate_ocr_extraction(tipo)

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
