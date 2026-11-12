#!/bin/bash
# Smoke test: send 100 requests to populate observability data
# Usage: bash scripts/smoke-test.sh [BASE_URL]

BASE_URL="${1:-http://localhost:18888}"
ENDPOINT="${BASE_URL}/api/v1/orderservice/order"
COUNT=100

echo "Sending ${COUNT} requests to ${ENDPOINT}..."

SUCCESS=0
FAIL=0

for i in $(seq 1 "$COUNT"); do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${ENDPOINT}")
  if [ "$STATUS" -ge 200 ] && [ "$STATUS" -lt 300 ]; then
    SUCCESS=$((SUCCESS + 1))
  else
    FAIL=$((FAIL + 1))
    echo "  Request ${i} failed with HTTP ${STATUS}"
  fi

  if [ $((i % 25)) -eq 0 ]; then
    echo "  Progress: ${i}/${COUNT} (success: ${SUCCESS}, fail: ${FAIL})"
  fi
done

echo ""
echo "Done! Success: ${SUCCESS}, Fail: ${FAIL}"
echo ""
echo "Verify:"
echo "  Prometheus:  http://localhost:9090"
echo "  Grafana:     http://localhost:3000 (admin/admin)"
echo "  Jaeger:      http://localhost:16686"
echo "  Loki:        http://localhost:3100/loki/api/v1/query?query={service=\"ts-order-service\"}"