#!/usr/bin/env bash
# Failure test: the metrics backend disappears in the middle of a canary.
#
# Expected: the analysis cannot measure the canary, so after consecutiveErrorLimit errors the
# AnalysisRun ends in "Error" and the rollout is aborted. An unverifiable release is never promoted.
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"
require kubectl helm docker kind
HELM_VALUES_FILE="${HELM_VALUES_FILE:-$ROOT_DIR/ci/fast-values.yaml}"
export HELM_VALUES_FILE
stable="$(rollout_field '.spec.template.spec.containers[0].image')"; stable="${stable#*:}"
trap 'kubectl -n monitoring scale deploy/prometheus --replicas=1 >/dev/null 2>&1 || true' EXIT

log "stable version is $stable; releasing healthy candidate 1.4.0"
"$ROOT_DIR/scripts/release.sh" 1.4.0
wait_until 120 "canary analysis running" bash -c \
  "[[ \$(kubectl -n $NAMESPACE get analysisrun --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1:].status.phase}') == Running ]]"

log "taking Prometheus down while the canary is at $(rollout_field .status.currentStepIndex) of the steps"
kubectl -n monitoring scale deploy/prometheus --replicas=0 >/dev/null

wait_until 300 "rollout aborted because the canary could not be verified" rollout_aborted
run="$(latest_analysis_run)"
phase="$(analysis_phase "$run")"
[[ "$phase" == "Error" || "$phase" == "Failed" ]] || fail "analysis run $run ended as $phase"
ok "rollout aborted while metrics were unavailable (analysis run $run phase: $phase)"
kubectl -n "$NAMESPACE" get analysisrun "$run" \
  -o jsonpath='{range .status.metricResults[*]}{.name}: phase={.phase} consecutiveError={.consecutiveError}{"\n"}{end}'

log "restoring Prometheus and the stable version $stable"
kubectl -n monitoring scale deploy/prometheus --replicas=1 >/dev/null
kubectl -n monitoring rollout status deploy/prometheus --timeout=180s >/dev/null
helm upgrade "$RELEASE" "$ROOT_DIR/charts/orders-api" -n "$NAMESPACE" --reuse-values -f "$HELM_VALUES_FILE" \
  --set "image.tag=$stable" --set-string fault.errorRate=0 --set-string fault.latencyMs=0 >/dev/null
wait_until 180 "rollout healthy on $stable" rollout_healthy_on "$stable"
ok "recovered: $stable healthy, Prometheus back"
