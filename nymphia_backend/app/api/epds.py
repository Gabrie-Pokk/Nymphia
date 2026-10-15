"""
Triagem emocional (EPDS). Regras e fontes em app/services/epds_service.py.
"""
from datetime import datetime
from typing import Annotated, List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, sessionmaker

from app.database import get_db
from app.models.auth import Gestante
from app.models.clinical import PerfilClinico, TriagemEPDS
from app.schemas.all_schemas import _serialize_datetime_utc
from app.security.jwt_auth import get_current_gestante
from app.services import epds_service
from app.services.notificacao_equipe import avisar_equipe, emails_da_equipe, tem_equipe_vinculada

router = APIRouter(prefix="/epds", tags=["Triagem emocional (EPDS)"])

CONTATOS = [
    {"sigla": "CVV", "nome": "Centro de Valorização da Vida", "telefone": "188", "quando": "para conversar, 24 horas, grátis"},
    {"sigla": "SAMU", "nome": "Serviço de Atendimento Móvel de Urgência", "telefone": "192", "quando": "se você estiver em perigo agora"},
]


class RespostasEPDS(BaseModel):
    # Posição da resposta escolhida em cada pergunta (0 = primeira), da pergunta 1 à 10
    respostas: List[Annotated[int, Field(ge=0, le=3)]] = Field(
        ..., min_length=epds_service.TOTAL_ITENS, max_length=epds_service.TOTAL_ITENS
    )


def _resumo(t: TriagemEPDS) -> dict:
    return {
        "id": t.id,
        "data_hora": _serialize_datetime_utc(t.data_hora),  # UTC com "Z", para o navegador mostrar no fuso local
        "semana_gestacional": t.semana_gestacional,
        "pontuacao": t.pontuacao,
        "nivel": t.nivel,
        "pensamento_de_se_machucar": t.pontos_autolesao > 0,
        "profissional_notificado": bool(t.profissional_notificado),
    }


def resumos_da_gestante(db: Session, gestante_id: str, limite: int = 50) -> List[dict]:
    triagens = (
        db.query(TriagemEPDS)
        .filter(TriagemEPDS.gestante_id == gestante_id)
        .order_by(TriagemEPDS.data_hora.desc())
        .limit(limite)
        .all()
    )
    return [_resumo(t) for t in triagens]


def _semana_atual(db: Session, gestante_id: str):
    perfil = db.query(PerfilClinico).filter(PerfilClinico.gestante_id == gestante_id).first()
    if not perfil or not perfil.dum:
        return None
    return max(0, (datetime.utcnow().date() - perfil.dum).days // 7)


def _avisar_e_registrar(fabrica_de_sessao, triagem_id: int, emails: List[str]) -> None:
    """Roda depois da resposta: envia o e-mail e só então marca como avisado."""
    if not emails or not avisar_equipe(emails, "questionário de bem-estar"):
        return
    db = fabrica_de_sessao()
    try:
        triagem = db.query(TriagemEPDS).filter(TriagemEPDS.id == triagem_id).first()
        if triagem:
            triagem.profissional_notificado = True
            db.commit()
    finally:
        db.close()


@router.get("/status")
def status_triagem(gestante: Gestante = Depends(get_current_gestante), db: Session = Depends(get_db)):
    ultimas = resumos_da_gestante(db, gestante.id, limite=1)
    return {"disponivel": epds_service.disponivel(), "ultima": ultimas[0] if ultimas else None}


@router.get("/questionario")
def obter_questionario(gestante: Gestante = Depends(get_current_gestante)):
    questionario, motivo = epds_service.questionario()
    if questionario is None:
        return {"disponivel": False, "motivo": motivo}
    return {
        "disponivel": True,
        "versao": questionario["versao"],
        "instrucao": questionario["instrucao"],
        "itens": questionario["itens"],  # texto e respostas, sem os pontos
        "aviso": epds_service.AVISO,
        "referencia": epds_service.REFERENCIA,
    }


@router.post("/respostas", status_code=status.HTTP_201_CREATED)
def registrar_respostas(
    payload: RespostasEPDS,
    tarefas: BackgroundTasks,
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db),
):
    questionario, motivo = epds_service.questionario()
    if questionario is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail=f"Questionário indisponível: {motivo}.")

    resultado = epds_service.pontuar(payload.respostas)
    triagem = TriagemEPDS(
        gestante_id=gestante.id,
        data_hora=datetime.utcnow(),
        semana_gestacional=_semana_atual(db, gestante.id),
        respostas=list(payload.respostas),
        pontos_por_item=resultado["pontos_por_item"],
        pontuacao=resultado["pontuacao"],
        pontos_autolesao=resultado["pontos_autolesao"],
        nivel=resultado["nivel"],
        versao_questionario=questionario["versao"][:255],
        profissional_notificado=False,
    )
    db.add(triagem)
    db.commit()
    db.refresh(triagem)

    equipe = tem_equipe_vinculada(db, gestante.id)
    if resultado["nivel"] == "urgente" and equipe:
        fabrica = sessionmaker(bind=db.get_bind(), autocommit=False, autoflush=False)
        tarefas.add_task(_avisar_e_registrar, fabrica, triagem.id, emails_da_equipe(db, gestante.id))

    return {
        **_resumo(triagem),
        "titulo": resultado["titulo"],
        "mensagem": resultado["mensagem"],
        "contatos": CONTATOS if resultado["nivel"] in ("urgente", "atencao") else [],
        "equipe_vinculada": equipe,
        "aviso": epds_service.AVISO,
    }


@router.get("/minhas")
def minhas_triagens(gestante: Gestante = Depends(get_current_gestante), db: Session = Depends(get_db)):
    return resumos_da_gestante(db, gestante.id)
