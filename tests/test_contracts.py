"""Pin CareMax product rules that do not need a network."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "caremax-auth" / "scripts" / "lib"))

import contracts  # noqa: E402


class SavedAbnormalityTests(unittest.TestCase):
    def test_nonzero_zero_and_null(self):
        self.assertIs(contracts.saved_record_has_abnormality(0), False)
        self.assertIs(contracts.saved_record_has_abnormality(False), False)
        self.assertIs(contracts.saved_record_has_abnormality("0"), False)
        self.assertIs(contracts.saved_record_has_abnormality("false"), False)
        self.assertIs(contracts.saved_record_has_abnormality(1), True)
        self.assertIs(contracts.saved_record_has_abnormality(2), True)
        self.assertIs(contracts.saved_record_has_abnormality(True), True)
        self.assertIs(contracts.saved_record_has_abnormality("1"), True)
        self.assertIsNone(contracts.saved_record_has_abnormality(None))
        self.assertIsNone(contracts.saved_record_has_abnormality(""))
        self.assertIsNone(contracts.saved_record_has_abnormality("报告概览：异常"))
        self.assertIsNone(contracts.saved_record_has_abnormality("未见明显异常"))

    def test_production_card_only_maps_exact_one(self):
        self.assertIs(contracts.production_sources_has_abnormality(1), True)
        self.assertIs(contracts.production_sources_has_abnormality(True), True)
        self.assertIs(contracts.production_sources_has_abnormality(0), False)
        self.assertIs(contracts.production_sources_has_abnormality(2), False)
        self.assertIsNone(contracts.production_sources_has_abnormality(None))
        self.assertIs(contracts.production_sources_has_abnormality("异常"), False)

    def test_snippet_never_changes_the_decision(self):
        snippet = "报告概览：未见明显异常。正文里出现异常二字。"
        self.assertIs(
            contracts.interpret_cited_abnormality(
                raw_has_abnormality=0, source_has_abnormality=True, snippet=snippet,
            ),
            False,
        )
        self.assertIs(
            contracts.interpret_cited_abnormality(
                raw_has_abnormality=2,
                source_has_abnormality=False,
                snippet="表述正常，未见明显异常",
            ),
            True,
        )
        self.assertIsNone(
            contracts.interpret_cited_abnormality(
                raw_has_abnormality=None, snippet=snippet,
            )
        )
        self.assertIs(
            contracts.interpret_cited_abnormality(
                source_has_abnormality=False, snippet=snippet,
            ),
            False,
        )
        self.assertIsNone(
            contracts.interpret_cited_abnormality(source_has_abnormality=None, snippet=snippet)
        )

    def test_indicator_row_is_separate_from_the_record_flag(self):
        self.assertTrue(contracts.indicator_is_abnormal(1))
        self.assertTrue(contracts.indicator_is_abnormal(True))
        self.assertFalse(contracts.indicator_is_abnormal(0))
        self.assertFalse(contracts.indicator_is_abnormal(2))
        self.assertFalse(contracts.indicator_is_abnormal(None))


class ReportKindTests(unittest.TestCase):
    def test_lab_is_indicator_and_other_types_are_text(self):
        self.assertEqual(contracts.report_kind({"reportType": "lab", "indicators": []}), "indicator")
        self.assertEqual(
            contracts.report_kind({"report_type": "imaging", "summary": "未见明显异常"}),
            "text",
        )
        self.assertEqual(
            contracts.report_kind({"record": {"indicators": [{"name": "肌酐", "is_abnormal": 1}]}}),
            "indicator",
        )
        self.assertEqual(
            contracts.report_kind({"sections": [{"content_text": "医生建议"}], "summary": "异常"}),
            "text",
        )

    def test_manual_mark_and_empty_lab_gate(self):
        text = {"reportType": "imaging", "summary": "异常"}
        lab = {"reportType": "lab", "indicators": []}
        lab_with_row = {"reportType": "lab", "indicators": [{"name": "肌酐"}]}
        self.assertTrue(contracts.manual_mark_applies(text))
        self.assertFalse(contracts.manual_mark_applies(lab_with_row))
        self.assertFalse(contracts.lab_report_can_confirm(lab))
        self.assertTrue(contracts.lab_report_can_confirm(lab_with_row))
        self.assertTrue(contracts.lab_report_can_confirm(text))
        self.assertIsNone(contracts.text_report_mark_for_write(None))
        self.assertIsNone(contracts.text_report_mark_for_write("未见明显异常"))
        self.assertIsNone(contracts.text_report_mark_for_write("未设置"))
        self.assertEqual(contracts.text_report_mark_for_write(1), 1)
        self.assertEqual(contracts.text_report_mark_for_write(2), 1)
        self.assertEqual(contracts.text_report_mark_for_write(0), 0)
        self.assertEqual(contracts.text_report_mark_for_write(False), 0)


class SaveRoutingTests(unittest.TestCase):
    def test_confirm_only_when_still_reviewing(self):
        self.assertEqual(contracts.decide_save("awaiting_confirm")["action"], "confirm")
        self.assertEqual(contracts.decide_save("error")["action"], "confirm")
        refused = contracts.decide_save("completed")
        self.assertEqual(refused["action"], "refuse_completed")
        self.assertEqual(refused["error"], "Session already completed")
        self.assertFalse(refused["retry_confirm"])
        self.assertEqual(refused["next"], "POST /api/records")
        self.assertEqual(contracts.decide_save("cancelled")["action"], "refuse_completed")
        waiting = contracts.decide_save("saving")
        self.assertEqual(waiting["action"], "wait_saving")
        self.assertFalse(waiting["retry_confirm"])
        self.assertEqual(contracts.decide_save("processing")["action"], "not_ready")

    def test_explicit_update_never_confirms(self):
        decision = contracts.decide_save("awaiting_confirm", explicit_update=True)
        self.assertEqual(decision["action"], "update_record")
        self.assertEqual(decision["path"], "/api/records")
        self.assertFalse(decision["retry_confirm"])

    def test_confirm_response_shapes(self):
        saving = contracts.interpret_confirm_response(202, {"accepted": True, "status": "saving"})
        self.assertEqual(saving["action"], "saving")
        self.assertFalse(saving["retry_confirm"])
        already = contracts.interpret_confirm_response(
            202, {"accepted": False, "status": "saving", "message": "正在保存"},
        )
        self.assertEqual(already["action"], "saving")
        saved = contracts.interpret_confirm_response(
            200, {"success": True, "message": "1 report(s) saved", "recordIds": ["r1"]},
        )
        self.assertEqual(saved["action"], "saved")
        refused = contracts.interpret_confirm_response(
            400, {"error": "Session already completed", "status": "completed"},
        )
        self.assertEqual(refused["action"], "refuse_completed")
        self.assertFalse(refused["retry_confirm"])
        self.assertEqual(
            contracts.interpret_confirm_response(422, {"code": "empty_indicators"})["action"],
            "rejected",
        )
        self.assertEqual(
            contracts.interpret_confirm_response(409, {"error": "Session is not ready to confirm"})["action"],
            "not_ready",
        )


class SessionListTests(unittest.TestCase):
    def test_unfinished_filters_are_not_the_history_query(self):
        unfinished = contracts.session_list_request("unfinished", member_id="mem-1", limit=20)
        self.assertEqual([item["query"]["status"] for item in unfinished], list(contracts.UNFINISHED_STATUSES))
        for item in unfinished:
            self.assertEqual(item["path"], "/api/skill/sessions")
            self.assertEqual(item["query"]["member_id"], "mem-1")
            self.assertIn("status", item["query"])
        history = contracts.session_list_request("history", member_id="mem-1", page=2, limit=20)
        self.assertEqual(len(history), 1)
        self.assertNotIn("status", history[0]["query"])
        self.assertEqual(history[0]["query"]["page"], 2)
        self.assertEqual(history[0]["query"]["limit"], 20)

    def test_empty_unfinished_does_not_copy_history(self):
        merged = contracts.merge_unfinished([
            {"sessions": []},
            {"sessions": []},
            {"sessions": [{"id": "s1", "status": "error"}, {"id": "s1", "status": "error"}]},
        ])
        self.assertEqual([item["id"] for item in merged], ["s1"])
        self.assertEqual(contracts.merge_unfinished([{"sessions": []} for _ in contracts.UNFINISHED_STATUSES]), [])

    def test_load_more_stops_on_short_page_and_known_total(self):
        self.assertFalse(contracts.history_has_more({"sessions": [], "total": 0}, page_number=1, limit=20))
        self.assertFalse(contracts.history_has_more(
            {"sessions": [{"id": "only"}], "total": 1}, page_number=1, limit=20,
        ))
        self.assertTrue(contracts.history_has_more(
            {"sessions": [{"id": str(i)} for i in range(20)], "total": 40},
            page_number=1,
            limit=20,
        ))
        self.assertFalse(contracts.history_has_more(
            {"sessions": [{"id": str(i)} for i in range(20)], "total": 20},
            page_number=1,
            limit=20,
        ))


class SseTests(unittest.TestCase):
    def test_chat_event_frames(self):
        raw = "\n".join([
            "event: status",
            'data: {"stage":"accepted","conversationId":"c1","isNew":true,"mode":"fast"}',
            "",
            "event: sources",
            'data: {"sources":[{"id":"r1","title":"总检综述与医生建议","snippet":"异常","hasAbnormality":false,"indicators":[]}]}',
            "",
            "event: delta",
            'data: {"delta":"没有把这份报告当成异常。"}',
            "",
            "event: citations",
            'data: {"citations":[{"index":1,"source":"总检综述与医生建议","relevance":"高","quote":"医生建议","recordId":"r1"}]}',
            "",
            "event: done",
            'data: {"conversationId":"c1","messageId":"m1","userMessageId":"u1"}',
            "",
        ])
        events = contracts.parse_sse(raw)
        self.assertEqual([item["event"] for item in events], ["status", "sources", "delta", "citations", "done"])
        source = events[1]["data"]["sources"][0]
        self.assertIs(
            contracts.interpret_cited_abnormality(
                raw_has_abnormality=0,
                source_has_abnormality=source["hasAbnormality"],
                snippet=source["snippet"],
            ),
            False,
        )
        self.assertIs(
            contracts.interpret_cited_abnormality(
                raw_has_abnormality=1,
                source_has_abnormality=False,
                snippet="表述正常",
            ),
            True,
        )


if __name__ == "__main__":
    unittest.main()
