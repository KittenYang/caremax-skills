---
name: caremax-indicators
description: "Query and track health indicators from CareMax Health API. Use when a user asks about health metrics, lab results, indicator trends, blood test values, or wants to view health data over time. Trigger terms: health indicator, lab result, blood test, creatinine, blood sugar, cholesterol, hemoglobin, trend, health metric, indicator category, health data."
license: MIT
---

# CareMax Health Indicators

This skill covers querying health indicators, viewing trends over time, and browsing indicator categories. Health indicators are structured lab test results extracted from medical reports via OCR.

## List All Indicators

Returns the user's complete indicator dictionary with latest values and data point counts.

```http
GET /api/skill/indicators
Authorization: Bearer sk-caremax-...
```

Optional query parameter: `?category=blood_routine` to filter by category.

Response includes:
- `id` — Indicator UUID (needed for trend queries)
- `canonical_name` — Standardized name
- `display_name` — User-customizable display name
- `canonical_unit` — Standard unit
- `category` — Category (e.g., blood routine, liver function, kidney function)
- `latest_value` — Most recent recorded value
- `data_count` — Number of historical data points

## Get Indicator Categories

```http
GET /api/skill/indicators/categories
Authorization: Bearer sk-caremax-...
```

Returns all available categories like: blood routine, liver function, kidney function, lipid panel, thyroid, urine, etc.

## Get Indicator Trend

**Important**: You need the indicator's UUID from the list endpoint first.

```http
GET /api/skill/indicators/trend?id={indicator_uuid}
Authorization: Bearer sk-caremax-...
```

Returns time-series data:
- `date` — Test date
- `value` — Indicator value
- `unit` — Unit
- `reference_range` — Normal range
- `is_abnormal` — 0 (normal) or 1 (abnormal)

## Get Trends by Category

View all indicators in a category at once:

```http
GET /api/skill/indicators/trends-by-category?category={category_name}
Authorization: Bearer sk-caremax-...
```

## Recommended Workflow

When a user asks "show my creatinine trend":

1. `GET /api/skill/indicators` — find the indicator matching "creatinine"
2. Extract its `id` (UUID)
3. `GET /api/skill/indicators/trend?id={uuid}` — get trend data
4. Present the data with dates, values, units, and highlight any abnormal readings

When a user asks "what are my abnormal indicators":

1. `GET /api/skill/indicators` — get all indicators
2. Filter for those with abnormal latest values
3. Present the abnormal indicators with their values and reference ranges

## Display Guidelines

- Always show values with their units (e.g., "98 umol/L" not just "98")
- Include reference ranges when available
- Flag abnormal values clearly
- For trends, show dates in chronological order
- Chinese indicator names are standard — display them as-is
