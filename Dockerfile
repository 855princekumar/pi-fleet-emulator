FROM python:3.11-slim

LABEL org.opencontainers.image.title="Pi Fleet Emulator" \
      org.opencontainers.image.description="Simulated Raspberry Pi fleet for testing edge deployments" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.licenses="MIT OR Apache-2.0" \
      org.opencontainers.image.source="https://github.com/855princekumar/pi-fleet-emulator" \
      org.opencontainers.image.authors="855princekumar"

# Install Docker CLI so the spawner can run docker compose commands
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        gnupg \
    && install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg \
       | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && chmod a+r /etc/apt/keyrings/docker.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
       https://download.docker.com/linux/debian bookworm stable" \
       > /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends docker-ce-cli docker-compose-plugin \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy spawner app
COPY spawner/ ./spawner/

# Copy node-base so the spawner can build Pi node images
COPY node-base/ ./node-base/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PFE_DATA_DIR=/data \
    PFE_NODE_BASE=/app/node-base

EXPOSE 7070

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -sf http://localhost:7070/ || exit 1

CMD ["gunicorn", \
     "--workers", "1", \
     "--bind", "0.0.0.0:7070", \
     "--timeout", "600", \
     "--chdir", "/app/spawner", \
     "app:app"]
