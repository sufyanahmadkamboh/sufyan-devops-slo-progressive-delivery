# 3. kind (Kubernetes in Docker)

## What is it?

**kind** creates a **real** Kubernetes cluster where every "machine" (node) is a Docker container on your computer. It was built by the Kubernetes project itself to test Kubernetes, so it is the genuine Kubernetes software, not a simulator.

## Why this project uses it

| Need | How kind meets it |
|---|---|
| Learn and test for free | No cloud account, no bill |
| Reproducible | The cluster is defined in a file ([`kind/cluster.yaml`](../kind/cluster.yaml)) and rebuilt in about 1 minute |
| Same setup in CI | GitHub Actions creates the identical cluster with `helm/kind-action`, so "works on my laptop" and "works in CI" mean the same thing |
| Several nodes | Canary and stable Pods spread across 2 worker nodes, closer to real life than a single node |

**Alternatives:**

| Tool | What it is | Why not used here |
|---|---|---|
| minikube, k3d | Other local clusters | Fine choices. kind was chosen because it's the standard for CI |
| EKS, GKE, AKS | Managed clusters in the cloud | They cost money. Nothing in this project depends on a specific cloud, so the same chart would run on EKS unchanged |

## How it is used in this project

```yaml
# kind/cluster.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: slo-delivery
nodes:
  - role: control-plane    # runs the Kubernetes "brain" (API server, scheduler, controllers)
  - role: worker           # runs our Pods
  - role: worker
```

- **[`scripts/up.sh`](../scripts/up.sh)** runs `kind create cluster --config kind/cluster.yaml` and sets your `kubectl` to talk to it (context `kind-slo-delivery`).
- **[`scripts/build-image.sh`](../scripts/build-image.sh)** runs `kind load docker-image orders-api:<version>`, which copies the image into every node. That's why no registry is needed.
- **`imagePullPolicy: IfNotPresent`** in the chart tells Kubernetes to use the loaded image rather than try to download it.

**Networking:** kind's default network plugin (kindnet) enforces NetworkPolicy. `scripts/check-network-policy.sh` proves it.

## Try it

```bash
kind get clusters                      # slo-delivery
docker ps --filter name=slo-delivery   # the 3 "nodes" are just containers
kubectl config current-context         # kind-slo-delivery
make down && make up                   # destroy and rebuild everything (about 3 min)
```

## Check yourself

1. Is a kind cluster "fake Kubernetes"?
2. Why does the lab not need Docker Hub or another registry?

<details><summary>Answers</summary>

1. **No.** It runs the real Kubernetes components; only the nodes are containers instead of VMs.
2. **No registry needed:** `kind load docker-image` copies locally built images directly into the nodes, and `imagePullPolicy: IfNotPresent` makes Kubernetes use them.
</details>

Next: [4. Helm](04-helm.md)
