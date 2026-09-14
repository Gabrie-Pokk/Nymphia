"""
Nymphia Backend -- Schemas (Pydantic)

Define o formato de entrada/saída de cada endpoint. Nomes em português,
espelhando a linguagem do domínio (a mesma usada no onboarding do app).
"""
from typing import Optional
from pydantic import BaseModel, Field


class DadosGestante(BaseModel):
    """Dados estruturados coletados no onboarding -- alimentam os modelos
    de risco baseados em SINASC (bem-estar fetal e malformação)."""
    idade_mae: int = Field(..., ge=10, le=60, description="Idade da gestante em anos")
    estado_civil: int = Field(..., ge=1, le=9, description="Código SINASC de estado civil (1-5, 9=ignorado)")
    escolaridade: int = Field(..., ge=1, le=9, description="Código SINASC de escolaridade (1-5, 9=ignorado)")
    qtd_gestacoes_anteriores: int = Field(0, ge=0, le=20)
    qtd_partos_normais: int = Field(0, ge=0, le=20)
    qtd_partos_cesarea: int = Field(0, ge=0, le=20)
    qtd_filhos_perdidos: int = Field(0, ge=0, le=20)
    tipo_gravidez: int = Field(1, ge=1, le=9, description="1=única, 2=dupla, 3=tripla+, 9=ignorado")
    qtd_consultas_prenatal: int = Field(..., ge=0, le=20)
    mes_inicio_prenatal: int = Field(..., ge=0, le=9, description="Mês de gestação em que o pré-natal começou")
    local_nascimento_previsto: int = Field(1, ge=1, le=9, description="1=hospital, 2=outro estabelecimento, 3=domicílio")
    # Enriquecimento CNES do estabelecimento onde a gestante faz o pré-natal (opcional)
    leitos_obstetricos_estabelecimento: Optional[float] = Field(None, description="Preenchido pelo backend via CNES, se disponível")
    leitos_obstetricos_sus: Optional[float] = None
    # Campos adicionais usados pelo modelo de malformação (marcos do parto, se já ocorrido)
    tipo_parto: Optional[int] = Field(None, description="1=vaginal, 2=cesáreo -- só preenchido pós-parto")
    apgar_1min: Optional[int] = Field(None, ge=0, le=10)
    apgar_5min: Optional[int] = Field(None, ge=0, le=10)
    peso_nascer_gramas: Optional[int] = Field(None, ge=200, le=6000)
    semanas_gestacao_no_parto: Optional[int] = Field(None, ge=20, le=45)


class RiscoCondicao(BaseModel):
    condicao: str
    probabilidade: float = Field(..., ge=0, le=1)
    nivel: str  # "baixo" | "moderado" | "alto"


class RespostaRiscoGestante(BaseModel):
    riscos: list[RiscoCondicao]
    modelos_indisponiveis: list[str] = Field(default_factory=list, description="Modelos que não puderam rodar (arquivo ausente, etc.)")
    aviso: str = "Este resultado é um sinal de apoio à triagem, não um diagnóstico. Sempre oriente avaliação médica."


class DadosInternacao(BaseModel):
    """Dados no formato SIH -- usados pelos modelos de pré-eclâmpsia,
    eclâmpsia, diabetes gestacional e ITU."""
    idade: int = Field(..., ge=10, le=60)
    sexo: int = Field(3, description="Código SIH: 1=masculino, 3=feminino")
    uf_zi: Optional[int] = Field(None, description="Código da UF de referência, se disponível")
    municipio_residencia: Optional[int] = None


class CheckinTexto(BaseModel):
    texto: str = Field(..., min_length=1, max_length=2000)


class CategoriaDetectada(BaseModel):
    categoria: str
    fonte: str  # "regras" | "bertimbau"
    confianca: Optional[float] = None
    trechos: list[str] = Field(default_factory=list)


class RespostaCheckin(BaseModel):
    categorias: list[CategoriaDetectada]
    alerta_sintoma_fisico: list[str] = Field(default_factory=list)
    bertimbau_disponivel: bool
    recomendacao: str


class RespostaAnomalia(BaseModel):
    anomalia_detectada: bool
    score: float
    modelo_disponivel: bool


# ============================================================
# Persistência de check-in (com data e hora)
# ============================================================
class CheckinCompleto(BaseModel):
    """O que o app manda pra SALVAR um check-in -- não só analisar."""
    gestante_id: str = Field(..., min_length=1, description="Identificador anônimo gerado no aparelho")
    humor: int = Field(..., ge=1, le=5)
    descricao: str = Field("", max_length=2000)
    sintomas: list[str] = Field(default_factory=list)
    movimentos_bebe: int = Field(0, ge=0)
    semana_gestacional: Optional[int] = Field(None, ge=1, le=45)


class CheckinRegistrado(BaseModel):
    id: int
    data_hora: str
    categorias: list[CategoriaDetectada]
    alerta_sintoma_fisico: list[str]
    bertimbau_disponivel: bool
    recomendacao: str


class CheckinHistoricoItem(BaseModel):
    id: int
    data_hora: str
    humor: int
    descricao: str
    sintomas: list[str]
    movimentos_bebe: int
    semana_gestacional: Optional[int]
    categorias_bertimbau: Optional[dict]
    categorias_regras: list[str]
    alerta_sintoma_fisico: list[str]
    score_anomalia: Optional[float]


# ============================================================
# Perfis de acesso e vínculo
# ============================================================
class GestanteCadastro(BaseModel):
    nome: str = Field(..., min_length=1, max_length=200)
    email: str = Field(..., min_length=5, max_length=200)
    senha: str = Field(..., min_length=8, max_length=72, description="Mínimo 8 caracteres")


class GestanteLogin(BaseModel):
    email: str
    senha: str


class ProfissionalCadastro(BaseModel):
    nome: str = Field(..., min_length=1, max_length=200)
    email: str = Field(..., min_length=5, max_length=200)
    senha: str = Field(..., min_length=8, max_length=72)
    registro_tipo: str = Field(..., description="'CRM' ou 'COREN'")
    registro_numero: str
    registro_uf: str = Field(..., min_length=2, max_length=2)


class ProfissionalLogin(BaseModel):
    email: str
    senha: str


class TokenResposta(BaseModel):
    token: str
    perfil: str  # "gestante" | "profissional"
    id: str
    nome: str
    status_verificacao: Optional[str] = None  # só preenchido pra profissional


class ConviteGerado(BaseModel):
    codigo: str


class ConviteUsar(BaseModel):
    codigo: str


class VinculoInfo(BaseModel):
    id: int
    profissional_id: str
    profissional_nome: str
    status: str
    origem: str


class GestanteVinculada(BaseModel):
    gestante_id: str
    nome: str
    vinculo_id: int
    vinculo_status: str


class EventoCriar(BaseModel):
    tipo: str = Field(..., description="consulta | medicacao | vacina | exame | marco")
    titulo: str = Field(..., min_length=1, max_length=200)
    data_hora: str = Field(..., description="ISO 8601, ex: 2026-10-01T09:00:00")
    notas: str = Field("", max_length=1000)


class EventoResposta(BaseModel):
    id: int
    tipo: str
    titulo: str
    data_hora: str
    notas: str
    concluido: bool
