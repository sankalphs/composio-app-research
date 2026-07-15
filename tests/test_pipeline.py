import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

REQUIRED = ["id", "name", "category", "one_line", "auth_methods", "self_serve",
            "self_serve_detail", "api_surface", "mcp", "verdict", "blocker", "evidence", "confidence"]


def test_dataset_complete():
    with open(os.path.join(ROOT, "data", "apps_research.json"), encoding="utf-8") as f:
        apps = json.load(f)
    assert len(apps) == 100, f"expected 100 apps, got {len(apps)}"
    for a in apps:
        for k in REQUIRED:
            assert k in a, f"app {a.get('name','?')} missing {k}"
        # blocker is required only when the app is actually blocked
        if a["verdict"] == "blocked":
            assert a["blocker"] != "", f"app {a.get('name')} blocked but no blocker"
        assert a["verdict"] in {"ready", "ready-mcp", "buildable-effort", "blocked"}
        assert a["self_serve"] in {"self-serve", "trial", "paid-only", "gated", "partner-gated"}


def test_aggregates_consistent():
    with open(os.path.join(ROOT, "data", "aggregates.json"), encoding="utf-8") as f:
        agg = json.load(f)
    v = agg["verdict"]
    assert sum(v.values()) == 100, f"verdict counts sum to {sum(v.values())}"


def test_verification_metrics_present():
    with open(os.path.join(ROOT, "data", "verification.json"), encoding="utf-8") as f:
        ver = json.load(f)
    m = ver["metrics"]
    assert m["sample_size"] == 40
    assert m["firstpass_blocked_precision"] < 0.5, "expected first pass to over-call 'blocked'"
    assert m["corrected_blocked_precision"] == 1.0


def test_build_report_runs():
    # Guard: build_report must run and emit a self-contained HTML.
    r = subprocess.run([sys.executable, os.path.join(ROOT, "build_report.py")],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    out = os.path.join(ROOT, "report", "report.html")
    assert os.path.exists(out), "report.html not produced"
    html = open(out, encoding="utf-8").read()
    assert "const DATA" in html and "100-cell coverage map" in html
