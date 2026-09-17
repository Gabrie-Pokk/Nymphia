from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth import Gestante
from app.models.interaction import Mensagem
from app.schemas.all_schemas import (
    ConversaEnviarRequest, ConversaResponse, MensagemOut
)
from app.security.jwt_auth import get_current_gestante
from app.services.ai_chat_service import generate_chat_response

router = APIRouter(prefix="/conversa", tags=["Conversa com a IA"])

@router.post("/enviar", response_model=ConversaResponse)
def enviar_mensagem_chat(
    payload: ConversaEnviarRequest,
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """
    Envia mensagem para a assistente Nymphia.
    Urgência tem prioridade sobre conversa: se detectar sinal de emergência,
    responde imediatamente sem aguardar LLM.
    """
    texto = payload.texto.strip()
    if not texto:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mensagem não pode ser vazia")

    # 1. Salva a mensagem da gestante
    msg_gestante = Mensagem(
        gestante_id=gestante.id,
        papel="gestante",
        conteudo=texto,
        data_hora=datetime.utcnow(),
        alerta_emergencia=False,
        autorizado_compartilhar=False
    )
    db.add(msg_gestante)
    db.commit()

    # 2. Gera resposta segura através do serviço clínico
    resposta_texto, is_alerta, fonte = generate_chat_response(texto, recusa_ia=gestante.recusa_ia)

    # 3. Salva a resposta da IA
    msg_ia = Mensagem(
        gestante_id=gestante.id,
        papel="ia",
        conteudo=resposta_texto,
        data_hora=datetime.utcnow(),
        alerta_emergencia=is_alerta,
        autorizado_compartilhar=False
    )
    db.add(msg_ia)
    db.commit()

    return ConversaResponse(
        resposta=resposta_texto,
        alerta_emergencia=is_alerta,
        fonte=fonte
    )

@router.get("/historico", response_model=List[MensagemOut])
def listar_historico_conversa(
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """
    Retorna todo o histórico de mensagens da gestante autenticada.
    Isolamento total: gestante nunca visualiza conversas de outras pacientes.
    """
    mensagens = (
        db.query(Mensagem)
        .filter(Mensagem.gestante_id == gestante.id)
        .order_by(Mensagem.data_hora.asc())
        .all()
    )
    return mensagens

@router.post("/{id}/autorizar-compartilhamento", status_code=status.HTTP_200_OK)
def autorizar_compartilhamento_mensagem(
    id: int,
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """
    Permite à gestante autorizar especificamente que este trecho seja visível ao médico.
    """
    msg = db.query(Mensagem).filter(Mensagem.id == id, Mensagem.gestante_id == gestante.id).first()
    if not msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mensagem não encontrada")
    
    msg.autorizado_compartilhar = True
    db.commit()
    return {"status": "autorizado", "mensagem_id": id}
