# Composio - App Buildability Intelligence (100 apps)

An agent-built research case study: **which of 100 real apps can become Composio
agent toolkits**, and *why*. Auth model, self-serve vs gated credentials, API
surface, MCP availability, and a buildability verdict - for every app - plus the
patterns across them and a verification loop that proves the findings are trustworthy.

> Live report: **https://sankalphs.github.io/composio-app-research/report.html**

## What's inside

| Path | What it is |
|------|------------|
| `agent/research.py` | The **research agent**. LLM + web-search ReAct loop that fills the structured schema per app. Provider-agnostic (OpenAI / Anthropic + Tavily / SerpAPI). |
| `data/apps_input.json` | The 100 apps (id, name, category, website). |
| `data/seed.py` | Curated knowledge seed that bootstraps the dataset (the schema the agent emits). |
| `data/verify.py` | Verification harness: merges the web-verified ground truth for **all 100 apps** (40-app sample + 60 re-verified this run via `data/web_wave*.json`), computes first-pass (knowledge-based) vs web-verified accuracy, writes the corrected dataset + `verification.json` + `aggregates.json`. |
| `data/apps_research.json` | **Final dataset (100 apps)**, every record web-verified from live documentation. |
| `data/web_wave1-12.json` | Raw sub-agent outputs: 60 apps re-verified this run (12 waves x 5). |
| `data/verification.json` | Full 100-app: first-pass (knowledge-based) vs web-verified, with accuracy metrics. |
| `data/aggregates.json` | Counts by category / auth / self-serve / verdict / MCP. |
| `build_report.py` | Generates the single self-contained `report/report.html` from the data. |
| `tests/test_pipeline.py` | Pipeline tests (schema completeness, aggregate consistency, build). E2E/Playwright excluded. |
| `.github/workflows/ci.yml` | CI runs the tests, regenerates the report, deploys to GitHub Pages, and verifies via `gh`. |

## The method (how it was done, not by hand)

1. **Seed + schema** - 100 apps and the field schema in `data/seed.py`.
2. **Agent research** - `agent/research.py` runs an LLM + web-search loop per app,
   emitting the structured record and flagging low-confidence rows.
 3. **Verify (full 100)** - research sub-agents web-verified **all 100 apps** from
    primary docs: a 40-app sample (2 waves x 4 agents x 5) plus **60 apps re-verified
    this run** across 12 sub-agent waves (`data/web_wave1-12.json`), each persisted as JSON.
 4. **Correct + report** - diff first-pass (knowledge-based) vs web-verified, fix the
    dataset (92/100 records changed), regenerate the page from the data.

### Why a human was needed
- Defining the schema + the **self-serve / gated / partner-gated** definitions so
  "needs approval" is not mistaken for "blocked".
- Seeding the first 100 (the sandbox had no LLM key) and orchestrating the
  sub-agent research + 12-wave verification, then merging their JSON outputs.
- **Adjudicating Waterfall.io** from its docs (agent said buildable; docs say
  "book a call" -> kept `blocked`).
- Fixing **Ramp** for consistency with its verified twin **Brex**.

## Run it

```bash
pip install openai tavily-python pytest
export OPENAI_API_KEY=... TAVILY_API_KEY=...

# research a single app
python agent/research.py --app "Slack" --hint "slack.com"

# reproduce the whole pipeline + report
python data/seed.py
python data/verify.py
python build_report.py
pytest -q
```

The deployed page and the dataset are regenerated from the same data on every push
via GitHub Actions (Pages source = GitHub Actions; deploy verified with `gh`).

### Note on Composio's own SDK / MCP
The assignment invites using Composio's SDK/MCP "in the spirit of the role." This
pipeline is provider-agnostic (OpenAI/Anthropic + Tavily/SerpAPI in `research.py`,
OpenRouter in the verification sub-agents) and does not depend on it, but
`research.py` can be pointed at Composio's tooling to source app metadata.

## Headline findings

- **97% buildable** (64 ready/ready-with-MCP + 33 with-effort); **only 3 truly blocked**
  (Salesforce Commerce Cloud, Waterfall.io, PitchBook).
- **OAuth2 dominates** (63/100), usually alongside an API key / bearer token.
- **95/100 already have an MCP server** (65 official + 30 community) - the win is
  wiring these up, not building from scratch; only 5 have none.
- The 33 "with-effort" apps need a paid plan or identity/app-review (e.g. finance,
  ads, enterprise). Dev/Infra + Comms are the easy wins; finance + enterprise commerce
  are the hard wall.

### Verification in one line
The knowledge-based first pass flagged **20** apps as `blocked`; only **3** truly are ->
blocked-precision **15%** (recall 100%). After web verification **92 of 100** records
were corrected, and the dataset is now **100% web-checked** from primary docs.
