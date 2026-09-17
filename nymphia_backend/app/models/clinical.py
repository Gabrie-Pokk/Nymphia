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
    dum = Column(Date, nullable=False)
    dpp = Column(Date, nullable=False)
    dpp_editada_manualmente = Column(Boolean, default=False, nullable=False)
    maternidade_nome = Column(String(255), nullable=True)
    maternidade_endereco = Column(String(255), nullable=True)
    maternidade_telefone = Column(String(50), nullable=True)
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
