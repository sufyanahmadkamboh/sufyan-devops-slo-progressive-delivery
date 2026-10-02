# Project summary: SLO-Driven Progressive Delivery with Automated Rollback

**One line:** Kubernetes releases that promote themselves when they meet their SLOs and roll themselves back when they don't.

**Problem:**
- Rolling updates send a bad release to every user within minutes.
- Most teams only learn about it from alerts or customers.
- Rolling back is a manual decision made under pressure.

**What I built:**
- **Argo Rollouts canary** (20 → 40 → 60 → 80 → 100%) with a background analysis. Every 30 seconds it queries Prometheus for the canary pods' own error ratio and p95 latency.
- **SLO-based gate:** a canary may burn the 0.5% error budget at most 14.4x faster than sustainable, giving an error-ratio limit of 7.2%. It must also keep p95 under 300 ms. 14.4x is the same threshold as the fast-burn page, so the release gate and on-call alerting share one definition of "unhealthy".
- **Multi-window, multi-burn-rate SLO alerts** (14.4x, 6x and 3x), unit-tested with `promtool test rules`.
- **Grafana SLO dashboard,** provisioned as code: error budget, burn rate, and canary vs stable per revision.
- **GitHub Actions pipeline** that runs unit tests, lint, rule tests, Kubernetes schema validation and a Trivy image scan, then proves the full release behaviour on a kind cluster.

**Validated (local kind cluster, 3 nodes):**
- A healthy release was promoted after passing every SLO check.
- A release with injected 25% errors was aborted about 45 seconds after release, and the stable version kept serving 100% of traffic.
- A release with +600 ms latency was aborted on the latency SLO.
- With Prometheus taken down mid-canary, the analysis ended in `Error` and the rollout aborted: unverified releases are never promoted.
- A NetworkPolicy blocks traffic from unrelated namespaces (tested).

**Findings worth sharing:**
- Helm 4's server-side apply conflicts with Argo Rollouts when Helm renders the stable/canary Service selectors that the controller rewrites. I removed the need for those Services by scoping the analysis to the pod-template-hash label.
- The image scan caught fixable HIGH vulnerabilities in pip's bundled libraries and an OS package. Removing pip from the runtime image and applying OS updates cleared them.

**Stack:** Kubernetes (kind), Argo Rollouts, Prometheus, Grafana, Helm, GitHub Actions, Docker, Python, Trivy, promtool, kubeconform

**Repository:** https://github.com/sufyanahmadkamboh/sufyan-devops-slo-progressive-delivery
**Portfolio:** https://sufyanahmadkamboh.github.io/
