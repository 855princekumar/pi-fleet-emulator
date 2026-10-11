<p align="center">
  <img src="https://cdn.jsdelivr.net/gh/855princekumar/pi-fleet-emulator@main/assets/banner.svg" alt="Pi Fleet Emulator" width="100%">
</p>

# Pi Fleet Emulator

**Spawn a realistic Raspberry Pi fleet in Docker - no hardware required.**

One container gives you a web GUI and a CLI that spawn **1 to 20 simulated Raspberry Pi nodes**. Each node runs a **real OpenSSH server** and **real Node-RED**, reports **`aarch64` / `armv7l`** and **Raspberry Pi OS**, and ships with simulated metrics, `docker`, `systemctl` and MQTT tools. Point any SSH-based fleet tool, Ansible playbook or CI pipeline at it and test against a fleet you can reset in seconds.

[GitHub](https://github.com/855princekumar/pi-fleet-emulator) · [Full docs](https://github.com/855princekumar/pi-fleet-emulator#readme) · [Test Playground](https://github.com/855princekumar/pi-fleet-emulator/blob/main/TEST-PLAYGROUND.md) · License: MIT or Apache 2.0

---

## Images

| Image | What it is |
|---|---|
| [`devprincekumar/pi-fleet-spawner`](https://hub.docker.com/r/devprincekumar/pi-fleet-spawner) | Web GUI (port 7070) + `pfe` CLI + REST API. Creates the nodes through the Docker socket. |
| [`devprincekumar/pi-fleet-node`](https://hub.docker.com/r/devprincekumar/pi-fleet-node) | The simulated Raspberry Pi node. Pulled automatically by the spawner. |

**Tags:** `1.0.0`, `latest` · **Platforms:** `linux/amd64`, `linux/arm64` (Windows, macOS incl. Apple Silicon, Linux, Raspberry Pi 4/5)

---

## Quick start (60 seconds)

**1. Save this as `docker-compose.yml`:**

```yaml
services:
  pi-fleet-spawner:
    image: devprincekumar/pi-fleet-spawner:1.0.0
    container_name: pi-fleet-spawner
    restart: unless-stopped
    ports:
      - "127.0.0.1:7070:7070"          # GUI, localhost only
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock   # lets it create the nodes
      - pi_fleet_data:/data                         # fleet config persists here
    environment:
      PFE_NODE_IMAGE: devprincekumar/pi-fleet-node:1.0.0
      PFE_PERSIST_HOME: "1"            # each node keeps its /home/pi

volumes:
  pi_fleet_data:
    name: pi_fleet_data
```

Or download it: `curl -O https://raw.githubusercontent.com/855princekumar/pi-fleet-emulator/main/docker-compose.hub.yml`

**2. Start it:**

```bash
docker compose up -d
```

**3. Spawn a fleet** - in the browser at **http://localhost:7070**, or from the CLI:

```bash
docker exec pi-fleet-spawner pfe spawn 3 --validate
```

**4. Use it:**

```bash
ssh pi@localhost -p 3000        # password: raspberry
uname -m                        # aarch64
```

Node-RED for node 1 is at **http://localhost:4000**, node 2 at `:4001`, and so on.

---

## The `pfe` CLI

Everything the GUI does, scriptable. Run it with `docker exec pi-fleet-spawner pfe <command>`.

| Command | What it does |
|---|---|
| `pfe spawn 5` | Fresh fleet of 5 nodes (alternating 64-bit / 32-bit). Options: `--arch` (aarch64, armv7l or mixed), `--debian` (bookworm, bullseye or buster), `--subnet`, `--ssh-port`, `--nr-port` |
| `pfe scale 10` | Grow or shrink the fleet to 10. Existing nodes keep running untouched |
| `pfe validate` | Checks every node: running, arch, OS, SSH, Node-RED, metrics, plus node-to-node MQTT. Exit code 0 = all PASS |
| `pfe status` | Nodes with their SSH and Node-RED host ports (`--json` for scripts) |
| `pfe health` | Confirms the spawner can reach Docker and shows which node image it uses |
| `pfe stop` | Stops all nodes. Config and node data are kept |
| `pfe reset --yes` | Removes all nodes, the saved config and every node's data |
| `pfe export` | Prints the fleet as JSON for EdgeShell or other tools |

Add `--validate` to `spawn` or `scale` to check the fleet once it is up (it waits up to `--wait 120` seconds for services to start).

Sample `pfe validate` output:

```
NODE                  ARCH     RUNNING   ARCH      OS        SSH       NODE_RED  METRICS
pi-emu-node-1         aarch64  PASS      PASS      PASS      PASS      PASS      PASS
pi-emu-node-2         armv7l   PASS      PASS      PASS      PASS      PASS      PASS

MQTT pi-emu-node-2 -> pi-emu-node-1: PASS

2/2 nodes running. Fleet: PASS
```

---

## Persistent data

Everything lives in Docker named volumes, so it survives container restarts, image upgrades and host reboots.

| Volume | Contents | Removed by |
|---|---|---|
| `pi_fleet_data` | Fleet config + generated compose file (spawner `/data`) | `docker compose down -v` |
| `pi-fleet_pi-emu-<name>-home` | Each node's `/home/pi`: Node-RED flows, files you copy in | `pfe reset --yes` or GUI **Reset** |

- **Stop / start** (`pfe stop`, then `pfe scale N` or GUI **Restore into UI** + **Spawn**): nodes come back with their data.
- **Scaling down** keeps the removed node's volume, so scaling back up restores it.
- **Throwaway nodes:** set `PFE_PERSIST_HOME: "0"` for a clean `/home/pi` on every spawn.
- **Back up:** `docker run --rm -v pi_fleet_data:/d -v "$PWD":/b alpine tar czf /b/pi-fleet-config.tgz -C /d .`

---

## What each node simulates

| On the node | Result |
|---|---|
| `ssh pi@localhost -p 3000` | Real OpenSSH, password `raspberry`, passwordless sudo |
| `uname -m`, `python3 -c "import platform; print(platform.machine())"` | `aarch64` or `armv7l` |
| `cat /etc/os-release` | Raspberry Pi OS, Debian 12 / 11 / 10 |
| `http://localhost:4000` | Real Node-RED 3.1 (Node.js 20) |
| `cat /tmp/metrics/summary.txt`, `/tmp/fake_temp` | Simulated CPU, RAM, disk, temperature |
| `docker ps`, `systemctl is-active node-red` | Simulated output, so monitoring tools work |
| `mosquitto`, `mosquitto_pub`, `mosquitto_sub` | Preinstalled for MQTT tests |

Nodes share the `10.20.0.0/24` network (node 1 = `10.20.0.20`, node 2 = `.21`, ...) so they can talk to each other.

> Nodes *report* ARM but run on your host's CPU. Use this to test management, deployment and monitoring, not ARM binaries.

---

## Configuration

| Variable (spawner) | Default | Purpose |
|---|---|---|
| `PFE_NODE_IMAGE` | `devprincekumar/pi-fleet-node:1.0.0` in the compose above | Node image to run. Empty = build from bundled source |
| `PFE_PERSIST_HOME` | `1` | `1` = persistent `/home/pi` per node, `0` = throwaway |
| `PFE_DATA_DIR` | `/data` | Where config is stored inside the spawner |

| Fleet setting | Default | Range |
|---|---|---|
| Nodes | - | 1 to 20 |
| SSH host ports | 3000, 3001, ... | `--ssh-port` |
| Node-RED host ports | 4000, 4001, ... | `--nr-port` |
| Subnet | `10.20.0` | `--subnet` |

**REST API** (same as the GUI uses): `POST /api/spawn`, `POST /api/stop`, `POST /api/clear-config`, `GET /api/status`, `GET /api/validate`, `GET /api/health`, `GET /api/export-edgeshell`, `GET /api/logs/<container>`.

---

## Security

This is a **local test bed**.

- The spawner mounts the Docker socket (root-equivalent on the host). Keep port 7070 bound to `127.0.0.1` as above.
- Nodes use well-known credentials (`pi` / `raspberry`) and publish SSH/Node-RED on all interfaces. Firewall ports 3000-3019 and 4000-4019 on untrusted networks.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `pfe validate` shows `NODE_RED FAIL` right after spawn | Node-RED takes ~20 s to start. Use `--validate` (it waits) or run again |
| `port is already allocated` | `pfe spawn N --ssh-port 5000 --nr-port 6000` |
| `Pool overlaps with other one` | `pfe spawn N --subnet 10.30.0` |
| Health check unhealthy | The Docker socket isn't mounted, or Docker isn't running |
| SSH host key warning after respawn | `ssh-keygen -R "[localhost]:3000"` |

---

Free and open source by [855princekumar](https://github.com/855princekumar). Licensed under your choice of [MIT](https://github.com/855princekumar/pi-fleet-emulator/blob/main/LICENSE-MIT) or [Apache 2.0](https://github.com/855princekumar/pi-fleet-emulator/blob/main/LICENSE-APACHE).
