# 2. Kubernetes

## What is it?

**Kubernetes** (often written **K8s**) runs containers on a group of machines (a **cluster**) and keeps them in the state you asked for.

You don't tell Kubernetes *how* to do things ("start a container on machine 2"). You declare *what* you want ("5 copies of orders-api must always be running"), and Kubernetes continuously works to make reality match. This is called **declarative** configuration, and the matching loop is called **reconciliation**.

## The objects you need for this project

You describe what you want in YAML files. Each file describes an **object**:

| Object | What it is | In this project |
|---|---|---|
| **Pod** | The smallest unit: one or more containers that run together | Each copy of orders-api is a Pod |
| **ReplicaSet** | Keeps N identical Pods running | Argo Rollouts creates one per version (stable and canary) |
| **Deployment** | Manages ReplicaSets for rolling updates | Used for the load generator, Prometheus and Grafana |
| **Rollout** (custom) | Argo Rollouts' smarter replacement for Deployment | orders-api, see chapter 7 |
| **Service** | A stable name and IP that load-balances across matching Pods | `orders-api` (port 80) spreads traffic across all versions |
| **Namespace** | A folder that groups objects | `delivery` (app), `monitoring` (Prometheus, Grafana), `argo-rollouts` |
| **ConfigMap** | Configuration files stored in the cluster | Prometheus config, SLO rules, Grafana dashboard |
| **Secret** | Like a ConfigMap, but for sensitive values | Grafana admin password (generated randomly) |
| **ServiceAccount + RBAC** | An identity for a Pod, plus what it is allowed to do | Prometheus may only *read* the pod list |
| **NetworkPolicy** | A firewall between Pods | Only the same namespace and Prometheus may call orders-api |

**Labels hold everything together.** A label is a key/value tag such as `app: orders-api`. A Service sends traffic to every Pod whose labels match its **selector**:

```yaml
# charts/orders-api/templates/services.yaml (rendered)
kind: Service
metadata: { name: orders-api }
spec:
  selector: { app: orders-api }   # every Pod labelled app=orders-api, old AND new version
  ports: [{ port: 80, targetPort: http }]
```

Because this Service selects both versions, **traffic splits by the number of Pods**: if 1 of 5 Pods runs the new version, about 20% of requests reach it. Argo Rollouts uses exactly this.

## Health checks: probes

Kubernetes needs to know if a container is healthy. Look at [`rollout.yaml`](../charts/orders-api/templates/rollout.yaml):

```yaml
readinessProbe: { httpGet: { path: /readyz, port: http }, periodSeconds: 5 }   # "may I receive traffic?"
livenessProbe:  { httpGet: { path: /healthz, port: http }, periodSeconds: 10 } # "am I alive, or should I be restarted?"
```

- **Readiness probe failing:** the Pod is removed from the Service and gets no traffic.
- **Liveness probe failing:** the container is restarted.
- **On shutdown,** our app fails `/readyz` first, waits 5 s, then exits (see `shutdown()` in `server.py`). In-flight requests finish instead of failing. This is called **graceful shutdown**.

## Resources

```yaml
resources:
  requests: { cpu: 50m, memory: 64Mi }    # guaranteed; used by the scheduler to place the Pod
  limits:   { cpu: 250m, memory: 128Mi }  # maximum; above the memory limit the container is killed
```

`50m` means 50 millicores, that is 5% of one CPU core.

## Security settings used here

```yaml
securityContext:                 # pod level
  runAsNonRoot: true
  runAsUser: 10001
  seccompProfile: { type: RuntimeDefault }    # blocks dangerous Linux system calls
containers: ... securityContext:  # container level
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true                # the app cannot write to its own filesystem
  capabilities: { drop: ["ALL"] }             # no special Linux powers
automountServiceAccountToken: false           # the app never talks to the Kubernetes API, so it gets no token
```

## Where it is in this repository

| File | Kubernetes objects |
|---|---|
| `charts/orders-api/templates/` | Rollout, Service, ServiceAccount, NetworkPolicy, load-generator Deployment (Helm templates, chapter 4) |
| `platform/monitoring/prometheus.yaml` | Namespace, ServiceAccount, ClusterRole + Binding, ConfigMap, Deployment, Service |
| `platform/monitoring/grafana.yaml` | ConfigMap, Deployment, Service |

## Try it (lab running)

```bash
kubectl get nodes                                  # the 3 machines (containers, in kind)
kubectl get ns                                     # namespaces
kubectl -n delivery get pods -o wide               # 5 orders-api Pods + load generator, and which node each runs on
kubectl -n delivery get pods --show-labels         # see app=orders-api and rollouts-pod-template-hash
kubectl -n delivery describe svc orders-api        # "Endpoints": the Pod IPs behind the Service
kubectl -n delivery delete pod <one-orders-api-pod>   # watch Kubernetes replace it:
kubectl -n delivery get pods -w
kubectl -n delivery logs deploy/orders-loadgen     # status-code counts every 30 s
kubectl explain rollout.spec.strategy.canary       # built-in documentation, works for every field
```

## Check yourself

1. You delete a Pod. Why does a new one appear?
2. How does the `orders-api` Service decide which Pods receive traffic?
3. What is the difference between a readiness and a liveness probe?

<details><summary>Answers</summary>

1. **Reconciliation:** the ReplicaSet wants N Pods, sees N−1, and creates one.
2. **Label selector:** every ready Pod labelled `app: orders-api` is an endpoint, so traffic spreads across them.
3. **Readiness vs liveness:** failing readiness only removes the Pod from traffic. Failing liveness restarts the container.
</details>

Next: [3. kind](03-kind.md)
