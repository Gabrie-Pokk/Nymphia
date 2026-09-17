from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.ai_risk_service import calculate_maternal_risks, DISCLAIMER_TEXT
from app.models.auth import Gestante
from app.models.clinical import PerfilClinico, HistoricoFamiliar
from app.security.jwt_auth import get_current_gestante

router = APIRouter(tags=["Risco e Anomalia"])

@router.post("/risco/gestante")
def calcular_risco_gestante(payload: Dict[str, Any]):
    """
    Calcula o risco estatístico para as 6 condições obstétricas com base no perfil.
    Aceita formato plano ou { "perfil_dados": {...}, "historico_familiar": [...] }.
    Retorna explicitamente o aviso legal de triagem CFM 2.454/2026.
    """
    # Suporte flexível a formato plano ou aninhado
    perfil = payload.get("perfil_dados")
    if perfil is None:
        perfil = {k: v for k, v in payload.items() if k != "historico_familiar"}
    historico = payload.get("historico_familiar", [])
    return calculate_maternal_risks(perfil, historico)

@router.get("/risco/meu-risco")
def calcular_meu_risco(
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """
    Calcula risco da gestante autenticada a partir do prontuário salvo.
    """
    perfil = db.query(PerfilClinico).filter(PerfilClinico.gestante_id == gestante.id).first()
    historico = db.query(HistoricoFamiliar).filter(HistoricoFamiliar.gestante_id == gestante.id).all()

    perfil_dict = {
        "idade": perfil.idade if perfil else 25,
        "perdas_gestacionais": perfil.perdas_gestacionais if perfil else 0,
        "partos_cesareos": perfil.partos_cesareos if perfil else 0,
        "gestacoes_anteriores": perfil.gestacoes_anteriores if perfil else 0,
    }
    historico_list = [{"parente": h.parente, "condicao": h.condicao} for h in historico]
    return calculate_maternal_risks(perfil_dict, historico_list)

@router.post("/risco/internacao")
def calcular_risco_internacao(dados: Dict[str, Any]):
    """
    Estimativa epidemiológica de internação obstétrica baseada em dados demográficos do SIH.
    """
    idade = dados.get("idade", 25)
    uf = dados.get("uf", dados.get("uf_cod", "SP"))
    
    res = calculate_maternal_risks(dados, [])
    cond = res["condicoes"]
    return {
        "pre_eclampsia": cond.get("pre_eclampsia"),
        "eclampsia": cond.get("eclampsia"),
        "diabetes_gestacional": cond.get("diabetes_gestacional"),
        "itu": cond.get("itu"),
        "fator_regional": f"Calibrado para UF {uf}",
        "aviso_legal": DISCLAIMER_TEXT
    }

@router.post("/anomalia/detectar")
@router.post("/risco/anomalia")
def detectar_anomalia_clinica(dados: Dict[str, Any]):
    """
    Detecta padrão atípico fora das categorias conhecidas utilizando Isolation Forest.
    """
    res = calculate_maternal_risks(dados, [])
    return {
        "score_anomalia": res["score_anomalia"],
        "anomalia_detectada": res["padrao_atipico_detectado"],
        "anomalo": res["padrao_atipico_detectado"],
        "recomendacao": "Avaliação clínica detalhada recomendada" if res["padrao_atipico_detectado"] else "Padrão dentro dos desvios usuais",
        "aviso_legal": DISCLAIMER_TEXT
    }
