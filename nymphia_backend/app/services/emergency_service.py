import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.clinical import CheckinRegistro, PerfilClinico
from app.models.interaction import EventoEmergencia
from app.models.relations import Vinculo
from app.services.notificacao_equipe import avisar_equipe, emails_da_equipe

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

    # Até 15/10/2026 aqui só havia um log e o evento era gravado como "profissional
    # notificado", e a tela dizia à gestante que a equipe tinha sido avisada sem
    # nada ter sido enviado. Agora só conta como avisado o e-mail aceito pelo
    # servidor; sem SMTP configurado, fica False e a tela diz isso.
    contexto["equipe_vinculada"] = vinculo_ativo is not None
    profissional_notificado = False
    if vinculo_ativo:
        try:
            profissional_notificado = await asyncio.wait_for(
                asyncio.to_thread(avisar_equipe, emails_da_equipe(db, gestante_id), "botão de emergência"),
                timeout=8,
            )
        except Exception as e:  # inclui o tempo esgotado: a resposta não espera mais que isso
            logger.error(f"Falha não-bloqueante ao avisar a equipe: {e}")
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
