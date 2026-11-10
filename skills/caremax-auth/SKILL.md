---
name: caremax-auth
description: "OAuth Device Flow authentication and shared HTTP scripts for the CareMax Health API. Prerequisite for every other caremax-* skill. Use automatically when credentials are missing or expired, and for upload, OCR kick, session lists, chat SSE, confirm-or-update, quick log, and authenticated JSON calls. Trigger terms: caremax login, caremax auth, health API token, authorize caremax, connect health data."
license: MIT
---

# CareMax Authentication

## Critical rules

1. This skill is a silent prerequisite. Do not ask whether to authenticate. Run the flow.
2. Do not hand-write curl. Use the scripts below.
3. Run `./scripts/auth-flow.sh` for a full device login. Do not split device-code, browser, and poll into separate manual steps.
4. If the user gives a base URL (local dev defaults to `http://localhost:8788`), pass it: `bash ./scripts/auth-flow.sh http://localhost:8788`. Later scripts read `base_url` from `~/.caremax/credentials.json`.

## Paths

- From this skill's directory: `./scripts/<name>.sh`.
- From a sibling `caremax-*` skill: `../caremax-auth/scripts/<name>.sh`.
- Credentials stay at `~/.caremax/credentials.json` (override with `CAREMAX_CREDENTIALS_FILE` only in tests).

HTTP shapes, status codes, and the production-vs-draft notes live in [references/http-contracts.md](./references/http-contracts.md).

## Scripts

### api-call.sh

```bash
bash ./scripts/api-call.sh GET /api/skill/indicators
bash ./scripts/api-call.sh POST /api/skill/records/query '{"searchText":"肝功能"}'
bash ./scripts/api-call.sh GET "/api/skill/indicators/trend?id=<uuid>&memberId=<member>"
```

Locally expired tokens refresh first. A response of HTTP 401 `invalid_token` or `token_expired` refreshes once and retries. `{"error":"no_credentials"}` means run `./scripts/auth-flow.sh`.

### auth-flow.sh

```bash
bash ./scripts/auth-flow.sh
bash ./scripts/auth-flow.sh http://localhost:8788
```

Requests a device code, opens the browser, polls until approval, and writes the token. Tell the user the authorization page is open. `CAREMAX_SKIP_BROWSER=1` skips the browser launch.

### check-token.sh / refresh-token.sh

Used by the other scripts. `check-token.sh` prints `valid`, `expired`, or `missing`. `refresh-token.sh` posts to `/api/auth/device/refresh` and stores a rotated refresh token when the server sends one.

### upload.sh

```bash
bash ./scripts/upload.sh /path/to/report.jpg /path/to/report.pdf
bash ./scripts/upload.sh --member <member_uuid> /path/to/report.jpg
```

`POST /api/sessions/upload` multipart field `files` (repeatable) and optional `member_id`. Returns `{session_id, member_id, files:[{id, original_name, mime_type, size}]}`.

### ocr-kick.sh and ocr-stream.sh

Production OCR is `POST /api/sessions/:id/ocr` → **HTTP 202** `{session_id, status, accepted, report_count}`. It is not a live SSE progress stream.

```bash
bash ./scripts/ocr-kick.sh <session_id>
bash ./scripts/session-status.sh <session_id>
```

`ocr-stream.sh` is the same kick. It prints one `step=accepted` object for JSON 202, or `step=error` for HTTP 400 `Session already completed`, 403 `ocr_limit_exceeded`, and other failures. If a server still returns `text/event-stream`, each SSE data payload is printed as its own line.

After `accepted`, poll status until `awaiting_confirm`, then fetch the session. If `is_stale` is true, kick again (checkpoint resume). Do not kick a `completed` session.

### sessions-list.sh

```bash
bash ./scripts/sessions-list.sh unfinished --member <member_uuid>
bash ./scripts/sessions-list.sh history --member <member_uuid> --page 1 --limit 20
bash ./scripts/sessions-list.sh status awaiting_confirm --member <member_uuid>
```

`unfinished` (上传待处理) sends one `GET /api/skill/sessions?status=` per in-progress status and merges them. `history` (全部任务) omits `status` and is paginated. Do not substitute one for the other. `has_more` is false on a short page or when `page * limit >= total`.

### chat-stream.sh

```bash
bash ./scripts/chat-stream.sh --question "我的肾功能怎么样" --member <member_uuid>
bash ./scripts/chat-stream.sh --question "这份呢" --conversation <id> --record <record_id>
```

Sends `Accept: text/event-stream` to `POST /api/skill/chat`. Prints `{"event","data"}` per SSE frame (`status`, `sources`, `thinking`, `delta`, `citations`, `done`, `error`). Read [the abnormality rule](./references/http-contracts.md#cited-report-abnormality) before calling a cited report abnormal. The non-stream JSON response has no `sources`.

### save-reports.sh

```bash
# first save, session still awaiting_confirm
bash ./scripts/save-reports.sh --session <session_id> --file /tmp/confirm.json
# edit an already saved report
bash ./scripts/save-reports.sh --update --file /tmp/records.json
```

The script reads session status and will not POST confirm when the session is `completed`, `cancelled`, or `saving`. A 202 `saving` body or a 400 `Session already completed` is not retried. Updates go to `POST /api/records`. Confirm JSON is `{"reports":[...]}`. Update JSON is `{"records":[...],"member_id":"..."}` and must include the existing record `id`.

### download-file.sh

```bash
bash ./scripts/download-file.sh <file_id> /tmp/report.jpg
```

`GET /api/sessions/file-content/:id`.

### list-system-presets.sh / quick-log.sh

```bash
bash ./scripts/list-system-presets.sh
bash ./scripts/quick-log.sh weight 72.5 --unit kg --date 2026-03-29 --member <member_uuid>
```

Presets come from `GET /api/indicators?category=common_indicator` (`preset_key` is `canonical_name`). Quick log is `POST /api/indicators/quick-log`.

## Workflow

1. Query, upload, chat, or quick-log through these scripts.
2. `no_credentials` or a failed refresh → `./scripts/auth-flow.sh [base_url]` in the background, tell the user to approve in the browser, then retry.
3. For upload, kick OCR in the same turn unless the user explicitly asked to store the file only. Review before confirm. Never confirm a session that is already `completed`.
