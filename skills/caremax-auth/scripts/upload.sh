#!/usr/bin/env bash
# Create an upload session and store files.
# Usage: bash upload.sh [--member UUID] <file1> [file2 ...]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/lib/client.py" upload "$@"
