import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, Date, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class Gestante(Base):
    __tablename__ = "gestantes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nome = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    recusa_ia = Column(Boolean, default=False)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    perfil_clinico = relationship("PerfilClinico", back_populates="gestante", uselist=False, cascade="all, delete-orphan")
    historico_familiar = relationship("HistoricoFamiliar", back_populates="gestante", cascade="all, delete-orphan")
    checkins = relationship("CheckinRegistro", back_populates="gestante", cascade="all, delete-orphan")
    mensagens = relationship("Mensagem", back_populates="gestante", cascade="all, delete-orphan")
    eventos_agenda = relationship("EventoAgenda", back_populates="gestante", cascade="all, delete-orphan")
    exames = relationship("Exame", back_populates="gestante", cascade="all, delete-orphan")
    eventos_emergencia = relationship("EventoEmergencia", back_populates="gestante", cascade="all, delete-orphan")
    vinculos = relationship("Vinculo", back_populates="gestante", cascade="all, delete-orphan")
    vinculos_parceiro = relationship("VinculoParceiro", back_populates="gestante", cascade="all, delete-orphan")
    posts = relationship("PostComunidade", back_populates="gestante", cascade="all, delete-orphan")
    comentarios = relationship("ComentarioComunidade", back_populates="gestante", cascade="all, delete-orphan")
    logs_acesso = relationship("LogAcesso", back_populates="gestante", cascade="all, delete-orphan")
    medicoes = relationship("MedicaoDispositivo", back_populates="gestante", cascade="all, delete-orphan")
    observacoes_medicas = relationship("ObservacaoProfissional", back_populates="gestante", cascade="all, delete-orphan")


class Profissional(Base):
    __tablename__ = "profissionais"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nome = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    registro_tipo = Column(String(10), nullable=False)  # CRM | COREN
    registro_numero = Column(String(50), nullable=False)
    registro_uf = Column(String(2), nullable=False)
    documento_comprovante_path = Column(String(500), nullable=True)
    status_verificacao = Column(String(20), default="pendente", nullable=False)  # pendente | aprovado | rejeitado
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    vinculos = relationship("Vinculo", back_populates="profissional", cascade="all, delete-orphan")
    codigos_convite = relationship("CodigoConvite", back_populates="profissional", cascade="all, delete-orphan")
    observacoes = relationship("ObservacaoProfissional", back_populates="profissional", cascade="all, delete-orphan")


class Parceiro(Base):
    __tablename__ = "parceiros"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nome = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    vinculos = relationship("VinculoParceiro", back_populates="parceiro", cascade="all, delete-orphan")
