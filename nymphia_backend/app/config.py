from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    DATABASE_URL: Optional[str] = None
    NYMPHIA_DATABASE_URL: str = "sqlite:///./nymphia.db"
    NYMPHIA_SECRET_KEY: str = "nymphia_super_secret_production_ready_key_change_me_in_prod_12345"
    NYMPHIA_S3_BUCKET: str = "nymphia-clinical-records"
    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    ENVIRONMENT: str = "development"
    
    # JWT algorithm and expiration
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    model_config = SettingsConfigDict(
        env_file=[
            str(_BACKEND_DIR / ".env"),
            ".env"
        ],
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()


_NOMES_DE_DESENVOLVIMENTO = {"development", "dev", "local"}


# Variáveis que o próprio Coolify cria em toda aplicação que publica
VARIAVEIS_DO_COOLIFY = ("COOLIFY_FQDN", "COOLIFY_URL", "COOLIFY_RESOURCE_UUID", "COOLIFY_CONTAINER_NAME")


def ambiente_de_desenvolvimento() -> bool:
    """
    True só em desenvolvimento. Ordem de decisão:
      1. ENVIRONMENT ou ENV definidos no ambiente decidem;
      2. sem eles, rodando no Render (variável RENDER) ou no Coolify
         (variáveis COOLIFY_*), que esses serviços criam sozinhos, é produção.
         Antes, um serviço sem ENVIRONMENT ficava em modo de desenvolvimento:
         documentação aberta, CORS livre, simulador de pagamento ligado e a
         chave pública aceita;
      3. senão, vale o ENVIRONMENT do .env (padrão: development).
    """
    import os
    explicito = (os.getenv("ENVIRONMENT") or os.getenv("ENV") or "").strip().lower()
    if explicito:
        return explicito in _NOMES_DE_DESENVOLVIMENTO
    if os.getenv("RENDER") or any(os.getenv(nome) for nome in VARIAVEIS_DO_COOLIFY):
        return False
    return (settings.ENVIRONMENT or "").strip().lower() in _NOMES_DE_DESENVOLVIMENTO


# Valor que está no código público do repositório. Com ele, qualquer pessoa
# consegue fabricar um token de login de qualquer conta.
SEGREDO_PUBLICO_DO_REPOSITORIO = "nymphia_super_secret_production_ready_key_change_me_in_prod_12345"
TAMANHO_MINIMO_SEGREDO = 32


def problemas_de_configuracao_em_producao(config: "Settings") -> list:
    """Lista o que impede o servidor de rodar com segurança em produção."""
    problemas = []
    chave = config.NYMPHIA_SECRET_KEY or ""
    if chave == SEGREDO_PUBLICO_DO_REPOSITORIO:
        problemas.append("NYMPHIA_SECRET_KEY está com o valor público que aparece no repositório.")
    elif len(chave) < TAMANHO_MINIMO_SEGREDO:
        problemas.append(f"NYMPHIA_SECRET_KEY tem menos de {TAMANHO_MINIMO_SEGREDO} caracteres.")
    if config.ALGORITHM != "HS256":
        problemas.append("ALGORITHM precisa ser HS256.")
    return problemas


def limpar_endereco_do_banco(valor: str) -> str:
    """
    Endereço do banco do jeito que o SQLAlchemy espera. Aceita o que as
    pessoas costumam colar: com espaços, entre aspas, com "psql" na frente
    (o Neon mostra assim) ou começando com postgres://. Recusa link de site:
    em 15/10/2026 um endereço https:// colado no lugar do banco derrubou um
    deploy com uma mensagem que ninguém entendia. A mensagem nunca repete o
    valor, que costuma ter senha.
    """
    texto = (valor or "").strip()
    if texto.lower().startswith("psql "):
        texto = texto[5:].strip()
    texto = texto.strip("'\"").strip()
    if texto.startswith("postgres://"):
        texto = "postgresql://" + texto[len("postgres://"):]
    if not texto.lower().startswith(("postgresql", "sqlite")):
        raise RuntimeError(
            "O endereço do banco precisa começar com postgresql:// (ou postgres://). "
            "Parece que foi colado outro tipo de endereço, como o link de um site. "
            "No painel do banco, copie a connection string."
        )
    return texto
