"""Orders API: a small HTTP service instrumented with Prometheus metrics.

The service exposes the request metrics that the SLOs and the canary analysis
are built on:

* ``http_requests_total{route,method,code}``: availability SLI (non-5xx ratio)
* ``http_request_duration_seconds{route}``: latency SLI (share of requests under 300 ms)

Fault injection (``FAULT_ERROR_RATE``, ``FAULT_LATENCY_MS``) exists so that a
"bad release" can be reproduced on demand and the automated rollback can be
tested end to end. Both default to 0, so a normal deployment is unaffected.
"""

from __future__ import annotations

import json
import logging
import os
import random
import signal
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Gauge, Histogram, generate_latest

LATENCY_BUCKETS = (0.025, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0, 2.5)

ORDERS = [
    {"id": "ORD-1001", "item": "keyboard", "quantity": 2, "status": "shipped"},
    {"id": "ORD-1002", "item": "monitor", "quantity": 1, "status": "processing"},
    {"id": "ORD-1003", "item": "usb-c dock", "quantity": 3, "status": "delivered"},
]


def _float_env(name: str, default: float, low: float, high: float) -> float:
    raw = os.environ.get(name, "")
    if raw == "":
        return default
    try:
        value = float(raw)
    except ValueError as exc:
        raise SystemExit(f"invalid {name}={raw!r}: not a number") from exc
    if not low <= value <= high:
        raise SystemExit(f"invalid {name}={raw!r}: must be between {low} and {high}")
    return value


class Config:
    """Runtime configuration read once from the environment."""

    def __init__(self) -> None:
        self.version = os.environ.get("APP_VERSION", "dev")
        self.port = int(_float_env("PORT", 8080, 1, 65535))
        self.fault_error_rate = _float_env("FAULT_ERROR_RATE", 0.0, 0.0, 1.0)
        self.fault_latency_ms = _float_env("FAULT_LATENCY_MS", 0.0, 0.0, 10_000.0)


class Metrics:
    """All metrics live in a dedicated registry so tests can create isolated instances."""

    def __init__(self, version: str) -> None:
        self.registry = CollectorRegistry()
        self.requests = Counter(
            "http_requests_total", "HTTP requests handled.", ["route", "method", "code"], registry=self.registry
        )
        self.duration = Histogram(
            "http_request_duration_seconds",
            "HTTP request latency.",
            ["route"],
            buckets=LATENCY_BUCKETS,
            registry=self.registry,
        )
        info = Gauge("app_info", "Build information.", ["version"], registry=self.registry)
        info.labels(version=version).set(1)


class App:
    """Request routing and business logic, independent of the HTTP server for testability."""

    def __init__(self, config: Config, metrics: Metrics, rng: random.Random | None = None) -> None:
        self.config = config
        self.metrics = metrics
        self.rng = rng or random.Random()
        self.ready = True

    def handle(self, method: str, path: str) -> tuple[int, str, bytes]:
        """Return (status, content type, body) for a request."""
        if path == "/metrics":
            return 200, CONTENT_TYPE_LATEST, generate_latest(self.metrics.registry)
        if path == "/healthz":
            return 200, "text/plain", b"ok"
        if path == "/readyz":
            return (200, "text/plain", b"ready") if self.ready else (503, "text/plain", b"shutting down")

        route = path if path in ("/api/orders", "/version") else "other"
        start = time.perf_counter()
        status, body = self._business(method, path)
        self.metrics.duration.labels(route=route).observe(time.perf_counter() - start)
        self.metrics.requests.labels(route=route, method=method, code=str(status)).inc()
        return status, "application/json", json.dumps(body).encode()

    def _business(self, method: str, path: str) -> tuple[int, dict]:
        if method != "GET":
            return 405, {"error": "method not allowed"}
        if path == "/version":
            return 200, {"version": self.config.version}
        if path != "/api/orders":
            return 404, {"error": "not found"}
        if self.config.fault_latency_ms:
            time.sleep(self.config.fault_latency_ms / 1000)
        if self.config.fault_error_rate and self.rng.random() < self.config.fault_error_rate:
            return 500, {"error": "internal error", "version": self.config.version}
        return 200, {"version": self.config.version, "orders": ORDERS}


def make_handler(app: App) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "orders-api"
        sys_version = ""

        def do_GET(self) -> None:  # noqa: N802 (stdlib naming)
            self._serve("GET")

        def do_POST(self) -> None:  # noqa: N802
            self._serve("POST")

        def _serve(self, method: str) -> None:
            status, content_type, body = app.handle(method, self.path.split("?", 1)[0])
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt: str, *args) -> None:
            return  # access logs are replaced by metrics; errors are logged by the server

    return Handler


def main() -> None:
    logging.basicConfig(level=logging.INFO, format='{"ts":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}')
    config = Config()
    app = App(config, Metrics(config.version))
    server = ThreadingHTTPServer(("0.0.0.0", config.port), make_handler(app))  # noqa: S104 (container port)

    def shutdown(signum: int, _frame) -> None:
        # Fail readiness first so the endpoint is removed from Services, then drain.
        logging.info("signal %s received: failing readiness and draining", signum)
        app.ready = False
        threading.Timer(5.0, server.shutdown).start()

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    logging.info(
        "orders-api %s listening on :%d (fault_error_rate=%s fault_latency_ms=%s)",
        config.version,
        config.port,
        config.fault_error_rate,
        config.fault_latency_ms,
    )
    server.serve_forever()
    logging.info("stopped")
    sys.exit(0)


if __name__ == "__main__":
    main()
