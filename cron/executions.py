#!/usr/bin/env python3
"""Cron execution ledger — record what ran, and answer what didn't.

Twenty-three scheduled jobs, and before this nothing read whether any of
them ran. See shared/applications_db_schema_addendum_20.sql for why that
is a specific hazard here rather than a general nicety: jobs 1 and 9
carry wake-gates that suppress the agent turn and FAIL OPEN, so a gate
erroring in the skip direction is indistinguishable from a quiet market.

Three subcommands:

  record   one row per tick. Called by the job itself, or by its
           wake-gate when it decides to skip.
  report   what has gone silent, what keeps skipping, what is failing.
           Job 5 (weekly self-improvement review) is the intended caller.
  seed     register expected cadence from cron/cron-jobs.md, so "has not
           run" is answerable rather than guessed.

Read-only except for `record` and `seed`. Never writes to memory, never
touches an application row — this is instrumentation, and Rule 5 owns
what may write facts about Kene.

Usage:
  python3 cron/executions.py record --job 1 --name "Job discovery scan" \
      --outcome skipped --detail "no source changed"
  python3 cron/executions.py report --db shared/applications.db
  python3 cron/executions.py seed  --db shared/applications.db
"""
import argparse
import datetime as _dt
import sqlite3
import sys
from pathlib import Path

OUTCOMES = ("ran", "skipped", "failed", "gate_error")

# Expected cadence per job. max_silence_hours is deliberately generous —
# roughly two missed ticks — because a false "this job is dead" is how a
# report like this gets ignored, and an ignored report is worse than none.
EXPECTATIONS = [
    ("1",  "Job discovery scan",                     12,  20),
    ("2",  "Open-web discovery sweep",               48,  10),
    ("3",  "Pipeline sweep",                         48,  10),
    ("4",  "Ghost-check / outcome nudge",            60,  10),
    ("5",  "Weekly self-improvement review",        360,   4),
    ("6",  "Monthly question-bank refresh",        1500,   3),
    ("7",  "Monthly title-taxonomy refresh",       1500,   3),
    ("8",  "Nightly Tier 1 backup",                  48,   3),
    ("8b", "Quarterly restore verification",       4400,   2),
    ("8c", "Weekly Tier 2 backup",                  360,   3),
    ("9",  "Interview-prep sweep",                   48,  20),
    ("10", "Social listening scan",                  48,  10),
    ("11", "Career-pulse journal check-in",         360,   6),
    ("12", "Explicit-channel profile monitor",      360,   6),
    ("13", "Cold prospecting cadence",              360,   6),
    ("14", "Career path plan re-evaluation",       1500,   3),
    ("15", "Enrichment tier-usage cycle reset",    1500,   3),
    ("16", "Bi-monthly configuration drift check", 1500,   3),
    ("17", "Nightly retrieval-index refresh",        48,   5),
    ("18", "Pause-expiry check",                     48,  10),
    ("19", "LinkedIn connection-flow maintenance",  360,   8),
    ("20", "X follow-state check",                  360,   8),
    ("21", "IG/FB engagement-window cleanup",       360,   8),
    ("22", "Weekly cron health check",              360,   4),
]


def _now():
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def _conn(db):
    p = Path(db)
    if not p.exists():
        sys.exit(f"no database at {p} — run install step 4 first")
    c = sqlite3.connect(str(p))
    c.row_factory = sqlite3.Row
    return c


def cmd_seed(a):
    c = _conn(a.db)
    c.executemany(
        "INSERT OR REPLACE INTO cron_job_expectations "
        "(job_label, job_name, max_silence_hours, skip_streak_warn) VALUES (?,?,?,?)",
        EXPECTATIONS)
    c.commit()
    print(f"seeded {len(EXPECTATIONS)} job expectations")


def cmd_record(a):
    if a.outcome not in OUTCOMES:
        sys.exit(f"outcome must be one of {OUTCOMES}")
    c = _conn(a.db)
    c.execute(
        "INSERT OR IGNORE INTO cron_executions "
        "(job_label, job_name, started_at, finished_at, outcome, detail) "
        "VALUES (?,?,?,?,?,?)",
        (a.job, a.name, a.started or _now(), _now(), a.outcome, a.detail))
    c.commit()
    print(f"recorded job {a.job}: {a.outcome}")


def cmd_report(a):
    c = _conn(a.db)
    exp = {r["job_label"]: r for r in c.execute("SELECT * FROM cron_job_expectations")}
    if not exp:
        sys.exit("no expectations registered — run `executions.py seed` first")

    now = _dt.datetime.now(_dt.timezone.utc)
    never, stale, failing, skipping = [], [], [], []

    for label, e in sorted(exp.items(), key=lambda kv: (len(kv[0]), kv[0])):
        rows = list(c.execute(
            "SELECT * FROM cron_executions WHERE job_label=? "
            "ORDER BY started_at DESC LIMIT 50", (label,)))
        if not rows:
            # Never registered is a DIFFERENT failure from ran-and-failed:
            # the fix is `hermes cron create`, not debugging the job.
            never.append(f"{label}. {e['job_name']}")
            continue
        last = _dt.datetime.fromisoformat(rows[0]["started_at"])
        hours = (now - last).total_seconds() / 3600
        if hours > e["max_silence_hours"]:
            stale.append(f"{label}. {e['job_name']} — last tick {hours:.0f}h ago "
                         f"(expected within {e['max_silence_hours']}h)")
        recent = rows[:10]
        fails = [r for r in recent if r["outcome"] in ("failed", "gate_error")]
        if fails:
            failing.append(f"{label}. {e['job_name']} — {len(fails)}/{len(recent)} recent "
                           f"ticks {fails[0]['outcome']}: {(fails[0]['detail'] or '')[:60]}")
        streak = 0
        for r in rows:
            if r["outcome"] != "skipped":
                break
            streak += 1
        if streak >= e["skip_streak_warn"]:
            # Not a failure. But a gate that has skipped this many times in a
            # row is either working perfectly or broken open, and those look
            # identical from outside — which is the whole reason for this table.
            skipping.append(f"{label}. {e['job_name']} — {streak} consecutive skips; "
                            f"verify the wake-gate is still discriminating")

    out = []
    for title, items in (("NEVER RAN (not registered?)", never),
                         ("SILENT PAST EXPECTED CADENCE", stale),
                         ("FAILING", failing),
                         ("SKIP STREAK — verify the gate", skipping)):
        if items:
            out.append(title)
            out += [f"  - {i}" for i in items]
    if not out:
        print(f"[SILENT] all {len(exp)} jobs within expected cadence, no failures")
        return 0
    print("\n".join(out))
    return 1


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--db", default="shared/applications.db")
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("record")
    r.add_argument("--job", required=True)
    r.add_argument("--name")
    r.add_argument("--outcome", required=True, choices=OUTCOMES)
    r.add_argument("--detail")
    r.add_argument("--started")
    r.set_defaults(fn=cmd_record)

    sub.add_parser("report").set_defaults(fn=cmd_report)
    sub.add_parser("seed").set_defaults(fn=cmd_seed)

    a = ap.parse_args()
    sys.exit(a.fn(a) or 0)


if __name__ == "__main__":
    main()
