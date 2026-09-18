import os
import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse

from app.database import Base, engine
from app.storage.object_storage import STORAGE_DIR
from app.api import (
    health, auth, perfil, checkin, conversa,
    agenda, vinculo, exames, risco, emergencia,
    parceiro, comunidade, dispositivos,
    governance, lgpd, legacy, assinaturas
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
except Exception as e:
    logger.error(f"Erro ao inicializar tabelas do banco de dados: {e}")

# Pré-carregamento dos modelos de Machine Learning (Random Forest, Isolation Forest, BERTimbau)
carregar_modelos_ml()
carregar_bertimbau()

app = FastAPI(
    title="Nymphia — Inteligência Artificial Obstétrica",
    description="Start-up de IA em saúde materno-fetal: 'Cada batimento importa.'",
    version="2.1.0-2027ready"
)

# CORS liberado para qualquer origem (mobile PWA, web, rede local)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
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
