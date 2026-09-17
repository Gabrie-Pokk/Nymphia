import re
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth import Gestante
from app.models.community import PostComunidade, ComentarioComunidade
from app.schemas.all_schemas import PostCreate, PostOut, ComentarioCreate, ComentarioOut
from app.security.jwt_auth import get_current_gestante
from app.services.rules_engine import analyze_urgency

router = APIRouter(prefix="/comunidade", tags=["Comunidade Segura"])

COMMUNITY_GROUPS = [
    "Primeiro Trimestre",
    "Segundo Trimestre",
    "Terceiro Trimestre",
    "Mães de Primeira Viagem",
    "Parto Humanizado",
    "Amamentação & Cuidados",
    "Tentantes & Histórico de Perdas"
]

CLINICAL_DISCUSS_PATTERNS = [
    r"(toma.*(mg|gotas|comprimido|remedio|medicamento))",
    r"(dosagem|dose de)",
    r"(voce.*tem|certeza que e|diagnostico)",
    r"(resultado.*exame.*deu|leucocitos altos|glicemia alta)"
]

def check_moderation(text: str) -> tuple[bool, Optional[str], bool]:
    """
    Moderação em três camadas:
    1. Detector de sofrimento severo/urgência
    2. Detecção de troca de informações clínicas/prescrições
    """
    is_urgent, alerts, _ = analyze_urgency(text)
    if is_urgent:
        return True, f"Sinal de urgência médica detectado ({', '.join(alerts)})", False

    # Verifica sugestão medicamentosa ou diagnóstico entre usuárias
    for pattern in CLINICAL_DISCUSS_PATTERNS:
        if re.search(pattern, text.lower()):
            return False, "Aviso de troca de orientação clínica entre usuárias", True

    return False, None, False

@router.get("/grupos", response_model=List[str])
def listar_grupos():
    return COMMUNITY_GROUPS

@router.get("/posts", response_model=List[PostOut])
def listar_posts(
    grupo: Optional[str] = None,
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    query = db.query(PostComunidade)
    if grupo:
        query = query.filter(PostComunidade.grupo == grupo)
    
    posts = query.order_by(PostComunidade.criado_em.desc()).limit(50).all()
    out: List[PostOut] = []
    for p in posts:
        comentarios_out = [
            ComentarioOut(
                id=c.id,
                post_id=c.post_id,
                apelido=c.apelido,
                conteudo=c.conteudo,
                sinalizado=c.sinalizado,
                criado_em=c.criado_em
            ) for c in p.comentarios
        ]
        out.append(PostOut(
            id=p.id,
            apelido=p.apelido,
            grupo=p.grupo,
            conteudo=p.conteudo,
            sinalizado=p.sinalizado,
            criado_em=p.criado_em,
            comentarios=comentarios_out
        ))
    return out

@router.post("/posts", response_model=PostOut, status_code=status.HTTP_201_CREATED)
def criar_post(
    payload: PostCreate,
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    sinalizado, motivo, requer_aviso_clinico = check_moderation(payload.conteudo)

    # Gera apelido carinhoso para preservar anonimato completo
    apelido = f"Gestante_{gestante.id[:4].upper()}"

    conteudo_final = payload.conteudo.strip()
    if requer_aviso_clinico:
        conteudo_final += "\n\n⚠️ [Aviso Nymphia]: Medicamentos e interpretações de exames devem ser sempre prescritos e avaliados exclusivamente pelo seu médico."

    post = PostComunidade(
        gestante_id=gestante.id,
        apelido=apelido,
        grupo=payload.grupo,
        conteudo=conteudo_final,
        sinalizado=sinalizado,
        motivo_sinalizacao=motivo,
        revisado_por_humano=False,
        criado_em=datetime.utcnow()
    )
    db.add(post)
    db.commit()
    db.refresh(post)

    return PostOut(
        id=post.id,
        apelido=post.apelido,
        grupo=post.grupo,
        conteudo=post.conteudo,
        sinalizado=post.sinalizado,
        criado_em=post.criado_em,
        comentarios=[]
    )

@router.post("/posts/{id}/comentar", response_model=ComentarioOut, status_code=status.HTTP_201_CREATED)
def comentar_post(
    id: int,
    payload: ComentarioCreate,
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    post = db.query(PostComunidade).filter(PostComunidade.id == id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post não encontrado")

    sinalizado, _, requer_aviso = check_moderation(payload.conteudo)
    apelido = f"Gestante_{gestante.id[:4].upper()}"

    conteudo_final = payload.conteudo.strip()
    if requer_aviso:
        conteudo_final += "\n\n⚠️ [Aviso Clínico Nymphia]: Informações de saúde entre usuárias não substituem consulta médica."

    comentario = ComentarioComunidade(
        post_id=post.id,
        gestante_id=gestante.id,
        apelido=apelido,
        conteudo=conteudo_final,
        sinalizado=sinalizado,
        criado_em=datetime.utcnow()
    )
    db.add(comentario)
    db.commit()
    db.refresh(comentario)

    return ComentarioOut(
        id=comentario.id,
        post_id=comentario.post_id,
        apelido=comentario.apelido,
        conteudo=comentario.conteudo,
        sinalizado=comentario.sinalizado,
        criado_em=comentario.criado_em
    )

@router.post("/posts/{id}/denunciar")
def denunciar_post(
    id: int,
    db: Session = Depends(get_db)
):
    post = db.query(PostComunidade).filter(PostComunidade.id == id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post não encontrado")
    
    post.sinalizado = True
    post.motivo_sinalizacao = "Denunciado por usuária para moderação"
    db.commit()
    return {"status": "denunciado", "mensagem": "Conteúdo enviado para revisão da moderação"}
