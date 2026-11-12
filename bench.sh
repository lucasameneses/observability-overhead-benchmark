#!/usr/bin/env bash
# Entry point for the observability overhead benchmark.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

GATEWAY="http://localhost:18888"
ORDER_ENDPOINT="${GATEWAY}/api/v1/orderservice/order"

usage() {
  cat <<'EOF'
Usage: ./bench.sh <command>

  up <baseline|observed>   Build and start one configuration (stops the other first)
  smoke                    Send 100 requests through the gateway
  down                     Stop and remove everything, including volumes
  run [--dry-run|--force]  Full experiment: 2 configs x 3 loads x 30 reps (about 17 h)
  analyze                  Statistical analysis of results/ (needs the k6 JSON files)
EOF
}

compose_file() {
  case "$1" in
    baseline) echo docker-compose.baseline.yml ;;
    observed) echo docker-compose.yml ;;
    *) echo "Unknown configuration: $1 (use baseline or observed)" >&2; exit 1 ;;
  esac
}

ensure_agent() {
  [[ -f opentelemetry-javaagent.jar ]] || bash scripts/download-otel-agent.sh
}

down_all() {
  docker compose -f docker-compose.yml down -v --remove-orphans 2>/dev/null || true
  docker compose -f docker-compose.baseline.yml down -v --remove-orphans 2>/dev/null || true
}

wait_for_gateway() {
  echo -n "Waiting for the gateway"
  for _ in $(seq 1 60); do
    if curl -sf -o /dev/null "${ORDER_ENDPOINT}"; then echo " ready"; return 0; fi
    echo -n "."; sleep 3
  done
  echo " not ready after 180 s" >&2
  exit 1
}

cmd="${1:-}"
case "$cmd" in
  up)
    file="$(compose_file "${2:-}")"
    ensure_agent
    down_all
    docker compose -f "$file" up -d --build
    wait_for_gateway
    if [[ "$2" == "observed" ]]; then
      echo "Grafana http://localhost:3000 | Jaeger http://localhost:16686 | Prometheus http://localhost:9090"
    fi
    ;;
  smoke) bash scripts/smoke-test.sh "$GATEWAY" ;;
  down) down_all ;;
  run) ensure_agent; shift; bash scripts/run-experiments.sh "$@" ;;
  analyze) python3 scripts/analyze.py ;;
  *) usage; exit 1 ;;
esac
