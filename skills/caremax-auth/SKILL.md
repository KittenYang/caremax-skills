---
name: caremax-auth
description: "OAuth Device Flow authentication for CareMax Health API. This skill is a PREREQUISITE for all other caremax-* skills — invoke it automatically when no token is found. Do NOT ask the user, just run the auth flow. Trigger terms: caremax login, caremax auth, health API token, authorize caremax, connect health data, health indicator, blood test, medical record, upload report."
license: MIT
---

# CareMax Authentication

## CRITICAL RULES

1. This is a **silent prerequisite** for ALL caremax-* skills. Do NOT ask "do you want to authenticate?" — just execute.
2. **NEVER write your own curl commands**. Only use the scripts below.
3. **NEVER split auth into multiple steps manually**. Use `auth-flow.sh` — it opens browser AND auto-polls until done.

## Scripts

All scripts are at `~/.claude/skills/caremax-auth/scripts/`.

### api-call.sh — Make authenticated API calls (PRIMARY TOOL)

This is what you should use for all API calls. It auto-checks token, auto-refreshes if expired.

```bash
bash ~/.claude/skills/caremax-auth/scripts/api-call.sh GET /api/skill/indicators
bash ~/.claude/skills/caremax-auth/scripts/api-call.sh POST /api/skill/records/search '{"query":"血常规"}'
bash ~/.claude/skills/caremax-auth/scripts/api-call.sh GET "/api/skill/indicators/trend?id=xxx"
```

If it returns `{"error":"no_credentials",...}` → run `auth-flow.sh` (see below), then retry.

### auth-flow.sh — One-shot full authorization (opens browser + auto-polls)

```bash
bash ~/.claude/skills/caremax-auth/scripts/auth-flow.sh
```

This script does EVERYTHING in one shot:
1. Requests device code from the API
2. Opens the user's browser to the authorize page
3. **Automatically polls every 5 seconds** until the user approves (up to 15 min)
4. Saves token to `~/.caremax/credentials.json`

Output when done: `{"status":"authorized","access_token":"sk-caremax-...","base_url":"..."}`

**Run this in the background** so you can tell the user what's happening while it polls:
```bash
bash ~/.claude/skills/caremax-auth/scripts/auth-flow.sh &
```
Then tell the user: "I've opened the authorization page in your browser. Please log in and click Allow. I'll detect it automatically."

Wait for the background job to finish — it will output the result.

### check-token.sh — Check token status (used internally by api-call.sh)

```bash
bash ~/.claude/skills/caremax-auth/scripts/check-token.sh
```

Output: `{"status":"valid"|"expired"|"missing", ...}`

### refresh-token.sh — Refresh expired token (used internally by api-call.sh)

```bash
bash ~/.claude/skills/caremax-auth/scripts/refresh-token.sh
```

## Standard Workflow

```
User asks about health data
  → caremax-indicators/records/ocr/members skill loads
  → run: api-call.sh GET /api/skill/xxx
      ├── token valid → returns data → done
      ├── token expired → auto-refreshes → returns data → done
      └── no token → returns error
          → run: auth-flow.sh (background)
          → tell user "please authorize in browser"
          → auth-flow.sh auto-polls and saves token
          → retry: api-call.sh → returns data → done
```
