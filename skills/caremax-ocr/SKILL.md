---
name: caremax-ocr
description: "Upload medical reports and run OCR recognition via CareMax Health API. Session-based: upload creates a session, OCR processes all files in the session, confirm saves all reports atomically. Trigger terms: upload report, scan report, OCR, recognize report, extract indicators, health report image, check-up photo, upload, scan, extract."
license: MIT
---

# CareMax Upload & OCR

Upload medical report files (PDF, JPG, PNG, HEIC) and extract structured data via AI-powered OCR.

**Session-based workflow**: upload → OCR → review → confirm. All operations are on a single session.

## Prerequisites — Auto-Auth (MANDATORY)

```bash
APICALL="bash ~/.claude/skills/caremax-auth/scripts/api-call.sh"
UPLOAD="bash ~/.claude/skills/caremax-auth/scripts/upload.sh"
OCRSTREAM="bash ~/.claude/skills/caremax-auth/scripts/ocr-stream.sh"
```

If any script returns `no_credentials` → run `bash ~/.claude/skills/caremax-auth/scripts/auth-flow.sh [base_url]`.

## Step 1: Upload (creates session)

```bash
$UPLOAD /path/to/report1.jpg /path/to/report2.jpg /path/to/report.pdf
```

Returns:
```json
{
  "session_id": "uuid-xxx",
  "member_id": "uuid-yyy",
  "files": [
    { "id": "file-1", "original_name": "report1.jpg" },
    { "id": "file-2", "original_name": "report2.jpg" },
    { "id": "file-3", "original_name": "report.pdf" }
  ]
}
```

Save the `session_id`.

## Step 2: OCR with real-time progress

```bash
$OCRSTREAM <session_id>
```

Outputs one JSON per line:
```json
{"step":"normalize","progress":5,"message":"Loading file 1/3..."}
{"step":"ocr","progress":30,"message":"OCR page 2/3: report2.jpg"}
{"step":"structure","progress":62,"message":"Detecting report groups..."}
{"step":"structure","progress":75,"message":"Structuring report 2/2..."}
{"step":"normalize_indicators","progress":88,"message":"Standardizing..."}
{"step":"done","progress":100,"data":{"session_id":"...","reports":[...]}}
```

Display progress to the user as each line arrives.

## Step 3: Review results (MANDATORY)

Parse the `step=done` data. Show formatted summary. **Do NOT auto-confirm.**

```
识别到 2 份报告：

📋 报告 1: 尿生化 (编号: 114431194)
   来源: report1.jpg, report2.jpg
   日期: 2025-02-05  医生: 俞海瑾  科室: 门诊肾脏
   ┌───────────────────────────┬────────┬──────────┬────────────────────┬──────┐
   │ 指标                      │ 结果   │ 单位     │ 参考范围           │ 异常 │
   ├───────────────────────────┼────────┼──────────┼────────────────────┼──────┤
   │ 尿总蛋白/尿肌酐(mg/mmol)  │ 9.75   │ mg/mmol  │ <15                │      │
   │ 24H尿钠                   │ 130.0  │ mmol/24h │ 137-257            │  ⬆   │
   └───────────────────────────┴────────┴──────────┴────────────────────┴──────┘

📋 报告 2: 尿生化 (编号: 119748491)
   来源: report2.jpg
   ...

确认保存吗？
```

## Step 4: Confirm and save

After user confirms:

```bash
$APICALL POST "/api/skill/sessions/<session_id>/confirm" '{"reports":[<reports from step 2>]}'
```

Returns: `{"success":true,"message":"2 report(s) saved","recordIds":[...]}`

## Other session operations

```bash
# List all sessions
$APICALL GET /api/skill/sessions

# Get session detail (including saved reports if completed)
$APICALL GET "/api/skill/sessions/<session_id>"

# Delete session (undo everything: files + reports)
$APICALL DELETE "/api/skill/sessions/<session_id>"
```
