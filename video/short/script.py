"""The 1-minute vertical short: one entry per voiceover line.

`say` is the caption (real spelling and numbers); the spoken text is in voiceover/lines.json.
`body` is the visual for that line (1080 wide); elements with data-at="<seconds>" pop in that long after the line
starts, data-count="<n>" counts up from 0. `sfx` plays at the start of the line.
Every number is from the recorded run (video/recordings/) and docs/test-results.md.
Logos (logos/): Kubernetes, Prometheus and Argo from the CNCF artwork repository; Grafana from the Grafana repository.
"""

NAME = "safe-releases-short"
HEADER = {"logo": "kubernetes-icon-color.svg", "topic": "Safe releases on Kubernetes", "sub": "canary + SLO + auto-rollback"}
SHOT = "../shots"


def crop(name: str, x: int, y: int, w: int, h: int, box: int = 1000) -> str:
    """A 1920x1080 screenshot cropped to one panel (x, y, w, h), shown <box> px wide."""
    k = box / w
    return (f'<div class="shot" data-at="0" style="width:{box}px;height:{round(h * k)}px;'
            f"background-image:url('{SHOT}/{name}');background-size:{round(1920 * k)}px auto;"
            f'background-position:{-round(x * k)}px {-round(y * k)}px"></div>')


def logo(name: str, text: str, at: float = 0, size: int = 92) -> str:
    """A tool logo with its name, e.g. logo("prometheus", "Prometheus")."""
    return (f'<div class="tool" data-at="{at}"><img src="logos/{name}-icon{"" if name == "grafana" else "-color"}.svg" '
            f'style="height:{size}px">{text}</div>')


# The DevOps infinity loop: Dev (blue) on the left, Ops (green) on the right, security in the middle.
LOOP = """<svg class="loop" viewBox="0 0 1000 520" width="{w}"><defs><linearGradient id="lg{w}" x1="0" x2="1">
<stop offset="0" stop-color="#3b8cff"/><stop offset=".5" stop-color="#9b6bff"/><stop offset="1" stop-color="#38e08a"/></linearGradient></defs>
<path d="M500 260 C 420 120, 120 90, 120 260 C 120 430, 420 400, 500 260 C 580 120, 880 90, 880 260 C 880 430, 580 400, 500 260 Z"
 fill="none" stroke="url(#lg{w})" stroke-width="46" stroke-linejoin="round"/>
<g font-family="Inter,Segoe UI,sans-serif" font-weight="900" font-size="34" fill="#f4f8ff" text-anchor="middle">
<text x="300" y="150">PLAN</text><text x="190" y="272">CODE</text><text x="300" y="392">BUILD</text><text x="378" y="272">TEST</text>
<text x="640" y="272">RELEASE</text><text x="700" y="150">DEPLOY</text><text x="822" y="272">OPERATE</text><text x="700" y="392">MONITOR</text></g>
<text x="300" y="70" font-size="64" font-weight="900" fill="#3b8cff" text-anchor="middle" font-family="Inter,Segoe UI">DEV</text>
<text x="700" y="70" font-size="64" font-weight="900" fill="#38e08a" text-anchor="middle" font-family="Inter,Segoe UI">OPS</text>
<circle cx="500" cy="260" r="50" fill="#070d17" stroke="#ffc23d" stroke-width="8"/>
<text x="500" y="279" font-size="50" text-anchor="middle">🛡️</text>
<text x="500" y="490" font-size="44" font-weight="900" fill="#ffc23d" text-anchor="middle" font-family="Inter,Segoe UI">+ SEC</text></svg>"""

LINES = [
    {"id": "l01", "say": "This release was broken. It rolled itself back in 42 seconds.", "sfx": "error", "body": """
<div class="stamp bad" data-at="-1">BROKEN RELEASE</div>
<div class="label dim" data-at="-1"><img class="inl" src="logos/kubernetes-icon-color.svg"> IN PRODUCTION</div>
<div class="big ok" data-at="1.3"><span data-count="42">42</span><small>s</small></div>
<div class="label ok" data-at="1.6">ROLLED BACK AUTOMATICALLY</div>"""},
    {"id": "l02", "say": "Nobody touched it.", "sfx": "pop", "body": """
<div class="emoji" data-at="0">🙅‍♂️</div><div class="label" data-at="0.2">0 HUMANS · 0 BUTTONS</div>"""},
    {"id": "l03", "say": "Here's the problem. A normal Kubernetes rollout sends every single user to the new version within minutes.",
     "sfx": "scene", "body": logo("kubernetes", "Kubernetes rolling update", 0) + """
<div class="pods">""" + "".join(f'<div class="pod flip" data-at="{1.2 + i * 0.55}"><b>v1</b><i>v2</i></div>' for i in range(5)) + """</div>
<div class="users" data-at="3.4">👥👥👥👥👥 → <b class="amber">v2</b></div>"""},
    {"id": "l04", "say": "If that version is broken, everyone gets the bug.", "sfx": "error", "body": """
<div class="pods">""" + "".join('<div class="pod red" data-at="0"><i>v2</i></div>' for _ in range(5)) + """</div>
<div class="label bad" data-at="0.6">100% OF USERS</div><div class="emoji" data-at="1.0">💥😱</div>"""},
    {"id": "l05", "say": "So I built a release that tests itself on real traffic.", "sfx": "chapter", "body": f"""
<div data-at="0">{LOOP.format(w=980)}</div>
<div class="title" data-at="0.8">A release that <span class="ok">tests itself</span></div>"""},
    {"id": "l06", "say": "The new version gets one pod in five. 20 percent.", "sfx": "scene", "body": logo("argo", "Argo Rollouts canary", 0) + """
<div class="pods"><div class="pod canary" data-at="0.3"><i>v2</i></div>""" + "".join(
        f'<div class="pod" data-at="{0.5 + i * 0.12}"><b>v1</b></div>' for i in range(4)) + """</div>
<div class="big amber" data-at="1.8"><span data-count="20">20</span><small>%</small></div>"""},
    {"id": "l07", "say": "Every 15 seconds, Prometheus checks its errors and its latency against an SLO.", "sfx": "scene",
     "body": logo("prometheus", "Prometheus · every 15 s", 0) + """
<div class="checks"><div class="check" data-at="1.6">🔥 errors <span>≤ 0.07</span></div>
<div class="check" data-at="2.4">🐢 latency p95 <span>≤ 300 ms</span></div></div>
<div class="label dim" data-at="3.4">SLO = THE AGREED LIMIT</div>"""},
    {"id": "l08", "say": "Now watch. Version 1.2 fails a quarter of its requests.", "sfx": "chapter",
     "body": logo("grafana", "Grafana · real run", 0, 72) + crop("grafana-error.webp", 560, 600, 395, 285) + """
<div class="tag bad" data-at="1.0">v1.2.0 · 25% ERRORS</div>"""},
    {"id": "l09", "say": "Error ratio: 0.3. The limit: 0.07.", "sfx": "pop", "body": """
<div class="meter"><div class="limit" data-at="1.3"><span>limit 0.072</span></div>
<div class="fill" data-at="0.1"></div></div>
<div class="big bad" data-at="0.4">0.305</div><div class="label bad" data-at="1.6">4× OVER THE LIMIT</div>"""},
    {"id": "l10", "say": "Two strikes. Rollout aborted. Every user back on the good version.", "sfx": "error", "body": """
<div class="strikes"><span data-at="0">❌</span><span data-at="0.4">❌</span></div>
<div class="stamp bad" data-at="1.0">ABORTED</div>
<div class="pods">""" + "".join(f'<div class="pod" data-at="{2.2 + i * 0.1}"><b>v1</b></div>' for i in range(5)) + """</div>"""},
    {"id": "l11", "say": "42 seconds. Zero humans.", "sfx": "success", "body": """
<div class="big ok" data-at="0"><span data-count="42">42</span><small>s</small></div>
<div class="label" data-at="1.0">FROM RELEASE TO ROLLBACK</div><div class="label ok" data-at="1.3">0 HUMANS</div>"""},
    {"id": "l12", "say": "Slow instead of broken? 600 ms of extra latency. Caught in 43 seconds.", "sfx": "scene",
     "body": logo("grafana", "Grafana · real run", 0, 72) + crop("grafana-latency.webp", 1490, 600, 410, 285) + """
<div class="tag amber" data-at="1.4">+600 ms LATENCY</div><div class="tag ok low" data-at="3.0">CAUGHT IN 43 s</div>"""},
    {"id": "l13", "say": "Prometheus goes down in the middle of a release? No data. No promotion.", "sfx": "error", "body": """
<div class="down" data-at="0"><img src="logos/prometheus-icon-color.svg"><span>🔌</span></div><div class="label bad" data-at="0.4">PROMETHEUS DOWN</div>
<div class="title" data-at="2.2">No data =<br><span class="bad">no promotion</span></div>"""},
    {"id": "l14", "say": "And a healthy release? Promoted to 100 percent, while nobody was watching.", "sfx": "success",
     "body": logo("argo", "Argo Rollouts · real run", 0, 72) + crop("argo-good-60.webp", 395, 160, 720, 645, 900) + """
<div class="tag ok" data-at="1.4">✅ PROMOTED TO 100%</div>"""},
    {"id": "l16", "say": "The full project is free. Follow, and I'll show you how to build it.", "sfx": "outro", "body": f"""
<div data-at="0">{LOOP.format(w=760)}</div>
<div class="logos" data-at="0.4"><img src="logos/kubernetes-icon-color.svg"><img src="logos/argo-icon-color.svg">
<img src="logos/prometheus-icon-color.svg"><img src="logos/grafana-icon.svg"></div>
<div class="title sm" data-at="0.8">Full DevSecOps project <span class="ok">FREE</span></div>
<div class="follow" data-at="1.8">FOLLOW ➜</div>"""},
]
