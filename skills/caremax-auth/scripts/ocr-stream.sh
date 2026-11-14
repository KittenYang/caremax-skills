#!/usr/bin/env bash
# Start OCR for a session.
# Current production API returns JSON 202 (queued). This script prints one
# JSON object: step=accepted, or step=error. If a server still replies with
# text/event-stream, each SSE data payload is printed as its own JSON line.
# Usage: bash ocr-stream.sh <session_id>
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/lib/client.py" ocr-stream "$@"
