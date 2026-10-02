#!/usr/bin/env bash
# Build the orders-api image for a version and load it into the kind cluster.
# Usage: scripts/build-image.sh <version>
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"

version="${1:?usage: build-image.sh <version>}"
require docker kind

log "building $IMAGE_REPO:$version"
docker build --quiet --build-arg "APP_VERSION=$version" -t "$IMAGE_REPO:$version" "$ROOT_DIR/app" >/dev/null
log "loading $IMAGE_REPO:$version into kind cluster $CLUSTER_NAME"
kind load docker-image "$IMAGE_REPO:$version" --name "$CLUSTER_NAME" >/dev/null
