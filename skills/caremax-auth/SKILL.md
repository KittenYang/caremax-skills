---
name: caremax-auth
description: "OAuth Device Flow authentication for CareMax Health API. Use when an agent needs to authenticate with CareMax, obtain API tokens, refresh expired tokens, or set up first-time authorization. Trigger terms: caremax login, caremax auth, health API token, authorize caremax, connect health data."
license: MIT
---

# CareMax Authentication — OAuth Device Flow

This skill handles agent authentication with the CareMax Health API using the OAuth Device Authorization Grant (RFC 8628). No manual API key copy-paste needed — the agent opens a browser, the user approves, and the token is returned automatically.

## Authentication Flow

### Step 1: Request Device Code

```http
POST https://api.caremax.ai/api/auth/device
Content-Type: application/json

{
  "client_id": "caremax-agent",
  "scope": "read:indicators read:records read:members write:upload write:ocr search:records"
}
```

Response:
```json
{
  "device_code": "dc-a1b2c3...",
  "user_code": "ABCD-1234",
  "verification_uri": "https://api.caremax.ai/authorize",
  "verification_uri_complete": "https://api.caremax.ai/authorize?code=ABCD-1234",
  "expires_in": 900,
  "interval": 5
}
```

### Step 2: Open Browser for User Approval

Open `verification_uri_complete` in the user's default browser. The user will:
1. Log in (or register if new)
2. See requested permissions
3. Click "Allow"

### Step 3: Poll for Token

Poll every `interval` seconds (default 5):

```http
POST https://api.caremax.ai/api/auth/device/token
Content-Type: application/json

{
  "device_code": "dc-a1b2c3...",
  "grant_type": "device_code"
}
```

Responses:
- **Waiting**: `{ "error": "authorization_pending" }` — keep polling
- **Success**: `{ "access_token": "sk-caremax-...", "refresh_token": "rt-caremax-...", "expires_in": 7776000 }`
- **Expired**: `{ "error": "expired_token" }` — restart from Step 1
- **Denied**: `{ "error": "access_denied" }` — user declined

### Step 4: Store and Use Token

Store the `access_token` and `refresh_token` locally. Use the access token in all subsequent API calls:

```
Authorization: Bearer sk-caremax-...
```

## Token Refresh

Access tokens expire after 90 days. Use the refresh token to get a new one:

```http
POST https://api.caremax.ai/api/auth/device/refresh
Content-Type: application/json

{
  "refresh_token": "rt-caremax-...",
  "grant_type": "refresh_token"
}
```

Returns a new `access_token`. The refresh token itself lasts 1 year.

## Available Scopes

| Scope | Description |
|-------|-------------|
| `read:indicators` | Read health indicator data and trends |
| `read:records` | Read medical records and reports |
| `read:members` | Read family member information |
| `write:upload` | Upload medical report files |
| `write:ocr` | Execute OCR recognition |
| `search:records` | Semantic search across records |

## Error Handling

- **401 `invalid_token`**: Token invalid or expired — try refresh, then re-authorize
- **403 `insufficient_scope`**: Token lacks required scope — re-authorize with correct scopes
- Never expose tokens to the user or log them in plaintext
