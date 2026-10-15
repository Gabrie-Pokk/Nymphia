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


def ambiente_de_desenvolvimento() -> bool:
    """
    True só em desenvolvimento. Ordem de decisão:
      1. ENVIRONMENT ou ENV definidos no ambiente decidem;
      2. sem eles, rodando no Render (variável RENDER, que o próprio Render
         cria) é produção. Antes, um serviço sem ENVIRONMENT ficava em modo
         de desenvolvimento: documentação aberta, CORS livre, simulador de
         pagamento ligado e a chave pública aceita;
      3. senão, vale o ENVIRONMENT do .env (padrão: development).
    """
    import os
    explicito = (os.getenv("ENVIRONMENT") or os.getenv("ENV") or "").strip().lower()
    if explicito:
        return explicito in _NOMES_DE_DESENVOLVIMENTO
    if os.getenv("RENDER"):
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
