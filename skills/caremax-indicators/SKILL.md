---
name: caremax-indicators
description: "Query and track health indicators from CareMax Health API. Use when a user asks about health metrics, lab results, indicator trends, blood test values, quick manual vitals entry, or wants to view health data over time. Trigger terms: health indicator, lab result, blood test, creatinine, blood sugar, cholesterol, hemoglobin, trend, health metric, indicator category, health data, quick log, vital log, 血常规, 肌酐, 血糖, 胆固醇, 指标, 趋势, 快捷记一笔, 快速记录."
license: MIT
---

# CareMax Health Indicators

> **Requires `caremax-auth` skill.** All scripts (api-call.sh, auth-flow.sh, etc.) live in caremax-auth. If missing, tell the user: "Please install caremax-auth first: `npx skills add KittenYang/caremax-skills` and select caremax-auth."

This skill covers querying health indicators, viewing trends over time, browsing indicator categories, and **quick single-point logging** (same flow as the app “快捷记一笔”).

## Prerequisites — Auto-Auth (MANDATORY)

All API calls below use `api-call.sh` from the caremax-auth skill. It handles token check + refresh automatically.

```bash
# shorthand used in all examples below
APICALL="bash ~/.claude/skills/caremax-auth/scripts/api-call.sh"
```

If `api-call.sh` returns `{"error":"no_credentials",...}` → **immediately run `bash ~/.claude/skills/caremax-auth/scripts/auth-flow.sh [base_url]`** in background. If the user specified a custom URL (e.g., `http://localhost:8788`), pass it as the argument. It opens the browser and auto-polls. Tell the user "please authorize in browser". Once it outputs `authorized`, retry the api-call.

## List All Indicators

```bash
$APICALL GET /api/skill/indicators
# with category filter:
$APICALL GET "/api/skill/indicators?category=血常规"
```

Response fields: `id` (UUID, needed for trend), `canonical_name`, `display_name`, `canonical_unit`, `category`, `latest_value`, `data_count`

## Get Indicator Categories

```bash
$APICALL GET /api/skill/indicators/categories
```

## Get Indicator Trend

**Important**: Get the indicator UUID from the list endpoint first.

```bash
$APICALL GET "/api/skill/indicators/trend?id={indicator_uuid}"
```

Returns time-series: `date`, `value`, `unit`, `reference_range`, `is_abnormal` (0/1)

## System presets & quick log (快捷记一笔)

**End-user OAuth token only** (`api-call.sh`). These are **not** `/api/skill/*` routes; they live under `/api/indicators/*` and power the in-app chip row for fast vitals.

### List active system presets (read-only)

```bash
$APICALL GET /api/indicators/system-presets
```

Response: `presets[]` with `id`, `preset_key`, `display_name`, `canonical_unit`, `category`, etc. Use `preset_key` when posting a quick log.

### Append one data point from a preset

```bash
$APICALL POST /api/indicators/quick-log '{
  "preset_key": "weight",
  "value": "72.5",
  "unit": "kg",
  "test_date": "2026-03-28",
  "member_id": "optional-family-member-uuid"
}'
```

- `preset_key` and `value` are required; `unit` defaults from the preset if omitted; `test_date` defaults to today (server local date logic).
- `member_id` optional — same semantics as other family-scoped APIs when recording for another profile.
- Creates/uses the user’s canonical indicator derived from the system preset and saves one indicator row (report title “快速记录”).

## Get Trends by Category

```bash
$APICALL GET "/api/skill/indicators/trends-by-category?category={category_name}"
```

## Recommended Workflow

When user asks "show my creatinine trend":

```bash
# 1. List all indicators, find the matching one
$APICALL GET /api/skill/indicators
# 2. Extract the id (UUID) of the matching indicator from the response
# 3. Get trend data
$APICALL GET "/api/skill/indicators/trend?id={uuid}"
# 4. Present with dates, values, units, highlight abnormals
```

When user asks "what are my abnormal indicators":

```bash
# 1. Get all indicators
$APICALL GET /api/skill/indicators
# 2. Filter response for those with abnormal latest values
# 3. Present with values and reference ranges
```

## Display Guidelines

- Always show values with units (e.g., "98 μmol/L" not just "98")
- Include reference ranges when available
- Flag abnormal values clearly
- For trends, show dates in chronological order
- Chinese indicator names are standard — display them as-is
