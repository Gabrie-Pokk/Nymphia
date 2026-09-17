from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from app.services.ai_risk_service import calculate_maternal_risks, DISCLAIMER_TEXT
from app.services.ai_text_service import classify_text_emotions

router = APIRouter(tags=["Rotas Legadas (Retrocompatibilidade)"])


class DadosGestanteLegacy(BaseModel):
    idade_mae: int = Field(..., ge=10, le=60)
    estado_civil: int = Field(1, ge=1, le=9)
    escolaridade: int = Field(4, ge=1, le=9)
    qtd_gestacoes_anteriores: int = Field(0, ge=0, le=20)
    qtd_partos_normais: int = Field(0, ge=0, le=20)
    qtd_partos_cesarea: int = Field(0, ge=0, le=20)
    qtd_filhos_perdidos: int = Field(0, ge=0, le=20)
    tipo_gravidez: int = Field(1, ge=1, le=9)
    qtd_consultas_prenatal: int = Field(4, ge=0, le=20)
    mes_inicio_prenatal: int = Field(2, ge=0, le=9)
    local_nascimento_previsto: int = Field(1, ge=1, le=9)
    leitos_obstetricos_estabelecimento: Optional[float] = None
    leitos_obstetricos_sus: Optional[float] = None
    tipo_parto: Optional[int] = None
    apgar_1min: Optional[int] = None
    apgar_5min: Optional[int] = None
    peso_nascer_gramas: Optional[int] = None
    semanas_gestacao_no_parto: Optional[int] = None


class DadosInternacaoLegacy(BaseModel):
    idade: int = Field(..., ge=10, le=60)
    uf: int = Field(35, description="Código IBGE do UF")
    municipio: int = Field(355030, description="Código IBGE do município")


class CheckinTextoLegacy(BaseModel):
    texto: str


@router.post("/risco/gestante")
def risco_gestante(dados: DadosGestanteLegacy):
    perfil = {
        "idade": dados.idade_mae,
        "estado_civil": dados.estado_civil,
        "escolaridade": dados.escolaridade,
        "gestacoes_anteriores": dados.qtd_gestacoes_anteriores,
        "partos_normais": dados.qtd_partos_normais,
        "partos_cesareos": dados.qtd_partos_cesarea,
        "perdas_gestacionais": dados.qtd_filhos_perdidos,
        "gravidez_multipla": dados.tipo_gravidez,
        "consultas_prenatal": dados.qtd_consultas_prenatal,
        "mes_inicio_prenatal": dados.mes_inicio_prenatal,
        "leitos_obstetricos": dados.leitos_obstetricos_estabelecimento or 15.0,
        "leitos_sus": dados.leitos_obstetricos_sus or 12.0,
    }
    res = calculate_maternal_risks(perfil, [])
    cond = res["condicoes"]
    return {
        "bem_estar_fetal": {
            "condicao": "bem_estar_fetal",
            "probabilidade": cond["bem_estar_fetal"]["probabilidade"],
            "nivel": cond["bem_estar_fetal"]["nivel"]
        },
        "malformacao": {
            "condicao": "malformacao",
            "probabilidade": cond["malformacao"]["probabilidade"],
            "nivel": cond["malformacao"]["nivel"]
        },
        "aviso_legal": DISCLAIMER_TEXT
    }


@router.post("/risco/internacao")
def risco_internacao(dados: DadosInternacaoLegacy):
    perfil = {
        "idade": dados.idade,
        "uf_cod": dados.uf,
        "municipio_cod": dados.municipio
    }
    res = calculate_maternal_risks(perfil, [])
    cond = res["condicoes"]
    return {
        "pre_eclampsia": {"condicao": "pre_eclampsia", "probabilidade": cond["pre_eclampsia"]["probabilidade"], "nivel": cond["pre_eclampsia"]["nivel"]},
        "eclampsia": {"condicao": "eclampsia", "probabilidade": cond["eclampsia"]["probabilidade"], "nivel": cond["eclampsia"]["nivel"]},
        "diabetes_gestacional": {"condicao": "diabetes_gestacional", "probabilidade": cond["diabetes_gestacional"]["probabilidade"], "nivel": cond["diabetes_gestacional"]["nivel"]},
        "itu": {"condicao": "itu", "probabilidade": cond["itu"]["probabilidade"], "nivel": cond["itu"]["nivel"]},
        "aviso_legal": DISCLAIMER_TEXT
    }


@router.post("/risco/anomalia")
def risco_anomalia(dados: DadosGestanteLegacy):
    perfil = {
        "idade": dados.idade_mae,
        "perdas_gestacionais": dados.qtd_filhos_perdidos,
        "partos_cesareos": dados.qtd_partos_cesarea,
    }
    res = calculate_maternal_risks(perfil, [])
    return {
        "score": res["score_anomalia"],
        "anomalo": res["padrao_atipico_detectado"],
        "aviso_legal": DISCLAIMER_TEXT
    }


@router.post("/checkin/analisar")
def checkin_analisar(dados: CheckinTextoLegacy):
    scores, active = classify_text_emotions(dados.texto)
    return {
        "scores": scores,
        "categorias_ativas": active,
        "alerta_sintoma_fisico": "sintoma_fisico" in active
    }
