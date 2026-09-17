from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict

# --- Auth Schemas ---
class GestanteRegister(BaseModel):
    nome: str = Field(..., min_length=3)
    email: EmailStr
    senha: str = Field(..., min_length=8)
    recusa_ia: bool = False

class GestanteLogin(BaseModel):
    email: EmailStr
    senha: str

class ProfissionalRegister(BaseModel):
    nome: str = Field(..., min_length=3)
    email: EmailStr
    senha: str = Field(..., min_length=8)
    registro_tipo: str = Field(..., pattern="^(CRM|COREN)$")
    registro_numero: str
    registro_uf: str = Field(..., min_length=2, max_length=2)

class ProfissionalLogin(BaseModel):
    email: EmailStr
    senha: str

class ParceiroRegister(BaseModel):
    nome: str = Field(..., min_length=3)
    email: EmailStr
    senha: str = Field(..., min_length=8)

class ParceiroLogin(BaseModel):
    email: EmailStr
    senha: str

class AuthResponse(BaseModel):
    token: str
    perfil: str
    id: str
    nome: str
    status_verificacao: Optional[str] = None
    recusa_ia: Optional[bool] = False

# --- Clinical Schemas ---
class PerfilClinicoBase(BaseModel):
    idade: int
    estado_civil: Optional[str] = None
    escolaridade: Optional[str] = None
    gestacoes_anteriores: int = 0
    partos_normais: int = 0
    partos_cesareos: int = 0
    perdas_gestacionais: int = 0
    dum: date
    dpp: date
    dpp_editada_manualmente: bool = False
    maternidade_nome: Optional[str] = None
    maternidade_endereco: Optional[str] = None
    maternidade_telefone: Optional[str] = None

class PerfilClinicoCreate(PerfilClinicoBase):
    pass

class PerfilClinicoUpdate(BaseModel):
    idade: Optional[int] = None
    estado_civil: Optional[str] = None
    escolaridade: Optional[str] = None
    gestacoes_anteriores: Optional[int] = None
    partos_normais: Optional[int] = None
    partos_cesareos: Optional[int] = None
    perdas_gestacionais: Optional[int] = None
    dum: Optional[date] = None
    dpp: Optional[date] = None
    dpp_editada_manualmente: Optional[bool] = None
    maternidade_nome: Optional[str] = None
    maternidade_endereco: Optional[str] = None
    maternidade_telefone: Optional[str] = None

class PerfilClinicoOut(PerfilClinicoBase):
    id: int
    gestante_id: str
    atualizado_em: datetime

    model_config = ConfigDict(from_attributes=True)

class HistoricoFamiliarCreate(BaseModel):
    parente: str  # mãe | pai | irmã | irmão | avó materna | avó paterna | avô materno | avô paterno
    condicao: str

class HistoricoFamiliarOut(BaseModel):
    id: int
    gestante_id: str
    parente: str
    condicao: str

    model_config = ConfigDict(from_attributes=True)

# --- Checkin Schemas ---
class CheckinAnalisarRequest(BaseModel):
    texto: str

class CheckinCreate(BaseModel):
    humor: int = Field(..., ge=1, le=5)
    descricao: Optional[str] = ""
    sintomas: List[str] = Field(default_factory=list)
    movimentos_bebe: int = 0
    semana_gestacional: Optional[int] = None

class CheckinOut(BaseModel):
    id: int
    data_hora: datetime
    humor: int
    descricao: Optional[str]
    sintomas: List[str]
    movimentos_bebe: int
    semana_gestacional: Optional[int]
    categorias_bertimbau: Optional[Dict[str, float]]
    categorias_regras: List[str]
    alerta_sintoma_fisico: List[str]
    score_anomalia: Optional[float]
    bertimbau_disponivel: bool = True
    recomendacao: str

    model_config = ConfigDict(from_attributes=True)

# --- Conversa Schemas ---
class ConversaEnviarRequest(BaseModel):
    texto: str

class ConversaResponse(BaseModel):
    resposta: str
    alerta_emergencia: bool
    fonte: str  # "regras_urgencia" | "base_clinica_ia" | "llm"

class MensagemOut(BaseModel):
    id: int
    papel: str
    conteudo: str
    data_hora: datetime
    alerta_emergencia: bool
    autorizado_compartilhar: bool

    model_config = ConfigDict(from_attributes=True)

# --- Agenda Schemas ---
class EventoAgendaCreate(BaseModel):
    tipo: str  # consulta | medicacao | vacina | exame | marco
    titulo: str
    data_hora: datetime
    notas: Optional[str] = ""
    recorrencia: Optional[str] = None

class EventoAgendaOut(BaseModel):
    id: int
    gestante_id: str
    tipo: str
    titulo: str
    data_hora: datetime
    notas: Optional[str]
    concluido: bool
    recorrencia: Optional[str]
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Exames Schemas ---
class ExameOut(BaseModel):
    id: int
    gestante_id: str
    tipo: str
    data_realizacao: date
    arquivo_url: str
    valores_extraidos: Optional[Dict[str, Any]]
    observacoes: Optional[str]
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Emergencia Schemas ---
class EmergenciaNotificarRequest(BaseModel):
    momento: Optional[datetime] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class EmergenciaResponse(BaseModel):
    status: str
    evento_id: int
    data_hora: datetime
    profissional_notificado: bool
    orientacao_samu: str = "Disque 192 imediatamente."

# --- Vinculo Schemas ---
class CodigoConviteOut(BaseModel):
    codigo: str
    expira_em: datetime

class UsarCodigoRequest(BaseModel):
    codigo: str

class SolicitarVinculoRequest(BaseModel):
    email_gestante: EmailStr

class ResponderVinculoRequest(BaseModel):
    aceitar: bool

class VinculoOut(BaseModel):
    id: int
    gestante_id: str
    profissional_id: str
    profissional_nome: Optional[str] = None
    gestante_nome: Optional[str] = None
    status: str
    origem: str
    criado_em: datetime
    respondido_em: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class PacientePainelItem(BaseModel):
    gestante_id: str
    nome: str
    semana_gestacional: Optional[int]
    total_alertas_30d: int
    ultimo_checkin: Optional[datetime]
    ultimo_checkin_relativo: str
    proxima_consulta: Optional[datetime]
    vinculo_id: int

# --- Parceiro Schemas ---
class ParceiroCodigoConviteOut(BaseModel):
    codigo: str

class ParceiroUsarCodigoRequest(BaseModel):
    codigo: str

# --- Comunidade Schemas ---
class PostCreate(BaseModel):
    grupo: str
    conteudo: str

class ComentarioCreate(BaseModel):
    conteudo: str

class ComentarioOut(BaseModel):
    id: int
    post_id: int
    apelido: str
    conteudo: str
    sinalizado: bool
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)

class PostOut(BaseModel):
    id: int
    apelido: str
    grupo: str
    conteudo: str
    sinalizado: bool
    criado_em: datetime
    comentarios: List[ComentarioOut] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

# --- Dispositivos Schemas ---
class MedicaoCreate(BaseModel):
    tipo: str  # pressao_arterial | glicemia
    sistolica: Optional[int] = None
    diastolica: Optional[int] = None
    glicemia: Optional[float] = None
    origem: str = "manual"  # dispositivo_bluetooth | manual

class MedicaoOut(BaseModel):
    id: int
    gestante_id: str
    tipo: str
    sistolica: Optional[int]
    diastolica: Optional[int]
    glicemia: Optional[float]
    data_hora: datetime
    origem: str

    model_config = ConfigDict(from_attributes=True)

# --- Cinta Nymphia Schemas (Roadmap 2027 V3) ---
class CintaLeituraCreate(BaseModel):
    bpm: int

class CintaLeituraOut(BaseModel):
    id: int
    gestante_id: str
    bpm: int
    status: str
    data_hora: datetime

    model_config = ConfigDict(from_attributes=True)

# --- LGPD Schemas ---
class LogAcessoOut(BaseModel):
    id: int
    acessado_por_id: str
    acessado_por_tipo: str
    recurso: str
    data_hora: datetime

    class Config:
        from_attributes = True

class ObservacaoProfissionalCreate(BaseModel):
    observacao: str

class ObservacaoProfissionalOut(BaseModel):
    id: int
    profissional_id: str
    gestante_id: str
    observacao: str
    criado_em: datetime

    class Config:
        from_attributes = True
