#!/usr/bin/env bash
# Delete the lab cluster and everything in it.
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"
require kind
log "deleting kind cluster $CLUSTER_NAME"
kind delete cluster --name "$CLUSTER_NAME"
