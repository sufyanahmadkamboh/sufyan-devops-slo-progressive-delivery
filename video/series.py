"""The script of the explainer video: "Safe releases that undo themselves".

A senior DevOps engineer explains the project to a junior colleague (two voices). The first half explains the idea
in plain words (the problem, SLIs, SLOs, error budgets, burn rates, the architecture and the code); the second half
is a real run of the lab on kind, recorded by video/record.sh:

  video/recordings/NN-name.txt          every command with its real output, exit code and duration
  video/recordings/watch/<run>/<t>.txt  `kubectl argo rollouts get rollout` every 4 seconds while releases ran
  video/shots/*.webp                    the Grafana and Argo Rollouts dashboards at chosen moments of that run

Every number on screen or in the narration is read from those files at build time; nothing is typed by hand.
"""

from __future__ import annotations

import re
from pathlib import Path

from components import arrow, box, card, checklist, code, esc, grid, label, svg, terminal

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
REC = HERE / "recordings"
SHOTS = HERE / "shots"
SENIOR, JUNIOR = "senior", "junior"
VOICES = {SENIOR: "Microsoft David Desktop", JUNIOR: "Microsoft Zira Desktop"}

CSS = """
.shot{width:100%;display:flex;flex-direction:column;align-items:center;gap:14px}
.shot img{max-width:100%;max-height:700px;border:3px solid var(--line);border-radius:18px;box-shadow:0 20px 60px rgba(0,0,0,.45)}
.shot .cap{font-size:24px;color:var(--muted)}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:34px;width:100%;align-items:start}
.big{font-size:64px;font-weight:900;text-align:center;letter-spacing:-1px}
.big .ok{color:var(--ok)}.big .bad{color:var(--bad)}.big .amb{color:var(--amber)}
.formula{display:flex;gap:26px;align-items:center;justify-content:center;font:800 58px Inter;margin:10px 0 34px}
.formula .v{background:var(--panel);border:3px solid var(--line);border-radius:20px;padding:14px 30px}
.formula .v small{display:block;font-size:22px;color:var(--muted);font-weight:600;margin-top:4px}
.formula .r{border-color:var(--amber);color:var(--amber)}
"""

# ------------------------------------------------------------------------------------------------ speech
SAY = [  # how the speech engine should say words it would otherwise mangle (captions keep the real spelling)
    (r"\bSLIs\b", "S L Is"), (r"\bSLI\b", "S L I"), (r"\bSLOs\b", "S L Os"), (r"\bSLO\b", "S L O"),
    (r"\bSRE\b", "S R E"), (r"\bp95\b", "P 95"), (r"\bkubectl\b", "kube control"), (r"\bYAML\b", "yammel"),
    (r"\bAPI\b", "A P I"), (r"\bCI\b", "C I"), (r"\bHTTP\b", "H T T P"), (r"\b5xx\b", "five hundred"),
    (r"\bNetworkPolicy\b", "network policy"), (r"\bAnalysisRun\b", "analysis run"),
    (r"\bAnalysisTemplate\b", "analysis template"), (r"\bkind\b", "kind"), (r"\bpromtool\b", "prom tool"),
    (r"\bPromQL\b", "prom Q L"), (r"\bpytest\b", "pie test"), (r"\bTrivy\b", "trivvy"), (r"\bms\b", "milliseconds"),
    (r"\bGitHub\b", "git hub"), (r"\bDevOps\b", "dev ops"), (r"\bGitOps\b", "git ops"), (r"\bUID\b", "U I D"),
    (r"\bArgo\b", "argo"), (r"\bGrafana\b", "gra fana"), (r"\bkubeconform\b", "kube conform"),
    (r"\bshellcheck\b", "shell check"), (r"\bruff\b", "ruff"), (r"\bhistogram_quantile\b", "histogram quantile"),
    (r"(\d)\.(\d+)\.(\d+)\b", r"\1 point \2 point \3"), (r"(\d+)%", r"\1 percent"), (r"(\d+) s\b", r"\1 seconds"),
    (r"→", " to "), (r"×", " times "), (r"…", "."), (r"·", ","), (r"—|–", ", "), (r"\s&\s", " and "),
]


def speech(text: str) -> str:
    t = text.replace("`", "")
    for pattern, repl in SAY:
        t = re.sub(pattern, repl, t)
    return re.sub(r"\s+", " ", t).strip()


def say(who: str, text: str, sfx: str | None = None) -> dict:
    text = re.sub(r"\s+", " ", text).strip()
    return {"say": text.replace("`", ""), "tts": speech(text), "hl": None, "zoom": 1, "sfx": sfx,
            "voice": VOICES[who], "who": who, "hold": 0}


S = lambda text, sfx=None: say(SENIOR, text, sfx)  # noqa: E731
J = lambda text, sfx=None: say(JUNIOR, text, sfx)  # noqa: E731


def scene(chapter: str | None, kicker: str, title: str, body: str, steps: list[dict]) -> dict:
    return {"chapter": chapter, "kicker": kicker, "title": title, "body": body, "steps": steps}


# ------------------------------------------------------------------------------------------------ the recordings
def rec(name: str) -> tuple[str, str, dict]:
    """(command, output, {"exit", "seconds", "at"}) of video/recordings/NN-<name>.txt."""
    f = next(p for p in sorted(REC.glob("*.txt")) if re.sub(r"^\d+-", "", p.stem) == name)
    lines = f.read_text(encoding="utf-8").rstrip("\n").split("\n")
    meta = dict(kv.split("=") for kv in lines[-1][2:].split())
    return lines[0][2:], "\n".join(lines[1:-1]), meta


def out_lines(name: str, keep=None, s: int = 0, cmd: bool = True, limit: int = 18) -> list[tuple[int, str, str]]:
    """Terminal lines of a recording; keep = regex of output lines to show (default: all)."""
    command, output, _ = rec(name)
    lines = [(s, "$ " + command, "cmd")] if cmd else []
    for ln in output.split("\n"):
        if not ln.strip() or (keep and not re.search(keep, ln)):
            continue
        lines.append((s, ln.rstrip(), classify(ln)))
    return lines[: limit]


def classify(text: str) -> str:
    if re.match(r"\[\d\d:\d\d:\d\d\]", text):        # the lab scripts' log lines: green PASS, red FAIL, else plain
        return "ok" if " PASS " in text else "bad" if " FAIL " in text else ""
    low = text.lower()
    if re.search(r"\bfail\b|aborted|degraded|error|✖|failed", low):
        return "bad"
    if re.search(r"\bpass\b|healthy|successful|✔|passed|success", low):
        return "ok"
    return ""


def watch(run: str) -> list[tuple[int, str]]:
    return [(int(p.stem), p.read_text(encoding="utf-8")) for p in sorted((REC / "watch" / run).glob("*.txt"))]


def snapshot(run: str, pattern: str, last: bool = False) -> str:
    """The first (or last) rollout snapshot of a run whose text matches pattern."""
    found = [t for _, t in watch(run) if re.search(pattern, t, re.M)]
    if not found:
        raise SystemExit(f"no snapshot of {run} matches {pattern!r}")
    return found[-1] if last else found[0]


def tree(text: str, s: int, keep: int = 22) -> list[tuple[int, str, str]]:
    rows = [ln.rstrip() for ln in text.rstrip().split("\n")]
    rows = [r for r in rows if r.strip()][:keep]
    out, in_message = [], False
    for r in rows:
        in_message = r.startswith("Message:") and "Aborted" in r or (in_message and r.startswith(" " * 17))
        out.append((s, r, "bad" if in_message else classify(r)))
    return out


def shot(s: int, name: str, caption: str) -> str:
    return (f'<div class="shot st" data-s="{s}"><img src="{(SHOTS / (name + ".webp")).as_uri()}">'
            f'<div class="cap">{esc(caption)}</div></div>')


def excerpt(path: str, start: str, end: str | None = None, lang: str = "yaml", size: int = 21, drop=()) -> str:
    """Lines of a real file from the line containing `start` up to (not including) the line containing `end`."""
    lines = (REPO / path).read_text(encoding="utf-8").split("\n")
    a = next(i for i, l in enumerate(lines) if start in l)
    b = next((i for i in range(a + 1, len(lines)) if end and end in lines[i]), len(lines)) if end else len(lines)
    body = [l for l in lines[a:b] if not any(d in l for d in drop)]
    return code(path, "\n".join(body).rstrip(), lang=lang, size=size)


# ------------------------------------------------------------------------------------------------ the script
def build(part: int = 1) -> tuple[dict, list[dict]]:
    info = {"part": 1, "slug": "safe-releases-that-undo-themselves",
            "title": "Safe releases that undo themselves",
            "subtitle": "SLO-driven canary releases with automatic rollback on Kubernetes"}
    from scenes import scenes                               # the scenes need the recordings; imported late
    return info, scenes()


def module_parts() -> list[dict]:
    return [{"part": 1}]
