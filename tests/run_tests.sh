#!/usr/bin/env bash
# tests/run_tests.sh
# Runs curl tests and stores detailed logs into logs/api-test-results.json

set -euo pipefail

BASE_URL="http://127.0.0.1:5090"
SECRET="secret-key-123"
REQID="test-req-$(date +%s)"
LOG_DIR="./logs"
LOG_FILE="${LOG_DIR}/api-test-results.json"

mkdir -p "$LOG_DIR"

# Start a fresh log file
echo "[" > "$LOG_FILE"

function log_test() {
  local test_name="$1"
  local cmd="$2"

  echo "Running: $test_name"
  local start_time=$(date +"%Y-%m-%d %H:%M:%S")

  # Execute and capture both response body and status
  local response
  response=$(eval "$cmd" 2>&1)
  local status=$?

  local end_time=$(date +"%Y-%m-%d %H:%M:%S")

  # Append structured JSON entry
  {
    echo "{"
    echo "\"test\": \"$test_name\","
    echo "\"start_time\": \"$start_time\","
    echo "\"end_time\": \"$end_time\","
    echo "\"status_code\": $status,"
    echo "\"response\": $(jq -Rs . <<< "$response")"
    echo "},"
  } >> "$LOG_FILE"
}

# Define test cases
log_test "Health check" "curl -s -w '\nHTTP %{http_code}\n' ${BASE_URL}/health"

log_test "Correct request" "curl -s -i -X POST ${BASE_URL}/api/secure \
  -H 'Content-Type: application/json' \
  -H 'X-Api-Key: ${SECRET}' \
  -H 'X-Request-Id: ${REQID}' \
  -d '{\"name\":\"Alice\"}'"

log_test "Missing API key" "curl -s -i -X POST ${BASE_URL}/api/secure \
  -H 'Content-Type: application/json' \
  -H 'X-Request-Id: ${REQID}' \
  -d '{\"name\":\"Alice\"}'"

log_test "Wrong API key" "curl -s -i -X POST ${BASE_URL}/api/secure \
  -H 'Content-Type: application/json' \
  -H 'X-Api-Key: wrong-key' \
  -H 'X-Request-Id: ${REQID}' \
  -d '{\"name\":\"Alice\"}'"

log_test "Malformed JSON" "curl -s -i -X POST ${BASE_URL}/api/secure \
  -H 'Content-Type: application/json' \
  -H 'X-Api-Key: ${SECRET}' \
  -H 'X-Request-Id: ${REQID}' \
  --data-binary '{\"name\": \"MissingQuote}'"

echo "{}]" >> "$LOG_FILE"

echo "✅ Logs written to $LOG_FILE"
