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

# Inicialização de tabelas e modelos de IA
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Tabelas do banco de dados verificadas e inicializadas com sucesso.")
    from app.database import executar_migracoes_automaticas
    executar_migracoes_automaticas()
    from app.seed_demo import seed_demo_accounts
    seed_demo_accounts()
except Exception as e:
    logger.error(f"Erro ao inicializar tabelas do banco de dados: {e}")

# Pré-carregamento dos modelos de Machine Learning (Random Forest & Isolation Forest)
carregar_modelos_ml()

# Pré-aquecimento do BERTimbau em segundo plano para que as requisições de chat respondam em milissegundos
import threading
def _iniciar_bertimbau_background():
    logger.info("Disparando thread em segundo plano para inicialização e aquecimento do BERTimbau...")
    try:
        carregar_bertimbau()
        logger.info("BERTimbau inicializado e pré-aquecido com sucesso.")
    except Exception as e:
        logger.warning(f"Exceção na inicialização do BERTimbau: {e}")

threading.Thread(target=_iniciar_bertimbau_background, daemon=True, name="bertimbau-worker").start()


is_prod = (
    settings.ENVIRONMENT.lower() in ["production", "producao"]
    or os.getenv("ENV", "").lower() in ["production", "producao"]
)

app = FastAPI(
    title="Nymphia — Inteligência Artificial Obstétrica",
    description="Start-up de IA em saúde materno-fetal: 'Cada batimento importa.'",
    version="2.3.0-2027ready",
    openapi_url=None if is_prod else "/openapi.json",
    docs_url=None if is_prod else "/docs",
    redoc_url=None if is_prod else "/redoc",
)

# Middleware de Cabeçalhos de Segurança (Grau A+ de Segurança e Conformidade LGPD/CFM)
@app.middleware("http")
async def cabecalhos_seguranca_middleware(request: Request, call_next):
    response = await call_next(request)

    # 1. HSTS (HTTP Strict Transport Security - 2 anos com subdomínios e preload)
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"

    # 2. X-Content-Type-Options: previne MIME-sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # 3. Anti-clickjacking: bloqueia inclusão em frames ou iframes arbitrários
    response.headers["X-Frame-Options"] = "DENY"

    # 4. Referrer-Policy: evita vazamento de URLs com IDs clínicos de gestantes em requisições externas
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # 5. Permissions-Policy: restringe recursos do dispositivo; libera câmera explicitamente para o próprio domínio (necessária para MediaPipe Pose no BodyVision)
    response.headers["Permissions-Policy"] = "geolocation=(self), camera=(self), microphone=()"

    # 6. Content-Security-Policy (CSP) robusta
    csp_directives = [
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' blob:",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
        "font-src 'self' https://fonts.gstatic.com data:",
        "img-src 'self' data: blob:",
        "connect-src 'self' https://api.cremesp.org.br ws: wss:",
        "frame-ancestors 'none'",
        "base-uri 'self'",
        "object-src 'none'",
    ]
    response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

    # 7. Remoção de fingerprints do servidor (ofuscação de infraestrutura)
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

# Tratamento Global de Exceções (Degradação Graciosa)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Exceção não tratada na rota {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "erro": "Falha interna no processamento",
            "detalhe": str(exc),
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
        # Rotas de API não devem ser capturadas pelo SPA
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
