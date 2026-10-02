import random

import pytest

from orders_api.server import App, Config, Metrics


def make_app(monkeypatch, **env) -> App:
    for key in ("APP_VERSION", "FAULT_ERROR_RATE", "FAULT_LATENCY_MS", "PORT"):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, str(value))
    config = Config()
    return App(config, Metrics(config.version), rng=random.Random(42))


def sample(app: App, name: str, labels: dict) -> float:
    value = app.metrics.registry.get_sample_value(name, labels)
    return value or 0.0


def test_orders_endpoint_returns_orders_and_version(monkeypatch):
    app = make_app(monkeypatch, APP_VERSION="1.2.3")
    status, ctype, body = app.handle("GET", "/api/orders")
    assert status == 200
    assert ctype == "application/json"
    assert b'"version": "1.2.3"' in body
    assert b"ORD-1001" in body


def test_requests_are_counted_by_route_and_code(monkeypatch):
    app = make_app(monkeypatch)
    for _ in range(3):
        app.handle("GET", "/api/orders")
    app.handle("GET", "/nope")
    labels = {"route": "/api/orders", "method": "GET", "code": "200"}
    assert sample(app, "http_requests_total", labels) == 3
    assert sample(app, "http_requests_total", {"route": "other", "method": "GET", "code": "404"}) == 1
    assert sample(app, "http_request_duration_seconds_count", {"route": "/api/orders"}) == 3


def test_probes_and_metrics_are_not_counted_as_traffic(monkeypatch):
    app = make_app(monkeypatch)
    assert app.handle("GET", "/healthz")[0] == 200
    assert app.handle("GET", "/readyz")[0] == 200
    status, _, body = app.handle("GET", "/metrics")
    assert status == 200 and b"http_requests_total" in body
    assert sample(app, "http_requests_total", {"route": "other", "method": "GET", "code": "200"}) == 0


def test_readiness_fails_while_draining(monkeypatch):
    app = make_app(monkeypatch)
    app.ready = False
    assert app.handle("GET", "/readyz")[0] == 503
    assert app.handle("GET", "/healthz")[0] == 200


def test_fault_error_rate_produces_roughly_that_share_of_5xx(monkeypatch):
    app = make_app(monkeypatch, FAULT_ERROR_RATE=0.25)
    codes = [app.handle("GET", "/api/orders")[0] for _ in range(2000)]
    share = codes.count(500) / len(codes)
    assert 0.22 < share < 0.28


def test_no_faults_by_default(monkeypatch):
    app = make_app(monkeypatch)
    assert all(app.handle("GET", "/api/orders")[0] == 200 for _ in range(500))


def test_fault_latency_is_recorded_in_histogram(monkeypatch):
    app = make_app(monkeypatch, FAULT_LATENCY_MS=350)
    app.handle("GET", "/api/orders")
    under_300ms = sample(app, "http_request_duration_seconds_bucket", {"route": "/api/orders", "le": "0.3"})
    assert under_300ms == 0
    assert sample(app, "http_request_duration_seconds_count", {"route": "/api/orders"}) == 1


def test_non_get_is_rejected(monkeypatch):
    app = make_app(monkeypatch)
    assert app.handle("POST", "/api/orders")[0] == 405


@pytest.mark.parametrize(
    "name,value", [("FAULT_ERROR_RATE", "1.5"), ("FAULT_ERROR_RATE", "abc"), ("FAULT_LATENCY_MS", "-1")]
)
def test_invalid_fault_configuration_is_rejected(monkeypatch, name, value):
    with pytest.raises(SystemExit):
        make_app(monkeypatch, **{name: value})
