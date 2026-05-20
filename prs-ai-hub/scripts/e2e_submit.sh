#!/usr/bin/env bash
# End-to-end: load fixture, submit PRS, poll until complete.
set -euo pipefail

API="${API_URL:-http://localhost:8000/api/v1}"
FIXTURE="${1:-apextech-clean}"
MAX_WAIT="${MAX_WAIT:-180}"

echo "=== E2E: fixture=$FIXTURE ==="

echo "1. Fetch fixture..."
PAYLOAD=$(curl -sf "$API/fixtures/$FIXTURE")
echo "   OK ($(echo "$PAYLOAD" | wc -c) bytes)"

echo "2. Submit PRS..."
RESP=$(curl -sf -X POST "$API/prs/submit" -H "Content-Type: application/json" -d "$PAYLOAD")
REQUEST_ID=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['request_id'])")
echo "   request_id=$REQUEST_ID"

echo "3. Poll status (max ${MAX_WAIT}s)..."
for i in $(seq 1 "$MAX_WAIT"); do
  STATUS_JSON=$(curl -sf "$API/prs/status/$REQUEST_ID")
  JOB=$(echo "$STATUS_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
  if [[ "$JOB" == "complete" ]]; then
    OVERALL=$(echo "$STATUS_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('result',{}).get('overall_status','?'))")
    echo ""
    echo "=== DONE (${i}s) ==="
    echo "   overall_status=$OVERALL"
    echo "   results: http://localhost:3000/results/$REQUEST_ID"
    echo "$STATUS_JSON" | python3 -m json.tool | head -80
    exit 0
  fi
  if [[ "$JOB" == "failed" ]]; then
    echo "FAILED:"
    echo "$STATUS_JSON" | python3 -m json.tool
    exit 1
  fi
  printf "\r   status=%s (%ds)   " "$JOB" "$i"
  sleep 1
done

echo "Timeout waiting for completion"
exit 1
