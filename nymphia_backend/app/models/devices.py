from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class MedicaoDispositivo(Base):
    __tablename__ = "medicoes_dispositivo"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gestante_id = Column(String(36), ForeignKey("gestantes.id", ondelete="CASCADE"), nullable=False, index=True)
    tipo = Column(String(50), nullable=False)  # pressao_arterial | glicemia
    sistolica = Column(Integer, nullable=True)
    diastolica = Column(Integer, nullable=True)
    glicemia = Column(Float, nullable=True)
    data_hora = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    origem = Column(String(50), default="manual", nullable=False)  # dispositivo_bluetooth | manual

    gestante = relationship("Gestante", back_populates="medicoes")


class CintaNymphiaLeitura(Base):
    """
    Roadmap 2027 V3: Ingestão de batimentos cardíacos fetais contínuos (Doppler)
    """
    __tablename__ = "cinta_nymphia_leituras"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gestante_id = Column(String(36), ForeignKey("gestantes.id", ondelete="CASCADE"), nullable=False, index=True)
    bpm = Column(Integer, nullable=False)
    status = Column(String(20), default="normal", nullable=False)  # normal | taquicardia | bradicardia | atipico
    data_hora = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    gestante = relationship("Gestante", back_populates="leituras_cinta")
