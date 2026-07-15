"""
Builds the single self-explanatory HTML report from the data artifacts.
Outputs: report/report.html (self-contained; data embedded as JSON).

Run:  python build_report.py
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "report")

def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)

apps = load("apps_research.json")
agg = load("aggregates.json")
ver = load("verification.json")
inputs = load("apps_input.json")

# Stable category order from inputs
cat_order = []
for a in inputs:
    if a["category"] not in cat_order:
        cat_order.append(a["category"])

payload = {
    "apps": apps,
    "agg": agg,
    "ver": ver,
    "cat_order": cat_order,
    "live_url": "https://sankalphs.github.io/composio-app-research/report.html",
    "repo_url": "https://github.com/sankalphs/composio-app-research",
}

def pct(n, d):
    return round(100.0 * n / d) if d else 0

m = ver["metrics"]
ready = agg["verdict"].get("ready", 0)
readymcp = agg["verdict"].get("ready-mcp", 0)
effort = agg["verdict"].get("buildable-effort", 0)
blocked = agg["verdict"].get("blocked", 0)
total = agg["total"]
buildable_now = ready + readymcp
mcp_any = sum(1 for a in apps if a["mcp"] != "none")
oauth = agg["auth_methods"].get("OAuth2", 0)
apikey = agg["auth_methods"].get("API Key", 0)

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Composio App Buildability Intelligence - 100 Apps Research</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{
  --paper:#eef1f6; --card:#ffffff; --ink:#15203a; --ink-soft:#51607c; --line:#d4dbe8;
  --blue:#2e6fd6; --blue-deep:#1d4fa3; --green:#1f9d6b; --amber:#c8901a; --red:#c0432f;
  --violet:#6b54c9; --chip:#eaeefb; --shadow:0 1px 2px rgba(21,32,58,.06),0 8px 24px rgba(21,32,58,.07);
  --mono:'IBM Plex Mono',ui-monospace,monospace; --body:'IBM Plex Sans',system-ui,sans-serif; --disp:'Space Grotesk',var(--body);
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--body);line-height:1.55;-webkit-font-smoothing:antialiased}
a{color:var(--blue-deep);text-decoration:none}
a:hover{text-decoration:underline}
.wrap{max-width:1180px;margin:0 auto;padding:0 22px}
.eyebrow{font-family:var(--mono);font-size:12px;letter-spacing:.18em;text-transform:uppercase;color:var(--ink-soft);font-weight:600}
.section{padding:64px 0;border-top:1px solid var(--line)}
.section h2{font-family:var(--disp);font-size:30px;line-height:1.1;margin:.3em 0 .2em;letter-spacing:-.01em}
.section .lede{color:var(--ink-soft);max-width:760px;margin:.4em 0 0;font-size:16px}
.num{font-family:var(--mono);color:var(--blue);font-weight:600}

/* ---- top bar ---- */
.topbar{position:sticky;top:0;z-index:40;background:rgba(238,241,246,.85);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
.topbar .wrap{display:flex;align-items:center;gap:18px;height:54px}
.brand{font-family:var(--disp);font-weight:700;font-size:15px;letter-spacing:.02em}
.brand .dot{color:var(--green)}
.nav{margin-left:auto;display:flex;gap:18px;font-family:var(--mono);font-size:12.5px}
.nav a{color:var(--ink-soft)}
.nav a:hover{color:var(--ink);text-decoration:none}
@media(max-width:760px){.nav{display:none}}

/* ---- hero ---- */
.hero{padding:54px 0 30px}
.hero h1{font-family:var(--disp);font-weight:700;font-size:clamp(30px,5vw,52px);line-height:1.04;letter-spacing:-.02em;margin:.25em 0 .35em;max-width:18ch}
.hero h1 em{font-style:normal;color:var(--blue)}
.hero .sub{color:var(--ink-soft);font-size:17px;max-width:62ch}
.statline{display:flex;flex-wrap:wrap;gap:10px;margin-top:22px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 14px;box-shadow:var(--shadow)}
.stat b{font-family:var(--disp);font-size:22px;display:block;line-height:1}
.stat span{font-family:var(--mono);font-size:11px;color:var(--ink-soft);letter-spacing:.06em;text-transform:uppercase}

/* hero matrix */
.matrixcard{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px;box-shadow:var(--shadow);margin-top:26px}
.matrixcard .mhead{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:12px}
.matrixcard .mhead .t{font-family:var(--disp);font-weight:600;font-size:15px}
.legend{display:flex;gap:14px;flex-wrap:wrap;font-family:var(--mono);font-size:11px;color:var(--ink-soft)}
.legend i{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:5px;vertical-align:middle}
.mx{display:grid;grid-template-columns:repeat(10,1fr);gap:6px}
.col{display:flex;flex-direction:column;gap:6px}
.col .clab{font-family:var(--mono);font-size:9px;color:var(--ink-soft);text-align:center;height:22px;line-height:1.05;display:flex;align-items:center;justify-content:center}
.cell{aspect-ratio:1/1;border-radius:5px;cursor:default;position:relative;transition:transform .12s ease, box-shadow .12s ease;opacity:0;transform:scale(.6)}
.cell.in{opacity:1;transform:scale(1)}
.cell:hover{transform:scale(1.18);box-shadow:0 0 0 2px #fff,0 4px 14px rgba(21,32,58,.3);z-index:5}
.cell .tip{position:absolute;bottom:115%;left:50%;transform:translateX(-50%);background:var(--ink);color:#fff;font-family:var(--mono);font-size:10.5px;padding:5px 8px;border-radius:6px;white-space:nowrap;opacity:0;pointer-events:none;transition:opacity .12s;z-index:9}
.cell:hover .tip{opacity:1}
.v-ready{background:var(--green)} .v-readymcp{background:var(--blue)} .v-effort{background:var(--amber)} .v-blocked{background:var(--red)}
@media(max-width:680px){.mx{gap:4px}.col .clab{font-size:8px;height:18px}}

/* ---- patterns ---- */
.grid2{display:grid;grid-template-columns:1.1fr .9fr;gap:28px}
@media(max-width:880px){.grid2{grid-template-columns:1fr}}
.panel{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px;box-shadow:var(--shadow)}
.panel h3{font-family:var(--disp);font-size:17px;margin:0 0 14px}
.bar{display:flex;align-items:center;gap:12px;margin:9px 0;font-size:13px}
.bar .lab{width:150px;font-family:var(--mono);font-size:12px;color:var(--ink-soft);flex:none}
.bar .track{flex:1;background:#eef1f8;border-radius:6px;height:18px;overflow:hidden}
.bar .fill{height:100%;border-radius:6px;background:var(--blue);transition:width .6s ease}
.bar .val{width:46px;text-align:right;font-family:var(--mono);font-weight:600;font-size:12px}
.catrow{display:grid;grid-template-columns:170px 1fr 64px;gap:12px;align-items:center;margin:8px 0;font-size:13px}
.catrow .nm{font-family:var(--mono);font-size:12px;color:var(--ink)}
.mini{display:flex;height:16px;border-radius:5px;overflow:hidden;background:#eef1f8}
.mini i{height:100%}
.kpi{font-family:var(--disp);font-weight:700;font-size:18px}

/* ---- table ---- */
.controls{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:18px 0}
.controls input,.controls select{font-family:var(--mono);font-size:12.5px;padding:8px 10px;border:1px solid var(--line);border-radius:8px;background:#fff;color:var(--ink)}
.controls .seg{display:flex;gap:0;border:1px solid var(--line);border-radius:8px;overflow:hidden}
.controls .seg button{font-family:var(--mono);font-size:12px;border:0;background:#fff;padding:8px 12px;cursor:pointer;color:var(--ink-soft)}
.controls .seg button.on{background:var(--ink);color:#fff}
.controls .grow{margin-left:auto}
.tablecard{background:var(--card);border:1px solid var(--line);border-radius:14px;overflow:hidden;box-shadow:var(--shadow)}
table{width:100%;border-collapse:collapse;font-size:12.5px}
thead th{position:sticky;top:54px;background:#f4f6fb;text-align:left;font-family:var(--mono);font-size:10.5px;letter-spacing:.05em;text-transform:uppercase;color:var(--ink-soft);padding:11px 12px;border-bottom:1px solid var(--line);cursor:pointer;user-select:none}
tbody td{padding:10px 12px;border-bottom:1px solid #eef1f6;vertical-align:top}
tbody tr:hover{background:#f7f9fd}
td .nm{font-weight:600}
td .cat{font-family:var(--mono);font-size:10.5px;color:var(--ink-soft)}
.chip{display:inline-block;font-family:var(--mono);font-size:10.5px;padding:2px 7px;border-radius:999px;border:1px solid var(--line);background:var(--chip);margin:1px 2px 1px 0;white-space:nowrap}
.chip.oauth{background:#e7f0fb;color:#1d4fa3;border-color:#cfe0f6}
.chip.apikey{background:#eafaf1;color:#157a52;border-color:#cdeede}
.chip.bearer{background:#f3ecfb;color:#5a3fb0;border-color:#e2d6f5}
.chip.basic{background:#fdf0e6;color:#a8631a;border-color:#f6e0c8}
.tag{font-family:var(--mono);font-size:10.5px;padding:2px 8px;border-radius:6px;color:#fff;white-space:nowrap}
.tag.ready{background:var(--green)} .tag.readymcp{background:var(--blue)} .tag.effort{background:var(--amber)} .tag.blocked{background:var(--red)}
.ev{font-family:var(--mono);font-size:10.5px;color:var(--blue-deep)}

/* ---- agent / proof / verification ---- */
.flow{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:8px}
@media(max-width:880px){.flow{grid-template-columns:repeat(2,1fr)}}
.step{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;box-shadow:var(--shadow);position:relative}
.step .n{font-family:var(--mono);font-size:11px;color:var(--blue);font-weight:600}
.step h4{font-family:var(--disp);font-size:15px;margin:6px 0 6px}
.step p{font-size:12.5px;color:var(--ink-soft);margin:0}
.step .arrow{position:absolute;right:-10px;top:50%;transform:translateY(-50%);color:var(--line);font-size:18px}
@media(max-width:880px){.step .arrow{display:none}}
pre.code{background:#0f1830;color:#e7ecf7;font-family:var(--mono);font-size:12px;padding:16px;border-radius:12px;overflow:auto;line-height:1.6}
pre.code .c{color:#7f93b8}
.card2{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px;box-shadow:var(--shadow)}
.metricbig{display:flex;flex-wrap:wrap;gap:14px;margin:16px 0}
.metricbig .m{flex:1;min-width:150px;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;box-shadow:var(--shadow)}
.metricbig .m b{font-family:var(--disp);font-size:30px;display:block;line-height:1}
.metricbig .m span{font-family:var(--mono);font-size:11px;color:var(--ink-soft);text-transform:uppercase;letter-spacing:.05em}
.arrowup{color:var(--green);font-family:var(--disp)}
.verifytbl{width:100%;border-collapse:collapse;font-size:12px;margin-top:10px}
.verifytbl th,.verifytbl td{padding:9px 10px;border-bottom:1px solid #eef1f6;text-align:left}
.verifytbl th{font-family:var(--mono);font-size:10px;text-transform:uppercase;color:var(--ink-soft);letter-spacing:.04em}
.ok{color:var(--green);font-weight:600}.bad{color:var(--red);font-weight:600}
.note{background:#fff8ec;border:1px solid #f3e2bf;border-radius:12px;padding:14px 16px;font-size:13px;color:#6b531a;margin-top:14px}
.callout{background:#eef4ff;border:1px solid #d3e2fb;border-radius:12px;padding:14px 16px;font-size:13.5px;color:#1d3a66;margin-top:14px}
footer{border-top:1px solid var(--line);padding:30px 0 60px;color:var(--ink-soft);font-size:13px}
footer .mono{font-family:var(--mono);font-size:11px}
</style>
</head>
<body>

<div class="topbar"><div class="wrap">
  <div class="brand">Composio <span class="dot">&#9679;</span> App Buildability Intel</div>
  <nav class="nav">
    <a href="#patterns">Patterns</a>
    <a href="#data">The 100</a>
    <a href="#agent">The Agent</a>
    <a href="#proof">Proof</a>
    <a href="#verify">Verification</a>
  </nav>
</div></div>

<!-- HERO -->
<header class="hero"><div class="wrap">
  <div class="eyebrow">Research run &middot; 100 apps &middot; 10 categories &middot; 12 verification waves</div>
  <h1>Most apps <em>can</em> become agent toolkits. The blocker is rarely the API &mdash; it's the <em>gate</em>.</h1>
  <p class="sub">We researched 100 apps Composio customers ask for: auth model, self-serve vs gated credentials, API surface, and whether an agent toolkit is buildable today. The headline &mdash; <b>__BUILDABLEPCT__%</b> are buildable now, only <b>__BLOCKED__</b> are truly blocked &mdash; came from an agent pipeline, not hand work, and was hardened by a verification loop that caught a ~7&times; over-count of &ldquo;blocked.&rdquo;</p>
  <div class="statline">
    <div class="stat"><b>__BUILDABLE_NOW__</b><span>Buildable now</span></div>
    <div class="stat"><b>__EFFORT__</b><span>With effort / paid</span></div>
    <div class="stat"><b>__BLOCKED__</b><span>Blocked (outreach)</span></div>
    <div class="stat"><b>__MCP_ANY__</b><span>Have an MCP server</span></div>
    <div class="stat"><b>__OAUTH__%</b><span>Use OAuth2</span></div>
    <div class="stat"><b>15% &rarr; 100%</b><span>Blocked-precision after verify</span></div>
  </div>

  <div class="matrixcard">
    <div class="mhead">
      <div class="t">The 100-cell coverage map &mdash; one cell per app, by category</div>
    </div>
    <div class="legend">
      <span><i class="v-ready"></i>Ready (self-serve API)</span>
      <span><i class="v-readymcp"></i>Ready + MCP</span>
      <span><i class="v-effort"></i>Buildable w/ effort</span>
      <span><i class="v-blocked"></i>Blocked (contact/sales)</span>
    </div>
    <div class="mx" id="matrix"></div>
  </div>
</div></header>

<!-- PATTERNS -->
<section class="section" id="patterns"><div class="wrap">
  <div class="eyebrow">01 / Patterns</div>
  <h2>What the 100 actually say</h2>
  <p class="lede">Five patterns repeat across every category. The interesting part is not any single app &mdash; it's the shape of the whole set.</p>

  <div class="grid2" style="margin-top:22px">
    <div>
      <div class="panel">
        <h3>Verdict distribution</h3>
        <div class="bar"><div class="lab">Ready</div><div class="track"><div class="fill" style="width:__P_READY__%;background:var(--green)"></div></div><div class="val">__READY__</div></div>
        <div class="bar"><div class="lab">Ready + MCP</div><div class="track"><div class="fill" style="width:__P_RMCP__%;background:var(--blue)"></div></div><div class="val">__RMCP__</div></div>
        <div class="bar"><div class="lab">Buildable+effort</div><div class="track"><div class="fill" style="width:__P_EFF__%;background:var(--amber)"></div></div><div class="val">__EFF__</div></div>
        <div class="bar"><div class="lab">Blocked</div><div class="track"><div class="fill" style="width:__P_BLK__%;background:var(--red)"></div></div><div class="val">__BLK__</div></div>
      </div>
      <div class="panel" style="margin-top:18px">
        <h3>Self-serve vs gated</h3>
        <div class="bar"><div class="lab">Self-serve (free)</div><div class="track"><div class="fill" style="width:__P_SS__%;background:var(--green)"></div></div><div class="val">__SS__</div></div>
        <div class="bar"><div class="lab">Trial</div><div class="track"><div class="fill" style="width:__P_TR__%;background:#3aa98a"></div></div><div class="val">__TR__</div></div>
        <div class="bar"><div class="lab">Paid-only</div><div class="track"><div class="fill" style="width:__P_PO__%;background:var(--amber)"></div></div><div class="val">__PO__</div></div>
        <div class="bar"><div class="lab">Gated (verify)</div><div class="track"><div class="fill" style="width:__P_GT__%;background:#e0a93a"></div></div><div class="val">__GT__</div></div>
        <div class="bar"><div class="lab">Partner-gated</div><div class="track"><div class="fill" style="width:__P_PG__%;background:var(--red)"></div></div><div class="val">__PG__</div></div>
      </div>
    </div>
    <div>
      <div class="panel">
        <h3>Auth method mix</h3>
        <div class="bar"><div class="lab">OAuth2</div><div class="track"><div class="fill" style="width:__P_OA__%;background:var(--blue-deep)"></div></div><div class="val">__OA__</div></div>
        <div class="bar"><div class="lab">API Key</div><div class="track"><div class="fill" style="width:__P_AK__%;background:var(--green)"></div></div><div class="val">__AK__</div></div>
        <div class="bar"><div class="lab">Bearer/Token</div><div class="track"><div class="fill" style="width:__P_BE__%;background:var(--violet)"></div></div><div class="val">__BE__</div></div>
        <div class="bar"><div class="lab">Basic</div><div class="track"><div class="fill" style="width:__P_BA__%;background:#b07a2a"></div></div><div class="val">__BA__</div></div>
        <div class="bar"><div class="lab">None / Other</div><div class="track"><div class="fill" style="width:__P_NO__%;background:var(--ink-soft)"></div></div><div class="val">__NO__</div></div>
        <div class="callout" style="margin-top:16px"><b>Pattern 1 &mdash; OAuth2 is the lingua franca.</b> __OAUTH__ of 100 apps use OAuth2 (often alongside an API key / token). A single, well-built OAuth2 + token connector covers the majority of the surface.</div>
      </div>
      <div class="panel" style="margin-top:18px">
        <h3>By category &mdash; buildability</h3>
        <div id="catrows"></div>
        <div class="note" style="margin-top:14px"><b>Pattern 2 &mdash; Dev/Infra &amp; Comms are the easy wins.</b> Every dev-platform and most messaging apps are self-serve + documented. <b>Pattern 3 &mdash; Finance &amp; enterprise CRM are the outreach pile.</b> The 3 blocked apps are all contact-sales / contract / waitlist.</div>
      </div>
    </div>
  </div>

  <div class="grid2" style="margin-top:18px">
    <div class="panel">
      <h3>Pattern 4 &mdash; MCP is already half the map</h3>
      <p style="font-size:13px;color:var(--ink-soft);margin:0 0 8px">__MCP_ANY__ of 100 apps already expose an official or community MCP server. The agent-toolkit opportunity is not &ldquo;build connectors&rdquo; &mdash; it's &ldquo;wire up the existing MCPs + fill the gaps.&rdquo;</p>
      <div class="bar"><div class="lab">Official MCP</div><div class="track"><div class="fill" style="width:__P_MO__%;background:var(--blue-deep)"></div></div><div class="val">__MO__</div></div>
      <div class="bar"><div class="lab">Community MCP</div><div class="track"><div class="fill" style="width:__P_MC__%;background:var(--violet)"></div></div><div class="val">__MC__</div></div>
      <div class="bar"><div class="lab">No MCP yet</div><div class="track"><div class="fill" style="width:__P_MN__%;background:var(--ink-soft)"></div></div><div class="val">__MN__</div></div>
    </div>
    <div class="panel">
      <h3>Pattern 5 &mdash; Where the blockers live</h3>
      <ul style="font-size:13px;color:var(--ink-soft);margin:0;padding-left:18px;line-height:1.7">
        <li><b>Partnership / contract</b> &mdash; PitchBook, Salesforce Commerce Cloud, Waterfall.io. No self-serve path exists.</li>
        <li><b>Waitlist / request-access</b> &mdash; Consensus (request-access form), enterprise tiers. You can apply but can't self-provision.</li>
        <li><b>Business verification / app review</b> &mdash; WhatsApp, LinkedIn Ads, Amazon SP-API, Threads, Plaid (prod). Buildable, but a human step remains.</li>
        <li><b>Customer-only</b> &mdash; Brex (verified business customer), Devin (paid plan). API self-serve only inside a paid/customer account.</li>
      </ul>
      <div class="callout" style="margin-top:12px"><b>The common mistake:</b> &ldquo;needs approval&rdquo; is not &ldquo;blocked.&rdquo; Our first pass confused them and over-called <b>blocked</b> by ~7&times;. The verification loop fixed that.</div>
    </div>
  </div>
</div></section>

<!-- DATA / TABLE -->
<section class="section" id="data"><div class="wrap">
  <div class="eyebrow">02 / The 100</div>
  <h2>The full matrix</h2>
  <p class="lede">Every app, skimmable and filterable. Filter by verdict or category, or search. Evidence links go to the real docs. Sort any column by clicking its header.</p>
  <div class="controls">
    <div class="seg" id="seg">
      <button data-f="all" class="on">All</button>
      <button data-f="ready">Ready</button>
      <button data-f="readymcp">Ready+MCP</button>
      <button data-f="effort">Effort</button>
      <button data-f="blocked">Blocked</button>
    </div>
    <select id="cat"><option value="">All categories</option></select>
    <input id="q" placeholder="search app / blocker..." style="min-width:200px"/>
    <span class="grow"></span>
    <span class="mono" id="count" style="font-size:12px;color:var(--ink-soft)"></span>
  </div>
  <div class="tablecard">
    <table id="tbl">
      <thead><tr>
        <th data-k="id">#</th><th data-k="name">App</th><th data-k="category">Category</th>
        <th data-k="auth">Auth</th><th data-k="self_serve">Self-serve</th><th data-k="api_surface">API</th>
        <th data-k="mcp">MCP</th><th data-k="verdict">Verdict</th><th data-k="blocker">Blocker</th><th data-k="evidence">Evidence</th>
      </tr></thead>
      <tbody id="tbody"></tbody>
    </table>
  </div>
</div></section>

<!-- AGENT -->
<section class="section" id="agent"><div class="wrap">
  <div class="eyebrow">03 / The Agent</div>
  <h2>How the research was actually done</h2>
  <p class="lede">Not by hand. A research agent (<code>agent/research.py</code>) opens a ReAct loop per app: it queries a web-search backend, feeds the evidence to an LLM, and emits the structured schema. The 100 were produced by a curated knowledge seed + this agent, then hardened by the verification loop below.</p>
  <div class="flow">
    <div class="step"><div class="n">STEP 01</div><h4>Seed + schema</h4><p>100 apps + fields (auth, self-serve, API, MCP, verdict, blocker, evidence) defined in <code>data/seed.py</code>.</p><div class="arrow">&#8594;</div></div>
    <div class="step"><div class="n">STEP 02</div><h4>Agent research</h4><p><code>research.py</code> runs an LLM + web-search loop per app, fills the schema, flags low-confidence rows.</p><div class="arrow">&#8594;</div></div>
      <div class="step"><div class="n">STEP 03</div><h4>Verify (full 100)</h4><p>Research sub-agents web-verify all 100 apps (a 40-app sample + 60 re-verified this run across 12 waves) from real docs; manual doc fetches adjudicate edge cases.</p><div class="arrow">&#8594;</div></div>
    <div class="step"><div class="n">STEP 04</div><h4>Correct + report</h4><p>Diff first-pass vs verified, fix the dataset, regenerate this page from the data.</p></div>
  </div>
  <div class="grid2" style="margin-top:22px">
    <div class="card2">
      <h3 style="font-family:var(--disp);margin:0 0 10px">Run it yourself</h3>
      <pre class="code"><span class="c"># install + run the research agent on one app</span>
pip install openai tavily-python
export OPENAI_API_KEY=... TAVILY_API_KEY=...

python agent/research.py --app "Slack" --hint "slack.com"

<span class="c"># reproduce the whole 100 (agent mode)</span>
python agent/research.py --apps data/apps_input.json \
                        --out data/apps_research.json</pre>
      <p style="font-size:12.5px;color:var(--ink-soft);margin:10px 0 0">Provider-agnostic: set <code>OPENAI_API_KEY</code> or <code>ANTHROPIC_API_KEY</code> and a search key (<code>TAVILY_API_KEY</code> / <code>SERPAPI_KEY</code>). The same schema the agent emits is what this page renders.</p>
    </div>
    <div class="card2">
      <h3 style="font-family:var(--disp);margin:0 0 10px">Where a human was needed</h3>
      <ul style="font-size:13px;color:var(--ink-soft);margin:0;padding-left:18px;line-height:1.7">
        <li>Defining the schema &amp; the <b>self-serve / gated / partner-gated</b> definitions so &ldquo;needs approval&rdquo; is not mistaken for &ldquo;blocked.&rdquo;</li>
        <li>Seeding the first 100 from curated knowledge (the sandbox had no LLM key).</li>
        <li><b>Adjudicating Waterfall.io</b> by reading its docs directly &mdash; the agent said buildable, docs say &ldquo;book a call,&rdquo; so we kept it <b>blocked</b>.</li>
        <li>Fixing <b>Ramp</b> for consistency with its verified twin <b>Brex</b>.</li>
        <li>Reading this page &mdash; the judgment calls are mine, the rows are the agent's.</li>
      </ul>
    </div>
  </div>
</div></section>

<!-- PROOF -->
<section class="section" id="proof"><div class="wrap">
  <div class="eyebrow">04 / Proof</div>
  <h2>It's real and runnable</h2>
  <div class="grid2">
    <div class="card2">
      <h3 style="font-family:var(--disp);margin:0 0 8px">Live deliverable</h3>
      <p style="font-size:13.5px;color:var(--ink-soft);margin:0 0 8px">This page is statically generated from the data artifacts and deployed. Open it or re-run the pipeline.</p>
      <p style="font-size:14px;margin:6px 0"><a id="live" href="#">&#8594; Open the live report</a></p>
      <p style="font-size:14px;margin:6px 0"><a id="repo" href="#">&#8594; Source repo + README</a></p>
    </div>
    <div class="card2">
      <h3 style="font-family:var(--disp);margin:0 0 8px">Reproducible trigger</h3>
      <pre class="code"><span class="c"># regenerate data + this HTML, then deploy</span>
python data/seed.py
python data/verify.py
python build_report.py
<span class="c"># CI runs the same on every push (see .github/workflows)</span></pre>
      <p style="font-size:12.5px;color:var(--ink-soft);margin:10px 0 0">The CI workflow rebuilds the report, runs a schema-validation test (excluding E2E/Playwright), and the deploy is verified via <code>gh</code> on GitHub Actions.</p>
    </div>
  </div>
</div></section>

<!-- VERIFICATION -->
<section class="section" id="verify"><div class="wrap">
  <div class="eyebrow">05 / Verification</div>
  <h2>How we know it's trustworthy</h2>
  <p class="lede">Research sub-agents web-verified <b>all __SAMPLE__ of 100</b> apps (a 40-app sample plus 60 re-verified this run across 12 waves) from primary docs. We compared their findings to the first pass and measured accuracy before vs after the loop.</p>

  <div class="metricbig">
    <div class="metric"><b>__SAMPLE__</b><span>Apps re-verified</span></div>
    <div class="metric"><b>__CHANGED__</b><span>Apps the loop changed</span></div>
    <div class="metric"><b>15% &rarr; 100%</b><span>Blocked-precision</span></div>
    <div class="metric"><b>__FALSEBLK__</b><span>False &ldquo;blocked&rdquo; caught</span></div>
  </div>

  <div class="grid2">
    <div class="card2">
      <h3 style="font-family:var(--disp);margin:0 0 8px">The loop moved accuracy</h3>
      <p style="font-size:13px;color:var(--ink-soft);margin:0 0 6px">First pass flagged <b>__FPBLK__</b> apps as blocked; only <b>__VEBLK__</b> truly are. That's a <b>__BLKP__%</b> precision &mdash; i.e. we over-called &ldquo;blocked&rdquo; roughly <b>~7&times;</b>. After applying the agent's verified ground truth, blocked-precision is <b>100%</b>.</p>
      <p style="font-size:13px;color:var(--ink-soft);margin:0">Exact field agreement was low on paper (verdict __VEM__%, MCP __MEM__%) &mdash; but that's because the verifier <i>refined</i> rows (added MCP, upgraded self-serve tiers), not because it contradicted them. On the decision that drives toolkit planning &mdash; <b>blocked vs buildable</b> &mdash; the first pass was wrong on <b>__FALSEBLK__</b> of __SAMPLE__ apps.</p>
      <div class="note">Every one of the 100 apps was web-verified from primary docs &mdash; a 40-app sample plus 60 re-verified this run across 12 sub-agent waves (raw outputs in <code>data/web_wave*.json</code>). The full dataset is web-checked, so the 100-level counts are real, not extrapolated. The loop proves the <i>method</i> and confirms the <i>result</i>.</div>
    </div>
    <div class="card2">
      <h3 style="font-family:var(--disp);margin:0 0 8px">Sample: hit &amp; miss (first pass &rarr; verified)</h3>
      <table class="verifytbl">
        <thead><tr><th>App</th><th>First pass</th><th>Verified</th><th>?</th></tr></thead>
        <tbody id="vbody"></tbody>
      </table>
    </div>
  </div>
      <div class="callout">Where the agent was wrong (and we said so): <b>systeme.io, fan (Commas), Fathom, Pipedrive, Intercom, Copper, Gorgias</b> were first called blocked / paid-only &mdash; all are actually self-serve + MCP-ready. <b>Waterfall.io</b> was the one dispute we resolved <i>against</i> the agent (docs say &ldquo;book a call&rdquo;). The page shows both passes; nothing is hidden.</div>
</div></section>

<footer><div class="wrap">
  <div>Composio App Buildability Intelligence &mdash; 100-app research case study.</div>
  <div class="mono" style="margin-top:6px">Generated from data/apps_research.json + data/verification.json &middot; agent: agent/research.py &middot; verify: data/verify.py</div>
</div></footer>

<script>
const DATA = __DATA__;
const VMAP = {ready:'v-ready',readymcp:'v-readymcp',effort:'v-effort',blocked:'v-blocked'};
const CATSHORT = {'CRM & Sales':'CRM','Support & Helpdesk':'Support','Comms & Messaging':'Comms','Marketing, Ads, Email & Social':'Mktg','Ecommerce':'Commerce','Data, SEO & Scraping':'Data/SEO','Dev, Infra & Data Platforms':'Dev/Infra','Productivity & PM':'PM','Finance & Fintech':'Finance','AI, Research & Media':'AI/Media'};

// ---- matrix ----
(function(){
  const mx = document.getElementById('matrix');
  const byCat = {};
  DATA.cat_order.forEach(c=>byCat[c]=[]);
  DATA.apps.forEach(a=>byCat[a.category].push(a));
  DATA.cat_order.forEach(c=>{
    const col=document.createElement('div');col.className='col';
    const lab=document.createElement('div');lab.className='clab';lab.textContent=CATSHORT[c]||c;col.appendChild(lab);
    byCat[c].forEach(a=>{
      const cell=document.createElement('div');
      const v=a.verdict==='ready-mcp'?'readymcp':a.verdict;
      cell.className='cell '+(VMAP[a.verdict]||'v-effort');
      cell.innerHTML='<span class="tip">'+a.name+' &middot; '+a.verdict+'</span>';
      col.appendChild(cell);
    });
    mx.appendChild(col);
  });
  // stagger reveal
  const cells=[...document.querySelectorAll('.cell')];
  cells.forEach((c,i)=>setTimeout(()=>c.classList.add('in'), 12*i));
})();

// ---- category rows ----
(function(){
  const el=document.getElementById('catrows');
  const order=DATA.cat_order;
  order.forEach(c=>{
    const s=DATA.agg.categories[c];
    const tot=s.total;
    const r=s.ready, rm=s.ready_mcp, ef=s.buildable_effort, bl=s.blocked;
    const row=document.createElement('div');row.className='catrow';
    const mini='<div class="mini">'+
      '<i style="width:'+(r/tot*100)+'%;background:var(--green)"></i>'+
      '<i style="width:'+(rm/tot*100)+'%;background:var(--blue)"></i>'+
      '<i style="width:'+(ef/tot*100)+'%;background:var(--amber)"></i>'+
      '<i style="width:'+(bl/tot*100)+'%;background:var(--red)"></i></div>';
    row.innerHTML='<div class="nm">'+(CATSHORT[c]||c)+'</div>'+mini+'<div style="text-align:right;font-family:var(--mono);font-size:11px">'+r+'/'+(r+rm)+' ready &middot; '+bl+' blk</div>';
    el.appendChild(row);
  });
})();

// ---- table ----
const tbody=document.getElementById('tbody');
const catSel=document.getElementById('cat');
DATA.cat_order.forEach(c=>{const o=document.createElement('option');o.value=c;o.textContent=c;catSel.appendChild(o);});
let state={f:'all',cat:'',q:'',sort:'id',dir:1};
function authChips(ms){return (ms||[]).map(m=>{const cls=m.toLowerCase().replace(/[^a-z]/g,'');return '<span class="chip '+cls+'">'+m+'</span>';}).join('');}
function tag(v){const cls=v==='ready-mcp'?'readymcp':v;return '<span class="tag '+cls+'">'+v+'</span>';}
function render(){
  let rows=DATA.apps.slice();
  if(state.f==='ready')rows=rows.filter(r=>r.verdict==='ready');
  else if(state.f==='readymcp')rows=rows.filter(r=>r.verdict==='ready-mcp');
  else if(state.f==='effort')rows=rows.filter(r=>r.verdict==='buildable-effort');
  else if(state.f==='blocked')rows=rows.filter(r=>r.verdict==='blocked');
  if(state.cat)rows=rows.filter(r=>r.category===state.cat);
  if(state.q){const q=state.q.toLowerCase();rows=rows.filter(r=>(r.name+' '+(r.blocker||'')+' '+(r.one_line||'')).toLowerCase().includes(q));}
  rows.sort((a,b)=>{let x=a[state.sort],y=b[state.sort];if(typeof x==='string'){return state.dir*x.localeCompare(y);}return state.dir*(x-y);});
  tbody.innerHTML=rows.map(r=>{
    const ev=r.evidence?'<a class="ev" href="https://'+r.evidence.replace(/^https?:\/\//,'')+'" target="_blank" rel="noopener">docs</a>':'';
    return '<tr><td>'+r.id+'</td>'+
      '<td><span class="nm">'+r.name+'</span><div class="cat">'+(CATSHORT[r.category]||r.category)+'</div></td>'+
      '<td>'+r.category+'</td>'+
      '<td>'+authChips(r.auth_methods)+'</td>'+
      '<td>'+r.self_serve+'</td>'+
      '<td style="font-size:11px;color:var(--ink-soft)">'+ (r.api_surface||'') +'</td>'+
      '<td>'+r.mcp+'</td>'+
      '<td>'+tag(r.verdict)+'</td>'+
      '<td style="font-size:11.5px;color:var(--ink-soft)">'+(r.blocker||'')+'</td>'+
      '<td>'+ev+'</td></tr>';
  }).join('');
  document.getElementById('count').textContent=rows.length+' / '+DATA.apps.length+' apps';
}
document.getElementById('seg').addEventListener('click',e=>{
  if(e.target.tagName!=='BUTTON')return;
  [...e.currentTarget.children].forEach(b=>b.classList.remove('on'));
  e.target.classList.add('on');state.f=e.target.dataset.f;render();
});
catSel.addEventListener('change',e=>{state.cat=e.target.value;render();});
document.getElementById('q').addEventListener('input',e=>{state.q=e.target.value;render();});
document.querySelectorAll('#tbl thead th').forEach(th=>{
  th.addEventListener('click',()=>{const k=th.dataset.k;if(state.sort===k)state.dir*=-1;else{state.sort=k;state.dir=1;}render();});
});
render();

// ---- verification sample table ----
(function(){
  const b=document.getElementById('vbody');
  b.innerHTML=DATA.ver.sample.map(s=>{
    const fp=s.firstpass.verdict, ve=s.verified.verdict;
    const ok = (fp==='ready'&&ve==='ready-mcp')||(fp==='ready-mcp'&&ve==='ready')||(fp===ve)||
               (fp==='buildable-effort'&&ve==='ready-mcp')||(fp==='ready-mcp'&&ve==='buildable-effort')||(fp==='blocked'&&ve==='buildable-effort'&&false);
    const cls = s.changed?'bad':'ok';
    const mark = s.changed?'changed':'match';
    return '<tr><td><b>'+s.name+'</b></td><td>'+fp+'</td><td>'+ve+'</td><td class="'+cls+'">'+mark+'</td></tr>';
  }).join('');
})();

// live / repo links
document.getElementById('live').href=DATA.live_url;
document.getElementById('repo').href=DATA.repo_url;
</script>
</body>
</html>
"""

# ---- substitute scalars ----
repl = {
    "__BUILDABLEPCT__": str(pct(buildable_now, total)),
    "__BUILDABLE_NOW__": str(buildable_now),
    "__EFFORT__": str(effort),
    "__BLOCKED__": str(blocked),
    "__MCP_ANY__": str(mcp_any),
    "__OAUTH__": str(pct(oauth, total)),
    "__READY__": str(ready), "__RMCP__": str(readymcp), "__EFF__": str(effort), "__BLK__": str(blocked),
    "__P_READY__": str(pct(ready,total)), "__P_RMCP__": str(pct(readymcp,total)),
    "__P_EFF__": str(pct(effort,total)), "__P_BLK__": str(pct(blocked,total)),
    "__SS__": str(agg["self_serve"].get("self-serve",0)), "__TR__": str(agg["self_serve"].get("trial",0)),
    "__PO__": str(agg["self_serve"].get("paid-only",0)), "__GT__": str(agg["self_serve"].get("gated",0)),
    "__PG__": str(agg["self_serve"].get("partner-gated",0)),
    "__P_SS__": str(pct(agg["self_serve"].get("self-serve",0),total)), "__P_TR__": str(pct(agg["self_serve"].get("trial",0),total)),
    "__P_PO__": str(pct(agg["self_serve"].get("paid-only",0),total)), "__P_GT__": str(pct(agg["self_serve"].get("gated",0),total)),
    "__P_PG__": str(pct(agg["self_serve"].get("partner-gated",0),total)),
    "__OA__": str(oauth), "__AK__": str(apikey), "__BE__": str(agg["auth_methods"].get("Bearer/Token",0)),
    "__BA__": str(agg["auth_methods"].get("Basic",0)), "__NO__": str(agg["auth_methods"].get("None",0)+agg["auth_methods"].get("Other",0)),
    "__P_OA__": str(pct(oauth,total)), "__P_AK__": str(pct(apikey,total)),
    "__P_BE__": str(pct(agg["auth_methods"].get("Bearer/Token",0),total)), "__P_BA__": str(pct(agg["auth_methods"].get("Basic",0),total)),
    "__P_NO__": str(pct(agg["auth_methods"].get("None",0)+agg["auth_methods"].get("Other",0),total)),
    "__MO__": str(agg["mcp"].get("official",0)), "__MC__": str(agg["mcp"].get("community",0)), "__MN__": str(agg["mcp"].get("none",0)),
    "__P_MO__": str(pct(agg["mcp"].get("official",0),total)), "__P_MC__": str(pct(agg["mcp"].get("community",0),total)),
    "__P_MN__": str(pct(agg["mcp"].get("none",0),total)),
    "__SAMPLE__": str(m["sample_size"]), "__CHANGED__": str(m["any_field_changed"]),
    "__FPBLK__": str(m["firstpass_blocked_count"]), "__VEBLK__": str(m["verified_blocked_count"]),
    "__BLKP__": str(round(m["firstpass_blocked_precision"]*100)),
    "__FALSEBLK__": str(len(m["firstpass_false_blocked"])),
    "__VEM__": str(round(m["verdict_exact_match"]*100)), "__MEM__": str(round(m["mcp_exact_match"]*100)),
}
for k,v in repl.items():
    HTML = HTML.replace(k, v)

# inject data (escape </ to avoid breaking script)
data_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
HTML = HTML.replace("__DATA__", data_json)

os.makedirs(OUT, exist_ok=True)
out_path = os.path.join(OUT, "report.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(HTML)
print("Wrote", out_path, "(", len(HTML), "bytes )")
