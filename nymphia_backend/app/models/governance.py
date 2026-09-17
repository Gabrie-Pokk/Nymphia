from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class ObservacaoProfissional(Base):
    """
    Observações do médico - campo próprio, NUNCA edita o registro da gestante
    """
    __tablename__ = "observacoes_profissionais"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profissional_id = Column(String(36), ForeignKey("profissionais.id", ondelete="CASCADE"), nullable=False)
    gestante_id = Column(String(36), ForeignKey("gestantes.id", ondelete="CASCADE"), nullable=False)
    observacao = Column(Text, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    profissional = relationship("Profissional", back_populates="observacoes")
    gestante = relationship("Gestante", back_populates="observacoes_medicas")


class CalibracaoClinica(Base):
    """
    Roadmap 2027 V3: Ajuste de limiar por condição com registro de justificativa
    """
    __tablename__ = "calibracoes_clinicas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    condicao = Column(String(100), nullable=False)
    limiar_chave = Column(String(100), nullable=False)
    limiar_valor = Column(Float, nullable=False)
    unidade = Column(String(20), nullable=False)
    justificativa = Column(Text, nullable=False)
    atualizado_por = Column(String(100), nullable=False)
    atualizado_em = Column(DateTime, default=datetime.utcnow, nullable=False)


class IntegracaoLaboratorial(Base):
    """
    Roadmap 2027 V3: Integração laboratorial com padrão FHIR / HL7
    """
    __tablename__ = "integracoes_laboratoriais"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gestante_id = Column(String(36), ForeignKey("gestantes.id", ondelete="CASCADE"), nullable=False)
    fhir_resource_type = Column(String(50), default="DiagnosticReport", nullable=False)
    fhir_identifier = Column(String(100), nullable=False)
    conteudo_fhir = Column(JSON, nullable=False)
    status_processamento = Column(String(50), default="processado", nullable=False)
    recebido_em = Column(DateTime, default=datetime.utcnow, nullable=False)
