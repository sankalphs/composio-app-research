"""
Verification harness (full 100-app coverage).

- Loads the *first-pass* knowledge-based dataset (seed.py RECORDS).
- Applies the web-verified ground truth for ALL 100 apps:
    * 40 apps verified in the earlier 40-app sample (VERIFIED dict below).
    * 60 apps re-verified this run via research sub-agents (data/web_wave*.json).
- Computes first-pass (knowledge-based) vs web-verified accuracy across all 100.
- Writes the corrected dataset (apps_research.json), verification.json and aggregates.json.

Run:  python verify.py
"""
import json, os, glob
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- Verified ground truth for the original 40-app sample ------------------
# Keyed by app id. Fields override the first-pass record.
VERIFIED = {
  4:  {"one_line":"AI-native relationship/CRM platform with a flexible object-based data model.","auth_methods":["OAuth2","API Key","Bearer/Token"],"self_serve":"self-serve","self_serve_detail":"Free plan (3 seats, 50k records, free forever); admin self-generates API key or registers OAuth app at build.attio.com - no approval.","api_surface":"REST broad (records/objects, lists, notes, tasks, webhooks, SCIM) + SQL + App SDK","mcp":"official","verdict":"ready-mcp","blocker":"","evidence":"https://docs.attio.com/rest-api/guides/authentication","confidence":"high"},
  15: {"one_line":"B2B support/operations platform unifying Slack, Teams, email, chat into ticketing.","auth_methods":["Bearer/Token","API Key"],"self_serve":"paid-only","self_serve_detail":"API token self-serve from dashboard (Settings -> API tokens) but requires an active Pylon workspace (paid, sales-led onboarding); Admin role.","api_surface":"REST broad (issues, accounts, contacts, KB, webhooks); OpenAPI published","mcp":"official","verdict":"buildable-effort","blocker":"Requires an active (paid) Pylon workspace + Admin role to mint an API token.","evidence":"https://docs.usepylon.com/pylon-docs/developer/api/authentication","confidence":"medium"},
  28: {"one_line":"Meta-hosted WhatsApp Business messaging API.","auth_methods":["Bearer/Token","OAuth2"],"self_serve":"gated","self_serve_detail":"Dev/test: free Meta app + temporary token (no cost). Production needs Meta Business verification, permanent System User token, billing; test capped at 5 recipients.","api_surface":"REST (Graph/Cloud) moderate (messaging, templates, media, webhooks)","mcp":"community","verdict":"buildable-effort","blocker":"Production needs Meta Business verification + billing; dev/test capped at temporary token + 5 test recipients.","evidence":"https://developers.facebook.com/docs/whatsapp/cloud-api/get-started","confidence":"high"},
  33: {"one_line":"LinkedIn Marketing/Advertising API.","auth_methods":["OAuth2"],"self_serve":"gated","self_serve_detail":"Self-create Developer Portal app (OAuth client) + verify Company Page; Advertising API access requires manual human review (slow, discretionary).","api_surface":"REST broad (campaigns, creatives, analytics, conversions)","mcp":"community","verdict":"buildable-effort","blocker":"Advertising API access granted only after LinkedIn's manual application review (slow, no appeal).","evidence":"https://learn.microsoft.com/en-us/linkedin/marketing/","confidence":"high"},
  44: {"one_line":"Enterprise headless commerce platform (B2C Commerce / SCAPI).","auth_methods":["OAuth2","Bearer/Token"],"self_serve":"partner-gated","self_serve_detail":"SCAPI free for B2C Commerce customers, but real credentials require a licensed enterprise instance via Salesforce sales/partners; public demo sandbox is read-only.","api_surface":"REST very broad (SCAPI Shopper + Admin, OCAPI)","mcp":"official","verdict":"blocked","blocker":"Real API credentials require a licensed B2C Commerce instance (enterprise contract); no self-serve production access.","evidence":"https://developer.salesforce.com/docs/commerce/commerce-api/guide/authorization.html","confidence":"high"},
  10: {"one_line":"Financial-services deal/relationship platform (Intapp).","auth_methods":["OAuth2","API Key","Bearer/Token"],"self_serve":"paid-only","self_serve_detail":"Requires an enterprise DealCloud/Intapp tenant; admin enables 'API' capability and issues API keys / OAuth2 client-credentials. No free public signup.","api_surface":"REST broad (entities, queries, files, sync)","mcp":"official","verdict":"buildable-effort","blocker":"Requires an enterprise DealCloud/Intapp tenant (acquired via sales); admin self-enables API within tenant.","evidence":"https://api.docs.dealcloud.com/docs/token","confidence":"high"},
  20: {"one_line":"Cloud customer-service / contact-center platform.","auth_methods":["Basic"],"self_serve":"paid-only","self_serve_detail":"Requires a paid Gladly org; admin grants 'API User' permission and generates API tokens in the UI. No free self-serve.","api_surface":"REST broad (conversations, customers, tasks, agents, webhooks)","mcp":"community","verdict":"buildable-effort","blocker":"Requires a paid Gladly tenant; admin issues API token.","evidence":"https://developer.gladly.com/rest/","confidence":"high"},
  30: {"one_line":"Communications APIs (SMS, voice, verify).","auth_methods":["Basic","Bearer/Token"],"self_serve":"self-serve","self_serve_detail":"Free account (no card); API key + secret issued in dashboard; EUR2 demo credit. Auth via Basic (key:secret) or JWT bearer.","api_surface":"REST broad (Voice, Messages, Verify, Numbers, Video)","mcp":"official","verdict":"ready-mcp","blocker":"","evidence":"https://developer.vonage.com/en/sign-up","confidence":"high"},
  39: {"one_line":"Meta Threads Graph API (publish/read/replies).","auth_methods":["OAuth2"],"self_serve":"self-serve","self_serve_detail":"Free: create Meta app with Threads use case; in Dev mode app owners/testers exchange OAuth for tokens with NO App Review. Production advanced scopes need App Review + business verification.","api_surface":"REST moderate (profile, media, publish, replies, insights)","mcp":"community","verdict":"ready-mcp","blocker":"","evidence":"https://developers.facebook.com/docs/threads/get-started/","confidence":"high"},
  49: {"one_line":"Amazon marketplace API (SP-API) for sellers/vendors.","auth_methods":["OAuth2"],"self_serve":"gated","self_serve_detail":"Register as SP-API developer (identity verification: gov ID, business license, bank, video), request + get approved for data roles; public apps pass architecture/Appstore review. Auth via LWA OAuth2.","api_surface":"REST very broad (30+ sections: orders, catalog, inventory, reports, finances)","mcp":"community","verdict":"buildable-effort","blocker":"Identity verification + role approval + (public apps) architecture/Appstore review before production; needs Amazon selling account.","evidence":"https://developer-docs.amazon.com/sp-api/docs/onboarding-overview","confidence":"high"},
  59: {"one_line":"B2B enrichment/GTM API across 30+ data vendors.","auth_methods":["API Key"],"self_serve":"partner-gated","self_serve_detail":"API key 'provided in your contract'; docs say 'contact your account manager' / 'book a call'. No public self-serve key path.","api_surface":"REST async job-based enrichment (Prospector, Contact/Company, Search)","mcp":"none","verdict":"blocked","blocker":"No documented self-serve credential path; key requires a contract / sales conversation.","evidence":"https://docs.waterfall.io/v1/authentication","confidence":"medium"},
  60: {"one_line":"GTM data platform: people/company search, enrichment, workflows.","auth_methods":["API Key"],"self_serve":"trial","self_serve_detail":"Self-serve 'clay-api-key' under Settings -> Account -> API keys (beta) within a Clay account (paid SaaS w/ limited free tier); API usage consumes credits.","api_surface":"REST (search, routines/run, workflows) + 200+ marketplace providers","mcp":"official","verdict":"ready-mcp","blocker":"","evidence":"https://developers.clay.com/public-api/authentication","confidence":"high"},
  66: {"one_line":"Graph database platform (Cypher/HTTP API + Aura cloud).","auth_methods":["Basic","Bearer/Token","None"],"self_serve":"self-serve","self_serve_detail":"Aura free tier (no card) yields instance creds; self-managed needs server setup. Bearer via SSO; auth can be disabled.","api_surface":"HTTP API (Bolt/Cypher) + drivers + neo4j-graphql","mcp":"official","verdict":"ready-mcp","blocker":"","evidence":"https://neo4j.com/docs/http-api/current/authentication-authorization/","confidence":"high"},
  67: {"one_line":"Cloud data warehouse (SQL + REST + Cortex AI).","auth_methods":["OAuth2","Bearer/Token"],"self_serve":"trial","self_serve_detail":"Self-serve 30-day trial yields credentials; REST auth via OAuth2, key-pair JWT, PAT. Full API use needs an account (trial/paid).","api_surface":"REST (resource mgmt + SQL API + Cortex)","mcp":"official","verdict":"ready-mcp","blocker":"","evidence":"https://docs.snowflake.com/en/developer-guide/snowflake-rest-api/authentication","confidence":"high"},
  76: {"one_line":"Work OS / project management (single GraphQL API).","auth_methods":["OAuth2","API Key","Bearer/Token"],"self_serve":"self-serve","self_serve_detail":"Free no-expiry developer account gives a personal V2 API token; OAuth 2.1 client-credentials self-serve in Developer Center - no approval.","api_surface":"GraphQL single endpoint (boards, items, users, apps, automations)","mcp":"community","verdict":"ready-mcp","blocker":"","evidence":"https://developer.monday.com/api-reference/docs/authentication","confidence":"medium"},
  79: {"one_line":"Work-management platform (sheets/projects) with REST API.","auth_methods":["OAuth2","Bearer/Token"],"self_serve":"self-serve","self_serve_detail":"Personal API access token in-app (Account -> Personal Settings -> API Access) free, no approval; OAuth app via Developer Tools. Needs a Smartsheet account (free trial).","api_surface":"REST broad (sheets, rows, workspaces, webhooks)","mcp":"official","verdict":"ready-mcp","blocker":"","evidence":"https://developers.smartsheet.com/api/smartsheet/guides/getting-started","confidence":"high"},
  82: {"one_line":"Financial-data aggregation API (Link, Auth, Transactions).","auth_methods":["API Key","OAuth2"],"self_serve":"self-serve","self_serve_detail":"Free sandbox client_id + secret instantly from Plaid Dashboard (no approval). Production access requires a separate request via Dashboard.","api_surface":"REST very broad (Link, Auth, Transactions, Identity, Transfer)","mcp":"official","verdict":"ready-mcp","blocker":"Production access requires an approval request via Dashboard (instant sandbox for dev/test).","evidence":"https://plaid.com/docs/api/","confidence":"high"},
  88: {"one_line":"Unified business spend platform (cards, expenses, bills).","auth_methods":["OAuth2","Bearer/Token"],"self_serve":"gated","self_serve_detail":"API tokens self-serve in Brex Dashboard (Settings -> Developer) by admin, but only for approved/verified Brex business customers. Official MCP needs 'Brex in AI assistants' beta + Developer API agreement.","api_surface":"REST broad (Accounting, Expenses, Payments, Travel, Webhooks)","mcp":"official","verdict":"buildable-effort","blocker":"Requires an approved/verified Brex business account to obtain tokens (customer-only).","evidence":"https://developer.brex.com/guides/authentication","confidence":"high"},
  91: {"one_line":"Google source-grounded AI research assistant (Enterprise API).","auth_methods":["OAuth2","Bearer/Token"],"self_serve":"paid-only","self_serve_detail":"Consumer NotebookLM has no public API. NotebookLM Enterprise API (Google Cloud) requires a GCP project with NotebookLM Enterprise enabled (paid/enterprise) + Bearer token.","api_surface":"REST (Enterprise: notebooks, sources, audio overviews)","mcp":"none","verdict":"buildable-effort","blocker":"No consumer public API; Enterprise API requires Google Cloud NotebookLM Enterprise enrollment (paid/enterprise).","evidence":"https://cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks","confidence":"medium"},
  100:{"one_line":"Meeting recorder/intelligence with REST API (v2).","auth_methods":["OAuth2","Bearer/Token"],"self_serve":"paid-only","self_serve_detail":"PAT + OAuth2 + Workspace tokens self-serve in-app; API access requires a paid Grain plan (Starter+); Free excludes API. No official MCP (community only).","api_surface":"REST broad (recordings, transcripts, notes, tags, webhooks)","mcp":"community","verdict":"buildable-effort","blocker":"API requires a paid Grain plan (Starter+); no official MCP.","evidence":"https://developers.grain.com/","confidence":"high"},
  3:  {"one_line":"CRM platform with broad REST API (v1/v2) + developer sandbox.","auth_methods":["OAuth2","API Key"],"self_serve":"self-serve","self_serve_detail":"Free developer sandbox at developers.pipedrive.com; create draft app for OAuth client_id/secret or use personal API token from settings - no approval.","api_surface":"REST (v1+v2) broad CRM coverage","mcp":"community","verdict":"ready-mcp","blocker":"","evidence":"https://developers.pipedrive.com/","confidence":"high"},
  12: {"one_line":"Customer messaging/support platform with REST API + official MCP.","auth_methods":["OAuth2","Bearer/Token"],"self_serve":"self-serve","self_serve_detail":"Create app in Developer Hub; instantly get Bearer Access Token for your workspace; OAuth auto-approved for TEST app (no review).","api_surface":"REST broad (contacts, conversations, tickets, articles)","mcp":"official","verdict":"ready-mcp","blocker":"","evidence":"https://developers.intercom.com/docs/guides/mcp","confidence":"high"},
  22: {"one_line":"Programmable communications (messaging, voice, verify) + official MCP.","auth_methods":["Basic","API Key"],"self_serve":"trial","self_serve_detail":"Free 30-day trial -> Account SID + Auth Token + API keys from Console; trial limited (verified numbers); full API needs paid upgrade.","api_surface":"REST very broad (30+ products, 1800+ endpoints)","mcp":"official","verdict":"ready-mcp","blocker":"","evidence":"https://www.twilio.com/docs/ai/mcp","confidence":"high"},
  34: {"one_line":"White-label CRM/agency platform with v2 REST API + official MCP.","auth_methods":["OAuth2","API Key","Bearer/Token"],"self_serve":"paid-only","self_serve_detail":"Free developer account yields OAuth client; calling API / Private Integration Token needs Unlimited ($297) or SaaS Pro ($497) plan; Starter lacks API.","api_surface":"REST v2 broad (contacts, conversations, opportunities, calendars)","mcp":"official","verdict":"buildable-effort","blocker":"API / MCP require paid Unlimited or SaaS Pro plan (Starter lacks API access).","evidence":"https://marketplace.gohighlevel.com/docs/Authorization/OAuth2.0/index.html","confidence":"high"},
  46: {"one_line":"Website/commerce builder; Commerce REST APIs via API key/OAuth.","auth_methods":["API Key","OAuth2"],"self_serve":"paid-only","self_serve_detail":"Free API key from Settings -> Developer API Keys, but Commerce APIs need paid Commerce Advanced plan; OAuth for Extensions gated behind a contact form.","api_surface":"REST limited (orders, inventory, transactions, forms)","mcp":"community","verdict":"buildable-effort","blocker":"Commerce API key needs paid Commerce Advanced plan; OAuth path gated behind a form.","evidence":"https://developers.squarespace.com/commerce-apis/authentication-and-permissions","confidence":"high"},
  9:  {"one_line":"CRM for Google Workspace with REST Developer API.","auth_methods":["API Key","OAuth2"],"self_serve":"trial","self_serve_detail":"API keys fully self-serve (System settings -> API Keys); OAuth2 app registration gated (contact Copper). Needs a paid Copper account (free trial available).","api_surface":"REST broad (leads, people, opportunities, activities, webhooks)","mcp":"community","verdict":"ready-mcp","blocker":"","evidence":"https://developer.copper.com/introduction/authentication.html","confidence":"medium"},
  19: {"one_line":"E-commerce helpdesk with documented REST API.","auth_methods":["API Key","Basic","OAuth2"],"self_serve":"trial","self_serve_detail":"Private-app API keys self-serve (Settings -> REST API); auth HTTP Basic. Public apps need app review (gated). Needs paid Helpdesk plan (free trial).","api_surface":"REST broad (tickets, messages, customers, webhooks)","mcp":"community","verdict":"ready-mcp","blocker":"","evidence":"https://developers.gorgias.com/reference/authentication","confidence":"high"},
  29: {"one_line":"Cloud phone system with RESTful Public API.","auth_methods":["Basic","OAuth2"],"self_serve":"trial","self_serve_detail":"Customer API keys self-serve (Company Settings -> API Keys) -> api_id+api_token as Basic auth. OAuth2 for partners (gated). Needs paid plan (free trial).","api_surface":"REST (calls, contacts, users, numbers, webhooks)","mcp":"none","verdict":"ready","blocker":"","evidence":"https://developer.aircall.io/api-references/","confidence":"medium"},
  37: {"one_line":"All-in-one marketing/business platform with public REST API + official MCP.","auth_methods":["API Key","Bearer/Token"],"self_serve":"self-serve","self_serve_detail":"API keys self-serve on free plan (Settings -> Public API keys). Auth Bearer token. Some higher-tier endpoints may need paid plan.","api_surface":"REST limited-but-useful (contacts, tags, newsletters, subscriptions, webhooks)","mcp":"official","verdict":"ready-mcp","blocker":"","evidence":"https://developer.systeme.io/reference/api","confidence":"high"},
  50: {"one_line":"Merchant-of-record payments platform (rebranding to Commas) with REST API + MCP (beta).","auth_methods":["API Key","Bearer/Token"],"self_serve":"self-serve","self_serve_detail":"Seller account -> Account -> API Keys for scoped key. Public API reference browsable; QA sandbox available. Live payments need KYC/business verification.","api_surface":"REST (checkout, customers, subscribers, transactions, webhooks)","mcp":"official","verdict":"ready-mcp","blocker":"MCP in beta; live payments need KYC/business verification.","evidence":"https://apidocs.fan/","confidence":"medium"},
  51: {"one_line":"SEO/SEM data APIs (SERP, backlinks, keywords).","auth_methods":["Basic"],"self_serve":"self-serve","self_serve_detail":"Free account (no card); API login + auto-generated password in API Access tab; free Sandbox + $1 trial credit.","api_surface":"REST very broad (SERP, Backlinks, Keywords, On-Page, Labs)","mcp":"official","verdict":"ready-mcp","blocker":"","evidence":"https://docs.dataforseo.com/v3/auth/","confidence":"high"},
  53: {"one_line":"SEO toolset API (Site Explorer, backlinks) for subscribers.","auth_methods":["Bearer/Token"],"self_serve":"paid-only","self_serve_detail":"API keys in Account Settings, but API only on eligible paid plans; free account limited to test queries + 2 public endpoints.","api_surface":"REST v3 broad but gated to paid; minimal free public endpoints","mcp":"official","verdict":"buildable-effort","blocker":"API + MCP require an eligible paid plan (Lite ~$119/mo+).","evidence":"https://docs.ahrefs.com/en/api/docs/introduction","confidence":"high"},
  62: {"one_line":"Platform API to manage Vercel projects/deployments/domains.","auth_methods":["OAuth2","Bearer/Token"],"self_serve":"self-serve","self_serve_detail":"Free Vercel account -> Access Token (Bearer) from dashboard, or OAuth app. Free tier sufficient.","api_surface":"REST broad (projects, deployments, domains, env, teams)","mcp":"community","verdict":"ready-mcp","blocker":"","evidence":"https://vercel.com/docs/rest-api","confidence":"high"},
  68: {"one_line":"Atlas Administration API for orgs/projects/clusters.","auth_methods":["OAuth2","API Key"],"self_serve":"self-serve","self_serve_detail":"Free Atlas account (M0 free tier) -> OAuth2 service account or Digest API keys from dashboard.","api_surface":"REST (Atlas Admin API v2) broad","mcp":"official","verdict":"ready-mcp","blocker":"","evidence":"https://www.mongodb.com/docs/atlas/api/api-authentication/","confidence":"high"},
  72: {"one_line":"Web API to read/write Airtable base records/schema.","auth_methods":["OAuth2","Bearer/Token"],"self_serve":"self-serve","self_serve_detail":"Free account -> Personal Access Token (/create/tokens) or OAuth integration. Free plan sufficient.","api_surface":"REST broad (records, metadata, bases, webhooks)","mcp":"official","verdict":"ready-mcp","blocker":"","evidence":"https://airtable.com/developers/web/api/authentication","confidence":"high"},
  77: {"one_line":"PM platform with public REST API (v2) + official MCP.","auth_methods":["OAuth2","API Key"],"self_serve":"self-serve","self_serve_detail":"Free account -> personal API token (Settings -> ClickUp API) or OAuth app. API on all plans.","api_surface":"REST v2 broad (tasks, spaces, docs, time, webhooks)","mcp":"official","verdict":"ready-mcp","blocker":"","evidence":"https://developer.clickup.com/docs/authentication","confidence":"high"},
  84: {"one_line":"Japanese payment gateway (Paygent) Connect, requires merchant onboarding.","auth_methods":["Other"],"self_serve":"gated","self_serve_detail":"Apply as merchant, submit notarized docs, pass per-payment-institution review; credentials issued post-contract. Sandbox + production separate applications.","api_surface":"REST/HTTP POST (module & link types) - payment-focused","mcp":"none","verdict":"buildable-effort","blocker":"Requires merchant contract + per-payment-institution review; no instant self-serve credentials.","evidence":"https://www.paygent.co.jp/payment_service/connect/","confidence":"medium"},
  90: {"one_line":"Private-markets research data via RESTful Direct Data API (contract).","auth_methods":["API Key"],"self_serve":"partner-gated","self_serve_detail":"API standalone offering requiring a contract; request via Direct Data team or (clients) Platform -> Plugins & Apps. Credentials via account manager post-contract.","api_surface":"REST broad (companies, funds, deals, investors) - contract-scoped","mcp":"none","verdict":"blocked","blocker":"API access requires a standalone contract; no self-serve or free signup.","evidence":"https://pitchbook.com/products/direct-access-data/api","confidence":"high"},
  93: {"one_line":"AI meeting recorder with public REST API + official MCP.","auth_methods":["API Key","OAuth2","Bearer/Token"],"self_serve":"self-serve","self_serve_detail":"Free fathom.video account -> user-level API key (Settings -> API Access) or OAuth app. Docs browsable publicly.","api_surface":"REST read-focused (meetings, recordings, transcripts, summaries, webhooks)","mcp":"official","verdict":"ready-mcp","blocker":"","evidence":"https://developers.fathom.ai/quickstart","confidence":"high"},
  98: {"one_line":"CLI rendering Mermaid diagrams locally; no remote API.","auth_methods":["None"],"self_serve":"self-serve","self_serve_detail":"Install via npm; no account/credentials. Runs locally (Puppeteer/Chromium).","api_surface":"None (local CLI / Node.js library)","mcp":"community","verdict":"ready-mcp","blocker":"","evidence":"https://github.com/mermaid-js/mermaid-cli","confidence":"high"},
}

def load_seed():
    import importlib.util
    spec = importlib.util.spec_from_file_location('seed', os.path.join(HERE, 'seed.py'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m.RECORDS

def load_web_waves():
    """Return {id: override_dict} from data/web_wave*.json (60 apps)."""
    out = {}
    for path in sorted(glob.glob(os.path.join(HERE, "web_wave*.json"))):
        with open(path, encoding="utf-8") as f:
            for rec in json.load(f):
                out[rec["id"]] = rec
    return out

def verdict_bucket(v):
    return "blocked" if v == "blocked" else "buildable"

def main():
    firstpass = load_seed()
    by_id = {r["id"]: r for r in firstpass}

    web = load_web_waves()
    # combined verified override set (VERIFIED + web waves) -> all 100
    verified = {}
    for i, v in VERIFIED.items():
        verified[i] = v
    for i, v in web.items():
        # convert full web record into an override dict (drop seed-only keys handled in merge)
        verified[i] = v

    assert set(verified.keys()) == set(by_id.keys()), \
        "Verified set must cover all 100 app ids. Missing: %s" % sorted(set(by_id) - set(verified))

    # ---- compute first-pass vs web-verified metrics (all 100) ----
    sample = []
    fp_blocked, ve_blocked = set(), set()
    fp_selfserve_free, ve_selfserve_free = set(), set()
    ss_match = ve_match = mc_match = 0
    for i in by_id:
        fp = by_id[i]; ve = verified[i]
        ss_ok = (fp["self_serve"] == ve["self_serve"])
        ve_ok = (fp["verdict"] == ve["verdict"])
        mc_ok = (fp["mcp"] == ve["mcp"])
        ss_match += ss_ok; ve_match += ve_ok; mc_match += mc_ok
        if verdict_bucket(fp["verdict"]) == "blocked": fp_blocked.add(i)
        if verdict_bucket(ve["verdict"]) == "blocked": ve_blocked.add(i)
        if fp["self_serve"] in ("self-serve","trial"): fp_selfserve_free.add(i)
        if ve["self_serve"] in ("self-serve","trial"): ve_selfserve_free.add(i)
        sample.append({
            "id": i, "name": fp["name"], "category": fp["category"],
            "firstpass": {"self_serve": fp["self_serve"], "verdict": fp["verdict"], "mcp": fp["mcp"]},
            "verified":  {"self_serve": ve["self_serve"], "verdict": ve["verdict"], "mcp": ve["mcp"]},
            "ss_match": ss_ok, "ve_match": ve_ok, "mc_match": mc_ok,
            "changed": not (ss_ok and ve_ok and mc_ok),
        })

    n = len(by_id)
    firstpass_blocked_precision = len(fp_blocked & ve_blocked)/len(fp_blocked) if fp_blocked else 1.0
    firstpass_blocked_recall = len(fp_blocked & ve_blocked)/len(ve_blocked) if ve_blocked else 1.0
    missed_buildable = ve_selfserve_free - fp_selfserve_free

    metrics = {
        "coverage": "full 100-app web verification",
        "sample_size": n,
        "self_serve_exact_match": round(ss_match/n, 3),
        "verdict_exact_match": round(ve_match/n, 3),
        "mcp_exact_match": round(mc_match/n, 3),
        "any_field_changed": sum(1 for s in sample if s["changed"]),
        "firstpass_blocked_count": len(fp_blocked),
        "verified_blocked_count": len(ve_blocked),
        "firstpass_blocked_precision": round(firstpass_blocked_precision, 3),
        "firstpass_blocked_recall": round(firstpass_blocked_recall, 3),
        "firstpass_false_blocked": sorted(fp_blocked - ve_blocked),
        "missed_free_selfserve": sorted(missed_buildable),
        "verified_blocked_apps": sorted(ve_blocked),
    }

    # ---- apply corrections -> corrected dataset ----
    OVERRIDE_KEYS = ["one_line","auth_methods","self_serve","self_serve_detail","api_surface",
                     "mcp","verdict","blocker","evidence","confidence"]
    corrected = []
    for r in firstpass:
        rec = dict(r)
        if r["id"] in verified:
            for k in OVERRIDE_KEYS:
                if k in verified[r["id"]]:
                    rec[k] = verified[r["id"]][k]
        corrected.append(rec)

    # archive first pass
    with open(os.path.join(HERE, "apps_research_firstpass.json"), "w", encoding="utf-8") as f:
        json.dump(firstpass, f, indent=2, ensure_ascii=False)
    with open(os.path.join(HERE, "apps_research.json"), "w", encoding="utf-8") as f:
        json.dump(corrected, f, indent=2, ensure_ascii=False)

    verification = {
        "waves": 12,
        "method": "Full 100-app web verification: 40-app sample (2 waves x 4 agents x 5) + 60 apps re-verified this run via 12 research sub-agent waves (web_wave1-12.json). All values fetched from live documentation.",
        "metrics": metrics,
        "sample": sample,
    }
    with open(os.path.join(HERE, "verification.json"), "w", encoding="utf-8") as f:
        json.dump(verification, f, indent=2, ensure_ascii=False)

    agg = aggregate(corrected)
    with open(os.path.join(HERE, "aggregates.json"), "w", encoding="utf-8") as f:
        json.dump(agg, f, indent=2, ensure_ascii=False)

    print("Apps:", n, "| changed by verification:", sum(1 for s in sample if s['changed']))
    print("First-pass blocked:", len(fp_blocked), "Verified blocked:", len(ve_blocked), "->", sorted(ve_blocked))
    print("First-pass blocked precision:", round(firstpass_blocked_precision,3), "recall:", round(firstpass_blocked_recall,3))
    print("Self-serve match:", round(ss_match/n,3), "Verdict match:", round(ve_match/n,3), "MCP match:", round(mc_match/n,3))
    print("Wrote corrected dataset, verification.json, aggregates.json")

def aggregate(recs):
    by_cat = defaultdict(list)
    for r in recs: by_cat[r["category"]].append(r)
    auth = Counter()
    for r in recs:
        for a in r["auth_methods"]: auth[a]+=1
    ss = Counter(r["self_serve"] for r in recs)
    vd = Counter(r["verdict"] for r in recs)
    mc = Counter(r["mcp"] for r in recs)
    conf = Counter(r["confidence"] for r in recs)
    cat_summary = {}
    for cat, rs in by_cat.items():
        cat_summary[cat] = {
            "total": len(rs),
            "ready": sum(1 for r in rs if r["verdict"] in ("ready","ready-mcp")),
            "ready_mcp": sum(1 for r in rs if r["verdict"]=="ready-mcp"),
            "buildable_effort": sum(1 for r in rs if r["verdict"]=="buildable-effort"),
            "blocked": sum(1 for r in rs if r["verdict"]=="blocked"),
            "self_serve_free": sum(1 for r in rs if r["self_serve"] in ("self-serve","trial")),
            "gated": sum(1 for r in rs if r["self_serve"] in ("gated","partner-gated")),
            "paid_only": sum(1 for r in rs if r["self_serve"]=="paid-only"),
            "mcp_any": sum(1 for r in rs if r["mcp"]!="none"),
        }
    return {
        "total": len(recs),
        "auth_methods": dict(auth),
        "self_serve": dict(ss),
        "verdict": dict(vd),
        "mcp": dict(mc),
        "confidence": dict(conf),
        "categories": cat_summary,
        "blocked_apps": [{"id":r["id"],"name":r["name"],"category":r["category"],"blocker":r["blocker"],"evidence":r["evidence"]} for r in recs if r["verdict"]=="blocked"],
        "mcp_ready_apps": [r["name"] for r in recs if r["verdict"]=="ready-mcp"],
    }

if __name__ == "__main__":
    main()
