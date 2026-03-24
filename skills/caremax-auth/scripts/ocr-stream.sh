#!/usr/bin/env bash
# OCR V2 流式调用 — 读取 SSE 进度并输出最终结果
# 用法: bash ocr-stream.sh <session_id>
# 输出: 每行一个 SSE 事件 JSON，最后一行 step=done 包含完整 reports

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SESSION_ID="${1:?Usage: ocr-stream.sh <session_id>}"

# 检查 token
TOKEN_STATUS=$("$SCRIPT_DIR/check-token.sh")
STATUS=$(echo "$TOKEN_STATUS" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")

if [ "$STATUS" = "missing" ]; then
  echo '{"step":"error","progress":-1,"message":"No credentials. Run auth-flow.sh first"}'
  exit 1
fi

if [ "$STATUS" = "expired" ]; then
  REFRESH_RESULT=$("$SCRIPT_DIR/refresh-token.sh")
  REFRESH_STATUS=$(echo "$REFRESH_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
  if [ "$REFRESH_STATUS" != "refreshed" ]; then
    echo '{"step":"error","progress":-1,"message":"Token expired and refresh failed"}'
    exit 1
  fi
  TOKEN_STATUS=$("$SCRIPT_DIR/check-token.sh")
fi

ACCESS_TOKEN=$(echo "$TOKEN_STATUS" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
BASE_URL=$(echo "$TOKEN_STATUS" | python3 -c "import sys,json; print(json.load(sys.stdin)['base_url'])")

# SSE 流式请求
curl -s -N -X POST "${BASE_URL}/api/sessions/${SESSION_ID}/ocr" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{}' |
while IFS= read -r line; do
  if [[ "$line" == data:* ]]; then
    echo "${line#data: }"
  fi
done
