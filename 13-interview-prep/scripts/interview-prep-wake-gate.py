#!/usr/bin/env python3
"""
job-hunting interview-prep wake-gate — a Hermes cron `script=` pre-run gate.

Purpose (see 13-interview-prep/SKILL.md's "Trigger conditions" and
cron/cron-jobs.md job #9): don't pay for an LLM agent turn on every tick
of the interview-prep sweep if there's nothing for it to actually build.

Unlike 01-job-discovery/scripts/discovery-wake-gate.py, this gate is pure
internal DB state — no network fetch, no external CLI, no source-type
coverage gaps. That makes it strictly more trustworthy than the discovery
gate: there's no "type of source I can't cheap-check" category here, so
when this script says skip, it's a real skip, not a best-effort guess.

Wakes when EITHER is true for any row in `applications`:
  1. interview_request_at IS NOT NULL AND last_interview_prep_at IS NULL
     — a first interview request that's never had a brief built.
  2. interview_request_at IS NOT NULL AND EXISTS a `email_insights` row
     for that application with category='interview_detail' AND
     extracted_at > last_interview_prep_at — a LATER round's details
     arrived since the last brief was built (multi-round interviews:
     phone screen, then onsite, each with their own interviewer/format
     details landing in separate emails over time), so the brief is
     stale and should be rebuilt, not treated as already handled.

FAILS OPEN on any error (missing DB, query failure) — same direction as
the discovery gate, same reason: a missed cheap-check just delays a
rebuild by one tick, which costs nothing dramatic; silently never
building a prep brief for a real interview would be a much worse
failure to have hidden behind a script bug.
"""
import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path.home() / ".hermes" / "skills" / "job-hunting" / "shared" / "applications.db"

QUERY = """
SELECT a.id, a.company, a.role_title
FROM applications a
WHERE a.interview_request_at IS NOT NULL
  AND (
        a.last_interview_prep_at IS NULL
        OR EXISTS (
            SELECT 1 FROM email_insights e
            WHERE e.application_id = a.id
              AND e.category = 'interview_detail'
              AND e.extracted_at > a.last_interview_prep_at
        )
      )
"""


def wake(reason: str) -> None:
    print(json.dumps({"wakeAgent": True, "reason": reason}))
    sys.exit(0)


def skip(reason: str) -> None:
    print(json.dumps({"wakeAgent": False, "reason": reason}))
    sys.exit(0)


def main() -> None:
    if not DB_PATH.exists():
        wake(f"applications.db not found at {DB_PATH} — waking so the agent can report the setup gap")
        return

    try:
        conn = sqlite3.connect(str(DB_PATH))
        rows = conn.execute(QUERY).fetchall()
        conn.close()
    except Exception as exc:
        wake(f"DB query failed ({exc}) — waking rather than guessing")
        return

    if not rows:
        skip("no application has an unprocessed or freshly-updated interview signal")
        return

    labels = [f"{company} / {role}" for (_id, company, role) in rows]
    wake(f"{len(rows)} application(s) need a prep brief built or refreshed: " + "; ".join(labels))


if __name__ == "__main__":
    main()
