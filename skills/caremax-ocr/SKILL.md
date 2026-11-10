---
name: caremax-ocr
description: "Upload medical reports and run CareMax OCR. After upload, queue OCR in the same turn unless the user asked for upload only. Covers unfinished tasks versus paginated history, review, async confirm (200 or 202 saving), and updates of already saved reports via POST /records. Trigger terms: upload report, scan report, OCR, 继续上传, 未完成, 上传待处理, 全部任务, confirm, 文字报告, 指标报告."
license: MIT
---

# CareMax upload and OCR

> Requires sibling `caremax-auth`. If it is missing: `npx skills add KittenYang/caremax-skills`.

Session workflow: upload → queue OCR → poll status → review → confirm once. Contracts: [../caremax-auth/references/http-contracts.md](../caremax-auth/references/http-contracts.md).

## Prerequisites

```bash
UPLOAD="bash ../caremax-auth/scripts/upload.sh"
OCR="bash ../caremax-auth/scripts/ocr-stream.sh"
STATUS="bash ../caremax-auth/scripts/session-status.sh"
SESSIONS="bash ../caremax-auth/scripts/sessions-list.sh"
SAVE="bash ../caremax-auth/scripts/save-reports.sh"
APICALL="bash ../caremax-auth/scripts/api-call.sh"
```

`no_credentials` → `bash ../caremax-auth/scripts/auth-flow.sh`.

## Default behavior

1. After a successful upload, run OCR in the same turn unless the user explicitly said to store the file only (只上传、不要识别).
2. Production OCR returns HTTP 202. Show that it is queued, then poll status. Do not wait on an SSE stream that the current API does not send.
3. After `awaiting_confirm`, show the review and wait for the user. Do not auto-confirm.
4. Do not call confirm on a `completed` session. That is either HTTP 400 `Session already completed` (unmerged async confirm) or a second insert (production). Edit with `save-reports.sh --update`.

## 1. Upload

```bash
$UPLOAD --member <member_uuid> /path/to/report.jpg /path/to/report.pdf
```

Keep `session_id`. Files may be PDF, JPG, PNG, or HEIC.

## 2. Queue OCR and poll

```bash
$OCR <session_id>
$STATUS <session_id>
```

`step=accepted` with `accepted:true` means queued (`status` becomes `queued`). `accepted:false` means it is already `queued`, `processing`, or `awaiting_confirm`. Poll every few seconds.

| status | Next step |
|---|---|
| `queued`, `processing`, and `is_stale:false` | Keep polling |
| `processing` or `queued` and `is_stale:true` | Kick OCR again. It resumes the checkpoint |
| `awaiting_confirm` | `GET /api/skill/sessions/<id>` and review `session.ocr_result` |
| `error` | Read `error.message` / `error.code`. `ocr_low_quality` will not succeed on retry; ask for a clearer image |
| `completed` | Already saved. Do not OCR or confirm |
| HTTP 403 `ocr_limit_exceeded` | Quota is exhausted |
| HTTP 400 `Session already completed` | Stop. Open the saved report |

`pipeline.completedStep` is how far the job got (`normalize`, `ocr`, `structure`). `pipeline.ocrFailed` counts pages that will be retried.

## 3. Review

`reportType` `lab` is an 指标报告. `imaging`, `genetic`, `pathology`, and `other` are 文字报告.

Indicator reports: table of name, value, unit, reference range, and abnormal when `is_abnormal` is 1. Do not confirm a lab report that has zero indicators.

Text reports: show summary and sections. The abnormality mark is manual. Ask the user. Nonzero means abnormal, 0 means not, and if they do not choose, leave it unset. Do not set the mark because the summary contains 异常. Omitting the field is stored as 0 (not abnormal), so say that explicitly when the user skips the switch.

## 4. Save

Write the reviewed payload to a file and run:

```bash
$SAVE --session <session_id> --file /tmp/confirm.json
```

`confirm.json` is `{"reports":[{"record":{...},"reportType":"lab","sourcePages":["a.jpg"]}]}`. Put `has_abnormality` on `record` for a text report only after the user chooses (`1` or `0`).

| Result | Meaning |
|---|---|
| `action:saved`, HTTP 200 `{success:true, recordIds}` | Production saved inline. Done |
| `action:saving`, HTTP 202 `{accepted, status:"saving"}` | Unmerged async save. Poll status until `completed` or `error`. Do not confirm again |
| `action:refuse_completed` or error `Session already completed` | Already saved. Do not retry confirm |
| `action:rejected` | Empty indicator report or HTTP 422. Fix the payload first |
| `action:wait_saving` | A save is already running |

## 5. Edit a saved report

```bash
$SAVE --update --file /tmp/records.json
```

`records.json` is `{"records":[{"id":"<existing record id>", ...}], "member_id":"<uuid>"}`. This is `POST /api/records`. iOS uses it for 「保存记录」 after the first confirm. Do not POST confirm for that edit.

## Unfinished vs all history

```bash
$SESSIONS unfinished --member <member_uuid>
$SESSIONS history --member <member_uuid> --page 1 --limit 20
```

未完成 / 上传待处理 is the merged status query (`uploading`, `queued`, `processing`, `awaiting_confirm`, `error`, `saving`). 全部任务 / 全部 is the paginated call **without** `status`. Empty unfinished does not mean history is empty. Refresh repeats page 1. Load more only while `has_more` is true.

Resume: `uploading` or stale `processing` → OCR kick. `awaiting_confirm` → review. `error` → show `error.message`, then kick only if the code is not a permanent image failure. `saving` → wait, do not press continue. `completed` rows in history are view/download only.

```bash
bash ../caremax-auth/scripts/download-file.sh <file_id> /tmp/source.jpg
$APICALL DELETE /api/skill/sessions/<session_id>
$APICALL DELETE /api/skill/sessions/<session_id>/records/<record_id>
```

Deleting one record keeps the rest of the session. Deleting the session removes its files and reports.
