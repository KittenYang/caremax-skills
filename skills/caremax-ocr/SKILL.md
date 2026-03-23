---
name: caremax-ocr
description: "Upload medical reports and run OCR recognition via CareMax Health API. Supports multiple files, auto-detects multiple reports from one upload, shows real-time progress. Trigger terms: upload report, scan report, OCR, recognize report, extract indicators, health report image, check-up photo, upload, scan, extract."
license: MIT
---

# CareMax Upload & OCR (V2)

Upload medical report files (PDF, JPG, PNG, HEIC) and extract structured data via AI-powered OCR.

**Key features:**
- Automatically splits multiple reports from one upload (e.g., 10 images → 3 reports)
- Long screenshots with multiple reports → auto-detected and separated
- Multi-page PDF → auto-split into individual reports
- Real-time SSE progress streaming
- PaddleOCR + Mistral OCR + LLM smart grouping

## Prerequisites — Auto-Auth (MANDATORY)

```bash
APICALL="bash ~/.claude/skills/caremax-auth/scripts/api-call.sh"
OCRSTREAM="bash ~/.claude/skills/caremax-auth/scripts/ocr-stream.sh"
```

If any script returns `no_credentials` → **immediately run `bash ~/.claude/skills/caremax-auth/scripts/auth-flow.sh`**.

## Step 1: Upload Files

Upload one or more files (supports PDF, JPG, PNG, HEIC):

```bash
TOKEN=$(bash ~/.claude/skills/caremax-auth/scripts/check-token.sh | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
BASE_URL=$(bash ~/.claude/skills/caremax-auth/scripts/check-token.sh | python3 -c "import sys,json; print(json.load(sys.stdin)['base_url'])")

# Single file
curl -s -X POST "$BASE_URL/api/skill/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "files=@/path/to/report1.jpg" \
  -F "member_id=member-uuid"

# Multiple files
curl -s -X POST "$BASE_URL/api/skill/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "files=@/path/to/page1.jpg" \
  -F "files=@/path/to/page2.jpg" \
  -F "files=@/path/to/report.pdf"
```

Response: `{"files":[{"id":"file-uuid-1",...},{"id":"file-uuid-2",...}]}`

## Step 2: OCR with Real-Time Progress (SSE)

Use the streaming script to get real-time progress:

```bash
$OCRSTREAM '{"fileIds":["file-uuid-1","file-uuid-2","file-uuid-3"],"memberId":"member-uuid"}'
```

This outputs one JSON per line as OCR progresses:

```json
{"step":"normalize","progress":5,"message":"Loading file 1/3..."}
{"step":"ocr","progress":25,"message":"OCR page 2/8: report.pdf#page2"}
{"step":"ocr","progress":45,"message":"OCR page 6/8: photo3.jpg"}
{"step":"structure","progress":62,"message":"CareMax-Qwen3 analyzing..."}
{"step":"normalize_indicators","progress":88,"message":"Standardizing indicator names..."}
{"step":"done","progress":100,"message":"3 report(s) ready for review","data":{"reports":[...]}}
```

**Display progress to the user as each line arrives.** The last line (step=done) contains the full results.

### Understanding the response

The `data.reports` array may contain MULTIPLE reports from the same upload:

```json
{
  "reports": [
    {
      "record": { "report_title": "Blood Routine", "indicators": [...], ... },
      "sourcePages": ["photo1.jpg", "photo2.jpg"],
      "confidence": 1.0
    },
    {
      "record": { "report_title": "Urine Test", "indicators": [...], ... },
      "sourcePages": ["photo3.jpg"],
      "confidence": 1.0
    }
  ]
}
```

## Step 3: Show Results to User (MANDATORY)

**You MUST show extracted results and ask for confirmation before saving.** Example:

```
Identified 2 reports from your 3 files:

Report 1: Blood Routine (from photo1.jpg, photo2.jpg)
  Hospital: City Hospital | Date: 2025-03-15
  - Hemoglobin: 135 g/L (normal, ref: 130-175)
  - White Blood Cells: 11.2 ×10⁹/L (HIGH, ref: 3.5-9.5)
  - Platelets: 230 ×10⁹/L (normal, ref: 125-350)

Report 2: Urine Test (from photo3.jpg)
  Hospital: City Hospital | Date: 2025-03-15
  - pH: 6.5 (normal, ref: 4.5-8.0)
  - Protein: Negative (normal)

Does this look correct? Should I save both reports?
```

Wait for user confirmation. User may want to correct values or remove a report.

## Step 4: Confirm and Save

After user confirms:

```bash
$APICALL POST /api/skill/ocr/confirm '{
  "reports": [
    { "record": { <report 1 JSON from step 2, with any user edits> } },
    { "record": { <report 2 JSON from step 2> } }
  ],
  "memberId": "member-uuid"
}'
```

Response: `{"success":true,"message":"2 report(s) saved","recordIds":["id1","id2"]}`

## Smart Detection Examples

| User uploads | What happens |
|---|---|
| 3 photos of one blood test | → merged into 1 report |
| 1 long screenshot with blood + urine | → split into 2 reports |
| 5 photos (3 blood + 2 liver) | → 2 reports |
| 10-page PDF check-up package | → N reports (auto-detected) |
| Mix of 2 JPGs + 1 PDF | → all pages analyzed together |
