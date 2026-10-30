"""Cross-browser, cross-device compatibility and page-performance test.

Loads every screen in three browser engines (Chromium: Chrome/Edge; Firefox: Gecko; WebKit: Safari) at phone,
tablet and desktop sizes, plus a low-end profile (Chromium with the CPU slowed 4x and a slow 3G connection).
For each page it records the HTTP status, page-load time, JavaScript errors, whether the layout overflows the
screen sideways, and whether the screen's main content rendered. Results go to docs/testing/compatibility.json
and docs/testing/compatibility.md; one screenshot per browser and size goes to docs/testing/screens/.

    pip install playwright && python -m playwright install chromium firefox webkit
    python3 scripts/test_compat.py                       # against http://localhost:8000 (make run-frappe)
    AXK_BASE_URL=https://axk-open-source-capstone.vercel.app python3 scripts/test_compat.py
"""

import json
import os
import platform
import statistics
import sys
import time

from playwright.sync_api import sync_playwright

BASE = os.environ.get("AXK_BASE_URL", "http://localhost:8000").rstrip("/")
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "docs", "testing")
TAG = os.environ.get("AXK_COMPAT_TAG", "local" if "localhost" in BASE else "vercel")

PAGES = ["/trade", "/trade/coop", "/trade/inspect", "/trade/buy", "/trade/logistics", "/trade/port", "/trace", "/chain"]
SIZES = {"phone": (375, 812), "tablet": (768, 1024), "desktop": (1440, 900)}
ENGINES = os.environ.get("AXK_ENGINES", "chromium,firefox,webkit").split(",")
# Content that proves the screen rendered, not just that the server answered.
READY = {"/trace": "input", "/chain": "#xt-chain, .cx-section, h1"}
SLOW_3G = {"offline": False, "latency": 400, "downloadThroughput": 400 * 1024 / 8, "uploadThroughput": 400 * 1024 / 8}


def measure(page, url, ready_selector):
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)[:200]))
    start = time.perf_counter()
    resp = page.goto(url, wait_until="load", timeout=60000)
    load_ms = (time.perf_counter() - start) * 1000
    rendered = True
    try:
        page.wait_for_selector(ready_selector, timeout=20000)
    except Exception:
        rendered = False
    ready_ms = (time.perf_counter() - start) * 1000
    overflow = page.evaluate("document.documentElement.scrollWidth > window.innerWidth + 1")
    timing = page.evaluate("""() => { const n = performance.getEntriesByType('navigation')[0];
        return n ? {dcl: n.domContentLoadedEventEnd, load: n.loadEventEnd, bytes: n.transferSize} : {}; }""")
    return {"status": resp.status if resp else None, "load_ms": round(load_ms), "ready_ms": round(ready_ms),
            "dom_content_loaded_ms": round(timing.get("dcl") or 0), "rendered": rendered,
            "horizontal_overflow": bool(overflow), "js_errors": errors}


def run_profile(p, engine, size_name, slow=False):
    browser = getattr(p, engine).launch()
    w, h = SIZES[size_name]
    ctx = browser.new_context(viewport={"width": w, "height": h}, is_mobile=(size_name == "phone" and engine != "firefox"),
                              has_touch=(size_name != "desktop"))
    page = ctx.new_page()
    if slow:
        cdp = ctx.new_cdp_session(page)
        cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})
        cdp.send("Network.enable")
        cdp.send("Network.emulateNetworkConditions", SLOW_3G)
    rows = []
    for path in PAGES:
        r = measure(page, BASE + path, READY.get(path, "main, .xt-main, h1"))
        r.update({"engine": engine, "size": size_name, "profile": "low-end (4x CPU, slow 3G)" if slow else "normal",
                  "page": path})
        rows.append(r)
        print(f"{engine:9s} {size_name:8s} {'slow' if slow else '    '} {path:18s} {r['status']} "
              f"{r['ready_ms']:6d} ms  overflow={r['horizontal_overflow']}  errors={len(r['js_errors'])}", flush=True)
    os.makedirs(os.path.join(OUT, "screens"), exist_ok=True)
    page.goto(BASE + "/trade", wait_until="load")
    page.wait_for_timeout(1500)
    shot = f"screens/{TAG}-{engine}-{size_name}{'-lowend' if slow else ''}.png"
    page.screenshot(path=os.path.join(OUT, shot), full_page=False)
    versions = browser.version
    browser.close()
    return rows, shot, versions


def main():
    results, shots, versions = [], [], {}
    with sync_playwright() as p:
        for engine in ENGINES:
            for size in SIZES:
                rows, shot, ver = run_profile(p, engine, size)
                results += rows
                shots.append(shot)
                versions[engine] = ver
        rows, shot, _ = run_profile(p, "chromium", "phone", slow=True)
        results += rows
        shots.append(shot)

    failures = [r for r in results if r["status"] != 200 or not r["rendered"] or r["js_errors"] or r["horizontal_overflow"]]
    summary = []
    for engine in ENGINES:
        for size in SIZES:
            sel = [r for r in results if r["engine"] == engine and r["size"] == size and r["profile"] == "normal"]
            summary.append((engine, size, "normal", sel))
    summary.append(("chromium", "phone", "low-end (4x CPU, slow 3G)",
                    [r for r in results if r["profile"].startswith("low-end")]))

    env = {"target": BASE, "tag": TAG, "host_os": f"{platform.system()} {platform.release()} ({platform.machine()})",
           "python": platform.python_version(), "browsers": versions, "pages": PAGES,
           "run_at": time.strftime("%Y-%m-%d %H:%M %Z")}
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, f"compatibility-{TAG}.json"), "w") as f:
        json.dump({"environment": env, "results": results, "screenshots": shots}, f, indent=1)

    lines = [f"# Compatibility and page performance ({TAG})", "",
             f"Target `{BASE}` · host {env['host_os']} · run {env['run_at']}", "",
             "Browsers: " + ", ".join(f"{k} {v}" for k, v in versions.items()), "",
             "| Engine | Size | Profile | Pages OK | Median ready (ms) | Slowest (ms) | JS errors | Sideways overflow |",
             "|---|---|---|---|---|---|---|---|"]
    for engine, size, profile, sel in summary:
        ok = sum(1 for r in sel if r["status"] == 200 and r["rendered"])
        times = [r["ready_ms"] for r in sel]
        lines.append(f"| {engine} | {size} | {profile} | {ok}/{len(sel)} | {round(statistics.median(times))} | "
                     f"{max(times)} | {sum(len(r['js_errors']) for r in sel)} | "
                     f"{sum(1 for r in sel if r['horizontal_overflow'])} |")
    lines += ["", f"Problems found: {len(failures)}"]
    for r in failures:
        lines.append(f"- {r['engine']} {r['size']} {r['page']}: status {r['status']}, rendered {r['rendered']}, "
                     f"overflow {r['horizontal_overflow']}, errors {r['js_errors'][:1]}")
    with open(os.path.join(OUT, f"compatibility-{TAG}.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
