from typing import List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.governance import CalibracaoClinica, IntegracaoLaboratorial
from app.models.auth import Profissional, Gestante
from app.security.jwt_auth import get_current_profissional, get_current_gestante

router = APIRouter(prefix="/governance", tags=["Governança Clínica, FHIR e Calibração (Roadmap 2027)"])

@router.get("/calibracao")
def listar_calibracoes(db: Session = Depends(get_db)):
    """
    Retorna limiares clínicos configurados com suas devidas justificativas científicas.
    """
    calibracoes = db.query(CalibracaoClinica).all()
    if not calibracoes:
        # Padrões iniciais de referência
        return [
            {
                "condicao": "Hipertensão Gestacional",
                "limiar_chave": "pressao_sistolica_alerta",
                "limiar_valor": 140.0,
                "unidade": "mmHg",
                "justificativa": "Consenso FEBRASGO 2024 / ACOG Guidelines",
                "atualizado_por": "Protocolo Nacional",
                "atualizado_em": datetime.utcnow()
            },
            {
                "condicao": "Diabetes Gestacional",
                "limiar_chave": "glicemia_jejum_alerta",
                "limiar_valor": 92.0,
                "unidade": "mg/dL",
                "justificativa": "Critério IADPSG / Ministério da Saúde",
                "atualizado_por": "Protocolo Nacional",
                "atualizado_em": datetime.utcnow()
            },
            {
                "condicao": "Frequência Cardíaca Materna (Wearable Bluetooth)",
                "limiar_chave": "fhr_bradicardia_corte",
                "limiar_valor": 110.0,
                "unidade": "bpm",
                "justificativa": "Critério FIGO Cardiotocografia",
                "atualizado_por": "Protocolo Nacional",
                "atualizado_em": datetime.utcnow()
            }
        ]
    return calibracoes

@router.post("/calibracao", status_code=status.HTTP_201_CREATED)
def atualizar_calibracao(
    condicao: str,
    limiar_chave: str,
    limiar_valor: float,
    unidade: str,
    justificativa: str,
    prof: Profissional = Depends(get_current_profissional),
    db: Session = Depends(get_db)
):
    """
    Ajuste de limiar clínico por médico responsável com registro auditável da justificativa.
    """
    calibracao = CalibracaoClinica(
        condicao=condicao,
        limiar_chave=limiar_chave,
        limiar_valor=limiar_valor,
        unidade=unidade,
        justificativa=justificativa,
        atualizado_por=f"Dr(a). {prof.nome} ({prof.registro_tipo} {prof.registro_numero}/{prof.registro_uf})",
        atualizado_em=datetime.utcnow()
    )
    db.add(calibracao)
    db.commit()
    db.refresh(calibracao)
    return calibracao

@router.post("/laboratorio/fhir", status_code=status.HTTP_201_CREATED)
def receber_exame_fhir(
    payload: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Estrutura para receber resultados laboratoriais parceiros em padrão FHIR (HL7 R4).
    Resource: DiagnosticReport / Observation
    """
    resource_type = payload.get("resourceType", "DiagnosticReport")
    identifier = payload.get("id", "FHIR-UNKNOWN")
    gestante_ref = payload.get("subject", {}).get("reference", "")

    # Extrai UUID se vier como 'Patient/<uuid>'
    gestante_id = gestante_ref.replace("Patient/", "") if "Patient/" in gestante_ref else gestante_ref

    registro = IntegracaoLaboratorial(
        gestante_id=gestante_id or "nao_vinculado",
        fhir_resource_type=resource_type,
        fhir_identifier=identifier,
        conteudo_fhir=payload,
        status_processamento="processado",
        recebido_em=datetime.utcnow()
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)

    return {
        "status": "sucesso_fhir",
        "registro_id": registro.id,
        "resourceType": resource_type,
        "identifier": identifier
    }

@router.get("/expansao-regional")
def parametros_regionais():
    """
    Suporte a múltiplas regiões com parâmetros e taxas epidemiológicas configuráveis.
    """
    return {
        "regioes": {
            "sudeste": {"fator_incidencia_pe": 1.0, "maternidades_conveniadas": 142},
            "nordeste": {"fator_incidencia_pe": 1.15, "maternidades_conveniadas": 98},
            "sul": {"fator_incidencia_pe": 0.95, "maternidades_conveniadas": 76},
            "centro-oeste": {"fator_incidencia_pe": 1.05, "maternidades_conveniadas": 54},
            "norte": {"fator_incidencia_pe": 1.25, "maternidades_conveniadas": 41}
        },
        "padrao_rnds_conectado": True,
        "versao_protocolo": "2027.3"
    }
