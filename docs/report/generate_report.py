#!/usr/bin/env python3
"""Regenerate docs/technical-report.html and docs/AXK-Capstone-Technical-Report.pdf.

Edit docs/report/report_body.html (content) or docs/report/report.css (layout), then run:
    python3 docs/report/generate_report.py
Needs playwright with chromium installed, and matplotlib for the charts
(pip install playwright matplotlib && playwright install chromium).

Figures marked {{LIKE_THIS}} in the body are filled from docs/testing/*.json, which
scripts/test_compat.py and scripts/measure_performance.py write, so re-running the tests and this
script keeps the report honest. The whole PDF must stay at 5 pages or fewer.
"""

import json
import re
import statistics
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOCS = HERE.parent
TESTING = DOCS / "testing"
HTML_OUT = DOCS / "technical-report.html"
PDF_OUT = DOCS / "AXK-Capstone-Technical-Report.pdf"
MAX_PAGES = 5
ACCENT, ACCENT_2, MUTED, AMBER = "#166350", "#2cbf82", "#9aa5a0", "#c98a1b"


def load(name):
    """A results file from docs/testing/, or None if that run has not been made."""
    path = TESTING / name
    return json.loads(path.read_text()) if path.exists() else None


def chart_transactions(perf, path):
    """Horizontal bars: seconds per step of one full trade on testnet."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    steps = perf["trade_on_testnet"]["seconds"]
    names, secs = list(steps)[::-1], list(steps.values())[::-1]
    fig, ax = plt.subplots(figsize=(3.6, 2.1), dpi=220)
    ax.barh(names, secs, color=ACCENT)
    for i, v in enumerate(secs):
        ax.text(v + 0.5, i, f"{v:.1f} s", va="center", fontsize=6)
    ax.set_xlabel("seconds, including ledger confirmation", fontsize=6)
    ax.tick_params(labelsize=6)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def chart_compat(compat, path):
    """Grouped bars: median ready time per engine and size, plus the low-end phone."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = compat["results"]
    engines = [("chromium", "Chromium"), ("firefox", "Firefox"), ("webkit", "WebKit")]
    fig, ax = plt.subplots(figsize=(3.6, 2.1), dpi=220)
    width = 0.22
    for i, (size, colour) in enumerate(zip(("phone", "tablet", "desktop"), (ACCENT, ACCENT_2, MUTED))):
        vals = [statistics.median(r["ready_ms"] for r in rows
                                  if r["engine"] == e and r["size"] == size and r["profile"] == "normal")
                for e, _ in engines]
        ax.bar([g + (i - 1) * width for g in range(3)], vals, width, label=size, color=colour)
    low = statistics.median(r["ready_ms"] for r in rows if r["profile"].startswith("low-end"))
    ax.bar([3], [low], width * 1.3, color=AMBER, label="slow phone")
    ax.set_xticks(range(4), [n for _, n in engines] + ["Chromium\n4x CPU, 3G"], fontsize=6)
    ax.set_ylabel("median ready (ms)", fontsize=6)
    ax.tick_params(labelsize=6)
    ax.legend(fontsize=5.5, frameon=False, ncol=4, loc="upper left")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def compat_rows(compat):
    """One table row per engine and size, then the low-end profile."""
    groups = [(e, s, "normal", [r for r in compat["results"]
                                if r["engine"] == e and r["size"] == s and r["profile"] == "normal"])
              for e in ("chromium", "firefox", "webkit") for s in ("phone", "tablet", "desktop")]
    groups.append(("chromium", "phone", "4x CPU, slow 3G",
                   [r for r in compat["results"] if r["profile"].startswith("low-end")]))
    rows = []
    for engine, size, profile, sel in groups:
        ok = sum(1 for r in sel if r["status"] == 200 and r["rendered"])
        rows.append(f"<tr><td>{engine}</td><td>{size}</td><td>{profile}</td><td>{ok}/{len(sel)}</td>"
                    f"<td>{round(statistics.median(r['ready_ms'] for r in sel))} ms</td>"
                    f"<td>{max(r['ready_ms'] for r in sel)} ms</td>"
                    f"<td>{sum(len(r['js_errors']) for r in sel)}</td>"
                    f"<td>{sum(1 for r in sel if r['horizontal_overflow'])}</td></tr>")
    return "\n".join(rows)


def measured_values():
    """Placeholder values from the latest performance and compatibility runs."""
    perf, compat = load("performance.json"), load("compatibility-local.json")
    if not perf or not compat:
        raise SystemExit("run scripts/measure_performance.py and scripts/test_compat.py first")
    chart_transactions(perf, HERE / "chart_transactions.png")
    chart_compat(compat, HERE / "chart_compat.png")
    lat = perf["latency"]
    return {
        "PAGE_MS": lat["GET /trade (page)"]["median_ms"],
        "TRACE_MS": lat["GET /trace/lot (public page with QR)"]["median_ms"],
        "TRADE_S": perf["trade_on_testnet"]["total_s"],
        "SETTLE_S": perf["trade_on_testnet"]["seconds"]["settle (4 transactions)"],
        "MEM_MB": round(sum(v["rss_mb"] for v in perf["processes"].values())),
        "JS_GZ": perf["sizes"]["frontend_assets"]["public/js/trade.js"]["gzip_kb"],
        "WASM_KB": max(perf["sizes"]["contract_wasm_kb"].values()),
        "COMPAT_ROWS": compat_rows(compat),
    }


def build_html(values=None):
    """Inline the CSS and body fragment into one standalone HTML document, filling any values given."""
    css = (HERE / "report.css").read_text()
    body = (HERE / "report_body.html").read_text()
    for key, value in (values or {}).items():
        body = body.replace("{{" + key + "}}", str(value))
    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n'
        "<title>AXK Network: Technical Report</title>\n"
        f"<style>\n{css}\n</style>\n</head>\n<body>\n{body}\n</body>\n</html>\n"
    )


def main():
    """Write the HTML, print it to an A4 PDF with headless Chromium, and check the page count."""
    from playwright.sync_api import sync_playwright

    html = build_html(measured_values())
    left = re.findall(r"\{\{[A-Z_]+\}\}", html)
    if left:
        raise SystemExit(f"unfilled values: {left}")
    HTML_OUT.write_text(html)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(HTML_OUT.as_uri())
        page.evaluate("document.fonts.ready")
        page.wait_for_timeout(500)
        page.pdf(path=str(PDF_OUT), format="A4", print_background=True, prefer_css_page_size=True)
        browser.close()
    info = subprocess.run(["pdfinfo", str(PDF_OUT)], capture_output=True, text=True).stdout
    pages = int(re.search(r"Pages:\s+(\d+)", info).group(1))
    print(f"wrote {HTML_OUT} and {PDF_OUT}: {pages} pages")
    if pages > MAX_PAGES:
        raise SystemExit(f"report is {pages} pages; the limit is {MAX_PAGES}")


if __name__ == "__main__":
    main()
