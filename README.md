<div align="center">

<img src="assets/banner.svg" alt="Pi Fleet Emulator - one command starts the spawner, one click spawns a fleet of simulated Raspberry Pi nodes with real SSH and Node-RED, which your fleet tool manages over SSH" width="100%">

### Spawn a realistic Raspberry Pi fleet in Docker - no hardware required.

A self-contained test bed for IoT deployment pipelines, fleet management tools and edge computing workflows.

<!-- Project -->
[![CI](https://github.com/855princekumar/pi-fleet-emulator/actions/workflows/ci.yml/badge.svg)](https://github.com/855princekumar/pi-fleet-emulator/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE-MIT)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE-APACHE)
[![Version](https://img.shields.io/badge/version-1.0.0-informational)](#)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](#contributing)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](#quick-start)

<!-- What gets simulated -->
[![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-simulated-C51A4A?logo=raspberrypi&logoColor=white)](#what-each-node-simulates)
[![Arch](https://img.shields.io/badge/arch-aarch64%20%7C%20armv7l-orange)](#fleet-configuration)
[![Raspberry Pi OS](https://img.shields.io/badge/Pi%20OS-Bookworm%20%7C%20Bullseye%20%7C%20Buster-A81D33?logo=debian&logoColor=white)](#fleet-configuration)
[![Fleet size](https://img.shields.io/badge/fleet-up%20to%2020%20nodes-success)](#fleet-configuration)

<!-- Stack -->
[![Docker Compose](https://img.shields.io/badge/Docker%20Compose-v2-2496ED?logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Node-RED](https://img.shields.io/badge/Node--RED-3.1-8F0000?logo=nodered&logoColor=white)](https://nodered.org)
[![Node.js](https://img.shields.io/badge/Node.js-20%20LTS-5FA04E?logo=nodedotjs&logoColor=white)](https://nodejs.org)
[![OpenSSH](https://img.shields.io/badge/SSH-OpenSSH-4EAA25?logo=gnubash&logoColor=white)](https://www.openssh.com/)
[![MQTT](https://img.shields.io/badge/MQTT-Mosquitto-3C5280?logo=eclipsemosquitto&logoColor=white)](https://mosquitto.org)
[![Ubuntu](https://img.shields.io/badge/base-Ubuntu%2022.04-E95420?logo=ubuntu&logoColor=white)](https://ubuntu.com)

**[Quick Start](#quick-start)** · **[Features](#features)** · **[Architecture](#architecture)** · **[Test Playground](TEST-PLAYGROUND.md)** · **[API](#api)** · **[Troubleshooting](#troubleshooting)**

</div>

---

## At a Glance

| | |
|---|---|
| **What** | A web GUI that spawns 1-20 Docker containers, each one looking like a Raspberry Pi over SSH |
| **Who it's for** | Anyone building or testing fleet managers, deployment pipelines, Ansible playbooks, OTA updaters or IoT dashboards |
| **How** | `docker compose up -d` → open `localhost:7070` → add nodes → **Spawn Fleet** |
| **You get** | Per node: real SSH on `:3000+`, real Node-RED on `:4000+`, ARM arch, Raspberry Pi OS, metrics, MQTT tools |
| **Then** | Point your tool at the fleet - or export `pi-fleet-nodes.json` and import it into EdgeShell |
| **Reset** | One click. Respawn a clean fleet in seconds. |

---

## Table of Contents

- [At a Glance](#at-a-glance)
- [Features](#features)
- [Why This Exists](#why-this-exists)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [What Each Node Simulates](#what-each-node-simulates)
- [Fleet Configuration](#fleet-configuration)
- [Connecting a Fleet Manager (EdgeShell)](#connecting-a-fleet-manager-edgeshell)
- [Test Playground](#test-playground)
- [Security Notes](#security-notes)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure) · [API](#api)
- [Contributing](#contributing)
- [License](#license)

---

## Features

<table>
<tr>
<td width="33%" valign="top">

**🖥️ One-click fleet**

Single-page GUI: add 64-bit or 32-bit nodes, name them, pick a Debian version, spawn. Stop, reset and restore your last fleet anytime.

</td>
<td width="33%" valign="top">

**🔐 Real services**

Genuine OpenSSH and Node-RED on every node. A `pi` user with passwordless sudo, like a stock Pi. Mosquitto preinstalled for MQTT.

</td>
<td width="33%" valign="top">

**🍓 Looks like a Pi**

`uname -m`, `platform.machine()` and `/etc/os-release` report ARM and Raspberry Pi OS. Simulated temperature, `docker` and `systemctl`.

</td>
</tr>
<tr>
<td valign="top">

**🌐 Real networking**

Nodes share a `10.20.0.0/24` network with fixed IPs, so they can talk to each other. They can also join your fleet manager's Docker network.

</td>
<td valign="top">

**📤 Export & integrate**

Export the running fleet as JSON for EdgeShell, or script everything through the small REST API.

</td>
<td valign="top">

**✅ Tested in CI**

Every push builds the images, spawns a 2-node fleet and checks the arch, OS, SSH, Node-RED, MQTT and the export.

</td>
</tr>
</table>

---

## Why This Exists

Testing fleet management tools against real Raspberry Pis is slow, expensive and fragile: you need physical devices, a local network and SSH set up on each one, and you can't easily reset to a clean state.

Pi Fleet Emulator spins up Pi-like containers in Docker that:

- Run a **real SSH server** (OpenSSH, not a mock)
- Run a **real Node-RED** instance you can open in the browser
- Report **ARM architecture** (`armv7l` / `aarch64`) through `uname -m` and Python's `platform.machine()`
- Report **Raspberry Pi OS** in `/etc/os-release`
- Have a **sudo-enabled `pi` user**, matching Pi defaults
- Answer **`docker` and `systemctl`** with simulated output so monitoring tools work

To any SSH-based management tool, the fleet looks like real hardware. Tear it down and respawn it in minutes.

> **Note:** nodes *report* ARM, but run natively on your host's CPU. Use this to test management, deployment and monitoring flows - not to test ARM-compiled binaries.

---

## Quick Start

**Prerequisites:** Docker Desktop (Windows/macOS) or Docker Engine with the Compose plugin (Linux).

```bash
git clone https://github.com/855princekumar/pi-fleet-emulator.git
cd pi-fleet-emulator
docker compose up -d
```

Open **http://localhost:7070**, then:

1. Click **+ 64-bit** or **+ 32-bit** for each Pi node you want
2. Name each node and choose a Debian version
3. Click **Spawn Fleet**
4. Nodes appear under **Running Nodes** - the first spawn builds the node image and takes 2-5 minutes; later spawns take seconds

Verify a node:

```bash
ssh pi@localhost -p 3000        # password: raspberry
uname -m                        # aarch64 or armv7l
cat /etc/os-release | head -3   # Raspberry Pi OS
cat /tmp/metrics/summary.txt    # simulated metrics
```

**Stop:** click **Stop** in the GUI (keeps your config), or the red **Reset** button to also forget it. Then stop the spawner itself:

```bash
docker compose down
```

The fleet config persists in a Docker volume - next time, click **Restore into UI** to reload it.

<details>
<summary><b>Alternative: run the spawner without Docker (Python 3.10+)</b></summary>

Useful when developing the spawner itself. Docker is still needed for the Pi nodes.

```bash
python run.py
```

`run.py` creates a `venv/`, installs `requirements.txt`, checks Docker is reachable and serves the GUI on http://localhost:7070. Fleet config and the generated compose file are written to the repo root (both gitignored).

</details>

---

## Architecture

```mermaid
graph TD
    Browser["🌐 Browser<br/>http://localhost:7070"]
    Browser -->|HTTP| Spawner

    subgraph SpawnerContainer["pi-fleet-spawner container"]
        Spawner["Flask Spawner GUI"]
        Spawner -->|"fleet-config.json<br/>docker-compose.generated.yml"| Vol[("spawner_data volume")]
    end

    Spawner -->|"docker compose -p pi-fleet up<br/>(via /var/run/docker.sock)"| DockerEngine

    subgraph DockerEngine["Docker Engine (host)"]
        N1["📦 pi-emu-node-1<br/>SSH:3000 NR:4000<br/>10.20.0.20"]
        N2["📦 pi-emu-node-2<br/>SSH:3001 NR:4001<br/>10.20.0.21"]
        N3["📦 pi-emu-node-N<br/>SSH:300N NR:400N"]
        FleetNet["pi_fleet_net<br/>10.20.0.0/24"]
        N1 --- FleetNet
        N2 --- FleetNet
        N3 --- FleetNet
    end

    Spawner -->|"Export pi-fleet-nodes.json"| EdgeShell["🔧 Fleet manager<br/>(e.g. EdgeShell)"]
    EdgeShell -->|"SSH via host.docker.internal"| N1
    EdgeShell -->|"SSH via host.docker.internal"| N2

    User["👤 Developer"]
    User -->|"ssh pi@localhost -p 3000"| N1
    User -->|"Node-RED UI localhost:4000"| N1
```

### Node internals

```mermaid
graph LR
    subgraph Node["Each Pi node container (Ubuntu 22.04 base)"]
        SSHD["OpenSSH<br/>port 22"] --> S
        NR["Node-RED<br/>port 1880"] --> S
        S["Simulation layer<br/>(entrypoint.sh)"]
        S --> A["uname -m<br/>→ armv7l / aarch64"]
        S --> B["/etc/os-release<br/>→ Raspberry Pi OS"]
        S --> C["fake-metrics.sh<br/>CPU · RAM · Disk · Temp · Load"]
        S --> D["/usr/local/bin/docker<br/>(simulated)"]
        S --> E["/usr/local/bin/systemctl<br/>(simulated)"]
    end
```

### Workflow

```mermaid
flowchart LR
    A["1️⃣ Configure<br/>size, arch, Debian"] --> B["2️⃣ Spawn<br/>SSH + Node-RED nodes"]
    B --> C["3️⃣ Develop<br/>test your tool<br/>against live SSH"]
    C --> D["4️⃣ Validate<br/>deploys, logs,<br/>monitoring"]
    D --> E["5️⃣ Export<br/>pi-fleet-nodes.json"]
    E --> F["6️⃣ Production<br/>swap in real Pi IPs"]
```

---

## What Each Node Simulates

| Feature | Real Pi behaviour | How it's simulated |
|---|---|---|
| **SSH** | OpenSSH server | Genuine `sshd`, password auth (`pi` / `raspberry`) |
| **Node-RED** | Node-RED service | Real Node-RED process under supervisord |
| **`uname -m`** | `armv7l` or `aarch64` | Wrapper at `/usr/local/bin/uname` |
| **OS** | Raspberry Pi OS | `/etc/os-release` written at boot, matching the chosen Debian version (10/11/12) |
| **`platform.machine()`** | Returns the arch | Patched via a `.pth` file in Python site-packages |
| **CPU / load** | `/proc/stat`, `/proc/loadavg` | Container's real values |
| **Memory** | `/proc/meminfo` | Container's real values (host memory unless you set limits) |
| **Temperature** | `vcgencmd measure_temp` | Simulated value in `/tmp/fake_temp`, written by `fake-metrics.sh` |
| **Docker** | `docker ps` lists containers | Simulated binary at `/usr/local/bin/docker` |
| **systemctl** | `is-active node-red` → `active` | Simulated binary at `/usr/local/bin/systemctl` |
| **Sudo** | Passwordless sudo for `pi` | Same as a stock Pi |
| **MQTT** | Mosquitto broker / clients | `mosquitto`, `mosquitto_pub`, `mosquitto_sub` preinstalled (broker not started by default) |

Run `node-info` inside a node for a quick diagnostic summary.

---

## Fleet Configuration

| Setting | Default | Description |
|---|---|---|
| Architecture | `aarch64` | `aarch64` (64-bit, Pi 4/5) or `armv7l` (32-bit, Pi 2/3) - per node |
| Debian version | Bookworm | Bookworm (12), Bullseye (11) or Buster (10) - per node |
| Base SSH port | 3000 | Node 1 → host:3000, node 2 → host:3001, … |
| Base Node-RED port | 4000 | Node 1 → host:4000, node 2 → host:4001, … |
| Fleet subnet | `10.20.0.0/24` | Internal Docker network; nodes get `.20`, `.21`, … |
| SSH user / password | `pi` / `raspberry` | Pi defaults |
| Max nodes | 20 | Per fleet |

Node names are normalised to lowercase letters, digits and dashes and become container names (`pi-emu-<name>`).

### Environment variables (spawner)

| Variable | Default | Purpose |
|---|---|---|
| `PFE_DATA_DIR` | `/data` in Docker, repo root with `run.py` | Where `fleet-config.json` and `docker-compose.generated.yml` are kept |
| `PFE_NODE_BASE` | `<repo>/node-base` | Build context for the Pi node image |

---

## Connecting a Fleet Manager (EdgeShell)

The emulator was built as a test bed for **EdgeShell**, but the export is plain JSON (name, host, port, user), so any SSH-based fleet tool can use it.

1. **Export** - in the GUI, click **Export as EdgeShell JSON** → `pi-fleet-nodes.json`
2. **Import** - EdgeShell → **Nodes → Import** → upload the file, enter password `raspberry`. Leave "Replace host.docker.internal" **off** if EdgeShell also runs in Docker.
3. **Test** - click **Test Connection** on any node; it should go green.

**Networking:** by default the export points at `host.docker.internal:<ssh_port>`, which works from another container on Docker Desktop. If your fleet manager runs in Docker, you can instead click **Detect** under **EdgeShell Network Bridge** and pick its network before spawning: nodes join that network and the export uses container names on port 22. If your tool runs directly on the host, use `localhost` and the SSH port.

```mermaid
sequenceDiagram
    participant PFE as Pi Fleet Emulator
    participant ES  as EdgeShell
    participant N   as Pi Node Container

    PFE->>N: docker compose up (SSH + Node-RED)
    N-->>PFE: Containers running ✓
    PFE->>ES: Export pi-fleet-nodes.json
    ES->>ES: Import nodes (host.docker.internal, port 3000…)
    ES->>N:  SSH → host.docker.internal:3000
    N-->>ES: Connected ✓
    ES->>N:  Collect metrics, deploy files, run commands
    N-->>ES: Results
```

---

## Test Playground

[TEST-PLAYGROUND.md](TEST-PLAYGROUND.md) has step-by-step, validated scenarios that run on the emulated fleet:

1. **Two-node chat session** - MQTT pub/sub between two nodes
2. **Multi-node telemetry broadcast** - every node publishes to a shared broker
3. **Bulk fleet stress simulation** - load across the whole fleet

It also includes a resource consumption reference so you can size your fleet for your machine.

---

## Security Notes

This is a **local test bed**, not something to expose on a network.

- **The spawner controls your Docker engine.** It mounts `/var/run/docker.sock`, which is root-equivalent on the host. Its port is bound to `127.0.0.1` only - keep it that way and don't put it behind a public proxy.
- **Nodes use well-known credentials** (`pi` / `raspberry`, passwordless sudo), and their SSH and Node-RED ports are published on all interfaces so other containers and tools can reach them. On a shared or untrusted network, firewall ports 3000-3019 and 4000-4019, or spawn fewer nodes.
- Node names, architectures, Debian versions, subnet and ports are validated before they reach the generated compose file.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Spawn hangs on first run | The node image is building (apt + npm). Give it 2-5 min; check `docker compose logs -f` for the spawner. |
| `port is already allocated` | Another service uses 3000/4000. Change **Base SSH port** / **Base Node-RED port** in the GUI. |
| `Pool overlaps with other one on this host` | Change **Fleet subnet** (e.g. `10.30.0`). |
| SSH `Connection refused` right after spawn | sshd starts a few seconds after the container - retry. |
| `ssh` warns *REMOTE HOST IDENTIFICATION HAS CHANGED* | Respawned nodes get new host keys: `ssh-keygen -R "[localhost]:3000"`. |
| `host.docker.internal` doesn't resolve (Linux) | Add `extra_hosts: ["host.docker.internal:host-gateway"]` to your fleet manager's container, or use the shared-network option. |
| Removing everything | Click **Reset** in the GUI, then `docker compose down -v` (also deletes the saved config volume). |

---

## Project Structure

```
pi-fleet-emulator/
├── Dockerfile                  ← Spawner image (Flask + gunicorn + Docker CLI)
├── docker-compose.yml          ← Spawner stack (recommended way to run)
├── run.py                      ← Alternative: run the spawner on the host
├── requirements.txt
├── README.md
├── TEST-PLAYGROUND.md          ← Validated MQTT / telemetry / stress scenarios
├── LICENSE-MIT
├── LICENSE-APACHE
├── assets/banner.svg           ← Animated hero banner
├── .github/workflows/ci.yml    ← Lint + end-to-end fleet smoke test
│
├── spawner/
│   ├── app.py                  ← Flask spawner (API + GUI, compose generator)
│   └── templates/
│       └── index.html          ← Single-page fleet configurator
│
└── node-base/                  ← Pi node image (built on first spawn)
    ├── Dockerfile              ← Ubuntu 22.04 + OpenSSH + Node-RED
    ├── supervisord.conf        ← Runs sshd, Node-RED and fake-metrics
    └── scripts/
        ├── entrypoint.sh       ← Boot: arch, os-release, logs, supervisord
        ├── fake-metrics.sh     ← CPU / memory / temp / load metrics
        ├── fake-docker-stats.sh← Simulated docker + systemctl binaries
        └── node-info.sh        ← Quick diagnostic helper
```

Runtime-generated (gitignored): `docker-compose.generated.yml`, `fleet-config.json`.

### API

The GUI is a thin client over a small JSON API, which you can also script against:

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/spawn` | Spawn a fleet - body: `{nodes:[{name,arch,debian}], network, base_ssh_port, base_nr_port, edgeshell_network}` |
| `POST` | `/api/stop` | Stop the fleet - body: `{keep_config: true}` |
| `POST` | `/api/clear-config` | Stop the fleet and delete saved config |
| `GET` | `/api/status` | Running nodes with SSH / Node-RED ports |
| `GET` | `/api/saved-config` | Last spawned config |
| `GET` | `/api/logs/<container>` | Last 120 log lines of a node |
| `GET` | `/api/detect-edgeshell-networks` | Docker networks whose name contains `edge` |
| `GET` | `/api/export-edgeshell` | Download `pi-fleet-nodes.json` |

---

## Contributing

Issues and pull requests are welcome. Good first areas: more simulated Pi commands (`vcgencmd`, `raspi-config`), GPIO stubs, and per-node resource limits.

When changing shell scripts under `node-base/`, keep LF line endings (enforced by `.gitattributes`) - CRLF breaks them inside the container.

Every pull request runs [CI](.github/workflows/ci.yml): Python and shell syntax checks, then a real 2-node spawn that checks the arch, OS, SSH, Node-RED, MQTT and the export. To run the same checks locally, follow the steps in that file.

---

## License

Pi Fleet Emulator is a free, open side project by [@855princekumar](https://github.com/855princekumar), open to anyone to use, modify and share.

It is dual-licensed under your choice of:

- [MIT License](LICENSE-MIT)
- [Apache License 2.0](LICENSE-APACHE)

Pick whichever suits your project. MIT is the simplest; Apache 2.0 adds an explicit patent grant.

Unless you state otherwise, any contribution you submit is dual-licensed the same way, with no additional terms.
