import random
import string
from typing import List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth import Gestante, Parceiro
from app.models.clinical import PerfilClinico
from app.models.interaction import EventoAgenda, EventoEmergencia
from app.models.relations import VinculoParceiro, LogAcesso
from app.schemas.all_schemas import ParceiroCodigoConviteOut, ParceiroUsarCodigoRequest, EventoAgendaOut
from app.security.jwt_auth import get_current_gestante, get_current_parceiro

router = APIRouter(prefix="/parceiro", tags=["Modo Parceiro"])

# Armazenamento simples em memória para códigos temporários de parceiro
_parceiro_convites: Dict[str, str] = {}  # codigo -> gestante_id

@router.post("/convite/gerar", response_model=ParceiroCodigoConviteOut)
def gerar_convite_parceiro(
    gestante: Gestante = Depends(get_current_gestante)
):
    chars = string.ascii_uppercase + string.digits
    codigo = "PARC-" + "".join(random.choices(chars, k=5))
    _parceiro_convites[codigo] = gestante.id
    return ParceiroCodigoConviteOut(codigo=codigo)

@router.post("/convite/usar", status_code=status.HTTP_201_CREATED)
def usar_convite_parceiro(
    payload: ParceiroUsarCodigoRequest,
    parceiro: Parceiro = Depends(get_current_parceiro),
    db: Session = Depends(get_db)
):
    codigo = payload.codigo.strip().upper()
    gestante_id = _parceiro_convites.get(codigo)
    if not gestante_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Código de convite inválido ou expirado")

    # Verifica se já existe parceiro ativo para esta gestante
    vinculo_ativo = db.query(VinculoParceiro).filter(
        VinculoParceiro.gestante_id == gestante_id,
        VinculoParceiro.status == "ativo"
    ).first()

    if vinculo_ativo:
        # Apenas um parceiro ativo por vez
        if vinculo_ativo.parceiro_id == parceiro.id:
            return {"status": "ativo", "mensagem": "Você já está vinculado a esta gestante"}
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A gestante já possui um parceiro ativo conectado"
        )

    novo_vinculo = VinculoParceiro(
        gestante_id=gestante_id,
        parceiro_id=parceiro.id,
        status="ativo",
        criado_em=datetime.utcnow()
    )
    db.add(novo_vinculo)
    db.commit()

    # Remove código usado
    _parceiro_convites.pop(codigo, None)

    return {"status": "sucesso", "mensagem": "Vínculo de parceiro estabelecido com sucesso"}

@router.post("/{id}/revogar", status_code=status.HTTP_200_OK)
def revogar_parceiro(
    id: int,
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    vinculo = db.query(VinculoParceiro).filter(
        VinculoParceiro.id == id,
        VinculoParceiro.gestante_id == gestante.id
    ).first()

    if not vinculo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vínculo de parceiro não encontrado")

    vinculo.status = "revogado"
    db.commit()
    return {"status": "revogado", "mensagem": "Vínculo de parceiro revogado imediatamente"}

@router.get("/agenda", response_model=List[EventoAgendaOut])
def listar_agenda_parceiro(
    parceiro: Parceiro = Depends(get_current_parceiro),
    db: Session = Depends(get_db)
):
    """
    Agenda de consultas e exames visível ao parceiro (Apoio logístico).
    Registra auditoria LGPD.
    """
    vinculo = db.query(VinculoParceiro).filter(
        VinculoParceiro.parceiro_id == parceiro.id,
        VinculoParceiro.status == "ativo"
    ).first()

    if not vinculo:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Nenhum vínculo ativo com gestante")

    # Auditoria LGPD
    db.add(LogAcesso(
        gestante_id=vinculo.gestante_id,
        acessado_por_id=parceiro.id,
        acessado_por_tipo="parceiro",
        recurso="agenda_compartilhada",
        data_hora=datetime.utcnow()
    ))
    db.commit()

    return db.query(EventoAgenda).filter(
        EventoAgenda.gestante_id == vinculo.gestante_id,
        EventoAgenda.data_hora >= datetime.utcnow()
    ).order_by(EventoAgenda.data_hora.asc()).all()

@router.get("/marcos")
def obter_marcos_parceiro(
    parceiro: Parceiro = Depends(get_current_parceiro),
    db: Session = Depends(get_db)
):
    """
    Marcos da semana gestacional e guia de apoio ao parceiro.
    """
    vinculo = db.query(VinculoParceiro).filter(
        VinculoParceiro.parceiro_id == parceiro.id,
        VinculoParceiro.status == "ativo"
    ).first()

    if not vinculo:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Nenhum vínculo ativo com gestante")

    perfil = db.query(PerfilClinico).filter(PerfilClinico.gestante_id == vinculo.gestante_id).first()
    semana = 24
    if perfil and perfil.dum:
        dias = (datetime.utcnow().date() - perfil.dum).days
        semana = max(1, dias // 7)

    return {
        "semana_atual": semana,
        "desenvolvimento_bebe": f"O bebê está na {semana}ª semana. Os sentidos estão em pleno desenvolvimento e os movimentos são mais vigorosos.",
        "dica_como_apoiar": "Prepare um lanche nutritivo, incentive momentos de repouso e certifique-se de que a garrafa de água esteja sempre cheia.",
        "preparativos": "Verifique com ela se as vacinas do pré-natal estão em dia e auxilie na organização do transporte para a próxima consulta."
    }

@router.get("/emergencias-ativas")
def obter_emergencias_ativas(
    parceiro: Parceiro = Depends(get_current_parceiro),
    db: Session = Depends(get_db)
):
    """
    Alerta de emergência em tempo real: GRATUITO PARA TODOS OS PLANOS.
    """
    vinculo = db.query(VinculoParceiro).filter(
        VinculoParceiro.parceiro_id == parceiro.id,
        VinculoParceiro.status == "ativo"
    ).first()

    if not vinculo:
        return {"alerta_ativo": False}

    recente = (
        db.query(EventoEmergencia)
        .filter(EventoEmergencia.gestante_id == vinculo.gestante_id)
        .order_by(EventoEmergencia.data_hora.desc())
        .first()
    )

    if recente:
        # Alerta se ocorreu nas últimas 2 horas
        diff_segundos = (datetime.utcnow() - recente.data_hora).total_seconds()
        if diff_segundos < 7200:
            return {
                "alerta_ativo": True,
                "evento_id": recente.id,
                "data_hora": recente.data_hora,
                "maternidade": recente.contexto.get("maternidade_referencia"),
                "telefone_maternidade": recente.contexto.get("maternidade_telefone"),
                "instrucao": "A gestante acionou o botão de emergência SAMU 192. Tente contato e dirija-se à maternidade de referência."
            }

    return {"alerta_ativo": False}
