---
name: caremax-indicators
description: "Query CareMax health indicators and quickly log a daily vital. Use for indicator lists, categories, trends, each lab row's normal range, the same-unit hospital union band, 「我的指标」, the trend record list, and 快捷记一笔. Trigger terms: health indicator, lab result, trend, normal range, reference range, quick log, 指标, 趋势, 正常范围, 参考范围, 各医院标准不同, 我的指标, 检查记录, 编辑检测报告, 快捷记一笔, 记一笔, 身高, 体重, 血压."
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

List fields include `id` (required for trend), `canonical_name`, `display_name`, `canonical_unit`, `category`, `category_label`, `latest_value`, `latest_date`, `data_count`. The dictionary and the 「我的指标」 table have no normal-range column.

Categories are `{category, label, count}`. Pass the stored `category` key back as the filter, not the display label. The common set is stored as `common_indicator` (older rows may still say 日常体征). Its chip label is 「常用指标」, shortened to fit the chip and translated with the app language. A localized label such as "Common" is still saved as `common_indicator`. Custom category names stay exactly as the user saved them.

Trend points are chronological: `date`, `value`, `unit`, `reference_range`, `is_abnormal`. Here `is_abnormal` is a boolean and is true only when the stored row is `1`. That is the indicator row, not the report-level `has_abnormality` flag used by text reports and chat sources.

Show every value with its unit and that row's reference range.

The 检查记录 list on a single-indicator trend has an edit action next to 查看. That action opens 编辑检测报告 for the saved report on that row. Saving is `save-reports.sh --update` (`POST /api/records`). See caremax-records. Chat trend cards use this same indicator id and the saved `is_abnormal` flag. See caremax-chat.

## Normal range

The range lives on each lab result as `indicators.reference_range`. It is visible on the single-indicator trend (badge, green band, and history rows) and on report detail. History rows and a point callout keep that result's own range and hospital. The badge and the green band use the merged interval below.

Name normalization still groups results onto one standard indicator. Values try to convert to that indicator's standard unit.

On one trend, ranges merge only after they are converted onto the chart unit. The merge is the widest interval any of those hospitals treated as normal. 1.1–2.3 and 1.9–2.5 become 1.1～2.5. A one-sided range widens only that side. A `≤` or `≥` string the parser already stores as a closed interval (such as `≤2.8` as 0–2.8) joins as that closed interval. Missing or unparseable ranges stay out. Ranges whose units cannot convert onto the chart unit stay out. mg/dL is never plotted on a mmol/L axis.

Conversion is only unique-factor pairs of the same quantity, for example g/L↔mg/dL, mmol/L↔μmol/L, and 10^9/L↔10^3/μL. There is no per-analyte medical conversion table.

The band is the widest interval that was treated as normal at any of those hospitals. It is not a combined medical standard. Point color follows the saved `is_abnormal` flag. When at least two named hospitals contribute intervals that differ (bounds within about 0.5% count as the same), show 「各医院标准不同」, localized with the app language. The existing unit-mismatch warning is a separate notice.

## 「我的指标」

This screen has no gear button in the top-right. Member and account settings stay in 「我的」. Loading uses the same carrot skeleton as the report list.

## Quick log

```bash
$LIST_PRESETS
$QUICK_LOG weight 72.5 --unit kg --date 2026-03-28
$QUICK_LOG height 175 --member <family_member_uuid>
```

`list-system-presets.sh` calls `GET /api/indicators?category=common_indicator` and maps `canonical_name` to `preset_key`. Do not assume a fixed set of chips. `GET /api/indicators/system-presets` still works, is marked `deprecated`, and is not the script's source.

Built-in quick-log names follow the app language on screen. Save and match still use the Simplified Chinese identity (`canonical_name` / preset key, and the canonical unit). Custom names stay as saved. A Chinese unit phrase may be translated on the chip; write the canonical unit back when saving. See caremax-members for the language list.

`quick-log.sh` posts `{preset_key, value, unit?, test_date?, member_id?}`. `member_id` is snake_case on this route. The server stores a small report titled 快速记录 with `has_abnormality: 0`. Confirm the value, unit, date, and whose profile you wrote.

Equivalent calls:

```bash
$APICALL GET "/api/indicators?category=common_indicator"
$APICALL POST /api/indicators/quick-log '{"preset_key":"weight","value":"72.5","unit":"kg","test_date":"2026-03-28","member_id":"<uuid>"}'
```

`canonical_id` may replace `preset_key`.
