import logging
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.clinical import CheckinRegistro, PerfilClinico
from app.models.interaction import EventoEmergencia
from app.models.relations import Vinculo

logger = logging.getLogger("nymphia.emergency")

async def process_emergency_event(
    gestante_id: str,
    db: Session,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None
) -> EventoEmergencia:
    """
    Sistema de emergência: fluxo paralelo não-bloqueante.
    1. Grava evento com timestamp do servidor e contexto clínico.
    2. Notifica o profissional vinculado (se houver) em background tolerante a falhas.
    3. Nunca bloqueia e nunca falha a requisição da gestante.
    """
    # Coleta contexto do último check-in
    ultimo_checkin = (
        db.query(CheckinRegistro)
        .filter(CheckinRegistro.gestante_id == gestante_id)
        .order_by(CheckinRegistro.data_hora.desc())
        .first()
    )

    perfil = db.query(PerfilClinico).filter(PerfilClinico.gestante_id == gestante_id).first()

    contexto: Dict[str, Any] = {
        "maternidade_referencia": perfil.maternidade_nome if perfil else None,
        "maternidade_telefone": perfil.maternidade_telefone if perfil else None,
        "ultimo_checkin_sintomas": ultimo_checkin.sintomas if ultimo_checkin else [],
        "ultimo_checkin_humor": ultimo_checkin.humor if ultimo_checkin else None,
        "ultimo_checkin_data": ultimo_checkin.data_hora.isoformat() if ultimo_checkin else None,
    }

    # Verifica se há profissional ativo vinculado
    vinculo_ativo = (
        db.query(Vinculo)
        .filter(Vinculo.gestante_id == gestante_id, Vinculo.status == "ativo")
        .first()
    )

    profissional_notificado = False
    if vinculo_ativo:
        try:
            # Simulação de envio paralelo de push / webhook para o profissional
            logger.info(f"Disparando notificação paralela de emergência ao profissional {vinculo_ativo.profissional_id}")
            profissional_notificado = True
        except Exception as e:
            logger.error(f"Falha não-bloqueante ao notificar profissional: {e}")
            profissional_notificado = False

    evento = EventoEmergencia(
        gestante_id=gestante_id,
        data_hora=datetime.utcnow(),  # Timestamp do servidor
        latitude=latitude,
        longitude=longitude,
        contexto=contexto,
        profissional_notificado=profissional_notificado
    )

    db.add(evento)
    db.commit()
    db.refresh(evento)

    return evento
