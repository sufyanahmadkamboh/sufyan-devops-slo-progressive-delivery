# Glossary

| Term | Meaning |
|---|---|
| **Abort (rollout)** | Argo Rollouts stops a release and returns all traffic to the stable version |
| **AnalysisRun** | One execution of an AnalysisTemplate during a release, with stored measurements and a phase (Running / Successful / Failed / Error) |
| **AnalysisTemplate** | Reusable definition of the metrics and success conditions used to judge a release |
| **Annotation** | Key/value metadata on a Kubernetes object, read by tools (for example `prometheus.io/scrape: "true"`) |
| **Burn rate** | Current error ratio ÷ error budget. 1x lasts exactly the SLO window; 14.4x spends 2% of a 30-day budget per hour |
| **Canary release** | Sending a small, growing share of traffic to a new version while checking its health |
| **CD** | Continuous Delivery/Deployment: automatically releasing changes that passed CI |
| **CI** | Continuous Integration: automatically building and testing every change |
| **ClusterRole / RoleBinding** | RBAC objects that define and grant permissions |
| **ConfigMap** | Kubernetes object holding non-secret configuration files |
| **Container / image** | A running isolated process / the immutable package it starts from |
| **Controller** | A program that watches Kubernetes objects and works to make reality match the desired state |
| **Counter** | Metric type that only increases (for example total requests) |
| **CRD** | Custom Resource Definition: adds a new object type to Kubernetes (for example Rollout) |
| **Error budget** | 1 − SLO: the share of requests allowed to fail (0.5% for a 99.5% SLO) |
| **Fail safe** | Design where a failure of the safety system leads to the safe outcome (here: abort, not promote) |
| **Gauge** | Metric type that can go up and down |
| **Helm chart / release** | Templated Kubernetes package / one installed instance with revision history |
| **Histogram** | Metric type that counts observations into buckets, used for latency percentiles |
| **kind** | Kubernetes IN Docker: a real cluster whose nodes are containers |
| **Label / selector** | Key/value tag on objects / a query that matches objects by their labels |
| **Liveness / readiness probe** | Health check that restarts a container / that adds or removes it from traffic |
| **Multi-window alert** | Alert that requires a long AND a short window to exceed a threshold |
| **Namespace** | A grouping and isolation boundary inside a cluster |
| **NetworkPolicy** | Firewall rules between Pods |
| **p95 latency** | 95% of requests are faster than this value |
| **Pod** | The smallest deployable unit in Kubernetes: one or more containers |
| **Pod-template hash** | Label (`rollouts-pod-template-hash`) identifying which version a Pod belongs to |
| **Progressive delivery** | Releasing gradually while verifying health at each step |
| **PromQL** | Prometheus' query language |
| **Recording rule** | Pre-computed, named PromQL result stored as a new time series |
| **Reconciliation** | The loop that keeps changing the cluster until it matches the declared state |
| **Relabelling** | Prometheus rules that add, change or drop labels during discovery or scraping |
| **ReplicaSet** | Keeps a set number of identical Pods running |
| **Rollback** | Returning to a previous version |
| **Rollout** | Argo Rollouts object replacing a Deployment, with canary or blue/green strategies |
| **Scrape** | Prometheus fetching `/metrics` from a target |
| **Server-side apply** | Kubernetes apply mode that tracks which tool owns each field (default in Helm 4) |
| **Service** | Stable network name and load balancer in front of matching Pods |
| **SLA** | Service Level Agreement: an external contract, usually with penalties |
| **SLI** | Service Level Indicator: a measured ratio of good events (for example non-5xx requests ÷ all requests) |
| **SLO** | Service Level Objective: the target for an SLI over a window (for example 99.5% over 30 days) |
| **Stable version** | The version currently trusted to serve all traffic |
| **Time series** | One metric name + one unique label set, with values over time |
| **Trivy** | Scanner for vulnerabilities in images, filesystems and configuration |
