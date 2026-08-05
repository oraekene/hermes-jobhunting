#!/usr/bin/env python3
"""
title_taxonomy_builder.py — build, enrich, embed, and query the title
taxonomy behind Phase 1.5's adjacent-title expansion. See
title-taxonomy.md for the full design reasoning; this is the
implementation of the four stages described there.

WHERE TO RUN THIS: same constraint as question_bank_crawler.py — an
environment with open internet access (Hermes box or Kene's laptop), not
a sandboxed chat tool. `build-core` and `enrich` both make outbound HTTP
calls this script cannot make from inside a restricted tool sandbox.

Dependencies:
    pip install requests pyyaml fastembed sqlite-vec
(fastembed/sqlite-vec are only needed for `embed`/`query` — `build-core`
and `enrich` work without them.)

Credentials needed:
    ONET_USERNAME / ONET_PASSWORD  — free O*NET Web Services developer
        account: https://services.onetcenter.org/developer/signup
        (HTTP Basic Auth against services.onetcenter.org — verify the
        exact current endpoint paths against O*NET's own docs before a
        real run; their Web Services API has had path revisions before,
        the same "verify against current docs" caveat
        question_bank_crawler.py already gives for Ashby applies here.)
    ADZUNA_APP_ID / ADZUNA_APP_KEY — free tier signup:
        https://developer.adzuna.com/

Usage:
    # Stage 1 — pull the validated O*NET base layer (run once, then
    # refreshed monthly/quarterly per title-taxonomy.md's cadence)
    python title_taxonomy_builder.py build-core \
        --out title_taxonomy_core.jsonl

    # Stage 2 — enrich a subset of occupations with current market signal,
    # reusing question_bank_crawler.py's ATS fetchers + Adzuna
    python title_taxonomy_builder.py enrich \
        --core title_taxonomy_core.jsonl \
        --relevant-only ../shared/target-profile.yaml \
        --out title_taxonomy_market.jsonl

    # Stage 3 — build embeddings and the sqlite-vec index
    python title_taxonomy_builder.py embed \
        --core title_taxonomy_core.jsonl \
        --market title_taxonomy_market.jsonl \
        --out title_taxonomy.sqlite

    # Stage 4 — query (what Phase 1.5 actually calls at interview time)
    python title_taxonomy_builder.py query \
        --db title_taxonomy.sqlite \
        --text-file /path/to/domain-knowledge-and-star-bank-dump.txt \
        --top 8
"""

import argparse
import json
import sys
from pathlib import Path

import requests
import yaml

sys.path.insert(0, str(Path(__file__).parent))
try:
    from question_bank_crawler import fetch_greenhouse, fetch_lever, fetch_ashby, USER_AGENT
except ImportError:
    # allows this file to be imported/linted standalone before
    # question_bank_crawler.py exists alongside it in a fresh checkout
    fetch_greenhouse = fetch_lever = fetch_ashby = None
    USER_AGENT = "job-hunting-title-taxonomy/1.0"

ONET_BASE = "https://services.onetcenter.org/ws/online"
EMBED_MODEL = "BAAI/bge-small-en-v1.5"  # ~130MB, CPU-friendly, 384-dim


# ----------------------------------------------------------------------
# Stage 1 — O*NET base layer
# ----------------------------------------------------------------------

def _onet_get(path: str, username: str, password: str) -> dict:
    resp = requests.get(
        f"{ONET_BASE}{path}",
        auth=(username, password),
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()


def fetch_onet_occupation_list(username: str, password: str) -> list:
    """All ~1,016 O*NET-SOC occupation codes + titles. Paginated by the
    API; loop until a page comes back short of the page size."""
    occupations, start = [], 1
    while True:
        page = _onet_get(f"/occupations?start={start}&end={start + 99}", username, password)
        batch = page.get("occupation", [])
        occupations.extend(batch)
        if len(batch) < 100:
            break
        start += 100
    return occupations


def fetch_onet_occupation_detail(code: str, username: str, password: str) -> dict:
    """Pulls the content-model fields that matter for a "full profile":
    tasks, knowledge, skills, abilities, education, job zone, alternate
    titles, hot technologies. Each content area is a separate O*NET
    endpoint — verify exact paths against current docs before a real run."""
    detail = {"onet_soc_code": code}
    endpoints = {
        "summary": f"/occupations/{code}/summary",
        "tasks": f"/occupations/{code}/details/tasks",
        "knowledge": f"/occupations/{code}/details/knowledge",
        "skills": f"/occupations/{code}/details/skills",
        "abilities": f"/occupations/{code}/details/abilities",
        "education": f"/occupations/{code}/details/education",
        "job_zone": f"/occupations/{code}/details/job_zone",
        "technology": f"/occupations/{code}/details/technology_skills",
        "alternate_titles": f"/occupations/{code}/details/alternate_titles",
    }
    for field, path in endpoints.items():
        try:
            detail[field] = _onet_get(path, username, password)
        except requests.RequestException as e:
            print(f"  [onet:{code}] {field} fetch failed: {e}", file=sys.stderr)
            detail[field] = None
    return detail


def cmd_build_core(args):
    import os
    username = os.environ.get("ONET_USERNAME")
    password = os.environ.get("ONET_PASSWORD")
    if not username or not password:
        print("Set ONET_USERNAME / ONET_PASSWORD env vars (free signup at "
              "services.onetcenter.org/developer/signup).", file=sys.stderr)
        sys.exit(1)

    print("fetching occupation list...")
    occupations = fetch_onet_occupation_list(username, password)
    print(f"found {len(occupations)} occupations, pulling full profiles "
          f"(this takes a while — one request per content area per code)")

    out_path = Path(args.out)
    with out_path.open("w") as f:
        for i, occ in enumerate(occupations, start=1):
            code = occ.get("code")
            detail = fetch_onet_occupation_detail(code, username, password)
            detail["onet_title"] = occ.get("title")
            f.write(json.dumps(detail) + "\n")
            if i % 25 == 0:
                print(f"  {i}/{len(occupations)}...")
    print(f"wrote {len(occupations)} occupation profiles to {out_path}")


# ----------------------------------------------------------------------
# Stage 2 — market-freshness enrichment (reuses existing ATS fetchers)
# ----------------------------------------------------------------------

def fetch_adzuna(query: str, country: str, app_id: str, app_key: str, results: int = 20) -> list:
    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
    params = {
        "app_id": app_id, "app_key": app_key, "what": query,
        "results_per_page": results, "content-type": "application/json",
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  [adzuna:{query}/{country}] fetch failed: {e}", file=sys.stderr)
        return []
    return resp.json().get("results", [])


def _relevant_occupations(core_path: Path, target_profile_path: Path) -> set:
    """Filter to occupations worth crawling right now — same 'don't
    enrich wildly outside Kene's domain' discipline title-taxonomy.md
    describes. Matches on simple substring overlap between the target
    profile's title_variants and each occupation's title/alternate
    titles; a rough filter is fine here since it only controls crawl
    *cost*, not correctness — anything missed just stays at O*NET-only
    fidelity until the quarterly broad enrichment pass."""
    profile = yaml.safe_load(target_profile_path.read_text()) or {}
    wanted_titles = {
        (tv.get("title") if isinstance(tv, dict) else tv).lower()
        for tv in profile.get("title_variants", [])
    }
    if not wanted_titles:
        return set()

    relevant = set()
    for line in core_path.read_text().splitlines():
        if not line.strip():
            continue
        occ = json.loads(line)
        titles = [occ.get("onet_title", "")]
        alt = occ.get("alternate_titles") or {}
        titles += [t.get("title", "") for t in alt.get("title", [])] if isinstance(alt, dict) else []
        titles_lower = [t.lower() for t in titles if t]
        if any(any(w in t or t in w for w in wanted_titles) for t in titles_lower):
            relevant.add(occ["onet_soc_code"])
    return relevant


def cmd_enrich(args):
    import os
    core_path = Path(args.core)
    codes_to_enrich = None
    if args.relevant_only:
        codes_to_enrich = _relevant_occupations(core_path, Path(args.relevant_only))
        print(f"enriching {len(codes_to_enrich)} occupations relevant to "
              f"the current target profile (pass --all for the full "
              f"quarterly sweep instead)")

    adzuna_id = os.environ.get("ADZUNA_APP_ID")
    adzuna_key = os.environ.get("ADZUNA_APP_KEY")

    out_path = Path(args.out)
    with out_path.open("w") as f:
        for line in core_path.read_text().splitlines():
            if not line.strip():
                continue
            occ = json.loads(line)
            code = occ["onet_soc_code"]
            if codes_to_enrich is not None and code not in codes_to_enrich:
                continue
            title = occ.get("onet_title", "")
            print(f"  enriching: {title} ({code})")

            postings = []
            if adzuna_id and adzuna_key:
                for country in (args.countries or ["us", "gb"]):
                    postings += fetch_adzuna(title, country, adzuna_id, adzuna_key)

            title_strings_seen = sorted({p.get("title", "") for p in postings if p.get("title")})
            tools_seen = []  # left for a human/LLM pass over description text —
                              # a plain keyword scan over free-text JD bodies is
                              # too noisy to auto-populate reliably; see
                              # title-taxonomy.md's crawl-only failure mode note
            salaries = [p.get("salary_min") for p in postings if p.get("salary_min")]

            market = {
                "onet_soc_code": code,
                "last_crawled_at": None,  # set by caller/cron wrapper to today's date
                "current_title_strings_seen": title_strings_seen,
                "tools_seen": tools_seen,
                "salary_band_observed": {
                    "currency": "USD",
                    "low": min(salaries) if salaries else None,
                    "high": max(salaries) if salaries else None,
                    "sample_size": len(salaries),
                },
                "source_count": len(postings),
            }
            f.write(json.dumps(market) + "\n")
    print(f"wrote market-signals layer to {out_path} — never overwrites "
          f"{core_path}, merge happens at embed time")


# ----------------------------------------------------------------------
# Stage 3 — embed + sqlite-vec index
# ----------------------------------------------------------------------

def _profile_text_blob(core_row: dict, market_row: dict = None) -> str:
    """One text blob per occupation for embedding — concatenates the
    fields that actually describe what the work involves, not metadata."""
    parts = [core_row.get("onet_title", "")]
    for field in ("tasks", "knowledge", "skills", "abilities"):
        block = core_row.get(field)
        if isinstance(block, dict):
            items = block.get("element") or block.get(field) or []
            parts += [str(i.get("name") or i.get("statement") or i) for i in items if i]
    if market_row:
        parts += market_row.get("current_title_strings_seen", [])
        parts += market_row.get("tools_seen", [])
    return " | ".join(p for p in parts if p)


def cmd_embed(args):
    from fastembed import TextEmbedding
    import sqlite3
    import sqlite_vec

    core_rows = [json.loads(l) for l in Path(args.core).read_text().splitlines() if l.strip()]
    market_by_code = {}
    if args.market and Path(args.market).exists():
        for l in Path(args.market).read_text().splitlines():
            if l.strip():
                m = json.loads(l)
                market_by_code[m["onet_soc_code"]] = m

    model = TextEmbedding(model_name=EMBED_MODEL)
    texts = [_profile_text_blob(r, market_by_code.get(r["onet_soc_code"])) for r in core_rows]
    print(f"embedding {len(texts)} occupation profiles with {EMBED_MODEL}...")
    vectors = list(model.embed(texts))

    db_path = Path(args.out)
    conn = sqlite3.connect(db_path)
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    conn.execute("CREATE TABLE IF NOT EXISTS profiles (id INTEGER PRIMARY KEY, onet_soc_code TEXT, onet_title TEXT, blob TEXT)")
    conn.execute(f"CREATE VIRTUAL TABLE IF NOT EXISTS profile_vectors USING vec0(embedding float[{len(vectors[0])}])")
    conn.execute("DELETE FROM profiles")
    conn.execute("DELETE FROM profile_vectors")
    for i, (row, text, vec) in enumerate(zip(core_rows, texts, vectors)):
        conn.execute("INSERT INTO profiles (id, onet_soc_code, onet_title, blob) VALUES (?, ?, ?, ?)",
                     (i, row["onet_soc_code"], row.get("onet_title", ""), text))
        conn.execute("INSERT INTO profile_vectors (rowid, embedding) VALUES (?, ?)",
                     (i, json.dumps(list(map(float, vec)))))
    conn.commit()
    conn.close()
    print(f"wrote {len(core_rows)} embedded profiles to {db_path}")


# ----------------------------------------------------------------------
# Stage 4 — query (what Phase 1.5 actually calls)
# ----------------------------------------------------------------------

def cmd_query(args):
    from fastembed import TextEmbedding
    import sqlite3
    import sqlite_vec

    text = Path(args.text_file).read_text() if args.text_file else args.text
    if not text:
        print("provide --text or --text-file", file=sys.stderr)
        sys.exit(1)

    model = TextEmbedding(model_name=EMBED_MODEL)
    query_vec = list(model.embed([text]))[0]

    conn = sqlite3.connect(args.db)
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    rows = conn.execute(
        """
        SELECT p.onet_soc_code, p.onet_title, p.blob, v.distance
        FROM profile_vectors v
        JOIN profiles p ON p.id = v.rowid
        WHERE v.embedding MATCH ? AND k = ?
        ORDER BY v.distance
        """,
        (json.dumps(list(map(float, query_vec))), args.top),
    ).fetchall()
    conn.close()

    results = [
        {"onet_soc_code": code, "onet_title": title, "distance": dist, "blob_preview": blob[:200]}
        for code, title, blob, dist in rows
    ]
    print(json.dumps(results, indent=2))
    print(f"\n{len(results)} candidates above — Phase 1.5 filters these against "
          f"existing title_variants and drafts suggestions only for genuinely "
          f"new ones, each with a cited rationale, never auto-applied.",
          file=sys.stderr)


# ----------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p_core = sub.add_parser("build-core", help="pull the O*NET base layer")
    p_core.add_argument("--out", required=True)
    p_core.set_defaults(func=cmd_build_core)

    p_enrich = sub.add_parser("enrich", help="add current market signal via crawl")
    p_enrich.add_argument("--core", required=True)
    p_enrich.add_argument("--relevant-only", help="path to target-profile.yaml — scope the crawl to relevant occupations")
    p_enrich.add_argument("--countries", nargs="*", help="Adzuna country codes, e.g. us gb ng")
    p_enrich.add_argument("--out", required=True)
    p_enrich.set_defaults(func=cmd_enrich)

    p_embed = sub.add_parser("embed", help="build embeddings + sqlite-vec index")
    p_embed.add_argument("--core", required=True)
    p_embed.add_argument("--market", help="market-signals jsonl from 'enrich' (optional)")
    p_embed.add_argument("--out", required=True)
    p_embed.set_defaults(func=cmd_embed)

    p_query = sub.add_parser("query", help="find nearest title profiles to a text blob")
    p_query.add_argument("--db", required=True)
    p_query.add_argument("--text")
    p_query.add_argument("--text-file")
    p_query.add_argument("--top", type=int, default=8)
    p_query.set_defaults(func=cmd_query)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
