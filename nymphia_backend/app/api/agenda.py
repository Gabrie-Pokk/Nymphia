from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth import Gestante, Parceiro
from app.models.interaction import EventoAgenda
from app.schemas.all_schemas import EventoAgendaCreate, EventoAgendaOut
from app.security.jwt_auth import get_current_user_payload

router = APIRouter(prefix="/agenda", tags=["Agenda e Alarmes"])

def get_target_gestante_id(
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
) -> str:
    perfil = payload.get("perfil")
    sub = payload.get("sub")
    if perfil == "gestante":
        return sub
    elif perfil == "parceiro":
        parceiro = db.query(Parceiro).filter_by(id=sub).first()
        if not parceiro:
            raise HTTPException(status_code=401, detail="Parceiro não encontrado")
        from app.api.parceiro import obter_vinculo_parceiro
        vinculo = obter_vinculo_parceiro(parceiro, db)
        return vinculo.gestante_id
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a gestantes e parceiros vinculados"
        )


@router.post("/eventos", response_model=EventoAgendaOut, status_code=status.HTTP_201_CREATED)
def criar_evento_agenda(
    payload: EventoAgendaCreate,
    gestante_id: str = Depends(get_target_gestante_id),
    db: Session = Depends(get_db)
):
    evento = EventoAgenda(
        gestante_id=gestante_id,
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
    gestante_id: str = Depends(get_target_gestante_id),
    db: Session = Depends(get_db)
):
    """
    Lista eventos da gestante ordenados por timestamp real.
    Se apenas_futuros=True, exibe eventos futuros OU alarmes/medicações recorrentes ativas.
    """
    query = db.query(EventoAgenda).filter(EventoAgenda.gestante_id == gestante_id)
    
    if apenas_futuros:
        now = datetime.utcnow()
        query = query.filter(
            or_(
                EventoAgenda.data_hora >= now,
                and_(
                    EventoAgenda.concluido.is_(False),
                    or_(
                        EventoAgenda.recorrencia.isnot(None),
                        EventoAgenda.tipo.in_(["medicacao", "alarme"])
                    )
                )
            )
        )

    # Ordenação por data_hora cronológica ascendente
    eventos = query.order_by(EventoAgenda.data_hora.asc()).all()
    return eventos


@router.patch("/eventos/{id}/concluir", response_model=EventoAgendaOut)
def concluir_evento_agenda(
    id: int,
    gestante_id: str = Depends(get_target_gestante_id),
    db: Session = Depends(get_db)
):
    """
    Marca o evento como concluído (ou desmarca).
    """
    evento = db.query(EventoAgenda).filter(
        EventoAgenda.id == id,
        EventoAgenda.gestante_id == gestante_id
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
    gestante_id: str = Depends(get_target_gestante_id),
    db: Session = Depends(get_db)
):
    """
    Remove evento da agenda.
    """
    evento = db.query(EventoAgenda).filter(
        EventoAgenda.id == id,
        EventoAgenda.gestante_id == gestante_id
    ).first()

    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento de agenda não encontrado"
        )

    db.delete(evento)
    db.commit()
    return None
