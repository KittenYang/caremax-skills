#!/usr/bin/env bash
# Print {"status":"valid"|"expired"|"missing", ...}
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/lib/client.py" check-token
