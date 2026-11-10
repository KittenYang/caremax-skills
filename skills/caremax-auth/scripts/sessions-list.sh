#!/usr/bin/env bash
# Unfinished upload tasks vs paginated history.
#   sessions-list.sh unfinished [--member UUID] [--limit N]
#   sessions-list.sh history [--member UUID] [--page N] [--limit N]
#   sessions-list.sh status <status> [--member UUID] [--page N] [--limit N]
# unfinished issues one GET per in-progress status. history omits status.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/lib/client.py" sessions "$@"
