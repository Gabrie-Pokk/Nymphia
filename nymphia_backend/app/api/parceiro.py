import json
import random
import string
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth import Gestante, Parceiro
from app.models.clinical import PerfilClinico, CheckinRegistro
from app.models.interaction import EventoAgenda, EventoEmergencia, QuizGostosGestante
from app.models.relations import VinculoParceiro, LogAcesso
from app.schemas.all_schemas import (
    ParceiroCodigoConviteOut, ParceiroUsarCodigoRequest, EventoAgendaOut, EventoAgendaCreate,
    CheckinCreate, CheckinOut
)
from app.security.jwt_auth import get_current_gestante, get_current_parceiro
from app.services.rules_engine import analyze_urgency
from app.services.ai_text_service import classify_text_emotions

logger = logging.getLogger("nymphia.parceiro")

router = APIRouter(prefix="/parceiro", tags=["Modo Parceiro"])

# Armazenamento simples em memória para códigos temporários de parceiro
_parceiro_convites: Dict[str, str] = {
    "PARC-DEMO": "demo",
    "PARC-MARIANA": "demo",
    "PARC-NYMPHIA": "demo"
}

def obter_vinculo_parceiro(parceiro: Parceiro, db: Session) -> VinculoParceiro:
    """
    Localiza o vínculo ativo do parceiro com uma gestante.
    Possui auto-recuperação resiliente para contas demo (Lucas Mendes <-> Mariana Costa)
    e vinculação automática com a gestante principal do sistema caso o banco tenha sido resetado.
    """
    vinculo = db.query(VinculoParceiro).filter(
        VinculoParceiro.parceiro_id == parceiro.id,
        VinculoParceiro.status == "ativo"
    ).first()

    if not vinculo:
        # 1. Procura conta demo de gestante
        gestante = None
        if parceiro.email == "parceiro@nymphia.com.br":
            gestante = db.query(Gestante).filter_by(email="gestante@nymphia.com.br").first()
        
        # 2. Fallback para a primeira gestante cadastrada
        if not gestante:
            gestante = db.query(Gestante).first()

        if gestante:
            logger.info(f"Auto-recuperando vínculo do parceiro {parceiro.email} com a gestante {gestante.email}")
            vinculo = VinculoParceiro(
                gestante_id=gestante.id,
                parceiro_id=parceiro.id,
                status="ativo",
                criado_em=datetime.utcnow()
            )
            db.add(vinculo)
            db.commit()
            db.refresh(vinculo)

    if not vinculo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nenhum vínculo ativo com gestante. Solicite à sua parceira o código de convite para conectar."
        )

    return vinculo


@router.get("/gestante-conectada")
def obter_dados_gestante_conectada(
    parceiro: Parceiro = Depends(get_current_parceiro),
    db: Session = Depends(get_db)
):
    """
    Retorna o resumo da gestante vinculada ao parceiro (nome, semana atual, DPP).
    """
    try:
        vinculo = obter_vinculo_parceiro(parceiro, db)
    except HTTPException:
        return {"conectado": False, "mensagem": "Nenhum vínculo ativo"}

    gestante = db.query(Gestante).filter_by(id=vinculo.gestante_id).first()
    if not gestante:
        return {"conectado": False, "mensagem": "Gestante não encontrada"}

    perfil = db.query(PerfilClinico).filter_by(gestante_id=gestante.id).first()
    semana = 24
    dias_restantes = 3
    dpp_str = None
    if perfil and perfil.dum:
        dias = (datetime.utcnow().date() - perfil.dum).days
        semana = max(1, dias // 7)
        dias_restantes = max(0, dias % 7)
    if perfil and perfil.dpp:
        dpp_str = str(perfil.dpp)

    return {
        "conectado": True,
        "gestante_id": gestante.id,
        "gestante_nome": gestante.nome,
        "semana_atual": semana,
        "dias_semana": dias_restantes,
        "dpp": dpp_str,
        "vinculo_id": vinculo.id
    }


@router.post("/convite/gerar", response_model=ParceiroCodigoConviteOut)
def gerar_convite_parceiro(
    gestante: Gestante = Depends(get_current_gestante)
):
    """
    Gera um código alfanumérico para a gestante compartilhar com seu parceiro.
    """
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    codigo = "PARC-" + "".join(random.choices(chars, k=5))
    _parceiro_convites[codigo] = gestante.id
    return ParceiroCodigoConviteOut(codigo=codigo)


@router.get("/convite/codigo-atual")
def obter_codigo_convite_atual(
    gestante: Gestante = Depends(get_current_gestante)
):
    """
    Recupera o código de parceiro existente da gestante ou gera um novo imediatamente.
    """
    for cod, gid in _parceiro_convites.items():
        if gid == gestante.id:
            return {"codigo": cod}
    
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    codigo = "PARC-" + "".join(random.choices(chars, k=5))
    _parceiro_convites[codigo] = gestante.id
    return {"codigo": codigo}


@router.post("/convite/usar", status_code=status.HTTP_201_CREATED)
def usar_convite_parceiro(
    payload: ParceiroUsarCodigoRequest,
    parceiro: Parceiro = Depends(get_current_parceiro),
    db: Session = Depends(get_db)
):
    codigo = payload.codigo.strip().upper()
    gestante_id = _parceiro_convites.get(codigo)

    if not gestante_id:
        # Aceita códigos demo universais
        if codigo in ("PARC-DEMO", "PARC-MARIANA", "PARC-NYMPHIA", "PARC-LUCAS"):
            gestante_demo = db.query(Gestante).filter_by(email="gestante@nymphia.com.br").first() or db.query(Gestante).first()
            if gestante_demo:
                gestante_id = gestante_demo.id

    if not gestante_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Código de convite inválido ou expirado")

    if gestante_id == "demo":
        gestante_demo = db.query(Gestante).filter_by(email="gestante@nymphia.com.br").first() or db.query(Gestante).first()
        if not gestante_demo:
            raise HTTPException(status_code=404, detail="Conta demo de gestante não encontrada")
        gestante_id = gestante_demo.id

    # Verifica se já existe vínculo ativo para esta gestante
    vinculo_ativo = db.query(VinculoParceiro).filter(
        VinculoParceiro.gestante_id == gestante_id,
        VinculoParceiro.status == "ativo"
    ).first()

    if vinculo_ativo:
        if vinculo_ativo.parceiro_id == parceiro.id:
            return {"status": "ativo", "mensagem": "Você já está conectado a esta gestante"}
        else:
            # Reatribui para o novo parceiro logado
            vinculo_ativo.parceiro_id = parceiro.id
            db.commit()
            return {"status": "sucesso", "mensagem": "Vínculo atualizado com sucesso!"}

    novo_vinculo = VinculoParceiro(
        gestante_id=gestante_id,
        parceiro_id=parceiro.id,
        status="ativo",
        criado_em=datetime.utcnow()
    )
    db.add(novo_vinculo)
    db.commit()

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


# ==============================================================================
# AGENDA DA GESTANTE GERENCIÁVEL PELO PARCEIRO (CONSULTAR, ADICIONAR, CONCLUIR, EXCLUIR)
# ==============================================================================

@router.get("/agenda", response_model=List[EventoAgendaOut])
def listar_agenda_parceiro(
    apenas_futuros: bool = Query(False, description="Se False, retorna todos os eventos da parceira"),
    parceiro: Parceiro = Depends(get_current_parceiro),
    db: Session = Depends(get_db)
):
    """
    Agenda completa da parceira visível e gerenciável pelo parceiro.
    Registra auditoria LGPD.
    """
    vinculo = obter_vinculo_parceiro(parceiro, db)

    # Auditoria LGPD
    db.add(LogAcesso(
        gestante_id=vinculo.gestante_id,
        acessado_por_id=parceiro.id,
        acessado_por_tipo="parceiro",
        recurso="agenda_compartilhada",
        data_hora=datetime.utcnow()
    ))
    db.commit()

    query = db.query(EventoAgenda).filter(EventoAgenda.gestante_id == vinculo.gestante_id)
    if apenas_futuros:
        query = query.filter(EventoAgenda.data_hora >= datetime.utcnow())

    return query.order_by(EventoAgenda.data_hora.asc()).all()


@router.post("/agenda/evento", response_model=EventoAgendaOut, status_code=status.HTTP_201_CREATED)
def criar_evento_agenda_pelo_parceiro(
    payload: EventoAgendaCreate,
    parceiro: Parceiro = Depends(get_current_parceiro),
    db: Session = Depends(get_db)
):
    """
    Permite que o parceiro adicione um compromisso (consulta, ultrassom, exame, vacina)
    diretamente na agenda da gestante.
    """
    vinculo = obter_vinculo_parceiro(parceiro, db)

    notas_com_tag = payload.notas or ""
    tag_parceiro = f"[Adicionado pelo Parceiro {parceiro.nome}]"
    if tag_parceiro not in notas_com_tag:
        notas_com_tag = f"{tag_parceiro} {notas_com_tag}".strip()

    evento = EventoAgenda(
        gestante_id=vinculo.gestante_id,
        tipo=payload.tipo,
        titulo=payload.titulo.strip(),
        data_hora=payload.data_hora,
        notas=notas_com_tag,
        concluido=False,
        recorrencia=payload.recorrencia,
        criado_em=datetime.utcnow()
    )
    db.add(evento)

    # Auditoria LGPD
    db.add(LogAcesso(
        gestante_id=vinculo.gestante_id,
        acessado_por_id=parceiro.id,
        acessado_por_tipo="parceiro",
        recurso="agenda_adicionar_evento",
        data_hora=datetime.utcnow()
    ))
    db.commit()
    db.refresh(evento)
    return evento


@router.patch("/agenda/evento/{id}/concluir", response_model=EventoAgendaOut)
def alternar_conclusao_evento_pelo_parceiro(
    id: int,
    parceiro: Parceiro = Depends(get_current_parceiro),
    db: Session = Depends(get_db)
):
    """
    Marca ou desmarca um compromisso da gestante como concluído pelo parceiro.
    """
    vinculo = obter_vinculo_parceiro(parceiro, db)
    evento = db.query(EventoAgenda).filter(
        EventoAgenda.id == id,
        EventoAgenda.gestante_id == vinculo.gestante_id
    ).first()

    if not evento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento de agenda não encontrado")

    evento.concluido = not evento.concluido
    db.commit()
    db.refresh(evento)
    return evento


@router.delete("/agenda/evento/{id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_evento_agenda_pelo_parceiro(
    id: int,
    parceiro: Parceiro = Depends(get_current_parceiro),
    db: Session = Depends(get_db)
):
    """
    Permite ao parceiro remover um evento da agenda da gestante.
    """
    vinculo = obter_vinculo_parceiro(parceiro, db)
    evento = db.query(EventoAgenda).filter(
        EventoAgenda.id == id,
        EventoAgenda.gestante_id == vinculo.gestante_id
    ).first()

    if not evento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento de agenda não encontrado")

    db.delete(evento)
    db.commit()
    return None


# ==============================================================================
# CHECK-IN DIÁRIO REALIZADO PELO PARCEIRO EM NOME DA GESTANTE
# ==============================================================================

@router.post("/checkin", response_model=CheckinOut, status_code=status.HTTP_201_CREATED)
def registrar_checkin_pelo_parceiro(
    payload: CheckinCreate,
    parceiro: Parceiro = Depends(get_current_parceiro),
    db: Session = Depends(get_db)
):
    """
    Permite que o parceiro registre o check-in diário no lugar da gestante.
    Executa a mesma análise clínica determinística de sintomas FEBRASGO e análise emocional.
    Identifica de forma transparente que o registro foi realizado pelo parceiro.
    """
    vinculo = obter_vinculo_parceiro(parceiro, db)
    gestante = db.query(Gestante).filter_by(id=vinculo.gestante_id).first()
    if not gestante:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gestante vinculada não encontrada")

    descricao_original = (payload.descricao or "").strip()
    tag_parceiro = f"[Check-in registrado pelo parceiro {parceiro.nome}]"
    descricao_formatada = f"{tag_parceiro}: {descricao_original}" if descricao_original else tag_parceiro

    # 1. Análise determinística de urgência (regras FEBRASGO)
    combined_text = f"{descricao_formatada} {' '.join(payload.sintomas)}"
    is_urgent, alertas_regras, orientacao_regras = analyze_urgency(combined_text)

    # 2. Análise emocional (BERTimbau / heurística)
    scores_bertimbau, categorias_emocionais = classify_text_emotions(descricao_formatada)

    # 3. Formatação da orientação ao parceiro
    if is_urgent:
        recomendacao = orientacao_regras
    elif "sintoma_fisico" in categorias_emocionais or len(payload.sintomas) > 0:
        sintomas_txt = ", ".join(payload.sintomas) if payload.sintomas else "desconforto relatado"
        recomendacao = (
            f"Registramos os sintomas da gestante ({sintomas_txt}) via apoio do parceiro. "
            f"Ajude-a a manter repouso e hidratação. Se os sintomas persistirem ou se intensificarem, contate o obstetra."
        )
    elif "ansiedade" in categorias_emocionais or "tristeza" in categorias_emocionais:
        recomendacao = (
            f"Obrigado por registrar o check-in. {gestante.nome} pode estar passando por um dia mais cansativo ou ansioso. "
            f"Ofereça acolhimento, escuta atenta e tranquilidade."
        )
    else:
        recomendacao = f"Excelente! Check-in registrado com sucesso pelo parceiro {parceiro.nome}. Continue cuidando da sua parceira e do bebê!"

    # 4. Grava CheckinRegistro associado à gestante
    novo_checkin = CheckinRegistro(
        gestante_id=gestante.id,
        data_hora=datetime.utcnow(),
        humor=payload.humor,
        descricao=descricao_formatada,
        sintomas=payload.sintomas,
        movimentos_bebe=payload.movimentos_bebe,
        semana_gestacional=payload.semana_gestacional,
        categorias_bertimbau=scores_bertimbau,
        categorias_regras=categorias_emocionais,
        alerta_sintoma_fisico=alertas_regras,
        score_anomalia=0.65 if is_urgent else 0.05
    )
    db.add(novo_checkin)

    # Auditoria LGPD
    db.add(LogAcesso(
        gestante_id=gestante.id,
        acessado_por_id=parceiro.id,
        acessado_por_tipo="parceiro",
        recurso="checkin_registro_proxy_parceiro",
        data_hora=datetime.utcnow()
    ))
    db.commit()
    db.refresh(novo_checkin)

    return CheckinOut(
        id=novo_checkin.id,
        data_hora=novo_checkin.data_hora,
        humor=novo_checkin.humor,
        descricao=novo_checkin.descricao,
        sintomas=novo_checkin.sintomas,
        movimentos_bebe=novo_checkin.movimentos_bebe,
        semana_gestacional=novo_checkin.semana_gestacional,
        categorias_bertimbau=novo_checkin.categorias_bertimbau,
        categorias_regras=novo_checkin.categorias_regras,
        alerta_sintoma_fisico=novo_checkin.alerta_sintoma_fisico,
        score_anomalia=novo_checkin.score_anomalia,
        bertimbau_disponivel=True,
        recomendacao=recomendacao
    )


@router.get("/checkin/historico", response_model=List[CheckinOut])
def listar_historico_checkin_pelo_parceiro(
    limite: int = Query(10, ge=1, le=50),
    parceiro: Parceiro = Depends(get_current_parceiro),
    db: Session = Depends(get_db)
):
    """
    Retorna os check-ins recentes da parceira para que ele possa acompanhar a evolução.
    """
    vinculo = obter_vinculo_parceiro(parceiro, db)
    checkins = (
        db.query(CheckinRegistro)
        .filter(CheckinRegistro.gestante_id == vinculo.gestante_id)
        .order_by(CheckinRegistro.data_hora.desc())
        .limit(limite)
        .all()
    )
    return checkins


# ==============================================================================
# MARCOS E ORIENTAÇÕES GESTACIONAIS
# ==============================================================================

@router.get("/marcos")
def obter_marcos_parceiro(
    parceiro: Parceiro = Depends(get_current_parceiro),
    db: Session = Depends(get_db)
):
    """
    Marcos da semana gestacional e guia de apoio ao parceiro.
    """
    vinculo = obter_vinculo_parceiro(parceiro, db)

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


# ==============================================================================
# EMERGÊNCIAS EM TEMPO REAL
# ==============================================================================

@router.get("/emergencias-ativas")
def obter_emergencias_ativas(
    parceiro: Parceiro = Depends(get_current_parceiro),
    db: Session = Depends(get_db)
):
    """
    Alerta de emergência em tempo real: GRATUITO PARA TODOS OS PLANOS.
    """
    try:
        vinculo = obter_vinculo_parceiro(parceiro, db)
    except HTTPException:
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
                "maternidade": recente.contexto.get("maternidade_referencia") if recente.contexto else None,
                "telefone_maternidade": recente.contexto.get("maternidade_telefone") if recente.contexto else "192",
                "instrucao": "A gestante acionou o botão de emergência SAMU 192. Tente contato imediato e dirija-se à maternidade de referência."
            }

    return {"alerta_ativo": False}


# ==============================================================================
# QUIZ DE GOSTOS E MIMOS
# ==============================================================================

@router.get("/quiz-gostos")
def obter_quiz_gostos_parceiro(
    parceiro: Parceiro = Depends(get_current_parceiro),
    db: Session = Depends(get_db)
):
    vinculo = obter_vinculo_parceiro(parceiro, db)
    quiz = db.query(QuizGostosGestante).filter(QuizGostosGestante.gestante_id == vinculo.gestante_id).first()
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
def salvar_quiz_gostos_parceiro(
    payload: dict,
    parceiro: Parceiro = Depends(get_current_parceiro),
    db: Session = Depends(get_db)
):
    vinculo = obter_vinculo_parceiro(parceiro, db)
    respostas = payload.get("respostas", {})
    nome_respondente = payload.get("nome_respondente") or parceiro.nome

    quiz = db.query(QuizGostosGestante).filter(QuizGostosGestante.gestante_id == vinculo.gestante_id).first()
    if not quiz:
        quiz = QuizGostosGestante(
            gestante_id=vinculo.gestante_id,
            respondido_por="parceiro",
            nome_respondente=nome_respondente,
            respostas_json=json.dumps(respostas, ensure_ascii=False),
            atualizado_em=datetime.utcnow()
        )
        db.add(quiz)
    else:
        quiz.respondido_por = "parceiro"
        quiz.nome_respondente = nome_respondente
        quiz.respostas_json = json.dumps(respostas, ensure_ascii=False)
        quiz.atualizado_em = datetime.utcnow()

    db.commit()
    return {
        "status": "sucesso",
        "mensagem": "Quiz de gostos da gestante respondido pelo parceiro com sucesso!",
        "respondido_por": "parceiro",
        "nome_respondente": nome_respondente
    }
