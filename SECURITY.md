# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| Latest release (`latest`, `1`, `1.0` tags) | Yes |
| `1.0.0` | No - shipped shared SSH host keys, upgrade to the latest release |

## Reporting a vulnerability

Please **do not open a public issue** for security problems. Use GitHub's private reporting instead:
**[Report a vulnerability](https://github.com/855princekumar/pi-fleet-emulator/security/advisories/new)**

You'll get a reply within 7 days. Fixes ship as a new patch release with updated Docker images.

## Threat model

Pi Fleet Emulator is a **local test bed**. It is safe by default on a single machine, and needs care when exposed to a network.

| Component | Trust boundary | Default protection |
|---|---|---|
| Spawner GUI / API (`:7070`) | Holds the Docker socket = root on the host | Bound to `127.0.0.1`; rejects other `Host` headers (DNS rebinding), cross-origin and non-JSON writes (CSRF); CSP, `X-Frame-Options: DENY` |
| Node SSH / Node-RED (`:3000+`, `:4000+`) | Well-known login, passwordless sudo inside the node | Bound to `127.0.0.1`; per-container SSH host keys; root login disabled; not privileged, no Docker socket |
| Images | Supply chain | Multi-arch builds in CI from pinned actions, SBOM + provenance attestations, secret and CVE scans on every push |

### Exposing nodes to a network

Set `PFE_BIND_ADDR=0.0.0.0` only on a trusted network, and always pair it with `PFE_NODE_PASSWORD=<something strong>`. Anyone who can log in to a node has root inside that container.

### Accepted risks

- **Spawner runs as root** inside its container: it needs the Docker socket, whose group ID differs per host.
- **Nodes run sshd and supervisord as root** inside the container, like a real Pi.
- **Base-image CVEs without an upstream fix** are tracked by the weekly rebuild (Dependabot) and fixed when Debian / Ubuntu publish patches.
