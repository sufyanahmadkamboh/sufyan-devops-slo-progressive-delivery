# 5. SRE basics: SLI, SLO, error budget, burn rate

These four ideas come from Google's **Site Reliability Engineering (SRE)** practice. They turn "the service feels slow" into numbers everybody agrees on. This project is built on them.

## SLI: Service Level Indicator, "what we measure"

An SLI is a measurement of user experience, usually as a ratio of good events to all events.

| SLI in this project | Formula |
|---|---|
| **Availability** | requests that did **not** return a 5xx error ÷ all requests |
| **Latency** | requests that finished in **under 300 ms** ÷ all requests |

**Why ratios?** They don't depend on traffic volume: 1 error in 1,000 is the same quality at night as at peak.

## SLO: Service Level Objective, "how good is good enough"

An SLO is a target for an SLI over a time window.

| SLO | Meaning |
|---|---|
| **Availability 99.5%** (30 days) | At most 0.5% of requests may fail |
| **Latency 99% < 300 ms** | At most 1% of requests may be slower than 300 ms |

**100% is never the target.** It's impossibly expensive, and users can't tell 99.99% from 100% anyway.

An **SLA** (Service Level Agreement) is different: it's a contract with customers, usually with financial penalties. SLOs are internal and stricter than any SLA.

## Error budget: "how much failure we can afford"

**Error budget = 1 − SLO.** With 99.5%, the budget is **0.5%** of requests. The budget is something you are *allowed to spend* on releases, experiments and incidents.
- **Budget left:** ship faster.
- **Budget gone:** slow down and fix reliability.

In this repo the recording rule `slo:error_budget_remaining:ratio` computes `1 − (error ratio ÷ 0.005)`.
- **1** means untouched.
- **0** means fully spent.
- **Negative** means overspent.

## Burn rate: "how fast we are spending the budget"

**Burn rate = current error ratio ÷ error budget.**

| Burn rate | Meaning |
|---|---|
| 1x | Spending exactly as planned; the budget lasts the whole 30 days |
| 14.4x | The 30-day budget would be gone in about 2 days. 2% of it disappears every hour |
| 0.5x | Well within budget |

**Example:** the error ratio is 7.2% and the budget is 0.5%, so the burn rate is 7.2 ÷ 0.5 = **14.4x**.

## Multi-window, multi-burn-rate alerting

**The naive alert, "page if errors > 0.5% for 5 minutes", is bad:**
- **Too noisy:** a 5-minute blip pages someone.
- **Too slow** for disasters, and it says nothing about *how much* budget is at risk.

**The SRE Workbook approach, used in [`slo/rules/orders-api-slo.rules.yaml`](../slo/rules/orders-api-slo.rules.yaml):**

| Alert | Fires when the burn rate is above… | …over BOTH windows | Severity |
|---|---|---|---|
| Fast burn | 14.4x | 1 hour **and** 5 minutes | page (wake someone up) |
| Slow burn | 6x | 6 hours **and** 30 minutes | page |
| Ticket burn | 3x | 1 day **and** 2 hours | ticket (fix during work hours) |

**Why two windows:**
- The **long** window proves the problem is significant (not a blip).
- The **short** window proves it is **still happening**, so the alert stops quickly after a fix instead of firing for another hour.

## How this project uses these ideas for releases

**The key design decision:** a canary may burn the error budget **at most 14.4x** faster than sustainable. That's the same number as the fast-burn page:

```
canary limit = error budget × max burn rate = 0.005 × 14.4 = 0.072  (7.2% errors)
```

In plain words: **a version that would page the on-call engineer if it served all users must never be promoted.** Release safety and alerting use one shared definition of "unhealthy".

**One more case:** a regression that is too small for the canary gate (for example 4% errors) still gets caught. Over hours it triggers the **slow-burn** page, which the `promtool` tests prove.

## Try it

**Open Grafana** (`kubectl -n monitoring port-forward svc/grafana 3000:3000`) and find:
- **Availability SLI (5m)**
- **Error budget remaining**
- **Burn rate (1h)**

Then run `scripts/release.sh 1.9.0 --inject-errors` and watch the burn rate rise and the error budget fall while the canary runs. Then watch the canary disappear.

## Check yourself

1. The SLO is 99.9%. What is the error budget, and what error ratio is a 6x burn?
2. Why does each alert need two windows?
3. Why is the canary limit 14.4x the budget, and not, say, 1x?

<details><summary>Answers</summary>

1. **Budget** = 0.1%. A 6x burn is an error ratio of 0.6%.
2. **Two windows:** the long window makes sure the problem is significant; the short window makes sure it is still ongoing, so alerts resolve quickly.
3. **14.4x, not 1x:** a canary only runs for minutes, so judging it at 1x would be extremely strict and noisy. 14.4x means "would trigger a page", which is exactly the line a release must not cross. Smaller regressions are caught later by the slow-burn alert.
</details>

Next: [6. Prometheus and PromQL](06-prometheus.md)
