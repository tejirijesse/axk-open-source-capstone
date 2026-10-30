"""Performance and resource measurements for the running full stack.

    python3 scripts/measure_performance.py                 # read-only: API latency, resources, sizes
    AXK_PERF_TX=1 python3 scripts/measure_performance.py   # also times one full trade on Stellar testnet

Writes docs/testing/performance.json and docs/testing/performance.md.
"""

import glob
import gzip
import json
import os
import platform
import statistics
import subprocess
import time
import urllib.parse
import urllib.request

BASE = os.environ.get("AXK_BASE_URL", "http://localhost:8000").rstrip("/")
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "docs", "testing")
APP = os.path.join(ROOT, "frappe_app", "axk_capstone", "axk_capstone")
N = int(os.environ.get("AXK_PERF_N", "20"))


def get(path, data=None):
    req = urllib.request.Request(BASE + path, data=json.dumps(data).encode() if data is not None else None,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.read()


def latency(path, n=N):
    get(path)  # warm-up (fills caches the way a real visitor's first page load would)
    samples = []
    for _ in range(n):
        t = time.perf_counter()
        get(path)
        samples.append((time.perf_counter() - t) * 1000)
    samples.sort()
    return {"median_ms": round(statistics.median(samples), 1), "p95_ms": round(samples[int(0.95 * (n - 1))], 1),
            "max_ms": round(samples[-1], 1), "n": n}


def api(method, data=None):
    return json.loads(get("/api/method/axk_capstone.trade_api." + method, data))["message"]


def timed_trade():
    steps = {}

    def step(name, method, data):
        t = time.perf_counter()
        out = api(method, data)
        steps[name] = round(time.perf_counter() - t, 1)
        return out

    lot = step("register", "register_lot", {"commodity": "Coffee (parchment)", "quantity_kg": 3850, "declared_grade": "A",
                                            "origin": "Huye District, Southern Province, Rwanda", "variety": "Bourbon",
                                            "harvest_date": "2026-10-10"})
    n = lot["name"]
    step("inspect", "inspect_lot", {"name": n, "passed": 1, "grade": "A", "quantity_kg": 3820, "moisture_pct": 11.5, "notes": "perf"})
    step("fund escrow", "fund_lot", {"name": n, "amount_rwf": 250000})
    step("dispatch", "dispatch_logistics", {"name": n, "seal_number": "RW-SEAL-PERF"})
    step("port gate-in", "receive_port", {"name": n, "seal_number": "RW-SEAL-PERF", "customs_ref": "C-PERF",
                                          "port_name": "Kigali Logistics Platform", "container_id": "AXKU0000888"})
    step("settle (4 transactions)", "confirm_delivery", {"name": n})
    step("verify against chain", "verify_lot", {"name": n})
    return {"lot_ref": lot["lot_ref"], "seconds": steps, "total_s": round(sum(steps.values()), 1)}


def processes():
    """Memory and CPU of the stack's processes (macOS/Linux ps)."""
    out = subprocess.run(["ps", "-axo", "rss=,pcpu=,command="], capture_output=True, text=True).stdout
    groups = {"web (gunicorn/werkzeug)": "frappe.utils.bench_helper frappe serve", "workers": "frappe worker",
              "redis": "redis-server 127.0.0.1:1", "socketio": "socketio.js", "mariadb": "mariadbd"}
    res = {}
    for label, needle in groups.items():
        rows = [line.split(None, 2) for line in out.splitlines() if needle in line and "grep" not in line]
        if rows:
            res[label] = {"processes": len(rows), "rss_mb": round(sum(int(r[0]) for r in rows) / 1024, 1),
                          "cpu_pct": round(sum(float(r[1]) for r in rows), 1)}
    return res


def sizes():
    files = {}
    for rel in ("public/js/trade.js", "public/js/chain.js", "public/css/axk.css", "public/css/chain.css"):
        data = open(os.path.join(APP, rel), "rb").read()
        files[rel] = {"kb": round(len(data) / 1024, 1), "gzip_kb": round(len(gzip.compress(data)) / 1024, 1)}
    wasm = {os.path.basename(p): round(os.path.getsize(p) / 1024, 1)
            for p in sorted(glob.glob(os.path.join(ROOT, "contracts", "target", "wasm32v1-none", "release", "*.wasm")))}
    return {"frontend_assets": files, "contract_wasm_kb": wasm}


def main():
    overview = api("overview")
    lot = next((l for l in overview["lots"] if l["status"] == "Settled"), overview["lots"][0])
    ref = urllib.parse.quote(lot["lot_ref"])
    endpoints = {
        "GET /trade (page)": "/trade",
        "GET /trace/lot (public page with QR)": f"/trace/lot?ref={ref}",
        "API overview (all lots)": "/api/method/axk_capstone.trade_api.overview",
        "API lot detail": f"/api/method/axk_capstone.trade_api.lot?name={urllib.parse.quote(lot['name'])}",
        "API personas (balances, cached)": "/api/method/axk_capstone.trade_api.personas",
        "EPCIS export": f"/api/method/axk_capstone.epcis.lot_events?ref={ref}",
    }
    report = {"environment": {"target": BASE, "host_os": f"{platform.system()} {platform.release()} ({platform.machine()})",
                              "cpu_count": os.cpu_count(), "run_at": time.strftime("%Y-%m-%d %H:%M %Z")},
              "latency": {name: latency(path) for name, path in endpoints.items()},
              "processes": processes(), "sizes": sizes()}
    if os.environ.get("AXK_PERF_TX") == "1":
        report["trade_on_testnet"] = timed_trade()

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "performance.json"), "w") as f:
        json.dump(report, f, indent=1)

    lines = ["# Performance and resource use", "", f"Target `{BASE}` · {report['environment']['host_os']} · "
             f"{report['environment']['cpu_count']} CPUs · run {report['environment']['run_at']}", "",
             "## Response times (local server, warm cache)", "", "| Request | Median (ms) | 95th percentile (ms) | n |",
             "|---|---|---|---|"]
    lines += [f"| {k} | {v['median_ms']} | {v['p95_ms']} | {v['n']} |" for k, v in report["latency"].items()]
    if "trade_on_testnet" in report:
        t = report["trade_on_testnet"]
        lines += ["", f"## One full trade on Stellar testnet ({t['lot_ref']})", "", "| Step | Seconds |", "|---|---|"]
        lines += [f"| {k} | {v} |" for k, v in t["seconds"].items()] + [f"| **Total** | **{t['total_s']}** |"]
    lines += ["", "## Server resources", "", "| Component | Processes | Memory (MB) | CPU % at rest |", "|---|---|---|---|"]
    lines += [f"| {k} | {v['processes']} | {v['rss_mb']} | {v['cpu_pct']} |" for k, v in report["processes"].items()]
    lines += ["", "## Sizes", "", "| File | KB | gzip KB |", "|---|---|---|"]
    lines += [f"| {k} | {v['kb']} | {v['gzip_kb']} |" for k, v in report["sizes"]["frontend_assets"].items()]
    lines += [f"| contract {k} | {v} | |" for k, v in report["sizes"]["contract_wasm_kb"].items()]
    with open(os.path.join(OUT, "performance.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
