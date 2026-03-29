#!/usr/bin/env bash
# Publish all CareMax skills to ClawHub.
# Prerequisite: npx clawhub@latest login  (or CLAWHUB_TOKEN for CI)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLAWHUB_BIN="${CLAWHUB_BIN:-npx --yes clawhub@latest}"
VERSION="${CAREMAX_CLAWHUB_VERSION:-1.0.0}"
CHANGELOG="${CAREMAX_CLAWHUB_CHANGELOG:-Initial publish to ClawHub}"

if ! $CLAWHUB_BIN whoami &>/dev/null; then
  echo "Not logged in. Run: cd \"$ROOT\" && npx clawhub@latest login"
  echo "Or set CLAWHUB_TOKEN and re-run."
  exit 1
fi

publish() {
  local dir="$1" slug="$2" name="$3"
  local skill_path="$ROOT/skills/$dir"
  echo ">>> Publishing $slug ($name) @ $VERSION ..."
  # clawhub CLI requires an absolute path here; "." is rejected as "not a folder"
  $CLAWHUB_BIN publish \
    --slug "$slug" \
    --name "$name" \
    --version "$VERSION" \
    --changelog "$CHANGELOG" \
    --tags latest \
    "$skill_path"
}

# Auth first — other skills document it as prerequisite
publish caremax-auth       caremax-auth       "CareMax Auth"
publish caremax-ocr        caremax-ocr        "CareMax OCR"
publish caremax-indicators caremax-indicators "CareMax Indicators"
publish caremax-members    caremax-members    "CareMax Members"
publish caremax-records    caremax-records    "CareMax Records"

echo "Done. Bump CAREMAX_CLAWHUB_VERSION for subsequent releases."
