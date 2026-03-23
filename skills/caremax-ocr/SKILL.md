---
name: caremax-ocr
description: "Upload medical reports and run OCR recognition via CareMax Health API. Use when a user wants to upload a health report image or PDF, scan a medical document, extract data from a check-up report. Trigger terms: upload report, scan report, OCR, recognize report, extract indicators, health report image, check-up photo, upload, scan, extract."
license: MIT
---

# CareMax Upload & OCR

Upload medical report files (PDF, JPG, PNG) and extract structured data via OCR.

**IMPORTANT: OCR is a THREE-step process: upload → OCR extract → user review → confirm.**
The agent MUST show extracted results to the user for review before confirming. Never auto-confirm.

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

## Step 2: OCR Extract (returns raw results for review)

```bash
$APICALL POST /api/skill/ocr '{"fileIds":["file-uuid-1"],"memberId":"member-uuid"}'
```

Response includes extracted records with indicators. **DO NOT consider this final.** Show the results to the user:

```
Extracted from your report:
  Hospital: XXX Hospital
  Date: 2025-03-15
  Report: Blood Routine

  Indicators:
  1. Hemoglobin: 135 g/L (normal, ref: 130-175)
  2. White Blood Cells: 11.2 ×10⁹/L (HIGH, ref: 3.5-9.5)
  3. Platelets: 230 ×10⁹/L (normal, ref: 125-350)

  Does this look correct? Should I save it?
```

Wait for user confirmation. The user may want to:
- Correct a misread value
- Change an indicator name mapping
- Remove a false positive indicator

## Step 3: Confirm (save to database)

After user says "looks good" / "save it" / confirms:

```bash
$APICALL POST /api/skill/ocr/confirm '{"results": [<the records array from step 2>]}'
```

Pass back the `results` array from step 2 (with any user edits applied).

## Complete Workflow

When user says "help me scan this report" or shares an image:

```bash
# 1. Upload
TOKEN=$(bash ~/.claude/skills/caremax-auth/scripts/check-token.sh | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
BASE_URL=$(bash ~/.claude/skills/caremax-auth/scripts/check-token.sh | python3 -c "import sys,json; print(json.load(sys.stdin)['base_url'])")
UPLOAD_RESULT=$(curl -s -X POST "$BASE_URL/api/skill/upload" -H "Authorization: Bearer $TOKEN" -F "file=@/path/to/report.pdf")
# Extract fileIds from UPLOAD_RESULT

# 2. OCR extract
$APICALL POST /api/skill/ocr '{"fileIds":["file-uuid-from-step-1"]}'
# Show results to user, ask for confirmation

# 3. After user confirms
$APICALL POST /api/skill/ocr/confirm '{"results": [...]}'
```

## Notes

- Free users have limited OCR scans/month; premium = unlimited
- OCR handles Chinese medical reports natively
- After confirm, data is immediately queryable via caremax-indicators and caremax-records
- Models used: Mistral OCR → multi-model validation (Qwen/Gemini) → indicator standardization (Gemini Flash)
