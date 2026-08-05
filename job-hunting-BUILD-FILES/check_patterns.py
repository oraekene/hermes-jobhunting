#!/usr/bin/env python3
"""
check_patterns.py — regression gate for the injection corpus.

    python3 check_patterns.py

This is step 4 of the weekly runbook and the reason the corpus stays usable.
It enforces:
  * every pattern has a positive fixture that fires
  * every pattern has >= 2 negative fixtures that do not
  * no pattern fires on the benign posting corpus
  * every pattern has a reproduction date and a plain-language user message
  * every pattern declares at least one of the four boundaries

A corpus that produces false positives gets switched off by the user, and then
it protects nothing. The false-positive budget is therefore zero, not small.
"""
import re, sys, yaml
from datetime import date

BOUNDARIES = {"posting_text", "email_body", "dm_reply", "fetched_page"}
SEVERITIES = {"block", "strip", "flag"}

# A small stand-in for the real benign corpus. In production this reads a few
# thousand real postings collected with consent, not seven lines.
BENIGN = [
    "We are looking for a Product Manager to own our payments surface.",
    "Please disregard the earlier salary range; the band has been updated.",
    "Ignore prior experience requirements if you have equivalent training.",
    "You are an experienced engineer who has shipped production systems.",
    "Send your resume to careers@company.example as part of your application.",
    "We use an applicant tracking system to manage submissions.",
    "Reference: 550e8400-e29b-41d4-a716-446655440000",
    "This role involves approval workflows and internal tooling.",
    "Update your permissions with the security team before day one.",
    "You are a natural communicator and a strong writer.",
]

FAIL, WARN = [], []


def fires(pat, text):
    m = pat["match"]
    if m["type"] == "regex":
        return re.search(m["pattern"], text) is not None
    if m["type"] == "keyword_any":
        low = text.lower()
        return any(k.lower() in low for k in m["keywords"])
    if m["type"] == "structural":
        return None          # evaluated by the HTML parser, not here
    if m["type"] == "composite":
        return None          # needs runtime context (posting domain, ATS list)
    FAIL.append(f"{pat['id']}: unknown match type {m['type']!r}")
    return False


def main(path="patterns.yaml"):
    doc = yaml.safe_load(open(path))
    pats = doc["patterns"]
    ids = [p["id"] for p in pats]
    if len(ids) != len(set(ids)):
        FAIL.append("duplicate pattern ids")

    structural = 0
    for p in pats:
        pid = p["id"]

        if p["severity"] not in SEVERITIES:
            FAIL.append(f"{pid}: unknown severity {p['severity']!r}")
        bad = set(p.get("boundaries", [])) - BOUNDARIES
        if bad:
            FAIL.append(f"{pid}: unknown boundaries {sorted(bad)}")
        if not p.get("boundaries"):
            FAIL.append(f"{pid}: declares no boundary — it cannot reach this pipeline")
        if not p.get("user_message", "").strip():
            FAIL.append(f"{pid}: no plain-language user message")
        elif any(w in p["user_message"] for w in ("regex", "pattern", "INJ-", ".py")):
            FAIL.append(f"{pid}: user message leaks internals")
        if not p.get("reproduced"):
            FAIL.append(f"{pid}: no reproduction date — unreproduced patterns rot the corpus")

        fx = p.get("fixtures") or {}
        pos, neg = fx.get("positive") or [], fx.get("negative") or []
        if not pos:
            FAIL.append(f"{pid}: no positive fixture")
        if len(neg) < 2:
            FAIL.append(f"{pid}: needs >= 2 negative fixtures, has {len(neg)}")

        if p["match"]["type"] in ("structural", "composite"):
            structural += 1
            if p["match"]["type"] == "composite" and not p["match"].get("stage_2_rule"):
                FAIL.append(f"{pid}: composite pattern with no stage-2 rule "
                            f"is a regex pretending to be safe")
            continue

        for t in pos:
            if not fires(p, t):
                FAIL.append(f"{pid}: positive fixture does not fire — {t[:60]!r}")
        for t in neg:
            if fires(p, t):
                FAIL.append(f"{pid}: NEGATIVE fixture fires — {t[:60]!r}")

    # the gate that matters
    fps = []
    for p in pats:
        if p["match"]["type"] in ("structural", "composite"):
            continue
        for t in BENIGN:
            if fires(p, t):
                fps.append((p["id"], t))
    for pid, t in fps:
        FAIL.append(f"{pid}: FALSE POSITIVE on benign text — {t[:60]!r}")

    # coverage
    cov = {b: sum(1 for p in pats if b in p.get("boundaries", [])) for b in sorted(BOUNDARIES)}

    print(f"{len(pats)} patterns ({structural} need runtime context: HTML parser or domain check)")
    for b, n in cov.items():
        print(f"  {b:<14} {n}")
        if n == 0:
            WARN.append(f"boundary {b} has no patterns")
    print(f"benign corpus: {len(BENIGN)} samples, {len(fps)} false positives")
    print()
    for w in WARN:
        print("WARN  " + w)
    for f in FAIL:
        print("FAIL  " + f)
    if FAIL:
        sys.exit(1)
    print("corpus clean — safe to sign and canary")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "patterns.yaml")
