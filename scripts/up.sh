#!/usr/bin/env bash
# Create the complete lab: kind cluster, Argo Rollouts, Prometheus + SLO rules, Grafana + dashboard,
# and the first release (1.0.0) of the orders API with its load generator.
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"
require docker kind kubectl helm

if kind get clusters 2>/dev/null | grep -qx "$CLUSTER_NAME"; then
  log "kind cluster $CLUSTER_NAME already exists, reusing it"
else
  log "creating kind cluster $CLUSTER_NAME"
  kind create cluster --config "$ROOT_DIR/kind/cluster.yaml" --name "$CLUSTER_NAME" --wait 120s
fi
kubectl config use-context "kind-$CLUSTER_NAME" >/dev/null

log "installing Argo Rollouts $ROLLOUTS_VERSION"
kubectl create namespace argo-rollouts --dry-run=client -o yaml | kubectl apply -f - >/dev/null
kubectl apply -n argo-rollouts --server-side --force-conflicts \
  -f "https://github.com/argoproj/argo-rollouts/releases/download/${ROLLOUTS_VERSION}/install.yaml" >/dev/null
kubectl -n argo-rollouts rollout status deploy/argo-rollouts --timeout=180s

log "deploying Prometheus with the SLO rules from slo/rules/"
kubectl apply -f "$ROOT_DIR/platform/monitoring/prometheus.yaml" >/dev/null
kubectl -n monitoring create configmap prometheus-slo-rules --from-file="$ROOT_DIR/slo/rules/" \
  --dry-run=client -o yaml | kubectl apply -f - >/dev/null

log "deploying Grafana with the SLO dashboard"
if ! kubectl -n monitoring get secret grafana-admin >/dev/null 2>&1; then
  kubectl -n monitoring create secret generic grafana-admin \
    --from-literal=password="$(LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 24)" >/dev/null
fi
kubectl -n monitoring create configmap grafana-dashboards --from-file="$ROOT_DIR/grafana/dashboards/" \
  --dry-run=client -o yaml | kubectl apply -f - >/dev/null
kubectl apply -f "$ROOT_DIR/platform/monitoring/grafana.yaml" >/dev/null
kubectl -n monitoring rollout status deploy/prometheus --timeout=180s
kubectl -n monitoring rollout status deploy/grafana --timeout=180s

"$ROOT_DIR/scripts/build-image.sh" 1.0.0

log "installing orders-api 1.0.0 (first revision goes straight to 100%)"
helm_args=(upgrade --install "$RELEASE" "$ROOT_DIR/charts/orders-api" -n "$NAMESPACE" --create-namespace
  --set image.tag=1.0.0)
[[ -n "$HELM_VALUES_FILE" ]] && helm_args+=(-f "$HELM_VALUES_FILE")
helm "${helm_args[@]}" >/dev/null
wait_until 300 "orders-api 1.0.0 healthy" rollout_healthy_on 1.0.0
kubectl -n "$NAMESPACE" rollout status deploy/orders-loadgen --timeout=180s

ok "lab is up. Next steps:"
cat <<EOF
  Release a new version:   scripts/release.sh 1.1.0
  Release a bad version:   scripts/release.sh 1.2.0 --inject-errors
  Watch the rollout:       kubectl -n $NAMESPACE get rollout $RELEASE -w
  Grafana:                 kubectl -n monitoring port-forward svc/grafana 3000:3000   -> http://localhost:3000
  Prometheus:              kubectl -n monitoring port-forward svc/prometheus 9090:9090 -> http://localhost:9090
EOF
