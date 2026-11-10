---
name: caremax-records
description: "Query CareMax medical records and update an already saved report. Use for report lists, record detail, natural-language record search, text versus indicator reports, and the saved has_abnormality flag. Conversational health Q&A belongs to caremax-chat. Trigger terms: medical record, check-up, 体检, 报告, 病历, 文字报告, 指标报告, 异常标记, update report, 保存记录."
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
```

`searchText` returns `{type:"search", query, data, totalCount, semanticHits, rag}`. Show matching reports first. `rag.answer` is optional context, with `rag.citations`. Indicator queries return `{type:"indicator", data:[{date, value, unit, isAbnormal}]}` where `isAbnormal` is `is_abnormal === 1`.

`memberId` is camelCase. Omit it to use the default member.

## Text vs indicator, and the abnormality flag

| Kind | Recognition | What to show |
|---|---|---|
| 指标报告 | `report_type` `lab`, or indicators on a report with no other type | Rows with value, unit, reference range. A row is abnormal only when `is_abnormal` is 1 |
| 文字报告 | `imaging`, `genetic`, `pathology`, `other`, or sections/summary without a lab type | Summary and `sections[]`. Abnormality is the manual `has_abnormality` switch |

Record-level rule, same as the list and the editor switch:

- nonzero / true → abnormal
- 0 / false → not abnormal
- null → unset, and not abnormal

Do not classify a report from summary keywords. 「未见明显异常」 does not clear or set the flag. Chat reference cards follow this same flag; see caremax-chat. Production chat cards only map exact `1` to true, so prefer `has_abnormality` from this query when deciding.

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

`POST /api/records` updates when `id` already exists and inserts when it does not. Do not call `POST /sessions/:id/confirm` for this. Confirm on a completed session is either `Session already completed` (unmerged API) or a duplicate insert (production).

For a text report, write `has_abnormality` only from the user's switch (`1` or `0`). If they do not choose, omit it and tell them the server stores that omission as not abnormal (`0`), not as unset.

## Upload history is not this endpoint

未完成 and 全部任务 are `GET /api/skill/sessions` via `sessions-list.sh` in caremax-ocr. `records/query` reads saved `medical_records`, not in-progress upload sessions.
