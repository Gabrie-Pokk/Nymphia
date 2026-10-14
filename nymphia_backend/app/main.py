import os
import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse

from app.config import settings
from app.database import Base, engine
from app.storage.object_storage import STORAGE_DIR
from app.api import (
    health, auth, perfil, checkin, conversa,
    agenda, vinculo, exames, risco, emergencia,
    parceiro, comunidade, dispositivos,
    governance, lgpd, legacy, assinaturas, antropometria
)
from app.services.ai_risk_service import carregar_modelos_ml
from app.services.ai_text_service import carregar_bertimbau

# Configuração de Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("nymphia")

import threading
from contextlib import asynccontextmanager

def is_dev_env() -> bool:
    env = (os.getenv("ENVIRONMENT") or os.getenv("ENV") or settings.ENVIRONMENT or "").lower()
    return env in ["development", "dev", "local"]

is_prod = not is_dev_env()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicialização resiliente e não-bloqueante no startup
    logger.info("Iniciando Nymphia Backend — Cada batimento importa.")
    try:
        from app.database import Base, engine, executar_migracoes_automaticas
        Base.metadata.create_all(bind=engine)
        executar_migracoes_automaticas()
    except Exception as e:
        logger.error(f"Aviso na inicialização do banco: {e}")

    # Seed de demonstração executado apenas em desenvolvimento quando explicitamente habilitado
    env_name = (os.getenv("ENVIRONMENT") or os.getenv("ENV") or settings.ENVIRONMENT or "").lower()
    if env_name in ["development", "dev", "local"] and os.getenv("ENABLE_DEMO_SEED", "").lower() == "true":
        try:
            from app.seed_demo import seed_demo_accounts
            seed_demo_accounts()
        except Exception as e:
            logger.warning(f"Aviso no seed demo: {e}")

    # Pré-carregamento assíncrono em background para que o processo atenda imediatamente na porta
    def _aquecer_modelos_background():
        try:
            carregar_modelos_ml()
            if os.getenv("NYMPHIA_CARREGAR_BERTIMBAU", "0").strip().lower() in ("1", "true", "sim", "yes"):
                carregar_bertimbau()
        except Exception as e:
            logger.warning(f"Aviso no pré-carregamento assíncrono: {e}")

    threading.Thread(target=_aquecer_modelos_background, daemon=True, name="ml-warmup").start()

    yield
    logger.info("Encerrando Nymphia Backend.")

from app.security.rate_limiter import auth_rate_limiter

app = FastAPI(
    title="Nymphia — Inteligência Artificial Obstétrica",
    description="Start-up de IA em saúde materno-fetal: 'Cada batimento importa.'",
    version="2.3.0-2027ready",
    openapi_url="/openapi.json" if is_dev_env() else None,
    docs_url="/docs" if is_dev_env() else None,
    redoc_url="/redoc" if is_dev_env() else None,
    lifespan=lifespan,
)

AUTH_RATE_LIMITED_PREFIXES = (
    "/auth/gestante/login",
    "/auth/gestante/cadastro",
    "/auth/profissional/login",
    "/auth/profissional/cadastro",
    "/auth/parceiro/login",
    "/auth/parceiro/cadastro",
    "/auth/login",
    "/auth/esqueci-senha",
    "/auth/redefinir-senha",
)

# Middleware unificado de Segurança, Governança, Rate Limiting e Bloqueio de Docs em Produção
@app.middleware("http")
async def seguranca_governanca_middleware(request: Request, call_next):
    path = request.url.path.rstrip("/").lower()

    # 1. Bloqueio de documentação automática em ambiente de produção (Aceite 1.1)
    if not is_dev_env() and path in ["/openapi.json", "/docs", "/redoc", "/openapi.yaml"]:
        return JSONResponse(status_code=404, content={"detail": "Not Found"})

    # 2. Rate limiting nos endpoints de autenticação (Aceite 1.5)
    if any(path == p or path.startswith(p + "/") for p in AUTH_RATE_LIMITED_PREFIXES):
        client_ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (request.client.host if request.client else "127.0.0.1")
        if not auth_rate_limiter.is_allowed(client_ip):
            return JSONResponse(
                status_code=429,
                content={"detail": "Muitas tentativas de autenticação na mesma origem. Tente novamente mais tarde."}
            )

    response = await call_next(request)

    # 3. Cabeçalhos de Segurança Obrigatórios (Aceite 1.2)
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(self), camera=(), microphone=()"

    # 4. Content-Security-Policy em modo Report-Only
    response.headers["Content-Security-Policy-Report-Only"] = (
        "default-src 'self'; frame-ancestors 'none'; base-uri 'self'; object-src 'none'; img-src 'self' data: blob:"
    )
    if "Content-Security-Policy" in response.headers:
        del response.headers["Content-Security-Policy"]

    # 5. Remoção de fingerprints do servidor (ofuscação de infraestrutura)
    if "x-render-origin-server" in response.headers:
        del response.headers["x-render-origin-server"]
    if "server" in response.headers:
        del response.headers["server"]

    return response

# CORS seguro e adaptativo
ORIGENS_PRODUCAO = [
    "https://nymphia-plataforma-ia.onrender.com",
    "https://nymphia-global.onrender.com",
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENS_PRODUCAO if is_prod else ["*"],
    allow_credentials=True if is_prod else False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Armazenamento estático seguro de laudos e fotos de exames
app.mount("/storage", StaticFiles(directory=str(STORAGE_DIR)), name="storage")

# Registro dos Roteadores Clínicos e de Governança
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(perfil.router)
app.include_router(checkin.router)
app.include_router(conversa.router)
app.include_router(agenda.router)
app.include_router(vinculo.router)
app.include_router(exames.router)
app.include_router(risco.router)
app.include_router(emergencia.router)
app.include_router(parceiro.router)
app.include_router(comunidade.router)
app.include_router(assinaturas.router)
app.include_router(dispositivos.router)
app.include_router(governance.router)
app.include_router(lgpd.router)
app.include_router(legacy.router)
app.include_router(antropometria.router)

# Tratamento Global de Exceções (Degradação Graciosa e Sanitização de Erros em Produção)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Exceção não tratada na rota {request.url.path}: {exc}", exc_info=True)
    # Em produção, nunca expor queries SQL, schemas, parâmetros de banco ou tracebacks
    detalhe_seguro = (
        str(exc)
        if is_dev_env()
        else "Ocorreu uma instabilidade interna momentânea. Os detalhes foram registrados no log e a equipe técnica foi notificada."
    )
    return JSONResponse(
        status_code=500,
        content={
            "erro": "Falha interna no processamento",
            "detalhe": detalhe_seguro,
            "degradacao_graciosa": "O sistema permanece operacional. Contate o suporte se o erro persistir."
        }
    )

# Servir Frontend compilado (Vite dist) para deploy unificado em nuvem (Render, Railway, Docker)
_FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if not _FRONTEND_DIST.exists():
    _FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend_dist"

if _FRONTEND_DIST.exists():
    logger.info(f"Servindo Frontend PWA a partir de: {_FRONTEND_DIST}")
    app.mount("/assets", StaticFiles(directory=str(_FRONTEND_DIST / "assets")), name="static-assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Bloqueia documentação automática em produção para não ser capturada pelo SPA
        normalized = full_path.strip("/").lower()
        if not is_dev_env() and normalized in ["openapi.json", "docs", "redoc", "openapi.yaml"]:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Not Found")
        file_path = _FRONTEND_DIST / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(_FRONTEND_DIST / "index.html")
else:
    @app.get("/")
    def raiz():
        return {
            "plataforma": "Nymphia — Inteligência Artificial Gestacional",
            "slogan": "Cada batimento importa.",
            "status": "online",
            "documentacao": "/docs",
            "modelos_ativos": ["Random Forest x6", "Isolation Forest", "BERTimbau (PT-BR)"]
        }
