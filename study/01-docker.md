# 1. Docker and containers

## What is it?

**The problem Docker solves:** a program needs more than its own code to run. It needs a language runtime (here Python 3.13), libraries (here `prometheus-client`) and an operating system underneath. "It works on my machine" happens when those differ between computers.

A **container image** is a snapshot that contains the program **and** everything it needs. A **container** is a running copy of that image. **Docker** is the tool that builds images and runs containers.

| Term | Meaning |
|---|---|
| **Dockerfile** | The recipe: step-by-step instructions to build the image |
| **Image** | The built result: read-only, versioned with a **tag** (`orders-api:1.1.0`) |
| **Container** | A running instance of an image, isolated from other processes |
| **Registry** | A storage place for images (Docker Hub, GHCR, ECR). This lab loads images straight into kind instead |

**A container is not a virtual machine.** It shares the host's kernel, so it starts in milliseconds and uses little memory.

## Why this project uses it

- **Kubernetes only runs containers**, so the app must be packaged as an image.
- **Each release is a new image tag** (`1.1.0`, `1.2.0`, …). Argo Rollouts compares old and new versions, and that only works if each version is an immutable, separately tagged artifact.

## How it works in this project

The recipe is [`app/Dockerfile`](../app/Dockerfile). Line by line:

```dockerfile
FROM python:3.13-slim AS build            # stage 1: start from an official Python image
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt   # install libraries into /install

FROM python:3.13-slim                     # stage 2: start clean again (the "runtime" image)
RUN apt-get update && apt-get upgrade -y ... \
 && python -m pip uninstall -y setuptools wheel pip \   # remove tools not needed at runtime
 && useradd --uid 10001 ... app           # create a non-root user
COPY --from=build /install /usr/local     # copy ONLY the installed libraries from stage 1
COPY orders_api/ orders_api/              # copy our code
USER 10001                                # never run as root
ENTRYPOINT ["python", "-m"]
CMD ["orders_api.server"]                 # default program; the load generator overrides this
```

**Key ideas used here:**

| Idea | Where | Why it matters |
|---|---|---|
| **Multi-stage build** | two `FROM` lines | Build tools stay in stage 1 and the final image is smaller with fewer vulnerabilities |
| **Non-root user** | `USER 10001` | If the app is hacked, the attacker isn't root inside the container |
| **Remove pip** | `pip uninstall … pip` | The security scan (Trivy) found vulnerabilities inside pip's bundled libraries. The app doesn't need pip at runtime, so it is removed |
| **Build argument** | `ARG APP_VERSION` | The version number is baked into the image, and the app reports it at `/version` |
| **`.dockerignore`** | `app/.dockerignore` | Keeps tests and caches out of the image |

**The same image is used two ways:**
- the API: `CMD orders_api.server`
- the load generator: the Helm chart passes `args: ["orders_api.loadgen"]`

One artifact serving two roles is simpler to maintain.

**Where images are built:** [`scripts/build-image.sh`](../scripts/build-image.sh) runs `docker build` and then `kind load docker-image`. That copies the image straight into the kind cluster's nodes, so no registry is needed for the lab.

## Try it

```bash
docker build -t orders-api:study app                 # build the image
docker image ls orders-api                            # see its size and tag
docker run --rm -p 8080:8080 orders-api:study         # run it (Ctrl+C to stop)
# in another terminal:
curl localhost:8080/api/orders
curl localhost:8080/metrics | head -20                # the numbers Prometheus will collect
docker run --rm --entrypoint id orders-api:study      # proves it runs as uid 10001, not root
docker run --rm -e FAULT_ERROR_RATE=0.5 -p 8080:8080 orders-api:study   # now about half the requests fail
```

## Common mistakes

- **Running as root:** this is the default in many images. Always add a `USER`.
- **One huge single-stage image** that carries compilers and caches into production.
- **The `latest` tag in production:** you can no longer tell which version is running, or roll back to "the previous one".

## Check yourself

1. Why are there two `FROM` lines?
2. What would break if every release used the same tag, `orders-api:latest`?
3. Why was pip removed from the final image?

<details><summary>Answers</summary>

1. **Two `FROM` lines:** this is a multi-stage build. Dependencies are installed in a build stage, and only the result is copied into a clean runtime stage, which gives a smaller, safer image.
2. **One shared tag:** Kubernetes and Argo Rollouts couldn't tell versions apart, so you couldn't compare canary and stable, roll back reliably, or know what's running.
3. **Removing pip:** it isn't needed at runtime, and its bundled libraries had known vulnerabilities that Trivy flagged. Less software means a smaller attack surface.
</details>

Next: [2. Kubernetes](02-kubernetes.md)
