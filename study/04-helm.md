# 4. Helm

## What is it?

**Helm** is the package manager for Kubernetes. A **chart** is a folder of Kubernetes YAML **templates** plus a **values.yaml** file of settings. Helm fills the templates with the values and sends the result to the cluster. Each install or upgrade is recorded as a **release revision**, so you can see the history and roll back.

```
values.yaml  +  templates/*.yaml   ──helm template──►  plain Kubernetes YAML  ──►  cluster
 (settings)       (with {{ }} gaps)
```

## Why this project uses it

1. **One source, many configurations.** The same chart runs with real timings (`values.yaml`: 60 s pauses) and fast test timings (`ci/fast-values.yaml`: 30 s pauses). No copy-pasted YAML.
2. **Computed values.** The canary error limit is **computed** from the SLO, not typed in by hand (see below).
3. **A release is one command.** `helm upgrade --set image.tag=1.2.0` changes the version; Argo Rollouts takes it from there.

## How it works in this project

**The chart:** [`charts/orders-api/`](../charts/orders-api/)

```
Chart.yaml            name and version of the chart
values.yaml           all settings with comments (SLO targets, analysis timing, canary steps, faults)
templates/
  _helpers.tpl        reusable snippets: labels, security contexts, the computed threshold
  rollout.yaml        the Argo Rollouts canary (chapter 7)
  analysistemplate.yaml  the SLO checks (chapter 7)
  services.yaml       the client-facing Service
  networkpolicy.yaml  the firewall rule
  serviceaccount.yaml
  loadgen.yaml        steady test traffic
```

**Template syntax in 30 seconds:**

```yaml
replicas: {{ .Values.replicas }}                    # insert a value
image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
{{- range .Values.canary.weights }}                 # loop: one step per weight
- setWeight: {{ . }}
{{- end }}
{{- if .Values.networkPolicy.enabled }} ... {{- end }}   # optional object
labels: {{- include "orders-api.labels" . | nindent 4 }} # reuse a snippet from _helpers.tpl
```

**The computed threshold** (in `_helpers.tpl`) turns business numbers into the technical limit:
```
{{- printf "%.4f" (mulf (subf 1.0 .Values.slo.availabilityTarget) .Values.analysis.maxBurnRate) -}}
            (1 - 0.995) × 14.4 = 0.0720
```
If someone changes the SLO to 99.9%, the canary limit becomes stricter automatically (0.0144).

**An escaping trick worth knowing:** the analysis query needs the literal text `{{args.canary-hash}}`, which Argo Rollouts fills in later. Because Helm would try to interpret `{{ }}` itself, the template writes `{{ "{{" }}args.canary-hash{{ "}}" }}`.

**A real problem found in this project (Helm 4):** Helm 4 uses **server-side apply**, so it "owns" every field it writes. When Argo Rollouts also changed the selector of extra stable/canary Services, the next `helm upgrade` failed with a field-ownership conflict. The fix was to remove those Services. Read [troubleshooting](../docs/troubleshooting.md).

## Try it

```bash
helm lint charts/orders-api                                   # checks the chart
helm template orders-api charts/orders-api | less             # see the final YAML without installing
helm template orders-api charts/orders-api -f ci/fast-values.yaml | grep -A2 "pause"
helm template orders-api charts/orders-api --set slo.availabilityTarget=0.999 | grep successCondition
helm -n delivery list                                         # installed releases
helm -n delivery history orders-api                           # every release revision
helm -n delivery get values orders-api                        # the values currently in use
```

## Check yourself

1. What does `helm template` do, and why is it useful in CI?
2. Where does the number 0.072 come from? What happens to it if the SLO becomes 99.9%?
3. What does `--reuse-values` do in `scripts/release.sh`?

<details><summary>Answers</summary>

1. **`helm template`** renders the final YAML locally without touching a cluster. CI pipes that output into kubeconform to validate it against Kubernetes schemas.
2. **0.072** is (1 − 0.995) × 14.4. At 99.9% it becomes (1 − 0.999) × 14.4 = 0.0144, a stricter gate.
3. **`--reuse-values`** keeps the values from the previous release and only changes what you `--set`, such as the image tag.
</details>

Next: [5. SRE basics](05-sre-slo-basics.md)
