# 10. Quality and security tools

These small tools each catch one class of mistake **before** it reaches a cluster. All of them run in CI.

| Tool | Checks | Catches, for example | Run it |
|---|---|---|---|
| **pytest** | Python unit tests | Fault injection producing the wrong error rate | `make test` |
| **ruff** | Python lint and format | Unused imports, insecure patterns, style | `cd app && ruff check .` |
| **ShellCheck** | Bash scripts | Unquoted variables, `A && B \|\| C` traps | `shellcheck scripts/*.sh` |
| **promtool** | Prometheus rules | Syntax errors, and **alerts that don't fire when they should** | `make slo-test` |
| **helm lint** | Helm chart | Template errors, missing fields | `helm lint charts/orders-api` |
| **kubeconform** | Kubernetes YAML against official schemas | Typos such as `replica:` vs `replicas:`, wrong types | `make lint` |
| **Trivy** | Container image vulnerabilities | Known CVEs in OS packages and libraries | see below |

## pytest: unit tests for the app

[`app/tests/test_server.py`](../app/tests/test_server.py) tests the logic without starting a server:
- metrics are counted per route and code
- probes are not counted as traffic
- `FAULT_ERROR_RATE=0.25` produces between 22% and 28% errors over 2,000 requests
- invalid configuration is rejected

**A design choice that makes testing easy:** `App.handle()` is plain Python that returns `(status, content_type, body)`, separate from the HTTP server.

## promtool: unit tests for alerts (rarely done, very valuable)

**Most teams never test their alerts.** They find out during an incident that an alert never fires. [`slo/tests/orders-api-slo.test.yaml`](../slo/tests/orders-api-slo.test.yaml) feeds **synthetic time series** into the real rules and asserts the outcome:

```yaml
- name: fast burn pages within minutes
  input_series:
    - series: 'http_requests_total{app="orders-api",route="/api/orders",method="GET",code="200"}'
      values: '0+90x120'       # starts at 0, +90 every minute, for 120 minutes
    - series: '...code="500"}'
      values: '0+10x120'       # +10 per minute, so 10% errors
  alert_rule_test:
    - eval_time: 10m
      alertname: OrdersApiErrorBudgetFastBurn
      exp_alerts: [ { exp_labels: { severity: page, ... } } ]   # MUST be firing
```

**The four tests prove:**
- **10% errors:** fast burn pages.
- **4% errors:** slow burn pages, but fast burn doesn't.
- **0.1% errors:** nothing fires, and 80% of the budget is left.
- **Slow requests:** the latency alert fires.

## kubeconform: schema validation

```bash
helm template orders-api charts/orders-api | kubeconform -strict -summary \
  -schema-location default \
  -schema-location 'https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json'
```
- **`-strict`** rejects unknown fields, which catches typos.
- **The second schema location** provides schemas for **custom** resources such as Argo Rollouts' `Rollout` and `AnalysisTemplate`, which plain Kubernetes doesn't know.

## Trivy: image vulnerability scanning

```bash
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:0.75.0 \
  image --exit-code 1 --ignore-unfixed --severity HIGH,CRITICAL orders-api:1.1.0
```

| Flag | Why |
|---|---|
| `--severity HIGH,CRITICAL` | Focus on serious issues |
| `--ignore-unfixed` | Only fail on vulnerabilities that **have** a fix, so the pipeline stays actionable |
| `--exit-code 1` | Makes CI fail when something is found |

**What happened in this project:** the first scan found **5 HIGH** vulnerabilities. None were in the app's own dependency:
- urllib3 and msgpack, inside **pip**
- setuptools
- an OS package (libpcre2)

**The fix was architectural, not a suppression:**
- remove pip and setuptools from the runtime image
- apply OS security updates

Result: **0 findings**. That's the DevSecOps habit: fix the cause, don't silence the scanner.

## Check yourself

1. What does promtool *test* (not *check*) give you that a syntax check doesn't?
2. Why `--ignore-unfixed` in CI?
3. Why does kubeconform need an extra schema location for this project?

<details><summary>Answers</summary>

1. **Behaviour:** proof that alerts fire under the right conditions, at the right time, and stay silent otherwise.
2. **`--ignore-unfixed`:** failing on vulnerabilities nobody can fix yet would block every build without giving anyone an action to take.
3. **The extra schema location:** Rollout and AnalysisTemplate are Custom Resources. Their schemas come from a CRD catalog, not from Kubernetes itself.
</details>

Next: [11. How everything fits together](11-how-it-fits-together.md)
