
class PlanoTipo:
    FREE = "free"
    PREMIUM = "premium"
    PREMIUM_PLUS = "premium_plus"
    CLINICA = "clinica"

class StatusAssinatura:
    ATIVA = "ativa"
    PENDENTE = "pendente"
    CANCELADA = "cancelada"
    INADIMPLENTE = "inadimplente"

from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Assinatura(Base):
    __tablename__ = "assinaturas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(String(36), ForeignKey("gestantes.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    plano = Column(String(50), default="free", nullable=False)  # free | premium | premium_plus | clinica
    status = Column(String(50), default="ativa", nullable=False)  # ativa | pendente | cancelada | inadimplente
    valor_mensal = Column(Float, default=0.0, nullable=False)
    mercado_pago_subscription_id = Column(String(100), nullable=True, index=True)
    mercado_pago_payer_id = Column(String(100), nullable=True)
    forma_pagamento = Column(String(50), nullable=True)  # pix | cartao_credito | boleto
    iniciada_em = Column(DateTime, default=datetime.utcnow, nullable=False)
    expira_em = Column(DateTime, nullable=True)
    proxima_cobranca = Column(DateTime, nullable=True)
    cancelada_em = Column(DateTime, nullable=True)
    inadimplente_desde = Column(DateTime, nullable=True)
    ultima_atualizacao = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    gestante = relationship("Gestante")


class TransacaoPagamento(Base):
    __tablename__ = "transacoes_pagamento"

    id = Column(Integer, primary_key=True, autoincrement=True)
    assinatura_id = Column(Integer, ForeignKey("assinaturas.id", ondelete="CASCADE"), nullable=False, index=True)
    mercado_pago_payment_id = Column(String(100), nullable=True, unique=True, index=True)
    valor = Column(Float, nullable=False)
    status = Column(String(50), nullable=False)  # approved | pending | rejected | refunded
    metodo_pagamento = Column(String(50), nullable=True)  # pix | credit_card
    detalhes = Column(Text, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    assinatura = relationship("Assinatura")
