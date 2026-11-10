---
name: caremax-members
description: "List and manage CareMax family members. Use when the user switches profiles, adds or edits a family member, or asks for another member's indicators, records, uploads, or chat. Trigger terms: family member, 家人, 家庭成员, switch member, spouse, parent, child."
license: MIT
---

# CareMax family members

> Requires sibling `caremax-auth`. If it is missing: `npx skills add KittenYang/caremax-skills`.

Profiles the account can file reports under. The signed-in user has one default member (`isDefault: true`). That member cannot be deleted.

Contracts: [../caremax-auth/references/http-contracts.md](../caremax-auth/references/http-contracts.md).

## Prerequisites

```bash
APICALL="bash ../caremax-auth/scripts/api-call.sh"
```

`no_credentials` → `bash ../caremax-auth/scripts/auth-flow.sh`.

## List and edit

Responses are camelCase: `id`, `userId`, `name`, `gender`, `birthDate`, `relationship`, `isDefault`, `createdAt`, `updatedAt`.

```bash
$APICALL GET /api/skill/members
$APICALL GET /api/skill/members/<member_id>
$APICALL POST /api/skill/members '{"name":"妈妈","relationship":"parent","gender":"female"}'
$APICALL PUT /api/skill/members/<member_id> '{"name":"妈妈","relationship":"parent"}'
$APICALL DELETE /api/skill/members/<member_id>
```

Create returns HTTP 201 `{member, message}`. `relationship` is `self`, `spouse`, `child`, `parent`, `sibling`, or `other`. DELETE of the default member is HTTP 400 `不能删除默认会员`.

## Which parameter name

| Call | Member field |
|---|---|
| Indicators, records query, chat | `memberId` |
| Upload, session list, quick log | `member_id` |

```bash
$APICALL GET "/api/skill/indicators?memberId=<id>"
$APICALL POST /api/skill/records/query '{"memberId":"<id>","page":1,"limit":20}'
bash ../caremax-auth/scripts/chat-stream.sh --question "最近的体检" --member <id>
bash ../caremax-auth/scripts/sessions-list.sh unfinished --member <id>
bash ../caremax-auth/scripts/sessions-list.sh history --member <id> --page 1 --limit 20
bash ../caremax-auth/scripts/upload.sh --member <id> /path/to/report.jpg
```

If no member is passed, indicator, record, and chat calls use the default member. Session history should still pass `member_id` when the user is looking at one profile. Unfinished tasks and all-history are different requests; see caremax-ocr.

Look up the member with `GET /api/skill/members` before guessing an id from a name. If two profiles match, ask which one.
