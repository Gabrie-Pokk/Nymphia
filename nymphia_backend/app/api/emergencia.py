from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.all_schemas import EmergenciaNotificarRequest, EmergenciaResponse
from app.security.jwt_auth import get_current_user_payload, security_bearer
from app.services.emergency_service import process_emergency_event
from app.models.interaction import EventoEmergencia

router = APIRouter(prefix="/emergencia", tags=["Sistema de Emergência SAMU 192"])

@router.post("/notificar", response_model=EmergenciaResponse, status_code=status.HTTP_200_OK)
async def notificar_emergencia(
    payload: EmergenciaNotificarRequest,
    db: Session = Depends(get_db),
    credentials = Depends(security_bearer)
):
    """
    Acionamento do fluxo paralelo de emergência.
    1. Ação principal: Discar 192 diretamente (gestante orientada na interface).
    2. Notificação ao profissional disparada em paralelo sem aguardar resposta.
    3. Registro do evento com data/hora do servidor.
    NUNCA bloqueia - responde 200 mesmo se serviços falharem.
    Acessível com ou sem login.
    """
    gestante_id = None
    if credentials:
        try:
            user_data = get_current_user_payload(credentials)
            if user_data.get("perfil") == "gestante":
                gestante_id = user_data.get("sub")
        except Exception:
            pass

    if gestante_id:
        evento = await process_emergency_event(
            gestante_id=gestante_id,
            db=db,
            latitude=payload.latitude,
            longitude=payload.longitude
        )
        return EmergenciaResponse(
            status="emergencia_registrada_em_paralelo",
            evento_id=evento.id,
            data_hora=evento.data_hora,
            profissional_notificado=evento.profissional_notificado,
            orientacao_samu="Ligue 192 (SAMU) imediatamente."
        )
    else:
        # Registro anônimo caso chamada ocorra sem login
        evento = EventoEmergencia(
            gestante_id="anonima_publica",
            data_hora=datetime.utcnow(),
            latitude=payload.latitude,
            longitude=payload.longitude,
            contexto={"origem": "rota_publica_emergencia"},
            profissional_notificado=False
        )
        db.add(evento)
        db.commit()
        db.refresh(evento)

        return EmergenciaResponse(
            status="emergencia_publica_acionada",
            evento_id=evento.id,
            data_hora=evento.data_hora,
            profissional_notificado=False,
            orientacao_samu="Ligue 192 (SAMU) imediatamente."
        )
