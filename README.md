# CareMax Health AI Skills

Official AI skills for [CareMax.ai](https://caremax.ai) — a health data management platform. Compatible with Claude Code, Cursor, Copilot, and 40+ other agents.

## Installation

```bash
# npx skills (recommended)
npx skills add https://github.com/KittenYang/caremax-skills

# Claude Code
/plugin marketplace add KittenYang/caremax-skills

# Cursor
Settings > Rules > Add Remote Rule (GitHub) > KittenYang/caremax-skills
```

## Skills

> **caremax-auth is REQUIRED.** All other skills depend on its scripts for authentication and API calls. Install it first.

| Skill | Required | Description |
|-------|----------|-------------|
| **caremax-auth** | **YES** | OAuth Device Flow auth + all shared scripts (api-call, upload, ocr-stream, download) |
| **caremax-indicators** | no | Health indicator queries, trends, categories, and quick log (`/api/indicators/system-presets`, `quick-log`) |
| **caremax-records** | no | Medical record queries and semantic search |
| **caremax-ocr** | no | Session-based upload, OCR, review, and confirm |
| **caremax-members** | no | Family member management |
| **caremax-admin** | no | Operator-only: `system_indicator_presets` CRUD via `/api/admin/*` (env username/password, not OAuth) |

## Session-Based Architecture

CareMax uses a **session-centric** workflow — each upload creates a session that groups files and reports together:

```
upload (creates session)
  → OCR (processes all files in session, SSE progress)
    → review (agent shows results, user confirms)
      → confirm (atomically saves all reports)
```

One session can produce multiple reports (e.g., a long screenshot with 2 reports, or 3 images from the same check-up).

## Try It Out

After installation, just ask your agent:

### Upload & OCR
- `Help me scan this medical report` (with image attached)
- `Upload this PDF report`
- `Extract data from this lab sheet`

### Health Indicators
- `Show all my health indicators`
- `What's my creatinine level?`
- `Blood sugar trend over the past 6 months`
- `Do I have any abnormal indicators?`

### Medical Records
- `Show my recent check-up reports`
- `Search for liver function related reports`
- `Find reports with abnormal results`

### Family Members
- `Show my mom's blood sugar trend`
- `Upload this report for my dad`

### Session Management
- `Show my pending uploads`
- `Continue my last upload`
- `Delete that upload session`

## Scripts

All scripts are in `skills/caremax-auth/scripts/`:

| Script | Purpose |
|--------|---------|
| `auth-flow.sh [base_url]` | One-shot auth: browser + auto-poll + save token |
| `upload.sh <files...>` | Upload files → create session |
| `ocr-stream.sh <session_id>` | OCR with real-time SSE progress |
| `api-call.sh <method> <path> [body]` | Authenticated API call (auto-refresh) |
| `download-file.sh <file_id> [path]` | Download a source file |
| `check-token.sh` | Check token status |
| `refresh-token.sh` | Refresh expired token |

## Local Development

```bash
# Point to local backend
bash auth-flow.sh http://localhost:8788
# All subsequent calls auto-use localhost
```

## API

Endpoints, request/response shapes, and auth flows are defined in the **[OpenAPI specification](https://api.caremax.ai/openapi.yaml)** — use it as the single source of truth.

- Base URL (production): `https://api.caremax.ai`
- Plugin discovery: `https://api.caremax.ai/.well-known/ai-plugin.json`

## License

MIT
