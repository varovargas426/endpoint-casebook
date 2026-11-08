from pathlib import Path
import json
import unittest
from casebook import investigate, render


class CaseTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).resolve().parents[1] / "examples/endpoint.jsonl"
        self.events = [json.loads(s) for s in path.read_text().splitlines()]

    def test_worked_case_from_unordered_records(self):
        result = investigate(reversed(self.events), "workstation-07", "p-office")
        self.assertEqual([r["id"] for r in result], ["E01","E02","E03","E04","E05"])

    def test_window_and_html(self):
        self.events[4]["time"] = "2026-02-01T09:11:01Z"
        self.events[0]["detail"] = "<script>alert(1)</script>"
        result = investigate(self.events, "workstation-07", "p-office", 1)
        self.assertNotIn("E05", [r["id"] for r in result])
        html = render("workstation-07","p-office",result)
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>", html)

    def test_missing_root(self):
        with self.assertRaisesRegex(ValueError,"root"):
            investigate(self.events,"workstation-08","p-office")
