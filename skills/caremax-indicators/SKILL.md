---
name: caremax-indicators
description: "Query and track health indicators from CareMax Health API. Use when a user asks about health metrics, lab results, trends, or wants to quickly log everyday vitals (e.g. height, weight, blood pressure — whatever presets the API returns for their account). Trigger terms: health indicator, lab result, blood test, trend, quick log, daily vitals, 指标, 趋势, 血常规, 血糖, 胆固醇, 快捷记一笔, 快速记录, 记一笔, 身高, 体重, 血压, 心率, 体温, 腰围."
license: MIT
---

# CareMax Health Indicators

> **Requires `caremax-auth` skill.** All scripts (api-call.sh, auth-flow.sh, etc.) live in caremax-auth. If missing, tell the user: "Please install caremax-auth first: `npx skills add KittenYang/caremax-skills` and select caremax-auth."

## What end users can do (plain language)

- **Browse and analyze** their saved indicators: lists, categories, trends over time (labs and long-term metrics).
- **Quickly add a single reading** for common day-to-day metrics — the same idea as the app’s **「快捷记一笔」**: pick a familiar item (often things like **身高、体重、血压、心率、体温、腰围**等，**具体有哪些以当前账号下列出的可选项为准**), enter a value and date, and it is stored like a normal indicator data point. No upload or report file required.

Agents should **describe this in user-friendly terms** (“帮你记一笔今天的体重”“看看现在能快捷记录哪些项目”) and only use the API steps below to implement it after the user is authenticated.

This skill also covers the **agent/skill** indicator endpoints under `/api/skill/indicators/*` for listing, categories, and trends.

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

## Quick log — same feature as 「快捷记一笔」 (authenticated user only)

Use the **same OAuth user token** as everywhere else (`api-call.sh`). This is for **normal users** logging everyday numbers, not for any privileged or server-side configuration.

**Typical user intents:** “记一下体重 70”“今天身高 175”“帮妈妈记血压 120/80” — always **first fetch the preset list** so you use a valid `preset_key` and optional `member_id` for family members.

### 1) List what the user can quick-log right now

Returns the active preset chips (display names + keys + default units). **Do not assume** a fixed list of metrics in prose; the API is the source of truth.

```bash
$APICALL GET /api/indicators/system-presets
```

Response: `presets[]` — use `preset_key` for the next call; show `display_name` / `canonical_unit` to the user when confirming.

### 2) Save one value

```bash
$APICALL POST /api/indicators/quick-log '{
  "preset_key": "weight",
  "value": "72.5",
  "unit": "kg",
  "test_date": "2026-03-28",
  "member_id": "optional-family-member-uuid"
}'
```

- Required: `preset_key`, `value`. `unit` can be omitted if the preset defines a default. `test_date` defaults to today if omitted.
- `member_id`: omit for the default profile; set when logging for another family member (same idea as other member-scoped calls).

### Recommended workflow (quick log)

```bash
# User: "帮我记身高" / "quick log my weight"
# 1) Show friendly names from presets
$APICALL GET /api/indicators/system-presets
# 2) Match user wording to the right preset_key (or ask which line if ambiguous)
# 3) POST quick-log with value (+ date / member if they specified)
$APICALL POST /api/indicators/quick-log '{"preset_key":"...","value":"...","test_date":"...","member_id":"..."}'
# 4) Confirm in natural language with value, unit, date, and whose profile
```

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
