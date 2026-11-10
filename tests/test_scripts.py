"""Run the skill scripts against a local mock. No production traffic."""

from __future__ import annotations

import json
import os
import subprocess
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "caremax-auth" / "scripts"


class MockState:
    def __init__(self):
        self.requests = []
        self.handler = None


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, _format, *_args):
        return

    def _dispatch(self):
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""
        parsed = urllib.parse.urlsplit(self.path)
        item = {
            "method": self.command,
            "path": parsed.path,
            "query": urllib.parse.parse_qs(parsed.query),
            "headers": {key.lower(): value for key, value in self.headers.items()},
            "body": body,
        }
        self.server.state.requests.append(item)  # type: ignore[attr-defined]
        status, payload, content_type = self.server.state.handler(item)  # type: ignore[attr-defined]
        if not isinstance(payload, (bytes, bytearray)):
            payload = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        self._dispatch()

    def do_POST(self):
        self._dispatch()

    def do_PUT(self):
        self._dispatch()

    def do_DELETE(self):
        self._dispatch()


class MockServer:
    def __init__(self, handler):
        self.state = MockState()
        self.state.handler = handler
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.httpd.state = self.state
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    @property
    def base_url(self):
        host, port = self.httpd.server_address
        return f"http://{host}:{port}"

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=3)


def run_script(tmp, name, args, base_url, extra_env=None):
    env = os.environ.copy()
    env["HOME"] = str(tmp)
    env["CAREMAX_SKIP_BROWSER"] = "1"
    env.pop("CAREMAX_CREDENTIALS_FILE", None)
    if extra_env:
        env.update(extra_env)
    completed = subprocess.run(
        ["bash", str(SCRIPTS / name), *args],
        cwd=str(tmp),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed


def write_creds(tmp, base_url, *, token="sk-caremax-test", expired=False, refresh="rt-caremax-test"):
    creds = tmp / ".caremax"
    creds.mkdir(parents=True, exist_ok=True)
    expires = "2000-01-01T00:00:00Z" if expired else "2099-01-01T00:00:00Z"
    (creds / "credentials.json").write_text(json.dumps({
        "access_token": token,
        "refresh_token": refresh,
        "expires_at": expires,
        "scope": "read:indicators read:records read:members write:upload write:ocr search:records",
        "base_url": base_url,
    }), encoding="utf-8")


def last_json(text):
    for line in reversed(text.splitlines()):
        line = line.strip()
        if line.startswith("{") or line.startswith("["):
            return json.loads(line)
    raise AssertionError(f"no JSON in output:\n{text}")


def json_lines(text):
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("{") or line.startswith("["):
            rows.append(json.loads(line))
    return rows


class ScriptContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(self.id().replace(".", "_"))
        # isolate each test under /tmp rather than the repo
        import tempfile
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmpdir.name)

    def tearDown(self):
        if hasattr(self, "server"):
            self.server.close()
        self._tmpdir.cleanup()

    def start(self, handler):
        self.server = MockServer(handler)
        return self.server

    def test_missing_credentials(self):
        completed = run_script(self.tmp, "api-call.sh", ["GET", "/api/skill/indicators"], "http://127.0.0.1")
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(last_json(completed.stdout)["error"], "no_credentials")

    def test_expired_token_refreshes_before_the_call(self):
        seen = []

        def handler(item):
            seen.append(item)
            if item["path"] == "/api/auth/device/refresh":
                self.assertIn(b"rt-caremax-old", item["body"])
                return 200, {
                    "access_token": "sk-caremax-new",
                    "refresh_token": "rt-caremax-new",
                    "expires_in": 3600,
                    "scope": "read:records",
                }, "application/json"
            self.assertEqual(item["headers"].get("authorization"), "Bearer sk-caremax-new")
            return 200, {"indicators": []}, "application/json"

        server = self.start(handler)
        write_creds(self.tmp, server.base_url, token="sk-caremax-old", expired=True, refresh="rt-caremax-old")
        completed = run_script(self.tmp, "api-call.sh", ["GET", "/api/skill/indicators"], server.base_url)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(last_json(completed.stdout), {"indicators": []})
        self.assertEqual([item["path"] for item in seen], ["/api/auth/device/refresh", "/api/skill/indicators"])
        stored = json.loads((self.tmp / ".caremax" / "credentials.json").read_text(encoding="utf-8"))
        self.assertEqual(stored["access_token"], "sk-caremax-new")
        self.assertEqual(stored["refresh_token"], "rt-caremax-new")

    def test_invalid_token_retries_once(self):
        calls = {"api": 0}

        def handler(item):
            if item["path"] == "/api/auth/device/refresh":
                return 200, {
                    "access_token": "sk-caremax-refreshed",
                    "refresh_token": "rt-caremax-test",
                    "expires_in": 3600,
                }, "application/json"
            calls["api"] += 1
            if calls["api"] == 1:
                self.assertEqual(item["headers"].get("authorization"), "Bearer sk-caremax-stale")
                return 401, {"error": "无效的 API Token", "code": "invalid_token"}, "application/json"
            self.assertEqual(item["headers"].get("authorization"), "Bearer sk-caremax-refreshed")
            return 200, {"ok": True}, "application/json"

        server = self.start(handler)
        write_creds(self.tmp, server.base_url, token="sk-caremax-stale")
        completed = run_script(self.tmp, "api-call.sh", ["GET", "/api/skill/members"], server.base_url)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(last_json(completed.stdout), {"ok": True})
        self.assertEqual(calls["api"], 2)

    def test_auth_flow_saves_token(self):
        polls = {"n": 0}

        def handler(item):
            if item["path"] == "/api/auth/device":
                body = json.loads(item["body"].decode())
                self.assertEqual(body["client_id"], "caremax-agent")
                self.assertIn("read:records", body["scope"])
                return 200, {
                    "device_code": "device-test",
                    "verification_uri_complete": "http://127.0.0.1/authorize",
                    "interval": 1,
                }, "application/json"
            polls["n"] += 1
            if polls["n"] == 1:
                return 200, {"error": "authorization_pending"}, "application/json"
            return 200, {
                "access_token": "sk-caremax-device",
                "refresh_token": "rt-caremax-device",
                "expires_in": 120,
                "scope": "read:records",
            }, "application/json"

        server = self.start(handler)
        completed = run_script(self.tmp, "auth-flow.sh", [server.base_url], server.base_url)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(last_json(completed.stdout)["status"], "authorized")
        stored = json.loads((self.tmp / ".caremax" / "credentials.json").read_text(encoding="utf-8"))
        self.assertEqual(stored["access_token"], "sk-caremax-device")
        self.assertEqual(stored["base_url"], server.base_url)
        self.assertGreaterEqual(polls["n"], 2)

    def test_unfinished_and_history_use_different_queries(self):
        def handler(item):
            status = (item["query"].get("status") or [None])[0]
            if status:
                if status == "error":
                    return 200, {"sessions": [{"id": "pending-1", "status": "error"}], "total": 1, "page": 1, "limit": 20}, "application/json"
                return 200, {"sessions": [], "total": 0, "page": 1, "limit": 20}, "application/json"
            self.assertNotIn("status", item["query"])
            self.assertEqual(item["query"].get("member_id"), ["mem-1"])
            self.assertEqual(item["query"].get("page"), ["2"])
            sessions = [
                {"id": "done-1", "status": "completed", "reports": [{"id": "r1", "has_abnormality": 0}]},
                *({"id": f"done-{index}", "status": "completed"} for index in range(2, 21)),
            ]
            return 200, {"sessions": sessions, "total": 45, "page": 2, "limit": 20}, "application/json"

        server = self.start(handler)
        write_creds(self.tmp, server.base_url)
        unfinished = run_script(self.tmp, "sessions-list.sh", ["unfinished", "--member", "mem-1"], server.base_url)
        self.assertEqual(unfinished.returncode, 0, unfinished.stderr)
        payload = last_json(unfinished.stdout)
        self.assertEqual(payload["mode"], "unfinished")
        self.assertEqual([row["id"] for row in payload["sessions"]], ["pending-1"])
        statuses = [
            (item["query"].get("status") or [None])[0]
            for item in self.server.state.requests
            if item["path"] == "/api/skill/sessions"
        ]
        import sys
        sys.path.insert(0, str(SCRIPTS / "lib"))
        import contracts
        self.assertEqual(statuses, list(contracts.UNFINISHED_STATUSES))
        self.assertNotIn(None, statuses)

        self.server.state.requests.clear()
        history = run_script(
            self.tmp, "sessions-list.sh",
            ["history", "--member", "mem-1", "--page", "2", "--limit", "20"],
            server.base_url,
        )
        self.assertEqual(history.returncode, 0, history.stderr)
        page = last_json(history.stdout)
        self.assertEqual(page["mode"], "history")
        self.assertIsNone(page["status"])
        self.assertEqual(page["sessions"][0]["id"], "done-1")
        self.assertTrue(page["has_more"])
        self.assertEqual(len(self.server.state.requests), 1)
        self.assertNotIn("status", self.server.state.requests[0]["query"])

    def test_empty_unfinished_is_not_cloned_from_history(self):
        def handler(item):
            if "status" in item["query"]:
                return 200, {"sessions": [], "total": 0, "page": 1, "limit": 20}, "application/json"
            return 200, {
                "sessions": [{"id": "done-9", "status": "completed"}],
                "total": 1,
                "page": 1,
                "limit": 20,
            }, "application/json"

        server = self.start(handler)
        write_creds(self.tmp, server.base_url)
        unfinished = run_script(self.tmp, "sessions-list.sh", ["unfinished", "--member", "mem-9"], server.base_url)
        history = run_script(self.tmp, "sessions-list.sh", ["history", "--member", "mem-9"], server.base_url)
        self.assertEqual(last_json(unfinished.stdout)["sessions"], [])
        self.assertEqual(last_json(history.stdout)["sessions"][0]["status"], "completed")
        self.assertFalse(last_json(history.stdout)["has_more"])

    def test_ocr_202_and_already_completed(self):
        def handler(item):
            self.assertEqual(item["method"], "POST")
            self.assertEqual(item["path"], "/api/sessions/sess-1/ocr")
            self.assertIn("text/event-stream", item["headers"].get("accept", ""))
            if item["headers"].get("x-test-case") == "done":
                return 400, {"error": "Session already completed", "status": "completed", "session_id": "sess-1"}, "application/json"
            return 202, {
                "session_id": "sess-1",
                "status": "queued",
                "accepted": True,
                "report_count": 0,
            }, "application/json"

        server = self.start(handler)
        write_creds(self.tmp, server.base_url)
        accepted = run_script(self.tmp, "ocr-stream.sh", ["sess-1"], server.base_url)
        self.assertEqual(accepted.returncode, 0, accepted.stderr)
        event = last_json(accepted.stdout)
        self.assertEqual(event["step"], "accepted")
        self.assertEqual(event["http_status"], 202)
        self.assertTrue(event["accepted"])
        self.assertEqual(event["status"], "queued")

        def done_handler(item):
            return 400, {"error": "Session already completed", "status": "completed", "session_id": "sess-1"}, "application/json"

        self.server.state.handler = done_handler
        self.server.state.requests.clear()
        refused = run_script(self.tmp, "ocr-kick.sh", ["sess-1"], server.base_url)
        self.assertEqual(refused.returncode, 1)
        error = last_json(refused.stdout)
        self.assertEqual(error["step"], "error")
        self.assertEqual(error["code"], "session_already_completed")
        self.assertEqual(error["error"], "Session already completed")
        self.assertEqual(len(self.server.state.requests), 1)

    def test_confirm_routes_and_does_not_retry_completed(self):
        calls = []

        def handler(item):
            calls.append((item["method"], item["path"]))
            if item["path"].endswith("/status"):
                return 200, {"session_id": "sess-2", "status": self.status}, "application/json"
            if item["path"].endswith("/confirm"):
                return self.confirm_status, self.confirm_body, "application/json"
            if item["path"] == "/api/records":
                body = json.loads(item["body"].decode())
                self.assertEqual(body["records"][0]["id"], "rec-1")
                self.assertEqual(body["records"][0]["has_abnormality"], 0)
                return 200, {"success": True, "normalization": {}}, "application/json"
            return 500, {"error": "unexpected", "path": item["path"]}, "application/json"

        server = self.start(handler)
        write_creds(self.tmp, server.base_url)
        confirm_file = self.tmp / "confirm.json"
        confirm_file.write_text(json.dumps({
            "reports": [{"record": {"report_title": "血常规", "has_abnormality": 0}, "reportType": "lab", "indicators": [{"name": "白细胞"}]}],
        }), encoding="utf-8")
        # indicators live on the report object in this fixture; the gate looks at report.indicators or record.indicators
        confirm_file.write_text(json.dumps({
            "reports": [{
                "reportType": "lab",
                "indicators": [{"name": "白细胞", "value": "5", "is_abnormal": 0}],
                "record": {"report_title": "血常规"},
            }],
        }), encoding="utf-8")

        self.status = "awaiting_confirm"
        self.confirm_status = 200
        self.confirm_body = {"success": True, "message": "1 report(s) saved", "recordIds": ["rec-1"]}
        saved = run_script(self.tmp, "save-reports.sh", ["--session", "sess-2", "--file", str(confirm_file)], server.base_url)
        self.assertEqual(saved.returncode, 0, saved.stdout + saved.stderr)
        self.assertEqual(last_json(saved.stdout)["action"], "saved")
        self.assertIn(("POST", "/api/skill/sessions/sess-2/confirm"), calls)

        calls.clear()
        self.status = "completed"
        refused = run_script(self.tmp, "save-reports.sh", ["--session", "sess-2", "--file", str(confirm_file)], server.base_url)
        self.assertEqual(refused.returncode, 1)
        self.assertEqual(last_json(refused.stdout)["error"], "Session already completed")
        self.assertFalse(any(path.endswith("/confirm") for _method, path in calls))

        calls.clear()
        self.status = "saving"
        waiting = run_script(self.tmp, "save-reports.sh", ["--session", "sess-2", "--file", str(confirm_file)], server.base_url)
        self.assertEqual(waiting.returncode, 1)
        self.assertEqual(last_json(waiting.stdout)["action"], "wait_saving")
        self.assertFalse(any(path.endswith("/confirm") for _method, path in calls))

        calls.clear()
        self.status = "awaiting_confirm"
        self.confirm_status = 202
        self.confirm_body = {"accepted": True, "status": "saving", "session_id": "sess-2"}
        async_save = run_script(self.tmp, "save-reports.sh", ["--session", "sess-2", "--file", str(confirm_file)], server.base_url)
        self.assertEqual(async_save.returncode, 0, async_save.stdout)
        self.assertEqual(last_json(async_save.stdout)["action"], "saving")
        self.assertFalse(last_json(async_save.stdout)["retry_confirm"])
        self.assertEqual(sum(1 for method, path in calls if path.endswith("/confirm")), 1)

        calls.clear()
        self.confirm_status = 400
        self.confirm_body = {"error": "Session already completed", "status": "completed"}
        raced = run_script(self.tmp, "save-reports.sh", ["--session", "sess-2", "--file", str(confirm_file)], server.base_url)
        self.assertEqual(raced.returncode, 1)
        self.assertEqual(last_json(raced.stdout)["action"], "refuse_completed")
        self.assertEqual(sum(1 for method, path in calls if path.endswith("/confirm")), 1)

        empty = self.tmp / "empty.json"
        empty.write_text(json.dumps({
            "reports": [{"reportType": "lab", "indicators": [], "record": {"report_title": "空指标"}}],
        }), encoding="utf-8")
        calls.clear()
        blocked = run_script(self.tmp, "save-reports.sh", ["--session", "sess-2", "--file", str(empty)], server.base_url)
        self.assertEqual(blocked.returncode, 1)
        self.assertEqual(last_json(blocked.stdout)["action"], "rejected")
        self.assertFalse(any(path.endswith("/confirm") for _method, path in calls))

        update = self.tmp / "update.json"
        update.write_text(json.dumps({
            "member_id": "mem-1",
            "records": [{
                "id": "rec-1",
                "report_title": "总检综述与医生建议",
                "report_type": "imaging",
                "has_abnormality": 0,
                "test_date": "2020-03-01",
                "indicators": [],
            }],
        }), encoding="utf-8")
        calls.clear()
        updated = run_script(self.tmp, "save-reports.sh", ["--update", "--file", str(update)], server.base_url)
        self.assertEqual(updated.returncode, 0, updated.stdout + updated.stderr)
        self.assertEqual(last_json(updated.stdout)["action"], "updated")
        self.assertEqual(calls, [("POST", "/api/records")])

    def test_chat_sse_posts_event_stream_accept(self):
        def handler(item):
            self.assertEqual(item["path"], "/api/skill/chat")
            self.assertIn("text/event-stream", item["headers"].get("accept", ""))
            body = json.loads(item["body"].decode())
            self.assertEqual(body["question"], "我的肾脏怎么样")
            self.assertEqual(body["memberId"], "mem-1")
            self.assertEqual(body["recordId"], "rec-text")
            self.assertIs(body["deepThinking"], False)
            raw = "\n".join([
                "event: status",
                'data: {"stage":"accepted","conversationId":"c1","isNew":true,"mode":"fast","userMessageId":"u1"}',
                "",
                "event: sources",
                'data: {"sources":[{"id":"rec-text","title":"总检综述与医生建议","date":"2020-03-01","snippet":"报告概览：异常","hasAbnormality":false,"matchType":"pinned","indicators":[]}]}',
                "",
                "event: delta",
                'data: {"delta":"这份报告已标记为不异常。"}',
                "",
                "event: citations",
                'data: {"citations":[{"index":1,"source":"总检综述与医生建议","relevance":"高","quote":"医生建议","recordId":"rec-text"}]}',
                "",
                "event: done",
                'data: {"requestId":"req-1","conversationId":"c1","messageId":"m1","userMessageId":"u1"}',
                "",
            ])
            return 200, raw.encode("utf-8"), "text/event-stream; charset=utf-8"

        server = self.start(handler)
        write_creds(self.tmp, server.base_url)
        completed = run_script(
            self.tmp,
            "chat-stream.sh",
            ["--question", "我的肾脏怎么样", "--member", "mem-1", "--record", "rec-text"],
            server.base_url,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        events = json_lines(completed.stdout)
        self.assertEqual([item["event"] for item in events], ["status", "sources", "delta", "citations", "done"])
        source = events[1]["data"]["sources"][0]
        import sys
        sys.path.insert(0, str(SCRIPTS / "lib"))
        import contracts
        self.assertIs(
            contracts.interpret_cited_abnormality(
                raw_has_abnormality=0,
                source_has_abnormality=source["hasAbnormality"],
                snippet=source["snippet"],
            ),
            False,
        )
        self.assertIs(
            contracts.interpret_cited_abnormality(raw_has_abnormality=None, snippet=source["snippet"]),
            None,
        )
        self.assertIs(
            contracts.interpret_cited_abnormality(raw_has_abnormality=1, snippet="表述正常"),
            True,
        )

    def test_chat_error_event_and_json_fallback(self):
        mode = {"json": False}

        def handler(item):
            if mode["json"]:
                return 200, {
                    "conversationId": "c9",
                    "answer": "json only",
                    "citations": [],
                }, "application/json"
            raw = 'event: error\ndata: {"error":"chat_failed","requestId":"req-9"}\n\n'
            return 200, raw.encode("utf-8"), "text/event-stream"

        server = self.start(handler)
        write_creds(self.tmp, server.base_url)
        failed = run_script(self.tmp, "chat-stream.sh", ["--question", "hello"], server.base_url)
        self.assertEqual(failed.returncode, 1)
        self.assertEqual(last_json(failed.stdout)["data"]["error"], "chat_failed")
        mode["json"] = True
        fallback = run_script(self.tmp, "chat-stream.sh", ["--question", "hello"], server.base_url)
        self.assertEqual(fallback.returncode, 0, fallback.stdout)
        self.assertEqual(last_json(fallback.stdout)["event"], "json")
        self.assertNotIn("sources", last_json(fallback.stdout)["data"])

    def test_upload_quick_log_presets_and_download(self):
        def handler(item):
            if item["path"] == "/api/sessions/upload":
                self.assertIn(b'name="files"', item["body"])
                self.assertIn(b'name="member_id"', item["body"])
                self.assertIn("report.jpg".encode(), item["body"])
                return 200, {
                    "session_id": "sess-up",
                    "member_id": "mem-1",
                    "files": [{"id": "file-1", "original_name": "report.jpg"}],
                }, "application/json"
            if item["path"] == "/api/indicators/quick-log":
                body = json.loads(item["body"].decode())
                self.assertEqual(body["preset_key"], "weight")
                self.assertEqual(body["value"], "61")
                self.assertEqual(body["member_id"], "mem-1")
                self.assertNotIn("memberId", body)
                return 200, {"success": True, "record_id": "rec-quick"}, "application/json"
            if item["path"] == "/api/indicators":
                self.assertEqual(item["query"].get("category"), ["common_indicator"])
                return 200, {"indicators": [{
                    "id": "ind-1",
                    "canonical_name": "weight",
                    "display_name": "体重",
                    "canonical_unit": "kg",
                    "category": "common_indicator",
                }]}, "application/json"
            if item["path"] == "/api/sessions/file-content/file-1":
                return 200, b"image-bytes", "image/jpeg"
            return 404, {"error": "not_found", "path": item["path"]}, "application/json"

        server = self.start(handler)
        write_creds(self.tmp, server.base_url)
        report = self.tmp / "report.jpg"
        report.write_bytes(b"not-a-real-image")
        uploaded = run_script(self.tmp, "upload.sh", ["--member", "mem-1", str(report)], server.base_url)
        self.assertEqual(uploaded.returncode, 0, uploaded.stdout + uploaded.stderr)
        self.assertEqual(last_json(uploaded.stdout)["session_id"], "sess-up")

        logged = run_script(
            self.tmp, "quick-log.sh",
            ["weight", "61", "--unit", "kg", "--member", "mem-1"],
            server.base_url,
        )
        self.assertEqual(logged.returncode, 0, logged.stdout + logged.stderr)
        self.assertTrue(last_json(logged.stdout)["success"])

        presets = run_script(self.tmp, "list-system-presets.sh", [], server.base_url)
        self.assertEqual(presets.returncode, 0, presets.stderr)
        self.assertEqual(last_json(presets.stdout)["presets"][0]["preset_key"], "weight")
        self.assertNotIn(
            "/api/indicators/system-presets",
            [item["path"] for item in self.server.state.requests],
        )

        destination = self.tmp / "downloaded.jpg"
        downloaded = run_script(self.tmp, "download-file.sh", ["file-1", str(destination)], server.base_url)
        self.assertEqual(downloaded.returncode, 0, downloaded.stdout + downloaded.stderr)
        self.assertEqual(destination.read_bytes(), b"image-bytes")

    def test_session_status_and_member_query_shape(self):
        def handler(item):
            if item["path"] == "/api/skill/sessions/sess-3/status":
                return 200, {
                    "session_id": "sess-3",
                    "status": "processing",
                    "report_count": 0,
                    "is_stale": False,
                    "pipeline": {"completedStep": "ocr", "pageCount": 2, "ocrCompleted": 1, "ocrFailed": 0},
                    "error": None,
                }, "application/json"
            if item["path"] == "/api/skill/records/query":
                body = json.loads(item["body"].decode())
                self.assertEqual(body["memberId"], "mem-1")
                self.assertEqual(body["searchText"], "肝功能")
                self.assertNotIn("member_id", body)
                return 200, {"type": "search", "data": [], "totalCount": 0, "semanticHits": [], "rag": None}, "application/json"
            return 404, {"error": "not_found"}, "application/json"

        server = self.start(handler)
        write_creds(self.tmp, server.base_url)
        status = run_script(self.tmp, "session-status.sh", ["sess-3"], server.base_url)
        self.assertEqual(status.returncode, 0, status.stderr)
        self.assertEqual(last_json(status.stdout)["pipeline"]["completedStep"], "ocr")
        query = run_script(
            self.tmp,
            "api-call.sh",
            ["POST", "/api/skill/records/query", '{"searchText":"肝功能","memberId":"mem-1"}'],
            server.base_url,
        )
        self.assertEqual(query.returncode, 0, query.stdout + query.stderr)
        self.assertEqual(last_json(query.stdout)["type"], "search")


if __name__ == "__main__":
    unittest.main()
