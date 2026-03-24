---
name: caremax-auth
description: "OAuth Device Flow authentication for CareMax Health API. This skill is a PREREQUISITE for all other caremax-* skills — invoke it automatically when no token is found. Do NOT ask the user, just run the auth flow. Trigger terms: caremax login, caremax auth, health API token, authorize caremax, connect health data, health indicator, blood test, medical record, upload report."
license: MIT
---

# CareMax Authentication

## CRITICAL RULES

1. This is a **silent prerequisite** for ALL caremax-* skills. Do NOT ask "do you want to authenticate?" — just execute.
2. **NEVER write your own curl commands**. Only use the scripts below.
3. **NEVER split auth into multiple steps manually**. Use `auth-flow.sh` — it opens browser AND auto-polls until done.
4. **BASE URL DETECTION**: If the user specifies a custom URL (e.g., `http://localhost:8787`, `http://localhost:8788`), you MUST:
   - Pass it as the first argument to `auth-flow.sh`: `bash auth-flow.sh http://localhost:8788`
   - After auth completes, `credentials.json` will have `base_url` set to that URL
   - All subsequent `api-call.sh`, `upload.sh`, `ocr-stream.sh` will auto-use it
   - Look for URL patterns like `http://localhost:XXXX`, `caremax(http://...)`, or explicit "use local" / "use localhost"

## Scripts

All scripts are at `~/.claude/skills/caremax-auth/scripts/`.

### api-call.sh — Make authenticated API calls (PRIMARY TOOL)

This is what you should use for all API calls. It auto-checks token, auto-refreshes if expired.

```bash
bash ~/.claude/skills/caremax-auth/scripts/api-call.sh GET /api/skill/indicators
bash ~/.claude/skills/caremax-auth/scripts/api-call.sh POST /api/skill/records/search '{"query":"血常规"}'
bash ~/.claude/skills/caremax-auth/scripts/api-call.sh GET "/api/skill/indicators/trend?id=xxx"
```

If it returns `{"error":"no_credentials",...}` → run `auth-flow.sh` (see below), then retry.

### upload.sh — Upload files (images/PDFs) to CareMax

```bash
bash ~/.claude/skills/caremax-auth/scripts/upload.sh /path/to/report.jpg
bash ~/.claude/skills/caremax-auth/scripts/upload.sh /path/to/img1.jpg /path/to/img2.png
```

Returns: `{"files":[{"id":"...","member_id":"...","original_name":"..."}]}`

Use the returned `id` values as `fileIds` for `ocr-stream.sh`.

**IMPORTANT**: Do NOT use `api-call.sh` for file uploads — it only supports JSON body. Always use `upload.sh` for multipart file uploads.

### ocr-stream.sh — OCR with real-time SSE progress (for caremax-ocr skill)

```bash
bash ~/.claude/skills/caremax-auth/scripts/ocr-stream.sh '{"fileIds":["id1","id2"],"memberId":"xxx"}'
```

Outputs one JSON per line as OCR progresses. Last line (step=done) has the full results.
Read each line and display progress to the user. See caremax-ocr skill for details.

### auth-flow.sh — One-shot full authorization (opens browser + auto-polls)

```bash
# Default (production)
bash ~/.claude/skills/caremax-auth/scripts/auth-flow.sh

# Custom base URL (localhost / staging)
bash ~/.claude/skills/caremax-auth/scripts/auth-flow.sh http://localhost:8788
```

This script does EVERYTHING in one shot:
1. Requests device code from the API
2. Opens the user's browser to the authorize page
3. **Automatically polls every 5 seconds** until the user approves (up to 15 min)
4. Saves token to `~/.caremax/credentials.json`

Output when done: `{"status":"authorized","access_token":"sk-caremax-...","base_url":"..."}`

**Run this in the background** so you can tell the user what's happening while it polls:
```bash
bash ~/.claude/skills/caremax-auth/scripts/auth-flow.sh &
```
Then tell the user: "I've opened the authorization page in your browser. Please log in and click Allow. I'll detect it automatically."

Wait for the background job to finish — it will output the result.

### check-token.sh — Check token status (used internally by api-call.sh)

```bash
bash ~/.claude/skills/caremax-auth/scripts/check-token.sh
```

Output: `{"status":"valid"|"expired"|"missing", ...}`

### refresh-token.sh — Refresh expired token (used internally by api-call.sh)

```bash
bash ~/.claude/skills/caremax-auth/scripts/refresh-token.sh
```

## Standard Workflow

### Query data
```
User asks about health data
  → run: api-call.sh GET /api/skill/xxx
      ├── token valid → returns data → done
      ├── token expired → auto-refreshes → returns data → done
      └── no token → returns error
          → run: auth-flow.sh (background)
          → tell user "please authorize in browser"
          → auth-flow.sh auto-polls and saves token
          → retry: api-call.sh → returns data → done
```

### Upload + OCR (save medical reports from images)

This is an **interactive multi-step workflow**. The agent MUST show progress, present results for review, and wait for user confirmation before saving.

#### Step 1: Upload
```bash
bash ~/.claude/skills/caremax-auth/scripts/upload.sh /path/to/image.jpg
```
Returns `{ files: [{ id, member_id, ... }] }`. Save `id` as `fileId`, `member_id` as `memberId`.

Tell the user: "文件已上传，正在识别中..."

#### Step 2: OCR (with real-time progress)
```bash
bash ~/.claude/skills/caremax-auth/scripts/ocr-stream.sh '{"fileIds":["<fileId>"],"memberId":"<memberId>"}'
```

**CRITICAL: Relay progress to the user in real-time.** Parse each output line and show status:
- `step=normalize` → "正在预处理文件..."
- `step=ocr` → "正在 OCR 识别第 X/Y 页..."
- `step=structure` → "AI 正在分析报告结构..."
- `step=normalize_indicators` → "正在标准化指标名称..."
- `step=done` → OCR complete, proceed to review

#### Step 3: Present results for user review (MANDATORY)

**Do NOT call /ocr/confirm automatically.** You MUST present the results and wait for user to say "确认" or similar.

Parse the final `step=done` data and display a formatted summary:

```
识别到 N 份报告：

📋 报告 1: {report_title}
   日期: {test_date}  医生: {doctor}  科室: {department}
   病历号: {case_number}
   ┌──────────────────┬────────┬────────┬──────────┬──────┐
   │ 指标名称         │ 结果   │ 单位   │ 参考范围 │ 异常 │
   ├──────────────────┼────────┼────────┼──────────┼──────┤
   │ xxx              │ 1.23   │ mg/L   │ 0-5      │      │
   │ yyy              │ 9.99   │ mmol/L │ 1-8      │  ⬆   │
   └──────────────────┴────────┴────────┴──────────┴──────┘
   标准化映射: {name} → {canonical_name}

📋 报告 2: ...
```

#### Step 3a: Handle ambiguous indicator mappings

If the OCR response contains `ambiguousIndicators` (confidence < 0.8), you MUST ask the user to resolve each one:

```
⚠️ 以下指标的标准化映射不确定，请确认：

1. 「蛋白」(报告1, 第3项)
   当前映射: 总蛋白 (置信度: 0.6)
   候选项:
     A) 总蛋白 — 通常在肝功能检查中出现
     B) 白蛋白 — 也简称为蛋白
     C) 尿蛋白 — 在尿检中常见
   请选择 A/B/C: ___
```

After the user selects, update the corresponding indicator's `canonical_id` and `canonical_name` in the reports data.

#### Step 3b: Wait for final confirmation

After presenting all reports (and resolving any ambiguities), ask:
```
以上数据是否正确？确认后将保存到数据库。请说「确认」保存，或告诉我需要修改的地方。
```

**Only proceed to Step 4 after the user explicitly confirms** (says 确认、保存、OK、没问题, etc.)

If the user requests corrections, modify the reports data accordingly and re-present the updated summary.

#### Step 4: Confirm and save
```bash
bash ~/.claude/skills/caremax-auth/scripts/api-call.sh POST /api/skill/ocr/confirm '<JSON>'
```

**IMPORTANT**: The confirm payload MUST include `fileId`:
```json
{
  "reports": [...],
  "fileId": "<fileId from step 1>",
  "memberId": "<memberId>"
}
```

This ensures:
- The upload placeholder record ("待解析的报告") is cleaned up
- All reports are linked to the source file
- `files.is_processed` is set to 1

After success, tell the user: "已保存 N 份报告。"
