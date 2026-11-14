#!/usr/bin/env bash
# Queue OCR. Production returns HTTP 202 JSON, not an SSE progress stream.
# Usage: bash ocr-kick.sh <session_id>
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/lib/client.py" ocr-kick "$@"
