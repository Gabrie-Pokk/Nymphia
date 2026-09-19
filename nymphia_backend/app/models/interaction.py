from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class Mensagem(Base):
    __tablename__ = "mensagens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gestante_id = Column(String(36), ForeignKey("gestantes.id", ondelete="CASCADE"), nullable=False, index=True)
    papel = Column(String(20), nullable=False)  # gestante | ia
    conteudo = Column(Text, nullable=False)
    data_hora = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    alerta_emergencia = Column(Boolean, default=False, nullable=False)
    autorizado_compartilhar = Column(Boolean, default=False, nullable=False)

    gestante = relationship("Gestante", back_populates="mensagens")


class EventoAgenda(Base):
    __tablename__ = "eventos_agenda"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gestante_id = Column(String(36), ForeignKey("gestantes.id", ondelete="CASCADE"), nullable=False, index=True)
    tipo = Column(String(50), nullable=False)  # consulta | medicacao | vacina | exame | marco
    titulo = Column(String(255), nullable=False)
    data_hora = Column(DateTime, nullable=False, index=True)
    notas = Column(Text, nullable=True)
    concluido = Column(Boolean, default=False, nullable=False)
    recorrencia = Column(String(50), nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    gestante = relationship("Gestante", back_populates="eventos_agenda")


class EventoEmergencia(Base):
    __tablename__ = "eventos_emergencia"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gestante_id = Column(String(36), ForeignKey("gestantes.id", ondelete="CASCADE"), nullable=False, index=True)
    data_hora = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    contexto = Column(JSON, default=dict, nullable=False)
    profissional_notificado = Column(Boolean, default=False, nullable=False)

    gestante = relationship("Gestante", back_populates="eventos_emergencia")


class QuizGostosGestante(Base):
    __tablename__ = "quiz_gostos_gestante"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gestante_id = Column(String(36), ForeignKey("gestantes.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    respondido_por = Column(String(50), default="gestante", nullable=False)  # 'gestante' ou 'parceiro'
    nome_respondente = Column(String(100), nullable=True)
    respostas_json = Column(Text, nullable=False)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    gestante = relationship("Gestante")

