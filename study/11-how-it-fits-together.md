# 11. How everything fits together

This chapter follows **one request** and then **one release** through every tool, so you can see how each piece hands work to the next.

## A. The life of one request

```
1. orders-loadgen Pod sends GET http://orders-api/api/orders            (load generator, 20 req/s)
2. Kubernetes DNS resolves "orders-api" to the Service IP                (Kubernetes Service)
3. The Service picks one ready Pod labelled app=orders-api               (old OR new version)
4. NetworkPolicy allows it: the source is in the same namespace          (Kubernetes NetworkPolicy)
5. orders-api handles it and increments
     http_requests_total{route="/api/orders",code="200"}                 (Python + prometheus-client)
     http_request_duration_seconds_bucket{le="0.025",...}
6. Every 5 s, Prometheus scrapes that Pod's /metrics, adding labels
     app, version, rollouts_pod_template_hash, pod                       (Prometheus discovery + relabelling)
7. Every 15 s, recording rules update slo:sli_error:ratio_rate5m, …      (Prometheus rules)
8. Grafana queries those series and draws the charts                     (Grafana)
```

## B. The life of one release

```
 t=0   You run: scripts/release.sh 1.2.0 --inject-errors
         ├─ docker build -t orders-api:1.2.0                (Docker)
         ├─ kind load docker-image orders-api:1.2.0          (kind)
         └─ helm upgrade --set image.tag=1.2.0               (Helm: the Rollout's Pod template changes)

 t=1s  Argo Rollouts notices the new Pod template           (Argo Rollouts controller)
         ├─ creates a new ReplicaSet with hash 6bb66c87ff
         ├─ setWeight 20 → 1 canary Pod + 4 stable Pods
         └─ starts AnalysisRun "orders-api-6bb66c87ff-3"
            with arg canary-hash=6bb66c87ff

 t≈10s The canary Pod is ready; the Service starts sending it about 20% of requests
         └─ 25% of its responses are 500 (injected fault)

 t≈20s First measurement: the AnalysisRun asks Prometheus     (Argo Rollouts → Prometheus)
         error ratio of pods with rollouts_pod_template_hash="6bb66c87ff" → 0.217
         0.217 ≤ 0.072?  NO → failed (1 of 2 allowed)

 t≈35s Second measurement → 0.198 → failed (2) > failureLimit (1)
         └─ AnalysisRun phase = Failed

 t≈47s Argo Rollouts ABORTS the rollout
         ├─ canary ReplicaSet scaled to 0
         ├─ stable ReplicaSet back to 5 Pods
         └─ Rollout: abort=true, phase=Degraded, message names the failed metric

 after Clients only get 1.1.0 again (verified by e2e.sh)
       Grafana: the canary error line spiked, then its traffic dropped to 0
       Burn-rate alerts: no page, because only 20% of traffic was exposed for under a minute
```

These timings are the real measurements from the lab run (`ci/fast-values.yaml`, 15 s interval). See [docs/test-results.md](../docs/test-results.md).

## C. Why each tool is there (and what would happen without it)

| Remove… | What breaks |
|---|---|
| Docker | Nothing to deploy; versions aren't immutable artifacts |
| Kubernetes | No self-healing, no Services, no Pods for Argo Rollouts to manage |
| kind | You'd need a paid cloud cluster to practise and test |
| Helm | Copy-pasted YAML per environment; the threshold would no longer be computed from the SLO |
| Prometheus | No SLIs: the analysis has nothing to measure, so every rollout aborts (fail safe) |
| The `rollouts_pod_template_hash` relabel | Canary and stable are indistinguishable; analysis returns no data |
| Argo Rollouts | Back to rolling updates: bad versions reach 100% with no automatic decision |
| Grafana | The system still works, but humans can't see or explain what happened |
| GitHub Actions | Nobody notices when a change breaks the safety net itself |
| promtool tests | An alert could silently never fire, and you'd find out during an incident |

## D. Files, mapped to concepts

| Concept | File |
|---|---|
| SLI metrics in code | `app/orders_api/server.py` |
| SLO numbers | `charts/orders-api/values.yaml` (`slo:`), `slo/rules/orders-api-slo.rules.yaml` |
| Canary steps | `charts/orders-api/templates/rollout.yaml` |
| Release gate | `charts/orders-api/templates/analysistemplate.yaml` |
| Version-aware scraping | `platform/monitoring/prometheus.yaml` (relabel_configs) |
| Burn-rate alerts | `slo/rules/orders-api-slo.rules.yaml` |
| Alert tests | `slo/tests/orders-api-slo.test.yaml` |
| Dashboard | `grafana/dashboards/orders-api-slo.json` |
| Full automation | `scripts/*.sh`, `Makefile`, `.github/workflows/ci.yaml` |

Next: [12. Hands-on labs](12-hands-on-labs.md)
