from typing import List, Optional, Tuple
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth import Gestante, Parceiro
from app.models.clinical import CheckinRegistro
from app.models.relations import LogAcesso
from app.schemas.all_schemas import (
    CheckinAnalisarRequest, CheckinCreate, CheckinOut
)
from app.security.jwt_auth import get_current_user_payload
from app.services.rules_engine import analyze_urgency
from app.services.ai_text_service import classify_text_emotions

router = APIRouter(prefix="/checkin", tags=["Check-in Diário"])

def get_checkin_user_context(
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Retorna (gestante_id, parceiro_id, nome_parceiro) permitindo que tanto
    a gestante quanto o parceiro vinculado possam registrar o check-in.
    """
    perfil = payload.get("perfil")
    sub = payload.get("sub")

    if perfil == "gestante":
        return (sub, None, None)
    elif perfil == "parceiro":
        parceiro = db.query(Parceiro).filter_by(id=sub).first()
        if not parceiro:
            raise HTTPException(status_code=401, detail="Parceiro não encontrado")
        from app.api.parceiro import obter_vinculo_parceiro
        vinculo = obter_vinculo_parceiro(parceiro, db)
        return (vinculo.gestante_id, parceiro.id, parceiro.nome)
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a gestantes e parceiros vinculados"
        )


@router.post("/analisar")
def analisar_checkin_preview(payload: CheckinAnalisarRequest):
    """
    Analisa texto sem persistir (para pré-visualização em tempo real na interface).
    """
    is_urgent, alertas_urgencia, orientacao_urgencia = analyze_urgency(payload.texto)
    scores, categorias_emocionais = classify_text_emotions(payload.texto)
    return {
        "is_urgente": is_urgent,
        "alertas_urgencia": alertas_urgencia,
        "orientacao_urgencia": orientacao_urgencia,
        "categorias_emocionais": categorias_emocionais,
        "scores_bertimbau": scores
    }

@router.post("/registrar", response_model=CheckinOut, status_code=status.HTTP_201_CREATED)
def registrar_checkin(
    payload: CheckinCreate,
    ctx: Tuple[str, Optional[str], Optional[str]] = Depends(get_checkin_user_context),
    db: Session = Depends(get_db)
):
    """
    Analisa e persiste o check-in com DATA E HORA DO SERVIDOR (nunca do dispositivo).
    Suporta registro direto pela gestante ou em nome dela pelo parceiro vinculado.
    Se houver alerta de urgência física, a resposta destaca a orientação de emergência.
    """
    gestante_id, parceiro_id, parceiro_nome = ctx

    descricao_texto = (payload.descricao or "").strip()
    if parceiro_nome:
        tag_parceiro = f"[Check-in registrado pelo parceiro {parceiro_nome}]"
        if tag_parceiro not in descricao_texto:
            descricao_texto = f"{tag_parceiro}: {descricao_texto}" if descricao_texto else tag_parceiro

    # 1. Análise determinística de urgência (regras FEBRASGO)
    combined_text = f"{descricao_texto} {' '.join(payload.sintomas)}"
    is_urgent, alertas_regras, orientacao_regras = analyze_urgency(combined_text)

    # 2. Análise emocional (BERTimbau / heurística)
    scores_bertimbau, categorias_emocionais = classify_text_emotions(descricao_texto)

    # 3. Formatar recomendação
    if is_urgent:
        recomendacao = orientacao_regras
    elif "sintoma_fisico" in categorias_emocionais or len(payload.sintomas) > 0:
        sintomas_txt = ", ".join(payload.sintomas) if payload.sintomas else "desconforto relatado"
        recomendacao = (
            f"Registramos os sintomas ({sintomas_txt}). Mantenha-se hidratada e em repouso. "
            f"Se a intensidade aumentar ou se surgirem sinais de alerta, contate seu obstetra ou dirija-se à maternidade."
        )
    elif "ansiedade" in categorias_emocionais or "tristeza" in categorias_emocionais:
        recomendacao = (
            "Percebemos que o dia de hoje pode estar exigindo mais emocionalmente. "
            "Respire fundo, tire momentos de descanso e compartilhe com sua rede de apoio."
        )
    else:
        autor = f"pelo parceiro {parceiro_nome}" if parceiro_nome else "com sucesso"
        recomendacao = f"Excelente! Check-in diário concluído {autor}. Continue cuidando da saúde e do bebê."

    # 4. Gravar com timestamp do SERVIDOR
    novo_checkin = CheckinRegistro(
        gestante_id=gestante_id,
        data_hora=datetime.utcnow(),  # Timestamp garantido pelo servidor
        humor=payload.humor,
        descricao=descricao_texto,
        sintomas=payload.sintomas,
        movimentos_bebe=payload.movimentos_bebe,
        semana_gestacional=payload.semana_gestacional,
        categorias_bertimbau=scores_bertimbau,
        categorias_regras=categorias_emocionais,
        alerta_sintoma_fisico=alertas_regras,
        score_anomalia=0.65 if is_urgent else 0.05
    )
    db.add(novo_checkin)

    if parceiro_id:
        db.add(LogAcesso(
            gestante_id=gestante_id,
            acessado_por_id=parceiro_id,
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

@router.get("/historico", response_model=List[CheckinOut])
def listar_historico_checkin(
    limite: int = Query(90, ge=1, le=365),
    ctx: Tuple[str, Optional[str], Optional[str]] = Depends(get_checkin_user_context),
    db: Session = Depends(get_db)
):
    """
    Retorna histórico ordenado do mais recente para o mais antigo.
    Gestante e seu parceiro vinculado acessam os check-ins da gestante.
    """
    gestante_id, _, _ = ctx
    checkins = (
        db.query(CheckinRegistro)
        .filter(CheckinRegistro.gestante_id == gestante_id)
        .order_by(CheckinRegistro.data_hora.desc())
        .limit(limite)
        .all()
    )
    
    out: List[CheckinOut] = []
    for c in checkins:
        out.append(CheckinOut(
            id=c.id,
            data_hora=c.data_hora,
            humor=c.humor,
            descricao=c.descricao,
            sintomas=c.sintomas or [],
            movimentos_bebe=c.movimentos_bebe,
            semana_gestacional=c.semana_gestacional,
            categorias_bertimbau=c.categorias_bertimbau,
            categorias_regras=c.categorias_regras or [],
            alerta_sintoma_fisico=c.alerta_sintoma_fisico or [],
            score_anomalia=c.score_anomalia,
            bertimbau_disponivel=True,
            recomendacao="Registro histórico salvo."
        ))
    return out
