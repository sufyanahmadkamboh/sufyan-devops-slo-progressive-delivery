#!/usr/bin/env bash
# End-to-end proof of the release safety net, run against the kind lab (scripts/up.sh first).
#
#   1. healthy release 1.1.0            -> canary analysis passes, promoted to 100%
#   2. release 1.2.0 with 25% errors    -> availability check fails, rollout aborted, 1.1.0 keeps serving
#   3. release 1.3.0 with +600 ms       -> latency check fails, rollout aborted, 1.1.0 keeps serving
#
# Uses ci/fast-values.yaml (shorter pauses and analysis intervals) unless HELM_VALUES_FILE is set.
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"
require kubectl helm docker kind
HELM_VALUES_FILE="${HELM_VALUES_FILE:-$ROOT_DIR/ci/fast-values.yaml}"
export HELM_VALUES_FILE
on_exit() {
  local status=$?
  if (( status != 0 )); then dump_diagnostics; fi
  exit "$status"
}
trap on_exit EXIT

restore_stable() {
  # Returning the spec to the stable version clears an aborted rollout without a new canary.
  log "restoring desired state to the stable version $1"
  helm upgrade "$RELEASE" "$ROOT_DIR/charts/orders-api" -n "$NAMESPACE" --reuse-values -f "$HELM_VALUES_FILE" \
    --set "image.tag=$1" --set-string fault.errorRate=0 --set-string fault.latencyMs=0 >/dev/null
  wait_until 180 "rollout healthy on $1 again" rollout_healthy_on "$1"
}

expect_abort() {
  local version=$1 flag=$2 metric=$3 stable=$4
  "$ROOT_DIR/scripts/release.sh" "$version" "$flag"
  wait_until 420 "rollout of $version aborted by the SLO analysis" rollout_aborted
  local run; run="$(latest_analysis_run)"
  [[ "$(analysis_phase "$run")" == "Failed" ]] || fail "analysis run $run is not Failed"
  [[ " $(failed_metrics "$run") " == *" $metric "* ]] || fail "expected failed metric $metric, got: $(failed_metrics "$run")"
  ok "$version aborted automatically; failed SLO check: $metric (analysis run $run)"
  wait_until 180 "canary pods of $version removed" bash -c \
    "[[ \$(kubectl -n $NAMESPACE get pods -l app=orders-api -o jsonpath='{.items[*].spec.containers[0].image}' | tr ' ' '\n' | sort -u) == '$IMAGE_REPO:$stable' ]]"
  [[ "$(served_versions)" == "$stable" ]] || fail "clients are not served exclusively by $stable"
  ok "all traffic is back on $stable"
  restore_stable "$stable"
}

log "scenario 1: healthy release is promoted"
"$ROOT_DIR/scripts/release.sh" 1.1.0
wait_until 600 "1.1.0 fully promoted" rollout_healthy_on 1.1.0
run="$(latest_analysis_run)"
[[ "$(analysis_phase "$run")" == "Successful" ]] || fail "analysis run $run is $(analysis_phase "$run"), expected Successful"
[[ "$(served_versions)" == "1.1.0" ]] || fail "clients are not served by 1.1.0"
ok "1.1.0 promoted to 100% after passing every SLO check (analysis run $run)"

log "scenario 2: release with an error regression is rolled back"
expect_abort 1.2.0 --inject-errors canary-error-ratio 1.1.0

log "scenario 3: release with a latency regression is rolled back"
expect_abort 1.3.0 --inject-latency canary-p95-latency 1.1.0

ok "all end-to-end scenarios passed"
