from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Vinculo(Base):
    __tablename__ = "vinculos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gestante_id = Column(String(36), ForeignKey("gestantes.id", ondelete="CASCADE"), nullable=False, index=True)
    profissional_id = Column(String(36), ForeignKey("profissionais.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), default="pendente", nullable=False, index=True)  # pendente | ativo | revogado | recusado
    origem = Column(String(20), default="convite", nullable=False)  # convite | solicitacao | qrcode
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)
    respondido_em = Column(DateTime, nullable=True)

    gestante = relationship("Gestante", back_populates="vinculos")
    profissional = relationship("Profissional", back_populates="vinculos")


class CodigoConvite(Base):
    __tablename__ = "codigos_convite"

    codigo = Column(String(8), primary_key=True)  # 8 chars uppercase
    profissional_id = Column(String(36), ForeignKey("profissionais.id", ondelete="CASCADE"), nullable=False)
    usado = Column(Boolean, default=False, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)
    expira_em = Column(DateTime, nullable=False)

    profissional = relationship("Profissional", back_populates="codigos_convite")


class VinculoParceiro(Base):
    __tablename__ = "vinculos_parceiro"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gestante_id = Column(String(36), ForeignKey("gestantes.id", ondelete="CASCADE"), nullable=False, index=True)
    parceiro_id = Column(String(36), ForeignKey("parceiros.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), default="ativo", nullable=False)  # pendente | ativo | revogado
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    gestante = relationship("Gestante", back_populates="vinculos_parceiro")
    parceiro = relationship("Parceiro", back_populates="vinculos")


class LogAcesso(Base):
    __tablename__ = "logs_acesso"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gestante_id = Column(String(36), ForeignKey("gestantes.id", ondelete="CASCADE"), nullable=False, index=True)
    acessado_por_id = Column(String(36), nullable=False)
    acessado_por_tipo = Column(String(20), nullable=False)  # profissional | parceiro
    recurso = Column(String(100), nullable=False)
    data_hora = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    gestante = relationship("Gestante", back_populates="logs_acesso")
