from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class PostComunidade(Base):
    __tablename__ = "posts_comunidade"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gestante_id = Column(String(36), ForeignKey("gestantes.id", ondelete="CASCADE"), nullable=False)
    apelido = Column(String(50), nullable=False)  # Pseudônimo protetivo anônimo
    grupo = Column(String(100), nullable=False)
    conteudo = Column(Text, nullable=False)
    sinalizado = Column(Boolean, default=False, nullable=False)
    motivo_sinalizacao = Column(String(255), nullable=True)
    revisado_por_humano = Column(Boolean, default=False, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    gestante = relationship("Gestante", back_populates="posts")
    comentarios = relationship("ComentarioComunidade", back_populates="post", cascade="all, delete-orphan")


class ComentarioComunidade(Base):
    __tablename__ = "comentarios_comunidade"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts_comunidade.id", ondelete="CASCADE"), nullable=False)
    gestante_id = Column(String(36), ForeignKey("gestantes.id", ondelete="CASCADE"), nullable=False)
    apelido = Column(String(50), nullable=False)
    conteudo = Column(Text, nullable=False)
    sinalizado = Column(Boolean, default=False, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    post = relationship("PostComunidade", back_populates="comentarios")
    gestante = relationship("Gestante", back_populates="comentarios")


class PreferenciasComunidade(Base):
    __tablename__ = "preferencias_comunidade"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gestante_id = Column(String(36), ForeignKey("gestantes.id", ondelete="CASCADE"), nullable=False, unique=True)
    experiencia = Column(String(100), nullable=True)  # ex: Primeira gestação, Já tenho filhos
    preferencia_parto = Column(String(100), nullable=True)  # ex: Parto humanizado, Cesárea planejada
    interesses = Column(Text, nullable=True)  # JSON codificado de interesses
    estilo_vida = Column(String(100), nullable=True)  # ex: Prática, Tranquila, Estudiosa
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    gestante = relationship("Gestante")
