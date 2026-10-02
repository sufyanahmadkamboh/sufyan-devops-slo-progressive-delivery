# 8. Grafana

## What is it?

**Grafana** turns numbers into dashboards: charts, single-value "stat" panels, tables. It doesn't store data itself. It asks a **data source** (here Prometheus) using queries and draws the answers.

## Why this project uses it

Prometheus can answer any question, but humans need to *see* a release happening.

**The dashboard "orders-api: SLOs & progressive delivery" shows at a glance:**
- **SLO state:** availability, error budget remaining, burn rate, latency, firing alerts.
- **Canary vs stable:** error ratio and p95 **per version**.
- **Traffic split:** the share of traffic per version, moving step by step during a rollout or dropping to 0 on abort.

**Alternatives:** the Prometheus UI (basic graphs), Kibana (logs-first), Datadog dashboards (hosted, paid).

## Dashboards as code

**Nothing is clicked together by hand.** Grafana is **provisioned from files**, so the dashboard is version-controlled and rebuilt identically every time:

| File | What it provides |
|---|---|
| [`platform/monitoring/grafana.yaml`](../platform/monitoring/grafana.yaml) → `datasources.yaml` | The Prometheus data source (uid `prometheus`) |
| same file → `dashboards.yaml` | Tells Grafana to load every JSON dashboard from a folder |
| [`grafana/dashboards/orders-api-slo.json`](../grafana/dashboards/orders-api-slo.json) | The dashboard: 9 panels, each with its PromQL query |

`scripts/up.sh` turns the JSON into a ConfigMap and mounts it into the Grafana Pod.

## The panels and what to look for

| Panel | Query idea | What it tells you |
|---|---|---|
| Availability SLI (5m) | `1 - slo:sli_error:ratio_rate5m` | Green ≥ 99.5% |
| Error budget remaining | `slo:error_budget_remaining:ratio` | Below 0 means the budget is overspent |
| Burn rate (1h) | `slo:sli_error:ratio_rate1h / 0.005` | Red at ≥ 14.4x (the fast-burn page) |
| Burn rate by window | 5m, 1h and 6h lines, threshold lines at 6x and 14.4x | The multi-window picture |
| Error ratio by revision | error ratio grouped by `version` | Canary vs stable side by side |
| p95 latency by revision | `histogram_quantile` grouped by `version` | Latency regressions per version |
| Traffic split by version | requests/s grouped by `version` | Watch the canary share grow, or vanish on abort |

**A lesson from this project:** a version with **zero** errors had no 5xx series, so it vanished from the error-ratio panel, which is exactly the version you want to see at 0%. The fix adds `or <total traffic> * 0` so every version always appears.

![Dashboard during an aborted release](../docs/images/grafana-rollback.png)

## Security note

- **Viewing:** the lab enables **read-only anonymous** access, so you can view the dashboard without logging in.
- **Admin password:** random, created at deploy time, stored only as a Kubernetes Secret.
- **To read the password:**
  ```bash
  kubectl -n monitoring get secret grafana-admin -o jsonpath='{.data.password}' | base64 -d
  ```

## Try it

```bash
kubectl -n monitoring port-forward svc/grafana 3000:3000     # http://localhost:3000
scripts/release.sh 3.0.0 --inject-errors                      # watch the canary spike and disappear
```
In Grafana:
- open any panel → **Edit** to see its PromQL
- change the time range to "Last 15 minutes"
- hover the charts to compare the canary and stable lines

## Check yourself

1. Where does Grafana get its data?
2. Why is the dashboard stored as JSON in Git instead of built in the UI?

<details><summary>Answers</summary>

1. **From Prometheus,** through the provisioned data source. Grafana only queries and draws.
2. **JSON in Git:** it is reproducible, reviewable and versioned. A rebuilt cluster gets the identical dashboard, and changes go through pull requests.
</details>

Next: [9. GitHub Actions](09-github-actions.md)
