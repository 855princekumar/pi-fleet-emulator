#!/usr/bin/env bash
# Build and push both images to Docker Hub for linux/amd64 + linux/arm64,
# then (optionally) set each repository's description on Docker Hub.
#
#   docker login -u devprincekumar
#   ./docker/publish.sh                 # version 1.1.0
#   ./docker/publish.sh 1.1.0
#   ./docker/publish.sh --describe-only # only update the Docker Hub descriptions
#
# Tags pushed per image: <version>, <major>.<minor>, <major>, latest
# Descriptions need DOCKERHUB_TOKEN (a Docker Hub personal access token with
# read/write scope). Without it the Docker Desktop sign-in is tried; if neither
# works the step is skipped and the files in docker/ can be pasted by hand.
set -euo pipefail

NAMESPACE="${PFE_NAMESPACE:-devprincekumar}"
PLATFORMS="${PFE_PLATFORMS:-linux/amd64,linux/arm64}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DESCRIBE_ONLY=0
if [ "${1:-}" = "--describe-only" ]; then DESCRIBE_ONLY=1; shift; fi
VERSION="${1:-1.1.0}"

[[ "$VERSION" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)$ ]] || { echo "Version must be X.Y.Z" >&2; exit 1; }
MAJOR="${BASH_REMATCH[1]}"; MINOR="${BASH_REMATCH[2]}"
REVISION="$(git -C "$ROOT" rev-parse HEAD 2>/dev/null || echo unknown)"
CREATED="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

SPAWNER_SHORT="Spawn, scale and validate a simulated Raspberry Pi fleet in Docker. Real SSH + Node-RED per node."
NODE_SHORT="Simulated Raspberry Pi node: real OpenSSH + Node-RED, reports aarch64/armv7l and Raspberry Pi OS."

build() {  # repo  context  title  description
  local repo="$1" ctx="$2" title="$3" desc="$4" img="$NAMESPACE/$1"
  echo "==> $img  $VERSION  ($PLATFORMS)"
  docker buildx build --builder pfe-builder --platform "$PLATFORMS" \
    --build-arg VERSION="$VERSION" --build-arg REVISION="$REVISION" --build-arg CREATED="$CREATED" \
    --annotation "index:org.opencontainers.image.title=$title" \
    --annotation "index:org.opencontainers.image.description=$desc" \
    --annotation "index:org.opencontainers.image.version=$VERSION" \
    --annotation "index:org.opencontainers.image.revision=$REVISION" \
    --annotation "index:org.opencontainers.image.created=$CREATED" \
    --annotation "index:org.opencontainers.image.source=https://github.com/855princekumar/pi-fleet-emulator" \
    --annotation "index:org.opencontainers.image.licenses=MIT OR Apache-2.0" \
    --annotation "index:org.opencontainers.image.authors=855princekumar" \
    --provenance=mode=max --sbom=true \
    -t "$img:$VERSION" -t "$img:$MAJOR.$MINOR" -t "$img:$MAJOR" -t "$img:latest" \
    --push "$ctx"
}

# Python is only used for JSON handling
PY="$(for c in python3 python; do "$c" -c 1 >/dev/null 2>&1 && { echo "$c"; break; }; done)"

hub_token() {
  if [ -n "${DOCKERHUB_TOKEN:-}" ]; then
    curl -sf -H 'Content-Type: application/json' \
      -d "{\"username\":\"$NAMESPACE\",\"password\":\"$DOCKERHUB_TOKEN\"}" \
      https://hub.docker.com/v2/users/login \
      | "$PY" -c 'import json,sys; print(json.load(sys.stdin)["token"])'
  elif command -v docker-credential-desktop >/dev/null 2>&1; then
    echo "https://index.docker.io/v1/access-token" | docker-credential-desktop get 2>/dev/null \
      | "$PY" -c 'import json,sys; print(json.load(sys.stdin)["Secret"])'
  fi
}

describe() {  # repo  short  markdown-file
  local body
  body="$(SHORT="$2" FILE="$3" "$PY" -c 'import json,os; print(json.dumps({"description": os.environ["SHORT"], "full_description": open(os.environ["FILE"], encoding="utf-8").read()}))')"
  if curl -sf -o /dev/null -X PATCH -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
       -d "$body" "https://hub.docker.com/v2/repositories/$NAMESPACE/$1/"; then
    echo "    description set: $NAMESPACE/$1"
  else
    echo "    could not set description for $NAMESPACE/$1 - paste $3 into its Overview by hand"
  fi
}

if [ "$DESCRIBE_ONLY" = 0 ]; then
  docker buildx inspect pfe-builder >/dev/null 2>&1 \
    || docker buildx create --name pfe-builder --driver docker-container >/dev/null
  build pi-fleet-node    "$ROOT/node-base" "Pi Fleet Emulator Node"    "$NODE_SHORT"
  build pi-fleet-spawner "$ROOT"           "Pi Fleet Emulator Spawner" "$SPAWNER_SHORT"
fi

echo "==> Docker Hub descriptions"
TOKEN="$(hub_token || true)"
if [ -z "$TOKEN" ]; then
  echo "    skipped (set DOCKERHUB_TOKEN) - paste docker/DOCKERHUB-*.md into each Overview by hand"
else
  describe pi-fleet-spawner "$SPAWNER_SHORT" "$ROOT/docker/DOCKERHUB-spawner.md"
  describe pi-fleet-node    "$NODE_SHORT"    "$ROOT/docker/DOCKERHUB-node.md"
fi

echo
echo "Done: $NAMESPACE/pi-fleet-spawner and $NAMESPACE/pi-fleet-node"
echo "      tags $VERSION, $MAJOR.$MINOR, $MAJOR, latest"
echo "Check: docker buildx imagetools inspect $NAMESPACE/pi-fleet-spawner:$VERSION"
