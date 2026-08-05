# Job-Hunting Pipeline — Hard Rules

These rules sit above every skill in `job-hunting/`. No skill, cron job, or
self-improvement update may override them. If a skill's instructions ever
conflict with this file, this file wins.

## Rule 0 — This package installs whole, or it does not work

Every skill in this package declares `shared/pipeline-rules.md` as
mandatory reading, and `shared/` deliberately sits outside every skill
directory so that one copy of the rules governs all of them rather than
23 copies drifting apart.

The cost of that choice: **`shared/` is not part of any skill's install
unit.** `hermes skills install job-hunting-discovery` brings the skill
and none of the rules it declares it must follow. The same applies to
`shared/applications.db`, `shared/target-profile.yaml`, and every
template the pipeline reads.

So: install the whole `job-hunting/` folder, or nothing here holds. A
partial install does not fail loudly — it produces a skill that reads
convincingly and has no rules file, no database, and no profile behind
it. That is a worse failure than a crash, which is why this is Rule 0
rather than a note in the README.

`00-orchestrator`'s install self-check
(`00-orchestrator/scripts/install-check.py`)
verifies this on demand and at first run of any session. If it reports a
missing `shared/` file, stop and fix the install before running anything
else in the pipeline.

## Rule 1 — Nothing is submitted without a human click

Every skill in this pipeline may search, parse, score, draft, rewrite,
fill in a web form, and stage output. **None of them may press submit,
send an email, or send a message to a recruiter.** The only skill allowed
to move an application from "staged" to "sent" is `10-approval-and-submit`,
and it may only do so after receiving an explicit approval reply from
Kene's paired Telegram account for that specific application.

This is enforced two ways, not one:
- **Procedurally**: every other skill's output ends in a "STAGED — awaiting
  approval" state, never a "SENT" state.
- **Technically**: the browser/form-fill tool calls used to prepare an
  application run, but the final submit action is wrapped in Hermes's
  dangerous-command approval gate (see `security/security-setup.md`) so
  that even if a skill's logic had a bug, the platform itself stops the
  click.

## Rule 2 — No claim goes out without evidence, by default

Any tactic that changes what the resume or cover letter *says happened*
(exact-phrase mirroring, CV title matching, skills added from "transferable
context") must run through `09-risk-tactics-gate` first and must cite the
specific line in Kene's base resume, portfolio, or STAR story bank that
supports it. If no evidence exists, the tactic is not applied — the gap is
flagged for the human instead of papered over.

**This rule's strictness is one explicit, confirmed setting — `fidelity_mode`
in `shared/target-profile.yaml` — not a silent per-skill judgment call.**
`09-risk-tactics-gate` reads that setting and branches its fail-handling
accordingly (`strict` / `balanced` / `embellish` — see that skill's own
"Fidelity mode" section for exactly what each does). `strict` is the
default, is what every existing description in this file assumes unless
stated otherwise, and is what a fresh install ships with until Kene
explicitly confirms a different value through `07-context-architect`
Phase 0.5 — the same confirm-before-write discipline Rule 5 already
requires for every other target-profile fact. No skill may set or change
`fidelity_mode` on its own; it changes exactly like any other target-profile
fact does.

## Rule 3 — Rate limits apply to staging, not sending

Daily volume settings (see `README.md`) cap how many application packages
`01-job-discovery` through `09-risk-tactics-gate` are allowed to *prepare*
per day. They are meaningless as a cap on sending, because nothing sends
itself. This is deliberate — see the note in `README.md` on why this
system is not designed to be resold as a submission-volume product.

## Rule 4 — Every outcome gets logged, good or bad

`11-analytics-and-learning` logs every staged application, every approval/
reject decision, and every downstream outcome Kene reports (response,
rejection, interview, offer). No skill may skip logging to save time or
because the outcome was a rejection. The self-improvement loop is only as
honest as this data.

## Rule 5 — Memory holds facts, not fabrications

`07-context-architect` is the only skill allowed to write new facts into
`MEMORY.md` / `USER.md` / the STAR story bank, and only after Kene
confirms them in the interview loop. Other skills may *read* memory but
never invent and persist a "fact" about Kene's career on their own.

**This is a hard boundary, not a soft default** — `09-risk-tactics-gate`
does not get an exception for flagging gaps. Its `Fail handling` writes go
to the `open_gaps` table in `shared/applications_db_schema.sql`, not to
`MEMORY.md`, specifically so this rule never has to bend for an
unattended cron write. `07-context-architect` reads `open_gaps` at the
start of every run the same way it always read `MEMORY.md`'s "Open gaps"
section — the worklist moved, the discipline didn't. See
`09-risk-tactics-gate/SKILL.md`'s "Fail handling" section and
`07-context-architect/SKILL.md`'s "When to re-run" section for the
mechanics on each side.
