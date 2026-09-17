FROM python:3.10-slim

# Dependências do sistema para bcrypt e compilação de pacotes C
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

COPY . .

# Pasta de modelos -- será sobrescrita pelo volume do Railway quando montado
RUN mkdir -p /app/modelos

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
