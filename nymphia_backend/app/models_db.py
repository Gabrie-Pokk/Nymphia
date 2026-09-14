"""
Nymphia -- Modelo de dado persistido

CheckinRegistro é a peça que faltava pro LSTM, pra agenda e pro painel
do médico: cada check-in salvo aqui vira um ponto na série temporal
daquela gestante.

Nota sobre gestante_id: como o sistema de perfis/login ainda não está
implementado (é o próximo item da fila, depois deste), usamos por
enquanto um identificador anônimo gerado e guardado no próprio
aparelho da gestante. Quando o login real existir, a migração é trocar
esse campo por um ID de usuária de verdade -- o resto da estrutura
não muda.
"""
from sqlalchemy import Column, DateTime, Float, Integer, String, JSON
from sqlalchemy.sql import func

from app.db import Base


class CheckinRegistro(Base):
    __tablename__ = "checkins"

    id = Column(Integer, primary_key=True, index=True)
    gestante_id = Column(String, index=True, nullable=False)
    data_hora = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # O que a gestante preencheu
    humor = Column(Integer, nullable=False)  # 1 a 5
    descricao = Column(String, default="")
    sintomas = Column(JSON, default=list)  # lista de strings
    movimentos_bebe = Column(Integer, default=0)
    semana_gestacional = Column(Integer, nullable=True)

    # O que a IA calculou em cima disso -- é isso que vira a sequência do LSTM
    categorias_bertimbau = Column(JSON, nullable=True)  # {"ansiedade": 0.96, ...}
    categorias_regras = Column(JSON, default=list)  # lista de categorias identificadas
    alerta_sintoma_fisico = Column(JSON, default=list)  # lista de alertas, se houver
    score_anomalia = Column(Float, nullable=True)

    def as_dict(self):
        return {
            "id": self.id,
            "gestante_id": self.gestante_id,
            "data_hora": self.data_hora.isoformat() if self.data_hora else None,
            "humor": self.humor,
            "descricao": self.descricao,
            "sintomas": self.sintomas or [],
            "movimentos_bebe": self.movimentos_bebe,
            "semana_gestacional": self.semana_gestacional,
            "categorias_bertimbau": self.categorias_bertimbau,
            "categorias_regras": self.categorias_regras or [],
            "alerta_sintoma_fisico": self.alerta_sintoma_fisico or [],
            "score_anomalia": self.score_anomalia,
        }
