---
name: caremax-admin
description: "Operate CareMax admin APIs for system_indicator_presets (CRUD + aliases). Use when an operator needs to configure built-in indicator presets, admin login, or backend-only preset management — not for end-user OAuth. Trigger terms: admin caremax, system preset, system_indicator_presets, CAREMAX_ADMIN, 管理后台, 内置指标, 系统指标库, 指标预设管理."
license: MIT
---

# CareMax Admin — System indicator presets

This skill is for **operators / deployers** who control the Worker environment. It is **separate** from `caremax-auth` (OAuth Device Flow for end users).

## Authentication model

- **User APIs:** `caremax-auth` → `api-call.sh` → Bearer **user** JWT.
- **Admin APIs:** username + password from server secrets → Bearer **admin** JWT (different payload / role).

Server must define:

- `CAREMAX_ADMIN_USER`
- `CAREMAX_ADMIN_PASSWORD`

(Local dev: `.dev.vars` for Wrangler.)

If unset, `POST /api/admin/auth/login` returns **503** with `admin_not_configured`.

## Admin login (get token)

Replace `BASE`, user, and password. **Do not** commit real credentials into repos or chat logs.

```bash
BASE="https://api.caremax.ai"   # or http://localhost:8788 for local Worker

RESP=$(curl -s -X POST "${BASE}/api/admin/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"YOUR_ADMIN_USER","password":"YOUR_ADMIN_PASSWORD"}')

ADMIN_TOKEN=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))")
# If ADMIN_TOKEN is empty, print RESP and fix credentials or env.
```

Use `Authorization: Bearer $ADMIN_TOKEN` for all routes below. **Never** use the user OAuth token from `credentials.json` on `/api/admin/*` — the Worker rejects it.

## List all presets (including inactive)

```bash
curl -s "${BASE}/api/admin/system-presets" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

Response: `{ "presets": [ ... ] }` — each row includes aliases, `is_active`, sort order, etc.

## Create preset

```bash
curl -s -X POST "${BASE}/api/admin/system-presets" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "optional-custom-id",
    "preset_key": "body_fat_pct",
    "display_name": "体脂率",
    "display_name_en": "Body fat",
    "canonical_unit": "%",
    "category": "体成分",
    "sort_order": 120,
    "is_active": 1,
    "aliases": ["体脂", "脂肪率"]
  }'
```

## Update preset

```bash
curl -s -X PUT "${BASE}/api/admin/system-presets/{preset_row_id}" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "体脂率",
    "canonical_unit": "%",
    "sort_order": 110,
    "is_active": 1,
    "aliases": ["体脂", "脂肪率"]
  }'
```

(`preset_row_id` is the primary key `id` in `system_indicator_presets`, not necessarily the same as `preset_key`.)

## Soft-delete (deactivate)

```bash
curl -s -X DELETE "${BASE}/api/admin/system-presets/{preset_row_id}" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

## Relationship to user-facing “快捷记一笔”

- The app loads **active** presets via `GET /api/indicators/system-presets` (user JWT).
- Quick log posts to `POST /api/indicators/quick-log` with `preset_key` (see `caremax-indicators` skill).
- Admin changes affect which chips appear after presets are created/activated; user UI intentionally avoids internal scroll boxes on small screens (full page scrolls).

## Errors

- **401** `admin_auth_required` — missing or invalid admin JWT.
- **503** `admin_not_configured` — env credentials not set on the Worker.
