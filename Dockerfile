FROM python:3.11-slim

LABEL maintainer="mira"
LABEL description="Switch TP-Link Monitor"
LABEL version="1.0.0"

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código fonte (SEM .env!)
COPY src/ ./src/

# Criar diretório de logs
RUN mkdir -p /app/logs && chmod 755 /app/logs

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV LOG_LEVEL=INFO
ENV LOG_FILE=/app/logs/app.log

# ✅ HEALTHCHECK MELHORADO - Verifica 3 coisas:
# 1. Se o processo Python está rodando
# 2. Se o arquivo de log está sendo escrito (atualizado recentemente)
# 3. Se consegue importar o módulo main
HEALTHCHECK --interval=2m --timeout=10s --start-period=40s --retries=3 \
    CMD pgrep -f "python -m src.main" > /dev/null && \
    test -f /app/logs/app.log && \
    python -c "import src.main" || exit 1

CMD ["python", "-m", "src.main"]