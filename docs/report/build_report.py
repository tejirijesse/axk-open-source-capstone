"""Build docs/AXK_Technical_Report.pdf from report.html and the latest test results.

Every figure in the report comes from docs/testing/*.json (written by scripts/test_compat.py and
scripts/measure_performance.py), so re-running the tests and this script keeps the report honest.

    pip install playwright matplotlib && python -m playwright install chromium
    python3 docs/report/build_report.py
"""

import json
import os
import re
import statistics
import subprocess

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.dirname(HERE)
TESTING = os.path.join(DOCS, "testing")
OUT_PDF = os.path.join(DOCS, "AXK_Technical_Report.pdf")
GREEN, GREY, AMBER = "#1F6B55", "#9AA5A0", "#C98A1B"


def load(name):
    path = os.path.join(TESTING, name)
    return json.load(open(path)) if os.path.exists(path) else None


def chart_transactions(perf, path):
    steps = perf["trade_on_testnet"]["seconds"]
    names, secs = list(steps), list(steps.values())
    fig, ax = plt.subplots(figsize=(6.2, 2.2), dpi=200)
    ax.barh(names[::-1], secs[::-1], color=GREEN)
    for i, v in enumerate(secs[::-1]):
        ax.text(v + 0.5, i, f"{v:.1f} s", va="center", fontsize=7)
    ax.set_xlabel("seconds (Stellar testnet, includes ledger confirmation)", fontsize=7)
    ax.tick_params(labelsize=7)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def chart_compat(compat, path):
    rows = compat["results"]
    groups = [("chromium", "Chromium"), ("firefox", "Firefox"), ("webkit", "WebKit")]
    sizes = ["phone", "tablet", "desktop"]
    fig, ax = plt.subplots(figsize=(6.2, 2.2), dpi=200)
    width = 0.2
    for i, size in enumerate(sizes):
        vals = [statistics.median([r["ready_ms"] for r in rows if r["engine"] == e and r["size"] == size
                                   and r["profile"] == "normal"]) for e, _ in groups]
        ax.bar([g + (i - 1) * width for g in range(3)], vals, width, label=size,
               color=[GREEN, GREY, "#5B8C7B"][i])
    low = [r["ready_ms"] for r in rows if r["profile"].startswith("low-end")]
    ax.bar([3], [statistics.median(low)], width * 1.2, color=AMBER, label="low-end phone")
    ax.set_xticks(range(4), [g for _, g in groups] + ["Chromium\n4x CPU, slow 3G"], fontsize=7)
    ax.set_ylabel("median ready time (ms)", fontsize=7)
    ax.tick_params(labelsize=7)
    ax.legend(fontsize=6, frameon=False, ncol=4)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def compat_rows(compat):
    out = []
    for engine in ("chromium", "firefox", "webkit"):
        for size in ("phone", "tablet", "desktop"):
            sel = [r for r in compat["results"] if r["engine"] == engine and r["size"] == size and r["profile"] == "normal"]
            out.append((engine, size, sel))
    out.append(("chromium", "phone, 4x CPU + slow 3G", [r for r in compat["results"] if r["profile"].startswith("low-end")]))
    html = []
    for engine, size, sel in out:
        ok = sum(1 for r in sel if r["status"] == 200 and r["rendered"])
        html.append(f"<tr><td>{engine}</td><td>{size}</td><td>{ok}/{len(sel)}</td>"
                    f"<td>{round(statistics.median(r['ready_ms'] for r in sel))}</td><td>{max(r['ready_ms'] for r in sel)}</td>"
                    f"<td>{sum(len(r['js_errors']) for r in sel)}</td><td>{sum(1 for r in sel if r['horizontal_overflow'])}</td></tr>")
    return "\n".join(html)


def main():
    perf, compat = load("performance.json"), load("compatibility-local.json")
    vercel = load("compatibility-vercel.json")
    chart_transactions(perf, os.path.join(HERE, "chart_transactions.png"))
    chart_compat(compat, os.path.join(HERE, "chart_compat.png"))

    lat = perf["latency"]
    total_loads = len(compat["results"]) + (len(vercel["results"]) if vercel else 0)
    ok_loads = sum(1 for r in compat["results"] + (vercel["results"] if vercel else [])
                   if r["status"] == 200 and r["rendered"] and not r["js_errors"])
    values = {
        "LAT_PAGE": lat["GET /trade (page)"]["median_ms"],
        "LAT_TRACE": lat["GET /trace/lot (public page with QR)"]["median_ms"],
        "LAT_API": lat["API lot detail"]["median_ms"],
        "LAT_EPCIS": lat["EPCIS export"]["median_ms"],
        "TX_TOTAL": perf["trade_on_testnet"]["total_s"],
        "TX_SETTLE": perf["trade_on_testnet"]["seconds"]["settle (4 transactions)"],
        "MEM_TOTAL": round(sum(v["rss_mb"] for v in perf["processes"].values())),
        "JS_GZ": perf["sizes"]["frontend_assets"]["public/js/trade.js"]["gzip_kb"],
        "WASM_MAX": max(perf["sizes"]["contract_wasm_kb"].values()),
        "COMPAT_ROWS": compat_rows(compat),
        "COMPAT_LOADS": total_loads, "COMPAT_OK": ok_loads,
        "BROWSERS": ", ".join(f"{k} {v}" for k, v in compat["environment"]["browsers"].items()),
        "LOWEND_MED": round(statistics.median(r["ready_ms"] for r in compat["results"] if r["profile"].startswith("low-end"))),
        "VERCEL_NOTE": (f"The same 80-load matrix against the public deployment (Vercel) passed "
                        f"{sum(1 for r in vercel['results'] if r['status'] == 200 and r['rendered'] and not r['js_errors'])}"
                        f"/{len(vercel['results'])}." if vercel else ""),
    }
    html = open(os.path.join(HERE, "report.html"), encoding="utf-8").read()
    for k, v in values.items():
        html = html.replace("{{" + k + "}}", str(v))
    left = re.findall(r"\{\{[A-Z_]+\}\}", html)
    if left:
        raise SystemExit(f"unfilled values: {left}")
    built = os.path.join(HERE, "report.built.html")
    open(built, "w", encoding="utf-8").write(html)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("file://" + built, wait_until="load")
        page.pdf(path=OUT_PDF, format="A4", print_background=True,
                 margin={"top": "14mm", "bottom": "14mm", "left": "14mm", "right": "14mm"},
                 display_header_footer=True, header_template="<span></span>",
                 footer_template='<div style="font-size:7px;color:#777;width:100%;text-align:center">'
                                 'AXK Network technical report | page <span class="pageNumber"></span> of '
                                 '<span class="totalPages"></span></div>')
        browser.close()
    pages = subprocess.run(["pdfinfo", OUT_PDF], capture_output=True, text=True).stdout
    n = int(re.search(r"Pages:\s+(\d+)", pages).group(1))
    print(f"wrote {OUT_PDF}: {n} pages")
    if n > 5:
        raise SystemExit("report is longer than the 5-page limit")


if __name__ == "__main__":
    main()
