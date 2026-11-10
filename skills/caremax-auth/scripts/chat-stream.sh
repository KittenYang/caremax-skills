#!/usr/bin/env bash
# Health Q&A with Accept: text/event-stream.
# Prints one JSON object per SSE event: {"event","data"}.
# Usage:
#   chat-stream.sh --question "..." [--conversation ID] [--record ID]
#                  [--member ID] [--retry USER_MESSAGE_ID] [--deep]
#   chat-stream.sh --file body.json
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/lib/client.py" chat-stream "$@"
