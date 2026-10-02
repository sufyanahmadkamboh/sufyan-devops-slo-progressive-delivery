# Troubleshooting

## `helm upgrade` fails: "conflict with rollouts-controller using v1: .spec.selector"

**Symptom:**
```
Error: UPGRADE FAILED: conflict occurred while applying object delivery/orders-api-stable /v1, Kind=Service:
Apply failed with 1 conflict: conflict with "rollouts-controller" using v1: .spec.selector
```

**Cause:**
- Helm 4 applies manifests with server-side apply by default, so Helm owns every field it renders.
- When a Rollout defines `stableService`/`canaryService`, the Argo Rollouts controller rewrites those Services' `spec.selector` (it adds the pod-template hash).
- On the next release, two field managers claim the same field and the API server rejects the apply.

I hit this during the first end-to-end run of this project.

**Fix used in this repository:**
- The chart has a single client-facing Service and no stable/canary Services.
- Canary traffic share comes from the replica ratio.
- The analysis selects canary pods by their `rollouts_pod_template_hash` label, so no field has two owners.

**Other options when separate Services are required** (for example with a traffic router):
- Don't render the selector of controller-managed Services from Helm.
- Or run `helm upgrade --server-side=false`.
- Avoid `--force-conflicts`: it takes the selector back from the controller in the middle of a rollout.

## Rollout stays `Paused`/`Progressing` and the analysis keeps failing with "no data"

`len(result) > 0` fails when Prometheus returns an empty vector for the canary hash.

1. Is traffic flowing? Check `kubectl -n delivery logs deploy/orders-loadgen`, which logs status-code counts every 30 s.
2. Are the canary pods scraped with their hash? Port-forward Prometheus and run `count by (rollouts_pod_template_hash) (up{job="kubernetes-pods"})`. There should be a series per revision.
3. Was a pod label renamed? The scrape config copies `rollouts-pod-template-hash` and `app`. If a pod template lost `app: orders-api`, its samples won't match the analysis selector.

## AnalysisRun phase `Error` (not `Failed`)

**`Error`** means the measurement itself failed, for example because Prometheus was unreachable or the query was invalid. **`Failed`** means the canary breached an SLO.
- **To see the message:** `kubectl -n delivery get analysisrun <name> -o yaml` (`status.metricResults[*].message`).
- **Prometheus unavailable:** this is the designed fail-safe. The rollout aborts after `consecutiveErrorLimit + 1` errors.

## NetworkPolicy check fails ("a pod in an unrelated namespace reached the API")

The cluster's CNI doesn't enforce NetworkPolicy.
- **kind:** its default CNI (kindnet) enforces NetworkPolicy in recent kind versions; this project is tested with kind v0.33.
- **Other clusters:** use a CNI with policy support, such as Calico or Cilium.

## Grafana shows "No data" on revision panels right after `up.sh`

Rate windows need at least two scrapes in the window, and burn-rate panels over 1h/6h only fill as history builds up. Give it about 2 minutes after the first traffic.

## Error budget jumps to 100% or far below 0% after a Prometheus restart

**Cause:** the lab stores Prometheus data in an `emptyDir`, so a restart (for example during the chaos test) deletes all history. The "1-day" windows are then computed over only the few minutes that exist:
- a clean restart shows **100% budget remaining**
- a few minutes containing a bad canary can show the budget as **overspent** (for example −175%)

The numbers are mathematically right for the data that exists, but they don't represent a full day.

**In production:** use persistent volumes plus long-term storage (Thanos or Mimir), so SLO windows survive restarts.

## Windows (Git Bash) notes

- Scripts need LF line endings. The `.gitattributes` enforces this; if a script fails with `$'\r': command not found`, re-checkout or run `sed -i 's/\r$//' scripts/*.sh`.
- Run the Makefile targets from Git Bash or WSL. On Git Bash, `export MSYS_NO_PATHCONV=1` before the promtool `docker run` commands, so the `/slo` volume path isn't rewritten.
