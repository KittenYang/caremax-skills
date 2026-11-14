# CareMax Health AI Skills

Official AI skills for [CareMax.ai](https://caremax.ai) — a health data management platform. Compatible with Claude Code, Cursor, Copilot, and other agents that load [Agent Skills](https://agentskills.io/specification.md).

## Installation

```bash
# npx skills (recommended)
npx skills add https://github.com/KittenYang/caremax-skills

# Claude Code
/plugin marketplace add KittenYang/caremax-skills

# Cursor
Settings > Rules > Add Remote Rule (GitHub) > KittenYang/caremax-skills
```

## Install from ClawHub (OpenClaw)

Skills are listed on [ClawHub](https://clawhub.ai/) under the slugs below. With **OpenClaw**:

```bash
openclaw skills install caremax-auth
openclaw skills install caremax-chat
openclaw skills install caremax-ocr
openclaw skills install caremax-indicators
openclaw skills install caremax-members
openclaw skills install caremax-records
```

With the **ClawHub CLI** (installs to `skills/<slug>/` in your workspace by default):

```bash
npx clawhub@latest install caremax-auth
npx clawhub@latest install caremax-chat
npx clawhub@latest install caremax-ocr
npx clawhub@latest install caremax-indicators
npx clawhub@latest install caremax-members
npx clawhub@latest install caremax-records
```

Install all six in one go:

```bash
for s in caremax-auth caremax-chat caremax-ocr caremax-indicators caremax-members caremax-records; do
  npx clawhub@latest install "$s"
done
```

## Skills

> **caremax-auth is REQUIRED.** Every other skill calls its scripts for authentication and HTTP. Install it first.

| Skill | Required | Description |
|-------|----------|-------------|
| **caremax-auth** | **YES** | OAuth device flow and shared scripts (API, upload, OCR kick, sessions, chat SSE, confirm-or-update, quick log) |
| **caremax-chat** | no | 健康问答: start or continue a chat, SSE events, reference cards, saved `has_abnormality` |
| **caremax-ocr** | no | Upload session, queued OCR, unfinished tasks vs paginated history, review, confirm or update |
| **caremax-indicators** | no | Indicator lists, categories, trends, and quick log (「快捷记一笔」) |
| **caremax-records** | no | Saved-report query and search, text vs indicator reports, update via `POST /records` |
| **caremax-members** | no | Family member list, create, update, and delete |

Field-level HTTP contracts, including what is production and what is only on an unmerged draft, are in `skills/caremax-auth/references/http-contracts.md`.

## Session-based upload

```
upload (creates session)
  → POST /sessions/:id/ocr (HTTP 202, queued)
    → poll GET /sessions/:id/status
      → review when status is awaiting_confirm
        → confirm once
```

Production confirm returns HTTP 200 when the write finishes inline. An unmerged API can return HTTP 202 with `status:"saving"`; poll until `completed` or `error`, and do not confirm again. A session that is already `completed` is not confirmed again. Editing that report is `POST /records`.

未完成 tasks and 全部 history are different `GET /sessions` calls. Unfinished filters by status. History is paginated and has no status filter.

## Try it out

### Health Q&A

- `我的肾功能怎么样`
- `继续刚才的对话，只看这一份报告`
- `这张参考资料算异常吗` (uses the saved flag, not the summary wording)

### Upload and OCR

- `帮我识别这张化验单` (image attached)
- `有哪些上传还没完成`
- `全部上传任务再翻一页`
- `这份已经保存的报告改一下异常标记`

### Indicators and quick log

- `Show all my health indicators`
- `Blood sugar trend over the past 6 months`
- `记一笔体重 61 kg`

### Records and family

- `Find liver-function reports`
- `Show my mom's blood sugar trend`
- `Upload this report for my dad`

## Scripts

Scripts live in `skills/caremax-auth/scripts/`. From that directory use `./scripts/<name>.sh`. From a sibling skill use `../caremax-auth/scripts/<name>.sh`.

| Script | Purpose |
|--------|---------|
| `auth-flow.sh [base_url]` | Device flow: browser, poll, save token |
| `api-call.sh <method> <path> [json]` | Authenticated JSON call; refreshes on expiry and on 401 |
| `upload.sh [--member id] <files...>` | Create a session and upload files |
| `ocr-kick.sh` / `ocr-stream.sh <session_id>` | Queue OCR (HTTP 202). `ocr-stream.sh` still understands a legacy SSE body |
| `session-status.sh <session_id>` | Poll OCR or save progress |
| `sessions-list.sh unfinished\|history\|status` | Unfinished tasks, or paginated history, or one status |
| `chat-stream.sh --question "..."` | 健康问答 SSE |
| `save-reports.sh --session id --file f` | Confirm a session that is still awaiting review |
| `save-reports.sh --update --file f` | Update a saved report with `POST /records` |
| `list-system-presets.sh` | Quick-log choices (`category=common_indicator`) |
| `quick-log.sh <key> <value> [...]` | Save one daily vital |
| `download-file.sh <file_id> [path]` | Download a source file |
| `check-token.sh` / `refresh-token.sh` | Token status and refresh |

## Tests

The suite uses fixtures and a local mock. It does not call production and it does not need secrets.

```bash
python3 -m unittest discover -s tests -v
# or
bash scripts/test.sh
```

An optional read-only smoke of the public manifest is skipped unless you opt in. It does not send a token and it does not write:

```bash
CAREMAX_LIVE_SMOKE=1 python3 -m unittest tests.test_live_smoke -v
```

## License

MIT
