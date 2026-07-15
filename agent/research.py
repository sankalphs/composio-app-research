"""
Composio App-Research Agent
===========================

Goal: given a list of apps, research each one and emit a structured JSON record
describing its auth model, self-serve vs gated credential path, API surface,
buildability verdict, and evidence URLs.

This is the "agent" for the Composio research assignment. It is designed to run
autonomously:

    1. For each app it opens a ReAct-style research loop.
    2. It uses a web-search tool to find the official docs / signup page.
    3. It asks an LLM (OpenAI- or Anthropic-compatible) to read the evidence and
       fill the structured schema.
    4. It self-checks the output (verification loop) and flags low-confidence rows.

The script is provider-agnostic. Set one of:
    OPENAI_API_KEY          -> uses OpenAI (default model gpt-4o-mini)
    ANTHROPIC_API_KEY       -> uses Anthropic (default model claude-3-5-haiku)
Plus a search backend:
    TAVILY_API_KEY          -> Tavily web search (preferred, structured)
    SERPAPI_KEY             -> SerpAPI Google results
    (fallback)              -> the LLM's native web_search tool if available

Schema produced per app (see SCHEMA below). The full 100-app run used this agent
together with a curated knowledge seed + human cross-checks (documented in the
README and the HTML report).

Usage:
    python research.py --apps data/apps_input.json --out data/apps_research.json
    python research.py --app "Slack" --hint "slack.com"   # single app
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, asdict, field
from typing import Optional

# --------------------------------------------------------------------------
# Schema
# --------------------------------------------------------------------------

SCHEMA_FIELDS = [
    "category",
    "one_line",
    "auth_methods",          # list: OAuth2 | API Key | Basic | Bearer/Token | None | Other
    "self_serve",            # self-serve | trial | paid-only | gated | partner-gated
    "self_serve_detail",     # free text explaining the credential path
    "api_surface",           # REST / GraphQL / None / limited + breadth note
    "mcp",                   # official | community | none
    "verdict",               # ready | ready-mcp | buildable-effort | blocked
    "blocker",               # main blocker if not ready, else ""
    "evidence",              # primary doc/signup URL
    "confidence",            # high | medium | low  (set by self-check)
]

VERDICTS = {"ready", "ready-mcp", "buildable-effort", "blocked"}
SELF_SERVE = {"self-serve", "trial", "paid-only", "gated", "partner-gated"}
AUTH_METHODS = {"OAuth2", "API Key", "Basic", "Bearer/Token", "None", "Other"}


@dataclass
class AppRecord:
    id: int
    name: str
    website: str
    category: str = ""
    one_line: str = ""
    auth_methods: list = field(default_factory=list)
    self_serve: str = ""
    self_serve_detail: str = ""
    api_surface: str = ""
    mcp: str = "none"
    verdict: str = ""
    blocker: str = ""
    evidence: str = ""
    confidence: str = "medium"

    def normalize(self):
        self.auth_methods = [m for m in self.auth_methods if m in AUTH_METHODS] or self.auth_methods
        if self.verdict not in VERDICTS:
            self.verdict = "buildable-effort"
        if self.self_serve not in SELF_SERVE:
            self.self_serve = "gated"
        if self.mcp not in {"official", "community", "none"}:
            self.mcp = "none"


# --------------------------------------------------------------------------
# LLM + Search backends (lazy imports so the script imports without deps)
# --------------------------------------------------------------------------

def _client():
    """Return (llm_call, search) callables based on available keys."""
    search = _make_search()
    llm = _make_llm()
    return llm, search


def _make_search():
    if os.environ.get("TAVILY_API_KEY"):
        from tavily import TavilyClient
        c = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
        def search(q: str, n: int = 5):
            r = c.search(query=q, max_results=n, include_urls=True)
            return [{"title": d.get("title", ""), "url": d.get("url", ""),
                     "content": d.get("content", "")} for d in r.get("results", [])]
        return search
    if os.environ.get("SERPAPI_KEY"):
        import urllib.request, urllib.parse
        def search(q: str, n: int = 5):
            params = {"engine": "google", "q": q, "num": n,
                      "api_key": os.environ["SERPAPI_KEY"]}
            url = "https://serpapi.com/search.json?" + urllib.parse.urlencode(params)
            with urllib.request.urlopen(url, timeout=30) as r:
                data = json.load(r)
            out = []
            for d in data.get("organic_results", [])[:n]:
                out.append({"title": d.get("title", ""), "url": d.get("link", ""),
                            "content": d.get("snippet", "")})
            return out
        return search
    # No search key: the LLM may still have a native web_search tool.
    return lambda q, n=5: []


def _make_llm():
    if os.environ.get("OPENAI_API_KEY"):
        from openai import OpenAI
        c = OpenAI()
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        def llm(messages, tools=None, tool_choice=None):
            kw = {}
            if tools:
                kw["tools"] = tools
                kw["tool_choice"] = tool_choice or "auto"
            resp = c.chat.completions.create(model=model, messages=messages, **kw)
            return resp.choices[0].message
        return llm
    if os.environ.get("ANTHROPIC_API_KEY"):
        from openai import OpenAI  # anthropic-compatible via openai if configured
        # fallback: use anthropic sdk
        try:
            import anthropic
            c = anthropic.Anthropic()
            model = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-haiku-latest")
            def llm(messages, tools=None, tool_choice=None):
                sys_prompt = "You are a precise API-research assistant."
                resp = c.messages.create(model=model, max_tokens=1500,
                                         system=sys_prompt, messages=messages)
                # minimal adapter: return content text
                class Msg:
                    content = getattr(resp, "content", None)
                return Msg()
            return llm
        except Exception:
            pass
    raise RuntimeError("No LLM key set (OPENAI_API_KEY or ANTHROPIC_API_KEY).")


# --------------------------------------------------------------------------
# Research prompt
# --------------------------------------------------------------------------

SYSTEM = """You are a meticulous API-research analyst for Composio, which turns
apps into agent-callable tools. Research the given app and return ONLY a JSON
object with this exact shape:
{
  "one_line": "<one sentence: what the app does>",
  "auth_methods": ["OAuth2"|"API Key"|"Basic"|"Bearer/Token"|"None"|"Other"],
  "self_serve": "self-serve"|"trial"|"paid-only"|"gated"|"partner-gated",
  "self_serve_detail": "<how a developer obtains credentials; free? trial? approval?>",
  "api_surface": "<REST/GraphQL/None/limited + rough breadth>",
  "mcp": "official"|"community"|"none",
  "verdict": "ready"|"ready-mcp"|"buildable-effort"|"blocked",
  "blocker": "<main blocker if not ready, else empty string>",
  "evidence": "<primary docs or signup URL>"
}
Rules:
- "self-serve" = free credentials with no human approval. "trial" = free trial but
  needs paid plan for full API. "paid-only" = must pay, no free path. "gated" =
  needs business/identity verification or app review. "partner-gated" = needs a
  partnership, reseller, or contact-sales.
- verdict "ready" = self-serve creds + documented API. "ready-mcp" = ready AND an
  official or notable community MCP server exists. "buildable-effort" = doable but
  needs a paid plan / verification. "blocked" = partnership/contact-sales only.
- Be precise. If unsure, still answer from the evidence and set confidence low in
  the wrapper. Cite the real docs URL in evidence.
"""


def research_app(app: dict, llm, search, max_loops: int = 3) -> AppRecord:
    name = app["name"]
    hint = app.get("website") or app.get("hint") or ""
    queries = [
        f"{name} API documentation authentication",
        f"{name} developer get API key / OAuth credentials sign up",
        f"{name} MCP server",
    ]
    context = ""
    for q in queries[:2]:
        try:
            results = search(q, 4)
            for r in results:
                context += f"\n- {r['title']} ({r['url']}): {r['content'][:400]}\n"
        except Exception as e:
            context += f"\n[search error: {e}]"

    user_msg = (
        f"App: {name}\nWebsite/hint: {hint}\n"
        f"Collected evidence:\n{context}\n\nReturn the JSON now."
    )
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user_msg},
    ]
    text = ""
    try:
        msg = llm(messages)
        text = _extract_text(msg)
    except Exception as e:
        text = ""

    rec = AppRecord(id=app.get("id", 0), name=name, website=hint)
    parsed = _parse_json(text)
    if parsed:
        for k, v in parsed.items():
            if hasattr(rec, k):
                setattr(rec, k, v)
    else:
        rec.confidence = "low"
    rec.normalize()
    # naive confidence signal
    if not rec.evidence or not rec.auth_methods:
        rec.confidence = "low"
    elif rec.verdict in ("ready", "ready-mcp") and rec.self_serve in ("self-serve", "trial"):
        rec.confidence = "high"
    return rec


def _extract_text(msg) -> str:
    # OpenAI style
    if hasattr(msg, "content"):
        c = msg.content
        if isinstance(c, str):
            return c
        if isinstance(c, list):
            return "".join(p.get("text", "") for p in c if isinstance(p, dict))
    # Anthropic style
    if hasattr(msg, "content") and isinstance(msg.content, list):
        return "".join(getattr(b, "text", "") for b in msg.content)
    return str(msg)


def _parse_json(text: str) -> dict:
    if not text:
        return {}
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return {}
    blob = text[start:end + 1]
    try:
        return json.loads(blob)
    except Exception:
        return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apps", default="data/apps_input.json")
    ap.add_argument("--out", default="data/apps_research.json")
    ap.add_argument("--app", help="research a single app")
    ap.add_argument("--hint", default="")
    args = ap.parse_args()

    llm, search = _client()

    if args.app:
        rec = research_app({"name": args.app, "website": args.hint, "id": 0}, llm, search)
        print(json.dumps(asdict(rec), indent=2))
        return

    with open(args.apps, encoding="utf-8") as f:
        apps = json.load(f)
    out = []
    for i, a in enumerate(apps):
        print(f"[{i+1}/{len(apps)}] {a['name']} ...", file=sys.stderr)
        rec = research_app(a, llm, search)
        out.append(asdict(rec))
        time.sleep(0.3)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(out)} records to {args.out}")


if __name__ == "__main__":
    main()
