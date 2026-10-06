"""The scenes of the explainer video, in order. Helpers and the recordings: series.py."""

from __future__ import annotations

from components import arrow, box, card, checklist, code, grid, label, svg, terminal
from series import REC, J, S, excerpt, scene


# ================================================================================================ part 1: the idea
def problem() -> list[dict]:
    body = '<div class="cols">' + grid([
        card(1, "🚀", "Rolling update", "the new version replaces the old pods one by one: a bug reaches 100% of users in minutes", "bad"),
        card(2, "📞", "Found by", "an alert, or a customer complaint", "bad"),
        card(3, "😰", "Rollback", "a judgment call, made under pressure, maybe at 3 a.m.", "bad"),
    ], cols=1, gap=22) + grid([
        card(5, "🐤", "Canary release", "the new version gets 20% of traffic first, then 40, 60, 80 and 100", "ok"),
        card(6, "📏", "Checked against the SLOs", "every 15 to 30 seconds: is it failing more, or slower, than allowed?", "ok"),
        card(7, "↩️", "Automatic decision", "healthy: promoted. Too many errors or too slow: rolled back by itself", "ok"),
    ], cols=1, gap=22) + '</div>'
    return [scene("The problem", "Why this project exists", "A green pipeline, and a broken release", body, [
        J("Last week a release broke the checkout for everyone, and the pipeline was green the whole time. "
          "How does that even happen?"),
        S("Because the pipeline only asked one question: did the deployment succeed? With a normal rolling update, "
          "the new version replaces the old pods one by one, and within minutes it serves every single user."),
        S("And then you find out the hard way: from an alert, or from a customer."),
        S("Then a person has to decide, under pressure, whether it is bad enough to roll back. "
          "Usually while the error count keeps climbing."),
        J("So what does this project do differently?"),
        S("Every release goes out as a canary. The new version first gets only twenty percent of the traffic."),
        S("While the traffic grows, the new version is measured against agreed targets, called SLOs, "
          "every fifteen to thirty seconds."),
        S("If it stays healthy, it is promoted to a hundred percent with nobody in the loop. If it fails too often, "
          "or gets too slow, it is rolled back automatically, and the old version keeps serving users."),
    ])]


def analogy() -> list[dict]:
    steps_x = [150, 470, 790, 1110, 1430]
    inner = ""
    for k, (x, w) in enumerate(zip(steps_x, [20, 40, 60, 80, 100])):
        s = 1 + k if k < 4 else 5
        inner += box(s, x - 120, 120, 240, 150, "🍲" if k < 4 else "🎉", f"{w}%",
                     ["of the tables", "taste test ✔" if k < 4 else "everyone"], "ok" if k == 4 else "blue")
        if k:
            inner += arrow(s, steps_x[k - 1] + 125, 195, x - 130, 195, "ok")
    inner += box(6, 300, 430, 640, 170, "🤢", "Tables complain", ["stop serving the new recipe", "everyone gets the old one again"], "bad")
    inner += arrow(6, 470, 275, 560, 425, "bad") + label(6, 540, 350, "too many complaints", tone="bad")
    inner += box(7, 1040, 430, 640, 170, "📋", "Agreed in advance", ["how many complaints are too many?", "that number is the SLO"], "amber")
    return [scene(None, "The idea in one picture", "A new recipe is served to a few tables first", svg(inner, 1720, 640), [
        J("Can you explain it without the jargon?"),
        S("Think of a restaurant with a new recipe. You do not serve it to the whole room. You serve it to one table "
          "in five, and you watch."),
        S("If those tables are happy, you serve it to two tables in five,"),
        S("then three,"),
        S("then four,"),
        S("and finally to everyone."),
        S("If the tables complain, you stop at once, and everybody gets the old recipe again. Only a few tables ever "
          "tasted the bad one.", sfx="error"),
        S("The important part: how many complaints are too many is agreed before the dinner starts. Nobody argues "
          "about it in the middle of the rush. In our world, that agreed number is the SLO."),
    ])]


def sli_slo() -> list[dict]:
    body = grid([
        card(1, "📐", "SLI · what we measure", "share of requests that fail (HTTP 5xx), and how long requests take (p95 latency)", "sky"),
        card(2, "🎯", "SLO · the target", "99.5% of requests succeed · 95% of requests are faster than 300 ms", "blue"),
        card(3, "💰", "Error budget · what may fail", "100% − 99.5% = 0.5% of requests are allowed to fail", "amber"),
        card(4, "🔥", "Burn rate · how fast we spend it", "1 = exactly on budget for 30 days · 14.4 = 2% of the month's budget gone in 1 hour", "bad"),
    ], cols=2)
    return [scene("SLI, SLO, error budget", "Four words, in plain language", "How we say \"healthy\" with numbers", body, [
        J("I hear SLO, SLI and error budget all the time. What do they actually mean?"),
        S("An SLI, a service level indicator, is simply something we measure. Here there are two: the share of "
          "requests that fail with a server error, and how long requests take. For time we use the p95: ninety-five "
          "percent of requests are faster than this value."),
        S("The SLO, the service level objective, is the target for that measurement. For this orders API: 99.5% of "
          "requests must succeed, and the p95 must stay under 300 ms."),
        S("The error budget is what is left over. If 99.5% must succeed, then 0.5% may fail. That is not a failure "
          "of the team: it is a budget the team is allowed to spend, on releases, experiments and bad luck."),
        S("And the burn rate says how fast you are spending it. A burn rate of one spends the budget exactly over "
          "thirty days. A burn rate of 14.4 spends two percent of the whole month's budget in a single hour. "
          "That is fast enough to wake someone up."),
    ])]


def threshold() -> list[dict]:
    body = ('<div class="formula st" data-s="1"><div class="v">0.005<small>error budget (0.5%)</small></div>×'
            '<div class="v">14.4<small>fastest allowed burn</small></div>=<div class="v r">0.072<small>max canary error ratio</small></div></div>'
            + grid([
                card(2, "✅", "Canary at 0% to 7.2% errors", "within the limit: the release continues", "ok"),
                card(3, "⛔", "Canary above 7.2% errors", "it would page the on-call engineer: the release is stopped", "bad"),
                card(4, "🤝", "One definition of healthy", "the release gate and the on-call alert use the same 14.4 burn rate", "blue"),
            ], cols=3))
    return [scene(None, "Where the limit comes from", "Why the canary may fail at most 7.2% of requests", body, [
        J("So how does the canary check turn the SLO into a yes or no?"),
        S("With one multiplication. The error budget is 0.005. The fastest burn rate we accept is 14.4. "
          "0.005 times 14.4 is 0.072. So the canary may fail at most 7.2% of its requests."),
        S("Below that, the release carries on."),
        S("Above it, the canary is burning budget as fast as an incident would, and the release is stopped."),
        S("And notice where 14.4 comes from: it is the same threshold as the alert that pages the on-call engineer. "
          "A release that would page someone is never promoted. The deployment and the alerting share one "
          "definition of healthy."),
    ])]


def architecture() -> list[dict]:
    inner = (
        box(1, 20, 20, 400, 150, "⚙️", "GitHub Actions", ["tests, lint, scan", "helm upgrade: new version"], "sky")
        + arrow(2, 425, 95, 585, 95, label="new tag")
        + box(2, 590, 20, 560, 150, "🐙", "Argo Rollouts", ["replaces the Deployment", "20 → 40 → 60 → 80 → 100%"], "blue")
        + box(3, 590, 250, 560, 190, "📦", "orders-api pods", ["stable pods (old version)", "canary pods (new version)", "/metrics with a revision label"], "ok")
        + arrow(3, 870, 175, 870, 245)
        + box(4, 20, 270, 400, 150, "🚗", "load generator", ["20 requests per second", "like real users"], "amber")
        + arrow(4, 425, 345, 585, 345, "sky")
        + box(5, 1290, 250, 410, 190, "🔥", "Prometheus", ["scrapes every pod", "SLI rules, burn-rate alerts", "answers the analysis"], "bad")
        + arrow(5, 1155, 345, 1285, 345, label="scrape")
        + arrow(6, 1400, 245, 1155, 120, "sky", dash=True) + label(6, 1300, 150, "canary SLIs every 15–30 s")
        + box(7, 1290, 520, 410, 150, "📊", "Grafana", ["SLO and error-budget", "canary vs stable"], "violet")
        + arrow(7, 1495, 445, 1495, 515)
        + box(8, 590, 520, 560, 150, "⚖️", "The decision", ["pass: promote to 100%", "fail: abort, stable gets 100%"], "amber")
        + arrow(8, 870, 445, 870, 515, "ok")
    )
    return [scene("Architecture", "How the pieces fit", "Six parts, one safety net", svg(inner, 1720, 690), [
        J("What is actually running? Draw me the picture."),
        S("It starts in GitHub Actions. After the tests, a release is just a Helm upgrade with a new image tag."),
        S("Argo Rollouts receives it. It replaces the normal Kubernetes Deployment with a Rollout, which knows how "
          "to move traffic in steps: twenty, forty, sixty, eighty, a hundred percent."),
        S("During a release there are two kinds of pods: the stable pods with the old version, and the canary pods "
          "with the new one. Every pod exposes metrics, labelled with its revision."),
        S("In a lab there are no real users, so a small load generator sends twenty requests per second. "
          "Without traffic there is nothing to measure."),
        S("Prometheus scrapes every pod, computes the SLIs, and evaluates the burn-rate alerts."),
        S("Every fifteen to thirty seconds, Argo Rollouts asks Prometheus about the canary pods only."),
        S("Grafana shows all of it on one dashboard: the SLOs, the error budget, and canary against stable."),
        S("And the answer decides the release: pass means promote, fail means abort, and all traffic goes back "
          "to the stable pods."),
    ])]


def rollout_code() -> list[dict]:
    left = excerpt("charts/orders-api/values.yaml", "# Service level objectives", "resources:", size=19)
    return [scene(None, "The settings", "Everything is decided in one values file", left, [
        J("Where are all these numbers written down?"),
        S("In one place: the Helm values file. The SLO targets, the burn rate, how often to measure, and the "
          "canary steps. Changing the policy is a reviewed pull request, not a decision in the middle of an incident."),
        S("Two settings deserve attention. failureLimit 1 means one bad measurement is forgiven, because one noisy "
          "sample should not kill a good release. The second bad one aborts."),
        S("And consecutiveErrorLimit 4: if Prometheus cannot answer five times in a row, the analysis gives up and "
          "the release is aborted. We will break Prometheus on purpose later to prove it."),
        S("With five replicas, each step of twenty percent moves exactly one pod from the old version to the new."),
    ])]


def analysis_code() -> list[dict]:
    rendered = (REC / "rendered-analysistemplate.yaml").read_text(encoding="utf-8").split("\n")
    a = next(i for i, l in enumerate(rendered) if "- name: canary-error-ratio" in l)
    b = next(i for i, l in enumerate(rendered) if "# Latency SLI" in l)
    text = "\n".join(l[4:] for l in rendered[a:b])
    text = text.replace('{app="orders-api",route="/api/orders",rollouts_pod_template_hash="{{args.canary-hash}}"',
                        '{\n          app="orders-api", route="/api/orders",\n'
                        '          rollouts_pod_template_hash="{{args.canary-hash}}"')
    body = code("helm template … (the rendered AnalysisTemplate)", text, size=21)
    return [scene(None, "The check", "The question Argo Rollouts asks Prometheus", body, [
        J("And what exactly does it ask Prometheus?"),
        S("This is the AnalysisTemplate. The first check is the canary's error ratio: failed requests divided by all "
          "requests, over the last minute."),
        S("The important detail is the selector. Every pod carries a label with the hash of its revision, and Argo "
          "Rollouts fills in the canary's hash. So the stable pods cannot hide a bad canary in the average."),
        S("The success condition has a second safety detail: the result must exist. If no traffic reached the canary, "
          "there is no data, and no data counts as a failure. A version nobody tested is never promoted."),
        S("The second check, below it, works the same way for the p95 latency, with the 300 ms limit."),
    ])]


def alerts() -> list[dict]:
    body = grid([
        card(1, "📟", "Fast burn · page", "burn rate above 14.4 over 1 hour AND 5 minutes: 2% of the budget gone in an hour", "bad"),
        card(2, "📟", "Slow burn · page", "above 6 over 6 hours AND 30 minutes: 5% of the budget gone in 6 hours", "amber"),
        card(3, "🎫", "Ticket", "above 3 over 1 day AND 2 hours: 10% of the budget gone in a day", "blue"),
        card(4, "🐢", "Latency fast burn · page", "more than 14.4% of requests slower than 300 ms, 1 hour and 5 minutes", "violet"),
    ], cols=2)
    return [scene(None, "Alerts that mean something", "Burn-rate alerts with two windows", body, [
        J("The canary is protected. What about problems that show up later, after a release?"),
        S("That is the job of the burn-rate alerts. They follow the Google SRE Workbook. The fast-burn alert pages "
          "when the budget burns fourteen times too fast, over one hour, and also over the last five minutes."),
        S("Why two windows? The long window proves it is significant, not a blip. The short window proves it is "
          "still happening now, so the alert stops soon after the problem does."),
        S("A slower burn over six hours also pages, and a slow leak over a whole day opens a ticket instead of "
          "waking anyone up."),
        S("There is a matching alert for latency. And all four rules are unit-tested with promtool, so we know they "
          "fire exactly when they should."),
    ])]


def idea_part() -> list[dict]:
    return problem() + analogy() + sli_slo() + threshold() + architecture() + rollout_code() + analysis_code() + alerts()


def scenes() -> list[dict]:
    from demo import demo_part
    return idea_part() + demo_part()
