# CareMax Health — Copilot Instructions

When working with health data, medical reports, or the CareMax platform, follow these guidelines.

## Authentication

Use the scripts in `skills/caremax-auth/scripts/` (OAuth device flow). Do not invent curl.

1. `bash skills/caremax-auth/scripts/auth-flow.sh` opens the browser and polls `POST /api/auth/device/token`
2. Tokens are stored in `~/.caremax/credentials.json`
3. `api-call.sh` sends `Authorization: Bearer` and refreshes on expiry or HTTP 401 `invalid_token`

## API Usage

- Base URL: `https://api.caremax.ai` (or `base_url` in the credentials file)
- Skill proxies: `/api/skill/*`
- The same token is valid on the app routes the scripts call
- Contracts: `skills/caremax-auth/references/http-contracts.md`

## Common Workflows

### Health Q&A (健康问答)
```
skills/caremax-auth/scripts/chat-stream.sh --question "..."
```
SSE events: `status`, `sources`, `delta`, `citations`, `done`, `error`.
A cited report follows saved `has_abnormality` (nonzero abnormal, 0/false not, null unset). Do not infer from summary text.

### Indicators
```
GET /api/skill/indicators
GET /api/skill/indicators/categories
GET /api/skill/indicators/trend?id={uuid}&memberId={uuid}
```
Quick log: `list-system-presets.sh` then `quick-log.sh`. List source is `GET /api/indicators?category=common_indicator`.

### Records
```
POST /api/skill/records/query    searchText, dateRange, indicatorName, reportTitle, recordId, memberId
```
There is no `/records/search`. Updating a saved report is `POST /api/records` (`save-reports.sh --update`), not session confirm.

### Upload and OCR
```
upload.sh [--member id] file...
ocr-stream.sh <session_id>          # HTTP 202 JSON on the current API
session-status.sh <session_id>
save-reports.sh --session <id> --file confirm.json
```
Unfinished: `sessions-list.sh unfinished`. All history: `sessions-list.sh history --page 1 --limit 20` with no status filter.

### Family members
```
GET /api/skill/members
```
Responses use `isDefault` and `birthDate`. Do not delete the default member.

## Best Practices

- Get the indicator UUID before requesting a trend
- Display values with units and reference ranges
- Do not confirm a completed session and do not confirm an indicator report with zero indicators
- Do not document admin or payment routes in this repo
