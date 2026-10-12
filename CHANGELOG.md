# Changelog

All notable changes to Pi Fleet Emulator. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/). Each version here matches a git tag `vX.Y.Z`, a [GitHub Release](https://github.com/855princekumar/pi-fleet-emulator/releases) and the Docker Hub image tags `X.Y.Z` of [`pi-fleet-spawner`](https://hub.docker.com/r/devprincekumar/pi-fleet-spawner) and [`pi-fleet-node`](https://hub.docker.com/r/devprincekumar/pi-fleet-node).

## [1.1.0] - 2026-10-12

First public release.

### Added
- Unit test suite (93 tests, Docker mocked): input validation, request guard, compose generation, fleet validation and the `pfe` CLI. Runs in CI on every push and pull request.
- `CHANGELOG.md`; release notes are now taken from it.
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, issue templates (bug, feature) and a pull request template.
- Social preview image (`assets/social-preview.png`).

### Changed
- README project structure lists every file, including the security and community files.

## [1.0.2] - 2026-10-12

### Changed
- Flask `>=3.1.3`, Gunicorn `>=26.2.0`.
- GitHub Actions moved to their current major versions (all pinned to verified commit SHAs).
- The node image keeps the `pi` user at UID 1000 on newer Ubuntu bases, so existing `/home/pi` volumes keep working after base upgrades.

### Added
- CI `release-dry-run` job: builds both images with the exact release actions on every pull request.

## [1.0.1] - 2026-10-11

Security release from a red-team audit. **Upgrade from 1.0.0.**

### Security
- The node image no longer ships SSH host keys. In 1.0.0 every node shared the same keys and anyone pulling the image had the private keys. Keys are now generated per container.
- The spawner API refuses DNS-rebinding requests (`Host` allowlist, `PFE_ALLOWED_HOSTS`) and cross-site requests (`Origin` check, JSON-only writes), and sends CSP, `X-Frame-Options: DENY`, `nosniff` and `no-referrer` headers. CDN assets carry SRI hashes.
- Node SSH and Node-RED ports bind to `127.0.0.1` by default (`PFE_BIND_ADDR`).
- The node password is set at container start (`PFE_NODE_PASSWORD`) instead of being baked into the image history.
- Removed the `SYS_PTRACE` capability from nodes and pip/setuptools/wheel from the spawner image.
- Workflows pin every action to a commit SHA, do not persist credentials, and use least-privilege permissions.
- CI security job: fails on secrets in images, fixable critical CVEs or critical misconfigurations.

### Changed
- Node-RED 5.0.8 on Node.js 22 LTS with npm 12.2.0 (from Node-RED 3.1 / Node.js 20). Critical CVEs in the node image: 6 to 0.

### Added
- `PFE_PROJECT` to run several spawners on one host without them touching each other's nodes. Status, export, validate and reset only see their own project.
- Dependabot, `SECURITY.md`, `.dockerignore`, GitHub branch and tag protection.

## [1.0.0] - 2026-10-11

Initial release. **Unsupported: shipped shared SSH host keys, use 1.0.1 or later.**

### Added
- Web GUI, REST API and `pfe` CLI to spawn, scale, validate, stop and reset fleets of 1 to 20 simulated Raspberry Pi nodes.
- Nodes with real OpenSSH and Node-RED, `aarch64` / `armv7l` and Raspberry Pi OS reporting, simulated metrics, `docker` and `systemctl`, Mosquitto MQTT tools.
- Persistent fleet config and per-node `/home/pi` volumes.
- Multi-arch images on Docker Hub, tag-driven release workflow, end-to-end CI.

[1.1.0]: https://github.com/855princekumar/pi-fleet-emulator/compare/v1.0.2...v1.1.0
[1.0.2]: https://github.com/855princekumar/pi-fleet-emulator/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/855princekumar/pi-fleet-emulator/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/855princekumar/pi-fleet-emulator/releases/tag/v1.0.0
