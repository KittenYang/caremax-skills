---
name: caremax-ocr
description: "Upload medical reports and run OCR recognition via CareMax Health API. Use when a user wants to upload a health report image or PDF, scan a medical document, extract data from a check-up report. Trigger terms: upload report, scan report, OCR, recognize report, extract indicators, health report image, check-up photo, 上传报告, 识别报告, 扫描."
license: MIT
---

# CareMax Upload & OCR

Upload medical report files (PDF, JPG, PNG) and extract structured data via OCR. Always two steps: upload, then OCR.

## Prerequisites — Auto-Auth (MANDATORY)

```bash
APICALL="bash ~/.claude/skills/caremax-auth/scripts/api-call.sh"
```

If `api-call.sh` returns `{"error":"no_credentials",...}` → **immediately run `bash ~/.claude/skills/caremax-auth/scripts/auth-flow.sh`** in background. It opens the browser and auto-polls. Tell the user "please authorize in browser". Once it outputs `authorized`, retry the api-call.

## Step 1: Upload Report

Upload requires multipart form-data, so use curl directly with the token from check-token.sh:

```bash
TOKEN=$(bash ~/.claude/skills/caremax-auth/scripts/check-token.sh | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
BASE_URL=$(bash ~/.claude/skills/caremax-auth/scripts/check-token.sh | python3 -c "import sys,json; print(json.load(sys.stdin)['base_url'])")

curl -s -X POST "$BASE_URL/api/skill/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/report.pdf" \
  -F "memberId=member-uuid"
```

Response: `{"fileIds":["file-uuid-1","file-uuid-2"]}`

## Step 2: OCR Recognition

```bash
$APICALL POST /api/skill/ocr '{"fileIds":["file-uuid-1"],"memberId":"member-uuid"}'
```

Response: `{"records":[{"test_date":"...","hospital":"...","indicators":[...]}]}`

## Complete Workflow

When user says "help me scan this report" or shares an image:

1. Upload the file → get fileIds
2. OCR with fileIds → get extracted records
3. Present: hospital, date, indicators with values, reference ranges
4. Highlight abnormal indicators

## Notes

- Free users have limited OCR scans/month; premium = unlimited
- OCR handles Chinese medical reports natively
- After OCR, data is immediately queryable via caremax-indicators and caremax-records
