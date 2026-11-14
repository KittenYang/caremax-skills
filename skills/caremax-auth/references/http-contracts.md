# CareMax HTTP contracts for agents

Source of truth checked against `health-tracker-backend` default branch, the iOS client on `health-ios` default branch, and the web client in `health-tracker`. Unmerged drafts are called out and are not production.

Base URL defaults to `https://api.caremax.ai`. Send `Authorization: Bearer <access_token>`.

User-app routes (`/api/sessions`, `/api/chat`, `/api/records`, `/api/indicators`, `/api/members`, `/api/query`) and skill proxies (`/api/skill/...`) accept the same OAuth access token. Prefer the script wrappers in `../scripts/` over hand-written curl.

## Authentication

| Call | Body |
|---|---|
| `POST /api/auth/device` | `{"client_id":"caremax-agent","scope":"read:indicators read:records read:members write:upload write:ocr search:records"}` |
| `POST /api/auth/device/token` | `{"device_code","grant_type":"device_code"}` while pending returns `authorization_pending` |
| `POST /api/auth/device/refresh` | `{"refresh_token","grant_type":"refresh_token"}` |

`api-call.sh` refreshes when the local `expires_at` is past, and once more if a call returns HTTP 401 with `invalid_token` or `token_expired`. HTTP 403 `insufficient_scope` is not refreshed.

## Health Q&A (健康问答)

`POST /api/skill/chat` proxies to `POST /api/chat`. Send `Accept: text/event-stream` or the server returns one JSON object **without** `sources`.

JSON body (camelCase):

```json
{
  "question": "这份报告异常吗",
  "conversationId": "optional-existing-id",
  "recordId": "optional-pinned-report",
  "memberId": "optional-member",
  "deepThinking": false,
  "retryUserMessageId": "only when the previous assistant turn is not complete"
}
```

SSE events, in order:

| event | data |
|---|---|
| `status` | `{stage:"accepted", requestId, conversationId, isNew, mode:"fast"\|"deep", userMessageId}` then `{stage:"retrieving"}` then `{stage:"generating"}` |
| `sources` | `{sources:[SourceCard]}` before tokens. One card per record id. |
| `thinking` | `{delta}` only when `deepThinking` is true |
| `delta` | `{delta}` answer text |
| `citations` | `{citations:[{index, source, relevance, quote, recordId?}]}` |
| `timing` | diagnostic; ignore if the shape changes |
| `done` | `{requestId, conversationId, messageId, userMessageId}` |
| `error` | `{error:"chat_failed"\|"answer_truncated", requestId}` |

`SourceCard`: `{id, title, date, snippet, hasAbnormality, matchType, indicators[]}`. `matchType` is `pinned`, `semantic`, `text`, or `fallback`. Each indicator is `{id, name, value, unit, isAbnormal}`.

Other chat routes:

- `GET /api/skill/chat/conversations?page&limit`
- `GET /api/skill/chat/conversations/:id` (messages may include `sources` and `citations`)
- `GET /api/skill/chat/messages/search?q=&page&limit&role&conversationId`
- `GET /api/skill/chat/history?page&limit` legacy flat Q&A pairs
- `GET /api/skill/chat/suggestions?recordId=`
- `DELETE /api/skill/chat/conversations/:id`, `DELETE /api/skill/chat/messages/:id`, `DELETE /api/skill/chat`

Pre-stream errors: 400 `question is required`; 404 `conversation_not_found`, `record_not_found`, `member_not_found`, `retry_not_found`.

### Cited-report abnormality

Whether a cited report is abnormal follows the user's saved `has_abnormality`. Same rule as the report list and the text-report editor switch:

| Saved `has_abnormality` | Meaning |
|---|---|
| nonzero, `true`, `"1"` | abnormal |
| `0`, `false`, `"0"` | not abnormal |
| `NULL`, blank, or a sentence | unset. Not abnormal |

Do not infer abnormality from `snippet`, summary, 「报告概览」, a precomputed digest, or the word 异常. 「未见明显异常」 is not a flag.

`indicators[].isAbnormal` is that row's saved `is_abnormal === 1`. A record flag can be false while one indicator row is abnormal. Say so separately. Do not promote the whole report to abnormal because of the row, and do not clear the row because the record flag is false.

Default branch vs unmerged draft:

- **Production chat cards** (`sources[].hasAbnormality`) use `Number(has_abnormality) === 1`. Exact `1` is true, `0` is false, `null` is null, and any other number (including `2`) is **false**. The model prompt on this branch does not include an 「异常标记」 line.
- **Unmerged backend draft** (health-tracker-backend PR 31) changes the card and the prompt to the nonzero rule above and tells the model not to reclassify from overview text. It is not production.
- **Unmerged iOS draft** (health-ios PR 48, in testing) draws the reference badge from `POST /query` `has_abnormality`, not from `sources[].hasAbnormality`.

When a raw `has_abnormality` is available from `POST /api/skill/records/query` or session detail, apply the nonzero rule even if the production card boolean disagrees. When only the card boolean exists, trust true/false/null and do not upgrade false or null because the snippet contains 异常.

## Upload tasks: unfinished vs all history

`GET /api/skill/sessions` (same handler as `GET /api/sessions`).

Query: `member_id` (snake_case), `page` (default 1), `limit` (default 20), `status` (one exact status). Response: `{sessions, total, page, limit}`.

| Product surface | Request |
|---|---|
| 未完成 / 上传待处理 | One GET **per** status: `uploading`, `queued`, `processing`, `awaiting_confirm`, `error`, and `saving`. Merge by session id. |
| 全部任务 / 全部 | `GET /api/skill/sessions?member_id&page&limit` with **no** `status`. Pull-to-refresh repeats page 1. Load-more increments `page` while `page * limit < total` and the page is full. |

`saving` is produced only by the unmerged async-confirm handler. On production the query returns an empty page. Including it does not turn history into the unfinished list.

These are different caches. An empty unfinished merge can sit beside a history page of `completed` sessions. Do not answer "未完成" with the unfiltered history call, and do not answer "全部" by concatenating only the unfinished statuses.

`completed` list rows include `reports[]` with `has_abnormality`, `indicator_count`, and `abnormal_count` (`is_abnormal = 1`). Other statuses return `reports: null`. Detail is `GET /api/skill/sessions/:id` → `{session:{files, ocr_result, reports}}`. `ocr_result` is present for `awaiting_confirm` and `error`.

## OCR

`POST /api/sessions/:id/ocr` with `{}`.

**Production:** HTTP 202 `{session_id, status, accepted, report_count}`. This is not an SSE progress stream. `accepted: true` means the job was queued. `accepted: false` with `queued`, `processing`, or `awaiting_confirm` means it is already running or ready; do not treat that as a 409.

| HTTP | Meaning |
|---|---|
| 202 | Accepted or already in flight |
| 400 `Session already completed` | Saved. Open the report. Do not OCR or confirm again |
| 400 `Session cancelled` | Cancelled |
| 403 `code=ocr_limit_exceeded` | Quota exhausted |
| 500 `code=enqueue_failed` | Queue failed; status rolled back |

The web client still sends `Accept: text/event-stream` and falls back when the body is JSON. `ocr-stream.sh` does the same: JSON 202 becomes one `step=accepted` object; a real SSE body is still printed line by line.

Poll `GET /api/skill/sessions/:id/status` → `{session_id, status, report_count, pipeline, error, is_stale, updated_at}`. `pipeline.completedStep` moves `normalize` → `ocr` → `structure` → done. When `awaiting_confirm`, `GET` the session and review `ocr_result`. If `processing` and `is_stale` is true, call OCR again; the pipeline resumes from the checkpoint. `uploading` with an `error` is a failed attempt, not a brand-new upload.

In-flight only (not production): HTTP 402 page quota, and `POST /api/sessions/:id/estimate`.

## Confirm vs update

First save of an upload session, while status is `awaiting_confirm` (or `error` on the unmerged handler):

`POST /api/skill/sessions/:id/confirm` body `{"reports":[{"record":{...},"reportType":"lab"|"imaging"|...,"sections":[...],"summary":"...","fullText":"...","sourcePages":["file.jpg"]}]}`.

**Production:** synchronous HTTP 200 `{"success":true,"message":"N report(s) saved","recordIds":[...]}`. This handler does **not** check for `completed`. Calling it again can insert another copy. Do not do that.

**Unmerged** (backend PR 27, iOS PR 48 testing builds): HTTP 202 `{"accepted":true,"status":"saving","session_id"}`. Already saving returns 202 `accepted:false`. Completed or cancelled returns HTTP 400 `{"error":"Session already completed"}`. Not ready returns 409. Empty indicator reports return 422. Poll status until `completed` or `error`. Do not call confirm again after 202 or after 400.

`save-reports.sh` reads status first:

| Status | Action |
|---|---|
| `awaiting_confirm` or `error` | POST confirm once |
| `saving` | Wait. Do not confirm again |
| `completed` or `cancelled` | Refuse with `Session already completed`. Do not POST confirm |
| anything else | Not ready |

Editing a report that already has a record id (iOS 「保存记录」 after the first save) is `POST /api/records`:

```json
{"records":[{"id":"<existing record id>","report_title":"...","test_date":"YYYY-MM-DD","has_abnormality":0,"indicators":[...]}],"member_id":"<member uuid>"}
```

An existing `id` updates that row. A new id inserts. Response: `{"success":true,"normalization":{...}}`.

## Text reports vs indicator reports

| Kind | How to tell | Abnormality |
|---|---|---|
| 指标报告 | `report_type` / `reportType` is `lab`, or the type is missing and the report has indicators | Each row uses `is_abnormal === 1`. The record flag still uses the nonzero rule when it is present. Do not confirm a lab report with zero indicators (in-flight API returns 422; production may still accept it). |
| 文字报告 | `imaging`, `genetic`, `pathology`, `other`, or prose/sections without a lab type | Manual switch. Ask the user. `1` abnormal, `0` not. Do not set `1` because the summary contains 异常. |

On both confirm (non-lab insert) and `POST /records`, omitting `has_abnormality` is stored as `0` (`value || 0`), which means not abnormal, not NULL. If the user has not chosen, say the mark is unset and do not invent `1`.

## Indicators and quick log

`/api/skill/indicators` proxies `/api/indicators`. Member scope query parameter is camelCase `memberId`. An unknown member is HTTP 400 `invalid_member_id` (it does not silently fall back to the default member).

- `GET /api/skill/indicators?category=&memberId=`
- `GET /api/skill/indicators/categories` → `{categories:[{category, label, count}]}`
- `GET /api/skill/indicators/trend?id=<uuid>&memberId=` → points use boolean `is_abnormal` (`=== 1`)
- `GET /api/skill/indicators/trends-by-category?category=&memberId=`
- Quick log: `GET /api/indicators?category=common_indicator`, then `POST /api/indicators/quick-log` with `preset_key` (the `canonical_name`) or `canonical_id`, plus `value`, optional `unit`, `test_date`, `member_id` (snake_case). `GET /api/indicators/system-presets` still returns `{deprecated:true, presets}` and is not the preferred list.

## Records query

There is no `/api/skill/records/search`. Natural language and structured filters are both:

`POST /api/skill/records/query` → `/api/query`.

Body fields are camelCase: `searchText`, `dateRange`, `indicatorName`, `reportTitle`, `recordId`, `memberId`, `page`, `limit`. With no filter, the latest reports are returned. `searchText` returns `{type:"search", data, semanticHits, rag}`. `rag.answer` is a search summary, not the multi-turn 健康问答 transcript. Use chat for a conversation.

`recordId` returns one record including `has_abnormality`, `report_type`, `summary`, `indicators`, and `sections` for non-lab types. Sections are omitted for `lab`.

## Members

`GET/POST /api/skill/members`, `GET/PUT/DELETE /api/skill/members/:id`.

Responses use camelCase: `isDefault`, `birthDate`, `userId`. Create body: `{name, gender, birthDate, relationship, isDefault}`. `relationship` values used by the product include `self`, `spouse`, `child`, `parent`, `sibling`, `other`. Deleting the default member returns HTTP 400 `不能删除默认会员`.

Indicator and record queries use `memberId`. Session list, upload, and quick-log use `member_id`. Chat uses `memberId`.

## Not for this skill pack

Do not call admin routes, payment callbacks, or APNs device registration. Those belong to the app and to operators. Page-quota billing and push notifications exist only on unmerged drafts; do not document them as production steps.
