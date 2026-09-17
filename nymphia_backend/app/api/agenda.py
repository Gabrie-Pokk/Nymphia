from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth import Gestante
from app.models.interaction import EventoAgenda
from app.schemas.all_schemas import EventoAgendaCreate, EventoAgendaOut
from app.security.jwt_auth import get_current_gestante

router = APIRouter(prefix="/agenda", tags=["Agenda e Alarmes"])

@router.post("/eventos", response_model=EventoAgendaOut, status_code=status.HTTP_201_CREATED)
def criar_evento_agenda(
    payload: EventoAgendaCreate,
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    evento = EventoAgenda(
        gestante_id=gestante.id,
        tipo=payload.tipo,
        titulo=payload.titulo.strip(),
        data_hora=payload.data_hora,
        notas=payload.notas,
        concluido=False,
        recorrencia=payload.recorrencia,
        criado_em=datetime.utcnow()
    )
    db.add(evento)
    db.commit()
    db.refresh(evento)
    return evento

@router.get("/eventos", response_model=List[EventoAgendaOut])
def listar_eventos_agenda(
    apenas_futuros: bool = Query(True, description="Filtro padrão: apenas eventos futuros"),
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """
    Lista eventos da gestante ordenados por timestamp real.
    Se apenas_futuros=True, eventos passados são omitidos.
    """
    query = db.query(EventoAgenda).filter(EventoAgenda.gestante_id == gestante.id)
    
    if apenas_futuros:
        now = datetime.utcnow()
        query = query.filter(EventoAgenda.data_hora >= now)

    # Ordenação por data_hora cronológica ascendente
    eventos = query.order_by(EventoAgenda.data_hora.asc()).all()
    return eventos

@router.patch("/eventos/{id}/concluir", response_model=EventoAgendaOut)
def concluir_evento_agenda(
    id: int,
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """
    Marca o evento como concluído. Retorna 404 (nunca 500) se o evento não existir.
    """
    evento = db.query(EventoAgenda).filter(
        EventoAgenda.id == id,
        EventoAgenda.gestante_id == gestante.id
    ).first()

    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento de agenda não encontrado"
        )

    evento.concluido = not evento.concluido  # Toggle
    db.commit()
    db.refresh(evento)
    return evento

@router.delete("/eventos/{id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_evento_agenda(
    id: int,
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """
    Remove evento. Retorna 404 (nunca 500) se o evento não existir.
    """
    evento = db.query(EventoAgenda).filter(
        EventoAgenda.id == id,
        EventoAgenda.gestante_id == gestante.id
    ).first()

    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento de agenda não encontrado"
        )

    db.delete(evento)
    db.commit()
    return None
