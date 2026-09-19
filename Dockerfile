# ==============================================================================
# NYMPHIA — DOCKERFILE UNIVERSAL DE PRODUÇÃO
# Constrói o frontend PWA e serve junto com o backend FastAPI e modelos de IA
# ==============================================================================

# ETAPA 1: Compilação do Frontend PWA
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --silent
COPY frontend/ ./
RUN npm run build

# ETAPA 2: Runtime Python com Modelos e FastAPI
FROM python:3.10-slim AS runner

# Evita geração de .pyc e força logs em tempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

WORKDIR /app

# Instala dependências do sistema necessárias para compilações leves
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala dependências Python de produção (leves, sem estouro de RAM no Render)
COPY nymphia_backend/requirements-prod.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia código do backend e modelos treinados
COPY nymphia_backend/ ./nymphia_backend/

# Copia build compilado do frontend da etapa anterior
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

WORKDIR /app/nymphia_backend

# Cria diretório de uploads persistente
RUN mkdir -p uploads_documentos

EXPOSE 8000

# Executa Uvicorn na porta definida pelo provedor de nuvem (Render/Railway/Cloud Run)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
