FROM python:3.11-slim

# Install Docker CLI so the spawner can run docker compose commands
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
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
# then drop pip/setuptools/wheel: not needed at runtime, and they vendor their own CVEs
RUN pip install --no-cache-dir -r requirements.txt \
    && pip uninstall -y pip setuptools wheel \
    && rm -rf /usr/local/lib/python3.11/ensurepip

# Copy spawner app + the pfe command line
COPY spawner/ ./spawner/
RUN printf '#!/bin/sh\nexec python /app/spawner/pfe.py "$@"\n' > /usr/local/bin/pfe \
    && chmod +x /usr/local/bin/pfe

# Copy node-base so the spawner can build Pi node images
COPY node-base/ ./node-base/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PFE_DATA_DIR=/data \
    PFE_NODE_BASE=/app/node-base

# Fleet config + generated compose file live here: mount a volume to persist them
VOLUME ["/data"]

EXPOSE 7070

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -sf http://localhost:7070/api/health || exit 1

# Labels last so changing values never bust the layer cache.
# Filled in by docker/publish.sh; defaults keep plain `docker build` working
ARG VERSION=1.0.2
ARG REVISION=unknown
ARG CREATED=unknown

LABEL org.opencontainers.image.title="Pi Fleet Emulator Spawner" \
      org.opencontainers.image.description="Web GUI, CLI and API that spawn, scale and validate simulated Raspberry Pi fleets in Docker" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${REVISION}" \
      org.opencontainers.image.created="${CREATED}" \
      org.opencontainers.image.licenses="MIT OR Apache-2.0" \
      org.opencontainers.image.authors="855princekumar" \
      org.opencontainers.image.vendor="855princekumar" \
      org.opencontainers.image.url="https://hub.docker.com/r/devprincekumar/pi-fleet-spawner" \
      org.opencontainers.image.documentation="https://github.com/855princekumar/pi-fleet-emulator#readme" \
      org.opencontainers.image.source="https://github.com/855princekumar/pi-fleet-emulator" \
      org.opencontainers.image.base.name="docker.io/library/python:3.11-slim"

CMD ["gunicorn", \
     "--workers", "1", \
     "--threads", "8", \
     "--bind", "0.0.0.0:7070", \
     "--timeout", "600", \
     "--chdir", "/app/spawner", \
     "app:app"]
