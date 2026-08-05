#!/usr/bin/env python3
"""
question_bank_crawler.py — crawl real, currently-open job postings from
public ATS job-board APIs, extract explicit application/screening
questions, cluster near-duplicate phrasings, and curate a
diversity-balanced top-N bank for the Context Architect interview.

WHERE TO RUN THIS: an environment with open internet access — the
Hermes box on Oracle Cloud, or Kene's laptop. It will NOT run inside a
sandboxed chat tool (no network egress to boards-api.greenhouse.io /
api.lever.co from there). Hand it to Hermes as: "run
question_bank_crawler.py against seed_companies.yaml" and it'll execute
it directly via its shell tool.

Dependencies: requests, pyyaml (both `pip install requests pyyaml`).
Clustering works with zero extra dependencies (stdlib difflib) by
default; if scikit-learn is installed it automatically upgrades to
TF-IDF + cosine similarity clustering, which handles paraphrases better.

Usage:
    # Step 1 — crawl a batch of ~100 postings worth of questions
    python question_bank_crawler.py crawl \
        --seed seed_companies.yaml \
        --limit 100 \
        --out question_bank_raw.jsonl \
        --skip-crawled  # rotate past companies already in --out

    # Step 2 — cluster + curate down to a diverse top-N bank
    python question_bank_crawler.py curate \
        --raw question_bank_raw.jsonl \
        --top 100 \
        --out ../shared/question_bank.yaml
"""

import argparse
import json
import re
import sys
import time
import difflib
from collections import defaultdict
from pathlib import Path

import requests
import yaml

USER_AGENT = "job-hunting-context-architect/1.0 (research bank crawl; contact: kene)"
REQUEST_DELAY_SECONDS = 1.0  # be polite; these are public but not infinite


# ----------------------------------------------------------------------
# Fetching — one function per ATS. Each returns a list of dicts:
#   {"job_title": str, "questions": [str, ...], "company_slug": str,
#    "platform": str, "location": str, "url": str}
# ----------------------------------------------------------------------

def fetch_greenhouse(slug: str) -> list:
    """Greenhouse: list jobs, then re-fetch each with ?questions=true."""
    results = []
    list_url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    try:
        resp = requests.get(list_url, headers={"User-Agent": USER_AGENT}, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  [greenhouse:{slug}] list fetch failed: {e}", file=sys.stderr)
        return results

    jobs = resp.json().get("jobs", [])
    for job in jobs[:25]:  # cap per company so one huge board doesn't dominate a batch
        job_id = job.get("id")
        detail_url = (
            f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs/{job_id}"
            f"?questions=true"
        )
        time.sleep(REQUEST_DELAY_SECONDS)
        try:
            d = requests.get(detail_url, headers={"User-Agent": USER_AGENT}, timeout=15)
            d.raise_for_status()
        except requests.RequestException as e:
            print(f"  [greenhouse:{slug}] job {job_id} fetch failed: {e}", file=sys.stderr)
            continue
        detail = d.json()
        questions = [
            q.get("label", "").strip()
            for q in detail.get("questions", [])
            if q.get("label") and _looks_like_free_text_question(q)
        ]
        if questions:
            results.append({
                "job_title": detail.get("title", ""),
                "questions": questions,
                "company_slug": slug,
                "platform": "greenhouse",
                "location": (detail.get("location") or {}).get("name", ""),
                "url": detail.get("absolute_url", ""),
            })
    return results


def _looks_like_free_text_question(q: dict) -> bool:
    """Greenhouse mixes real free-text questions with file-upload /
    yes-no / demographic fields. Keep only fields likely to be an
    actual written-answer prompt (has real question-like text, isn't a
    resume/cover-letter upload or an EEO field)."""
    label = q.get("label", "").lower()
    if any(skip in label for skip in [
        "resume", "cover letter", "cv", "linkedin", "portfolio url",
        "gender", "race", "ethnicity", "veteran", "disability", "pronoun",
    ]):
        return False
    return len(label.split()) >= 4  # short labels are almost always form fields, not questions


def fetch_lever(slug: str) -> list:
    """Lever: postings endpoint includes application-form custom questions."""
    results = []
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  [lever:{slug}] fetch failed: {e}", file=sys.stderr)
        return results

    for posting in resp.json()[:25]:
        questions = []
        # Lever nests custom questions inside the posting's "additional"
        # or "questions" fields depending on account config — check both
        # defensively since this isn't as uniformly documented as Greenhouse.
        for block in posting.get("additionalQuestions", []) or []:
            text = block.get("text", "").strip()
            if text and len(text.split()) >= 4:
                questions.append(text)
        if questions:
            results.append({
                "job_title": posting.get("text", ""),
                "questions": questions,
                "company_slug": slug,
                "platform": "lever",
                "location": (posting.get("categories") or {}).get("location", ""),
                "url": posting.get("hostedUrl", ""),
            })
        time.sleep(REQUEST_DELAY_SECONDS)
    return results


def fetch_ashby(slug: str) -> list:
    """Ashby's public posting-api is strong on JD/comp text but doesn't
    reliably expose the application-form question set through this
    endpoint — included mainly as a JD-diversity source for the
    gap-analysis engine, not the literal question bank. Verify against
    current Ashby docs if you need the question set specifically."""
    results = []
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=false"
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  [ashby:{slug}] fetch failed: {e}", file=sys.stderr)
        return results
    # No standardized `questions` field here as of this writing — this
    # function currently returns JD text only (jobDescriptionHtml), and
    # is a placeholder for whoever revisits this once Ashby's
    # application-form endpoint is confirmed.
    for job in resp.json().get("jobs", [])[:25]:
        results.append({
            "job_title": job.get("title", ""),
            "questions": [],  # intentionally empty — see docstring
            "company_slug": slug,
            "platform": "ashby",
            "location": job.get("location", ""),
            "url": job.get("jobUrl", ""),
        })
        time.sleep(REQUEST_DELAY_SECONDS)
    return results


FETCHERS = {
    "greenhouse": fetch_greenhouse,
    "lever": fetch_lever,
    "ashby": fetch_ashby,
}


# ----------------------------------------------------------------------
# Crawl command
# ----------------------------------------------------------------------

def normalize(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text


def cmd_crawl(args):
    seed_path = Path(args.seed)
    if not seed_path.exists():
        print(f"Seed file {seed_path} not found. See ../templates/seed_companies.yaml "
              f"in this folder for the expected format.", file=sys.stderr)
        sys.exit(1)

    seed = yaml.safe_load(seed_path.read_text())

    already_crawled = set()
    out_path = Path(args.out)
    if args.skip_crawled and out_path.exists():
        for line in out_path.read_text().splitlines():
            if line.strip():
                already_crawled.add(json.loads(line)["company_slug"])

    raw_rows = []
    total_questions = 0
    for company in seed["companies"]:
        if total_questions >= args.limit:
            break
        slug = company["slug"]
        platform = company["platform"]
        if args.skip_crawled and slug in already_crawled:
            continue
        fetcher = FETCHERS.get(platform)
        if not fetcher:
            print(f"  no fetcher for platform '{platform}', skipping {slug}", file=sys.stderr)
            continue
        print(f"crawling {platform}:{slug} ...")
        postings = fetcher(slug)
        for p in postings:
            for q in p["questions"]:
                raw_rows.append({
                    "question_text": normalize(q),
                    "job_title": p["job_title"],
                    "company_slug": slug,
                    "platform": platform,
                    "location": p["location"],
                    "url": p["url"],
                    "industry_tag": company.get("industry_tags", []),
                    "seniority_tag": company.get("seniority_tags", []),
                    "function_tag": company.get("function_tags", []),
                    "geo_tag": company.get("geo_tags", []),
                    "date_crawled": time.strftime("%Y-%m-%d"),
                })
                total_questions += 1

    with open(out_path, "a") as f:
        for row in raw_rows:
            f.write(json.dumps(row) + "\n")

    print(f"\nWrote {len(raw_rows)} question rows to {out_path} "
          f"(from {len(seed['companies'])} seed companies attempted).")
    print("Run the 'curate' command next once you've accumulated ~300 rows "
          "across 2-3 crawl batches.")


# ----------------------------------------------------------------------
# Curate command — cluster near-duplicates, then pick a diverse top-N
# ----------------------------------------------------------------------

def _similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


def cluster_questions(rows: list, threshold: float = 0.72) -> list:
    """Greedy clustering: try sklearn TF-IDF+cosine if available (handles
    paraphrases better), else fall back to difflib string similarity
    (zero extra dependencies, weaker on true paraphrases but fine for
    near-duplicate phrasing, which is most of what this bank will see)."""
    texts = [r["question_text"] for r in rows]

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np

        vec = TfidfVectorizer(stop_words="english").fit_transform(texts)
        sim_matrix = cosine_similarity(vec)
        sim_fn = lambda i, j: sim_matrix[i, j]
        print("(clustering with TF-IDF + cosine similarity — sklearn found)")
    except ImportError:
        sim_fn = lambda i, j: _similarity(texts[i], texts[j])
        print("(clustering with difflib string similarity — install scikit-learn "
              "for better paraphrase detection)")

    n = len(texts)
    assigned = [-1] * n
    clusters = []
    for i in range(n):
        if assigned[i] != -1:
            continue
        cluster_id = len(clusters)
        assigned[i] = cluster_id
        members = [i]
        for j in range(i + 1, n):
            if assigned[j] != -1:
                continue
            if sim_fn(i, j) >= threshold:
                assigned[j] = cluster_id
                members.append(j)
        clusters.append(members)

    clustered = []
    for members in clusters:
        member_rows = [rows[i] for i in members]
        # canonical text: the shortest phrasing among the most-frequent
        # near-exact wording, as a reasonable proxy for "cleanest version"
        canonical = min((r["question_text"] for r in member_rows), key=len)
        clustered.append({
            "canonical_text": canonical,
            "variants_seen": sorted(set(r["question_text"] for r in member_rows) - {canonical}),
            "source_count": len(member_rows),
            "industry": sorted(set(t for r in member_rows for t in r.get("industry_tag", []))),
            "seniority": sorted(set(t for r in member_rows for t in r.get("seniority_tag", []))),
            "function": sorted(set(t for r in member_rows for t in r.get("function_tag", []))),
            "geo": sorted(set(t for r in member_rows for t in r.get("geo_tag", []))),
        })
    return clustered


def curate_diverse_top_n(clusters: list, top_n: int) -> list:
    """Pick clusters by coverage across the tag matrix, not just raw
    frequency — round-robin through (industry, seniority) cells, taking
    the highest-source_count unpicked cluster in each cell each round,
    so the final N stays spread across the diversity matrix instead of
    collapsing to whatever's most common in the easiest-to-crawl slice."""
    cells = defaultdict(list)
    for c in clusters:
        industries = c["industry"] or ["general"]
        seniorities = c["seniority"] or ["general"]
        for ind in industries:
            for sen in seniorities:
                cells[(ind, sen)].append(c)
    for cell in cells.values():
        cell.sort(key=lambda c: -c["source_count"])

    picked = []
    picked_texts = set()
    cell_keys = list(cells.keys())
    idx = 0
    while len(picked) < top_n and cell_keys:
        key = cell_keys[idx % len(cell_keys)]
        bucket = cells[key]
        candidate = next((c for c in bucket if c["canonical_text"] not in picked_texts), None)
        if candidate:
            picked.append(candidate)
            picked_texts.add(candidate["canonical_text"])
        idx += 1
        if idx > len(cell_keys) * (top_n + 5):  # exhausted — every cell drained
            break

    # top up with highest-frequency remaining clusters overall if the
    # matrix didn't fill the quota
    if len(picked) < top_n:
        remaining = sorted(
            (c for c in clusters if c["canonical_text"] not in picked_texts),
            key=lambda c: -c["source_count"],
        )
        picked.extend(remaining[: top_n - len(picked)])

    return picked[:top_n]


JURISDICTION_KEYWORDS = [
    "sponsorship", "legally entitled to work", "legally authorized to work",
    "work authorization", "work permit", "visa status", "require a visa",
    "eligible to work",
]


def _looks_jurisdiction_dependent(text: str) -> bool:
    """Heuristic only, not a firm classification — flags a candidate for
    the human review pass in HOW-TO-RUN.md Step 3, per
    answer-variants.md. Deliberately biased toward over-flagging: a
    false negative here (missing one) is worse than a false positive."""
    lowered = text.lower()
    return any(kw in lowered for kw in JURISDICTION_KEYWORDS)


def cmd_curate(args):
    raw_path = Path(args.raw)
    rows = [json.loads(line) for line in raw_path.read_text().splitlines() if line.strip()]
    print(f"loaded {len(rows)} raw question rows")

    clusters = cluster_questions(rows)
    print(f"collapsed to {len(clusters)} distinct question clusters")

    top = curate_diverse_top_n(clusters, args.top)
    print(f"curated down to {len(top)} — review this list before treating it as live")

    bank = []
    for i, c in enumerate(top, start=1):
        bank.append({
            "id": f"qb_{i:04d}",
            "canonical_text": c["canonical_text"],
            "variants_seen": c["variants_seen"],
            "tags": {
                "industry": c["industry"],
                "seniority": c["seniority"],
                "function": c["function"],
                "geo": c["geo"],
            },
            "jurisdiction_dependent": _looks_jurisdiction_dependent(c["canonical_text"]),
            "source_count": c["source_count"],
        })

    out_path = Path(args.out)
    out_path.write_text(yaml.dump(bank, sort_keys=False, allow_unicode=True))
    print(f"wrote curated bank to {out_path}")
    print("\nNext: Kene reviews this file once by hand before "
          "07-context-architect starts drawing from it live.")


# ----------------------------------------------------------------------
# Diff / promote — for the low-cadence automated refresh (cron job #6).
# A cron-triggered curate run should never overwrite the live bank
# directly; it writes a candidate file, `diff` produces a human-readable
# summary of what changed, and only `promote` (run after Kene approves
# the digest) copies candidate -> live. Mirrors the same staged-approval
# spirit as `skills.write_approval` in security/security-setup.md,
# applied to a data file instead of a skill file.
# ----------------------------------------------------------------------

def cmd_diff(args):
    live_path = Path(args.live)
    candidate_path = Path(args.candidate)

    live = (yaml.safe_load(live_path.read_text()) or []) if live_path.exists() else []
    candidate = yaml.safe_load(candidate_path.read_text()) or []

    live_texts = {row["canonical_text"] for row in live}
    candidate_texts = {row["canonical_text"] for row in candidate}

    added = candidate_texts - live_texts
    dropped = live_texts - candidate_texts

    print(f"Comparing {live_path} ({len(live)} questions) -> {candidate_path} ({len(candidate)} questions)\n")

    if added:
        print(f"NEW ({len(added)}):")
        for row in candidate:
            if row["canonical_text"] in added:
                tags = row.get("tags", {})
                tag_str = ", ".join(f"{k}={v}" for k, v in tags.items() if v)
                print(f"  + {row['canonical_text']}  [{tag_str}]")
        print()

    if dropped:
        print(f"DROPPED ({len(dropped)}) — no longer among the top {len(candidate)} by coverage:")
        for row in live:
            if row["canonical_text"] in dropped:
                print(f"  - {row['canonical_text']}")
        print()

    if not added and not dropped:
        print("No change in question set — coverage/source_count may have "
              "shifted slightly but nothing worth a Telegram digest.")

    print(f"\nRun 'promote --candidate {candidate_path} --live {live_path}' "
          f"after Kene approves this diff.")


def cmd_promote(args):
    candidate_path = Path(args.candidate)
    live_path = Path(args.live)
    if live_path.exists():
        backup = live_path.with_suffix(live_path.suffix + ".bak")
        backup.write_text(live_path.read_text())
        print(f"backed up previous live bank to {backup}")
    live_path.write_text(candidate_path.read_text())
    print(f"promoted {candidate_path} -> {live_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p_crawl = sub.add_parser("crawl", help="crawl a batch of postings and extract questions")
    p_crawl.add_argument("--seed", required=True, help="path to seed_companies.yaml")
    p_crawl.add_argument("--limit", type=int, default=100, help="stop after ~N questions extracted")
    p_crawl.add_argument("--out", required=True, help="jsonl file to append raw rows to")
    p_crawl.add_argument("--skip-crawled", action="store_true", help="skip company slugs already in --out")
    p_crawl.set_defaults(func=cmd_crawl)

    p_curate = sub.add_parser("curate", help="cluster + curate raw rows into a bank file")
    p_curate.add_argument("--raw", required=True, help="jsonl file produced by 'crawl'")
    p_curate.add_argument("--top", type=int, default=100, help="final bank size")
    p_curate.add_argument("--out", required=True, help="output path — a candidate file for 'diff', or the live bank on first build")
    p_curate.set_defaults(func=cmd_curate)

    p_diff = sub.add_parser("diff", help="compare a curated candidate bank against the live bank")
    p_diff.add_argument("--live", required=True, help="path to the current shared/question_bank.yaml")
    p_diff.add_argument("--candidate", required=True, help="path to a freshly curated candidate file")
    p_diff.set_defaults(func=cmd_diff)

    p_promote = sub.add_parser("promote", help="copy an approved candidate bank over the live bank (backs up the old one)")
    p_promote.add_argument("--candidate", required=True)
    p_promote.add_argument("--live", required=True)
    p_promote.set_defaults(func=cmd_promote)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
