# Pi Fleet Emulator - Node

**A simulated Raspberry Pi in a container.** This is the node image used by [`devprincekumar/pi-fleet-spawner`](https://hub.docker.com/r/devprincekumar/pi-fleet-spawner), which spawns, scales and validates fleets of up to 20 of these. **Start with the spawner** - it pulls this image for you.

[GitHub](https://github.com/855princekumar/pi-fleet-emulator) · [Spawner image + quick start](https://hub.docker.com/r/devprincekumar/pi-fleet-spawner) · License: MIT or Apache 2.0

**Tags:** `1.0.0`, `latest` · **Platforms:** `linux/amd64`, `linux/arm64`

## What's inside

| Feature | Detail |
|---|---|
| SSH | Real OpenSSH on port 22, user `pi` / `raspberry`, passwordless sudo |
| Node-RED | 3.1 on Node.js 20, port 1880, user dir `/home/pi/.node-red` |
| Architecture | `uname -m` and Python `platform.machine()` report `SIM_ARCH` (`aarch64` / `armv7l`) |
| OS | `/etc/os-release` reports Raspberry Pi OS (Debian 12 / 11 / 10 from `SIM_DEBIAN`) |
| Metrics | Simulated CPU, RAM, disk, temperature in `/tmp/metrics/summary.txt`, `/tmp/fake_temp` |
| Tools | Simulated `docker` and `systemctl`, `mosquitto` + clients, `stress-ng`, `jq`, `htop`, `curl` |
| Base | Ubuntu 22.04, services run under supervisord |

## Run one node on its own

```bash
docker run -d --name pi-node-1 --hostname pi-node-1 -p 3000:22 -p 4000:1880 \
  -e NODE_NAME=pi-node-1 -e SIM_ARCH=aarch64 -e SIM_DEBIAN=bookworm \
  -e SIM_OS="Raspberry Pi OS 64-bit bookworm" \
  -v pi-node-1-home:/home/pi \
  devprincekumar/pi-fleet-node:1.0.0

ssh pi@localhost -p 3000     # password: raspberry
```

| Variable | Default | Purpose |
|---|---|---|
| `NODE_NAME` | `edge-node` | Node name used in logs and `uname -a` (set the hostname with `--hostname`) |
| `SIM_ARCH` | `x86_64` | Reported architecture: `aarch64` or `armv7l` |
| `SIM_DEBIAN` | `bookworm` | `bookworm`, `bullseye` or `buster` |
| `SIM_OS` | `Raspberry Pi OS Lite` | `PRETTY_NAME` in `/etc/os-release` |

Mount a volume on `/home/pi` to keep Node-RED flows and files across restarts.

> Local test bed only: the credentials are well known. Nodes report ARM but run on the host CPU.

Free and open source by [855princekumar](https://github.com/855princekumar).
