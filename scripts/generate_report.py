#!/usr/bin/env python3
"""Regenerate docs/technical-report.html and docs/AXK-Capstone-Technical-Report.pdf.

Edit scripts/report_body.html (content) or scripts/report.css (layout), then run:
    python3 scripts/generate_report.py
Needs playwright with chromium installed. The report must stay at 5 pages or fewer.
"""

from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
DOCS = HERE.parent / "docs"
HTML_OUT = DOCS / "technical-report.html"
PDF_OUT = DOCS / "AXK-Capstone-Technical-Report.pdf"


def build_html():
    css = (HERE / "report.css").read_text()
    body = (HERE / "report_body.html").read_text()
    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n'
        "<title>AXK Network: Technical Report</title>\n"
        f"<style>\n{css}\n</style>\n</head>\n<body>\n{body}\n</body>\n</html>\n"
    )


def main():
    HTML_OUT.write_text(build_html())
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(HTML_OUT.as_uri())
        page.evaluate("document.fonts.ready")
        page.wait_for_timeout(500)
        page.pdf(path=str(PDF_OUT), format="A4", print_background=True, prefer_css_page_size=True)
        browser.close()
    print(f"wrote {HTML_OUT} and {PDF_OUT}")


if __name__ == "__main__":
    main()
