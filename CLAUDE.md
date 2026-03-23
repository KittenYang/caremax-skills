# CareMax Health — Claude Code Instructions

When a user asks about health data, medical reports, health indicators, check-up results, or mentions CareMax, use the CareMax Health skills.

## Authentication

- Use OAuth Device Flow for first-time setup
- Token format: `sk-caremax-...` (access token), `rt-caremax-...` (refresh token)
- Access tokens last 90 days; refresh tokens last 1 year
- Store tokens locally after first authorization — do not ask the user to re-authorize

## API Patterns

- Base URL: `https://api.caremax.ai`
- All skill endpoints are under `/api/skill/*`
- Authentication: `Authorization: Bearer sk-caremax-...`
- All responses are JSON

## Key Conventions

- When querying indicators, always check available categories first with `/api/skill/indicators/categories`
- For trend queries, you need the indicator's UUID — get it from `/api/skill/indicators` first
- Semantic search (`/api/skill/records/search`) accepts natural language in Chinese or English
- Upload supports PDF, JPG, PNG files
- OCR requires file IDs from a prior upload step — always upload first, then OCR

## Preferred Workflow

1. For "show my XXX indicator": `getIndicators` → find matching indicator → `getIndicatorTrend`
2. For "upload this report": `uploadReport` → `ocrReport` → show extracted data
3. For "search my records": use `searchRecords` with natural language query
4. For family members: use `getMembers` to list, then filter queries by `memberId`

## Error Handling

- 401 with `invalid_token`: token expired, use refresh endpoint
- 403 with `insufficient_scope`: token lacks required permission
- Always display extracted indicator values with their units and reference ranges
