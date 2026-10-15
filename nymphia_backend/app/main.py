import os
import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse

from app.config import settings
from app.database import Base, engine
from app.api import (
    health, auth, perfil, checkin, conversa,
    agenda, vinculo, exames, risco, emergencia,
    parceiro, comunidade, dispositivos,
    governance, lgpd, legacy, assinaturas, antropometria,
    arquivos, admin
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
    from app.config import ambiente_de_desenvolvimento
    return ambiente_de_desenvolvimento()

is_prod = not is_dev_env()


def garantir_chave_jwt_segura() -> None:
    """
    Em produção, a chave que assina os logins nunca é a pública do
    repositório. Se NYMPHIA_SECRET_KEY vier ausente, curta ou igual ao valor
    público, o servidor usa uma chave aleatória guardada no próprio banco
    (criada na primeira vez). Sem banco, o servidor não sobe.
    """
    from app.config import problemas_de_configuracao_em_producao
    problemas = problemas_de_configuracao_em_producao(settings)
    if not problemas:
        return
    from app.database import obter_ou_criar_segredo
    settings.NYMPHIA_SECRET_KEY = obter_ou_criar_segredo("jwt_hs256")
    logger.warning(
        "[SEGURANÇA] " + " ".join(problemas)
        + " Usando a chave aleatória guardada no banco (tabela segredos_servidor)."
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicialização resiliente e não-bloqueante no startup
    logger.info("Iniciando Nymphia Backend — Cada batimento importa.")
    from app.database import Base, engine, executar_migracoes_automaticas, executar_manutencoes_unicas
    try:
        Base.metadata.create_all(bind=engine)
        executar_migracoes_automaticas()
    except Exception as e:
        logger.error(f"Aviso na inicialização do banco: {e}")

    # Troca de banco: copia o antigo (NYMPHIA_DATABASE_URL_ANTIGO) uma vez, antes
    # de qualquer manutenção. Se falhar, a inicialização para de propósito.
    from app.copia_de_banco import copiar_banco_antigo_se_preciso
    copiar_banco_antigo_se_preciso()

    try:
        executar_manutencoes_unicas()
    except Exception as e:
        logger.error(f"Aviso nas manutenções do banco: {e}")

    # Sem chave segura, o servidor não atende ninguém (a exceção derruba a inicialização)
    if is_prod:
        garantir_chave_jwt_segura()

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

from app.security.rate_limiter import auth_rate_limiter, admin_rate_limiter

app = FastAPI(
    title="Nymphia — Inteligência Artificial Obstétrica",
    description="Start-up de IA em saúde materno-fetal: 'Cada batimento importa.'",
    version="2.3.0-2027ready",
    openapi_url="/openapi.json" if is_dev_env() else None,
    docs_url="/docs" if is_dev_env() else None,
    redoc_url="/redoc" if is_dev_env() else None,
    lifespan=lifespan,
)

def ip_do_cliente(request: Request) -> str:
    """
    IP de quem fez o pedido, para o limite de tentativas de login.

    Atrás de proxy (Render, ou o Traefik do Coolify na Hostinger) o IP real é o
    que o PROXY acrescenta no FIM do cabeçalho X-Forwarded-For. O começo da
    lista é escrito pelo próprio cliente e pode ser inventado; antes, o código
    usava o primeiro item, e bastava trocar o cabeçalho a cada tentativa para
    escapar do limite. NYMPHIA_PROXIES_CONFIAVEIS diz quantos proxies há na
    frente do servidor (padrão 1; use 2 se houver Cloudflare na frente do Coolify).
    """
    try:
        saltos = max(0, int(os.getenv("NYMPHIA_PROXIES_CONFIAVEIS", "1")))
    except ValueError:
        saltos = 1
    lista = [p.strip() for p in request.headers.get("x-forwarded-for", "").split(",") if p.strip()]
    if saltos and lista:
        return lista[-saltos] if len(lista) >= saltos else lista[0]
    return request.client.host if request.client else "desconhecido"


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
        client_ip = ip_do_cliente(request)
        if not auth_rate_limiter.is_allowed(client_ip):
            return JSONResponse(
                status_code=429,
                content={"detail": "Muitas tentativas de autenticação na mesma origem. Tente novamente mais tarde."}
            )

    if path == "/admin" or path.startswith("/admin/"):
        if not admin_rate_limiter.is_allowed(ip_do_cliente(request)):
            return JSONResponse(
                status_code=429,
                content={"detail": "Muitos pedidos na área da equipe. Espere um minuto e tente de novo."}
            )

    response = await call_next(request)

    # 3. Cabeçalhos de Segurança Obrigatórios (Aceite 1.2)
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # A câmera é liberada só para o próprio site (antropometria e visão corporal).
    # Microfone continua bloqueado.
    response.headers["Permissions-Policy"] = "geolocation=(self), camera=(self), microphone=()"

    # Respostas da API trazem dados pessoais e de saúde: o navegador não deve
    # guardar cópia. Sem isso, a lista da área da equipe vinha do cache e não
    # mostrava a aprovação que tinha acabado de ser feita.
    if "cache-control" not in response.headers and response.headers.get("content-type", "").startswith("application/json"):
        response.headers["Cache-Control"] = "no-store"

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

# Laudos, fotos de exame e documentos profissionais NÃO são mais servidos
# como pasta pública. A rota GET /storage/{nome} (app/api/arquivos.py) exige
# login e confere quem tem direito a cada arquivo.

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
app.include_router(arquivos.router)
app.include_router(admin.router)

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
        # Impede sair da pasta do frontend com "../" (path traversal)
        raiz = _FRONTEND_DIST.resolve()
        file_path = (raiz / full_path).resolve()
        if file_path.is_file() and (file_path == raiz or raiz in file_path.parents):
            return FileResponse(file_path)
        return FileResponse(raiz / "index.html")
else:
    @app.get("/")
    def raiz():
        return {
            "plataforma": "Nymphia — Inteligência Artificial Gestacional",
            "slogan": "Cada batimento importa.",
            "status": "online",
            "documentacao": "/docs",
            # Quais modelos estão ligados de verdade depende da memória do servidor
            "estado_dos_modelos": "/health",
        }
