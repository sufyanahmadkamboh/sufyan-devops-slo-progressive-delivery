# 9. GitHub Actions (CI/CD)

## What is it?

**CI (Continuous Integration)** means automatically building and testing every code change. **CD (Continuous Delivery/Deployment)** means automatically releasing changes that passed.

**GitHub Actions** is GitHub's built-in automation. You write a **workflow** (YAML in `.github/workflows/`) that runs on GitHub's machines (**runners**) when something happens, for example a push.

| Term | Meaning |
|---|---|
| **Workflow** | The whole automation file ([`ci.yaml`](../.github/workflows/ci.yaml)) |
| **Trigger** (`on:`) | When it runs: here on push to `main`, on pull requests, and manually |
| **Job** | A group of steps on one fresh machine. Jobs run in parallel unless they `need` each other |
| **Step** | One command (`run:`) or a reusable action (`uses:`) |
| **Action** | A packaged step from the marketplace, for example `actions/checkout`, `helm/kind-action` |

## Why this project uses it

**Every change must prove that the safety net still works.** A pipeline that only runs unit tests could miss a broken Prometheus rule or a broken rollback. This pipeline runs the **real release scenarios on a real cluster** for every push.

**Alternatives:** Jenkins (self-hosted, very flexible), GitLab CI, CircleCI. GitHub Actions is used because the code lives on GitHub and kind runs well on its runners.

## The pipeline in this project

```
push ─┬─► job "static" ─────────┐
      │   pytest, ruff, shellcheck, promtool check + test, helm lint, kubeconform
      ├─► job "image" ──────────┤
      │   docker build, Trivy scan (fails on fixable HIGH/CRITICAL)
      └─────────────────────────┴─► job "e2e" (needs both; runs only if they pass)
                                    create kind cluster → scripts/up.sh
                                    → scripts/e2e.sh (good release promoted, 2 bad ones rolled back)
                                    → scripts/chaos-prometheus-outage.sh
                                    → scripts/check-network-policy.sh
                                    on failure: collect diagnostics → upload as artifact
```

**Good practices to notice in [`ci.yaml`](../.github/workflows/ci.yaml):**

| Practice | Line | Why |
|---|---|---|
| Least-privilege token | `permissions: contents: read` | The workflow can't push code or change settings |
| Cancel outdated runs | `concurrency: … cancel-in-progress: true` | A new push stops the old, now-pointless run |
| Pinned versions | `prom/prometheus:v3.15.0`, `kubeconform v0.8.0`, `trivy:0.75.0` | Same result today and next month |
| Fail fast, expensive last | `needs: [static, image]` | The 15-minute cluster test runs only if the cheap checks pass |
| Debuggable failures | `if: failure()` → upload diagnostics | You get the Rollout, AnalysisRun and controller logs without re-running |
| Same scripts as local | `scripts/up.sh`, `scripts/e2e.sh` | "Passes on my laptop" and "passes in CI" mean the same thing |

**Two real CI lessons from this project:**
1. **ShellCheck versions:** the runner's ShellCheck version flagged a pattern (`A && B || C`, SC2015) that the local version didn't, so the code was fixed.
2. **The executable bit:** the scripts were created on Windows without it, so Linux refused to run them (`Permission denied`). Fixed with `git update-index --chmod=+x scripts/*.sh`.

## Try it

**On GitHub:** open the repository's **Actions** tab, open a run, then open each job and step. You can see every command's output.

**Locally:** the Makefile runs the same checks:
```bash
make test lint slo-test        # the "static" job
make image                     # the build part of the "image" job
make e2e chaos netpol          # the "e2e" job (lab must be up)
```

## Check yourself

1. Why does the `e2e` job declare `needs: [static, image]`?
2. Why are tool versions pinned?
3. What is the benefit of CI calling the same scripts you run locally?

<details><summary>Answers</summary>

1. **`needs`:** it's slow and expensive, so it only runs when the fast checks have passed. That gives quick feedback for simple mistakes.
2. **Pinned versions:** they make results reproducible. An unpinned tool can change behaviour overnight and break or silently weaken the pipeline.
3. **Same scripts locally and in CI:** one implementation, no drift. If it passes locally, CI runs exactly the same steps.
</details>

Next: [10. Quality and security tools](10-quality-security-tools.md)
