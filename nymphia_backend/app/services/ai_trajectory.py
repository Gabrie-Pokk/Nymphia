from typing import List, Dict, Any
import numpy as np

class LSTMTrajectoryPipeline:
    """
    Pipeline do Modelo de Trajetória (LSTM).
    Integra a evolução temporal do risco gestacional.
    Entrada: Vetores sequenciais de [semana_normalizada, prob_ansiedade, prob_tristeza,
                                     prob_estresse, prob_medo, prob_sintoma_fisico, score_anomalia].
    """

    def __init__(self, weights_path: str = None):
        self.weights_path = weights_path
        self.is_loaded = False
        if weights_path:
            self.load_model(weights_path)

    def load_model(self, weights_path: str):
        # Section 6.4 requirement:
        # Se não houver arquivo/pesos treinados longitudinais validados,
        # levanta erro explícito para impedir execução enganosa de treino/inferência.
        raise RuntimeError(
            "Modelo LSTM de Trajetória: Não há base longitudinal anotada suficiente no ambiente atual "
            "(mínimo de 3.8M sequências SINASC/SIH completas). O carregamento é bloqueado deliberadamente "
            "para evitar predições temporais fictícias ou inferências sem respaldo estatístico."
        )

    def format_input_vector(
        self,
        semana_gestacional: int,
        emocoes: Dict[str, float],
        score_anomalia: float
    ) -> List[float]:
        """
        Normaliza e formata o vetor de uma semana para a camada LSTM.
        """
        # Normalização da semana (1 a 42 semanas -> 0.0 a 1.0)
        semana_norm = min(1.0, max(0.0, (semana_gestacional or 20) / 42.0))
        vec = [
            semana_norm,
            emocoes.get("ansiedade", 0.0),
            emocoes.get("tristeza", 0.0),
            emocoes.get("estresse", 0.0),
            emocoes.get("medo", 0.0),
            emocoes.get("sintoma_fisico", 0.0),
            score_anomalia or 0.0
        ]
        return vec
