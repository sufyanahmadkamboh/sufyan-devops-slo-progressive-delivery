# Runbook: orders-api SLO alerts and release aborts

Every alert's `runbook_url` points to a section of this page.

**Quick commands:**
```bash
kubectl -n delivery get rollout orders-api -o wide                  # phase, step, stable vs current revision
kubectl -n delivery get analysisrun --sort-by=.metadata.creationTimestamp
kubectl -n delivery get analysisrun <name> -o yaml | sed -n '/^status:/,$p'   # which metric failed, with values
kubectl -n monitoring port-forward svc/grafana 3000:3000               # dashboard "orders-api: SLOs & progressive delivery"
```

## fast-burn

**OrdersApiErrorBudgetFastBurn (page):** more than 7.2% of requests are failing. That's 14.4x the sustainable rate, enough to spend 2% of the monthly error budget in one hour.

1. **Is a release in progress?** Run `kubectl -n delivery get rollout orders-api`.
   - If the phase is `Progressing` or `Paused`, the canary analysis normally aborts it on its own within about a minute. If it hasn't, abort it manually by pointing the spec back at the stable version: `helm upgrade orders-api charts/orders-api -n delivery --reuse-values --set image.tag=<stable>`.
2. **Find the failing revision.** In Grafana, check *Error ratio by revision*. Errors from a single revision point to the release. Errors from all revisions point to a dependency or the platform.
3. **No release involved:** check node health (`kubectl get nodes`), pod restarts (`kubectl -n delivery get pods`) and recent configuration changes.
4. **Close out:** when the 5m burn rate drops below 14.4x, the alert resolves within minutes because of the short window. Write up an incident note with the budget consumed (the *Error budget remaining* panel).

## slow-burn

**OrdersApiErrorBudgetSlowBurn (page):** 3–7% of requests have been failing for hours. Not an outage, but it will exhaust the budget in under a week.

- A slow burn often follows a promoted release whose regression was smaller than the canary gate (7.2%).
  - Compare the timing with `kubectl -n delivery get rs` (the newest ReplicaSet's age).
  - If it matches, roll back: `helm rollback orders-api -n delivery`. The previous version then goes through the same canary analysis, which it is expected to pass.
- **Consider tightening `analysis.maxBurnRate`** if regressions like this one keep getting through.

## ticket-burn

**OrdersApiErrorBudgetTicketBurn (ticket):** the budget is draining 3x faster than sustainable over the last day. No immediate action is needed. Raise a ticket to find the cause before it becomes a page, and look at the error ratio by revision across the day.

## latency-burn

**OrdersApiLatencyBudgetFastBurn (page):** more than 14.4% of requests take longer than 300 ms.

- Check *p95 latency by revision*.
- A single slow revision points to the release (the `canary-p95-latency` gate should have stopped it).
- If all revisions are slow, check CPU throttling against the `250m` limit (`kubectl top pods -n delivery`) and node pressure.

## Release aborted by the analysis

**What it means:** the safety net worked. Users were protected and stable is serving 100%.

1. **Find the failing check:**
   ```bash
   run=$(kubectl -n delivery get analysisrun --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1:].metadata.name}')
   kubectl -n delivery get analysisrun "$run" -o jsonpath='{range .status.metricResults[*]}{.name}{"\t"}{.phase}{"\t"}{.measurements[-1].value}{"\n"}{end}'
   ```
2. **Act on the phase:**
   - **`Failed`:** the canary breached an SLO. Fix the release.
   - **`Error`:** the analysis could not measure, for example because Prometheus was unreachable. Fix monitoring first, then retry the same version.
3. **Clear the aborted state** by setting the desired version back to stable, or by releasing a fixed version: `scripts/release.sh <fixed-version>`.
