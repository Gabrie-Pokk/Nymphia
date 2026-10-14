import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth import Gestante
from app.models.relations import LogAcesso
from app.models.governance import ObservacaoProfissional, SolicitacaoRevisaoIA, CustodiaProntuario
from app.schemas.all_schemas import LogAcessoOut, SolicitacaoRevisaoIACreate, SolicitacaoRevisaoIAOut
from app.security.jwt_auth import get_current_gestante
from app.services.export_service import export_gestante_json, export_gestante_pdf

logger = logging.getLogger("nymphia.lgpd")

router = APIRouter(tags=["Conformidade LGPD, Governança e Portabilidade"])

# Dados oficiais do Encarregado pelo Tratamento de Dados Pessoais (DPO) - Art. 41 LGPD
DPO_INFO = {
    "encarregado_nome": "Comitê de Governança Clínica e Privacidade Nymphia",
    "responsavel_tecnico": "Dra. Daniele R. Estedan (Consultoria Clínica)",
    "email_contato": "privacidade@nymphia.com.br",
    "canal_atendimento": "https://nymphia.app/meus-dados",
    "prazo_resposta_dias_uteis": 3,
    "fundamento_legal": "Art. 41 da Lei 13.709/2018 (LGPD) e Resolução CD/ANPD nº 15/2024"
}

POLITICA_PRIVACIDADE_DOC = {
    "versao": "1.0-2026",
    "data_atualizacao": "11 de outubro de 2026",
    "controlador": "Nymphia Tecnologia em Saúde",
    "encarregado_dpo": DPO_INFO,
    "resumo": (
        "A Nymphia trata dados pessoais e dados pessoais sensíveis de saúde materno-infantil com o mais alto padrão de segurança, "
        "privacidade desde a concepção (Privacy by Design) e estrita conformidade com a Lei Geral de Proteção de Dados (LGPD - Lei 13.709/2018), "
        "com as Resoluções CFM 2.454/2026 (Inteligência Artificial na Medicina) e CFM 1.821/2007 (Prontuário Eletrônico)."
    ),
    "principios": [
        "Finalidade específica e legítima para apoio ao pré-natal e prevenção de riscos obstétricos.",
        "Minimização de dados: coleta restrita ao estritamente necessário à assistência perinatal.",
        "Transparência ativa: logs de acesso abertos à titular para verificar visualizações de terceiros.",
        "Segurança reforçada: hashing bcrypt para credenciais, tokens JWT temporários e WebAssembly Edge AI na câmera sem envio de fotos à nuvem.",
        "Livre consentimento e direito incondicional de recusa de inteligência artificial (CFM 2.454/2026)."
    ],
    "bases_legais": [
        {
            "operacao": "Cadastro e Autenticação da Conta",
            "base_legal": "Execução de contrato e procedimentos preliminares (Art. 7º, V da LGPD)"
        },
        {
            "operacao": "Tratamento de Dados Pessoais Sensíveis de Saúde (Sintomas, Histórico, Gestações, DUM)",
            "base_legal": "Consentimento específico e destacado da titular (Art. 11, I da LGPD) e Tutela da Saúde (Art. 11, II, 'f' da LGPD)"
        },
        {
            "operacao": "Triagem Automatizada e Modelos Preditivos de Risco",
            "base_legal": "Consentimento específico para IA com direito de recusa (Resolução CFM 2.454/2026 e Art. 11, I da LGPD)"
        },
        {
            "operacao": "Acionamento de Emergência Obstétrica SAMU 192",
            "base_legal": "Proteção da vida ou da incolumidade física da titular ou de terceiro (Art. 11, II, 'e' da LGPD)"
        },
        {
            "operacao": "Guarda de Prontuário Médico e Pareceres Profissionais",
            "base_legal": "Cumprimento de obrigação legal ou regulatória pelo controlador (Art. 16, I da LGPD c/c Resolução CFM nº 1.821/2007)"
        }
    ],
    "direitos_do_titular_art18": [
        "Confirmação da existência de tratamento e acesso facilitado aos dados.",
        "Portabilidade dos dados em formato JSON estruturado ou relatório médico PDF diagramado.",
        "Revogação do consentimento a qualquer momento de forma simples e gratuita.",
        "Direito de recusa expressa do uso de inteligência artificial sem prejuízo ao uso das funções clínicas baseadas em protocolos do Ministério da Saúde.",
        "Direito à revisão humana de decisões automatizadas e escores de triagem (Art. 20 da LGPD).",
        "Eliminação dos dados pessoais tratados com consentimento, ressalvado o dever de guarda de prontuário eletrônico."
    ],
    "recorte_guarda_prontuario": (
        "IMPORTANTE (CFM 1.821/2007 vs Art. 18 LGPD): Em caso de solicitação de eliminação de conta pela gestante, "
        "todos os dados pessoais cadastrais, diários de humor, check-ins e mensagens de IA são imediatamente excluídos do sistema. "
        "Contudo, havendo registros de prontuário, condutas médicas e laudos emitidos por médicos vinculados, tais registros clínicos "
        "são conservados sob dever de guarda legal da equipe médica responsável pelo prazo regulatório de guarda permanente ou mínimo "
        "de 20 anos, em estrito cumprimento ao Art. 16, I da LGPD e Resoluções CFM 1.821/2007 e CFM 2.314/2022."
    )
}

TERMOS_DE_USO_DOC = {
    "versao": "1.0-2026",
    "data_atualizacao": "11 de outubro de 2026",
    "titulo": "Termos de Uso e Condições Gerais — Plataforma Nymphia",
    "resumo": (
        "A Nymphia é uma ferramenta digital de apoio educativo, organização de informações e suporte à triagem perinatal. "
        "Seu propósito é conectar gestantes à sua equipe de saúde e rede de apoio, integrando protocolos do Ministério da Saúde, "
        "FEBRASGO e OMS."
    ),
    "natureza_do_servico": [
        "A Nymphia NÃO substitui consultas médicas de pré-natal, exames laboratoriais ou diagnósticos clínicos presenciais.",
        "Todas as análises estatísticas e classificações geradas por modelos preditivos são de triagem e apoio informativo, sujeitas a margem probabilística de erro.",
        "O julgamento clínico e a conduta terapêutica cabem exclusivamente ao médico obstetra ou enfermeiro legalmente habilitado.",
        "O canal de Emergência (SAMU 192 e maternidade de referência) é gratuito, aberto e universal em qualquer plano, inclusive para usuárias sem plano pago ou inadimplentes."
    ],
    "regras_comunitarias": [
        "É terminantemente proibido indicar dosagens de medicamentos, sugerir automedicação ou substituir prescrições médicas na comunidade.",
        "É vedada a divulgação de conteúdos difamatórios, discriminatórios, ofensivos ou contrários à segurança de gestantes e crianças.",
        "Conteúdos que indiquem sofrimento mental perinatal severo recebem acolhimento prioritário e encaminhamento aos serviços de apoio à vida (CVV 188 e SAMU 192)."
    ],
    "responsabilidades": [
        "A gestante compromete-se a fornecer informações verídicas sobre seu histórico gestacional.",
        "O profissional de saúde deve manter registro regular e ativo no CRM ou COREN e responde pelas condutas registradas sob sua autoria.",
        "A Nymphia compromete-se a manter disponibilidade, segurança e criptografia de ponta a ponta dos dados transmitidos."
    ]
}


@router.get("/politica-privacidade")
def obter_politica_privacidade():
    """
    Retorna a Política de Privacidade e Governança Clínica pública completa da Nymphia.
    Atende aos Arts. 9º, 11 e 41 da LGPD e Resoluções CFM 2.454/2026 e CFM 1.821/2007.
    """
    return POLITICA_PRIVACIDADE_DOC


@router.get("/termos-de-uso")
def obter_termos_de_uso():
    """
    Retorna os Termos de Uso públicos oficiais da plataforma Nymphia.
    """
    return TERMOS_DE_USO_DOC


@router.get("/meus-dados/dpo")
def obter_contato_dpo():
    """
    Informa publicamente a identidade e canal de contato do Encarregado pelo Tratamento de Dados (DPO - Art. 41 LGPD).
    """
    return DPO_INFO


@router.get("/meus-dados/exportar")
def exportar_meus_dados(
    formato: str = Query("json", pattern="^(json|pdf)$"),
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """
    Portabilidade de dados pessoais (Art. 18, V da LGPD).
    Permite exportação em JSON estruturado ou PDF diagramado.
    """
    if formato == "pdf":
        pdf_bytes = export_gestante_pdf(gestante.id, db)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=nymphia_prontuario_{gestante.id[:8]}.pdf"}
        )
    else:
        json_data = export_gestante_json(gestante.id, db)
        return json_data


@router.get("/meus-dados/log-acesso", response_model=List[LogAcessoOut])
def listar_log_acesso(
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """
    Transparência ativa (Art. 18 da LGPD):
    A gestante consulta quem acessou os dados dela (profissional ou parceiro) e quando.
    """
    return db.query(LogAcesso).filter(LogAcesso.gestante_id == gestante.id).order_by(LogAcesso.data_hora.desc()).all()


@router.put("/meus-dados/consentimento-ia")
def atualizar_consentimento_ia(
    recusa_ia: bool,
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """
    Resolução CFM 2.454/2026: Direito de informação e de recusa do uso de IA.
    A gestante pode utilizar a plataforma recusando a análise automatizada por IA.
    """
    gestante.recusa_ia = recusa_ia
    db.commit()
    db.refresh(gestante)
    return {
        "status": "atualizado",
        "recusa_ia": gestante.recusa_ia,
        "mensagem": "Preferência de consentimento de inteligência artificial atualizada com sucesso"
    }


@router.post("/meus-dados/solicitar-revisao-ia", response_model=SolicitacaoRevisaoIAOut, status_code=status.HTTP_201_CREATED)
def solicitar_revisao_decisao_ia(
    payload: SolicitacaoRevisaoIACreate,
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """
    Direito de revisão humana de decisões automatizadas (Art. 20 da LGPD).
    Registra solicitação formal para reanálise humana por profissional clínico.
    """
    solicitacao = SolicitacaoRevisaoIA(
        gestante_id=gestante.id,
        motivo=payload.motivo.strip(),
        recurso_analisado=payload.recurso_analisado or "escore_triagem",
        status="pendente",
        criado_em=datetime.utcnow()
    )
    db.add(solicitacao)
    db.commit()
    db.refresh(solicitacao)
    logger.info(f"Nova solicitação de revisão humana LGPD Art. 20 aberta por gestante {gestante.id}: ID {solicitacao.id}")
    return solicitacao


@router.get("/meus-dados/minhas-revisoes", response_model=List[SolicitacaoRevisaoIAOut])
def listar_minhas_revisoes_ia(
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """Lista as solicitações de revisão algorítmica abertas pela gestante."""
    return db.query(SolicitacaoRevisaoIA).filter(
        SolicitacaoRevisaoIA.gestante_id == gestante.id
    ).order_by(SolicitacaoRevisaoIA.criado_em.desc()).all()


@router.delete("/minha-conta", status_code=status.HTTP_200_OK)
def excluir_minha_conta(
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """
    Direito de eliminação de dados sensíveis (Art. 18, VI da LGPD) com cumprimento do
    dever de guarda legal de prontuários médicos (Art. 16, I da LGPD e Resolução CFM nº 1.821/2007).
    
    1. Preserva de forma anonimizada pareceres médicos formais emitidos por obstetras para atender ao dever de guarda do CFM.
    2. Exclui permanentemente todos os dados cadastrais, diários de humor, check-ins, mensagens e credenciais da gestante.
    """
    # 1. Preservação de custódia médica legal (Resolução CFM 1.821/2007)
    obs_medicas = db.query(ObservacaoProfissional).filter(ObservacaoProfissional.gestante_id == gestante.id).all()
    for obs in obs_medicas:
        db.add(CustodiaProntuario(
            profissional_id=obs.profissional_id,
            gestante_id_anonimizado=f"anon_{gestante.id[:8]}",
            observacao=obs.observacao,
            data_original=obs.criado_em,
            arquivado_em=datetime.utcnow()
        ))
    db.commit()

    # 2. Exclusão permanente da titular e dados pessoais em cascata
    db.delete(gestante)
    db.commit()

    return {
        "status": "excluida",
        "mensagem": (
            "Conta e dados cadastrais, diários de humor, check-ins e conversas foram completamente eliminados (Art. 18, VI da LGPD). "
            "Anotações médicas e condutas clínicas emitidas por profissionais vinculados permanecem sob dever de guarda legal da equipe de saúde "
            "responsável pelo prazo legal (Art. 16, I da LGPD e Resolução CFM nº 1.821/2007)."
        )
    }
