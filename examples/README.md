# CareMax Skills — Examples

## Quick Start

After installing the skills, ask for any of the following:

```
我的肾功能怎么样
这份参考资料算异常吗
有哪些上传还没做完
全部上传任务
Show all my health indicators
Blood sugar trend over the past 6 months
记一笔体重 61 kg
Find liver function reports
Show my mom's blood sugar trend
帮我识别这张化验单
```

## Conversation Examples

### Example 1: Health Q&A

```
User: 我的肾功能怎么样？

Agent:
  → bash ../caremax-auth/scripts/chat-stream.sh --question "我的肾功能怎么样"
  → SSE status accepted, then sources, then delta, then citations, then done
  → Shows the answer and reference cards
  → A card is "abnormal" only when saved has_abnormality is nonzero
  → Snippet text that contains 异常 does not flip a 0 or null flag
```

### Example 2: Indicator trend

```
User: How's my creatinine been lately?

Agent:
  → bash ../caremax-auth/scripts/api-call.sh GET /api/skill/indicators
  → Finds creatinine id
  → bash ../caremax-auth/scripts/api-call.sh GET "/api/skill/indicators/trend?id=<uuid>"
  → Lists dates, values, units, and reference ranges
  → Row is_abnormal is true only when the stored flag is 1
```

### Example 3: Upload, queue OCR, confirm once

```
User: [sends a photo of a blood test]

Agent:
  → bash ../caremax-auth/scripts/upload.sh /path/to/report.jpg
  → bash ../caremax-auth/scripts/ocr-stream.sh <session_id>
  → step=accepted, HTTP 202, status queued
  → bash ../caremax-auth/scripts/session-status.sh <session_id>
  → when awaiting_confirm, shows the indicator table and waits
  → bash ../caremax-auth/scripts/save-reports.sh --session <session_id> --file confirm.json
  → HTTP 200 saved, or HTTP 202 saving (poll; do not confirm again)
```

### Example 4: Unfinished tasks are not all history

```
User: 还有没处理完的上传吗？另外全部任务有哪些？

Agent:
  → sessions-list.sh unfinished --member <id>
  → empty unfinished list is allowed
  → sessions-list.sh history --member <id> --page 1 --limit 20
  → history can still contain completed sessions
```

### Example 5: Edit a saved text report

```
User: 把那份总检综述标成不异常

Agent:
  → POST /api/skill/records/query {"recordId":"..."}
  → sees a text report (not lab)
  → save-reports.sh --update --file records.json
  → POST /api/records with the existing id and has_abnormality 0
  → does not call session confirm
```

### Example 6: Record search

```
User: 找肝功能相关的报告

Agent:
  → POST /api/skill/records/query {"searchText":"肝功能"}
  → shows data[] and, when present, rag.answer
  → this is search, not a 健康问答 conversation
```

### Example 7: Family member and quick log

```
User: 给妈妈记一笔体重 52 kg

Agent:
  → GET /api/skill/members
  → list-system-presets.sh
  → quick-log.sh weight 52 --unit kg --member <parent id>
```

### Example 8: First authentication

```
User: Show my blood routine

Agent:
  → api-call.sh returns no_credentials
  → auth-flow.sh opens the browser and polls
  → retries the indicator list after authorization
```
