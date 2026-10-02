SHELL := bash
.DEFAULT_GOAL := help
PROMETHEUS_IMAGE := prom/prometheus:v3.15.0
CRD_SCHEMAS := https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json

help: ## Show available targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-16s %s\n", $$1, $$2}'

test: ## Unit tests for the service (pytest)
	cd app && python -m pytest -q

lint: ## Static checks: ruff, shellcheck, helm lint, kubeconform
	cd app && ruff check . && ruff format --check .
	shellcheck scripts/*.sh
	helm lint charts/orders-api
	helm template orders-api charts/orders-api -n delivery \
	  | kubeconform -strict -summary -schema-location default -schema-location '$(CRD_SCHEMAS)'
	kubeconform -strict -summary platform/monitoring/*.yaml

slo-test: ## Validate and unit-test the SLO recording/alerting rules (promtool)
	docker run --rm -v "$(CURDIR)/slo:/slo" --entrypoint promtool $(PROMETHEUS_IMAGE) check rules /slo/rules/orders-api-slo.rules.yaml
	docker run --rm -v "$(CURDIR)/slo:/slo" -w /slo/tests --entrypoint promtool $(PROMETHEUS_IMAGE) test rules orders-api-slo.test.yaml

image: ## Build the service image
	docker build -t orders-api:dev app

up: ## Create the kind lab and deploy everything (release 1.0.0)
	scripts/up.sh

e2e: ## Prove promotion of a good release and automatic rollback of bad ones
	scripts/e2e.sh

chaos: ## Failure test: Prometheus outage during a canary
	scripts/chaos-prometheus-outage.sh

netpol: ## Security test: NetworkPolicy blocks other namespaces
	scripts/check-network-policy.sh

down: ## Delete the lab cluster
	scripts/down.sh

.PHONY: help test lint slo-test image up e2e chaos netpol down
