---
name: caremax-members
description: "List and manage CareMax family members, family chips, and the in-app language. Use when the user switches profiles, adds or edits a family member, changes language, or asks for another member's indicators, records, uploads, or chat. Trigger terms: family member, 家人, 家庭成员, switch member, spouse, parent, child, 语言, 头像, Follow system."
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

## Family chips

A family chip shows the avatar to the left of the name. Use the photo when there is one, otherwise the first character of the name, otherwise a person symbol. The avatar sits in a white or light ring. On member management, the selected member card uses a solid opaque fill on the dotted paper.

Member and account settings, including language, stay in 「我的」. 「我的指标」 has no settings gear.

## Language

The app ships Simplified Chinese, Traditional Chinese (繁體中文 / zh-Hant), English, Japanese, and French. Copy is short and written for the app. The name CareMax stays as CareMax. Help text and toasts follow the selected language.

In-app language follows the system, or the user sets it at 我的 → 通用 → 语言. The choices are Follow system (跟随系统), 简体中文, 繁體中文, English, 日本語, and Français. Those language names stay in their own writing; only 「跟随系统」 follows the current language.

Built-in category labels and built-in quick-log names follow this language. Custom category names and custom indicator names stay as saved. Saving a quick log still matches the Simplified Chinese identity. See caremax-indicators.
