# Pi Fleet Emulator node: a simulated Raspberry Pi / Linux edge device
# - Full SSH server (OpenSSH)
# - Process management via supervisord
# - Simulated docker and systemctl commands
# - Node-RED (IoT middleware) and Mosquitto MQTT tools
# - Realistic /proc metrics (CPU/RAM/disk readable via SSH)
# - Ansible-compatible (Python3 + sudo)

FROM ubuntu:22.04

ARG NODE_NAME=edge-node
ARG NODE_USER=pi
ARG NODE_PASSWORD=raspberry

ENV DEBIAN_FRONTEND=noninteractive
ENV NODE_NAME=${NODE_NAME}
ENV NODE_USER=${NODE_USER}

# Install everything a real Pi would have
RUN apt-get update && apt-get install -y --no-install-recommends \
    # SSH
    openssh-server \
    # Python (Ansible requirement)
    python3 python3-pip \
    # Utilities EdgeShell will run
    htop curl wget net-tools procps \
    iproute2 dnsutils lsof \
    # Simulate workloads
    stress-ng \
    # MQTT broker + clients (used by TEST-PLAYGROUND.md)
    mosquitto mosquitto-clients \
    # Supervisor (keeps sshd + fake services running)
    supervisor \
    # Needed to add the NodeSource repo
    ca-certificates gnupg \
    # Misc
    sudo vim nano jq bc \
    && rm -rf /var/lib/apt/lists/*

# Node.js 20 LTS (Ubuntu 22.04's apt ships Node 12, too old for Node-RED 3.x)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Node-RED globally
RUN npm install -g --unsafe-perm node-red@3.1.15

# Create the edge node user (mimics pi user on Raspberry Pi)
RUN useradd -m -s /bin/bash ${NODE_USER} \
    && echo "${NODE_USER}:${NODE_PASSWORD}" | chpasswd \
    && usermod -aG sudo ${NODE_USER} \
    && echo "${NODE_USER} ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# SSH setup
RUN mkdir -p /var/run/sshd \
    && sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config \
    && sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config \
    && sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config \
    && sed -i 's/UsePAM yes/UsePAM no/' /etc/ssh/sshd_config \
    && echo "AllowUsers ${NODE_USER}" >> /etc/ssh/sshd_config

# Supervisor config - manages sshd + node-red + fake-docker-stats
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Boot scripts
COPY scripts/entrypoint.sh /entrypoint.sh
COPY scripts/fake-docker-stats.sh /usr/local/bin/fake-docker-stats
COPY scripts/fake-metrics.sh /usr/local/bin/fake-metrics
COPY scripts/node-info.sh /usr/local/bin/node-info

RUN chmod +x /entrypoint.sh /usr/local/bin/fake-docker-stats \
    /usr/local/bin/fake-metrics /usr/local/bin/node-info

EXPOSE 22 1880

# Labels last so changing values never bust the layer cache.
# Filled in by docker/publish.sh; defaults keep plain `docker build` working
ARG VERSION=1.0.0
ARG REVISION=unknown
ARG CREATED=unknown

LABEL org.opencontainers.image.title="Pi Fleet Emulator Node" \
      org.opencontainers.image.description="Simulated Raspberry Pi node: real OpenSSH and Node-RED, reports aarch64/armv7l and Raspberry Pi OS" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${REVISION}" \
      org.opencontainers.image.created="${CREATED}" \
      org.opencontainers.image.licenses="MIT OR Apache-2.0" \
      org.opencontainers.image.authors="855princekumar" \
      org.opencontainers.image.vendor="855princekumar" \
      org.opencontainers.image.url="https://hub.docker.com/r/devprincekumar/pi-fleet-node" \
      org.opencontainers.image.documentation="https://github.com/855princekumar/pi-fleet-emulator#readme" \
      org.opencontainers.image.source="https://github.com/855princekumar/pi-fleet-emulator" \
      org.opencontainers.image.base.name="docker.io/library/ubuntu:22.04"

ENTRYPOINT ["/entrypoint.sh"]
