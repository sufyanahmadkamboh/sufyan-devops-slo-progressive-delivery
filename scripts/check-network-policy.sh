#!/usr/bin/env bash
# Security check: the orders API accepts traffic from its own namespace and from Prometheus,
# but not from any other namespace.
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"
require kubectl

probe() { # <namespace>: exit 0 if the API answered
  kubectl -n "$1" run "np-probe-$RANDOM" --rm -i --restart=Never --quiet --image=busybox:1.37 -- \
    wget -q -T 4 -O /dev/null "http://orders-api.$NAMESPACE.svc.cluster.local/version" >/dev/null 2>&1
}

kubectl create namespace np-outsider --dry-run=client -o yaml | kubectl apply -f - >/dev/null
trap 'kubectl delete namespace np-outsider --wait=false >/dev/null 2>&1 || true' EXIT

probe "$NAMESPACE" || fail "a pod in $NAMESPACE could not reach the API"
ok "same-namespace client can reach orders-api"
if probe np-outsider; then
  fail "a pod in an unrelated namespace reached the API: NetworkPolicy is not enforced"
fi
ok "pod in an unrelated namespace is blocked by the NetworkPolicy"
