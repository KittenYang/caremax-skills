#!/usr/bin/env bash
# Authenticated JSON API call. Refreshes a locally expired token and retries
# once on HTTP 401 invalid_token / token_expired.
# Usage: bash api-call.sh <METHOD> <PATH> [JSON_BODY]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/lib/client.py" call "$@"
