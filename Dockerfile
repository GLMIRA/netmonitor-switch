FROM python:3.11-slim

# Metadados
LABEL maintainer="mira"
LABEL description="Switch TP-Link Monitor"

# Diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fonte
COPY src/ ./src/
COPY .env .

# Criar diretório de logs
RUN mkdir -p /app/logs

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Healthcheck
HEALTHCHECK --interval=5m --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Comando padrão
CMD ["python", "-m", "src.main"]