#!/usr/bin/env bash
# List quick-log presets from GET /api/indicators?category=common_indicator.
# The deprecated GET /api/indicators/system-presets route still exists; this
# script uses the successor and normalizes canonical_name to preset_key.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/lib/client.py" presets
