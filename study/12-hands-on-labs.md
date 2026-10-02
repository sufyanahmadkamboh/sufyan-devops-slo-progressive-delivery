# 12. Hands-on labs

Do these in order with the lab running (`make up`). Each lab says what to do, what you should see, and what you learned. Open three terminals:
```bash
# terminal 1: watch the rollout
kubectl -n delivery get rollout orders-api -w
# terminal 2: Grafana (http://localhost:3000)
kubectl -n monitoring port-forward svc/grafana 3000:3000
# terminal 3: your commands
```

## Lab 1: Explore the running system (15 min)

1. `kubectl get pods -A`: find the Pods for the app, the load generator, Prometheus, Grafana and Argo Rollouts.
2. `kubectl -n delivery get pods --show-labels`: find the `rollouts-pod-template-hash` label.
3. `kubectl -n delivery logs deploy/orders-loadgen`: see the responses by status code.
4. In Grafana, find the current availability and the traffic per version.

✅ **You learned:** how the pieces are laid out across namespaces, and how labels identify a version.

## Lab 2: Release a healthy version (10 min)

```bash
scripts/release.sh 1.6.0
```
Watch terminal 1: the phase goes `Progressing` → `Paused` (at each step) → `Healthy`.
```bash
kubectl -n delivery get rs                         # during the canary: two ReplicaSets (old and new)
kubectl -n delivery get analysisrun                # Running, then Successful
```
In Grafana, *Traffic split by version* shows 1.6.0 growing from 20% to 100%.

✅ **You learned:** a canary moves step by step while measurements keep passing.

## Lab 3: Release a broken version (10 min)

```bash
scripts/release.sh 1.7.0 --inject-errors
```

**Expect:**
- within about a minute, terminal 1 shows the rollout aborted
- the canary Pod disappears

```bash
run=$(kubectl -n delivery get analysisrun --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1:].metadata.name}')
kubectl -n delivery get analysisrun "$run" -o jsonpath='{range .status.metricResults[*]}{.name}: {.phase} {.measurements[*].value}{"\n"}{end}'
kubectl -n delivery get rollout orders-api -o jsonpath='{.status.message}{"\n"}'
```

**To clear the abort,** point the release back at the stable version:
```bash
helm upgrade orders-api charts/orders-api -n delivery --reuse-values --set image.tag=1.6.0 \
  --set-string fault.errorRate=0 --set-string fault.latencyMs=0
```

✅ **You learned:** a measured SLO breach stops a release automatically, and users keep the stable version.

## Lab 4: Latency regression (10 min)

```bash
scripts/release.sh 1.8.0 --inject-latency
```

**Expect:** this time `canary-p95-latency` fails and `canary-error-ratio` passes.

**Question:** why does the p95 read 0.975 s instead of 0.62 s? (Hint: chapter 6, histogram buckets.)

✅ **You learned:** each SLI catches a different kind of regression.

## Lab 5: Break the monitoring (15 min)

```bash
scripts/chaos-prometheus-outage.sh
```
Read the output. The AnalysisRun phase is `Error` (not `Failed`), with `consecutiveError=5`.

✅ **You learned:** fail-safe design. Not being able to measure is treated as "not safe to promote".

## Lab 6: Prove the network isolation (5 min)

```bash
scripts/check-network-policy.sh
```
Then try it by hand from another namespace; it should time out:
```bash
kubectl create ns test-outside
kubectl -n test-outside run probe --rm -it --image=busybox:1.37 --restart=Never -- \
  wget -T 4 -qO- http://orders-api.delivery.svc.cluster.local/version
kubectl delete ns test-outside
```
✅ **You learned:** NetworkPolicy is a firewall between Pods, and it really is enforced.

## Lab 7: Change the SLO and see the gate move (15 min)

1. In `charts/orders-api/values.yaml`, set `slo.availabilityTarget: 0.999`.
2. `helm template orders-api charts/orders-api | grep successCondition`. The limit is now `0.0144`.
3. Release with a **smaller** fault:
   ```bash
   helm upgrade orders-api charts/orders-api -n delivery --reuse-values -f charts/orders-api/values.yaml \
     --set image.tag=1.9.0 --set-string fault.errorRate=0.03
   ```
   (Build the image first: `scripts/build-image.sh 1.9.0`.)
4. **Expect an abort.** With the old 99.5% SLO, 3% errors would have passed (limit 7.2%). Revert the file afterwards.

✅ **You learned:** the business target (the SLO) directly controls release safety, and Helm computes the technical limit from it.

## Lab 8: Test the alerts (15 min)

```bash
make slo-test
```
Open `slo/tests/orders-api-slo.test.yaml` and change the healthy test from 0.1% errors to 5% errors (`values: '0+95x150'` and `'0+5x150'`). Run it again: it **fails**, because now alerts *do* fire. Read the failure message, then revert.

✅ **You learned:** alert logic can be unit-tested like code.

## Stretch goals

- **Change the steps:** set `canary.weights: [10, 30, 50, 100]` with `replicas: 10` and observe the finer steps.
- **Add a metric:** add a third analysis metric (for example "the canary must receive at least 1 req/s") to `analysistemplate.yaml`.
- **Fill the alerts panel:** add Alertmanager and route the `page` alerts to a webhook.

When you are done: `make down`.
