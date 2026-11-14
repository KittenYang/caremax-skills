#!/usr/bin/env bash
# Download a session source file.
# Usage: bash download-file.sh <file_id> [output_path]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/lib/client.py" download "$@"
