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
| `data/verify.py` | Verification harness: applies the agent-verified ground truth for a 40-app sample, computes before/after accuracy, writes the corrected dataset + `verification.json` + `aggregates.json`. |
| `data/apps_research.json` | **Final dataset (100 apps)** after the verification loop. |
| `data/verification.json` | The 40-app sample: first-pass vs verified, with accuracy metrics. |
| `data/aggregates.json` | Counts by category / auth / self-serve / verdict / MCP. |
| `build_report.py` | Generates the single self-contained `report/report.html` from the data. |
| `tests/test_pipeline.py` | Pipeline tests (schema completeness, aggregate consistency, build). E2E/Playwright excluded. |
| `.github/workflows/ci.yml` | CI runs the tests, regenerates the report, deploys to GitHub Pages, and verifies via `gh`. |

## The method (how it was done, not by hand)

1. **Seed + schema** - 100 apps and the field schema in `data/seed.py`.
2. **Agent research** - `agent/research.py` runs an LLM + web-search loop per app,
   emitting the structured record and flagging low-confidence rows.
3. **Verify (2 waves)** - 8 parallel research sub-agents re-researched a 40-app
   stratified sample from primary docs; manual `webfetch` adjudicated edge cases.
4. **Correct + report** - diff first-pass vs verified, fix the dataset, regenerate
   the page from the data.

### Why a human was needed
- Defining the schema + the **self-serve / gated / partner-gated** definitions so
  "needs approval" is not mistaken for "blocked".
- Seeding the first 100 (the sandbox had no LLM key).
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

## Headline findings

- **72% buildable now** (43 ready + 29 ready-with-MCP); 23% buildable-with-effort; **only 5 truly blocked**.
- **OAuth2 dominates** (66/100), usually alongside an API key / token.
- **56/100 already have an MCP server** (official or community) - the win is wiring
  these up, not building from scratch.
- Finance + enterprise CRM are the outreach pile (PitchBook, Salesforce Commerce
  Cloud, Waterfall, Plain, Consensus). Dev/Infra + Comms are the easy wins.

### Verification in one line
First pass flagged **17** apps as `blocked`; only **3** truly are -> blocked-precision
**17.6%**. After the loop: **100%**, and **38 of 40** sampled apps were corrected.
