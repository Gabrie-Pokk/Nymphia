"""
Nymphia -- Perfis de acesso e vínculo com consentimento

Três tabelas novas:
  Gestante -- conta da usuária principal, cadastro autônomo
  Profissional -- conta do médico/enfermeira, com verificação pendente
  Vinculo -- a ligação entre os dois, que só a GESTANTE pode criar ou revogar

Princípio de design: o profissional nunca escreve na tabela Vinculo com
status "ativo" por conta própria -- só a gestante ativa (usando um código
de convite) ou aprova uma solicitação. Isso está refletido na própria
lógica dos endpoints em auth.py, não só documentado em texto.
"""
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.db import Base


def novo_id() -> str:
    return str(uuid.uuid4())


class Gestante(Base):
    __tablename__ = "gestantes"

    id = Column(String, primary_key=True, default=novo_id)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    senha_hash = Column(String, nullable=False)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())


class Profissional(Base):
    __tablename__ = "profissionais"

    id = Column(String, primary_key=True, default=novo_id)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    senha_hash = Column(String, nullable=False)

    registro_tipo = Column(String, nullable=False)     # "CRM" ou "COREN"
    registro_numero = Column(String, nullable=False)
    registro_uf = Column(String, nullable=False)

    # Modelo decidido: upload de documento + conferência posterior.
    # Acesso já é liberado no cadastro (status "pendente"); suspende-se
    # depois se a conferência manual encontrar irregularidade.
    status_verificacao = Column(String, default="pendente")  # pendente | aprovado | rejeitado
    documento_comprovante_path = Column(String, nullable=True)

    criado_em = Column(DateTime(timezone=True), server_default=func.now())


class Vinculo(Base):
    __tablename__ = "vinculos"

    id = Column(Integer, primary_key=True, index=True)
    gestante_id = Column(String, ForeignKey("gestantes.id"), nullable=False, index=True)
    profissional_id = Column(String, ForeignKey("profissionais.id"), nullable=False, index=True)

    # pendente (aguardando resposta da gestante) | ativo | revogado | recusado
    status = Column(String, default="pendente", index=True)
    origem = Column(String, nullable=False)  # "convite" | "solicitacao" | "qrcode"

    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    respondido_em = Column(DateTime(timezone=True), nullable=True)


class CodigoConvite(Base):
    """Código gerado pelo profissional -- vira vínculo ativo assim que
    uma gestante o utiliza. O ato de digitar o código É o consentimento
    dela; não precisa de segunda aprovação."""
    __tablename__ = "codigos_convite"

    codigo = Column(String, primary_key=True)
    profissional_id = Column(String, ForeignKey("profissionais.id"), nullable=False)
    usado = Column(String, default="nao")  # "nao" | "sim" -- string por simplicidade no SQLite
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
