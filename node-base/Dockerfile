# Pi Fleet Emulator node: a simulated Raspberry Pi / Linux edge device
# - Full SSH server (OpenSSH)
# - Process management via supervisord
# - Simulated docker and systemctl commands
# - Node-RED (IoT middleware) and Mosquitto MQTT tools
# - Realistic /proc metrics (CPU/RAM/disk readable via SSH)
# - Ansible-compatible (Python3 + sudo)

FROM ubuntu:25.10

ARG NODE_NAME=edge-node
ARG NODE_USER=pi

ENV DEBIAN_FRONTEND=noninteractive
ENV NODE_NAME=${NODE_NAME}
ENV NODE_USER=${NODE_USER}

# Install everything a real Pi would have (and pick up pending security updates)
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
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
    # openssh-server generates host keys on install: delete them in this same
    # layer so they never exist in any image layer (each container makes its own)
    && rm -f /etc/ssh/ssh_host_* \
    && rm -rf /var/lib/apt/lists/*

# Node.js 22 LTS (Ubuntu 22.04's apt ships Node 12, too old for Node-RED)
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Current npm (the bundled one ships vulnerable deps), then Node-RED
RUN npm install -g npm@12.2.0 \
    && npm install -g node-red@5.0.8 \
    && npm cache clean --force

# Create the edge node user (mimics pi user on Raspberry Pi).
# The password is set at container start from NODE_PASSWORD (default: raspberry),
# so it never lives in the image history.
# Newer Ubuntu images ship an 'ubuntu' user at UID 1000; remove it so pi is 1000
# like on a real Pi (and existing /home/pi volumes keep working after upgrades).
RUN (userdel -r ubuntu 2>/dev/null || true) \
    && useradd -m -u 1000 -s /bin/bash ${NODE_USER} \
    && usermod -aG sudo ${NODE_USER} \
    && echo "${NODE_USER} ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# SSH setup (host keys are generated per container by entrypoint.sh)
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
ARG VERSION=1.1.0
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
