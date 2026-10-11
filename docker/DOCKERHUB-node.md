# Pi Fleet Emulator · Node

A **simulated Raspberry Pi** in a container: real **OpenSSH** and **Node-RED**, reports **aarch64 / armv7l** and **Raspberry Pi OS**, with simulated metrics, `docker`, `systemctl` and MQTT tools.

Usually run by the **[spawner](https://hub.docker.com/r/devprincekumar/pi-fleet-spawner)**, which spawns, scales and validates fleets of up to 20 nodes. Start there for a full fleet.

**[GitHub](https://github.com/855princekumar/pi-fleet-emulator)** · **[Docs](https://github.com/855princekumar/pi-fleet-emulator#readme)** · MIT or Apache-2.0

## Tags

| Tag | Platforms |
|---|---|
| `1.0.0`, `1.0`, `1`, `latest` | `linux/amd64`, `linux/arm64` |

Images carry OCI labels, SBOM and provenance attestations.

## Run nodes without the spawner

`docker-compose.yml`

```yaml
services:
  pi-node-1:
    image: devprincekumar/pi-fleet-node:1.0.0
    hostname: pi-node-1
    restart: unless-stopped
    ports:
      - "3000:22"        # SSH
      - "4000:1880"      # Node-RED
    environment:
      NODE_NAME: pi-node-1
      SIM_ARCH: aarch64                  # or armv7l
      SIM_DEBIAN: bookworm               # bullseye, buster
      SIM_OS: "Raspberry Pi OS 64-bit bookworm"
    volumes:
      - pi-node-1-home:/home/pi          # keeps Node-RED flows and files

  pi-node-2:
    image: devprincekumar/pi-fleet-node:1.0.0
    hostname: pi-node-2
    restart: unless-stopped
    ports:
      - "3001:22"
      - "4001:1880"
    environment:
      NODE_NAME: pi-node-2
      SIM_ARCH: armv7l
      SIM_DEBIAN: bullseye
      SIM_OS: "Raspberry Pi OS 32-bit bullseye"
    volumes:
      - pi-node-2-home:/home/pi

volumes:
  pi-node-1-home:
  pi-node-2-home:
```

```bash
docker compose up -d
ssh pi@localhost -p 3000     # password: raspberry
uname -m                     # aarch64
```

## Inside each node

| | |
|---|---|
| SSH | Port 22, `pi` / `raspberry`, passwordless sudo |
| Node-RED | 3.1 on Node.js 20, port 1880 |
| Reports | `uname -m`, `platform.machine()`, `/etc/os-release` |
| Metrics | `/tmp/metrics/summary.txt`, `/tmp/fake_temp` |
| Tools | `mosquitto`, `stress-ng`, `jq`, `curl`, simulated `docker` / `systemctl` |

Local test bed: the login is well known. Nodes report ARM but run on the host CPU.
