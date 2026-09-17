from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth import Gestante
from app.models.clinical import CheckinRegistro
from app.schemas.all_schemas import (
    CheckinAnalisarRequest, CheckinCreate, CheckinOut
)
from app.security.jwt_auth import get_current_gestante
from app.services.rules_engine import analyze_urgency
from app.services.ai_text_service import classify_text_emotions

router = APIRouter(prefix="/checkin", tags=["Check-in Diário"])

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
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """
    Analisa e persiste o check-in com DATA E HORA DO SERVIDOR (nunca do dispositivo).
    Se houver alerta de urgência física, a resposta destaca a orientação de emergência.
    """
    # 1. Análise determinística de urgência (regras)
    combined_text = f"{payload.descricao or ''} {' '.join(payload.sintomas)}"
    is_urgent, alertas_regras, orientacao_regras = analyze_urgency(combined_text)

    # 2. Análise emocional (BERTimbau / heurística)
    scores_bertimbau, categorias_emocionais = classify_text_emotions(payload.descricao or "")

    # 3. Formatar recomendação
    if is_urgent:
        recomendacao = orientacao_regras
    elif "sintoma_fisico" in categorias_emocionais or len(payload.sintomas) > 0:
        sintomas_txt = ", ".join(payload.sintomas) if payload.sintomas else "desconforto relatado"
        recomendacao = (
            f"Registramos seus sintomas ({sintomas_txt}). Mantenha-se hidratada e em repouso. "
            f"Se a intensidade aumentar ou se surgirem sinais de alerta, contate seu obstetra ou dirija-se à maternidade."
        )
    elif "ansiedade" in categorias_emocionais or "tristeza" in categorias_emocionais:
        recomendacao = (
            "Percebemos que seu dia pode estar exigindo mais de você emocionalmente. Respire fundo, "
            "tome um momento para você e, se desejar, converse com nossa assistente de apoio na aba de Conversa."
        )
    else:
        recomendacao = "Excelente! Seu check-in diário foi concluído com sucesso. Continue cuidando de você e do seu bebê."

    # 4. Gravar com timestamp do SERVIDOR
    novo_checkin = CheckinRegistro(
        gestante_id=gestante.id,
        data_hora=datetime.utcnow(),  # Timestamp garantido pelo servidor
        humor=payload.humor,
        descricao=payload.descricao,
        sintomas=payload.sintomas,
        movimentos_bebe=payload.movimentos_bebe,
        semana_gestacional=payload.semana_gestacional,
        categorias_bertimbau=scores_bertimbau,
        categorias_regras=categorias_emocionais,
        alerta_sintoma_fisico=alertas_regras,
        score_anomalia=0.65 if is_urgent else 0.05
    )
    db.add(novo_checkin)
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
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """
    Retorna histórico ordenado do mais recente para o mais antigo.
    Gestante acessa EXCLUSIVAMENTE os seus próprios check-ins.
    """
    checkins = (
        db.query(CheckinRegistro)
        .filter(CheckinRegistro.gestante_id == gestante.id)
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
