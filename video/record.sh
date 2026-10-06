#!/usr/bin/env bash
# Runs the whole lab once and records it for the video: every command with its real output, exit code and
# duration (video/recordings/NN-name.txt), rollout snapshots every few seconds while releases run
# (video/recordings/watch/<scenario>/<unix time>.txt) and screenshots of the Grafana and Argo Rollouts
# dashboards (video/out/shots/). Ends by deleting the cluster.
#
#   bash video/record.sh
#
# Needs the lab's tools (docker, kind, kubectl, helm) plus the kubectl-argo-rollouts plugin, Node.js and Edge.
set -uo pipefail
cd "$(dirname "$0")/.."
REPO="$PWD"
REC="$REPO/video/recordings"
OUT="$REPO/video/out"
export KUBECONFIG="$OUT/kubeconfig"          # an isolated kubeconfig: other clusters stay untouched
rm -rf "$REC" "$OUT/shots" "$OUT/capture-profile"
mkdir -p "$REC/watch" "$OUT/shots"
n=0

rec() { # rec <name> <command>: run the command, save "$ command", its output and "# exit=… seconds=…"
  local name=$1 cmd=$2 f start code
  n=$((n + 1))
  f="$REC/$(printf %02d "$n")-$name.txt"
  start=$(date +%s)
  printf '$ %s\n' "$cmd" > "$f"
  bash -c "$cmd" 2>&1 | sed -u 's/\x1b\[[0-9;]*m//g' >> "$f"
  code=${PIPESTATUS[0]}
  printf '# exit=%s seconds=%s at=%s\n' "$code" "$(($(date +%s) - start))" "$(date +%H:%M:%S)" >> "$f"
  echo "[$(date +%H:%M:%S)] $name exit=$code"
}

watch_start() { # rollout snapshots every 4 s into watch/<name>/ until watch_stop
  mkdir -p "$REC/watch/$1"
  rm -f "$OUT/watch.stop"
  ( while [[ ! -f "$OUT/watch.stop" ]]; do
      kubectl argo rollouts get rollout orders-api -n delivery --no-color > "$REC/watch/$1/$(date +%s).txt" 2>&1
      sleep 4
    done ) &
  WATCH_PID=$!
}
watch_stop() { touch "$OUT/watch.stop"; wait "$WATCH_PID" 2>/dev/null; }

# ---------------------------------------------------------------- 1. the checks that need no cluster
python -m venv "$OUT/venv" >/dev/null && "$OUT/venv/Scripts/python" -m pip -q install -r app/requirements-dev.txt
helm template orders-api charts/orders-api -n delivery --show-only templates/analysistemplate.yaml \
  > "$REC/rendered-analysistemplate.yaml"
rec tools 'kind version; kubectl version --client | head -1; helm version --short; kubectl argo rollouts version --short'
rec unit-tests "cd app && ../video/out/venv/Scripts/python -m pytest -q"
rec promtool-check 'MSYS_NO_PATHCONV=1 docker run --rm -v "$(cygpath -m "$PWD/slo"):/slo" --entrypoint promtool prom/prometheus:v3.15.0 check rules /slo/rules/orders-api-slo.rules.yaml'
rec promtool-test 'MSYS_NO_PATHCONV=1 docker run --rm -v "$(cygpath -m "$PWD/slo"):/slo" -w /slo/tests --entrypoint promtool prom/prometheus:v3.15.0 test rules orders-api-slo.test.yaml'

# ---------------------------------------------------------------- 2. the lab
rec up 'scripts/up.sh'
rec nodes 'kubectl get nodes'
rec platform-pods 'kubectl get pods -n argo-rollouts; kubectl get pods -n monitoring'
rec app-pods 'kubectl get pods -n delivery -o wide'
rec rollout-v1 'kubectl argo rollouts get rollout orders-api -n delivery'

# kubectl port-forward exits on the first broken connection: keep restarting it until the end of the session
rm -f "$OUT/capture.stop"
( while [[ ! -f "$OUT/capture.stop" ]]; do
    kubectl -n monitoring port-forward svc/grafana 3000:3000 >/dev/null 2>&1
    sleep 1
  done ) &
PF_PID=$!
kubectl argo rollouts dashboard -p 3100 >/dev/null 2>&1 &
DASH_PID=$!
sleep 5
node video/capture.mjs "$OUT/shots" "$(cygpath -w "$OUT/capture-profile")" "$(cygpath -w "$OUT/capture.stop")" &
CAP_PID=$!
echo "[$(date +%H:%M:%S)] baseline traffic for 3 minutes"
sleep 180

# ---------------------------------------------------------------- 3. the proof: one good and two bad releases
watch_start e2e
rec e2e 'scripts/e2e.sh'
watch_stop
rec analysisruns 'kubectl get analysisrun -n delivery'
for run in $(kubectl get analysisrun -n delivery --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[*].metadata.name}'); do
  rec "measurements-$run" "kubectl get analysisrun $run -n delivery -o jsonpath='{.status.phase}{\"\\n\"}{range .status.metricResults[*]}{.name}: {.phase} {range .measurements[*]}{.value} {end}{\"\\n\"}{end}'"
done
rec rollout-after-e2e 'kubectl argo rollouts get rollout orders-api -n delivery'

# ---------------------------------------------------------------- 4. failure test and security test
watch_start chaos
rec chaos 'scripts/chaos-prometheus-outage.sh'
watch_stop
rec netpol 'scripts/check-network-policy.sh'
sleep 30

touch "$OUT/capture.stop"
wait "$CAP_PID"
kill "$PF_PID" "$DASH_PID" 2>/dev/null
taskkill //F //IM kubectl-argo-rollouts.exe >/dev/null 2>&1   # the dashboard and port-forward
taskkill //F //IM kubectl.exe >/dev/null 2>&1                 # processes outlive their bash parents
rec down 'scripts/down.sh'
echo "[$(date +%H:%M:%S)] done: $(ls "$REC" | wc -l) recordings, $(ls "$OUT/shots" | wc -l) screenshots"
