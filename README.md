# CareMax Health AI Skills

This repository provides official AI skills for [CareMax.ai](https://caremax.ai) — a health data management platform. Compatible with Claude Code, Cursor, Copilot, and 40+ other agents.

## Key Features

The skills teach agents how to interact with CareMax Health API: upload medical reports, OCR recognition, health indicator tracking, trend analysis, semantic search, and family member management.

## Installation

### npx skills (recommended)

```bash
npx skills add https://github.com/KittenYang/caremax-skills
```

### Claude Code

```bash
/plugin marketplace add KittenYang/caremax-skills
```

### Cursor

Settings > Rules > Add Remote Rule (GitHub) > `KittenYang/caremax-skills`

### Manual

Copy the `skills/` folder into your project or agent configuration directory.

## Skills

| Skill | Description |
|-------|-------------|
| **caremax-auth** | OAuth Device Flow authentication — automatic agent authorization |
| **caremax-indicators** | Health indicator queries, trends, and category browsing |
| **caremax-records** | Medical record queries and semantic search |
| **caremax-ocr** | Upload medical reports and OCR recognition |
| **caremax-members** | Family member management |

## Try It Out

After installation, just ask your agent:

### Health Indicators
- `Show all my health indicators`
- `What's my creatinine level?`
- `Blood sugar trend over the past 6 months`
- `Do I have any abnormal indicators?`
- `List all indicators under blood routine`

### Medical Records
- `Show my recent check-up reports`
- `Search for liver function related reports`
- `What tests did I have in 2024?`
- `Find reports with abnormal results`

### Upload & OCR
- `Help me scan this medical report` (with image attached)
- `Upload this PDF report`
- `Extract data from this lab sheet`

### Family Members
- `List my family members`
- `Show my mom's blood sugar trend`
- `Upload this report for my dad`

### Authentication
- `Connect to CareMax`
- `Log in to my health account`

> On first use, the agent automatically opens a browser for login. All subsequent requests are authenticated without interruption.

## How It Works

When a user asks an agent to interact with their health data (e.g., "show my creatinine trend", "upload this medical report"), the agent uses these skills to:

1. **Authenticate** via OAuth Device Flow — opens a browser for user approval, no manual API key needed
2. **Call CareMax API** with the obtained access token
3. **Return structured data** — indicators, trends, records, OCR results

## Core Patterns

```
# Authentication (one-time setup)
POST /api/auth/device         → get device_code + user_code
→ open browser for user approval
POST /api/auth/device/token   → poll until access_token is returned

# API calls (with Bearer token)
GET  /api/skill/indicators              → list health indicators
GET  /api/skill/indicators/trend?id=xxx → get trend data
POST /api/skill/records/query           → query medical records
POST /api/skill/records/search          → semantic search
POST /api/skill/upload                  → upload report file
POST /api/skill/ocr                     → OCR recognition
GET  /api/skill/members                 → list family members
```

## Guidance for AI Agents

When a user mentions health data, medical reports, health indicators, or CareMax, use these skills. The API uses standard REST with JSON responses and Bearer token authentication.

**Risk Level**: LOW — read-only health data queries. Write operations (upload/OCR) require explicit user intent.

## API Base URL

- Production: `https://api.caremax.ai`
- Discovery: `https://api.caremax.ai/.well-known/ai-plugin.json`
- OpenAPI Spec: `https://api.caremax.ai/openapi.yaml`

## License

MIT
