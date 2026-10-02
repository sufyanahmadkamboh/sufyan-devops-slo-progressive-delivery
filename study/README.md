# Study guide: learn every tool used in this project

This guide is for engineers who are **new to DevOps**. You don't need to know any of these tools before you start. Each chapter explains:

1. **What** the tool is, in plain language
2. **Why** this project uses it, and what problem it solves here
3. **How** it works: the few concepts you really need
4. **Where** it is wired into this repository, with file paths
5. **Try it:** commands to run in the lab
6. **Check yourself:** short questions (answers at the end of each chapter)

## How to use this guide

Read the chapters in order. Each one builds on the previous ones. Do the "Try it" sections with the lab running (`make up`). Reading alone won't make the ideas stick; running the commands will.

| Step | Chapter | You will understand |
|---|---|---|
| 0 | [The big picture](00-big-picture.md) | What the whole system does, in 5 minutes, with no jargon |
| 1 | [Docker and containers](01-docker.md) | How the application is packaged |
| 2 | [Kubernetes](02-kubernetes.md) | Where and how the containers run |
| 3 | [kind](03-kind.md) | How we get a real Kubernetes cluster on a laptop |
| 4 | [Helm](04-helm.md) | How all the Kubernetes files are packaged and versioned |
| 5 | [SRE basics: SLI, SLO, error budget, burn rate](05-sre-slo-basics.md) | How "healthy" is defined with numbers |
| 6 | [Prometheus and PromQL](06-prometheus.md) | How metrics are collected and queried |
| 7 | [Progressive delivery and Argo Rollouts](07-argo-rollouts.md) | How releases are shifted step by step and rolled back |
| 8 | [Grafana](08-grafana.md) | How the numbers are visualised |
| 9 | [GitHub Actions (CI/CD)](09-github-actions.md) | How every change is tested automatically |
| 10 | [Quality and security tools](10-quality-security-tools.md) | pytest, ruff, shellcheck, promtool, kubeconform, Trivy |
| 11 | [How everything fits together](11-how-it-fits-together.md) | Following one request and one release through the whole system |
| 12 | [Hands-on labs](12-hands-on-labs.md) | 8 guided exercises, from "look around" to "break it on purpose" |
| | [Glossary](glossary.md) | Every term in one place |
| | [Interview questions](interview-questions.md) | 25 questions this project prepares you for, with answers |

## Before you start

**You need:**
- **Docker Desktop**, running
- **Command-line tools:** `kind`, `kubectl`, `helm`, `make` and bash. On Windows, use Git Bash or WSL.
- About **4 GB** of free memory

```bash
make up        # builds the whole lab in about 3 minutes
```

**Time needed:**
- about 1 hour to read chapters 0–4
- about 2 hours for chapters 5–11
- 2–3 hours for the labs

## A tip for learning

Every time you read "this project uses X", open the file mentioned next to it and find the line. The best way to learn a tool is to see it doing a real job, and this repository is that job.
