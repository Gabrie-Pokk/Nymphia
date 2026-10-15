from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, Date, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class PerfilClinico(Base):
    __tablename__ = "perfis_clinicos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gestante_id = Column(String(36), ForeignKey("gestantes.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    idade = Column(Integer, nullable=False)
    estado_civil = Column(String(50), nullable=True)
    escolaridade = Column(String(50), nullable=True)
    gestacoes_anteriores = Column(Integer, default=0, nullable=False)
    partos_normais = Column(Integer, default=0, nullable=False)
    partos_cesareos = Column(Integer, default=0, nullable=False)
    perdas_gestacionais = Column(Integer, default=0, nullable=False)
    # Usados pelos modelos v2 e pelos fatores clínicos (15/10/2026). Vazio = não informado.
    numero_fetos = Column(Integer, nullable=True)            # 1 único, 2 gêmeos, 3 trigêmeos ou mais
    mes_inicio_prenatal = Column(Integer, nullable=True)     # mês da gestação em que começou o pré-natal
    uf_residencia = Column(Integer, nullable=True)           # código IBGE do estado (11 a 53)
    pre_eclampsia_previa = Column(Boolean, nullable=True)
    hipertensao_cronica = Column(Boolean, nullable=True)
    diabetes_previo = Column(Boolean, nullable=True)
    dum = Column(Date, nullable=False)
    dpp = Column(Date, nullable=False)
    dpp_editada_manualmente = Column(Boolean, default=False, nullable=False)
    altura_cm = Column(Float, nullable=True)
    peso_pre_gestacional = Column(Float, nullable=True)
    maternidade_nome = Column(String(255), nullable=True)
    maternidade_endereco = Column(String(255), nullable=True)
    maternidade_telefone = Column(String(50), nullable=True)
    maternidade_latitude = Column(Float, nullable=True)
    maternidade_longitude = Column(Float, nullable=True)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    gestante = relationship("Gestante", back_populates="perfil_clinico")


class HistoricoFamiliar(Base):
    __tablename__ = "historico_familiar"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gestante_id = Column(String(36), ForeignKey("gestantes.id", ondelete="CASCADE"), nullable=False, index=True)
    parente = Column(String(50), nullable=False)  # mãe | pai | irmã | irmão | avó materna | avó paterna | avô materno | avô paterno
    condicao = Column(String(100), nullable=False)

    gestante = relationship("Gestante", back_populates="historico_familiar")


class CheckinRegistro(Base):
    __tablename__ = "checkin_registros"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gestante_id = Column(String(36), ForeignKey("gestantes.id", ondelete="CASCADE"), nullable=False, index=True)
    # Server timestamp, NEVER client device timestamp
    data_hora = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    humor = Column(Integer, nullable=False)  # 1 to 5
    descricao = Column(Text, nullable=True)
    sintomas = Column(JSON, default=list, nullable=False)
    movimentos_bebe = Column(Integer, default=0, nullable=False)
    semana_gestacional = Column(Integer, nullable=True)
    categorias_bertimbau = Column(JSON, nullable=True)
    categorias_regras = Column(JSON, default=list, nullable=False)
    alerta_sintoma_fisico = Column(JSON, default=list, nullable=False)
    # Sinais de atenção (falar com o pré-natal hoje); os urgentes ficam em alerta_sintoma_fisico
    sinais_atencao = Column(JSON, nullable=True)
    score_anomalia = Column(Float, nullable=True)

    gestante = relationship("Gestante", back_populates="checkins")


class Exame(Base):
    __tablename__ = "exames"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gestante_id = Column(String(36), ForeignKey("gestantes.id", ondelete="CASCADE"), nullable=False, index=True)
    tipo = Column(String(100), nullable=False)
    data_realizacao = Column(Date, nullable=False)
    arquivo_url = Column(String(500), nullable=False)  # Object storage URL, NEVER binary blob in db
    valores_extraidos = Column(JSON, nullable=True)
    observacoes = Column(Text, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    gestante = relationship("Gestante", back_populates="exames")


class RegistroAntropometrico(Base):
    __tablename__ = "registros_antropometricos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gestante_id = Column(String(36), ForeignKey("gestantes.id", ondelete="CASCADE"), nullable=False, index=True)
    data_registro = Column(Date, default=lambda: datetime.utcnow().date(), nullable=False)
    semana_gestacional = Column(Integer, nullable=False)
    peso_atual_kg = Column(Float, nullable=False)
    altura_uterina_cm = Column(Float, nullable=True)
    circunferencia_abdominal_cm = Column(Float, nullable=True)
    pressao_arterial = Column(String(20), nullable=True)
    edema = Column(String(20), nullable=True)  # ausente | +/4+ | ++/4+ | +++/4+ | ++++/4+
    observacoes = Column(Text, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    gestante = relationship("Gestante", back_populates="registros_antropometricos")


class TriagemEPDS(Base):
    """
    Respostas da Escala de Edimburgo (EPDS). Guarda a posição de cada resposta e
    os pontos dados pela chave da escala; o texto das perguntas não é guardado.
    Dado de saúde mental: só a gestante e o profissional com vínculo ativo veem.
    """
    __tablename__ = "triagens_epds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gestante_id = Column(String(36), ForeignKey("gestantes.id", ondelete="CASCADE"), nullable=False, index=True)
    data_hora = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)  # hora do servidor
    semana_gestacional = Column(Integer, nullable=True)
    respostas = Column(JSON, nullable=False)          # posição escolhida em cada pergunta (0 a 3)
    pontos_por_item = Column(JSON, nullable=False)    # pontos de cada pergunta pela chave da escala
    pontuacao = Column(Integer, nullable=False)       # 0 a 30
    pontos_autolesao = Column(Integer, nullable=False)  # pergunta 10
    nivel = Column(String(20), nullable=False)        # urgente | atencao | sem_sinais
    versao_questionario = Column(String(255), nullable=True)
    profissional_notificado = Column(Boolean, default=False, nullable=False)

    gestante = relationship("Gestante", back_populates="triagens_epds")
