"""Checks for the technical report source (docs/report/).

Guards the 5-page body limit and the output locations without launching a browser.

    python3 docs/report/test_generate_report.py
"""

import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import generate_report  # noqa: E402


class ReportSource(unittest.TestCase):
    def setUp(self):
        self.html = generate_report.build_html()
        self.pages = re.findall(r'<div class="page(?: ([\w-]+))?"(?: id="([\w-]+)")?>', self.html)

    def test_cover_and_contents_come_first(self):
        self.assertEqual([cls for cls, _ in self.pages[:2]], ["cover-page", "toc-page"])

    def test_body_is_at_most_five_pages(self):
        body = [pid for cls, pid in self.pages if not cls]
        self.assertTrue(1 <= len(body) <= 5, f"report body has {len(body)} pages")

    def test_body_pages_are_numbered_in_order(self):
        body = [pid for cls, pid in self.pages if not cls]
        self.assertEqual(body, [f"page-{i}" for i in range(1, len(body) + 1)])

    def test_css_is_inlined(self):
        self.assertIn("--accent", self.html)
        self.assertNotIn('<link rel="stylesheet"', self.html)

    def test_outputs_land_in_docs(self):
        docs = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.assertEqual(str(generate_report.HTML_OUT.parent), docs)
        self.assertEqual(str(generate_report.PDF_OUT.parent), docs)


if __name__ == "__main__":
    unittest.main()
