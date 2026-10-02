# syntax=docker/dockerfile:1.7
# ---- build stage: install dependencies into an isolated prefix ----
FROM python:3.13-slim AS build
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- runtime stage: no pip cache, no build tools, non-root ----
FROM python:3.13-slim
ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
# Apply Debian security updates, and remove pip/setuptools: they are not needed at runtime and
# their bundled libraries (urllib3, msgpack) were the source of HIGH findings in the image scan.
RUN apt-get update \
 && apt-get upgrade -y --no-install-recommends \
 && rm -rf /var/lib/apt/lists/* \
 && python -m pip uninstall -y --no-cache-dir setuptools wheel pip \
 && useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin app
COPY --from=build /install /usr/local
WORKDIR /app
COPY orders_api/ orders_api/
USER 10001
EXPOSE 8080
ENTRYPOINT ["python", "-m"]
CMD ["orders_api.server"]
LABEL org.opencontainers.image.title="orders-api" \
      org.opencontainers.image.source="https://github.com/sufyanahmadkamboh/sufyan-devops-slo-progressive-delivery" \
      org.opencontainers.image.version="${APP_VERSION}"
