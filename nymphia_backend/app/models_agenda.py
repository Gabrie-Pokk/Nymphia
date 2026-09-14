from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Boolean
from sqlalchemy.sql import func
from app.db import Base


class EventoAgenda(Base):
    __tablename__ = "eventos_agenda"

    id = Column(Integer, primary_key=True, index=True)
    gestante_id = Column(String, ForeignKey("gestantes.id"), nullable=False, index=True)
    tipo = Column(String, nullable=False)  # consulta | medicacao | vacina | exame | marco
    titulo = Column(String, nullable=False)
    data_hora = Column(DateTime(timezone=True), nullable=False, index=True)
    notas = Column(String, default="")
    concluido = Column(Boolean, default=False)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

    def as_dict(self):
        return {
            "id": self.id,
            "tipo": self.tipo,
            "titulo": self.titulo,
            "data_hora": self.data_hora.isoformat() if self.data_hora else None,
            "notas": self.notas,
            "concluido": self.concluido,
        }
