#!/usr/bin/env bash
# Refresh access_token using the stored refresh_token.
# Success: {"status":"refreshed","access_token":"...","base_url":"..."}
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/lib/client.py" refresh
