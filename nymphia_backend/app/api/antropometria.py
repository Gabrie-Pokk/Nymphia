from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth import Gestante
from app.models.clinical import PerfilClinico, RegistroAntropometrico
from app.schemas.all_schemas import (
    RegistroAntropometricoCreate,
    RegistroAntropometricoOut,
    PerfilAntropometricoUpdate,
    PainelAntropometriaResponse,
    SegurancaMovimentoRequest,
    SegurancaMovimentoResponse
)
from app.security.jwt_auth import get_current_gestante
from app.services.anthropometry_service import (
    calcular_imc,
    classificar_imc_pre_gestacional,
    classificar_curva_atalah,
    avaliar_altura_uterina,
    obter_guia_educativo_antropometria
)
from app.services.clinical_movement_service import avaliar_seguranca_movimento

router = APIRouter(prefix="/antropometria", tags=["Antropometria e Postura Materna"])

def _calcular_semana_atual(dum: Optional[date]) -> int:
    if not dum:
        return 24
    hoje = datetime.utcnow().date()
    diff = (hoje - dum).days
    return max(1, min(42, diff // 7))

@router.get("/painel", response_model=PainelAntropometriaResponse)
def obter_painel_antropometria(
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """
    Retorna o painel clínico antropométrico completo da gestante:
    - Altura e peso pré-gestacional com IMC e categoria
    - Última pesagem e ganho ponderal total acumulado
    - Avaliação da Curva de Atalah para a semana gestacional atual
    - Avaliação da Altura Uterina (P10-P90)
    - Alerta de ganho rápido súbito (possível edema/pré-eclâmpsia)
    - Guia educativo rico sobre nutrição, mitos e distribuição de peso
    """
    perfil = db.query(PerfilClinico).filter(PerfilClinico.gestante_id == gestante.id).first()
    registros = (
        db.query(RegistroAntropometrico)
        .filter(RegistroAntropometrico.gestante_id == gestante.id)
        .order_by(RegistroAntropometrico.data_registro.desc(), RegistroAntropometrico.id.desc())
        .all()
    )

    semana_atual = _calcular_semana_atual(perfil.dum if perfil else None)
    altura_cm = perfil.altura_cm if perfil else None
    peso_pre = perfil.peso_pre_gestacional if perfil else None

    # Valores pré-gestacionais
    imc_pre = calcular_imc(peso_pre, altura_cm) if (peso_pre and altura_cm) else None
    classificacao_pre = classificar_imc_pre_gestacional(imc_pre) if imc_pre else None

    # Último registro
    ultimo_registro = registros[0] if registros else None
    peso_atual = ultimo_registro.peso_atual_kg if ultimo_registro else peso_pre
    au_atual = ultimo_registro.altura_uterina_cm if ultimo_registro else None

    # Ganho acumulado e IMC atual
    ganho_acumulado = None
    if peso_atual and peso_pre:
        ganho_acumulado = round(peso_atual - peso_pre, 2)

    imc_atual = calcular_imc(peso_atual, altura_cm) if (peso_atual and altura_cm) else None
    
    # Avaliação Atalah e Altura Uterina
    avaliacao_atalah = None
    if imc_atual:
        avaliacao_atalah = classificar_curva_atalah(semana_atual, imc_atual)

    avaliacao_au = None
    if au_atual:
        avaliacao_au = avaliar_altura_uterina(semana_atual, au_atual)

    # Detecção de Ganho Súbito de Peso (> 1.0 kg em menos de 10 dias no 2º ou 3º trimestre)
    alerta_ganho_subito = False
    mensagem_alerta = None
    if len(registros) >= 2:
        reg_atual = registros[0]
        reg_anterior = registros[1]
        diff_dias = (reg_atual.data_registro - reg_anterior.data_registro).days
        ganho_recente = reg_atual.peso_atual_kg - reg_anterior.peso_atual_kg
        if 0 < diff_dias <= 10 and ganho_recente >= 1.0 and semana_atual >= 20:
            alerta_ganho_subito = True
            mensagem_alerta = (
                f"Alerta Clínico: Identificamos um aumento de {ganho_recente:.1f} kg em {diff_dias} dias. "
                "Ganhos rápidos superiores a 1 kg por semana podem indicar retenção hídrica acentuada "
                "(edema) e requerem aferição da pressão arterial para rastreio de pré-eclâmpsia."
            )

    return PainelAntropometriaResponse(
        altura_cm=altura_cm,
        peso_pre_gestacional=peso_pre,
        imc_pre_gestacional=imc_pre,
        classificacao_pre_gestacional=classificacao_pre,
        peso_atual_kg=peso_atual,
        ganho_peso_acumulado_kg=ganho_acumulado,
        imc_atual=imc_atual,
        semana_gestacional_atual=semana_atual,
        avaliacao_atalah=avaliacao_atalah,
        avaliacao_altura_uterina=avaliacao_au,
        historico_registros=registros,
        guia_educativo=obter_guia_educativo_antropometria(),
        alerta_ganho_subito=alerta_ganho_subito,
        mensagem_alerta=mensagem_alerta
    )

@router.post("/perfil-base", status_code=status.HTTP_200_OK)
def atualizar_dados_base(
    payload: PerfilAntropometricoUpdate,
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """
    Atualiza ou cadastra a altura e o peso pré-gestacional da gestante.
    """
    perfil = db.query(PerfilClinico).filter(PerfilClinico.gestante_id == gestante.id).first()
    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil clínico não encontrado. Realize o onboarding primeiro.")

    perfil.altura_cm = payload.altura_cm
    perfil.peso_pre_gestacional = payload.peso_pre_gestacional
    db.commit()

    return {"status": "sucesso", "altura_cm": perfil.altura_cm, "peso_pre_gestacional": perfil.peso_pre_gestacional}

@router.post("/registro", response_model=RegistroAntropometricoOut, status_code=status.HTTP_201_CREATED)
def registrar_pesagem_medicao(
    payload: RegistroAntropometricoCreate,
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """
    Adiciona um novo registro de peso, semana gestacional, altura uterina e circunferência abdominal.
    """
    data_reg = payload.data_registro or datetime.utcnow().date()
    novo_reg = RegistroAntropometrico(
        gestante_id=gestante.id,
        data_registro=data_reg,
        semana_gestacional=payload.semana_gestacional,
        peso_atual_kg=payload.peso_atual_kg,
        altura_uterina_cm=payload.altura_uterina_cm,
        circunferencia_abdominal_cm=payload.circunferencia_abdominal_cm,
        pressao_arterial=payload.pressao_arterial,
        edema=payload.edema or "ausente",
        observacoes=payload.observacoes
    )
    db.add(novo_reg)
    db.commit()
    db.refresh(novo_reg)
    return novo_reg

@router.delete("/registro/{registro_id}", status_code=status.HTTP_200_OK)
def remover_registro(
    registro_id: int,
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """Remove uma pesagem inserida incorretamente."""
    reg = db.query(RegistroAntropometrico).filter(
        RegistroAntropometrico.id == registro_id,
        RegistroAntropometrico.gestante_id == gestante.id
    ).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Registro antropométrico não encontrado.")

    db.delete(reg)
    db.commit()
    return {"status": "removido", "id": registro_id}

@router.post("/avaliar-movimento", response_model=SegurancaMovimentoResponse)
def avaliar_movimento_seguro(
    payload: SegurancaMovimentoRequest,
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """
    Analisa como a gestante está se sentindo e retorna a triagem clínica de movimentos:
    - O que ela PODE e DEVE fazer de exercícios e posturas
    - O que ela NUNCA DEVE FAZER (proibições absolutas e relativas por segurança materno-fetal)
    - Mensagem de voz humanizada para a IA orientar em tempo real
    """
    perfil = db.query(PerfilClinico).filter(PerfilClinico.gestante_id == gestante.id).first()
    semana = payload.semana_gestacional or _calcular_semana_atual(perfil.dum if perfil else None)

    resultado = avaliar_seguranca_movimento(
        disposicao=payload.disposicao,
        queixas=payload.queixas,
        sinais_alerta=payload.sinais_alerta,
        semana_gestacional=semana
    )
    return SegurancaMovimentoResponse(**resultado)
