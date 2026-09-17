import json
import re
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth import Gestante
from app.models.community import PostComunidade, ComentarioComunidade, PreferenciasComunidade
from app.schemas.all_schemas import (
    PostCreate, PostOut, ComentarioCreate, ComentarioOut,
    PreferenciasComunidadeCreate, PreferenciasComunidadeOut
)
from app.security.jwt_auth import get_current_gestante
from app.services.moderation_service import moderate_community_content

router = APIRouter(prefix="/comunidade", tags=["Comunidade Segura"])

COMMUNITY_GROUPS = [
    # Grupos por Trimestre
    "Primeiro Trimestre",
    "Segundo Trimestre",
    "Terceiro Trimestre",
    # Grupos por Perfil e Experiência
    "Mães de Primeira Viagem",
    "Mães Experientes & Multiparidade",
    "Parto Humanizado & Preparação",
    "Cesárea Segura & Recuperação",
    # Grupos de Bem-Estar e Interesses
    "Nutrição & Receitas Gestacionais",
    "Yoga, Exercícios & Bem-Estar",
    "Amamentação & Cuidados com o Bebê",
    "Saúde Emocional & Puerpério",
    "Enxoval, Quarto & Preparativos",
    "Tentantes & Histórico de Perdas"
]

def calcular_grupos_recomendados(
    experiencia: Optional[str],
    preferencia_parto: Optional[str],
    interesses: List[str],
    estilo_vida: Optional[str]
) -> List[str]:
    recomendados = []

    # 1. Avaliação de Experiência Materna
    if experiencia:
        exp_lower = experiencia.lower()
        if "primeir" in exp_lower:
            recomendados.append("Mães de Primeira Viagem")
        elif any(k in exp_lower for k in ["experiente", "já tenho", "outro"]):
            recomendados.append("Mães Experientes & Multiparidade")

    # 2. Preferência de Parto
    if preferencia_parto:
        parto_lower = preferencia_parto.lower()
        if any(k in parto_lower for k in ["normal", "humanizad"]):
            recomendados.append("Parto Humanizado & Preparação")
        elif any(k in parto_lower for k in ["cesárea", "cesarea", "cesariana", "planejad"]):
            recomendados.append("Cesárea Segura & Recuperação")

    # 3. Interesses e Gostos
    for inter in (interesses or []):
        il = inter.lower()
        if any(k in il for k in ["nutri", "receita", "peso", "alimenta"]):
            recomendados.append("Nutrição & Receitas Gestacionais")
        if any(k in il for k in ["exerc", "yoga", "pilates", "movimento"]):
            recomendados.append("Yoga, Exercícios & Bem-Estar")
        if any(k in il for k in ["amamenta", "cuidados", "pega", "bebê", "bebe"]):
            recomendados.append("Amamentação & Cuidados com o Bebê")
        if any(k in il for k in ["emocional", "apoio", "ansiedade", "psicol"]):
            recomendados.append("Saúde Emocional & Puerpério")
        if any(k in il for k in ["enxoval", "quarto", "chá", "cha", "prepara"]):
            recomendados.append("Enxoval, Quarto & Preparativos")

    if not recomendados:
        recomendados = ["Mães de Primeira Viagem", "Nutrição & Receitas Gestacionais", "Saúde Emocional & Puerpério"]

    # Preserva ordem única
    vistos = set()
    resultado = []
    for g in recomendados:
        if g in COMMUNITY_GROUPS and g not in vistos:
            vistos.add(g)
            resultado.append(g)

    return resultado

@router.get("/grupos", response_model=List[str])
def listar_grupos():
    """Retorna a lista completa de grupos da comunidade segura."""
    return COMMUNITY_GROUPS

@router.get("/preferencias", response_model=PreferenciasComunidadeOut)
def obter_preferencias(
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """Obtém as preferências e gostos da gestante com os grupos recomendados para seu perfil."""
    pref = db.query(PreferenciasComunidade).filter(PreferenciasComunidade.gestante_id == gestante.id).first()
    if not pref:
        return PreferenciasComunidadeOut(
            experiencia=None,
            preferencia_parto=None,
            interesses=[],
            estilo_vida=None,
            grupos_recomendados=["Mães de Primeira Viagem", "Nutrição & Receitas Gestacionais", "Saúde Emocional & Puerpério"],
            atualizado_em=None
        )

    interesses_lista = []
    if pref.interesses:
        try:
            interesses_lista = json.loads(pref.interesses)
        except Exception:
            interesses_lista = [i.strip() for i in pref.interesses.split(",") if i.strip()]

    recomendados = calcular_grupos_recomendados(
        pref.experiencia,
        pref.preferencia_parto,
        interesses_lista,
        pref.estilo_vida
    )

    return PreferenciasComunidadeOut(
        experiencia=pref.experiencia,
        preferencia_parto=pref.preferencia_parto,
        interesses=interesses_lista,
        estilo_vida=pref.estilo_vida,
        grupos_recomendados=recomendados,
        atualizado_em=pref.atualizado_em
    )

@router.post("/preferencias", response_model=PreferenciasComunidadeOut)
def salvar_preferencias(
    payload: PreferenciasComunidadeCreate,
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """Salva as respostas do questionário de gostos e interesses da gestante."""
    pref = db.query(PreferenciasComunidade).filter(PreferenciasComunidade.gestante_id == gestante.id).first()
    interesses_json = json.dumps(payload.interesses, ensure_ascii=False)

    if not pref:
        pref = PreferenciasComunidade(
            gestante_id=gestante.id,
            experiencia=payload.experiencia,
            preferencia_parto=payload.preferencia_parto,
            interesses=interesses_json,
            estilo_vida=payload.estilo_vida,
            atualizado_em=datetime.utcnow()
        )
        db.add(pref)
    else:
        pref.experiencia = payload.experiencia
        pref.preferencia_parto = payload.preferencia_parto
        pref.interesses = interesses_json
        pref.estilo_vida = payload.estilo_vida
        pref.atualizado_em = datetime.utcnow()

    db.commit()
    db.refresh(pref)

    recomendados = calcular_grupos_recomendados(
        pref.experiencia,
        pref.preferencia_parto,
        payload.interesses,
        pref.estilo_vida
    )

    return PreferenciasComunidadeOut(
        experiencia=pref.experiencia,
        preferencia_parto=pref.preferencia_parto,
        interesses=payload.interesses,
        estilo_vida=pref.estilo_vida,
        grupos_recomendados=recomendados,
        atualizado_em=pref.atualizado_em
    )

@router.get("/posts", response_model=List[PostOut])
def listar_posts(
    grupo: Optional[str] = None,
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """Lista postagens ordenadas das mais recentes para as mais antigas."""
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
    """
    Cria postagem na Comunidade Segura com moderação em 3 camadas:
    1. Bloqueio estrito de termos tóxicos, substâncias ilícitas e automedicação perigosa.
    2. Aviso educativo automático quando exames ou consultas forem mencionados.
    3. Proteção e preservação irrestrita do anonimato da gestante.
    """
    bloqueado, motivo, requer_aviso_clinico = moderate_community_content(payload.conteudo)
    if bloqueado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=motivo or "A publicação não cumpre as Diretrizes de Segurança da Comunidade Nymphia."
        )

    # Gera apelido protetivo anônimo (ex: Gestante_3B4F)
    apelido = f"Gestante_{gestante.id[:4].upper()}"

    conteudo_final = payload.conteudo.strip()
    if requer_aviso_clinico:
        conteudo_final += "\n\n📋 *[Nota da Comunidade Segura]: Exames laboratoriais e condutas médicas devem ser sempre avaliados presencialmente com o seu obstetra.*"

    post = PostComunidade(
        gestante_id=gestante.id,
        apelido=apelido,
        grupo=payload.grupo,
        conteudo=conteudo_final,
        sinalizado=requer_aviso_clinico,
        motivo_sinalizacao="Nota informativa adicionada automaticamente" if requer_aviso_clinico else None,
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
    """Adiciona comentário moderado a uma postagem existente."""
    post = db.query(PostComunidade).filter(PostComunidade.id == id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Postagem não encontrada.")

    bloqueado, motivo, requer_aviso = moderate_community_content(payload.conteudo)
    if bloqueado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=motivo or "O comentário não cumpre as Diretrizes de Segurança da Comunidade Nymphia."
        )

    apelido = f"Gestante_{gestante.id[:4].upper()}"
    conteudo_final = payload.conteudo.strip()
    if requer_aviso:
        conteudo_final += "\n\n📋 *[Nota Nymphia]: Trocas de experiências entre usuárias não substituem a consulta de pré-natal.*"

    comentario = ComentarioComunidade(
        post_id=post.id,
        gestante_id=gestante.id,
        apelido=apelido,
        conteudo=conteudo_final,
        sinalizado=requer_aviso,
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
    """Sinaliza uma postagem suspeita para análise prioritária da equipe clínica."""
    post = db.query(PostComunidade).filter(PostComunidade.id == id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Postagem não encontrada.")

    post.sinalizado = True
    post.motivo_sinalizacao = "Denunciado por usuária para moderação clínica"
    db.commit()
    return {"status": "denunciado", "mensagem": "Conteúdo enviado para moderação prioritária."}
