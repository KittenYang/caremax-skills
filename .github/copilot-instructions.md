# CareMax Health — Copilot Instructions

When working with health data, medical reports, or the CareMax platform, follow these guidelines.

## Authentication

Use OAuth Device Flow to authenticate with CareMax API:

1. `POST https://api.caremax.ai/api/auth/device` with `{ "client_id": "caremax-agent" }`
2. Open the returned `verification_uri_complete` in the user's browser
3. Poll `POST https://api.caremax.ai/api/auth/device/token` with the `device_code` every 5 seconds
4. Once approved, store the `access_token` (sk-caremax-...) for subsequent API calls

## API Usage

- Base URL: `https://api.caremax.ai`
- All skill endpoints: `/api/skill/*`
- Auth header: `Authorization: Bearer sk-caremax-...`
- Response format: JSON

## Common Workflows

### Query health indicators
```
GET /api/skill/indicators                    → list all indicators
GET /api/skill/indicators/categories         → list categories
GET /api/skill/indicators/trend?id={uuid}    → get trend data
```

### Search medical records
```
POST /api/skill/records/query   → filter by date, indicator, report title
POST /api/skill/records/search  → natural language semantic search
```

### Upload and OCR medical reports
```
POST /api/skill/upload  → upload file (multipart/form-data)
POST /api/skill/ocr     → OCR recognition (pass fileIds from upload)
```

### Family members
```
GET /api/skill/members  → list family members (use memberId to filter queries)
```

### User app — quick vitals (OAuth user token, not `/api/skill/*`)
```
GET  /api/indicators/system-presets   → active presets for “快捷记一笔” chips
POST /api/indicators/quick-log        → single data point (preset_key, value, optional member_id, test_date)
```

### Operator — system preset CRUD (separate admin JWT)
```
POST /api/admin/auth/login            → { username, password } from Worker env
GET|POST /api/admin/system-presets
PUT|DELETE /api/admin/system-presets/{id}
```
See skills `caremax-indicators` and `caremax-admin` in this repo.

## Best Practices

- Always get indicator UUID from `/api/skill/indicators` before querying trends
- Semantic search accepts Chinese and English natural language queries
- Upload supports PDF, JPG, PNG formats
- OCR is a two-step process: upload first, then OCR with the returned file IDs
- Display indicator values with units and reference ranges for clarity
