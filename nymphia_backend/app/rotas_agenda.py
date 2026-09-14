from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import exigir_gestante
from app.db import get_db
from app.models_agenda import EventoAgenda
from app.schemas import EventoCriar, EventoResposta

router = APIRouter()
TIPOS_VALIDOS = {"consulta", "medicacao", "vacina", "exame", "marco"}


@router.post("/agenda/eventos", response_model=EventoResposta)
def criar_evento(payload: EventoCriar, gestante_id: str = Depends(exigir_gestante), db: Session = Depends(get_db)):
    if payload.tipo not in TIPOS_VALIDOS:
        raise HTTPException(400, f"Tipo inválido. Use um de: {', '.join(TIPOS_VALIDOS)}")
    try:
        data_hora = datetime.fromisoformat(payload.data_hora)
    except ValueError:
        raise HTTPException(400, "data_hora precisa estar em formato ISO 8601, ex: 2026-10-01T09:00:00")

    evento = EventoAgenda(
        gestante_id=gestante_id, tipo=payload.tipo, titulo=payload.titulo,
        data_hora=data_hora, notas=payload.notas,
    )
    db.add(evento)
    db.commit()
    db.refresh(evento)
    return EventoResposta(**evento.as_dict())


@router.get("/agenda/eventos", response_model=list[EventoResposta])
def listar_eventos(
    apenas_futuros: bool = True,
    gestante_id: str = Depends(exigir_gestante),
    db: Session = Depends(get_db),
):
    query = db.query(EventoAgenda).filter(EventoAgenda.gestante_id == gestante_id)
    if apenas_futuros:
        agora = datetime.now(timezone.utc).replace(tzinfo=None)
        query = query.filter(EventoAgenda.data_hora >= agora)
    eventos = query.order_by(EventoAgenda.data_hora.asc()).all()
    return [EventoResposta(**e.as_dict()) for e in eventos]


@router.patch("/agenda/eventos/{evento_id}/concluir", response_model=EventoResposta)
def concluir_evento(evento_id: int, gestante_id: str = Depends(exigir_gestante), db: Session = Depends(get_db)):
    evento = db.query(EventoAgenda).filter(
        EventoAgenda.id == evento_id, EventoAgenda.gestante_id == gestante_id
    ).first()
    if not evento:
        raise HTTPException(404, "Evento não encontrado.")
    evento.concluido = True
    db.commit()
    db.refresh(evento)
    return EventoResposta(**evento.as_dict())


@router.delete("/agenda/eventos/{evento_id}")
def excluir_evento(evento_id: int, gestante_id: str = Depends(exigir_gestante), db: Session = Depends(get_db)):
    evento = db.query(EventoAgenda).filter(
        EventoAgenda.id == evento_id, EventoAgenda.gestante_id == gestante_id
    ).first()
    if not evento:
        raise HTTPException(404, "Evento não encontrado.")
    db.delete(evento)
    db.commit()
    return {"status": "excluído"}
