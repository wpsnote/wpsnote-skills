#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "evals" / "scripts" / "tri_state_eval.py"

SPEC = importlib.util.spec_from_file_location("tri_state_eval", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load module from {MODULE_PATH}")
TRI_STATE_EVAL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TRI_STATE_EVAL)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class TriStateEvalTests(unittest.TestCase):
    def test_all_cases_validate(self) -> None:
        case_files = sorted((ROOT / "evals" / "cases").rglob("*.json"))
        self.assertGreaterEqual(len(case_files), 12)

        for case_file in case_files:
            with self.subTest(case=str(case_file.relative_to(ROOT))):
                case = load_json(case_file)
                errors = TRI_STATE_EVAL.validate_case(case)
                self.assertEqual(errors, [])

    def test_news_to_note_fixture_passes(self) -> None:
        report = self._grade_fixture(
            "news-to-note/save-linked-news-with-personal-insight.original.json",
            "news-to-note/save-linked-news-with-personal-insight.final.json",
            "golden/news-to-note/save-linked-news-with-personal-insight.json",
        )
        self.assertEqual(report["status"], "pass")

    def test_tag_organize_fixture_passes(self) -> None:
        report = self._grade_fixture(
            "tag-organize/merge-synonym-tags.original.json",
            "tag-organize/merge-synonym-tags.final.json",
            "golden/tag-organize/merge-synonym-tags.json",
        )
        self.assertEqual(report["status"], "pass")

    def test_wpsnote_beautifier_fixture_passes(self) -> None:
        report = self._grade_fixture(
            "wpsnote-beautifier/beautify-mixed-mainline.original.json",
            "wpsnote-beautifier/beautify-mixed-mainline.final.json",
            "golden/wpsnote-beautifier/beautify-mixed-mainline.json",
        )
        self.assertEqual(report["status"], "pass")

    def test_wps_deep_search_fixture_passes(self) -> None:
        report = self._grade_fixture(
            "wps-deep-search/time-bounded-query.original.json",
            "wps-deep-search/time-bounded-query.final.json",
            "golden/wps-deep-search/time-bounded-query.json",
        )
        self.assertEqual(report["status"], "pass")

    def test_forbidden_change_on_control_note_fails(self) -> None:
        case = load_json(
            ROOT
            / "evals"
            / "cases"
            / "golden"
            / "news-to-note"
            / "save-linked-news-with-personal-insight.json"
        )
        original = load_json(
            ROOT
            / "evals"
            / "fixtures"
            / "news-to-note"
            / "save-linked-news-with-personal-insight.original.json"
        )
        final = load_json(
            ROOT
            / "evals"
            / "fixtures"
            / "news-to-note"
            / "save-linked-news-with-personal-insight.final.json"
        )

        polluted = deepcopy(final)
        polluted["notes"]["random_note"]["body_xml"] = "<p>被误改了</p>"

        report = TRI_STATE_EVAL.build_report(case, original, polluted)
        self.assertEqual(report["status"], "assert_fail")
        joined_reasons = "\n".join(report["state_diff_report"]["failed_reasons"])
        self.assertIn("无关随手记", joined_reasons)

    def _grade_fixture(self, original_rel: str, final_rel: str, case_rel: str) -> dict:
        case = load_json(ROOT / "evals" / "cases" / case_rel)
        original = load_json(ROOT / "evals" / "fixtures" / original_rel)
        final = load_json(ROOT / "evals" / "fixtures" / final_rel)
        return TRI_STATE_EVAL.build_report(case, original, final)


if __name__ == "__main__":
    unittest.main()
