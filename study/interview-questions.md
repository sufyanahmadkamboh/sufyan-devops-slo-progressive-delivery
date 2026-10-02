# Interview questions this project prepares you for

Try to answer each question out loud first, then open the answer.

## SRE and SLOs

1. **What is the difference between an SLI, an SLO and an SLA?**
   <details><summary>Answer</summary>An SLI is a measurement (non-5xx requests ÷ all requests). An SLO is the internal target for it (99.5% over 30 days). An SLA is an external contract with consequences, usually looser than the SLO.</details>

2. **What is an error budget and how do teams use it?**
   <details><summary>Answer</summary>1 − SLO: the amount of failure allowed. With budget left, teams ship faster; when it runs out, they prioritise reliability work. It turns reliability into a shared, measurable trade-off.</details>

3. **Explain burn rate. What does 14.4x mean?**
   <details><summary>Answer</summary>Error ratio ÷ budget. 14.4x spends the 30-day budget in about 2 days, which is 2% of the budget per hour. It is the classic fast-burn paging threshold.</details>

4. **Why use multi-window, multi-burn-rate alerts instead of "errors > X% for 5 min"?**
   <details><summary>Answer</summary>The long window ensures significance (no paging on blips). The short window ensures the problem is current, so alerts resolve quickly after a fix. Different burn rates separate "page now" from "fix this week".</details>

5. **How did you test that your alerts actually fire?**
   <details><summary>Answer</summary>With `promtool test rules`: synthetic series for 10%, 4%, 0.1% errors and slow requests, asserting which alerts fire at which time, and that none fire when healthy.</details>

## Progressive delivery

6. **Compare rolling update, blue/green and canary.**
   <details><summary>Answer</summary>Rolling update replaces Pods gradually but doesn't check health. Blue/green switches all traffic at once between two full environments (fast rollback, but all-or-nothing). Canary shifts a growing share while measuring, so it limits the blast radius.</details>

7. **How does your canary decide to promote or roll back?**
   <details><summary>Answer</summary>A background AnalysisRun queries Prometheus every 30 s for the canary pods only (by pod-template hash): error ratio ≤ 0.072 and p95 ≤ 300 ms. Two failed measurements abort the rollout; passing all steps promotes it.</details>

8. **Why is the canary threshold 0.072?**
   <details><summary>Answer</summary>Budget 0.5% × max burn rate 14.4 = 7.2%. It's the same as the fast-burn page, so a version that would page at full traffic is never promoted. It's computed in Helm from the SLO, not hard-coded.</details>

9. **How do you make sure the analysis measures only the new version?**
   <details><summary>Answer</summary>Prometheus relabelling copies the `rollouts-pod-template-hash` Pod label onto every sample. The Rollout passes the canary's hash to the AnalysisTemplate, and every query filters on it.</details>

10. **What happens if Prometheus is down during a release?**
    <details><summary>Answer</summary>Queries error out. After `consecutiveErrorLimit` (4) is exceeded, the AnalysisRun ends in `Error` and the rollout aborts. That's fail safe: unverified releases are never promoted. It was tested with a chaos script (aborted 60 s after the outage).</details>

11. **What if the canary receives no traffic?**
    <details><summary>Answer</summary>The query returns no data, `len(result) > 0` fails, and the release isn't promoted. "No evidence" is treated as "not verified".</details>

12. **Your canary weights are 20/40/60/80. How is traffic split without a service mesh?**
    <details><summary>Answer</summary>By replica ratio: one Service selects all Pods, so 1 of 5 Pods gets about 20%. The trade-off is granularity of 1/replicas. A traffic router (Gateway API, Istio, NGINX) gives exact percentages.</details>

13. **What regression would slip through your canary, and how is it caught?**
    <details><summary>Answer</summary>One below the gate, for example 4% errors. The 6x slow-burn alert (6h and 30m windows) catches it, and that is proven in the promtool tests.</details>

## Kubernetes and Helm

14. **Readiness vs liveness probe?**
    <details><summary>Answer</summary>Readiness controls whether the Pod receives traffic. Liveness controls whether the container gets restarted.</details>

15. **How does your service shut down gracefully?**
    <details><summary>Answer</summary>On SIGTERM it fails `/readyz` so it is removed from the Service, waits 5 s for in-flight requests, then stops. `terminationGracePeriodSeconds` is 20.</details>

16. **Which pod security controls did you apply?**
    <details><summary>Answer</summary>Non-root UID, read-only root filesystem, no privilege escalation, all capabilities dropped, seccomp RuntimeDefault, no service-account token, CPU and memory limits, and a NetworkPolicy.</details>

17. **What was the Helm 4 server-side-apply problem?**
    <details><summary>Answer</summary>Helm 4 owns every field it applies. Argo Rollouts rewrites the selectors of stable/canary Services, so the next upgrade conflicted on `.spec.selector`. I removed those Services and scoped the analysis by pod hash, so every field has one owner.</details>

18. **Why template the threshold in Helm instead of writing 0.072?**
    <details><summary>Answer</summary>One source of truth: change the SLO and the gate follows automatically. It avoids drift between the business target and the technical limit.</details>

## Observability

19. **Why `rate()` on counters, and why `or vector(0)` in the error ratio?**
    <details><summary>Answer</summary>`rate()` gives the per-second increase and handles counter resets. `or vector(0)` makes the numerator 0 when no 5xx series exists yet, instead of an empty result.</details>

20. **How is p95 computed, and what limits its accuracy?**
    <details><summary>Answer</summary>`histogram_quantile(0.95, …)` over bucket rates. It interpolates inside buckets, so precision depends on the bucket boundaries (600 ms read as 0.975 s within the 0.5–1 s bucket).</details>

21. **Why are recording rules used?**
    <details><summary>Answer</summary>They pre-compute expensive queries over long windows, give them stable names that alerts and dashboards share, and make evaluation cheap.</details>

## CI/CD and DevSecOps

22. **What does your pipeline test, and in what order?**
    <details><summary>Answer</summary>The fast checks run in parallel: unit tests, lint, shellcheck, promtool, helm lint, kubeconform, and the image build plus Trivy. Only if all pass does a kind cluster run the real release scenarios, the chaos test and the network-policy test. Diagnostics are uploaded on failure.</details>

23. **The image scan failed. What did you do?**
    <details><summary>Answer</summary>The findings came from pip's vendored libraries, setuptools and an OS package, not the app. I removed pip and setuptools from the runtime image and applied OS updates, which got the scan to 0 findings. I fixed the cause rather than suppressing it.</details>

24. **Why pin tool versions in CI?**
    <details><summary>Answer</summary>Reproducibility: the same commit gives the same result, and upstream changes can't silently break or weaken the pipeline.</details>

25. **What would you add for production?**
    <details><summary>Answer</summary>A traffic router for fine-grained weights, Alertmanager routing, GitOps with Argo CD, persistent and long-term metrics storage (Thanos or Mimir) for real 30-day windows, and signed images with admission verification.</details>
