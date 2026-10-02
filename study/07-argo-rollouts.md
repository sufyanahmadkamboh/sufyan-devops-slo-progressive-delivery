# 7. Progressive delivery and Argo Rollouts

## What is progressive delivery?

**Progressive delivery** releases a new version to a **small share of users first**, measures it, and only continues if it is healthy.

| Strategy | How it works | Risk |
|---|---|---|
| **Recreate** | Stop the old version, start the new | Downtime; everybody is hit by bugs |
| **Rolling update** (Kubernetes default) | Replace Pods a few at a time | No downtime, but it doesn't *check health*, so a bad version still reaches 100% in minutes |
| **Blue/green** | Run the full new version next to the old one, switch all traffic at once | Fast rollback, but an all-or-nothing switch and double the resources |
| **Canary** ← this project | Send a small, growing share of traffic to the new version, check metrics at each step | Bad versions reach few users, and only briefly |

The name comes from the canaries miners took into coal mines to detect gas early.

## What is Argo Rollouts?

**Argo Rollouts** is a Kubernetes **controller**: a program running in the cluster (namespace `argo-rollouts`) that adds new object types (**CRDs**, Custom Resource Definitions):

| Object | Role |
|---|---|
| **Rollout** | Replaces a Deployment. Same Pod template, plus a `strategy.canary` section describing the steps |
| **AnalysisTemplate** | A reusable definition of *what to measure* and *what counts as success* |
| **AnalysisRun** | One execution of a template during a specific release, with every measurement stored |

**Why this tool:** Kubernetes Deployments can't pause, measure, or roll back on metrics. Argo Rollouts adds exactly that, with native Prometheus support.

**Alternatives:** Flagger (similar, often with a service mesh); feature-flag platforms (release *features* rather than *deployments*); hand-written pipeline scripts (fragile).

## How it works in this project

### The steps ([`rollout.yaml`](../charts/orders-api/templates/rollout.yaml))
```yaml
strategy:
  canary:
    analysis:                          # BACKGROUND analysis: runs from step 1 until full promotion
      startingStep: 1
      templates: [{ templateName: orders-api-slo }]
      args:
        - name: canary-hash
          valueFrom: { podTemplateHashValue: Latest }   # the new version's pod hash
    steps:
      - setWeight: 20                  # 1 of 5 pods runs the new version
      - pause: { duration: 60s }
      - setWeight: 40
      - pause: { duration: 60s }
      - setWeight: 60
      - pause: { duration: 60s }
      - setWeight: 80
      - pause: { duration: 60s }       # after the last step: promoted to 100%
```

**No traffic router:**
- `setWeight: 20` with 5 replicas means **1 canary Pod**.
- The single Service spreads traffic across all Pods, so the canary gets about 20%.
- **Trade-off:** steps can only be multiples of 1/replicas. A traffic router (Gateway API, Istio, NGINX) would allow exact 1% or 5% steps.

### The checks ([`analysistemplate.yaml`](../charts/orders-api/templates/analysistemplate.yaml))
```yaml
metrics:
  - name: canary-error-ratio
    interval: 30s                 # measure every 30 s
    failureLimit: 1               # 2 failures → the analysis fails → the rollout aborts
    consecutiveErrorLimit: 4      # 5 query ERRORS in a row (Prometheus down) → abort
    successCondition: "len(result) > 0 && !isNaN(result[0]) && result[0] <= 0.0720"
    provider:
      prometheus:
        address: http://prometheus.monitoring.svc.cluster.local:9090
        query: <error ratio, filtered with rollouts_pod_template_hash="{{args.canary-hash}}">
  - name: canary-p95-latency       # same idea, success if p95 ≤ 0.3 s
```

**Reading `successCondition`:**
- `len(result) > 0`: Prometheus returned data. **No data means fail**, because a canary nobody used is not verified.
- `!isNaN(result[0])`: the value is a real number (dividing by zero traffic gives NaN).
- `result[0] <= 0.0720`: within the SLO-based limit.

### The three outcomes

| Analysis result | What Argo Rollouts does |
|---|---|
| **Successful** at every check | Continues through all steps, then promotes: the new version becomes **stable** |
| **Failed** (SLO breached twice) | **Aborts**: the canary scales to 0, stable returns to 5 Pods, users get the old version |
| **Error** (cannot measure 5 times in a row) | **Aborts** too: never promote what you can't verify (fail safe) |

**After an abort:**
- the Rollout shows `abort: true` and phase `Degraded`
- you fix the code and release a new version, or point the spec back to the stable version

## Measured in this project (kind lab)

| Release | Decision |
|---|---|
| Healthy 1.1.0 | 9 of 9 checks passed, promoted after 2 min 46 s |
| 25% errors | Aborted after **47 s** (measured 21.7% and 19.8% against the 7.2% limit) |
| +600 ms | Aborted after 46 s (p95 0.975 s against the 0.3 s limit) |
| Prometheus outage | Analysis `Error`, aborted after 60 s |

## Try it

```bash
kubectl -n delivery get rollout orders-api -w            # watch phase and step change
scripts/release.sh 2.0.0                                 # healthy release
kubectl -n delivery get rs                               # two ReplicaSets during the canary: old and new
kubectl -n delivery get analysisrun                      # one run per release
kubectl -n delivery get analysisrun <name> -o yaml | sed -n '/^status:/,$p'   # every measurement
scripts/release.sh 2.1.0 --inject-errors                 # watch the abort happen
```

**Optional kubectl plugin** for a nice tree view: install `kubectl-argo-rollouts`, then `kubectl argo rollouts get rollout orders-api -n delivery --watch`.

## Check yourself

1. Why does the analysis query filter by `rollouts_pod_template_hash`?
2. What happens if no traffic reaches the canary?
3. Why is a Prometheus outage treated as "abort", not "continue"?

<details><summary>Answers</summary>

1. **The hash filter:** to judge only the new version's Pods. A service-wide average at 20% canary weight would dilute a broken canary with healthy stable traffic.
2. **No traffic:** the query returns no data, `len(result) > 0` fails, and the release is not promoted.
3. **Fail safe:** promoting a release without evidence that it is healthy is exactly the risk this system exists to remove.
</details>

Next: [8. Grafana](08-grafana.md)
