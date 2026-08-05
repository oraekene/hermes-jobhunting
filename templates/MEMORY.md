<!--
Copy into ~/.hermes/memories/MEMORY.md (or merge). ~800-token budget —
durable facts and standing instructions the pipeline should always have
in context, not the full narrative (that lives in star-story-bank.md,
domain-knowledge.md, career-timeline.md as skill references instead).
-->

# Durable Job-Search Memory

## Standing instructions
- Never apply to: [company exclusion list, if any]
- Daily staging cap: [see README.md — current tier/value]
- Title matching: [e.g. "only apply title-matching to roles at or below
  current scope — never upward beyond documented experience"]
- Fidelity mode: [strict | balanced | embellish — see
  shared/target-profile.yaml's `fidelity_mode` field, set via
  07-context-architect Phase 0.5. Shown here too since it's a standing
  decision every application-writing skill should have in context, same
  reason the daily cap is listed here.]

## Current strategy notes (updated by 11-analytics-and-learning)
- [Example: "Exact-phrase mirroring shows a real response-rate lift as of
  <date> — keep enabled by default."]
- [Example: "Applications sent >48h after posting underperform — 01-job-
  discovery's priority window tightened to 12h as of <date>."]

<!--
Gaps 09-risk-tactics-gate flags for missing evidence do NOT live here.
They go in the `open_gaps` table (shared/applications_db_schema.sql)
instead — that table has no character cap and can be written unattended
during a cron run without risking Rule 5 or MEMORY.md's ~2,200-char
limit. 07-context-architect reads `open_gaps WHERE resolved = 0` at the
start of every run the same way it used to read a section here. See
that skill's "When to re-run" section and 09-risk-tactics-gate's "Fail
handling" section for the mechanics on each side. If you're looking at
an older copy of this template that still has an "Open gaps" heading
below this note, that's the pre-fix version — delete it and query the DB
instead.
-->

