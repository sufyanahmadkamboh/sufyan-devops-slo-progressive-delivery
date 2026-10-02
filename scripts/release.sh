#!/usr/bin/env bash
# Release a version of orders-api through the SLO-gated canary.
#
# Usage: scripts/release.sh <version> [--inject-errors | --inject-latency]
#   --inject-errors   the new version fails 25% of requests (reproduces a bad release)
#   --inject-latency  the new version adds 600 ms to every request (reproduces a performance regression)
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"
require kubectl helm

version="${1:?usage: release.sh <version> [--inject-errors|--inject-latency]}"
error_rate=0
latency_ms=0
case "${2:-}" in
  "") ;;
  --inject-errors)  error_rate=0.25 ;;
  --inject-latency) latency_ms=600 ;;
  *) fail "unknown option: $2" ;;
esac

"$ROOT_DIR/scripts/build-image.sh" "$version"

log "releasing $version (fault.errorRate=$error_rate fault.latencyMs=$latency_ms)"
helm_args=(upgrade "$RELEASE" "$ROOT_DIR/charts/orders-api" -n "$NAMESPACE" --reuse-values
  --set "image.tag=$version" --set-string "fault.errorRate=$error_rate" --set-string "fault.latencyMs=$latency_ms")
[[ -n "$HELM_VALUES_FILE" ]] && helm_args+=(-f "$HELM_VALUES_FILE")
helm "${helm_args[@]}" >/dev/null
log "canary started. Watch it with: kubectl -n $NAMESPACE get rollout $RELEASE -w"
