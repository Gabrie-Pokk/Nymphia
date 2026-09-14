"""
Nymphia Backend -- API principal

Serve os modelos treinados (Random Forest x6, Isolation Forest,
BERTimbau) pro app consumir. Roda com:

    uvicorn app.main:app --reload --port 8000

Documentação interativa automática em /docs assim que subir.
"""
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app import modelos
from app.db import get_db, criar_tabelas
from app.models_db import CheckinRegistro
from app import models_perfis  # garante que as tabelas de perfil registram no Base antes de criar_tabelas()
from app import models_agenda
from app.rotas_perfis import router as router_perfis
from app.rotas_agenda import router as router_agenda
from app.regras_checkin import classificar_checkin
from app.schemas import (
    DadosGestante, DadosInternacao, CheckinTexto,
    RespostaRiscoGestante, RiscoCondicao,
    RespostaCheckin, CategoriaDetectada,
    RespostaAnomalia,
    CheckinCompleto, CheckinRegistrado, CheckinHistoricoItem,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nymphia.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Carregando modelos...")
    modelos.carregar_todos()
    logger.info(f"Modelos RF disponíveis: {modelos.modelos_rf_disponiveis()}")
    logger.info(f"BERTimbau disponível: {modelos.bertimbau_disponivel()}")
    logger.info("Criando tabelas do banco de dados (se não existirem)...")
    criar_tabelas()
    yield


app = FastAPI(
    title="Nymphia -- API de IA",
    description="Serve os modelos de risco clínico, detecção de anomalia e análise de check-in emocional.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS aberto pro app React Native consumir durante desenvolvimento --
# restrinja allow_origins em produção.
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

app.include_router(router_perfis)
app.include_router(router_agenda)


def _nivel(prob: float) -> str:
    if prob >= 0.6:
        return "alto"
    if prob >= 0.3:
        return "moderado"
    return "baixo"


@app.get("/health")
def health():
    return {
        "status": "ok",
        "modelos_rf_disponiveis": modelos.modelos_rf_disponiveis(),
        "isolation_forest_disponivel": modelos._estado["isolation_forest"] is not None,
        "bertimbau_disponivel": modelos.bertimbau_disponivel(),
    }


@app.post("/risco/gestante", response_model=RespostaRiscoGestante)
def risco_gestante(dados: DadosGestante):
    """Roda os modelos treinados em SINASC (bem-estar fetal e
    malformação) -- usados no onboarding e a cada atualização de
    dados estruturados da gestante."""
    base = {
        "IDADEMAE": dados.idade_mae,
        "ESTCIVMAE": dados.estado_civil,
        "ESCMAE": dados.escolaridade,
        "QTDGESTANT": dados.qtd_gestacoes_anteriores,
        "QTDPARTNOR": dados.qtd_partos_normais,
        "QTDPARTCES": dados.qtd_partos_cesarea,
        "QTDFILMORT": dados.qtd_filhos_perdidos,
        "GRAVIDEZ": dados.tipo_gravidez,
        "CONSULTAS": dados.qtd_consultas_prenatal,
        "MESPRENAT": dados.mes_inicio_prenatal,
        "LOCNASC": dados.local_nascimento_previsto,
        "leitos_obst_compl_exist": dados.leitos_obstetricos_estabelecimento or 0,
        "leitos_obst_compl_sus": dados.leitos_obstetricos_sus or 0,
    }

    riscos, indisponiveis = [], []

    prob = modelos.prever_rf("bem_estar_fetal", base)
    if prob is not None:
        riscos.append(RiscoCondicao(condicao="bem_estar_fetal", probabilidade=prob, nivel=_nivel(prob)))
    else:
        indisponiveis.append("bem_estar_fetal")

    # Malformação precisa de campos pós-parto -- só roda se todos vieram preenchidos
    if None not in (dados.tipo_parto, dados.apgar_1min, dados.apgar_5min,
                     dados.peso_nascer_gramas, dados.semanas_gestacao_no_parto):
        base_malform = {
            **base,
            "GESTACAO": dados.semanas_gestacao_no_parto,
            "SEMAGESTAC": dados.semanas_gestacao_no_parto,
            "PARTO": dados.tipo_parto,
            "APGAR1": dados.apgar_1min,
            "APGAR5": dados.apgar_5min,
            "PESO": dados.peso_nascer_gramas,
        }
        prob = modelos.prever_rf("malformacao", base_malform)
        if prob is not None:
            riscos.append(RiscoCondicao(condicao="malformacao", probabilidade=prob, nivel=_nivel(prob)))
        else:
            indisponiveis.append("malformacao")

    if not riscos and not indisponiveis:
        raise HTTPException(status_code=503, detail="Nenhum modelo de risco disponível no momento.")

    return RespostaRiscoGestante(riscos=riscos, modelos_indisponiveis=indisponiveis)


@app.post("/risco/internacao", response_model=RespostaRiscoGestante)
def risco_internacao(dados: DadosInternacao):
    """Roda os modelos treinados em SIH (pré-eclâmpsia, eclâmpsia,
    diabetes gestacional, ITU) -- pensados pra sinalizar padrão de
    risco a partir de dados demográficos básicos."""
    base = {
        "IDADE": dados.idade,
        "SEXO": dados.sexo,
        "UF_ZI": dados.uf_zi or 0,
        "MUNIC_RES": dados.municipio_residencia or 0,
    }
    riscos, indisponiveis = [], []
    for condicao in ["pre_eclampsia", "eclampsia", "diabetes_gestacional", "itu"]:
        prob = modelos.prever_rf(condicao, base)
        if prob is not None:
            riscos.append(RiscoCondicao(condicao=condicao, probabilidade=prob, nivel=_nivel(prob)))
        else:
            indisponiveis.append(condicao)

    if not riscos and not indisponiveis:
        raise HTTPException(status_code=503, detail="Nenhum modelo de risco disponível no momento.")

    return RespostaRiscoGestante(riscos=riscos, modelos_indisponiveis=indisponiveis)


def _analisar_texto_checkin(texto: str):
    """Lógica central de análise -- reaproveitada tanto por /checkin/analisar
    (só analisa) quanto por /checkin/registrar (analisa E salva)."""
    resultado_regras = classificar_checkin(texto)
    categorias = []
    for cat, trechos in resultado_regras["categorias"].items():
        if cat == "neutro_sem_sinal_claro":
            continue
        categorias.append(CategoriaDetectada(categoria=cat, fonte="regras", trechos=trechos))

    bert_disponivel = modelos.bertimbau_disponivel()
    probs_bertimbau = None
    if bert_disponivel:
        probs_bertimbau = modelos.prever_bertimbau(texto)
        for cat, p in probs_bertimbau.items():
            if p >= 0.5:
                ja_tem = any(c.categoria == cat and c.fonte == "regras" for c in categorias)
                categorias.append(CategoriaDetectada(
                    categoria=cat, fonte="bertimbau", confianca=round(p, 3),
                    trechos=[] if not ja_tem else None,
                ))

    if not categorias:
        categorias.append(CategoriaDetectada(categoria="neutro_sem_sinal_claro", fonte="regras"))

    alerta = resultado_regras["alerta_sintoma_fisico"]
    recomendacao = (
        "Sinal de possível urgência física detectado -- oriente contato médico imediato."
        if alerta else
        "Sem sinal de urgência física no texto. Sinais emocionais, se houver, seguem no acompanhamento normal."
    )
    return {
        "categorias": categorias,
        "alerta": alerta,
        "bert_disponivel": bert_disponivel,
        "recomendacao": recomendacao,
        "probs_bertimbau": probs_bertimbau,
        "categorias_regras_nomes": [c for c in resultado_regras["categorias"].keys() if c != "neutro_sem_sinal_claro"],
    }


@app.post("/checkin/analisar", response_model=RespostaCheckin)
def checkin_analisar(payload: CheckinTexto):
    """Analisa o texto livre do check-in diário, SEM salvar. Útil pra
    pré-visualização, ou quando quem chama não tem gestante_id ainda."""
    r = _analisar_texto_checkin(payload.texto)
    return RespostaCheckin(
        categorias=r["categorias"],
        alerta_sintoma_fisico=r["alerta"],
        bertimbau_disponivel=r["bert_disponivel"],
        recomendacao=r["recomendacao"],
    )


@app.post("/checkin/registrar", response_model=CheckinRegistrado)
def checkin_registrar(payload: CheckinCompleto, db: Session = Depends(get_db)):
    """Analisa E persiste o check-in completo, com data e hora geradas
    pelo servidor. Esta é a peça que faltava pra agenda, pro painel do
    médico e pro treino real do LSTM -- cada chamada aqui vira um ponto
    na série temporal daquela gestante."""
    r = _analisar_texto_checkin(payload.descricao) if payload.descricao.strip() else {
        "categorias": [], "alerta": [], "bert_disponivel": modelos.bertimbau_disponivel(),
        "recomendacao": "Sem texto livre neste check-in.", "probs_bertimbau": None,
        "categorias_regras_nomes": [],
    }

    registro = CheckinRegistro(
        gestante_id=payload.gestante_id,
        humor=payload.humor,
        descricao=payload.descricao,
        sintomas=payload.sintomas,
        movimentos_bebe=payload.movimentos_bebe,
        semana_gestacional=payload.semana_gestacional,
        categorias_bertimbau=r["probs_bertimbau"],
        categorias_regras=r["categorias_regras_nomes"],
        alerta_sintoma_fisico=r["alerta"],
        score_anomalia=None,  # calculado à parte, via /anomalia/detectar, se o onboarding já rodou
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)

    return CheckinRegistrado(
        id=registro.id,
        data_hora=registro.data_hora.isoformat(),
        categorias=r["categorias"],
        alerta_sintoma_fisico=r["alerta"],
        bertimbau_disponivel=r["bert_disponivel"],
        recomendacao=r["recomendacao"],
    )


@app.get("/checkin/historico/{gestante_id}", response_model=list[CheckinHistoricoItem])
def checkin_historico(gestante_id: str, limite: int = 90, db: Session = Depends(get_db)):
    """Retorna o histórico de check-ins de uma gestante, do mais recente
    pro mais antigo -- é isso que alimenta a agenda, o painel do médico
    e, no futuro, o treino do LSTM."""
    registros = (
        db.query(CheckinRegistro)
        .filter(CheckinRegistro.gestante_id == gestante_id)
        .order_by(CheckinRegistro.data_hora.desc())
        .limit(limite)
        .all()
    )
    return [CheckinHistoricoItem(**r.as_dict()) for r in registros]


@app.post("/anomalia/detectar", response_model=RespostaAnomalia)
def anomalia_detectar(dados: DadosGestante):
    """Roda o Isolation Forest sobre os mesmos dados estruturados do
    onboarding -- detecta padrão atípico mesmo sem bater com nenhuma
    categoria de risco catalogada."""
    base = {
        "IDADEMAE": dados.idade_mae,
        "ESTCIVMAE": dados.estado_civil,
        "ESCMAE": dados.escolaridade,
        "QTDGESTANT": dados.qtd_gestacoes_anteriores,
        "QTDPARTNOR": dados.qtd_partos_normais,
        "QTDPARTCES": dados.qtd_partos_cesarea,
        "QTDFILMORT": dados.qtd_filhos_perdidos,
        "GRAVIDEZ": dados.tipo_gravidez,
        "CONSULTAS": dados.qtd_consultas_prenatal,
        "MESPRENAT": dados.mes_inicio_prenatal,
        "LOCNASC": dados.local_nascimento_previsto,
        "leitos_obst_compl_exist": dados.leitos_obstetricos_estabelecimento or 0,
        "leitos_obst_compl_sus": dados.leitos_obstetricos_sus or 0,
    }
    resultado = modelos.prever_anomalia(base)
    if resultado is None:
        return RespostaAnomalia(anomalia_detectada=False, score=0.0, modelo_disponivel=False)
    return RespostaAnomalia(
        anomalia_detectada=resultado["anomalo"], score=resultado["score"], modelo_disponivel=True,
    )


# ============================================================
# Emergência
# ============================================================
LOG_EMERGENCIAS = os.environ.get("NYMPHIA_LOG_EMERGENCIAS", "emergencias.log")


@app.post("/emergencia/notificar")
def emergencia_notificar(payload: dict):
    """Registra o evento de emergência assim que a tela abre no app.

    ATENÇÃO -- isto é um estágio inicial, não a funcionalidade completa:
    hoje só GRAVA o evento em log. Ainda NÃO envia notificação push real
    pro médico vinculado, porque duas peças da arquitetura ainda não
    existem: (1) a tabela de vínculo gestante-médico com consentimento,
    e (2) o registro do token de notificação push de cada médico.

    Ambas estão especificadas na seção 7 da Especificação Funcional v2,
    como pré-requisito desta funcionalidade ficar completa. Por ora, a
    função prova o contrato do endpoint e garante que o app nunca trava
    esperando resposta daqui -- o socorro real (SAMU) nunca depende
    deste endpoint funcionar.
    """
    momento = payload.get("momento", datetime.now(timezone.utc).isoformat())
    linha = f"{momento} -- evento de emergência registrado\n"
    try:
        with open(LOG_EMERGENCIAS, "a", encoding="utf-8") as f:
            f.write(linha)
        logger.info(f"Emergência registrada: {momento}")
    except Exception as e:
        # Mesmo se o log falhar, a resposta continua sendo 200 -- o app
        # do lado da gestante não pode travar por causa disso.
        logger.warning(f"Falha ao registrar emergência: {e}")
    return {"status": "registrado", "notificacao_medico": "pendente -- vínculo ainda não implementado"}
