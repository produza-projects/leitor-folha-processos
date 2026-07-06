# Imagem base enxuta com Python 3.12
FROM python:3.12-slim

# Evita geração de arquivos .pyc e melhora logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Dependências necessárias para psycopg2-binary e healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements primeiro para aproveitar cache de build
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia código da aplicação
COPY backend ./backend
COPY frontend ./frontend

# Uvicorn escutando em todas as interfaces
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
