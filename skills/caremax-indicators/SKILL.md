---
name: caremax-indicators
description: "Query CareMax health indicators and quickly log a daily vital. Use for indicator lists, categories, trends, and 快捷记一笔 (weight, blood pressure, and whatever presets the account currently returns). Trigger terms: health indicator, lab result, trend, quick log, 指标, 趋势, 快捷记一笔, 记一笔, 身高, 体重, 血压."
license: MIT
---

# CareMax health indicators

> Requires sibling `caremax-auth`. If it is missing: `npx skills add KittenYang/caremax-skills`.

Browse saved indicators and add one daily reading without uploading a report. The reading is the in-app 「快捷记一笔」 action.

Contracts: [../caremax-auth/references/http-contracts.md](../caremax-auth/references/http-contracts.md).

## Prerequisites

```bash
APICALL="bash ../caremax-auth/scripts/api-call.sh"
LIST_PRESETS="bash ../caremax-auth/scripts/list-system-presets.sh"
QUICK_LOG="bash ../caremax-auth/scripts/quick-log.sh"
```

`no_credentials` → `bash ../caremax-auth/scripts/auth-flow.sh`.

## List, categories, trend

Member scope uses camelCase `memberId`. A wrong id returns HTTP 400 `invalid_member_id` instead of the default member's data.

```bash
$APICALL GET "/api/skill/indicators?memberId=<uuid>"
$APICALL GET "/api/skill/indicators?category=common_indicator&memberId=<uuid>"
$APICALL GET /api/skill/indicators/categories
$APICALL GET "/api/skill/indicators/trend?id=<indicator_uuid>&memberId=<uuid>"
$APICALL GET "/api/skill/indicators/trends-by-category?category=<category>&memberId=<uuid>"
```

List fields include `id` (required for trend), `canonical_name`, `display_name`, `canonical_unit`, `category`, `category_label`, `latest_value`, `latest_date`, `data_count`.

Categories are `{category, label, count}`. Pass the stored `category` key back as the filter, not the display label.

Trend points are chronological: `date`, `value`, `unit`, `reference_range`, `is_abnormal`. Here `is_abnormal` is a boolean and is true only when the stored row is `1`. That is the indicator row, not the report-level `has_abnormality` flag used by text reports and chat sources.

Show every value with its unit and reference range.

## Quick log

```bash
$LIST_PRESETS
$QUICK_LOG weight 72.5 --unit kg --date 2026-03-28
$QUICK_LOG height 175 --member <family_member_uuid>
```

`list-system-presets.sh` calls `GET /api/indicators?category=common_indicator` and maps `canonical_name` to `preset_key`. Do not assume a fixed set of chips. `GET /api/indicators/system-presets` still works, is marked `deprecated`, and is not the script's source.

`quick-log.sh` posts `{preset_key, value, unit?, test_date?, member_id?}`. `member_id` is snake_case on this route. The server stores a small report titled 快速记录 with `has_abnormality: 0`. Confirm the value, unit, date, and whose profile you wrote.

Equivalent calls:

```bash
$APICALL GET "/api/indicators?category=common_indicator"
$APICALL POST /api/indicators/quick-log '{"preset_key":"weight","value":"72.5","unit":"kg","test_date":"2026-03-28","member_id":"<uuid>"}'
```

`canonical_id` may replace `preset_key`.
