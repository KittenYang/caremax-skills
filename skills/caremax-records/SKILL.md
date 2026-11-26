---
name: caremax-records
description: "Query CareMax medical records and update an already saved report. Use for report lists and sort, record detail, natural-language record search, text versus indicator reports, the saved has_abnormality flag, report-card abnormal counts, and 报告总览. Conversational health Q&A belongs to caremax-chat. Trigger terms: medical record, check-up, 体检, 报告, 病历, 文字报告, 指标报告, 异常标记, 异常 0, 按更新日期, 按检查日期, update report, 保存记录, 编辑检测报告, 报告总览."
license: MIT
---

# CareMax medical records

> Requires sibling `caremax-auth`. If it is missing: `npx skills add KittenYang/caremax-skills`.

Search and list saved reports. For a back-and-forth health question, use **caremax-chat** (`chat-stream.sh`). Record search does not open a conversation and its `rag` blurb is not the 健康问答 transcript.

Contracts: [../caremax-auth/references/http-contracts.md](../caremax-auth/references/http-contracts.md).

## Prerequisites

```bash
APICALL="bash ../caremax-auth/scripts/api-call.sh"
SAVE="bash ../caremax-auth/scripts/save-reports.sh"
```

`no_credentials` → `bash ../caremax-auth/scripts/auth-flow.sh`.

## Query

`POST /api/skill/records/query`. There is no `/api/skill/records/search`.

```bash
# natural language (LIKE + vectors + a short rag answer)
$APICALL POST /api/skill/records/query '{"searchText":"肝功能","memberId":"<uuid>","page":1,"limit":20}'

# latest reports when the body has no filter
$APICALL POST /api/skill/records/query '{"memberId":"<uuid>","page":1,"limit":20}'

# structured
$APICALL POST /api/skill/records/query '{"dateRange":["2025-01-01","2025-12-31"],"memberId":"<uuid>"}'
$APICALL POST /api/skill/records/query '{"indicatorName":"肌酐","memberId":"<uuid>"}'
$APICALL POST /api/skill/records/query '{"reportTitle":"血常规","memberId":"<uuid>"}'

# one record, including sections for non-lab types
$APICALL POST /api/skill/records/query '{"recordId":"<uuid>"}'

# newest edits first (also upload_date or test_date)
$APICALL POST /api/skill/records/query '{"memberId":"<uuid>","sort":"updated_at","page":1,"limit":20}'
```

`searchText` returns `{type:"search", query, data, totalCount, semanticHits, rag}`. Show matching reports first. `rag.answer` is optional context, with `rag.citations`. Indicator queries return `{type:"indicator", data:[{date, value, unit, isAbnormal}]}` where `isAbnormal` is `is_abnormal === 1`.

`memberId` is camelCase. Omit it to use the default member.

## List order

Clients may send `sort` as `upload_date`, `test_date`, or `updated_at`. Each value is newer first. A tie breaks on `id` ascending so pages do not reshuffle.

Leave `sort` out, or send a blank or unknown value, and the unfiltered list, `dateRange`, and text query `q` stay on `test_date` descending (`q` also orders `id` ascending). A legal `sort` replaces that order on those three paths. `dateRange` still filters on `test_date`. `indicatorName`, `reportTitle`, `searchText`, and `recordId` ignore `sort`.

Every `data[]` item includes `updated_at` as an ISO-8601 string. A single `recordId` read includes it too. iOS maps the field to `updatedAt`. It is the last save of that report, not `test_date` and not the upload-session clock.

iOS adds 「按更新日期」 to the report-list sort menu. Web keeps 「按检查日期」 as the default and adds the same updated-date option. There is no separate ascending parameter.

## Report cards

On a report card, hide 「异常 0」 when the abnormal indicator count is 0. Show 「异常 N」 when that count is greater than 0. 「正常 N」, the color bar, and 「共 N 项」 stay, including a zero normal count. The report list and search results share this card. A card with no indicators keeps the whole footer hidden. The separate 「异常」 badge with no number still follows saved `has_abnormality`.

## Text vs indicator, and the abnormality flag

| Kind | Recognition | What to show |
|---|---|---|
| 指标报告 | `report_type` `lab`, or indicators on a report with no other type | Rows with value, unit, and that row's `reference_range`. A row is abnormal only when `is_abnormal` is 1 |
| 文字报告 | `imaging`, `genetic`, `pathology`, `other`, or sections/summary without a lab type | Summary and `sections[]`. Abnormality is the manual `has_abnormality` switch |

Record-level rule, same as the list and the editor switch:

- nonzero / true → abnormal
- 0 / false → not abnormal
- null → unset, and not abnormal

Do not classify a report from summary keywords. 「未见明显异常」 does not clear or set the flag. Chat analysis uses this same saved flag. `sources[].hasAbnormality` is only a mapping of it; current iOS paints the reference badge from this query, not from the card or the snippet. See caremax-chat. Production chat cards only map exact `1` to true, so prefer `has_abnormality` from this query when deciding.

The indicator dictionary has no shared normal range. Report detail shows each lab row's own `reference_range`. A single-indicator trend may draw a same-unit union of those ranges; that band does not recolor rows. See caremax-indicators.

`abnormal_count` on a session history row counts indicator rows with `is_abnormal = 1`. It is not a substitute for the record flag on a text report.

## Update a saved report

First-time save of an upload is session confirm (`caremax-ocr`, `save-reports.sh --session`). Changing a report that already has an id:

```bash
$SAVE --update --file /tmp/records.json
```

```json
{
  "member_id": "<member uuid>",
  "records": [{
    "id": "<existing record id>",
    "report_title": "总检综述与医生建议",
    "test_date": "2024-03-01",
    "has_abnormality": 0,
    "hospital": "",
    "indicators": []
  }]
}
```

`POST /api/records` updates when `id` already exists and inserts when it does not. Do not call `POST /sessions/:id/confirm` for this. Confirm on a completed session is either `Session already completed` (unmerged API) or a duplicate insert (production). In the app, edit and delete on the report list are a system-style left swipe.

Record detail edits from the top-right pencil. The single-indicator trend's 检查记录 list edits from its edit action. Both open 编辑检测报告, the same editor the list already uses. Saving is still this update.

## Report overview

When confirm or the editor is showing exactly one report, 报告总览 is that report's indicator catalog. The subtitle is the report name. Do not subtitle it 「共 1 份」. The catalog lists rows that have both a name and a value. With two or more reports, the overview stays one row per report, and choosing a row opens that report.

Count chips: while exactly one count chip is the active filter, that chip stays at full opacity and the other count chips use opacity 0.2. On the default 「全部」 view, every count chip stays at full opacity. 「全部」 clears the filter. It is not a count chip, and it stays fully opaque.

For a text report, write `has_abnormality` only from the user's switch (`1` or `0`). If they do not choose, omit it and tell them the server stores that omission as not abnormal (`0`), not as unset.

## Upload history is not this endpoint

未完成 and 全部任务 are `GET /api/skill/sessions` via `sessions-list.sh` in caremax-ocr. `records/query` reads saved `medical_records`, not in-progress upload sessions.
