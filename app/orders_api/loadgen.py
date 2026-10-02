"""Steady synthetic traffic for the orders API.

Progressive delivery needs live traffic: without requests there are no SLI
samples and the canary analysis cannot judge a release. This generator sends
a constant request rate to the Service, which spreads it across stable and
canary pods in proportion to their replica counts.
"""

from __future__ import annotations

import logging
import os
import threading
import time
import urllib.error
import urllib.request


def worker(url: str, interval: float, stop: threading.Event, stats: dict, lock: threading.Lock) -> None:
    next_at = time.monotonic()
    while not stop.is_set():
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:  # noqa: S310 (fixed in-cluster URL)
                code = resp.status
        except urllib.error.HTTPError as exc:
            code = exc.code
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            code = 0
        with lock:
            stats[code] = stats.get(code, 0) + 1
        next_at += interval
        stop.wait(max(0.0, next_at - time.monotonic()))


def main() -> None:
    logging.basicConfig(level=logging.INFO, format='{"ts":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}')
    url = os.environ.get("TARGET_URL", "http://orders-api/api/orders")
    rps = float(os.environ.get("REQUESTS_PER_SECOND", "20"))
    concurrency = max(1, int(os.environ.get("CONCURRENCY", "4")))
    interval = concurrency / rps
    stop, lock, stats = threading.Event(), threading.Lock(), {}
    for _ in range(concurrency):
        threading.Thread(target=worker, args=(url, interval, stop, stats, lock), daemon=True).start()
    logging.info("sending %.1f req/s to %s with %d workers", rps, url, concurrency)
    while True:
        time.sleep(30)
        with lock:
            snapshot = dict(stats)
            stats.clear()
        logging.info("last 30s responses by status: %s", snapshot)


if __name__ == "__main__":
    main()
