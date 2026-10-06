"""The second half of the video: the real run recorded by video/record.sh. Every value comes from the recordings."""

from __future__ import annotations

import re
from datetime import datetime

from components import card, checklist, grid, terminal
from series import J, S, out_lines, rec, scene, shot, snapshot, tree

TERM = "~/sufyan-devops-slo-progressive-delivery"


# ------------------------------------------------------------------------------------------------ facts from the run
def e2e_time(pattern: str) -> datetime:
    _, output, _ = rec("e2e")
    m = re.search(r"^\[(\d\d:\d\d:\d\d)\] " + pattern, output, re.M)
    if not m:
        raise SystemExit(f"e2e recording has no line matching {pattern!r}")
    return datetime.strptime(m.group(1), "%H:%M:%S")


def seconds(a: str, b: str) -> int:
    return int((e2e_time(b) - e2e_time(a)).total_seconds())


def measurements(version_pattern: str) -> dict[str, list[float]]:
    """{metric: [values]} of the analysis run named in the e2e PASS line for that release."""
    _, output, _ = rec("e2e")
    run = re.search(version_pattern + r".*\(analysis run (\S+)\)", output).group(1)
    _, text, _ = rec(f"measurements-{run}")
    found = {}
    for name, values in re.findall(r"^(canary-[\w-]+): \w+ (.*)$", text, re.M):
        found[name] = [float(v) for v in re.findall(r"\[([\d.e-]+)\]", values)]
    return found


def mins(sec: int) -> str:
    return f"{sec // 60} min {sec % 60} s" if sec >= 60 else f"{sec} seconds"


def wrap_message(text: str) -> str:
    """The rollout's one-line abort message, wrapped so it stays readable on screen."""
    out = []
    for line in text.split("\n"):
        if line.startswith("Message:") and len(line) > 100:
            cur = ""
            for w in line.split(" "):
                if len(cur) + len(w) > 96:
                    out.append(cur.rstrip())
                    cur = " " * 17
                cur += w + " "
            out.append(cur.rstrip())
        else:
            out.append(line)
    return "\n".join(out)


def header(text: str, rows: int = 9) -> str:
    """The summary block of `kubectl argo rollouts get rollout` (Name … Images), without the replica counts."""
    lines = wrap_message(text).split("\n")
    end = next((i for i, l in enumerate(lines) if l.startswith("Replicas:")), len(lines))
    return "\n".join(lines[:end][:rows + 3])


def compact(text: str) -> str:
    """Status, weight and images of a rollout snapshot, then its tree of ReplicaSets, pods and analysis runs."""
    lines = text.split("\n")
    keep = [l for i, l in enumerate(lines) if l.startswith(("Status:", "  SetWeight:", "Images:"))
            or (i and lines[i - 1].startswith("Images:"))]
    return "\n".join(keep) + "\n" + pods_tree(text)


def pods_tree(text: str) -> str:
    lines = text.split("\n")
    start = next(i for i, l in enumerate(lines) if l.startswith("NAME"))
    return "\n".join(lines[start:])


# ------------------------------------------------------------------------------------------------ scenes
def build_lab() -> list[dict]:
    lines = out_lines("up", keep=r"^\[\d", s=1)
    lines += out_lines("nodes", s=3)
    return [scene("A real run", "On a laptop, for free", "One command builds the whole lab", terminal(lines, TERM), [
        J("Can I see it working for real, not just on slides?"),
        S("Everything you will see now is a real run, recorded on my laptop. One script, scripts/up.sh, builds the "
          "whole lab: a local Kubernetes cluster with kind, Argo Rollouts, Prometheus with the SLO rules, Grafana "
          "with the dashboard, and version 1.0.0 of the orders API with its load generator."),
        S(f"It took {mins(int(rec('up')[2]['seconds']))}. No cloud account, nothing to pay."),
        S("The cluster has one control plane and two worker nodes, so the stable and canary pods spread across "
          "machines, like in a real cluster."),
    ])]


def version_one() -> list[dict]:
    _, text, _ = rec("rollout-v1")
    return [scene(None, "Before the first release", "Version 1.0.0 serves all traffic",
                  terminal(tree(compact(text), 1, keep=26), "kubectl argo rollouts get rollout orders-api -n delivery"), [
        J("What am I looking at?"),
        S("This is the Argo Rollouts view of the service. Status healthy, step eight of eight, weight one hundred: "
          "version 1.0.0 is the stable version, and it serves everything."),
        S("Below it, the tree: one ReplicaSet, revision one, with five pods. Remember this shape. During a release, "
          "a second ReplicaSet appears next to it."),
    ]), scene(None, "The dashboard", "Grafana: everything green before we release",
              shot(1, "grafana-baseline", "Grafana · orders-api: SLOs & progressive delivery (recorded during the run)"), [
        J("And the dashboard?"),
        S("At the top: availability one hundred percent, the whole error budget left, burn rate zero, latency inside "
          "the target, and no alert firing."),
        S("Below: the burn rate over several windows, and then the error ratio and the p95 latency split by "
          "revision. That split is what lets us compare a canary with the stable version, side by side."),
    ])]


def good_release() -> list[dict]:
    canary20 = snapshot("e2e", r"Paused[\s\S]*SetWeight:\s+20\b[\s\S]*1\.1\.0 \(canary\)[\s\S]*AnalysisRun")
    m = measurements(r"PASS 1\.1\.0 promoted")
    err, lat = m["canary-error-ratio"], m["canary-p95-latency"]
    took = seconds(r"releasing 1\.1\.0", r"PASS 1\.1\.0 promoted")
    release = [(1, "$ scripts/e2e.sh", "cmd")]
    pass_line = [(1, ln, cls) for _, ln, cls in out_lines("e2e", keep=r"PASS 1\.1\.0", cmd=False)]
    result = [(2, f"canary-error-ratio   {len(err)} measurements, highest {max(err):.3f}     (limit 0.072)", "ok"),
              (2, f"canary-p95-latency   {len(lat)} measurements, highest {max(lat) * 1000:.1f} ms  (limit 300 ms)", "ok")]
    return [scene("Release 1: a healthy version", "The proof, part one", "A good release goes out on its own",
                  terminal(release + tree(compact(canary20), 2, keep=20), TERM), [
        J("Now release a new version. What happens?"),
        S("The test script, e2e.sh, releases version 1.1.0, a healthy version. It uses shorter pauses than "
          "production, thirty seconds instead of sixty, so the whole proof fits in a few minutes. The decision rules "
          "are exactly the same."),
        S("Look at the tree now. Revision two appeared, with one canary pod, next to the four stable pods of "
          "revision one. Weight twenty: one pod in five. And there is an AnalysisRun, the background check, already "
          "running."),
    ]), scene(None, "Halfway", "The Argo Rollouts dashboard at 60%",
              shot(1, "argo-good-60", "Argo Rollouts dashboard · version 1.1.0 at 60% (recorded during the run)"), [
        S("Argo Rollouts also has a dashboard. Here the release is at sixty percent: the steps on the left, three "
          "canary pods with version 1.1.0, two stable pods with 1.0.0, and the analysis run doing its work."),
        J("So nobody pressed a button here?"),
        S("Nobody. Every step waits, the analysis keeps measuring, and the rollout moves on by itself."),
    ]), scene(None, "The result", "Promoted after every check passed",
              terminal(pass_line + result, "the end of scenario 1, and the analysis run's measurements"), [
        S(f"After {mins(took)}, version 1.1.0 was promoted to a hundred percent.", sfx="success"),
        S(f"These are the real measurements. {len(err)} error-ratio checks, the highest {max(err):.3f}. {len(lat)} "
          f"latency checks, with a p95 of about {round(max(lat) * 1000)} milliseconds, far under the 300 millisecond "
          "limit."),
        S("A boring release, exactly as it should be. And nobody had to watch it."),
    ])]


def error_release() -> list[dict]:
    abort = snapshot("e2e", r'canary-error-ratio" assessed Failed')
    m = measurements(r"PASS 1\.2\.0 aborted")["canary-error-ratio"]
    took = seconds(r"releasing 1\.2\.0", r"PASS 1\.2\.0 aborted")
    release = [(1, ln, cls) for _, ln, cls in out_lines("e2e", keep=r"^\[\d.*(scenario 2|releasing 1\.2\.0)", cmd=False)]
    passes = [(1, ln, cls) for _, ln, cls in out_lines("e2e", keep=r"PASS (1\.2\.0|all traffic)", cmd=False)][:2]
    values = [(1, f"canary-error-ratio measured: {', '.join(f'{v:.3f}' for v in m)}   (limit 0.072)", "bad")]
    return [scene("Release 2: 25% errors", "The proof, part two", "A bad release stops itself",
                  terminal(release + tree(header(abort, rows=12), 2, keep=16), TERM), [
        J("And a bad release?"),
        S("Version 1.2.0 is broken on purpose. The fault injection makes it fail twenty-five percent of requests: "
          "the kind of bug that slips through tests because it only shows up with real traffic."),
        S("And here is the rollout a few seconds later. Status: degraded. Rollout aborted. The message even says "
          "why: the metric canary-error-ratio failed two times, and only one failure is allowed. The weight is back "
          "to zero.", sfx="error"),
    ]), scene(None, "What the dashboards saw", "The canary's errors, and nobody else's",
              shot(1, "grafana-error", "Grafana · just after the abort of 1.2.0 (recorded during the run)"), [
        S("On Grafana you can see the spike, and you can see whose spike it is: the error ratio of the canary "
          "revision only. The stable revision stays at zero."),
        S("That is why the analysis looks at the canary's own pods. Mixed into the average, one pod's errors would "
          "look small. Measured alone, they are impossible to miss."),
    ]), scene(None, "The numbers", f"Stopped {took} seconds after the release started",
              terminal(passes + values, "scenario 2 · from the recording"), [
        S(f"The two measurements were {m[0]:.3f} and {m[1]:.3f}: about the twenty-five percent we injected. "
          "The limit is 0.072. Two failures, so the rollout was aborted."),
        S(f"From release to abort: {took} seconds. Then the test sent forty requests through the Service and "
          "checked that every answer came from version 1.1.0. Users were back on the good version.", sfx="success"),
        J("So only one pod in five ever served the bad version, and for less than a minute."),
        S("Exactly. With a rolling update, it would have reached every user."),
    ])]


def latency_release() -> list[dict]:
    abort = snapshot("e2e", r'canary-p95-latency" assessed Failed')
    m = measurements(r"PASS 1\.3\.0 aborted")["canary-p95-latency"]
    took = seconds(r"releasing 1\.3\.0", r"PASS 1\.3\.0 aborted")
    release = [(1, ln, cls) for _, ln, cls in out_lines("e2e", keep=r"^\[\d.*(scenario 3|releasing 1\.3\.0)", cmd=False)]
    values = [(3, f"canary-p95-latency measured: {', '.join(f'{v:.3f} s' for v in m)}   (limit 0.300 s)", "bad")]
    values += [(4, ln, cls) for _, ln, cls in out_lines("e2e", keep=r"PASS (1\.3\.0|all end)", cmd=False)]
    return [scene("Release 3: 600 ms slower", "The proof, part three", "A slow release is stopped too",
                  terminal(release + tree(header(abort, rows=12), 2, keep=12) + values, TERM), [
        J("What if the new version does not fail, but is just slow?"),
        S("That is release three. Version 1.3.0 answers correctly, but adds 600 milliseconds to every request. "
          "No errors at all, so an error check alone would happily promote it."),
        S(f"The latency check caught it: canary-p95-latency failed twice, and the rollout was aborted "
          f"{took} seconds after the release.", sfx="error"),
        S(f"The measured p95 was {m[0]:.3f} seconds. Why not exactly 0.6? Because the histogram's buckets jump from "
          "half a second to one second, and Prometheus estimates inside the bucket. The estimate is rough, but the "
          "breach is obvious: far above 300 milliseconds."),
        S("And the last line: all end-to-end scenarios passed. One good release promoted, two bad releases rolled "
          "back by themselves.", sfx="success"),
    ]), scene(None, "Latency, side by side", "The slow canary on the dashboard",
              shot(1, "grafana-latency", "Grafana · just after the abort of 1.3.0 (recorded during the run)"), [
        S("Here it is on Grafana: the p95 of the canary revision jumps to about a second, while the stable revision "
          "stays at about twenty milliseconds."),
    ])]


def chaos() -> list[dict]:
    lines = out_lines("chaos", keep=r"^\[\d|phase=", s=1, limit=14)
    return [scene("When monitoring breaks", "A failure test", "No measurements, no promotion", terminal(lines, TERM), [
        J("What if Prometheus itself goes down in the middle of a release? Does the release just continue blind?"),
        S("That is exactly what this test checks. It releases version 1.4.0, which is perfectly healthy, and while "
          "the canary is running it scales Prometheus down to zero."),
        S("The analysis can no longer measure anything. After five errors in a row, the analysis run ends in Error, "
          "and the rollout is aborted.", sfx="error"),
        S("Even though 1.4.0 was actually fine! That is on purpose: a release that cannot be verified is not "
          "promoted. Failing safe means: when in doubt, keep the version we know works."),
        S("Then the script brings Prometheus back and restores the stable version.", sfx="success"),
    ])]


def security() -> list[dict]:
    lines = out_lines("netpol", keep=r"PASS|FAIL", s=1)
    body = terminal(lines, TERM) + '<div style="height:26px"></div>' + grid([
        card(2, "👤", "Non-root, locked down", "UID 10001, read-only file system, all capabilities dropped, seccomp", "blue"),
        card(3, "🔑", "No API token", "the pods get no service-account token; Grafana's password is generated at deploy", "amber"),
        card(4, "🔎", "Scanned image", "Trivy fails the build on fixable HIGH or CRITICAL vulnerabilities", "violet"),
    ], cols=3)
    return [scene("Security", "Safe in more than one way", "Locked down, and tested", body, [
        J("Is the service itself secure?"),
        S("A NetworkPolicy lets traffic in only from the same namespace and from monitoring. The security test proves "
          "it: a pod in the same namespace reaches the API, a pod in another namespace is blocked."),
        S("The containers run as a non-root user, with a read-only file system, no Linux capabilities, and the "
          "default seccomp profile."),
        S("The pods get no Kubernetes API token, because they do not need one. And the Grafana admin password is "
          "generated when the lab is deployed, so nothing secret lives in the repository."),
        S("In CI, the image is scanned with Trivy, and the build fails on any fixable high or critical "
          "vulnerability."),
    ])]


def tests() -> list[dict]:
    lines = out_lines("unit-tests", keep=r"passed|failed", s=1)
    lines += out_lines("promtool-check", keep=r"SUCCESS|FAILED|rules found", s=2)
    lines += out_lines("promtool-test", keep=r"SUCCESS|FAILED", s=3)
    for i, (s, t, c) in enumerate(lines):           # the docker commands are long: show them shortened
        if "venv/Scripts/python" in t:
            lines[i] = (s, "$ cd app && python -m pytest -q", c)
        if t.startswith("$ MSYS_NO_PATHCONV=1 docker run"):
            lines[i] = (s, "$ promtool " + t.split("--entrypoint promtool prom/prometheus:v3.15.0 ")[1], c)
    body = terminal(lines, TERM) + '<div style="height:26px"></div>' + grid([
        card(4, "🧪", "Static stage", "pytest, ruff, shellcheck, promtool, helm lint, kubeconform", "blue"),
        card(4, "📦", "Image stage", "build the image, Trivy scan", "violet"),
        card(5, "☸️", "End-to-end stage", "a fresh kind cluster: the same three releases, the outage and the NetworkPolicy test", "ok"),
    ], cols=3)
    return [scene("Tests and CI", "Proved on every change", "The safety net is tested too", body, [
        J("How do you know the safety net itself still works next month?"),
        S("Because it is tested on every change. The service has unit tests."),
        S("The SLO rules are checked with promtool,"),
        S("and the alerts are unit-tested: promtool feeds them made-up metrics and checks that each alert fires "
          "exactly when it should, and stays quiet when it should."),
        S("GitHub Actions runs three stages: static checks, then the image build and scan,"),
        S("and then the full end-to-end run on a fresh kind cluster: the good release, the two bad releases, the "
          "monitoring outage and the NetworkPolicy check. If the safety net breaks, the pipeline goes red."),
    ])]


def recap() -> list[dict]:
    body = checklist([
        (1, "Measure what users feel", "SLIs: the error ratio and the p95 latency, per revision"),
        (2, "Agree the limits in advance", "SLOs and a burn rate, written in a values file and reviewed like code"),
        (3, "Release to a few users first", "a canary at 20%, then 40, 60, 80 and 100"),
        (4, "Let the numbers decide", "pass: promote · fail: abort and roll back · no data: abort too"),
        (5, "Test the safety net", "a good release, two bad ones and an outage, on every change"),
    ])
    return [scene("Recap", "What to remember", "Safe releases that undo themselves", body, [
        J("Let me try to sum it up. First, measure what users feel: errors and latency, separately for the new version."),
        J("Second, agree on the limits before the release, not during the incident."),
        J("Third, give the new version only a part of the traffic first."),
        J("Fourth, let the numbers decide. Pass, promote. Fail, roll back. And no data counts as a fail."),
        S("And fifth: test the safety net itself, with real bad releases, on every change. That is the whole project. "
          "The repository has a beginner study guide with a PDF, if you want to learn every tool from zero, and you "
          "can run all of this on your own laptop with two commands."),
    ])]


def demo_part() -> list[dict]:
    return (build_lab() + version_one() + good_release() + error_release() + latency_release() + chaos() + security()
            + tests() + recap())
