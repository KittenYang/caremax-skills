#!/usr/bin/env bash
# Confirm a session that is still awaiting review, or update a saved report.
#   save-reports.sh --session ID --file payload.json
#   save-reports.sh --update --file payload.json
# payload.json for confirm is {"reports":[...]}.
# payload.json for update is {"records":[...],"member_id":"..."}.
# Does not call confirm on completed, cancelled, or saving sessions.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/lib/client.py" save-reports "$@"
