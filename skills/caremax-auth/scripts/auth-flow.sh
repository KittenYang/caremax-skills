#!/usr/bin/env bash
# One-shot Device Flow: request a code, open the browser, poll, save the token.
# Usage: bash auth-flow.sh [base_url]
# Set CAREMAX_SKIP_BROWSER=1 to skip launching a browser (tests and headless agents).
set -euo pipefail

BASE_URL="${1:-https://api.caremax.ai}"
CREDS_FILE="${CAREMAX_CREDENTIALS_FILE:-$HOME/.caremax/credentials.json}"

DEVICE_RESPONSE=$(curl -sS -X POST "$BASE_URL/api/auth/device" \
  -H "Content-Type: application/json" \
  -d '{"client_id":"caremax-agent","scope":"read:indicators read:records read:members write:upload write:ocr search:records"}')

DEVICE_CODE=$(echo "$DEVICE_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['device_code'])" 2>/dev/null) || {
  echo "{\"status\":\"error\",\"message\":\"Failed to get device code\"}"
  exit 1
}
VERIFY_URL=$(echo "$DEVICE_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['verification_uri_complete'])")
INTERVAL=$(echo "$DEVICE_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('interval',5))")

if [[ "${CAREMAX_SKIP_BROWSER:-}" != "1" ]]; then
  if command -v open >/dev/null 2>&1; then
    open "$VERIFY_URL" || true
  elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$VERIFY_URL" >/dev/null 2>&1 || true
  fi
fi

echo "Authorization page opened: $VERIFY_URL"
echo "Waiting for user to approve..."

if [[ "$INTERVAL" -lt 1 ]]; then
  INTERVAL=1
fi
MAX_ATTEMPTS=$(( 900 / INTERVAL ))
for _ in $(seq 1 "$MAX_ATTEMPTS"); do
  sleep "$INTERVAL"

  TOKEN_RESPONSE=$(curl -sS -X POST "$BASE_URL/api/auth/device/token" \
    -H "Content-Type: application/json" \
    -d "{\"device_code\":\"$DEVICE_CODE\",\"grant_type\":\"device_code\"}")

  if echo "$TOKEN_RESPONSE" | CAREMAX_BASE_URL="$BASE_URL" CAREMAX_CREDS_FILE="$CREDS_FILE" python3 -c '
import json, os, sys
from datetime import datetime, timedelta, timezone
resp = json.load(sys.stdin)
if "access_token" not in resp:
    sys.exit(1)
expires = datetime.now(timezone.utc) + timedelta(seconds=int(resp["expires_in"]))
creds = {
    "access_token": resp["access_token"],
    "refresh_token": resp.get("refresh_token", ""),
    "expires_at": expires.strftime("%Y-%m-%dT%H:%M:%SZ"),
    "scope": resp.get("scope", ""),
    "base_url": os.environ["CAREMAX_BASE_URL"],
}
path = os.environ["CAREMAX_CREDS_FILE"]
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w", encoding="utf-8") as handle:
    json.dump(creds, handle, indent=2)
    handle.write("\n")
print(json.dumps({"status": "authorized", "access_token": resp["access_token"], "base_url": os.environ["CAREMAX_BASE_URL"]}))
' ; then
    exit 0
  fi

  ERROR=$(echo "$TOKEN_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('error','unknown'))" 2>/dev/null || echo "unknown")

  if [[ "$ERROR" == "authorization_pending" ]]; then
    continue
  elif [[ "$ERROR" == "access_denied" ]]; then
    echo "{\"status\":\"denied\",\"message\":\"User denied authorization\"}"
    exit 1
  elif [[ "$ERROR" == "expired_token" ]]; then
    echo "{\"status\":\"expired\",\"message\":\"Authorization code expired\"}"
    exit 1
  else
    echo "{\"status\":\"error\",\"message\":\"Unexpected error: $ERROR\"}"
    exit 1
  fi
done

echo "{\"status\":\"timeout\",\"message\":\"Authorization timed out after 15 minutes\"}"
exit 1
