#!/usr/bin/env bash
# Shared settings and helpers for the lab scripts.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export ROOT_DIR
CLUSTER_NAME="${CLUSTER_NAME:-slo-delivery}"
NAMESPACE="${NAMESPACE:-delivery}"
RELEASE="${RELEASE:-orders-api}"
IMAGE_REPO="${IMAGE_REPO:-orders-api}"
ROLLOUTS_VERSION="${ROLLOUTS_VERSION:-v1.10.0}"
# Extra Helm values (for example ci/fast-values.yaml in the end-to-end test).
HELM_VALUES_FILE="${HELM_VALUES_FILE:-}"

log()  { printf '\033[1;34m[%s]\033[0m %s\n' "$(date +%H:%M:%S)" "$*"; }
ok()   { printf '\033[1;32m[%s] PASS\033[0m %s\n' "$(date +%H:%M:%S)" "$*"; }
fail() { printf '\033[1;31m[%s] FAIL\033[0m %s\n' "$(date +%H:%M:%S)" "$*" >&2; exit 1; }

require() {
  local tool
  for tool in "$@"; do
    command -v "$tool" >/dev/null 2>&1 || fail "required tool not found on PATH: $tool"
  done
}

# wait_until <timeout-seconds> <description> <command...>: retry a command until it succeeds.
wait_until() {
  local timeout=$1 what=$2; shift 2
  local deadline=$((SECONDS + timeout))
  until "$@" >/dev/null 2>&1; do
    if (( SECONDS >= deadline )); then
      fail "timed out after ${timeout}s waiting for: $what"
    fi
    sleep 5
  done
}

rollout_field() {
  kubectl -n "$NAMESPACE" get rollout "$RELEASE" -o "jsonpath={$1}" 2>/dev/null
}

rollout_phase()   { rollout_field .status.phase; }
rollout_aborted() { [[ "$(rollout_field .status.abort)" == "true" ]]; }
rollout_healthy_on() {
  # Healthy, fully promoted, and the stable revision runs the expected image tag.
  [[ "$(rollout_phase)" == "Healthy" ]] || return 1
  [[ "$(rollout_field .status.stableRS)" == "$(rollout_field .status.currentPodHash)" ]] || return 1
  [[ "$(rollout_field .spec.template.spec.containers[0].image)" == "$IMAGE_REPO:$1" ]]
}

latest_analysis_run() {
  kubectl -n "$NAMESPACE" get analysisrun --sort-by=.metadata.creationTimestamp \
    -o jsonpath='{.items[-1:].metadata.name}' 2>/dev/null
}

analysis_phase() {
  kubectl -n "$NAMESPACE" get analysisrun "$1" -o jsonpath='{.status.phase}' 2>/dev/null
}

failed_metrics() {
  kubectl -n "$NAMESPACE" get analysisrun "$1" \
    -o jsonpath='{range .status.metricResults[?(@.phase=="Failed")]}{.name}{" "}{end}' 2>/dev/null
}

# Versions actually served to clients, asked from inside the cluster through the orders-api Service.
served_versions() {
  kubectl -n "$NAMESPACE" exec deploy/orders-loadgen -- python -c '
import json, urllib.request
seen = set()
for _ in range(40):
    with urllib.request.urlopen("http://orders-api/version", timeout=5) as r:
        seen.add(json.load(r)["version"])
print(" ".join(sorted(seen)))
'
}

dump_diagnostics() {
  log "diagnostics"
  kubectl -n "$NAMESPACE" get rollout,rs,pods,analysisrun -o wide || true
  local run; run="$(latest_analysis_run || true)"
  if [[ -n "$run" ]]; then
    kubectl -n "$NAMESPACE" get analysisrun "$run" -o yaml | sed -n '/^status:/,$p' || true
  fi
  kubectl -n argo-rollouts logs deploy/argo-rollouts --tail=50 || true
}
