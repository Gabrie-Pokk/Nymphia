from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth import Gestante
from app.models.clinical import PerfilClinico, RegistroAntropometrico, Exame
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
    categoria_por_imc,
    classificar_imc_pre_gestacional,
    classificar_ganho_ponderal_ufrj_ms,
    avaliar_altura_uterina,
    obter_guia_educativo_antropometria,
    semana_na_data,
    ler_pressao_arterial,
    avaliar_pressao_arterial,
    avaliar_edema,
    avaliar_ritmo_de_ganho,
    curva_ganho_recomendada,
)
from app.services.clinical_movement_service import avaliar_seguranca_movimento

router = APIRouter(prefix="/antropometria", tags=["Antropometria e Postura Materna"])

def _calcular_semana_atual(dum: Optional[date]) -> Optional[int]:
    """Semana de hoje pela DUM. Sem DUM, None: antes o app inventava 24 semanas."""
    if not dum:
        return None
    return max(1, min(42, (datetime.utcnow().date() - dum).days // 7))


def _semana_do_registro(reg: RegistroAntropometrico, dum: Optional[date]) -> int:
    """Semana em que a medida foi feita: pela DUM quando existe, senão a informada."""
    pela_dum = semana_na_data(dum, reg.data_registro)
    return max(1, min(42, pela_dum if pela_dum is not None else int(reg.semana_gestacional)))


def _alertas_do_registro(reg: RegistroAntropometrico, anterior: Optional[RegistroAntropometrico],
                         dum: Optional[date]) -> List[dict]:
    """Pressão, inchaço e ritmo de ganho da medida, do mais grave para o mais leve."""
    alertas = []
    pressao = avaliar_pressao_arterial(reg.pressao_arterial, reg.data_registro)
    if pressao and pressao["nivel"] != "nenhum":
        alertas.append(pressao)
    edema = avaliar_edema(reg.edema)
    if edema:
        alertas.append(edema)
    if anterior is not None:
        ritmo = avaliar_ritmo_de_ganho(reg.peso_atual_kg, reg.data_registro, anterior.peso_atual_kg,
                                       anterior.data_registro, _semana_do_registro(reg, dum))
        if ritmo:
            alertas.append(ritmo)
    ordem = {"urgente": 0, "atencao": 1}
    return sorted(alertas, key=lambda a: ordem.get(a["nivel"], 2))

@router.get("/painel", response_model=PainelAntropometriaResponse)
def obter_painel_antropometria(
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """
    Retorna o painel clínico antropométrico completo da gestante:
    - Altura e peso pré-gestacional com IMC e categoria
    - Última pesagem e ganho ponderal total acumulado
    - Avaliação do ganho de peso pela recomendação brasileira (FEBRASGO 2023 / MS 2022)
    - avaliacao_atalah fica sempre vazia: a curva de Atalah não é mais usada
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

    dum = perfil.dum if perfil else None
    ultimo_registro = registros[0] if registros else None
    if dum:
        semana_atual = _calcular_semana_atual(dum)
    elif ultimo_registro:
        # Sem DUM: a semana informada na última pesagem, somada ao tempo que passou desde ela
        dias_desde = (datetime.utcnow().date() - ultimo_registro.data_registro).days
        semana_atual = max(1, min(42, int(ultimo_registro.semana_gestacional) + max(0, dias_desde) // 7))
    else:
        semana_atual = None
    altura_cm = perfil.altura_cm if perfil else None
    peso_pre = perfil.peso_pre_gestacional if perfil else None
    idade_gestante = perfil.idade if perfil else None

    # Valores pré-gestacionais
    imc_pre = calcular_imc(peso_pre, altura_cm) if (peso_pre and altura_cm) else None
    classificacao_pre = classificar_imc_pre_gestacional(imc_pre) if imc_pre else None

    # Peso atual = o da última pesagem. Sem pesagem não há avaliação: antes o app
    # usava o peso de antes da gravidez como atual e dizia "abaixo da faixa".
    peso_atual = ultimo_registro.peso_atual_kg if ultimo_registro else None
    ganho_acumulado = round(peso_atual - peso_pre, 2) if (peso_atual and peso_pre) else None
    imc_atual = calcular_imc(peso_atual, altura_cm) if (peso_atual and altura_cm) else None

    # O ganho é avaliado na semana em que a pesagem foi feita, não na de hoje
    avaliacao_ganho_ufrj = None
    if ultimo_registro is not None:
        avaliacao_ganho_ufrj = classificar_ganho_ponderal_ufrj_ms(
            semana=_semana_do_registro(ultimo_registro, dum),
            peso_atual_kg=peso_atual,
            peso_pre_kg=peso_pre,
            altura_cm=altura_cm,
            idade_gestante=idade_gestante
        )
        avaliacao_ganho_ufrj["data_pesagem"] = ultimo_registro.data_registro.isoformat()

    # A curva de Atalah foi substituída no Brasil em 2022; o campo segue no
    # contrato da API, sempre vazio, para não quebrar telas antigas.
    avaliacao_atalah = None

    # Altura uterina: a medida mais recente, avaliada na semana em que foi feita
    avaliacao_au = None
    com_au = next((r for r in registros if r.altura_uterina_cm), None)
    if com_au is not None:
        avaliacao_au = avaliar_altura_uterina(_semana_do_registro(com_au, dum), com_au.altura_uterina_cm)
        if avaliacao_au:
            avaliacao_au["data_medida"] = com_au.data_registro.isoformat()

    # Alertas: pressão (a anotação mais recente), inchaço e ritmo de ganho da última pesagem
    alertas = []
    com_pressao = next((r for r in registros if r.pressao_arterial), None)
    if com_pressao is not None:
        pressao = avaliar_pressao_arterial(com_pressao.pressao_arterial, com_pressao.data_registro)
        if pressao and pressao["nivel"] != "nenhum":
            alertas.append(pressao)
    if ultimo_registro is not None:
        edema = avaliar_edema(ultimo_registro.edema)
        if edema:
            alertas.append(edema)
    alerta_ganho_subito = False
    mensagem_alerta = None
    if len(registros) >= 2:
        ritmo = avaliar_ritmo_de_ganho(
            registros[0].peso_atual_kg, registros[0].data_registro,
            registros[1].peso_atual_kg, registros[1].data_registro,
            _semana_do_registro(registros[0], dum),
        )
        if ritmo:
            alertas.append(ritmo)
            alerta_ganho_subito = True
            mensagem_alerta = f"{ritmo['titulo']}. {ritmo['orientacao']}"
    ordem = {"urgente": 0, "atencao": 1}
    alertas.sort(key=lambda a: ordem.get(a["nivel"], 2))

    # Gráfico: faixa recomendada (pelo IMC de antes da gravidez) e os pontos de cada pesagem
    categoria = categoria_por_imc(imc_pre) if imc_pre else None
    curva = curva_ganho_recomendada(categoria) if categoria else None
    pontos_ganho = []
    if peso_pre:
        for reg in sorted(registros, key=lambda r: (r.data_registro, r.id)):
            pontos_ganho.append({
                "data": reg.data_registro.isoformat(),
                "semana": _semana_do_registro(reg, dum),
                "ganho_kg": round(reg.peso_atual_kg - peso_pre, 2),
            })

    exames = db.query(Exame).filter(Exame.gestante_id == gestante.id).all()

    return PainelAntropometriaResponse(
        altura_cm=altura_cm,
        peso_pre_gestacional=peso_pre,
        imc_pre_gestacional=imc_pre,
        classificacao_pre_gestacional=classificacao_pre,
        peso_atual_kg=peso_atual,
        ganho_peso_acumulado_kg=ganho_acumulado,
        imc_atual=imc_atual,
        semana_gestacional_atual=semana_atual,
        avaliacao_ganho_ufrj=avaliacao_ganho_ufrj,
        avaliacao_atalah=avaliacao_atalah,
        avaliacao_altura_uterina=avaliacao_au,
        historico_registros=registros,
        guia_educativo=obter_guia_educativo_antropometria(exames=exames),
        alerta_ganho_subito=alerta_ganho_subito,
        mensagem_alerta=mensagem_alerta,
        alertas=alertas,
        semana_pela_dum=bool(dum),
        curva_ganho_recomendada=curva,
        pontos_ganho=pontos_ganho,
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
        # Antes, sem cadastro clínico, o sistema INVENTAVA idade 28 e uma DUM de
        # 24 semanas atrás. Agora pede o cadastro clínico primeiro.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Complete primeiro o cadastro clínico (data da última menstruação e idade) para registrar altura e peso."
        )
    perfil.altura_cm = payload.altura_cm
    perfil.peso_pre_gestacional = payload.peso_pre_gestacional
    db.commit()
    db.refresh(perfil)

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
    hoje = datetime.utcnow().date()
    data_reg = payload.data_registro or hoje
    if data_reg > hoje:
        raise HTTPException(status_code=422, detail="A data da medida não pode estar no futuro.")

    perfil = db.query(PerfilClinico).filter(PerfilClinico.gestante_id == gestante.id).first()
    dum = perfil.dum if perfil else None
    semana = payload.semana_gestacional
    if dum:
        if data_reg < dum:
            raise HTTPException(status_code=422, detail="A data da medida é anterior à data da última menstruação.")
        # Com DUM, a semana vem da data: a tela sugeria 24 semanas e muita gente salvava assim
        semana = max(1, min(44, semana_na_data(dum, data_reg)))

    pressao_txt = None
    if payload.pressao_arterial and payload.pressao_arterial.strip():
        leitura = ler_pressao_arterial(payload.pressao_arterial)
        if leitura is None:
            raise HTTPException(
                status_code=422,
                detail="Não entendi a pressão. Escreva como 120/80 (ou 12 por 8), com a máxima primeiro.",
            )
        pressao_txt = f"{leitura[0]}/{leitura[1]}"

    anterior = (
        db.query(RegistroAntropometrico)
        .filter(RegistroAntropometrico.gestante_id == gestante.id, RegistroAntropometrico.data_registro <= data_reg)
        .order_by(RegistroAntropometrico.data_registro.desc(), RegistroAntropometrico.id.desc())
        .first()
    )

    novo_reg = RegistroAntropometrico(
        gestante_id=gestante.id,
        data_registro=data_reg,
        semana_gestacional=semana,
        peso_atual_kg=payload.peso_atual_kg,
        altura_uterina_cm=payload.altura_uterina_cm,
        circunferencia_abdominal_cm=payload.circunferencia_abdominal_cm,
        pressao_arterial=pressao_txt,
        edema=payload.edema or "ausente",
        observacoes=payload.observacoes
    )
    db.add(novo_reg)
    db.commit()
    db.refresh(novo_reg)

    resposta = RegistroAntropometricoOut.model_validate(novo_reg).model_dump()
    resposta["alertas"] = _alertas_do_registro(novo_reg, anterior, dum)
    return resposta

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
