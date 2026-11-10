#!/usr/bin/env bash
# Lightweight OCR / save progress: GET /api/skill/sessions/:id/status
# Usage: bash session-status.sh <session_id>
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/lib/client.py" session-status "$@"
