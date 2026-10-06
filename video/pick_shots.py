"""Chooses the dashboard screenshots shown in the video, by the moments recorded in the rollout snapshots.

    python video/pick_shots.py      (after video/record.sh)

Writes video/shots/<name>.webp and video/shots/README.md (which screenshot, taken when, and why).
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
RAW = HERE / "out" / "shots"
WATCH = HERE / "recordings" / "watch"
OUT = HERE / "shots"


def first(run: str, pattern: str) -> int:
    for p in sorted((WATCH / run).glob("*.txt")):
        if re.search(pattern, p.read_text(encoding="utf-8")):
            return int(p.stem)
    raise SystemExit(f"no snapshot of {run} matches {pattern!r}")


def taken(kind: str) -> list[tuple[int, Path]]:
    shots = []
    for p in RAW.glob(f"{kind}-*.png"):
        if p.stat().st_size > 80_000:                   # an error page ("can't reach this page") is about 36 kB
            shots.append((int(p.stem.split("-")[1]), p))
    return sorted(shots)


def at(kind: str, t: int) -> tuple[int, Path]:
    """The first good screenshot taken at or after t."""
    return next(s for s in taken(kind) if s[0] >= t)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    e2e_start = first("e2e", r".")
    picks = {
        "grafana-baseline": ("grafana", e2e_start - 15, "before the first release"),
        "argo-good-60": ("argo", first("e2e", r"SetWeight:\s+60\b[\s\S]*1\.1\.0 \(canary\)") + 4, "1.1.0 at 60%"),
        "grafana-error": ("grafana", first("e2e", r'canary-error-ratio" assessed Failed') + 15, "after the abort of 1.2.0"),
        "grafana-latency": ("grafana", first("e2e", r'canary-p95-latency" assessed Failed') + 15, "after the abort of 1.3.0"),
    }
    rows = []
    for name, (kind, t, why) in picks.items():
        when, src = at(kind, t)
        Image.open(src).convert("RGB").save(OUT / f"{name}.webp", "WEBP", quality=86, method=6)
        stamp = datetime.fromtimestamp(when).strftime("%H:%M:%S")
        rows.append(f"| `{name}.webp` | {kind} | {stamp} | {why} |")
        print(name, "<-", src.name)
    (OUT / "README.md").write_text(
        "# Dashboard screenshots\n\nTaken by `video/capture.mjs` while `video/record.sh` ran the lab, and chosen by "
        "`video/pick_shots.py` from the moments in the rollout snapshots (`video/recordings/watch/`).\n\n"
        "| File | Dashboard | Taken at | Moment |\n|---|---|---|---|\n" + "\n".join(rows) + "\n",
        encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
