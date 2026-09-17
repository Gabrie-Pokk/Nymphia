import random
import string
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.auth import Gestante, Profissional
from app.models.clinical import PerfilClinico, HistoricoFamiliar, CheckinRegistro, Exame
from app.models.interaction import EventoEmergencia, Mensagem, EventoAgenda
from app.models.relations import Vinculo, CodigoConvite, LogAcesso
from app.models.governance import ObservacaoProfissional
from app.schemas.all_schemas import (
    CodigoConviteOut, UsarCodigoRequest, SolicitarVinculoRequest,
    ResponderVinculoRequest, VinculoOut, PacientePainelItem,
    ObservacaoProfissionalCreate, ObservacaoProfissionalOut
)
from app.security.jwt_auth import get_current_gestante, get_current_profissional
from app.services.ai_risk_service import calculate_maternal_risks

router = APIRouter(prefix="/vinculo", tags=["Vínculo Gestante-Profissional e Painel"])

def generate_random_code(length: int = 8) -> str:
    chars = string.ascii_uppercase + string.digits
    # Avoid ambiguous characters (0, O, 1, I)
    clean_chars = "".join([c for c in chars if c not in "0O1I"])
    return "".join(random.choices(clean_chars, k=length))

# --- PROFISSIONAL: GERAR CÓDIGO DE CONVITE ---
@router.post("/convite/gerar", response_model=CodigoConviteOut)
def gerar_codigo_convite(
    prof: Profissional = Depends(get_current_profissional),
    db: Session = Depends(get_db)
):
    """
    Gera código alfanumérico de 8 caracteres.
    REGRA ESPECIFICADA: Gerar código NÃO cria vínculo nenhum.
    """
    codigo_str = generate_random_code(8)
    # Garante unicidade
    while db.query(CodigoConvite).filter(CodigoConvite.codigo == codigo_str).first():
        codigo_str = generate_random_code(8)

    expira_em = datetime.utcnow() + timedelta(days=7)
    convite = CodigoConvite(
        codigo=codigo_str,
        profissional_id=prof.id,
        usado=False,
        criado_em=datetime.utcnow(),
        expira_em=expira_em
    )
    db.add(convite)
    db.commit()
    return CodigoConviteOut(codigo=codigo_str, expira_em=expira_em)

# --- GESTANTE: USAR CÓDIGO (CRIA O VÍNCULO) ---
@router.post("/convite/usar", response_model=VinculoOut, status_code=status.HTTP_201_CREATED)
def usar_codigo_convite(
    payload: UsarCodigoRequest,
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """
    É ESTE endpoint que cria o vínculo ativo.
    Só a gestante pode chamá-lo.
    404 se código inexistente ou expirado | 409 se já usado | 409 se já vinculada
    """
    codigo_limpo = payload.codigo.strip().upper()
    convite = db.query(CodigoConvite).filter(CodigoConvite.codigo == codigo_limpo).first()
    
    if not convite or convite.expira_em < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Código de convite inexistente ou expirado"
        )

    if convite.usado:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este código de convite já foi utilizado"
        )

    # Verifica se já existe vínculo ativo ou pendente com este profissional
    vinculo_existente = db.query(Vinculo).filter(
        Vinculo.gestante_id == gestante.id,
        Vinculo.profissional_id == convite.profissional_id,
        Vinculo.status.in_(["ativo", "pendente"])
    ).first()

    if vinculo_existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Você já possui vínculo ativo ou pendente com este profissional"
        )

    # Marca convite como usado
    convite.usado = True

    # Cria vínculo ATIVO
    novo_vinculo = Vinculo(
        gestante_id=gestante.id,
        profissional_id=convite.profissional_id,
        status="ativo",
        origem="convite",
        criado_em=datetime.utcnow(),
        respondido_em=datetime.utcnow()
    )
    db.add(novo_vinculo)
    db.commit()
    db.refresh(novo_vinculo)

    prof = db.query(Profissional).filter(Profissional.id == convite.profissional_id).first()

    return VinculoOut(
        id=novo_vinculo.id,
        gestante_id=gestante.id,
        profissional_id=convite.profissional_id,
        profissional_nome=prof.nome if prof else "",
        gestante_nome=gestante.nome,
        status="ativo",
        origem="convite",
        criado_em=novo_vinculo.criado_em,
        respondido_em=novo_vinculo.respondido_em
    )

# --- REVOGAÇÃO PELA GESTANTE ---
@router.post("/{id}/revogar", status_code=status.HTTP_200_OK)
def revogar_vinculo(
    id: int,
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """
    Efeito imediato. Verifica posse antes de qualquer ação.
    Após revogação, o profissional deixa de ver a gestante.
    """
    vinculo = db.query(Vinculo).filter(
        Vinculo.id == id,
        Vinculo.gestante_id == gestante.id
    ).first()

    if not vinculo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vínculo não encontrado ou não pertence a esta gestante"
        )

    vinculo.status = "revogado"
    db.commit()
    return {"status": "revogado", "mensagem": "Vínculo revogado com sucesso"}

# --- LISTAGENS DE VÍNCULOS ---
@router.get("/meus-profissionais", response_model=List[VinculoOut])
def listar_meus_profissionais(
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    vinculos = db.query(Vinculo).filter(
        Vinculo.gestante_id == gestante.id,
        Vinculo.status == "ativo"
    ).all()

    out = []
    for v in vinculos:
        prof = db.query(Profissional).filter(Profissional.id == v.profissional_id).first()
        out.append(VinculoOut(
            id=v.id,
            gestante_id=v.gestante_id,
            profissional_id=v.profissional_id,
            profissional_nome=prof.nome if prof else "",
            gestante_nome=gestante.nome,
            status=v.status,
            origem=v.origem,
            criado_em=v.criado_em,
            respondido_em=v.respondido_em
        ))
    return out

# --- PAINEL DO MÉDICO: ORDENAÇÃO POR PRIORIDADE DE URGÊNCIA ---
@router.get("/minhas-gestantes", response_model=List[PacientePainelItem])
def listar_minhas_gestantes(
    prof: Profissional = Depends(get_current_profissional),
    db: Session = Depends(get_db)
):
    """
    PAINEL DO PROFISSIONAL:
    Ordenada ESTRITAMENTE por prioridade de urgência, NUNCA alfabética.
    Critério 1: Contagem de alertas (check-in e conversa) nos últimos 30 dias (DESC).
    Critério 2 (desempate): Check-in mais recente primeiro (DESC).
    Critério 3: Gestante sem check-in fica por ÚLTIMO dentro do seu grupo.
    """
    vinculos = db.query(Vinculo).filter(
        Vinculo.profissional_id == prof.id,
        Vinculo.status == "ativo"
    ).all()

    now = datetime.utcnow()
    trinta_dias_atras = now - timedelta(days=30)

    lista_pacientes = []

    for v in vinculos:
        gestante = db.query(Gestante).filter(Gestante.id == v.gestante_id).first()
        if not gestante:
            continue

        perfil = db.query(PerfilClinico).filter(PerfilClinico.gestante_id == gestante.id).first()

        # Check-ins dos últimos 30 dias
        checkins_30d = db.query(CheckinRegistro).filter(
            CheckinRegistro.gestante_id == gestante.id,
            CheckinRegistro.data_hora >= trinta_dias_atras
        ).all()

        # Mensagens com alerta de emergência nos últimos 30 dias
        mensagens_alerta_30d = db.query(Mensagem).filter(
            Mensagem.gestante_id == gestante.id,
            Mensagem.alerta_emergencia == True,
            Mensagem.data_hora >= trinta_dias_atras
        ).count()

        # Total de alertas
        total_alertas_checkin = sum(len(c.alerta_sintoma_fisico or []) for c in checkins_30d)
        total_alertas = total_alertas_checkin + mensagens_alerta_30d

        # Último check-in geral
        ultimo_checkin = (
            db.query(CheckinRegistro)
            .filter(CheckinRegistro.gestante_id == gestante.id)
            .order_by(CheckinRegistro.data_hora.desc())
            .first()
        )

        ultimo_checkin_dt = ultimo_checkin.data_hora if ultimo_checkin else None
        
        # Formatar relativo
        if ultimo_checkin_dt:
            diff_dias = (now - ultimo_checkin_dt).days
            if diff_dias == 0:
                ultimo_relativo = "hoje"
            elif diff_dias == 1:
                ultimo_relativo = "ontem"
            else:
                ultimo_relativo = f"há {diff_dias} dias"
        else:
            ultimo_relativo = "nunca realizou"

        # Próxima consulta futura
        prox_consulta = (
            db.query(EventoAgenda)
            .filter(
                EventoAgenda.gestante_id == gestante.id,
                EventoAgenda.tipo == "consulta",
                EventoAgenda.data_hora >= now
            )
            .order_by(EventoAgenda.data_hora.asc())
            .first()
        )

        # Semana gestacional estimada
        semana_gest = None
        if perfil and perfil.dum:
            dias_gest = (datetime.utcnow().date() - perfil.dum).days
            semana_gest = max(1, dias_gest // 7)

        lista_pacientes.append({
            "gestante_id": gestante.id,
            "nome": gestante.nome,
            "semana_gestacional": semana_gest,
            "total_alertas_30d": total_alertas,
            "ultimo_checkin": ultimo_checkin_dt,
            "ultimo_checkin_relativo": ultimo_relativo,
            "proxima_consulta": prox_consulta.data_hora if prox_consulta else None,
            "vinculo_id": v.id
        })

    # Regras de ordenação:
    # 1. total_alertas_30d DESC
    # 2. tem_checkin: True antes de False (gestante sem check-in fica por último)
    # 3. timestamp do último check-in DESC
    def sorting_key(item):
        alertas = item["total_alertas_30d"]
        tem_checkin = 1 if item["ultimo_checkin"] is not None else 0
        ts = item["ultimo_checkin"].timestamp() if item["ultimo_checkin"] else 0.0
        return (alertas, tem_checkin, ts)

    lista_pacientes.sort(key=sorting_key, reverse=True)

    return [PacientePainelItem(**p) for p in lista_pacientes]

# --- FICHA DA PACIENTE (SOMENTE LEITURA + AUDITORIA LGPD) ---
@router.get("/paciente/{gestante_id}/ficha")
def obter_ficha_paciente(
    gestante_id: str,
    prof: Profissional = Depends(get_current_profissional),
    db: Session = Depends(get_db)
):
    # Verifica vínculo ativo
    vinculo = db.query(Vinculo).filter(
        Vinculo.profissional_id == prof.id,
        Vinculo.gestante_id == gestante_id,
        Vinculo.status == "ativo"
    ).first()

    if not vinculo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não possui vínculo clínico ativo com esta gestante"
        )

    # REGISTRO DE AUDITORIA LGPD (LogAcesso)
    log_acesso = LogAcesso(
        gestante_id=gestante_id,
        acessado_por_id=prof.id,
        acessado_por_tipo="profissional",
        recurso="prontuario_completo",
        data_hora=datetime.utcnow()
    )
    db.add(log_acesso)
    db.commit()

    gestante = db.query(Gestante).filter(Gestante.id == gestante_id).first()
    perfil = db.query(PerfilClinico).filter(PerfilClinico.gestante_id == gestante_id).first()
    historico = db.query(HistoricoFamiliar).filter(HistoricoFamiliar.gestante_id == gestante_id).all()
    checkins = db.query(CheckinRegistro).filter(CheckinRegistro.gestante_id == gestante_id).order_by(CheckinRegistro.data_hora.desc()).all()
    exames = db.query(Exame).filter(Exame.gestante_id == gestante_id).all()
    emergencias = db.query(EventoEmergencia).filter(EventoEmergencia.gestante_id == gestante_id).all()
    mensagens_autorizadas = db.query(Mensagem).filter(
        Mensagem.gestante_id == gestante_id,
        Mensagem.autorizado_compartilhar == True
    ).order_by(Mensagem.data_hora.asc()).all()
    observacoes_medicas = db.query(ObservacaoProfissional).filter(
        ObservacaoProfissional.profissional_id == prof.id,
        ObservacaoProfissional.gestante_id == gestante_id
    ).order_by(ObservacaoProfissional.criado_em.desc()).all()

    # Cálculo dos riscos obstétricos
    perfil_dict = {
        "idade": perfil.idade if perfil else 25,
        "perdas_gestacionais": perfil.perdas_gestacionais if perfil else 0,
        "partos_cesareos": perfil.partos_cesareos if perfil else 0,
        "gestacoes_anteriores": perfil.gestacoes_anteriores if perfil else 0,
    }
    historico_list = [{"parente": h.parente, "condicao": h.condicao} for h in historico]
    riscos_calculados = calculate_maternal_risks(perfil_dict, historico_list)

    return {
        "identificacao": {
            "nome": gestante.nome,
            "email": gestante.email,
            "recusa_ia": gestante.recusa_ia
        },
        "perfil_clinico": perfil,
        "historico_familiar": historico,
        "riscos_calculados": riscos_calculados,
        "checkins": checkins,
        "exames": exames,
        "emergencias": emergencias,
        "mensagens_autorizadas": mensagens_autorizadas,
        "observacoes_medicas": observacoes_medicas,
        "somente_leitura": True
    }

@router.post("/paciente/{gestante_id}/observacao", response_model=ObservacaoProfissionalOut, status_code=status.HTTP_201_CREATED)
def adicionar_observacao_medica(
    gestante_id: str,
    payload: ObservacaoProfissionalCreate,
    prof: Profissional = Depends(get_current_profissional),
    db: Session = Depends(get_db)
):
    """
    O profissional registra observações em campo próprio, NUNCA edita o registro da gestante.
    """
    vinculo = db.query(Vinculo).filter(
        Vinculo.profissional_id == prof.id,
        Vinculo.gestante_id == gestante_id,
        Vinculo.status == "ativo"
    ).first()

    if not vinculo:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem vínculo ativo com a gestante")

    obs = ObservacaoProfissional(
        profissional_id=prof.id,
        gestante_id=gestante_id,
        observacao=payload.observacao.strip(),
        criado_em=datetime.utcnow()
    )
    db.add(obs)
    db.commit()
    db.refresh(obs)
    return obs
