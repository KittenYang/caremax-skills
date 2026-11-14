# CareMax Health — Claude Code Instructions

When a user asks about health data, medical reports, health indicators, check-up results, health Q&A, or mentions CareMax, use the CareMax Health skills.

## CRITICAL: Authentication is automatic — NEVER ask the user

When any caremax skill is triggered:
1. Read `~/.caremax/credentials.json`
2. If missing or expired → **silently run the caremax-auth Device Flow** (`bash ./scripts/auth-flow.sh` from `caremax-auth`, or `../caremax-auth/scripts/auth-flow.sh` from a sibling skill). Do NOT ask "do you want to authenticate?" — just do it.
3. If expired but has refresh_token → the shared scripts refresh silently, including one retry when the API returns 401 `invalid_token` or `token_expired`
4. Then proceed with the user's actual request

The user should never be interrupted with an authentication prompt. Auth is infrastructure, not a user action.

## Token Storage

Credentials are stored at `~/.caremax/credentials.json`:
```json
{
  "access_token": "sk-caremax-...",
  "refresh_token": "rt-caremax-...",
  "expires_at": "2026-09-15T00:00:00Z",
  "scope": "read:indicators read:records read:members write:upload write:ocr search:records",
  "base_url": "https://api.caremax.ai"
}
```

## Authentication Details

- Token format: `sk-caremax-...` (access token), `rt-caremax-...` (refresh token)
- Access tokens last 90 days; refresh tokens last 1 year
- After Device Flow completes, save tokens to `~/.caremax/credentials.json` immediately
- Do not hardcode tokens. Do not put tokens in the repo.

## API Patterns

- Base URL: `https://api.caremax.ai` unless `credentials.json` has another `base_url`
- Prefer `caremax-auth` scripts. Skill proxies live under `/api/skill/*`. The same bearer token also calls the app routes those scripts use (`/api/sessions`, `/api/chat`, `/api/records`, `/api/indicators`, `/api/query`)
- Authentication: `Authorization: Bearer sk-caremax-...`
- Field-level contracts: `skills/caremax-auth/references/http-contracts.md`

## Key Conventions

- Indicator categories: `GET /api/skill/indicators/categories`. Trend needs the indicator UUID from `GET /api/skill/indicators`. Member scope on those routes is `memberId`.
- Natural-language record search is `POST /api/skill/records/query` with `searchText`. There is no `/api/skill/records/search`.
- Health Q&A (健康问答) is `caremax-chat` / `chat-stream.sh` (`POST /api/skill/chat`, `Accept: text/event-stream`). A cited report is abnormal only from saved `has_abnormality`: nonzero abnormal, 0/false not, null unset. Do not infer from summary text or from the word 异常. Indicator rows use `is_abnormal === 1` on their own.
- Upload is `upload.sh` (multipart `files`, optional `member_id`). OCR is `POST /sessions/:id/ocr`, which returns HTTP 202 on the current API. Poll `session-status.sh`. Do not require an SSE progress stream.
- Unfinished uploads (`sessions-list.sh unfinished`) and all history (`sessions-list.sh history`) are different queries. History is paginated with `page` and `limit` and no status filter.
- Confirm a session only while it is awaiting review. HTTP 200 means production saved inline. HTTP 202 `saving` means wait and do not confirm again. `Session already completed` means stop. Editing a saved report is `save-reports.sh --update` (`POST /records`).
- Text reports use the manual abnormality switch. Indicator reports list lab rows. Do not confirm an indicator report that has zero indicators.
- Quick log: `list-system-presets.sh`, then `quick-log.sh`. Presets come from `GET /api/indicators?category=common_indicator`.

## Preferred Workflow

1. "show my XXX indicator": list indicators → match → `trend?id=`
2. "ask about my reports": `chat-stream.sh`, then apply the saved abnormality flag to `sources`
3. "upload this report": `upload.sh` → `ocr-stream.sh` → poll status → review → `save-reports.sh --session` after the user agrees
4. "what's still uploading" vs "all upload tasks": `sessions-list.sh unfinished` vs `sessions-list.sh history`
5. "change this saved report": `save-reports.sh --update`, not session confirm
6. "search my records": `POST /api/skill/records/query`
7. Family members: `GET /api/skill/members`, then pass that id with the parameter name the route expects

## Error Handling

- 401 `invalid_token` or `token_expired`: refresh once, then device flow if refresh fails
- 403 `insufficient_scope`: token lacks the required permission
- 400 `Session already completed`: do not retry confirm or OCR
- Show indicator values with units and reference ranges
