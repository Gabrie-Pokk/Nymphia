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
    ocultado = Column(Boolean, default=False, nullable=False)
    motivo_ocultacao = Column(String(255), nullable=True)
    revisado_por_humano = Column(Boolean, default=False, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    gestante = relationship("Gestante", back_populates="posts")
    comentarios = relationship("ComentarioComunidade", back_populates="post", cascade="all, delete-orphan")
    denuncias = relationship("DenunciaComunidade", back_populates="post", cascade="all, delete-orphan")
    recursos = relationship("RecursoModeracao", back_populates="post", cascade="all, delete-orphan")


class ComentarioComunidade(Base):
    __tablename__ = "comentarios_comunidade"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts_comunidade.id", ondelete="CASCADE"), nullable=False)
    gestante_id = Column(String(36), ForeignKey("gestantes.id", ondelete="CASCADE"), nullable=False)
    apelido = Column(String(50), nullable=False)
    conteudo = Column(Text, nullable=False)
    sinalizado = Column(Boolean, default=False, nullable=False)
    ocultado = Column(Boolean, default=False, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    post = relationship("PostComunidade", back_populates="comentarios")
    gestante = relationship("Gestante", back_populates="comentarios")
    denuncias = relationship("DenunciaComunidade", back_populates="comentario", cascade="all, delete-orphan")


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


class DenunciaComunidade(Base):
    """
    Registro estruturado de denúncias de conteúdo da comunidade (STF Tema 987 & Marco Civil).
    Permite categorização por motivo de segurança e ativação de protocolos especiais (ex: ideação/automutilação).
    """
    __tablename__ = "denuncias_comunidade"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts_comunidade.id", ondelete="CASCADE"), nullable=True)
    comentario_id = Column(Integer, ForeignKey("comentarios_comunidade.id", ondelete="CASCADE"), nullable=True)
    denunciante_id = Column(String(36), ForeignKey("gestantes.id", ondelete="SET NULL"), nullable=True)
    motivo = Column(String(100), nullable=False)  # desinformacao_saude, automedicacao, automutilacao_suicidio, violencia_assedio, comercial_spam, outro
    detalhes = Column(Text, nullable=True)
    status = Column(String(50), default="pendente", nullable=False)  # pendente, em_analise, procedente, improcedente
    acao_tomada = Column(String(255), nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    post = relationship("PostComunidade", back_populates="denuncias")
    comentario = relationship("ComentarioComunidade", back_populates="denuncias")
    denunciante = relationship("Gestante")


class RecursoModeracao(Base):
    """
    Direito ao devido processo e canal recursal de moderação de conteúdo (STF Tema 987).
    Garante que a autora de conteúdo moderado ou ocultado possa justificar e solicitar reavaliação.
    """
    __tablename__ = "recursos_moderacao"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts_comunidade.id", ondelete="CASCADE"), nullable=True)
    comentario_id = Column(Integer, ForeignKey("comentarios_comunidade.id", ondelete="CASCADE"), nullable=True)
    gestante_id = Column(String(36), ForeignKey("gestantes.id", ondelete="CASCADE"), nullable=False)
    justificativa = Column(Text, nullable=False)
    status = Column(String(50), default="pendente", nullable=False)  # pendente, deferido, indeferido
    decisao_motivo = Column(Text, nullable=True)
    revisado_em = Column(DateTime, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    post = relationship("PostComunidade", back_populates="recursos")
    gestante = relationship("Gestante")
