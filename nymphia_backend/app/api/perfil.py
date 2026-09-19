import json
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth import Gestante
from app.models.clinical import PerfilClinico, HistoricoFamiliar
from app.models.interaction import QuizGostosGestante
from app.schemas.all_schemas import (
    PerfilClinicoCreate, PerfilClinicoUpdate, PerfilClinicoOut,
    HistoricoFamiliarCreate, HistoricoFamiliarOut
)
from app.security.jwt_auth import get_current_gestante

router = APIRouter(tags=["Perfil Clínico e Onboarding"])

@router.post("/perfil-clinico", response_model=PerfilClinicoOut, status_code=status.HTTP_201_CREATED)
def criar_perfil_clinico(
    payload: PerfilClinicoCreate,
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    existente = db.query(PerfilClinico).filter(PerfilClinico.gestante_id == gestante.id).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Perfil clínico já cadastrado para esta gestante. Utilize PUT para atualizar."
        )

    perfil = PerfilClinico(
        gestante_id=gestante.id,
        idade=payload.idade,
        estado_civil=payload.estado_civil,
        escolaridade=payload.escolaridade,
        gestacoes_anteriores=payload.gestacoes_anteriores,
        partos_normais=payload.partos_normais,
        partos_cesareos=payload.partos_cesareos,
        perdas_gestacionais=payload.perdas_gestacionais,
        dum=payload.dum,
        dpp=payload.dpp,
        dpp_editada_manualmente=payload.dpp_editada_manualmente,
        maternidade_nome=payload.maternidade_nome,
        maternidade_endereco=payload.maternidade_endereco,
        maternidade_telefone=payload.maternidade_telefone,
        maternidade_latitude=payload.maternidade_latitude,
        maternidade_longitude=payload.maternidade_longitude,
        atualizado_em=datetime.utcnow()
    )
    db.add(perfil)
    db.commit()
    db.refresh(perfil)
    return perfil

@router.get("/perfil-clinico", response_model=PerfilClinicoOut)
def obter_perfil_clinico(
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    perfil = db.query(PerfilClinico).filter(PerfilClinico.gestante_id == gestante.id).first()
    if not perfil:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil clínico não preenchido")
    return perfil

@router.put("/perfil-clinico", response_model=PerfilClinicoOut)
def atualizar_perfil_clinico(
    payload: PerfilClinicoUpdate,
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    perfil = db.query(PerfilClinico).filter(PerfilClinico.gestante_id == gestante.id).first()
    if not perfil:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil clínico não encontrado")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(perfil, field, value)
    perfil.atualizado_em = datetime.utcnow()

    db.commit()
    db.refresh(perfil)
    return perfil

# --- HISTÓRICO FAMILIAR ---
@router.post("/historico-familiar", response_model=HistoricoFamiliarOut, status_code=status.HTTP_201_CREATED)
def adicionar_historico_familiar(
    payload: HistoricoFamiliarCreate,
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    item = HistoricoFamiliar(
        gestante_id=gestante.id,
        parente=payload.parente.strip(),
        condicao=payload.condicao.strip()
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.get("/historico-familiar", response_model=List[HistoricoFamiliarOut])
def listar_historico_familiar(
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    return db.query(HistoricoFamiliar).filter(HistoricoFamiliar.gestante_id == gestante.id).all()

@router.delete("/historico-familiar/{id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_historico_familiar(
    id: int,
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    item = db.query(HistoricoFamiliar).filter(
        HistoricoFamiliar.id == id,
        HistoricoFamiliar.gestante_id == gestante.id
    ).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro de histórico não encontrado")
    
    db.delete(item)
    db.commit()
    return None

@router.get("/quiz-gostos")
def obter_quiz_gostos(
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    quiz = db.query(QuizGostosGestante).filter(QuizGostosGestante.gestante_id == gestante.id).first()
    if not quiz:
        return {
            "preenchido": False,
            "respondido_por": None,
            "nome_respondente": None,
            "respostas": {},
            "atualizado_em": None
        }
    try:
        respostas = json.loads(quiz.respostas_json)
    except Exception:
        respostas = {}
    return {
        "preenchido": True,
        "respondido_por": quiz.respondido_por,
        "nome_respondente": quiz.nome_respondente,
        "respostas": respostas,
        "atualizado_em": quiz.atualizado_em
    }

@router.post("/quiz-gostos")
def salvar_quiz_gostos(
    payload: dict,
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    respostas = payload.get("respostas", {})
    respondido_por = payload.get("respondido_por", "gestante")
    nome_respondente = payload.get("nome_respondente") or gestante.nome

    quiz = db.query(QuizGostosGestante).filter(QuizGostosGestante.gestante_id == gestante.id).first()
    if not quiz:
        quiz = QuizGostosGestante(
            gestante_id=gestante.id,
            respondido_por=respondido_por,
            nome_respondente=nome_respondente,
            respostas_json=json.dumps(respostas, ensure_ascii=False),
            atualizado_em=datetime.utcnow()
        )
        db.add(quiz)
    else:
        quiz.respondido_por = respondido_por
        quiz.nome_respondente = nome_respondente
        quiz.respostas_json = json.dumps(respostas, ensure_ascii=False)
        quiz.atualizado_em = datetime.utcnow()

    db.commit()
    return {
        "status": "sucesso",
        "mensagem": "Quiz de gostos e mimos salvo com carinho!",
        "respondido_por": respondido_por,
        "nome_respondente": nome_respondente
    }

