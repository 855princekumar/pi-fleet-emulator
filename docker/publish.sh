#!/usr/bin/env bash
# Build and push both images to Docker Hub for linux/amd64 + linux/arm64.
#
#   docker login -u devprincekumar
#   ./docker/publish.sh            # pushes :1.0.0 and :latest
#   ./docker/publish.sh 1.1.0      # pushes :1.1.0 and :latest
set -euo pipefail

VERSION="${1:-1.0.0}"
NAMESPACE="${PFE_NAMESPACE:-devprincekumar}"
PLATFORMS="${PFE_PLATFORMS:-linux/amd64,linux/arm64}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Multi-platform pushes need a docker-container builder
if ! docker buildx inspect pfe-builder >/dev/null 2>&1; then
  docker buildx create --name pfe-builder --driver docker-container >/dev/null
fi

build() {  # image-name  context
  echo "==> $NAMESPACE/$1:$VERSION  ($PLATFORMS)"
  docker buildx build --builder pfe-builder --platform "$PLATFORMS" \
    -t "$NAMESPACE/$1:$VERSION" -t "$NAMESPACE/$1:latest" \
    --push "$2"
}

build pi-fleet-node    "$ROOT/node-base"
build pi-fleet-spawner "$ROOT"

echo
echo "Pushed:"
echo "  $NAMESPACE/pi-fleet-node:$VERSION    (+ latest)"
echo "  $NAMESPACE/pi-fleet-spawner:$VERSION (+ latest)"
echo "Check: docker buildx imagetools inspect $NAMESPACE/pi-fleet-spawner:$VERSION"
