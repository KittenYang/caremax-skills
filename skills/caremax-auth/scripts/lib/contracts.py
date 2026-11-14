"""Pure CareMax HTTP/product contracts for scripts and tests.

These helpers do not perform I/O. They encode the rules external agents must
follow, including where the default branch and unmerged client drafts differ.
"""

from __future__ import annotations

import json
from typing import Any, Iterable, Mapping, Optional

_MISSING = object()

# Statuses the iOS unfinished list asks for one request at a time.
# `saving` is only produced by the unmerged async-confirm handler. Querying it
# on the current default branch returns an empty page, which is correct.
UNFINISHED_STATUSES = (
    "uploading",
    "queued",
    "processing",
    "awaiting_confirm",
    "error",
    "saving",
)

HISTORY_PAGE_SIZE = 20


def saved_record_has_abnormality(value: Any) -> Optional[bool]:
    """Product rule shared by the report list and the text-report editor switch.

    Nonzero / true is abnormal. 0 / false is not. NULL, blank, or a non-numeric
    string (including summary text) is unset and is not abnormal.

    This is the rule agents apply to a raw ``has_abnormality`` value. It matches
    the unmerged chat-source change. The default-branch chat card serializer is
    narrower; see ``production_sources_has_abnormality``.
    """

    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if value != value:  # NaN
            return None
        return value != 0
    if isinstance(value, str):
        normalized = value.strip().lower()
        if not normalized:
            return None
        if normalized in {"true", "1"}:
            return True
        if normalized in {"false", "0"}:
            return False
        try:
            parsed = float(normalized)
        except ValueError:
            return None
        if parsed != parsed:
            return None
        return parsed != 0
    return None


def production_sources_has_abnormality(value: Any) -> Optional[bool]:
    """Default-branch ``sources[].hasAbnormality`` mapping (``Number(value) === 1``).

    Only an exact 1 (or boolean true) becomes true. Any other present value,
    including 2, becomes false. Null stays null. Do not treat this as the
    product rule when the raw ``has_abnormality`` column is available.
    """

    if value is None:
        return None
    if isinstance(value, bool):
        return value is True
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value == 1
    if isinstance(value, str):
        try:
            return float(value.strip()) == 1
        except ValueError:
            return False
    return False


def indicator_is_abnormal(value: Any) -> bool:
    """A single lab row is abnormal only when its saved ``is_abnormal`` is 1 / true.

    This is independent of the record-level ``has_abnormality`` flag.
    """

    if value is True:
        return True
    if value is False or value is None:
        return False
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value == 1
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true"}
    return False


def interpret_cited_abnormality(
    *,
    raw_has_abnormality: Any = _MISSING,
    source_has_abnormality: Any = _MISSING,
    snippet: str = "",
) -> Optional[bool]:
    """Decide whether a cited report is abnormal.

    ``snippet`` is accepted so callers can pass the card text, and is ignored.
    Summary words such as 异常 never flip the result.

    When the raw saved flag is present (including null), it wins, even if a
    production chat card boolean disagrees (the default branch only maps
    exact 1 to true). When only the card boolean exists, true/false are used
    as-is and null stays unset.
    """

    del snippet  # never infer from overview, digest, or keywords
    if raw_has_abnormality is not _MISSING:
        return saved_record_has_abnormality(raw_has_abnormality)
    if source_has_abnormality is _MISSING or source_has_abnormality is None:
        return None
    if isinstance(source_has_abnormality, bool):
        return source_has_abnormality
    return saved_record_has_abnormality(source_has_abnormality)


def report_kind(report: Mapping[str, Any]) -> str:
    """``indicator`` (指标报告) or ``text`` (文字报告).

    ``report_type`` / ``reportType`` of ``lab`` is an indicator report.
    Any other explicit type is a text report, even if the summary mentions
    numbers. A missing type with indicators is an indicator report; a missing
    type with only sections or prose is a text report.
    """

    explicit = report.get("reportType", report.get("report_type"))
    nested = report.get("record") if isinstance(report.get("record"), Mapping) else {}
    if explicit is None and nested:
        explicit = nested.get("reportType", nested.get("report_type"))
    indicators = _indicators(report)
    sections = report.get("sections") or (nested or {}).get("sections") or []
    prose = any(
        report.get(key) or (nested or {}).get(key)
        for key in ("summary", "fullText", "full_text")
    )
    if explicit is None:
        if indicators:
            return "indicator"
        if sections or prose:
            return "text"
        return "indicator"
    if str(explicit).strip().lower() == "lab":
        return "indicator"
    return "text"


def manual_mark_applies(report: Mapping[str, Any]) -> bool:
    """The editor's manual abnormality switch is for text reports."""

    return report_kind(report) == "text"


def text_report_mark_for_write(user_choice: Any) -> Optional[int]:
    """Map an explicit user choice to the integer stored on a text report.

    ``None`` means the user did not set the switch. Callers must not replace
    that with a guess from the summary. Omitting the field on confirm/update
    is stored as 0 by the current SQL (``has_abnormality || 0``), which means
    "not abnormal", not "unset".
    """

    if user_choice is None:
        return None
    if isinstance(user_choice, str) and user_choice.strip().lower() in {
        "",
        "unset",
        "unknown",
        "未设置",
    }:
        return None
    flag = saved_record_has_abnormality(user_choice)
    if flag is None:
        return None
    return 1 if flag else 0


def lab_report_can_confirm(report: Mapping[str, Any]) -> bool:
    """Indicator reports need at least one indicator before confirm.

    The in-flight API rejects an empty indicator report with HTTP 422. The
    default branch does not, but agents still must not confirm one.
    """

    if report_kind(report) != "indicator":
        return True
    return len(_indicators(report)) > 0


def decide_save(
    session_status: Optional[str],
    *,
    explicit_update: bool = False,
) -> dict[str, Any]:
    """Choose confirm vs ``POST /records`` vs wait vs refuse.

    A saved report is updated with ``POST /api/records`` (the iOS editor path).
    Confirm is only for a session still in ``awaiting_confirm`` or ``error``.
    ``completed`` must not be confirmed again: the unmerged confirm handler
    returns 400 ``Session already completed``, and the default branch would
    insert another copy because it does not check that status.
    """

    status = (session_status or "").strip().lower()
    if explicit_update:
        return {
            "action": "update_record",
            "method": "POST",
            "path": "/api/records",
            "retry_confirm": False,
        }
    if status in {"completed", "cancelled"}:
        return {
            "action": "refuse_completed",
            "error": "Session already completed",
            "status": status,
            "retry_confirm": False,
            "next": "POST /api/records",
        }
    if status == "saving":
        return {
            "action": "wait_saving",
            "status": "saving",
            "retry_confirm": False,
        }
    if status in {"awaiting_confirm", "error"}:
        return {
            "action": "confirm",
            "method": "POST",
            "retry_confirm": False,
        }
    return {
        "action": "not_ready",
        "status": status,
        "retry_confirm": False,
    }


def interpret_confirm_response(http_status: int, body: Any) -> dict[str, Any]:
    """Normalize a confirm response from either the default branch or the draft."""

    payload = body if isinstance(body, Mapping) else {}
    error = str(payload.get("error") or "")
    status = str(payload.get("status") or "")
    if http_status == 202 or status == "saving":
        return {
            "action": "saving",
            "http_status": http_status,
            "accepted": payload.get("accepted"),
            "status": status or "saving",
            "retry_confirm": False,
            "body": payload,
        }
    if http_status == 200 and payload.get("success") is True:
        return {
            "action": "saved",
            "http_status": http_status,
            "retry_confirm": False,
            "body": payload,
        }
    if http_status == 400 and "already completed" in error.lower():
        return {
            "action": "refuse_completed",
            "http_status": http_status,
            "error": "Session already completed",
            "retry_confirm": False,
            "next": "POST /api/records",
            "body": payload,
        }
    if http_status == 422:
        return {
            "action": "rejected",
            "http_status": http_status,
            "retry_confirm": False,
            "body": payload,
        }
    if http_status == 409:
        return {
            "action": "not_ready",
            "http_status": http_status,
            "retry_confirm": False,
            "body": payload,
        }
    return {
        "action": "error",
        "http_status": http_status,
        "retry_confirm": False,
        "body": payload,
    }


def session_list_request(
    mode: str,
    *,
    member_id: Optional[str] = None,
    page: int = 1,
    limit: int = HISTORY_PAGE_SIZE,
    status: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Query strings for unfinished tasks vs paginated history.

    Unfinished is one exact ``status`` per in-progress state. History omits
    ``status`` so completed sessions are included. The two calls are not
    interchangeable: an empty unfinished merge can sit next to a non-empty
    history page.
    """

    mode = mode.strip().lower()
    if mode == "unfinished":
        requests = []
        for item in UNFINISHED_STATUSES:
            requests.append(_session_query(member_id=member_id, page=1, limit=limit, status=item))
        return requests
    if mode == "history":
        return [_session_query(member_id=member_id, page=page, limit=limit, status=None)]
    if mode == "status":
        if not status:
            raise ValueError("status mode requires a status")
        return [_session_query(member_id=member_id, page=page, limit=limit, status=status)]
    raise ValueError(f"unknown session list mode: {mode}")


def merge_unfinished(pages: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Merge per-status unfinished pages. Duplicate ids collapse. History rows are not added."""

    merged: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for page in pages:
        for session in page.get("sessions") or []:
            if not isinstance(session, Mapping):
                continue
            sid = str(session.get("id") or session.get("session_id") or "")
            if not sid or sid in merged:
                continue
            merged[sid] = dict(session)
            order.append(sid)
    return [merged[sid] for sid in order]


def history_has_more(page: Mapping[str, Any], *, page_number: int, limit: int) -> bool:
    """Load-more stops when this page is short or the server total is exhausted."""

    sessions = page.get("sessions") or []
    total = page.get("total")
    if not sessions:
        return False
    if isinstance(total, int) and page_number * limit >= total:
        return False
    if len(sessions) < limit:
        return False
    return True


def parse_sse(text: str) -> list[dict[str, Any]]:
    """Parse an SSE document into ``{event, data}`` objects. ``data`` is JSON when possible."""

    frames: list[dict[str, Any]] = []
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if normalized and not normalized.endswith("\n"):
        normalized += "\n"
    chunks = normalized.split("\n\n")
    for chunk in chunks:
        parsed = parse_sse_frame(chunk)
        if parsed:
            frames.append(parsed)
    return frames


def parse_sse_frame(frame: str) -> Optional[dict[str, Any]]:
    event_name = ""
    data_lines: list[str] = []
    for raw_line in frame.split("\n"):
        line = raw_line.rstrip("\r")
        if not line or line.startswith(":"):
            continue
        if ":" in line:
            field, value = line.split(":", 1)
            if value.startswith(" "):
                value = value[1:]
        else:
            field, value = line, ""
        if field == "event":
            event_name = value
        elif field == "data":
            data_lines.append(value)
    if not event_name or not data_lines:
        return None
    raw = "\n".join(data_lines)
    try:
        data: Any = json.loads(raw)
    except json.JSONDecodeError:
        data = raw
    return {"event": event_name, "data": data}


def _indicators(report: Mapping[str, Any]) -> list[Any]:
    nested = report.get("record") if isinstance(report.get("record"), Mapping) else {}
    indicators = report.get("indicators")
    if indicators is None and nested:
        indicators = nested.get("indicators")
    return list(indicators or [])


def _session_query(
    *,
    member_id: Optional[str],
    page: int,
    limit: int,
    status: Optional[str],
) -> dict[str, Any]:
    query: dict[str, Any] = {"page": int(page), "limit": int(limit)}
    if member_id:
        query["member_id"] = member_id
    if status:
        query["status"] = status
    return {"method": "GET", "path": "/api/skill/sessions", "query": query}
