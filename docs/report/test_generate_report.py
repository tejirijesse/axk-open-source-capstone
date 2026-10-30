"""Checks for the technical report source (docs/report/).

Guards the 5-page limit and the output locations without launching a browser.

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
        self.pages = re.findall(r'<div class="page(?: [\w-]+)?" id="([\w-]+)">', self.html)

    def test_page_one_opens_with_the_title_band(self):
        first = self.html.index('id="page-1"')
        self.assertLess(first, self.html.index('class="cover"'))

    def test_report_is_at_most_five_pages(self):
        self.assertEqual(len(re.findall(r'<div class="page[" ]', self.html)), len(self.pages))
        self.assertTrue(1 <= len(self.pages) <= generate_report.MAX_PAGES, f"report has {len(self.pages)} pages")

    def test_pages_are_numbered_in_order(self):
        self.assertEqual(self.pages, [f"page-{i}" for i in range(1, len(self.pages) + 1)])

    def test_placeholders_are_named_measurements(self):
        names = set(re.findall(r"\{\{([A-Z_]+)\}\}", self.html))
        known = {"PAGE_MS", "TRACE_MS", "TRADE_S", "SETTLE_S", "MEM_MB", "JS_GZ", "WASM_KB", "COMPAT_ROWS"}
        self.assertLessEqual(names, known)

    def test_css_is_inlined(self):
        self.assertIn("--accent", self.html)
        self.assertNotIn('<link rel="stylesheet"', self.html)

    def test_outputs_land_in_docs(self):
        docs = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.assertEqual(str(generate_report.HTML_OUT.parent), docs)
        self.assertEqual(str(generate_report.PDF_OUT.parent), docs)


if __name__ == "__main__":
    unittest.main()
