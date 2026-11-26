---
name: caremax-chat
description: "CareMax health Q&A (健康问答 / 对话). Use when the user asks a question about their reports, starts or continues a chat, wants citations, reference cards, or a trend card, or asks whether a cited report is abnormal. Covers SSE events, conversation ids, trend cards, and the saved has_abnormality rule. Trigger terms: 健康问答, 对话, chat, ask my reports, citations, sources, 参考资料, 异常吗, 趋势卡片, trend card, caremax-card."
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

Always use `chat-stream.sh`. It sets `Accept: text/event-stream`. A JSON POST without that header returns an answer and citations but **no `sources` array**. When that turn has trend cards, the same JSON includes `cards`. With no cards, the field is absent.

Relay events as they arrive:

| event | What to show |
|---|---|
| `status` | `accepted` (keep `conversationId`, `userMessageId`), then `retrieving`, then `generating` |
| `sources` | Reference cards, before the answer. One card per record id |
| `thinking` | Only for `--deep` |
| `delta` | Append to the answer |
| `card` | A trend card. `data` is the card object, with no wrapper. It arrives between `delta` chunks |
| `citations` | `[n]` markers already in the answer; `recordId` points at the report |
| `done` | Turn is stored. Keep `conversationId` for the next turn. A turn can finish with no card |
| `error` | `chat_failed` or `answer_truncated`. Do not invent the rest of the answer |

`mode` is `fast` or `deep`. `retryUserMessageId` is only for retrying a user turn whose assistant status is not `complete` (`--retry <userMessageId>`). A completed assistant turn returns 404 `retry_not_found`.

Pinned `recordId` limits facts to that report. `memberId` limits retrieval to that family member. Both 404 when they do not belong to the user (`record_not_found`, `member_not_found`). A trend card still loads that member's saved history for the named indicator, not only the report pinned on this turn.

## Trend cards

Offer a trend card when the answer compares one indicator across dates. Name the indicator. Do not invent the series, draw HTML, or put `points` in the answer. At most three cards per message. Each card keeps at most the 120 most recent points.

The in-app answer marks the indicator, and only the indicator:

```text
<caremax-card>{"type":"trend","indicator_id":"<id>"}</caremax-card>
```

Use `name` when there is no id. Optional `member_id` must be the current member. The serving prompt that asks the in-app model for this marker lives in the backend, not in this skill pack.

The server strips the marker, fills points from that member's saved indicators and medical records, and emits `event: card` whose `data` is the card. Relay that object where the marker sat. If there is no `card` event, leave the chart out and do not keep `<caremax-card>` in the text. A marker that carries `points`, numeric values, HTML, or an unregistered type is dropped the same way. iOS renders `type: trend` natively and opens the existing single-indicator trend for that indicator.

```json
{
  "v": 1,
  "type": "trend",
  "id": "card_…",
  "indicator_id": "<user canonical indicator id>",
  "name": "异型红细胞",
  "unit": "/HP",
  "member_id": "<member uuid>",
  "title": "异型红细胞趋势",
  "reference": { "low": 0, "high": 3, "unit": "/HP" },
  "points": [
    {
      "date": "2021-12-08",
      "value": 10,
      "abnormal": true,
      "record_id": "<record uuid>",
      "report_name": "尿常规"
    }
  ]
}
```

Unused fields are omitted. They are not null.

- `indicator_id` is the same id as `GET /api/skill/indicators/trend?id=`. Omit it only when the series was never linked to a canonical indicator and is grouped by the original name.
- `abnormal` is saved `indicators.is_abnormal === 1`. Do not recompute it from `reference`.
- `value` is present only when the saved result is one finite number (the converted value when the row has one, otherwise the original). A range such as `10-12`, or a result such as `++`, uses `value_text`. Do not turn `10-12` into `10`.
- `reference` is the latest saved `reference_range` that parses to numeric bounds. Omit it when that parse fails.
- An English question uses the title `{name} trend`.
- Stored on `chat_messages.cards_json`. Reopening the conversation, message search, and the legacy history include `cards` when any exist. The marker does not remain in `content`.

## Abnormality of a cited report

Use the saved `has_abnormality` flag. Do not decide from the card `snippet`, the summary, or the word 异常.

| Saved flag | Say |
|---|---|
| nonzero / true | This report is marked abnormal |
| 0 / false | This report is marked not abnormal |
| null / missing | The mark is unset. Do not call the report abnormal |

Indicator rows are separate: `indicators[].isAbnormal` is true only when that row's `is_abnormal` is 1. A report can be marked not abnormal while one row is abnormal. Say which is which.

Analysis uses the user's saved abnormality marks. Do not infer them from summary text.

`sources[].hasAbnormality` comes only from saved `has_abnormality`. On the production API that boolean is true only for exact `1` (`0` is false, `null` is null, any other number is false). The unmerged backend change (not production) uses the nonzero rule and adds an 「异常标记」 line to the prompt.

Current iOS (on `health-ios` main) does not paint the reference badge from the chat card or from the snippet. The badge follows saved `has_abnormality` from `POST /api/skill/records/query`, the same flag as the report list. A missing saved flag shows no 异常 badge, even when the card boolean is true or the snippet contains 异常. When the raw flag is available, it wins over the card boolean.

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

`GET /api/skill/chat/history` is the legacy flat list. Prefer conversations. Stored messages can include `sources`, `citations`, and `cards` from the SSE turn.

In the app, the history sheet loads with the same carrot skeleton as the report list. Bottom sheets do not draw an extra bar along the bottom.

`GET /api/skill/chat/suggestions?recordId=` returns suggested questions only when digest precompute is enabled; `status:"disabled"` means there are none.
