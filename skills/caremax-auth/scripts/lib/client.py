#!/usr/bin/env python3
"""Authenticated CareMax HTTP client used by the shell wrappers.

Prints JSON to stdout. Exit 1 means the call could not be authorized or the
server rejected a command that must not be retried blindly. Response bodies
from the API are still printed.
"""

from __future__ import annotations

import json
import mimetypes
import os
import sys
import uuid
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping, Optional

import contracts

SCRIPT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_BASE = "https://api.caremax.ai"


class AuthError(Exception):
    def __init__(self, payload: dict[str, Any]):
        super().__init__(payload.get("error") or "auth_error")
        self.payload = payload


def creds_path() -> Path:
    override = os.environ.get("CAREMAX_CREDENTIALS_FILE")
    if override:
        return Path(override)
    return Path.home() / ".caremax" / "credentials.json"


def load_creds() -> Optional[dict[str, Any]]:
    path = creds_path()
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_creds(creds: Mapping[str, Any]) -> None:
    path = creds_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(creds), indent=2) + "\n", encoding="utf-8")


def token_status(creds: Optional[Mapping[str, Any]] = None) -> dict[str, Any]:
    creds = dict(creds) if creds is not None else load_creds()
    if not creds:
        return {"status": "missing"}
    expires_at = str(creds.get("expires_at") or "")
    base_url = str(creds.get("base_url") or DEFAULT_BASE)
    try:
        exp = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        now = datetime.now(exp.tzinfo)
        if now < exp:
            return {
                "status": "valid",
                "access_token": creds.get("access_token", ""),
                "base_url": base_url,
                "expires_at": expires_at,
                "scope": creds.get("scope", ""),
            }
    except (TypeError, ValueError):
        pass
    return {
        "status": "expired",
        "refresh_token": creds.get("refresh_token", ""),
        "base_url": base_url,
    }


def _iso_expiry(seconds: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(seconds=int(seconds))
    return exp.strftime("%Y-%m-%dT%H:%M:%SZ")


def refresh_creds(creds: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    creds = dict(creds) if creds is not None else (load_creds() or {})
    refresh_token = creds.get("refresh_token")
    if not refresh_token:
        return {"status": "refresh_failed", "error": "no_refresh_token"}
    base_url = str(creds.get("base_url") or DEFAULT_BASE).rstrip("/")
    body = json.dumps({
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url}/api/auth/device/refresh",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")
        return {"status": "refresh_failed", "error": detail, "http_status": error.code}
    except urllib.error.URLError as error:
        return {"status": "refresh_failed", "error": str(error.reason)}
    if "access_token" not in payload:
        return {"status": "refresh_failed", "error": payload}
    creds["access_token"] = payload["access_token"]
    if payload.get("refresh_token"):
        creds["refresh_token"] = payload["refresh_token"]
    if payload.get("scope"):
        creds["scope"] = payload["scope"]
    creds["expires_at"] = _iso_expiry(int(payload.get("expires_in") or 0))
    creds["base_url"] = base_url
    save_creds(creds)
    return {
        "status": "refreshed",
        "access_token": creds["access_token"],
        "base_url": base_url,
    }


def ensure_token() -> tuple[str, str]:
    status = token_status()
    if status["status"] == "missing":
        raise AuthError({
            "error": "no_credentials",
            "message": "Run auth-flow.sh first to authenticate",
        })
    if status["status"] == "expired":
        refreshed = refresh_creds()
        if refreshed.get("status") != "refreshed":
            raise AuthError({
                "error": "token_expired",
                "message": "Refresh failed. Run auth-flow.sh to re-authenticate",
                "detail": refreshed,
            })
        status = token_status()
    return str(status["access_token"]), str(status["base_url"]).rstrip("/")


def _should_refresh(http_status: int, body_text: str) -> bool:
    if http_status != 401:
        return False
    try:
        payload = json.loads(body_text)
    except json.JSONDecodeError:
        return "invalid_token" in body_text or "token_expired" in body_text
    code = str(payload.get("code") or payload.get("error") or "")
    return code in {"invalid_token", "token_expired"}


def _request(
    method: str,
    url: str,
    *,
    token: str,
    body: Optional[bytes] = None,
    headers: Optional[dict[str, str]] = None,
    timeout: int = 120,
) -> tuple[int, str, str]:
    merged = {"Authorization": f"Bearer {token}"}
    if headers:
        merged.update(headers)
    request = urllib.request.Request(url, data=body, method=method, headers=merged)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get("Content-Type", "")
            return response.status, content_type, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as error:
        content_type = error.headers.get("Content-Type", "") if error.headers else ""
        return error.code, content_type, error.read().decode("utf-8", "replace")


def authorized_request(
    method: str,
    path: str,
    *,
    json_body: Any = None,
    raw_body: Optional[bytes] = None,
    headers: Optional[dict[str, str]] = None,
    timeout: int = 120,
) -> tuple[int, str, str]:
    token, base = ensure_token()
    url = path if path.startswith("http") else f"{base}{path if path.startswith('/') else '/' + path}"
    extra = dict(headers or {})
    body = raw_body
    if json_body is not None:
        body = json.dumps(json_body, ensure_ascii=False).encode("utf-8")
        extra.setdefault("Content-Type", "application/json")
    status, content_type, text = _request(method, url, token=token, body=body, headers=extra, timeout=timeout)
    if _should_refresh(status, text):
        refreshed = refresh_creds()
        if refreshed.get("status") != "refreshed":
            raise AuthError({
                "error": "token_expired",
                "message": "Refresh failed. Run auth-flow.sh to re-authenticate",
                "http_status": status,
                "body": text,
            })
        token, base = ensure_token()
        url = path if path.startswith("http") else f"{base}{path if path.startswith('/') else '/' + path}"
        status, content_type, text = _request(
            method, url, token=token, body=body, headers=extra, timeout=timeout,
        )
    return status, content_type, text


def _print(payload: Any) -> None:
    if isinstance(payload, str):
        sys.stdout.write(payload)
        if payload and not payload.endswith("\n"):
            sys.stdout.write("\n")
        return
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _loads(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw": text}


def cmd_call(argv: list[str]) -> int:
    if len(argv) < 2:
        _print({"error": "usage", "message": "api-call.sh <METHOD> <PATH> [JSON_BODY]"})
        return 1
    method, path = argv[0], argv[1]
    json_body = None
    if len(argv) >= 3 and argv[2] != "":
        json_body = json.loads(argv[2])
    status, _content_type, text = authorized_request(method.upper(), path, json_body=json_body)
    _print(text)
    return 0 if status < 400 else 1


def _encode_multipart(fields: list[tuple[str, str]], files: list[tuple[str, str]]) -> tuple[bytes, str]:
    boundary = f"----caremax{uuid.uuid4().hex}"
    chunks: list[bytes] = []
    for name, value in fields:
        chunks.append(
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode("utf-8")
        )
    for field, filepath in files:
        path = Path(filepath)
        filename = path.name.replace('"', "")
        mime = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        data = path.read_bytes()
        chunks.append(
            (
                f"--{boundary}\r\n"
                f"Content-Disposition: form-data; name=\"{field}\"; filename=\"{filename}\"\r\n"
                f"Content-Type: {mime}\r\n\r\n"
            ).encode("utf-8")
        )
        chunks.append(data)
        chunks.append(b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(chunks), boundary


def cmd_upload(argv: list[str]) -> int:
    member = None
    files: list[str] = []
    index = 0
    while index < len(argv):
        if argv[index] == "--member":
            member = argv[index + 1]
            index += 2
            continue
        files.append(argv[index])
        index += 1
    if not files:
        _print({"error": "usage", "message": "upload.sh <file1> [file2 ...] [--member UUID]"})
        return 1
    missing = [item for item in files if not Path(item).is_file()]
    if missing:
        _print({"error": "file_not_found", "message": f"File not found: {missing[0]}"})
        return 1
    fields = [("member_id", member)] if member else []
    body, boundary = _encode_multipart(fields, [("files", item) for item in files])
    status, _content_type, text = authorized_request(
        "POST",
        "/api/sessions/upload",
        raw_body=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    _print(text)
    return 0 if status < 400 else 1


def cmd_download(argv: list[str]) -> int:
    if not argv:
        _print({"error": "usage", "message": "download-file.sh <file_id> [output_path]"})
        return 1
    file_id = argv[0]
    output = Path(argv[1]) if len(argv) > 1 else Path(file_id)
    token, base = ensure_token()
    url = f"{base}/api/sessions/file-content/{urllib.parse.quote(file_id)}"
    request = urllib.request.Request(url, method="GET", headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            data = response.read()
            http_status = response.status
    except urllib.error.HTTPError as error:
        if output.exists():
            output.unlink()
        _print({"error": "download_failed", "http_code": error.code})
        return 1
    if http_status != 200:
        _print({"error": "download_failed", "http_code": http_status})
        return 1
    output.write_bytes(data)
    _print({"status": "ok", "path": str(output), "size": len(data)})
    return 0


def _query(path: str, query: Mapping[str, Any]) -> str:
    pairs = []
    for key, value in query.items():
        if value is None:
            continue
        pairs.append((key, str(value)))
    encoded = urllib.parse.urlencode(pairs)
    return f"{path}?{encoded}" if encoded else path


def cmd_sessions(argv: list[str]) -> int:
    if not argv:
        _print({"error": "usage", "message": "sessions-list.sh unfinished|history|status ..."})
        return 1
    mode = argv[0]
    member = None
    page = 1
    limit = contracts.HISTORY_PAGE_SIZE
    status_filter = None
    index = 1
    if mode == "status":
        if len(argv) < 2:
            _print({"error": "usage", "message": "sessions-list.sh status <status>"})
            return 1
        status_filter = argv[1]
        index = 2
    while index < len(argv):
        flag = argv[index]
        if flag == "--member":
            member = argv[index + 1]
            index += 2
        elif flag == "--page":
            page = int(argv[index + 1])
            index += 2
        elif flag == "--limit":
            limit = int(argv[index + 1])
            index += 2
        else:
            _print({"error": "usage", "message": f"unknown argument {flag}"})
            return 1
    requests = contracts.session_list_request(
        mode, member_id=member, page=page, limit=limit, status=status_filter,
    )
    pages = []
    for item in requests:
        path = _query(item["path"], item["query"])
        http_status, _content_type, text = authorized_request("GET", path)
        body = _loads(text)
        if http_status >= 400:
            _print({"error": "session_list_failed", "http_status": http_status, "path": path, "body": body})
            return 1
        pages.append(body if isinstance(body, dict) else {"sessions": []})
    if mode == "unfinished":
        sessions = contracts.merge_unfinished(pages)
        _print({
            "mode": "unfinished",
            "sessions": sessions,
            "total": len(sessions),
            "queried_statuses": list(contracts.UNFINISHED_STATUSES),
        })
        return 0
    page_body = pages[0]
    _print({
        "mode": "history" if mode == "history" else "status",
        "status": None if mode == "history" else status_filter,
        "sessions": page_body.get("sessions") or [],
        "total": page_body.get("total", 0),
        "page": page_body.get("page", page),
        "limit": page_body.get("limit", limit),
        "has_more": contracts.history_has_more(page_body, page_number=page, limit=limit),
    })
    return 0


def cmd_session_status(argv: list[str]) -> int:
    if not argv:
        _print({"error": "usage", "message": "session-status.sh <session_id>"})
        return 1
    session_id = argv[0]
    http_status, _content_type, text = authorized_request(
        "GET", f"/api/skill/sessions/{urllib.parse.quote(session_id)}/status",
    )
    body = _loads(text)
    if isinstance(body, dict):
        body = {"http_status": http_status, **body}
    _print(body)
    return 0 if http_status < 400 else 1


def cmd_ocr_kick(argv: list[str]) -> int:
    if not argv:
        _print({"step": "error", "message": "ocr-kick.sh <session_id>"})
        return 1
    return _ocr_post(argv[0], stream=False)


def cmd_ocr_stream(argv: list[str]) -> int:
    if not argv:
        _print({"step": "error", "progress": -1, "message": "ocr-stream.sh <session_id>"})
        return 1
    return _ocr_post(argv[0], stream=True)


def _ocr_post(session_id: str, *, stream: bool) -> int:
    http_status, content_type, text = authorized_request(
        "POST",
        f"/api/sessions/{urllib.parse.quote(session_id)}/ocr",
        json_body={},
        headers={"Accept": "text/event-stream", "Content-Type": "application/json"},
    )
    if "text/event-stream" in content_type.lower():
        frames = contracts.parse_sse(text)
        if stream:
            for frame in frames:
                _print(frame["data"] if isinstance(frame["data"], (dict, list)) else {"step": frame["event"], "data": frame["data"]})
        else:
            _print({"http_status": http_status, "events": frames})
        failed = any(
            isinstance(frame.get("data"), dict) and frame["data"].get("step") == "error"
            for frame in frames
        )
        return 1 if failed or http_status >= 400 else 0
    body = _loads(text)
    if not isinstance(body, dict):
        body = {"raw": text}
    error = str(body.get("error") or "")
    code = str(body.get("code") or "")
    if http_status >= 400:
        if "already completed" in error.lower():
            code = code or "session_already_completed"
        event = {
            "step": "error",
            "progress": -1,
            "http_status": http_status,
            "message": error or "OCR request failed",
            "error": error,
            "session_id": body.get("session_id", session_id),
            "status": body.get("status"),
        }
        if code:
            event["code"] = code
        _print(event)
        return 1
    event = {
        "step": "accepted",
        "progress": 0,
        "http_status": http_status,
        "message": "OCR queued. Poll GET /sessions/:id/status until awaiting_confirm.",
        "session_id": body.get("session_id", session_id),
        "status": body.get("status"),
        "accepted": body.get("accepted"),
        "report_count": body.get("report_count", 0),
    }
    _print(event)
    return 0


def cmd_chat(argv: list[str]) -> int:
    question = None
    conversation = None
    record = None
    member = None
    retry = None
    deep = False
    body_file = None
    index = 0
    while index < len(argv):
        flag = argv[index]
        if flag == "--question":
            question = argv[index + 1]
            index += 2
        elif flag == "--conversation":
            conversation = argv[index + 1]
            index += 2
        elif flag == "--record":
            record = argv[index + 1]
            index += 2
        elif flag == "--member":
            member = argv[index + 1]
            index += 2
        elif flag == "--retry":
            retry = argv[index + 1]
            index += 2
        elif flag == "--deep":
            deep = True
            index += 1
        elif flag == "--file":
            body_file = argv[index + 1]
            index += 2
        else:
            _print({"event": "error", "data": {"error": "usage", "message": f"unknown argument {flag}"}})
            return 1
    if body_file:
        payload = json.loads(Path(body_file).read_text(encoding="utf-8"))
    else:
        if not question:
            _print({"event": "error", "data": {"error": "question is required"}})
            return 1
        payload = {"question": question, "deepThinking": deep}
        if conversation:
            payload["conversationId"] = conversation
        if record:
            payload["recordId"] = record
        if member:
            payload["memberId"] = member
        if retry:
            payload["retryUserMessageId"] = retry
    http_status, content_type, text = authorized_request(
        "POST",
        "/api/skill/chat",
        json_body=payload,
        headers={"Accept": "text/event-stream", "Content-Type": "application/json"},
        timeout=180,
    )
    if http_status >= 400:
        parsed = _loads(text)
        if not isinstance(parsed, dict):
            parsed = {"raw": text}
        _print({"event": "error", "data": {"http_status": http_status, **parsed}})
        return 1
    if "text/event-stream" in content_type.lower():
        frames = contracts.parse_sse(text)
        for frame in frames:
            _print(frame)
        failed = any(frame.get("event") == "error" for frame in frames)
        return 1 if failed else 0
    _print({"event": "json", "data": _loads(text)})
    return 0


def cmd_save(argv: list[str]) -> int:
    session_id = None
    body_file = None
    explicit_update = False
    index = 0
    while index < len(argv):
        flag = argv[index]
        if flag == "--session":
            session_id = argv[index + 1]
            index += 2
        elif flag == "--file":
            body_file = argv[index + 1]
            index += 2
        elif flag == "--update":
            explicit_update = True
            index += 1
        else:
            _print({"action": "error", "error": f"unknown argument {flag}"})
            return 1
    if not body_file:
        _print({"action": "error", "error": "save-reports.sh requires --file payload.json"})
        return 1
    payload = json.loads(Path(body_file).read_text(encoding="utf-8"))
    if explicit_update or not session_id:
        decision = contracts.decide_save(None, explicit_update=True)
        return _post_records(payload, decision)
    http_status, _content_type, text = authorized_request(
        "GET", f"/api/skill/sessions/{urllib.parse.quote(session_id)}/status",
    )
    status_body = _loads(text)
    if http_status >= 400:
        _print({"action": "error", "http_status": http_status, "body": status_body, "retry_confirm": False})
        return 1
    session_status = status_body.get("status") if isinstance(status_body, dict) else ""
    decision = contracts.decide_save(session_status, explicit_update=False)
    if decision["action"] == "confirm":
        reports = payload.get("reports") if isinstance(payload, dict) else None
        if isinstance(reports, list):
            blocked = [item for item in reports if isinstance(item, dict) and not contracts.lab_report_can_confirm(item)]
            if blocked:
                _print({
                    "action": "rejected",
                    "http_status": 422,
                    "error": "indicator report has no indicators",
                    "retry_confirm": False,
                })
                return 1
        post_status, _ctype, post_text = authorized_request(
            "POST",
            f"/api/skill/sessions/{urllib.parse.quote(session_id)}/confirm",
            json_body=payload,
        )
        interpreted = contracts.interpret_confirm_response(post_status, _loads(post_text))
        interpreted["session_id"] = session_id
        _print(interpreted)
        return 0 if interpreted["action"] in {"saved", "saving"} else 1
    if decision["action"] == "update_record":
        return _post_records(payload, decision)
    _print({**decision, "session_id": session_id})
    return 1


def _post_records(payload: Any, decision: Mapping[str, Any]) -> int:
    http_status, _content_type, text = authorized_request("POST", "/api/records", json_body=payload)
    body = _loads(text)
    ok = http_status < 400 and isinstance(body, dict) and body.get("success") is True
    _print({
        "action": "updated" if ok else "error",
        "http_status": http_status,
        "path": decision.get("path", "/api/records"),
        "retry_confirm": False,
        "body": body,
    })
    return 0 if ok else 1


def cmd_presets(_argv: list[str]) -> int:
    http_status, _content_type, text = authorized_request(
        "GET", "/api/indicators?category=common_indicator",
    )
    body = _loads(text)
    if http_status >= 400:
        _print(body if isinstance(body, dict) else {"error": "presets_failed", "http_status": http_status, "body": body})
        return 1
    indicators = body.get("indicators") if isinstance(body, dict) else []
    presets = []
    for row in indicators or []:
        if not isinstance(row, dict):
            continue
        presets.append({
            "id": row.get("id"),
            "preset_key": row.get("canonical_name"),
            "display_name": row.get("display_name"),
            "display_name_en": row.get("display_name_en"),
            "canonical_unit": row.get("canonical_unit"),
            "category": row.get("category"),
            "category_label": row.get("category_label"),
        })
    _print({
        "source": "GET /api/indicators?category=common_indicator",
        "deprecated_endpoint": "GET /api/indicators/system-presets",
        "presets": presets,
    })
    return 0


def main(argv: list[str]) -> int:
    if not argv:
        _print({"error": "usage", "message": "client.py <command> ..."})
        return 1
    command, rest = argv[0], argv[1:]
    try:
        if command == "check-token":
            _print(token_status())
            return 0
        if command == "refresh":
            result = refresh_creds()
            _print(result)
            return 0 if result.get("status") == "refreshed" else 1
        if command == "call":
            return cmd_call(rest)
        if command == "upload":
            return cmd_upload(rest)
        if command == "download":
            return cmd_download(rest)
        if command == "sessions":
            return cmd_sessions(rest)
        if command == "session-status":
            return cmd_session_status(rest)
        if command == "ocr-kick":
            return cmd_ocr_kick(rest)
        if command == "ocr-stream":
            return cmd_ocr_stream(rest)
        if command == "chat-stream":
            return cmd_chat(rest)
        if command == "save-reports":
            return cmd_save(rest)
        if command == "presets":
            return cmd_presets(rest)
        _print({"error": "usage", "message": f"unknown command {command}"})
        return 1
    except AuthError as error:
        _print(error.payload)
        return 1
    except json.JSONDecodeError as error:
        _print({"error": "invalid_json", "message": str(error)})
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
