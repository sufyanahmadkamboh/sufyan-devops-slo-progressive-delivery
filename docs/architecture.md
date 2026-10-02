# Architecture

## Goal

Make "is this release healthy for users?" an automated, measured decision inside the deployment
itself, rather than a question someone answers after customers have already noticed.

## Components

| Component | Role | Why this choice |
|---|---|---|
| **orders-api** (Python) | Service under release. Exposes `http_requests_total` and `http_request_duration_seconds` | Small enough to read in minutes. Instrumented exactly like a production service. Fault injection reproduces bad releases on demand |
| **Argo Rollouts** v1.10 | Replaces the Deployment with a `Rollout` that shifts traffic in steps and runs analysis | Kubernetes-native progressive delivery controller; analysis is declarative (`AnalysisTemplate`) |
| **Prometheus** v3.15 | Scrapes every pod with its revision label, records SLIs, evaluates burn-rate alerts, answers the analysis queries | The SLO data source; recording rules keep queries cheap and consistent |
| **Grafana** v13 | SLO and error-budget dashboard, canary vs stable comparison | Provisioned as code: datasource and dashboard come from the repo |
| **Helm** | Packages the Rollout, AnalysisTemplate, Service, NetworkPolicy and load generator | One parameterised source for real and test timings (`ci/fast-values.yaml`) |
| **kind** | Local multi-node Kubernetes (1 control plane + 2 workers) | Zero-cost, reproducible, and the same setup runs in GitHub Actions |
| **GitHub Actions** | Unit tests, lint, rule tests, schema validation, image scan, full end-to-end run on kind | Every change proves the safety net still works |

## Release flow

```
helm upgrade (new image tag)
        │
        ▼
Argo Rollouts creates the canary ReplicaSet (new pod-template hash)
        │
        ├─ step 1: 20% of pods canary ──┐
        ├─ step 2: 40% ─────────────────┤   background AnalysisRun, from step 1 to full promotion:
        ├─ step 3: 60% ─────────────────┤     every 30 s, query Prometheus for the CANARY pods only
        ├─ step 4: 80% ─────────────────┤       canary-error-ratio   <= 0.0720   (0.5% budget x 14.4)
        └─ promote: 100%                │       canary-p95-latency   <= 0.300 s
                                        │
             any check fails twice ─────┴──► rollout ABORTED: canary scaled to 0,
                                             stable ReplicaSet scaled back to 100%
```

Traffic shaping is **replica-based**: the one `orders-api` Service selects both revisions, so 1 of 5
pods means about 20% of requests. That needs no service mesh or ingress controller. The trade-off is
that weights are only as fine as `1 / replicas` (see "Possible extensions").

## How the analysis sees only the canary

Prometheus' pod discovery copies the pod label `rollouts-pod-template-hash` onto every sample as
`rollouts_pod_template_hash`. The Rollout passes the canary's hash to the analysis
(`valueFrom.podTemplateHashValue: Latest`), so every query is scoped to the new revision:

```promql
(sum(rate(http_requests_total{app="orders-api",route="/api/orders",rollouts_pod_template_hash="<canary>",code=~"5.."}[1m])) or vector(0))
/
sum(rate(http_requests_total{app="orders-api",route="/api/orders",rollouts_pod_template_hash="<canary>"}[1m]))
```

The stable pods' good behaviour can't hide a broken canary, which an aggregate service-wide error
rate would do at 20% weight.

## Why the threshold is 0.072

| Term | Value |
|---|---|
| Availability SLO | 99.5% non-5xx over 30 days |
| Error budget | 0.5% of requests |
| Max canary burn rate | 14.4x, the same value as the fast-burn **page** |
| Max canary error ratio | 0.005 × 14.4 = **0.072** |

**Rule of thumb:** a canary that would trigger a page if it served all traffic must not be promoted.
Using the same number for the gate and the page keeps release safety and on-call alerting consistent.

## SLO alerting (multi-window, multi-burn-rate)

| Alert | Long window | Short window | Burn rate | Budget used | Severity |
|---|---|---|---|---|---|
| OrdersApiErrorBudgetFastBurn | 1h | 5m | 14.4x | 2% in 1 h | page |
| OrdersApiErrorBudgetSlowBurn | 6h | 30m | 6x | 5% in 6 h | page |
| OrdersApiErrorBudgetTicketBurn | 1d | 2h | 3x | 10% in 1 day | ticket |
| OrdersApiLatencyBudgetFastBurn | 1h | 5m | 14.4x of the 1% latency budget | | page |

**Why both windows:**
- The long window makes an alert significant. A one-minute blip can't page anyone.
- The short window makes it resolve quickly once the problem is fixed, instead of firing for another hour.

**Tests:** `slo/tests/orders-api-slo.test.yaml` proves these behaviours with `promtool test rules`:
- 10% errors page via fast burn.
- 4% errors page via slow burn only.
- 0.1% errors stay silent.

## Key design decisions and trade-offs

| Decision | Alternative | Why this way |
|---|---|---|
| **Background analysis** from step 1 to promotion | Analysis only at selected steps | A regression that appears at 60% traffic (load-dependent) is still caught |
| **No data = failed measurement** (`len(result) > 0`) | Treat no data as success | A canary that receives no traffic has not been verified, so it must not be promoted |
| **`consecutiveErrorLimit: 4`** | Ignore query errors | If Prometheus is down, the analysis errors out and the rollout aborts: fail safe, tested in `chaos-prometheus-outage.sh` |
| **`failureLimit: 1`** (abort on 2nd failure) | Abort on the first failure | One noisy 30-second sample doesn't kill a good release; a real regression still aborts within about a minute |
| **One Service, no stable/canary Services** | Separate Services with selector rewriting | Avoids a field-ownership conflict between Helm 4 server-side apply and the Rollouts controller (see troubleshooting) |
| **Load generator in-cluster** | Rely on real users | A lab needs steady traffic so every step produces samples. In production, real traffic fills this role |
| **Rules as files, ConfigMap generated at deploy** | Inline rules in the Prometheus manifest | The rules unit-tested by promtool are byte-for-byte the rules Prometheus runs |

## Security

- **Pods are locked down:**
  - non-root (UID 10001)
  - read-only root filesystem
  - all Linux capabilities dropped
  - `seccompProfile: RuntimeDefault`
  - no service-account token mounted
- **Network isolation:** a NetworkPolicy admits ingress only from the same namespace and from `monitoring`. `scripts/check-network-policy.sh` verifies that a pod in an unrelated namespace is blocked.
- **Image:**
  - multi-stage build with no pip cache
  - runs as a non-root user
  - CI scans it with Trivy and fails on fixable HIGH/CRITICAL vulnerabilities
- **Grafana admin password:** generated randomly at deploy time and stored only as a Kubernetes Secret. Nothing secret is in the repository.
- **Least-privilege discovery:** Prometheus' ClusterRole can only `get/list/watch` pods.

## Possible extensions

| Extension | What it adds |
|---|---|
| Traffic router (Gateway API, Istio, NGINX) | Exact percentages (1%, 5%) independent of the replica count |
| Alertmanager | Routes the burn-rate pages to on-call (PagerDuty, Slack) |
| Argo CD | Releases come from Git commits instead of `helm upgrade` (GitOps) |
| A full 30-day SLO window | Needs long-term storage such as Thanos or Mimir |
