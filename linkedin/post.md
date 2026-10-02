"Is the deployment green?" and "is the new version healthy for users?" are two different questions. Most pipelines only answer the first one.

I built a project to answer the second one automatically: SLO-driven progressive delivery with automated rollback on Kubernetes.

🔧 What it does
Every release goes out as a canary: 20% → 40% → 60% → 80% → 100% of traffic. While traffic shifts, Argo Rollouts queries Prometheus every 30 seconds for the canary's own SLIs (error ratio and p95 latency) and compares them with the service's SLOs.

✅ Meets the SLOs → promoted step by step
❌ Breaches them → aborted, canary removed, the stable version keeps serving 100%

📐 The decision I like most
The availability SLO is 99.5%, so the error budget is 0.5%. A canary may burn that budget at most 14.4x faster than sustainable, which gives a 7.2% error-ratio limit. 14.4x is exactly the fast-burn paging threshold from the Google SRE Workbook model I used for alerting. So the release gate and the on-call page share one definition of "unhealthy": a release that would page someone at full traffic is never promoted.

🧪 How I tested it (local kind cluster)
• A healthy release was promoted after passing every SLO check
• A release with injected 25% errors was aborted about 45 seconds after release, with the stable version untouched
• A release with +600 ms latency was rolled back on the latency SLO
• I took Prometheus down in the middle of a canary: the analysis ended in "Error" and the rollout aborted. A release that can't be verified is never promoted
• The burn-rate alert logic is unit-tested with promtool, and the full flow runs in GitHub Actions on kind

💡 Two things I learned on the way
1️⃣ Helm 4 uses server-side apply. If Helm renders Service selectors that Argo Rollouts later rewrites, the next upgrade fails with a field-ownership conflict. Scoping the analysis to the pod-template-hash label removed the need for those Services.
2️⃣ Trivy flagged fixable HIGH vulnerabilities in the image. They came from pip's bundled libraries, not my code. Removing pip from the runtime image and applying OS updates got the scan clean.

Stack: Kubernetes · Argo Rollouts · Prometheus · Grafana · Helm · GitHub Actions · Docker · Python · Trivy

📂 Code, architecture and runbook: https://github.com/sufyanahmadkamboh/sufyan-devops-slo-progressive-delivery
🌐 Portfolio: https://sufyanahmadkamboh.github.io/

How do you decide when a release is "good enough" to promote: manual checks, metrics, or SLOs?

#DevOps #SRE #Kubernetes #ProgressiveDelivery #ArgoRollouts #Prometheus #Grafana #SLO #Observability #CICD
