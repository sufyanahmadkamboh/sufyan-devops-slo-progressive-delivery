Safe releases that undo themselves: SLO-driven canary releases with automatic rollback on Kubernetes.

Every release of a service goes out as a canary: 20% of traffic first, then 40, 60, 80 and 100. While the traffic shifts, Argo Rollouts asks Prometheus how the new version is doing against its SLOs (error ratio and p95 latency). A healthy release is promoted with nobody in the loop; a release that would burn the error budget too fast is aborted and rolled back automatically, while the old version keeps serving users.

A senior DevOps engineer explains the project to a junior colleague: the problem, SLIs, SLOs, error budgets and burn rates in plain words, the architecture, the code, and then a real run on a local kind cluster: one good release promoted, an error regression and a latency regression rolled back, a monitoring outage that fails safe, and a NetworkPolicy check. Every command, output and dashboard on screen is from that run.

Chapters
0:00 The problem
1:44 SLI, SLO, error budget
3:37 Architecture
7:00 A real run
8:27 Release 1: a healthy version
9:51 Release 2: 25% errors
11:16 Release 3: 600 ms slower
12:17 When monitoring breaks
13:00 Security
13:42 Tests and CI
14:20 Recap

The project (free, MIT, with a beginner study guide): https://github.com/sufyanahmadkamboh/sufyan-devops-slo-progressive-delivery
Try it yourself: clone the repository, run scripts/up.sh, then scripts/e2e.sh.

#kubernetes #devops #sre #argorollouts #prometheus
