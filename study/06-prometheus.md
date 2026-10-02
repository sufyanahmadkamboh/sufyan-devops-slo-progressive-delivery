# 6. Prometheus and PromQL

## What is it?

**Prometheus** is a monitoring system that **collects numbers over time** (time series) and lets you **query** them. Every few seconds it visits each application's `/metrics` page (called **scraping**) and stores what it reads.

```
orders-api pod  ──  GET /metrics every 5 s  ──►  Prometheus  ──►  stores, queries, alerts
http_requests_total{route="/api/orders",code="200"} 1234
http_requests_total{route="/api/orders",code="500"} 7
```

## Why this project uses it

**Prometheus is the single source of truth for the SLIs.** It does four jobs here:
1. **Collects** request counts and latencies from every Pod, labelled with the Pod's **version**.
2. **Records** the SLIs over several windows (recording rules).
3. **Alerts** on error-budget burn rate (alerting rules).
4. **Answers the canary analysis.** Argo Rollouts sends it a query every 30 s.

**Alternatives:** Datadog, New Relic (hosted, paid), OpenTelemetry + a backend. Prometheus is the open-source standard for Kubernetes and the native data source for Argo Rollouts' analysis.

## Metric types used by the app

From [`app/orders_api/server.py`](../app/orders_api/server.py):

| Metric | Type | Meaning |
|---|---|---|
| `http_requests_total{route,method,code}` | **Counter**: only goes up | Total requests, split by route and status code |
| `http_request_duration_seconds{route}` | **Histogram**: counts per time "bucket" | How many requests took ≤ 25 ms, ≤ 50 ms, … ≤ 300 ms, … ≤ 2.5 s |
| `app_info{version}` | **Gauge**: can go up and down | Constant 1, with the version as a label |

**Labels** (the `{…}` part) let you filter and group. Each unique combination of labels is one **time series**.

## Service discovery and relabelling: the clever part

**Prometheus has to find the Pods on its own**, because they come and go during every release. [`platform/monitoring/prometheus.yaml`](../platform/monitoring/prometheus.yaml) uses `kubernetes_sd_configs` (role: pod) and then **relabelling** rules:

```yaml
- source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
  action: keep
  regex: "true"                      # only Pods annotated prometheus.io/scrape: "true"
- source_labels: [__meta_kubernetes_pod_label_rollouts_pod_template_hash]
  target_label: rollouts_pod_template_hash   # ← THE key line
```

**Argo Rollouts** gives every version's Pods a label `rollouts-pod-template-hash` (for example `7f6866c7fc`). By copying it onto every sample, Prometheus can answer "error ratio of the **new** version only". Without this line, canary analysis would be impossible.

**RBAC:** Prometheus' ClusterRole allows only `get/list/watch` on Pods. That's the least privilege needed for discovery.

## PromQL: the query language, step by step

```promql
http_requests_total                                    # every series of this counter
http_requests_total{route="/api/orders",code=~"5.."}   # filter: =~ is a regex match, so any 5xx
rate(http_requests_total[1m])                          # per-second increase over the last minute
sum(rate(http_requests_total[1m]))                     # add all series: total requests/s
sum by (version) (rate(http_requests_total[1m]))       # requests/s per version (the traffic split!)
```

**The availability SLI** (error ratio):
```promql
(sum(rate(http_requests_total{route="/api/orders",code=~"5.."}[5m])) or vector(0))
/
sum(rate(http_requests_total{route="/api/orders"}[5m]))
```
`or vector(0)` handles the case where no 5xx has *ever* happened, so the numerator series doesn't exist yet. Without it, the result would be empty instead of 0.

**The p95 latency** from the histogram:
```promql
histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[1m])))
```
**Accuracy note:** the result is interpolated inside a bucket, so its precision depends on the bucket boundaries. With +600 ms injected, the lab measured 0.975 s, because the true value sits in the 0.5–1 s bucket.

## Recording rules and alerting rules

**Recording rules** pre-compute expensive queries and give them a name. The convention is `level:metric:operation`:
```yaml
- record: slo:sli_error:ratio_rate1h
  expr: <the error-ratio query with [1h]>
```
**Alerting rules** fire when an expression is true for a duration (`for:`):
```yaml
- alert: OrdersApiErrorBudgetFastBurn
  expr: slo:sli_error:ratio_rate1h > (14.4 * 0.005) and slo:sli_error:ratio_rate5m > (14.4 * 0.005)
  for: 2m
```

**The rules file is the single source of truth.** `scripts/up.sh` turns `slo/rules/` into a ConfigMap, and the same file is unit-tested by `promtool` (chapter 10).

## Try it

```bash
kubectl -n monitoring port-forward svc/prometheus 9090:9090   # open http://localhost:9090
```

**In the Prometheus UI:**
- **Status → Targets:** every orders-api Pod, with its `rollouts_pod_template_hash`
- **Graph:** run the queries above one by one, then `slo:sli_error:ratio_rate5m`
- **Alerts:** the 4 SLO alerts and their state

Start a bad release (`scripts/release.sh 1.9.0 --inject-errors`) and query:
```promql
sum by (version) (rate(http_requests_total{code=~"5.."}[1m])) / sum by (version) (rate(http_requests_total[1m]))
```

## Check yourself

1. Why is `rate()` applied to a counter instead of using the raw value?
2. What would break if the relabel rule for `rollouts_pod_template_hash` were deleted?
3. What does `for: 2m` add to an alert?

<details><summary>Answers</summary>

1. **`rate()` on counters:** a counter only grows, and resets when a Pod restarts. `rate()` gives the per-second speed and handles resets.
2. **Without the relabel rule:** the analysis queries could no longer separate canary Pods from stable Pods. They would return no data, so every rollout would fail safe.
3. **`for: 2m`:** the condition must stay true for 2 minutes before the alert fires, which filters out short spikes.
</details>

Next: [7. Progressive delivery and Argo Rollouts](07-argo-rollouts.md)
