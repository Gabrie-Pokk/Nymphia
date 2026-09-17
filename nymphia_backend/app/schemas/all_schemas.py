import re
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator, model_validator

# Regex para nomes: apenas letras (com acentos), espaços, apóstrofos e hífens. Proíbe números e símbolos.
NOME_REGEX = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ\s'.\-]{2,100}$")
# Regex para UF brasileira
UF_REGEX = re.compile(r"^(AC|AL|AP|AM|BA|CE|DF|ES|GO|MA|MT|MS|MG|PA|PB|PR|PE|PI|RJ|RN|RS|RO|RR|SC|SP|SE|TO)$")
# Regex para CRM/COREN: 3 a 10 dígitos com sufixo opcional
REGISTRO_REGEX = re.compile(r"^[0-9]{3,10}(-[A-Za-z0-9])?$")
# Regex para código de convite de 8 caracteres alfanuméricos limpos
CODIGO_REGEX = re.compile(r"^[A-Z0-9\-]{6,12}$")
# Regex para telefone (emergência 190/192/193 ou fixo/celular brasileiro com DDD)
TELEFONE_REGEX = re.compile(r"^(?:19[0-9]|\(?\d{2}\)?\s?\d{4,5}-?\d{4})$")

# --- Auth Schemas ---
class GestanteRegister(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100)
    email: EmailStr = Field(..., max_length=120)
    senha: str = Field(..., min_length=8, max_length=72)
    recusa_ia: bool = False

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, v: str) -> str:
        v_clean = v.strip()
        if not NOME_REGEX.match(v_clean):
            raise ValueError("O nome deve conter apenas letras, espaços e hífens, sem números ou caracteres especiais.")
        return v_clean

class GestanteLogin(BaseModel):
    email: EmailStr = Field(..., max_length=120)
    senha: str = Field(..., max_length=72)

class ProfissionalRegister(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100)
    email: EmailStr = Field(..., max_length=120)
    senha: str = Field(..., min_length=8, max_length=72)
    registro_tipo: str = Field(..., pattern="^(CRM|COREN)$")
    registro_numero: str = Field(..., min_length=3, max_length=12)
    registro_uf: str = Field(..., min_length=2, max_length=2)

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, v: str) -> str:
        v_clean = v.strip()
        if not NOME_REGEX.match(v_clean):
            raise ValueError("O nome deve conter apenas letras, espaços e hífens, sem números.")
        return v_clean

    @field_validator("registro_numero")
    @classmethod
    def validar_registro_numero(cls, v: str) -> str:
        v_clean = v.strip()
        if not REGISTRO_REGEX.match(v_clean):
            raise ValueError("O número de registro deve conter entre 3 e 10 dígitos numéricos.")
        return v_clean

    @field_validator("registro_uf")
    @classmethod
    def validar_uf(cls, v: str) -> str:
        v_upper = v.strip().upper()
        if not UF_REGEX.match(v_upper):
            raise ValueError("UF inválida. Use uma sigla válida de estado brasileiro (ex: SP, RJ, MG).")
        return v_upper

class ProfissionalLogin(BaseModel):
    email: EmailStr = Field(..., max_length=120)
    senha: str = Field(..., max_length=72)

class ParceiroRegister(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100)
    email: EmailStr = Field(..., max_length=120)
    senha: str = Field(..., min_length=8, max_length=72)

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, v: str) -> str:
        v_clean = v.strip()
        if not NOME_REGEX.match(v_clean):
            raise ValueError("O nome deve conter apenas letras, sem números.")
        return v_clean

class ParceiroLogin(BaseModel):
    email: EmailStr = Field(..., max_length=120)
    senha: str = Field(..., max_length=72)

class AuthResponse(BaseModel):
    token: str
    perfil: str
    id: str
    nome: str
    status_verificacao: Optional[str] = None
    recusa_ia: Optional[bool] = False

# --- Clinical Schemas ---
class PerfilClinicoBase(BaseModel):
    idade: int = Field(..., ge=10, le=65, description="Idade materna viável (10 a 65 anos)")
    estado_civil: Optional[str] = Field(None, max_length=50)
    escolaridade: Optional[str] = Field(None, max_length=50)
    gestacoes_anteriores: int = Field(0, ge=0, le=20, description="Total de gestações prévias (máx. 20)")
    partos_normais: int = Field(0, ge=0, le=20, description="Partos normais prévios (máx. 20)")
    partos_cesareos: int = Field(0, ge=0, le=10, description="Partos cesáreos prévios (máx. 10)")
    perdas_gestacionais: int = Field(0, ge=0, le=15, description="Abortos/óbitos fetais prévios (máx. 15)")
    dum: date
    dpp: date
    dpp_editada_manualmente: bool = False
    maternidade_nome: Optional[str] = Field(None, max_length=120)
    maternidade_endereco: Optional[str] = Field(None, max_length=200)
    maternidade_telefone: Optional[str] = Field(None, max_length=25)

    @field_validator("dum")
    @classmethod
    def validar_dum(cls, v: date) -> date:
        hoje = date.today()
        if v > hoje:
            raise ValueError("A DUM (Data da Última Menstruação) não pode ser uma data futura.")
        limite_passado = hoje - timedelta(days=320)
        if v < limite_passado:
            raise ValueError("A DUM não pode ser anterior a 320 dias (~45 semanas no passado).")
        return v

    @field_validator("maternidade_telefone")
    @classmethod
    def validar_telefone(cls, v: Optional[str]) -> Optional[str]:
        if not v or not v.strip():
            return None
        v_clean = v.strip()
        if not TELEFONE_REGEX.match(v_clean):
            raise ValueError("Telefone da maternidade inválido. Use um formato válido com DDD ou número de emergência (ex: 192 ou (11) 98888-7777).")
        return v_clean

    @model_validator(mode="after")
    def validar_consistencia_obstetrica(self) -> "PerfilClinicoBase":
        # Regra Médica Cruzada: Total de partos e perdas não pode ultrapassar o número de gestações anteriores informadas
        soma_desfechos = self.partos_normais + self.partos_cesareos + self.perdas_gestacionais
        if soma_desfechos > self.gestacoes_anteriores:
            raise ValueError(
                f"Inconsistência obstétrica: a soma de partos normais ({self.partos_normais}), "
                f"cesáreas ({self.partos_cesareos}) e perdas ({self.perdas_gestacionais}) = {soma_desfechos}, "
                f"não pode ser maior do que as gestações anteriores informadas ({self.gestacoes_anteriores})."
            )
        # Validação DPP vs DUM
        if self.dpp < self.dum:
            raise ValueError("A DPP (Data Provável do Parto) não pode ser anterior à DUM.")
        return self

class PerfilClinicoCreate(PerfilClinicoBase):
    pass

class PerfilClinicoUpdate(BaseModel):
    idade: Optional[int] = Field(None, ge=10, le=65)
    estado_civil: Optional[str] = Field(None, max_length=50)
    escolaridade: Optional[str] = Field(None, max_length=50)
    gestacoes_anteriores: Optional[int] = Field(None, ge=0, le=20)
    partos_normais: Optional[int] = Field(None, ge=0, le=20)
    partos_cesareos: Optional[int] = Field(None, ge=0, le=10)
    perdas_gestacionais: Optional[int] = Field(None, ge=0, le=15)
    dum: Optional[date] = None
    dpp: Optional[date] = None
    dpp_editada_manualmente: Optional[bool] = None
    maternidade_nome: Optional[str] = Field(None, max_length=120)
    maternidade_endereco: Optional[str] = Field(None, max_length=200)
    maternidade_telefone: Optional[str] = Field(None, max_length=25)

    @field_validator("dum")
    @classmethod
    def validar_dum(cls, v: Optional[date]) -> Optional[date]:
        if v is not None:
            hoje = date.today()
            if v > hoje:
                raise ValueError("A DUM não pode ser uma data futura.")
            if v < (hoje - timedelta(days=320)):
                raise ValueError("A DUM não pode ser anterior a 320 dias.")
        return v

class PerfilClinicoOut(PerfilClinicoBase):
    id: int
    gestante_id: str
    atualizado_em: datetime

    model_config = ConfigDict(from_attributes=True)

class HistoricoFamiliarCreate(BaseModel):
    parente: str = Field(..., pattern="^(mãe|pai|irmã|irmão|avó materna|avô materno|avó paterna|avô paterno|filho anterior)$")
    condicao: str = Field(..., min_length=2, max_length=100)

    @field_validator("condicao")
    @classmethod
    def validar_condicao(cls, v: str) -> str:
        v_clean = v.strip()
        if len(v_clean) < 2:
            raise ValueError("A condição familiar deve ter no mínimo 2 caracteres.")
        return v_clean

class HistoricoFamiliarOut(BaseModel):
    id: int
    gestante_id: str
    parente: str
    condicao: str

    model_config = ConfigDict(from_attributes=True)

# --- Checkin Schemas ---
class CheckinAnalisarRequest(BaseModel):
    texto: str = Field(..., min_length=1, max_length=1500)

class CheckinCreate(BaseModel):
    humor: int = Field(..., ge=1, le=5, description="Escala de 1 (muito mal) a 5 (excelente)")
    descricao: Optional[str] = Field("", max_length=1500)
    sintomas: List[str] = Field(default_factory=list, max_length=20)
    movimentos_bebe: int = Field(0, ge=0, le=150, description="Contagem diária de movimentos fetais (0 a 150)")
    semana_gestacional: Optional[int] = Field(None, ge=1, le=45)

    @field_validator("sintomas")
    @classmethod
    def validar_sintomas(cls, v: List[str]) -> List[str]:
        if len(v) > 20:
            raise ValueError("Máximo de 20 sintomas por registro.")
        return [s.strip()[:80] for s in v if s.strip()]

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
    texto: str = Field(..., min_length=1, max_length=1000)

    @field_validator("texto")
    @classmethod
    def validar_texto(cls, v: str) -> str:
        v_clean = v.strip()
        if not v_clean:
            raise ValueError("A mensagem não pode ser vazia ou conter apenas espaços.")
        return v_clean

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
    tipo: str = Field(..., pattern="^(consulta|medicacao|vacina|exame|marco)$")
    titulo: str = Field(..., min_length=2, max_length=100)
    data_hora: datetime
    notas: Optional[str] = Field("", max_length=500)
    recorrencia: Optional[str] = Field(None, max_length=30)

    @field_validator("titulo")
    @classmethod
    def validar_titulo(cls, v: str) -> str:
        v_clean = v.strip()
        if len(v_clean) < 2:
            raise ValueError("O título do evento deve ter no mínimo 2 caracteres.")
        return v_clean

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
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)

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
    codigo: str = Field(..., min_length=8, max_length=8)

    @field_validator("codigo")
    @classmethod
    def validar_codigo(cls, v: str) -> str:
        v_clean = v.strip().upper()
        if not CODIGO_REGEX.match(v_clean):
            raise ValueError("Código de convite inválido. Deve possuir 8 caracteres alfanuméricos válidos.")
        return v_clean

class SolicitarVinculoRequest(BaseModel):
    email_gestante: EmailStr = Field(..., max_length=120)

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
    codigo: str = Field(..., min_length=8, max_length=8)

    @field_validator("codigo")
    @classmethod
    def validar_codigo(cls, v: str) -> str:
        v_clean = v.strip().upper()
        if not CODIGO_REGEX.match(v_clean):
            raise ValueError("Código de convite inválido. Deve possuir 8 caracteres.")
        return v_clean

# --- Comunidade Schemas ---
class PostCreate(BaseModel):
    grupo: str = Field(..., max_length=80)
    conteudo: str = Field(..., min_length=5, max_length=1500)

    @field_validator("conteudo")
    @classmethod
    def validar_conteudo(cls, v: str) -> str:
        v_clean = v.strip()
        if len(v_clean) < 5:
            raise ValueError("O conteúdo da postagem deve ter no mínimo 5 caracteres.")
        return v_clean

class ComentarioCreate(BaseModel):
    conteudo: str = Field(..., min_length=1, max_length=500)

    @field_validator("conteudo")
    @classmethod
    def validar_conteudo(cls, v: str) -> str:
        v_clean = v.strip()
        if not v_clean:
            raise ValueError("O comentário não pode ser vazio.")
        return v_clean

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

class PreferenciasComunidadeCreate(BaseModel):
    experiencia: Optional[str] = Field(None, max_length=100)
    preferencia_parto: Optional[str] = Field(None, max_length=100)
    interesses: List[str] = Field(default_factory=list)
    estilo_vida: Optional[str] = Field(None, max_length=100)

class PreferenciasComunidadeOut(BaseModel):
    experiencia: Optional[str] = None
    preferencia_parto: Optional[str] = None
    interesses: List[str] = Field(default_factory=list)
    estilo_vida: Optional[str] = None
    grupos_recomendados: List[str] = Field(default_factory=list)
    atualizado_em: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# --- Dispositivos Schemas ---
class MedicaoCreate(BaseModel):
    tipo: str = Field(..., pattern="^(pressao_arterial|glicemia)$")
    sistolica: Optional[int] = Field(None, ge=60, le=250, description="Pressão sistólica entre 60 e 250 mmHg")
    diastolica: Optional[int] = Field(None, ge=30, le=160, description="Pressão diastólica entre 30 e 160 mmHg")
    glicemia: Optional[float] = Field(None, ge=20.0, le=600.0, description="Glicemia entre 20 e 600 mg/dL")
    origem: str = Field("manual", pattern="^(manual|dispositivo_bluetooth)$")

    @model_validator(mode="after")
    def validar_medicoes(self) -> "MedicaoCreate":
        if self.tipo == "pressao_arterial":
            if self.sistolica is None or self.diastolica is None:
                raise ValueError("Para pressão arterial, sistólica e diastólica são obrigatórias.")
            if self.sistolica <= self.diastolica:
                raise ValueError("A pressão sistólica (máxima) deve ser obrigatoriamente maior que a diastólica (mínima).")
        elif self.tipo == "glicemia":
            if self.glicemia is None:
                raise ValueError("O valor de glicemia é obrigatório para este tipo de medição.")
        return self

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
    bpm: int = Field(..., ge=40, le=240, description="Batimentos Cardíacos Fetais entre 40 e 240 bpm")

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

    model_config = ConfigDict(from_attributes=True)

class ObservacaoProfissionalCreate(BaseModel):
    observacao: str = Field(..., min_length=3, max_length=2000)

    @field_validator("observacao")
    @classmethod
    def validar_observacao(cls, v: str) -> str:
        v_clean = v.strip()
        if len(v_clean) < 3:
            raise ValueError("A anotação médica deve conter pelo menos 3 caracteres.")
        return v_clean

class ObservacaoProfissionalOut(BaseModel):
    id: int
    profissional_id: str
    gestante_id: str
    observacao: str
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)
