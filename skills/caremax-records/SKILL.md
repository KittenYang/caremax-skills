---
name: caremax-records
description: "Query and search medical records from CareMax Health API. Use when a user asks about medical reports, check-up history, hospital visits, test results, or wants to find specific records. Supports structured query and AI-powered semantic search. Trigger terms: medical record, check-up, hospital report, test result, health report, find report, search records, medical history."
license: MIT
---

# CareMax Medical Records

This skill covers querying and searching medical records. Records are structured data extracted from uploaded health reports, containing hospital info, department, indicators, and diagnosis.

## Query Records (Structured)

Filter records by specific criteria:

```http
POST /api/skill/records/query
Authorization: Bearer sk-caremax-...
Content-Type: application/json

{
  "dateRange": ["2025-01-01", "2025-12-31"],
  "indicatorName": "creatinine",
  "reportTitle": "blood routine",
  "memberId": "member-uuid",
  "page": 1,
  "limit": 20
}
```

All fields are optional. Common queries:
- By date range: `{ "dateRange": ["2025-06-01", "2025-06-30"] }`
- By indicator: `{ "indicatorName": "hemoglobin" }`
- By report type: `{ "reportTitle": "liver function" }`
- By family member: `{ "memberId": "..." }`

## Semantic Search (AI-Powered)

Natural language search across all medical records:

```http
POST /api/skill/records/search
Authorization: Bearer sk-caremax-...
Content-Type: application/json

{
  "query": "liver function abnormalities in the past year",
  "memberId": "member-uuid",
  "topK": 5
}
```

The search query accepts Chinese and English natural language. Examples:
- "recent blood routine reports"
- "any abnormal liver function results"
- "kidney function tests from last month"
- "all reports from Peking University Hospital"

## Response Structure

Each record contains:
- `id` — Record UUID
- `test_date` — When the test was performed
- `hospital` — Hospital name
- `doctor` — Doctor name
- `department` — Department (e.g., internal medicine, ophthalmology)
- `report_title` — Report type (e.g., blood routine, liver function panel)
- `has_abnormality` — Whether any indicator is abnormal (0/1)
- `diagnosis` — Diagnosis or notes
- `indicators[]` — Array of extracted indicators with name, value, unit, reference_range, is_abnormal

## Recommended Workflow

When a user asks "show my recent check-up results":
1. `POST /api/skill/records/query` with a recent date range
2. Present records grouped by date, showing report titles and key indicators

When a user asks "find reports with abnormal results":
1. `POST /api/skill/records/search` with query "abnormal indicators"
2. Highlight the abnormal indicators in each result

When a user asks a vague question like "how's my liver":
1. Use semantic search: `{ "query": "liver function" }`
2. Present the most relevant records with liver-related indicators
