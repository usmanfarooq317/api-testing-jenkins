#!/usr/bin/env bash
# tests/run_tests.sh
# This script runs a suite of curl checks against http://localhost:5090
# It prints status codes and bodies for each scenario (normal, missing header, wrong key, bad body, extra header)
set -euo pipefail

BASE_URL="http://127.0.0.1:5090"
SECRET="secret-key-123"
REQID="test-req-$(date +%s)"

echo "== Basic health check =="
curl -s -o /dev/stderr -w "HTTP %{http_code}\n" "${BASE_URL}/health" || true
echo

json_good='{"name":"Alice"}'
json_bad='{"bad": "payload"}'
json_malformed='{"name": "MissingQuote}'

# 1) correct request
echo "== Test 1: correct request (expect 200) =="
curl -s -i -X POST "${BASE_URL}/api/secure" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: ${SECRET}" \
  -H "X-Request-Id: ${REQID}" \
  -d "${json_good}"
echo -e "\n\n"

# 2) missing X-Api-Key header
echo "== Test 2: missing X-Api-Key (expect 400) =="
curl -s -i -X POST "${BASE_URL}/api/secure" \
  -H "Content-Type: application/json" \
  -H "X-Request-Id: ${REQID}" \
  -d "${json_good}"
echo -e "\n\n"

# 3) wrong API key (expect 401)
echo "== Test 3: wrong X-Api-Key (expect 401) =="
curl -s -i -X POST "${BASE_URL}/api/secure" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: wrong-key" \
  -H "X-Request-Id: ${REQID}" \
  -d "${json_good}"
echo -e "\n\n"

# 4) missing X-Request-Id (expect 400)
echo "== Test 4: missing X-Request-Id (expect 400) =="
curl -s -i -X POST "${BASE_URL}/api/secure" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: ${SECRET}" \
  -d "${json_good}"
echo -e "\n\n"

# 5) bad/malformed JSON (expect 400)
echo "== Test 5: malformed JSON (expect 400) =="
curl -s -i -X POST "${BASE_URL}/api/secure" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: ${SECRET}" \
  -H "X-Request-Id: ${REQID}" \
  --data-binary "${json_malformed}"
echo -e "\n\n"

# 6) wrong body field (e.g., name too short) (expect 400)
echo "== Test 6: wrong body (name too short) (expect 400) =="
curl -s -i -X POST "${BASE_URL}/api/secure" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: ${SECRET}" \
  -H "X-Request-Id: ${REQID}" \
  -d '{"name":"A"}'
echo -e "\n\n"

# 7) extra header but otherwise OK (should still work -> 200)
echo "== Test 7: extra header present (expect 200) =="
curl -s -i -X POST "${BASE_URL}/api/secure" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: ${SECRET}" \
  -H "X-Request-Id: ${REQID}" \
  -H "X-Debug: 1" \
  -d "${json_good}"
echo -e "\n\n"

echo "== Done tests =="
