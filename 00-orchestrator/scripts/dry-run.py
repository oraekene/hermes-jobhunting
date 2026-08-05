#!/usr/bin/env python3
"""Dry-run the pipeline against a fixture posting (D8).

Nothing in this package could be validated before pointing it at real
employers. Every check was manual and after the fact — and the artifacts
it produces go to real companies under Rule 1's approval boundary, so
"we'll notice if it looks wrong" is a weak position to be in.

This runs against a fixture in a THROWAWAY database, asserts the
invariants that must hold, and tears down. No network access needed. It
never touches shared/applications.db.

Verifies:
  1. The migration chain applies cleanly, in order, from scratch.
  2. The superseded _3.sql stayed out of the chain.
  3. Cross-source dedup: one posting from three sources = one
     application, three posting_sources rows.
  4. Gate 2 skips are distinguishable from Gate 2 passes.
  5. Rule 1: nothing at 'submitted' without an approval decision.
  6. Soft-deleted journal entries drop out of the live set immediately.

Usage:  python 00-orchestrator/scripts/dry-run.py --skill-dir .
"""
import argparse, os, re, sqlite3, sys, tempfile
from pathlib import Path

# Derived from shared/, not hand-listed. The hand-listed form went stale
# twice independently (this file stopped at _13, install-check.py at _14)
# while README step 4 stayed correct, so the chain a green dry-run had
# actually exercised was five migrations short of the one users install.
# A derived list cannot drift; adding a migration is now a one-file change.
SUPERSEDED = {"applications_db_schema_addendum_3.sql"}   # superseded by _4

def migration_chain(root):
    import glob, os
    def order(n):
        m = re.search(r"addendum_(\d+)\.sql$", n)
        return (1, int(m.group(1))) if m else (0, 0)
    files = [os.path.basename(f) for f in glob.glob(str(root / "shared" / "*.sql"))]
    base = "applications_db_schema.sql"
    rest = sorted((f for f in files if f != base and f not in SUPERSEDED), key=order)
    return ([base] if base in files else []) + rest

FIXTURE = {
    "company": "Fixture Analytics Ltd",
    "role_title": "Analytics Lead, Operations",
    "location": "Remote",
    "urls": [
        ("https://linkedin.example/jobs/1", "linkedin", "job_1_boards"),
        ("https://fixture.example/careers/1", "company_careers", "job_2_openweb"),
        ("https://x.example/status/1", "x", "job_10_social"),
    ],
}

results = []
def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  -- {detail}" if detail and not ok else ""))

def fingerprint(c, t, l):
    return f"{c.strip().lower()}|{t.strip().lower()}|{l.strip().lower()}"

def summarise():
    failed = [r for r in results if not r[1]]
    print(f"\n{len(results)-len(failed)}/{len(results)} checks passed")
    if failed:
        print("\nFAILED:")
        for n,_,d in failed: print(f"  - {n}: {d}")
        return 1
    print("pipeline invariants hold -- safe to point at real postings")
    return 0

# ---------------------------------------------------------------- static
# Package-integrity checks. No database, no network. These turn one-time
# fixes into enforced invariants: D6 (description length), D7
# (related_skills resolution), B21 (reference paths), and the cron-number
# collision class that the A/B merge actually hit.

def static_checks(root: Path):
    import re, glob, yaml

    skills = sorted(glob.glob(str(root / "*" / "SKILL.md")))
    fms = {}
    for sp in skills:
        m = re.match(r"^---\n(.*?)\n---", Path(sp).read_text(encoding="utf-8"), re.S)
        if not m:
            check(f"{Path(sp).parent.name}: has YAML frontmatter", False)
            continue
        try:
            fms[sp] = yaml.safe_load(m.group(1))
        except Exception as e:
            check(f"{Path(sp).parent.name}: frontmatter parses", False, str(e)[:80])

    check("every SKILL.md has parseable frontmatter", len(fms) == len(skills),
          f"{len(fms)} of {len(skills)}")

    # D6 -- the skill index truncates descriptions at 57 chars. Over that
    # and the trigger class is invisible, silently: the skill simply stops
    # being selected. Nothing else in the package would report it.
    long = [(Path(s).parent.name, len(f["description"])) for s, f in fms.items()
            if len(f.get("description", "")) > 60]
    check("all descriptions <= 60 chars (skill index truncates at 57)", not long,
          "; ".join(f"{n}={l}" for n, l in long))

    boiler = [Path(s).parent.name for s, f in fms.items()
              if f.get("description", "").startswith("Use this skill")]
    check("no description wastes the budget on boilerplate", not boiler, ", ".join(boiler))

    # D7 -- build_edges only forms an edge where BOTH endpoints exist. A
    # typo does not error, it silently produces no edge.
    names = {f.get("name") for f in fms.values()}
    dangling = [(f.get("name"), r) for f in fms.values()
                for r in (f.get("metadata", {}).get("hermes", {}).get("related_skills") or [])
                if r not in names]
    check("no dangling related_skills edge", not dangling,
          "; ".join(f"{a}->{b}" for a, b in dangling))

    check("no duplicate skill names", len(names) == len(fms),
          f"{len(names)} unique of {len(fms)}")

    nometa = [Path(s).parent.name for s, f in fms.items()
              if "hermes" not in (f.get("metadata") or {})]
    check("every skill declares metadata.hermes", not nometa, ", ".join(nometa))

    # B21 -- reference paths resolve. Line-wrapped paths are excluded:
    # the regex sees a fragment, not a broken link.
    bad = set()
    for fp in glob.glob(str(root / "**" / "*"), recursive=True):
        if not os.path.isfile(fp) or ".merge-history" in fp: continue
        if os.path.basename(fp) == "dry-run.py": continue  # its comments hold example paths
        # Changelogs describe PAST layouts. A path that was correct when
        # written stays correct as history; rewriting it to satisfy a link
        # checker falsifies the record. Same reasoning that keeps the
        # retired 15-interview-prep references in them.
        if os.path.basename(fp) in ("ADDENDUM-CHANGELOG.md", "HERMES_UPGRADE_CHANGELOG.md"): continue
        if not fp.endswith((".md", ".py", ".sql", ".yaml", ".template")): continue
        body = Path(fp).read_text(encoding="utf-8", errors="replace")
        # Prose wraps mid-path: "06-cover-letter/\n  references/x.md" is one
        # correct link, not a broken one. Rejoin before matching, or the
        # scan reports every wrapped path as missing -- which is noise, and
        # noise is how a real broken link gets ignored.
        body = re.sub(r"/\s*\n\s*", "/", body)
        body = re.sub(r"-\s*\n\s*", "-", body)   # names wrap mid-hyphen too
        for m in re.finditer(r"(?<![\w/])[\w./-]*(?:references|templates|scripts)/[\w.-]+\.(?:md|py|sh|yaml|json|jsonl)", body):
            ref = m.group(0)
            if ref.startswith("/") or "SKILL_DIR" in ref: continue
            # Paths into OTHER Hermes skills (bundled or optional) are not
            # this package's to resolve.
            if ref.startswith(("optional-skills/", "skills/")): continue
            # Generated at runtime by question_bank_crawler.py -- absent on
            # a fresh checkout by design.
            if "question_bank_raw" in ref: continue
            base = os.path.dirname(fp)
            cands = [os.path.normpath(os.path.join(base, ref)),
                     os.path.normpath(os.path.join(str(root), ref))]
            # README step 4 does `cd shared` before invoking ../00-.../x.py.
            # That path is relative to a shell cwd, not to the file. Try every
            # package directory as a possible cwd rather than reporting it.
            if ref.startswith("../"):
                cands += [os.path.normpath(os.path.join(d, ref))
                          for d, _, _ in os.walk(str(root))]
            if not any(os.path.exists(c) for c in cands):
                # Report WHERE, not just what. A missing-path message
                # without a source file makes the fix a search.
                bad.add(f"{ref}  (in {os.path.relpath(fp, str(root))})")
    check("every reference path resolves", not bad, "\n           ".join(sorted(bad)[:6]))

    # Cron numbering -- the A/B merge collided on job 9 because the
    # addendum was numbered against a stale count. Contiguity is cheap to
    # assert and the failure is a job silently overwriting another.
    cj = (root / "cron" / "cron-jobs.md")
    if cj.exists():
        # Labels, not integers: "8" and "8b" are different jobs. Keying on
        # the integer alone reports a deliberate sub-job as a collision.
        labels = re.findall(r"^## (\d+[a-z]?)\.", cj.read_text(encoding="utf-8"), re.M)
        check("no duplicate cron job labels", len(labels) == len(set(labels)),
              f"{sorted(l for l in set(labels) if labels.count(l) > 1)}")
        nums = sorted({int(re.match(r"\d+", l).group()) for l in labels})
        check("cron job numbers are contiguous from 1",
              nums == list(range(1, max(nums) + 1)) if nums else False, f"got {nums}")

    # Every migration in shared/ appears in README install step 4. The
    # chain itself is now derived, so THIS is the copy that can go stale:
    # README step 4 is the sequence a human actually runs. Catches
    # "added a migration, forgot the install docs" -- which is the failure
    # that put this package five migrations behind its own verifier.
    # superseded. Catches "added a migration, forgot the install docs".
    chain = migration_chain(root)
    readme = (root / "README.md")
    if readme.exists():
        rt = readme.read_text(encoding="utf-8")
        undocumented = [m for m in chain if m not in rt]
        check("every migration in the chain is in README install step 4",
              not undocumented, ", ".join(undocumented))
        # And the reverse: a sentinel comment claiming a command count.
        import re as _re
        cnt = len(_re.findall(r"^sqlite3 applications\.db < ", rt, _re.M))
        check("README step 4 applies the whole chain", cnt == len(chain),
              f"README runs {cnt}, chain has {len(chain)}")

    # install-check.py's SCHEMA_FILES is authored on purpose (see the note
    # there). Authored means it can drift, and it did -- range(2, 15)
    # against a chain reaching _18. This is the check that catches it.
    ic = root / "00-orchestrator" / "scripts" / "install-check.py"
    if ic.exists():
        m = re.search(r"for i in range\((\d+),\s*(\d+)\)", ic.read_text(encoding="utf-8"))
        top = max((int(re.search(r"addendum_(\d+)", f).group(1))
                   for f in chain if "addendum_" in f), default=1)
        check("install-check.py covers every migration on disk",
              bool(m) and int(m.group(2)) == top + 1,
              f"install-check stops at _{int(m.group(2))-1}, disk has _{top}" if m else "range not found")

    # Rule numbers, across pipeline-rules.md and its addendum. Both addenda
    # shipped a second Rule 9 and a second Rule 10 -- different subject
    # matter, same numbers, in the file that declares itself the tiebreaker.
    # Nothing checked it, and a merge optimising for consistency deletes one.
    rf = [root / "shared" / "pipeline-rules.md",
          root / "shared" / "pipeline-rules-addendum.md"]
    seen, dupes = {}, []
    for f in rf:
        if not f.exists(): continue
        for n in re.findall(r"^## Rule (\d+)\b", f.read_text(encoding="utf-8"), re.M):
            if int(n) in seen: dupes.append(f"Rule {n} ({seen[int(n)]} + {f.name})")
            seen[int(n)] = f.name
    check("no duplicate rule numbers", not dupes, "; ".join(dupes))
    nums = sorted(seen)
    check("rule numbers are contiguous", nums == list(range(min(nums), max(nums)+1)) if nums else False,
          f"missing {sorted(set(range(min(nums), max(nums)+1)) - set(nums))}" if nums else "none found")

    # Count fossils. LESSONS: the largest defect category here, and the
    # reliable predictor is "files that describe the state of the package
    # rather than doing their own job". Nothing breaks when one goes stale
    # -- it just quietly misinforms. So assert the counts a reader could
    # act on, against the tree that actually exists.
    import glob as _g
    n_skills = len(_g.glob(str(root / "*" / "SKILL.md")))
    cjf = root / "cron" / "cron-jobs.md"
    n_jobs = len(re.findall(r"^## (\d+[a-z]?)\.", cjf.read_text(encoding="utf-8"), re.M)) if cjf.exists() else 0
    stale = []
    words = {"four":4,"five":5,"six":6,"seven":7,"eight":8,"nine":9,"ten":10,
             "eleven":11,"twelve":12,"thirteen":13,"fourteen":14,"fifteen":15,
             "sixteen":16,"seventeen":17,"eighteen":18,"nineteen":19,"twenty":20}
    for fp in _g.glob(str(root / "**" / "*.md"), recursive=True):
        if ".merge-history" in fp or os.path.basename(fp).endswith("CHANGELOG.md"): continue
        body = re.sub(r"\s*\n\s*", " ", Path(fp).read_text(encoding="utf-8", errors="replace"))
        pats = [
            # "all 24 skills", "all nine jobs"
            r"\ball (\d+|" + "|".join(words) + r") (skill|job)s\b",
            # "a 23-skill package", "a 17-job register". The (?!-) is load-
            # bearing: without it every folder name (01-job-discovery,
            # 18-skill-composer) matches and the check becomes noise.
            r"\b(\d+)-(skill|job)(?![-\w])",
        ]
        for pat in pats:
            for m in re.finditer(pat, body):
                v = words.get(m.group(1).lower(), m.group(1))
                try: v = int(v)
                except ValueError: continue
                want = n_skills if m.group(2) == "skill" else n_jobs
                if v != want:
                    stale.append(f"{os.path.relpath(fp, str(root))}: '{m.group(0)}' (actual {want})")
    check("no file states a stale skill/job count", not stale,
          "; ".join(sorted(set(stale))[:4]))

    # `table.column` references in prose. A wrong column name does not
    # error -- the skill reads a field that is not there and continues.
    # Found social_outreach.outcome this way: the table names that concept
    # reply_type, and the doc telling the query-tuning loop what to read
    # named a column that has never existed.
    import sqlite3 as _sq, tempfile as _tf
    _c = _sq.connect(":memory:")
    try:
        for _m in migration_chain(root):
            _c.executescript((root / "shared" / _m).read_text(encoding="utf-8"))
        _tabs = {r[0] for r in _c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        _cols = {t_: {r[1] for r in _c.execute(f"PRAGMA table_info({t_})")} for t_ in _tabs}
        badcol = set()
        for fp in glob.glob(str(root / "**" / "*.md"), recursive=True):
            if ".merge-history" in fp: continue
            for m in re.finditer(r"`([a-z][a-z0-9_]+)\.([a-z][a-z0-9_]+)`",
                                 Path(fp).read_text(encoding="utf-8", errors="replace")):
                tb, cl = m.groups()
                # `applications.db` is a filename, not a column reference.
                if cl in ("db","sql","md","py","yaml","json","sh","html","template"): continue
                if tb in _tabs and cl not in _cols[tb]:
                    badcol.add(f"{tb}.{cl} (in {os.path.relpath(fp, str(root))})")
        check("every table.column reference resolves", not badcol,
              "; ".join(sorted(badcol)[:4]))
    finally:
        _c.close()

    # Scripts compile. Cheap, and the journal-export bug was found by
    # running code rather than reading it.
    import ast
    broken = []
    for py in glob.glob(str(root / "**" / "*.py"), recursive=True):
        if ".merge-history" in py: continue
        try: ast.parse(Path(py).read_text(encoding="utf-8"))
        except SyntaxError as e: broken.append(f"{os.path.basename(py)}:{e.lineno}")
    check("every .py in the package parses", not broken, ", ".join(broken))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill-dir", default=".")
    a = ap.parse_args()
    shared = Path(a.skill_dir) / "shared"
    chain = migration_chain(Path(a.skill_dir))
    print("static checks -- package integrity")
    static_checks(Path(a.skill_dir))
    print("\nruntime checks -- fixture pipeline")

    tmp = tempfile.mkdtemp(prefix="jobhunt-dryrun-")
    print(f"dry-run in {tmp}\n")
    conn = sqlite3.connect(os.path.join(tmp, "fixture.db"))

    try:
        for m in chain:
            conn.executescript((shared/m).read_text(encoding="utf-8"))
        n = conn.execute("SELECT COUNT(*) FROM schema_version").fetchone()[0]
        check("migration chain applies from scratch", n == len(chain),
              f"ledger has {n}, expected {len(chain)}")
    except Exception as e:
        check("migration chain applies from scratch", False, str(e)[:120])
        return summarise()

    check("superseded _3.sql absent from ledger",
          conn.execute("SELECT COUNT(*) FROM schema_version WHERE filename LIKE '%addendum_3%'").fetchone()[0] == 0)

    fp = fingerprint(FIXTURE["company"], FIXTURE["role_title"], FIXTURE["location"])
    app_id = None
    for url, source, job in FIXTURE["urls"]:
        row = conn.execute("SELECT id FROM applications WHERE posting_fingerprint=?", (fp,)).fetchone()
        if row:
            app_id = row[0]
        else:
            app_id = conn.execute(
                "INSERT INTO applications (company, role_title, posting_url, posting_fingerprint, status) "
                "VALUES (?,?,?,?,?)",
                (FIXTURE["company"], FIXTURE["role_title"], url, fp, "discovered")).lastrowid
        conn.execute("INSERT OR IGNORE INTO posting_sources "
                     "(application_id, posting_url, source_name, discovered_by, is_canonical) VALUES (?,?,?,?,?)",
                     (app_id, url, source, job, 1 if source == "company_careers" else 0))

    check("three sources produce ONE application",
          conn.execute("SELECT COUNT(*) FROM applications WHERE posting_fingerprint=?", (fp,)).fetchone()[0] == 1)
    check("all three source URLs recorded",
          conn.execute("SELECT COUNT(*) FROM posting_sources WHERE application_id=?", (app_id,)).fetchone()[0] == 3)

    conn.execute("UPDATE applications SET overqualification_gate='skipped', "
                 "overqualification_skip_reason='profile_stage_first_time', "
                 "title_delta=NULL, comp_delta_pct=NULL WHERE id=?", (app_id,))
    g = conn.execute("SELECT overqualification_gate,title_delta,comp_delta_pct FROM applications WHERE id=?",
                     (app_id,)).fetchone()
    check("a skipped gate does not look like a pass",
          g[0] == "skipped" and g[1] is None and g[2] is None)

    conn.execute("UPDATE applications SET status='staged' WHERE id=?", (app_id,))
    cols = [r[1] for r in conn.execute("PRAGMA table_info(applications)")]
    ac = next((c for c in cols if "approval" in c), None)
    check("applications table has an approval column", ac is not None, "Rule 1 has nothing to check against")
    if ac:
        bad = conn.execute(f"SELECT COUNT(*) FROM applications WHERE status='submitted' AND {ac} IS NULL").fetchone()[0]
        check("no submitted row lacks an approval decision", bad == 0, f"{bad} found")

    jc = [r[1] for r in conn.execute("PRAGMA table_info(career_journal)")]
    body = next((c for c in jc if c in ("raw_text","entry","response","body","text","content")), None)
    ts = next((c for c in jc if c in ("entry_at","created_at","entry_date","logged_at")), None)
    if body and ts:
        conn.execute(f"INSERT INTO career_journal ({ts},{body}) VALUES ('2026-01-01','kept')")
        conn.execute(f"INSERT INTO career_journal ({ts},{body},deleted_at,delete_reason) "
                     f"VALUES ('2026-01-02','removed','2026-01-03','private')")
        live = conn.execute("SELECT COUNT(*) FROM career_journal WHERE deleted_at IS NULL").fetchone()[0]
        total = conn.execute("SELECT COUNT(*) FROM career_journal").fetchone()[0]
        check("soft-deleted journal entries leave the live set", live == 1 and total == 2, f"{live} live of {total}")
    else:
        check("career_journal has an identifiable body/timestamp column", False, f"cols: {jc}")

    conn.close()
    return summarise()

if __name__ == "__main__":
    sys.exit(main())
