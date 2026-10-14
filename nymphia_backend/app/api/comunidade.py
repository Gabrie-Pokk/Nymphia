import json
import re
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth import Gestante
from app.models.community import (
    PostComunidade, ComentarioComunidade, PreferenciasComunidade,
    DenunciaComunidade, RecursoModeracao
)
from app.schemas.all_schemas import (
    PostCreate, PostOut, ComentarioCreate, ComentarioOut,
    PreferenciasComunidadeCreate, PreferenciasComunidadeOut,
    DenunciaCreate, DenunciaOut, RecursoCreate, RecursoOut, ModeracaoItemOut
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
    """Lista postagens não ocultadas, ordenadas das mais recentes para as mais antigas."""
    query = db.query(PostComunidade).filter(PostComunidade.ocultado == False)
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
            ) for c in p.comentarios if not c.ocultado
        ]
        out.append(PostOut(
            id=p.id,
            apelido=p.apelido,
            grupo=p.grupo,
            conteudo=p.conteudo,
            sinalizado=p.sinalizado,
            ocultado=p.ocultado,
            motivo_sinalizacao=p.motivo_sinalizacao,
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

# Protocolo Institucional de Apoio Emocional Imediato (CVV 188 / SUS)
PROTOCOLO_CVV_188: Dict[str, Any] = {
    "titulo": "Acolhimento e Apoio Emocional Imediato",
    "mensagem": (
        "Você não está sozinha. A gestação e o puerpério trazem transformações profundas e momentos de vulnerabilidade. "
        "Existem profissionais e voluntários capacitados prontos para ouvir você com sigilo absoluto e sem qualquer julgamento."
    ),
    "cvv": "188",
    "cvv_titulo": "Centro de Valorização da Vida (CVV)",
    "cvv_descricao": "Ligação 100% gratuita, sigilosa e disponível 24 horas por dia em todo o Brasil.",
    "cvv_link": "tel:188",
    "cvv_site": "https://www.cvv.org.br",
    "samu": "192",
    "samu_descricao": "SAMU - Serviço de Atendimento Móvel de Urgência em situações de emergência física imediata.",
    "caps": "Unidades do CAPS (Centro de Atenção Psicossocial) e UPAs do SUS oferecem acolhimento multiprofissional imediato e gratuito."
}

DIRETRIZES_COMUNIDADE: Dict[str, Any] = {
    "titulo": "Diretrizes de Segurança e Convivência da Comunidade Nymphia",
    "fundamento_legal": "Marco Civil da Internet (Lei 12.965/2014), Decisão STF Tema 987 (26/06/2025) e Resoluções CFM/COFEN",
    "regras": [
        {
            "topico": "Vedação Estrita à Automedicação",
            "descricao": "É expressamente proibido sugerir doses, alterar prescrições ou indicar medicamentos alopáticos ou fórmulas caseiras de risco. Decisões clínicas cabem exclusivamente ao médico assistente."
        },
        {
            "topico": "Anonimato Protetivo e Sigilo de Dados",
            "descricao": "Suas postagens utilizam pseudônimos protetivos para resguardar sua privacidade. Nunca divulgue telefones, endereços ou dados identificáveis."
        },
        {
            "topico": "Respeito e Comunicação Empática",
            "descricao": "Não toleramos julgamentos estigmatizantes sobre parto, ganho de peso, amamentação ou escolhas familiares. Qualquer forma de ódio ou assédio é removida."
        },
        {
            "topico": "Direito de Recurso (STF Tema 987)",
            "descricao": "Se sua publicação for moderada ou ocultada, você tem o direito garantido de justificar o contexto e requerer revisão humana."
        },
        {
            "topico": "Acolhimento em Sofrimento Mental (CVV 188)",
            "descricao": "Sinais de sofrimento agudo, depressão pós-parto ou ideação acionam imediatamente a rede de acolhimento do CVV (Ligue 188) e emergências do SUS."
        }
    ]
}


@router.get("/diretrizes")
def obter_diretrizes_comunidade():
    """Retorna as diretrizes clínicas e de convivência segura da comunidade Nymphia."""
    return DIRETRIZES_COMUNIDADE


@router.post("/posts/{id}/denunciar", response_model=DenunciaOut)
def denunciar_post(
    id: int,
    payload: Optional[DenunciaCreate] = None,
    db: Session = Depends(get_db)
):
    """
    Sinaliza postagem com motivo estruturado (STF Tema 987 & Marco Civil).
    Caso o motivo seja 'automutilacao_suicidio', aciona ocultação preventiva imediata
    e retorna o protocolo de acolhimento humanizado (CVV 188 e SAMU 192).
    """
    post = db.query(PostComunidade).filter(PostComunidade.id == id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Postagem não encontrada.")

    motivo = payload.motivo if payload else "Denunciado por usuária para moderação clínica"
    detalhes = payload.detalhes if payload else None

    # Cria registro estruturado da denúncia
    denuncia = DenunciaComunidade(
        post_id=post.id,
        motivo=motivo,
        detalhes=detalhes,
        status="pendente",
        criado_em=datetime.utcnow()
    )

    acao_imediata = None
    protocolo_acolhimento = None

    if motivo == "automutilacao_suicidio":
        post.sinalizado = True
        post.ocultado = True
        post.motivo_sinalizacao = "Ocultado preventivamente por sofrimento mental grave / risco de ideação"
        post.motivo_ocultacao = "Ocultação preventiva imediata para salvaguarda de integridade física e mental"
        denuncia.status = "em_analise_prioritaria"
        denuncia.acao_tomada = "ocultacao_preventiva_imediata"
        acao_imediata = "ocultacao_preventiva"
        protocolo_acolhimento = PROTOCOLO_CVV_188
    else:
        post.sinalizado = True
        if not post.motivo_sinalizacao:
            post.motivo_sinalizacao = f"Sinalizado por denúncia: {motivo}"
        denuncia.acao_tomada = "sinalizacao_para_auditoria"

    db.add(denuncia)
    db.commit()
    db.refresh(denuncia)

    return DenunciaOut(
        id=denuncia.id,
        status=denuncia.status,
        mensagem="Denúncia registrada com sucesso e encaminhada à equipe de moderação clínica.",
        acao_imediata=acao_imediata,
        protocolo_acolhimento=protocolo_acolhimento
    )


@router.post("/comentarios/{id}/denunciar", response_model=DenunciaOut)
def denunciar_comentario(
    id: int,
    payload: Optional[DenunciaCreate] = None,
    db: Session = Depends(get_db)
):
    """Sinaliza um comentário com motivo estruturado e auditoria preventiva."""
    comentario = db.query(ComentarioComunidade).filter(ComentarioComunidade.id == id).first()
    if not comentario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comentário não encontrado.")

    motivo = payload.motivo if payload else "Denunciado por usuária para moderação clínica"
    detalhes = payload.detalhes if payload else None

    denuncia = DenunciaComunidade(
        comentario_id=comentario.id,
        motivo=motivo,
        detalhes=detalhes,
        status="pendente",
        criado_em=datetime.utcnow()
    )

    acao_imediata = None
    protocolo_acolhimento = None

    if motivo == "automutilacao_suicidio":
        comentario.sinalizado = True
        comentario.ocultado = True
        denuncia.status = "em_analise_prioritaria"
        denuncia.acao_tomada = "ocultacao_preventiva_imediata"
        acao_imediata = "ocultacao_preventiva"
        protocolo_acolhimento = PROTOCOLO_CVV_188
    else:
        comentario.sinalizado = True
        denuncia.acao_tomada = "sinalizacao_para_auditoria"

    db.add(denuncia)
    db.commit()
    db.refresh(denuncia)

    return DenunciaOut(
        id=denuncia.id,
        status=denuncia.status,
        mensagem="Denúncia do comentário registrada com sucesso.",
        acao_imediata=acao_imediata,
        protocolo_acolhimento=protocolo_acolhimento
    )


@router.post("/posts/{id}/recorrer", response_model=RecursoOut, status_code=status.HTTP_201_CREATED)
def submeter_recurso_post(
    id: int,
    payload: RecursoCreate,
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """
    Submete recurso/contestação contra moderação ou ocultação de postagem (STF Tema 987).
    Garante o devido processo legal e contraditório à autora da postagem.
    """
    post = db.query(PostComunidade).filter(PostComunidade.id == id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Postagem não encontrada.")

    if post.gestante_id != gestante.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas a autora da postagem pode submeter recurso.")

    if not post.sinalizado and not post.ocultado:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Esta postagem não sofreu moderação ou ocultação.")

    # Verifica se já existe recurso pendente
    existente = db.query(RecursoModeracao).filter(
        RecursoModeracao.post_id == post.id,
        RecursoModeracao.status == "pendente"
    ).first()
    if existente:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Já existe um recurso pendente de análise para esta postagem.")

    recurso = RecursoModeracao(
        post_id=post.id,
        gestante_id=gestante.id,
        justificativa=payload.justificativa.strip(),
        status="pendente",
        criado_em=datetime.utcnow()
    )
    db.add(recurso)
    db.commit()
    db.refresh(recurso)

    return RecursoOut(
        id=recurso.id,
        post_id=recurso.post_id,
        comentario_id=recurso.comentario_id,
        justificativa=recurso.justificativa,
        status=recurso.status,
        decisao_motivo=recurso.decisao_motivo,
        criado_em=recurso.criado_em
    )


@router.get("/minhas-moderacoes", response_model=List[ModeracaoItemOut])
def listar_minhas_moderacoes(
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """
    Lista todos os conteúdos da gestante que foram sinalizados ou ocultados pela moderação,
    apresentando o status de recursos e o motivo da ação de moderação (STF Tema 987).
    """
    posts = db.query(PostComunidade).filter(
        PostComunidade.gestante_id == gestante.id,
        (PostComunidade.sinalizado == True) | (PostComunidade.ocultado == True)
    ).order_by(PostComunidade.criado_em.desc()).all()

    resultado: List[ModeracaoItemOut] = []
    for p in posts:
        ultimo_recurso = db.query(RecursoModeracao).filter(
            RecursoModeracao.post_id == p.id
        ).order_by(RecursoModeracao.criado_em.desc()).first()

        resultado.append(ModeracaoItemOut(
            id=p.id,
            tipo="post",
            grupo=p.grupo,
            conteudo=p.conteudo,
            sinalizado=p.sinalizado,
            ocultado=p.ocultado,
            motivo_sinalizacao=p.motivo_sinalizacao,
            motivo_ocultacao=p.motivo_ocultacao,
            criado_em=p.criado_em,
            recurso_status=ultimo_recurso.status if ultimo_recurso else None,
            recurso_decisao=ultimo_recurso.decisao_motivo if ultimo_recurso else None
        ))

    return resultado
