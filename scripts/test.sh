#!/usr/bin/env bash
# Run the full CareMax skills suite. No production calls, no secrets.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 -m unittest discover -s tests -v
