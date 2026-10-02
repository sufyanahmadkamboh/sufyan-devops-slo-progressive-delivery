# 0. The big picture (no jargon)

## The problem, as a story

A team runs an online shop. Its "orders" service answers when a customer opens *My orders*. Every week developers ship a new version.

**The usual way to release:** replace the old version with the new one for everyone. If the new version has a bug, *every* customer hits it at once. Someone gets an alarm at night, has to decide "is this bad enough to undo?", and undoes it by hand.

**What this project does instead:** it releases the new version like a careful restaurant tests a new dish.
1. Serve it to **1 table out of 5** first, and **watch** what happens.
2. If the guests are happy, serve it to 2 tables, then 3, then 4, then everyone.
3. If guests complain, **take it off the menu immediately**, and everyone keeps getting the old dish.

**"Watching" is done with numbers, not opinions:**
- How many requests to the new version **fail**?
- How **slow** is the new version?

Before any release, the team agreed on the limits: "at most 7.2% failures" and "95% of requests faster than 300 ms". A computer checks these numbers every 30 seconds and makes the decision, so nobody has to wake up.

## The pieces, and their jobs

| Piece | Job in one sentence | Restaurant analogy |
|---|---|---|
| **orders-api** (our app) | Answers requests and counts how many succeed or fail | The kitchen |
| **Docker** | Packs the app with everything it needs into one portable box | Meal-prep boxes that taste the same anywhere |
| **Kubernetes** | Runs many copies of the boxes and keeps them alive | The restaurant manager who assigns cooks and replaces sick ones |
| **kind** | A small but real Kubernetes running on your laptop | A practice kitchen at home |
| **Helm** | Installs all the Kubernetes settings in one command, with versions | The recipe book |
| **Prometheus** | Collects the numbers (requests, errors, speed) every 5 seconds | The waiter writing down every complaint and how long each dish took |
| **Argo Rollouts** | Shifts traffic step by step and decides "continue or undo" from the numbers | The head chef who decides whether the new dish stays |
| **Grafana** | Draws the numbers as charts | The whiteboard in the kitchen |
| **GitHub Actions** | Tests everything automatically on every code change | The food inspector who checks before the restaurant opens |

## The flow, in one picture

```
developer pushes code ──► GitHub Actions tests it (unit tests, scans, a full rehearsal on kind)
                                   │
                         helm upgrade (new version)
                                   ▼
          Argo Rollouts: 20% of pods new ──► 40% ──► 60% ──► 80% ──► 100%
                    ▲                    │
     "is the new    │                    │ every 30 s: "error ratio of NEW pods?  p95 latency of NEW pods?"
      version OK?"  │                    ▼
                 yes/no ◄──────── Prometheus ◄── collects numbers from every pod every 5 s
                                       │
                                       ▼
                              Grafana draws the charts
```

## What you will be able to do after this guide

- Explain each tool and **why it was chosen**.
- Run the system, release versions, and watch a bad release get rolled back on its own.
- Read and change the Kubernetes, Helm, Prometheus and CI files.
- Answer the interview questions in [interview-questions.md](interview-questions.md).

Next: [1. Docker and containers](01-docker.md)
