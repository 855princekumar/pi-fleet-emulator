# Pi Fleet Emulator - Test Playground

[![Fleet](https://img.shields.io/badge/Fleet-MQTT%20Telemetry-1a56db)](.)
[![Protocol](https://img.shields.io/badge/Protocol-MQTT%202.0-orange)](.)
[![Nodes](https://img.shields.io/badge/Nodes-up%20to%2020-059669)](.)
[![Status](https://img.shields.io/badge/Validated-%E2%9C%85-success)](.)
[![EdgeShell](https://img.shields.io/badge/Works%20with-EdgeShell-7c3aed)](.)

> **Validated test cases for simulated fleet communication.**
> Real MQTT pub/sub, inter-node telemetry, and bulk fleet messaging
> across emulated Raspberry Pi nodes - no hardware required.

---

## Table of Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Test Case 1 - Two-Node Chat Session](#test-case-1--two-node-chat-session)
- [Test Case 2 - Multi-Node Telemetry Broadcast](#test-case-2--multi-node-telemetry-broadcast)
- [Test Case 3 - Bulk Fleet Stress Simulation](#test-case-3--bulk-fleet-stress-simulation)
- [Resource Consumption Reference](#resource-consumption-reference)
- [Troubleshooting](#troubleshooting)

---

## Architecture

### Fleet Network Topology

```mermaid
graph TD
    subgraph HOST["🖥️ Windows Host - Docker Desktop"]
        subgraph FLEET["pi_fleet_net - 10.20.0.0/24"]
            N1["📦 pi-emu-node-1
10.20.0.20
🟢 MQTT Broker :1883
SSH :3000 · NR :4000
ARMv7 32-bit"]
            N2["📦 pi-emu-node-2
10.20.0.21
🟣 MQTT Client
SSH :3001 · NR :4001
ARM64 64-bit"]
            N3["📦 pi-emu-node-3
10.20.0.22
🟡 MQTT Client
SSH :3002 · NR :4002"]
            NN["📦 pi-emu-node-N
10.20.0.2N
⬜ MQTT Client
SSH :300N · NR :400N
up to 20 nodes"]
        end
        ES["🔧 EdgeShell
localhost:5000"]
        PFE["🖱️ Pi Fleet Emulator
localhost:7070"]
    end

    N2 -->|"PUBLISH fleet/chat"| N1
    N1 -->|"DELIVER fleet/chat"| N2
    N1 -->|"DELIVER fleet/chat"| N3
    N1 -->|"DELIVER fleet/chat"| NN
    N3 -->|"PUBLISH fleet/telemetry/node-3"| N1
    NN -->|"PUBLISH fleet/telemetry/node-N"| N1

    ES -->|"SSH heartbeat
collect metrics"| N1
    ES -->|"SSH heartbeat"| N2
    ES -->|"SSH heartbeat"| N3
    PFE -->|"docker compose up
spawn nodes"| FLEET
```

### MQTT Message Flow

```mermaid
sequenceDiagram
    participant N1 as node-1 🟢 Broker<br/>10.20.0.20
    participant N2 as node-2 🟣<br/>10.20.0.21
    participant NN as node-N 🟡<br/>10.20.0.2N

    Note over N1: mosquitto starts<br/>listener 1883 0.0.0.0<br/>allow_anonymous true

    N2->>N1: CONNECT + SUBSCRIBE fleet/#
    N1-->>N2: CONNACK ✓
    NN->>N1: CONNECT + SUBSCRIBE fleet/#
    N1-->>NN: CONNACK ✓

    Note over N2: types "hello"
    N2->>N1: PUBLISH fleet/chat "[node-2] hello"
    N1-->>N2: DELIVER fleet/chat "[node-2] hello"
    N1-->>NN: DELIVER fleet/chat "[node-2] hello"

    Note over N1: types "hi back"
    N1->>N1: PUBLISH fleet/chat "[node-1] hi back"
    N1-->>N2: DELIVER fleet/chat "[node-1] hi back"
    N1-->>NN: DELIVER fleet/chat "[node-1] hi back"

    Note over N1,NN: Telemetry mode
    loop Every 1 second
        N1->>N1: PUBLISH fleet/telemetry/node-1 {json}
        N1-->>N2: DELIVER
        N1-->>NN: DELIVER
    end
```

---

## Prerequisites

### Spawn the fleet

Open **http://localhost:7070** → add nodes → **Spawn Fleet**

Minimum: **2 nodes**. Recommended for full test: **3-5 nodes** (mix 32-bit and 64-bit).

### Verify containers running

```bash
docker ps --filter name=pi-emu
```

```
pi-emu-node-2   Up 3 minutes   0.0.0.0:3001->22/tcp, 0.0.0.0:4001->1880/tcp
pi-emu-node-1   Up 3 minutes   0.0.0.0:3000->22/tcp, 0.0.0.0:4000->1880/tcp
```

Every node ships with `mosquitto` and `mosquitto-clients` preinstalled - no extra setup needed.

### Credentials

```
User:     pi
Password: raspberry
```

---

## Test Case 1 - Two-Node Chat Session

> **Proves:** Real inter-container MQTT pub/sub. Both nodes send and receive simultaneously on a shared topic.

```mermaid
flowchart LR
    A["🖥️ PowerShell 1\nssh pi@localhost -p 3000"] --> B["Start Mosquitto broker\n/tmp/mq/mq.conf"]
    B --> C["Subscribe fleet/chat\n127.0.0.1:1883"]
    C --> D["Publish loop\n read → mosquitto_pub"]

    E["🖥️ PowerShell 2\nssh pi@localhost -p 3001"] --> F["Subscribe fleet/chat\n10.20.0.20:1883"]
    F --> G["Publish loop\nread → mosquitto_pub"]

    D <-->|"fleet/chat\nreal-time"| G
```

---

### Window 1 - Node 1 - Broker + Chat

```powershell
ssh pi@localhost -p 3000
```
*Password: raspberry*

```bash
pkill mosquitto 2>/dev/null; sleep 1
mkdir -p /tmp/mq
cat > /tmp/mq/mq.conf << 'EOF'
listener 1883 0.0.0.0
allow_anonymous true
EOF
mosquitto -c /tmp/mq/mq.conf &
sleep 1
echo "Broker up on $(hostname -I | awk '{print $1}'):1883"
mosquitto_sub -h 127.0.0.1 -p 1883 -t fleet/chat &
while true; do
  read -p $'\n[node-1]> ' m
  mosquitto_pub -h 127.0.0.1 -p 1883 -t fleet/chat -m "[node-1] $m"
done
```

Wait for `[node-1]>` before opening Window 2.

---

### Window 2 - Node 2 - Client + Chat

```powershell
ssh pi@localhost -p 3001
```
*Password: raspberry*

```bash
pkill mosquitto_sub 2>/dev/null; sleep 1
mosquitto_sub -h 10.20.0.20 -p 1883 -t fleet/chat &
while true; do
  read -p $'\n[node-2]> ' m
  mosquitto_pub -h 10.20.0.20 -p 1883 -t fleet/chat -m "[node-2] $m"
done
```

### Expected output

**Node 1:**
```
Broker up on 10.20.0.20:1883
[node-1]>
fleet/chat [node-2] hello from node 2
[node-1]> hi back!
fleet/chat [node-1] hi back!
```

**Node 2:**
```
[node-2]> hello from node 2
fleet/chat [node-2] hello from node 2
fleet/chat [node-1] hi back!
[node-2]>
```

**Stop:** `Ctrl+C` on both windows.

---

## Test Case 2 - Multi-Node Telemetry Broadcast

> **Proves:** One publisher sends structured JSON sensor data every second. All subscriber nodes receive it - replicating a real IoT pipeline.

```mermaid
flowchart TD
    PUB["node-1\nPublishes every 1s\nfleet/telemetry/node-1\n{temp, cpu, mem, ts}"]
    PUB -->|MQTT deliver| S2["node-2\nmosquitto_sub\nfleet/telemetry/#"]
    PUB -->|MQTT deliver| S3["node-3\nmosquitto_sub\nfleet/telemetry/#"]
    PUB -->|MQTT deliver| SN["node-N\nmosquitto_sub\nfleet/telemetry/#"]
    S2 --> LOG["Terminal output\non each subscriber"]
    S3 --> LOG
    SN --> LOG
```

### Node 1 - Start broker + publish telemetry

```bash
pkill mosquitto 2>/dev/null; sleep 1
mkdir -p /tmp/mq
cat > /tmp/mq/mq.conf << 'EOF'
listener 1883 0.0.0.0
allow_anonymous true
EOF
mosquitto -c /tmp/mq/mq.conf &
sleep 1

while true; do
  CPU=$(awk '{printf "%d", $1*100}' /proc/loadavg)
  MEM=$(free | awk '/Mem/{printf "%d", $3/$2*100}')
  TEMP=$((40 + RANDOM % 25))
  TS=$(date -u +%s)
  MSG="{\"node\":\"node-1\",\"temp\":$TEMP,\"cpu\":$CPU,\"mem\":$MEM,\"ts\":$TS}"
  mosquitto_pub -h 127.0.0.1 -p 1883 -t fleet/telemetry/node-1 -m "$MSG"
  echo "$MSG"
  sleep 1
done
```

### All other nodes - subscribe

```bash
# Run this on node-2, node-3, node-N
mosquitto_sub -h 10.20.0.20 -p 1883 -t "fleet/telemetry/#" -v
```

### Expected output on subscribers

```
fleet/telemetry/node-1 {"node":"node-1","temp":53,"cpu":4,"mem":68,"ts":1783606900}
fleet/telemetry/node-1 {"node":"node-1","temp":51,"cpu":2,"mem":69,"ts":1783606901}
fleet/telemetry/node-1 {"node":"node-1","temp":57,"cpu":5,"mem":68,"ts":1783606902}
```

**Stop:** `Ctrl+C` on all nodes.

---

## Test Case 3 - Bulk Fleet Stress Simulation

> **Proves:** All nodes publish simultaneously to the same broker. Demonstrates concurrent connections and message throughput. EdgeShell monitors resources fleet-wide while traffic runs.

```mermaid
flowchart LR
    subgraph Fleet["All Nodes - Simultaneous Publishers"]
        N1["node-1\nPublishes + Broker"]
        N2["node-2\nPublishes"]
        N3["node-3\nPublishes"]
        NN["node-N\nPublishes"]
    end
    N1 -->|fleet/telemetry/node-1| BRK["Mosquitto\n10.20.0.20:1883"]
    N2 -->|fleet/telemetry/node-2| BRK
    N3 -->|fleet/telemetry/node-3| BRK
    NN -->|fleet/telemetry/node-N| BRK
    BRK -->|"Delivers to ALL\nsubscribers"| ALL["All Nodes\nreceive all telemetry"]
    ES["EdgeShell\nMonitoring"] -->|"SSH heartbeat\nevery 15s"| Fleet
```

### Step 1 - Via EdgeShell Terminal (all nodes at once)

In EdgeShell → **Terminal** → select **all nodes** → send:

```bash
sudo apt install -y mosquitto-clients -qq 2>/dev/null && echo "Ready: $(hostname)"
```

### Step 2 - Select all nodes EXCEPT node-1, send:

```bash
NODE=$(hostname)
BROKER=10.20.0.20
for i in $(seq 1 20); do
  CPU=$(awk '{printf "%d", $1*100}' /proc/loadavg)
  MEM=$(free | awk '/Mem/{printf "%d", $3/$2*100}')
  TEMP=$((38 + RANDOM % 28))
  mosquitto_pub -h $BROKER -p 1883 \
    -t "fleet/telemetry/$NODE" \
    -m "{\"node\":\"$NODE\",\"temp\":$TEMP,\"cpu\":$CPU,\"mem\":$MEM,\"seq\":$i}" \
    2>/dev/null
  sleep 1
done
echo "Done: 20 messages sent from $NODE"
```

### Step 3 - Monitor all nodes simultaneously

While traffic runs, in EdgeShell → **Monitoring** → click **Refresh All**.

Or via Terminal, select all nodes:

```bash
echo "=== $(hostname) $(date -u +%H:%M:%S) ===" \
  && cat /proc/loadavg \
  && free -h | grep Mem
```

### Step 4 - Subscribe to all telemetry on node-1

```bash
# On node-1
mosquitto_sub -h 127.0.0.1 -p 1883 -t "fleet/telemetry/#" -v
```

You will see telemetry from every node arriving simultaneously:

```
fleet/telemetry/pi-emu-node-2 {"node":"pi-emu-node-2","temp":44,"cpu":3,"mem":71,"seq":1}
fleet/telemetry/pi-emu-node-3 {"node":"pi-emu-node-3","temp":51,"cpu":2,"mem":69,"seq":1}
fleet/telemetry/pi-emu-node-4 {"node":"pi-emu-node-4","temp":47,"cpu":4,"mem":72,"seq":1}
fleet/telemetry/pi-emu-node-2 {"node":"pi-emu-node-2","temp":46,"cpu":3,"mem":71,"seq":2}
```

---

## Resource Consumption Reference

Measured during validated test runs on Windows 11, Docker Desktop, 16GB RAM:

| Scenario | CPU per node | RAM per node | Network |
|---|---|---|---|
| Idle - SSH only | < 1% | ~80 MB | negligible |
| Chat session (2 nodes) | 2-5% | ~90 MB | < 1 KB/s |
| Telemetry 1 msg/s | 3-8% | ~95 MB | ~2 KB/s |
| Bulk stress - all nodes | 10-25% | ~100 MB | ~10 KB/s |
| Node-RED active | 15-30% | ~120 MB | ~5 KB/s |
| EdgeShell heartbeat | +1-3% | +5 MB | ~0.5 KB/s |

---

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `Connection refused` from node-2 | Broker not on `0.0.0.0` | Use exact broker command with `/tmp/mq/mq.conf` config |
| `systemctl: simulated` | Fake systemctl in container | Start mosquitto directly: `mosquitto -c /tmp/mq/mq.conf &` |
| Subscriber exits instantly | Node-2 had its own Mosquitto | Run `pkill mosquitto` on node-2 before subscribing |
| No messages on subscriber | Wrong broker IP | Get correct IP with `hostname -I` on node-1 |
| `ping: command not found` | Not in slim image | Use `hostname -I` instead - ping not needed |
| Messages only echo locally | Node-1 subscriber missing | Re-run node-1 block - include the `mosquitto_sub &` line |
| Broker won't start | Port 1883 in use | Run `pkill mosquitto; sleep 1` then restart |

---

## Key Takeaways

This playground validates that Pi Fleet Emulator faithfully replicates a real Raspberry Pi fleet for:

- **Real MQTT networking** - identical to physical Pi nodes on a LAN
- **Cross-architecture fleet** - 32-bit ARMv7 and 64-bit ARM64 nodes co-existing
- **Concurrent pub/sub** - multiple publishers, multiple subscribers, zero collision
- **EdgeShell integration** - deploy, monitor, and execute across all nodes while MQTT traffic runs
- **Production IoT pattern** - sensor → broker → gateway → cloud pipeline validated end-to-end

The only gap from real hardware is GPIO/camera. All networking, protocol, and software behaviour is genuine.

---

*Part of [Pi Fleet Emulator](README.md) · Works with EdgeShell*
