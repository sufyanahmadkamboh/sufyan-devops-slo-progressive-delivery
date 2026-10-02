{{- define "orders-api.labels" -}}
app.kubernetes.io/name: orders-api
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
{{- end }}

{{- define "orders-api.podSecurityContext" -}}
runAsNonRoot: true
runAsUser: 10001
runAsGroup: 10001
seccompProfile:
  type: RuntimeDefault
{{- end }}

{{- define "orders-api.containerSecurityContext" -}}
allowPrivilegeEscalation: false
readOnlyRootFilesystem: true
capabilities:
  drop: ["ALL"]
{{- end }}

{{/* Highest acceptable canary error ratio: (1 - availability target) x max burn rate. */}}
{{- define "orders-api.maxErrorRatio" -}}
{{- printf "%.4f" (mulf (subf 1.0 .Values.slo.availabilityTarget) .Values.analysis.maxBurnRate) -}}
{{- end }}

{{/* Prometheus label selector for the canary pods; the hash is filled in by Argo Rollouts at analysis time. */}}
{{- define "orders-api.canarySelector" -}}
app="orders-api",route="/api/orders",rollouts_pod_template_hash="{{ "{{" }}args.canary-hash{{ "}}" }}"
{{- end }}
