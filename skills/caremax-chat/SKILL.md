---
name: caremax-chat
description: "CareMax health Q&A (健康问答 / 对话). Use when the user asks a question about their reports, starts or continues a chat, wants citations or reference cards, or asks whether a cited report is abnormal. Covers SSE events, conversation ids, and the saved has_abnormality rule. Trigger terms: 健康问答, 对话, chat, ask my reports, citations, sources, 参考资料, 异常吗."
license: MIT
---

# CareMax health Q&A

> Requires sibling `caremax-auth`. If it is missing: `npx skills add KittenYang/caremax-skills`.

Multi-turn health chat over `POST /api/skill/chat`. This is the in-app 「健康问答」 surface. Record search (`caremax-records`) is a different call and does not keep a conversation.

Contract details: [../caremax-auth/references/http-contracts.md](../caremax-auth/references/http-contracts.md).

## Prerequisites

```bash
CHAT="bash ../caremax-auth/scripts/chat-stream.sh"
APICALL="bash ../caremax-auth/scripts/api-call.sh"
```

`no_credentials` → `bash ../caremax-auth/scripts/auth-flow.sh` immediately, then retry.

## Start or continue

```bash
$CHAT --question "我的肾功能怎么样" --member <member_uuid>
$CHAT --question "那肌酐呢" --conversation <conversationId> --member <member_uuid>
$CHAT --question "只看这一份" --record <record_id> --member <member_uuid>
$CHAT --question "再想深一点" --conversation <conversationId> --deep
```

Always use `chat-stream.sh`. It sets `Accept: text/event-stream`. A JSON POST without that header returns an answer and citations but **no `sources` array**.

Relay events as they arrive:

| event | What to show |
|---|---|
| `status` | `accepted` (keep `conversationId`, `userMessageId`), then `retrieving`, then `generating` |
| `sources` | Reference cards, before the answer. One card per record id |
| `thinking` | Only for `--deep` |
| `delta` | Append to the answer |
| `citations` | `[n]` markers already in the answer; `recordId` points at the report |
| `done` | Turn is stored. Keep `conversationId` for the next turn |
| `error` | `chat_failed` or `answer_truncated`. Do not invent the rest of the answer |

`mode` is `fast` or `deep`. `retryUserMessageId` is only for retrying a user turn whose assistant status is not `complete` (`--retry <userMessageId>`). A completed assistant turn returns 404 `retry_not_found`.

Pinned `recordId` limits facts to that report. `memberId` limits retrieval to that family member. Both 404 when they do not belong to the user (`record_not_found`, `member_not_found`).

## Abnormality of a cited report

Use the saved `has_abnormality` flag. Do not decide from the card `snippet`, the summary, or the word 异常.

| Saved flag | Say |
|---|---|
| nonzero / true | This report is marked abnormal |
| 0 / false | This report is marked not abnormal |
| null / missing | The mark is unset. Do not call the report abnormal |

Indicator rows are separate: `indicators[].isAbnormal` is true only when that row's `is_abnormal` is 1. A report can be marked not abnormal while one row is abnormal. Say which is which.

Production `sources[].hasAbnormality` is true only for exact `1`. The unmerged backend change (not production) uses the nonzero rule and adds an 「异常标记」 line to the prompt. The unmerged iOS build draws the badge from `POST /api/skill/records/query` `has_abnormality`, not from the chat card. If the raw flag is available, it wins over the card boolean. Never upgrade a false or null card because the snippet contains 异常.

```bash
$APICALL POST /api/skill/records/query '{"recordId":"<source id>"}'
```

Read `has_abnormality` from that record. Apply the table above.

## History

```bash
$APICALL GET "/api/skill/chat/conversations?page=1&limit=20"
$APICALL GET /api/skill/chat/conversations/<conversationId>
$APICALL GET "/api/skill/chat/messages/search?q=肌酐&page=1&limit=20"
$APICALL DELETE /api/skill/chat/conversations/<conversationId>
```

`GET /api/skill/chat/history` is the legacy flat list. Prefer conversations. Stored messages can include `sources` and `citations` from the SSE turn.

`GET /api/skill/chat/suggestions?recordId=` returns suggested questions only when digest precompute is enabled; `status:"disabled"` means there are none.
