---
name: job-hunting-risk-tactics-gate
description: "Risk-check application drafts before submission"
metadata:
  hermes:
    tags: [job-hunting, risk-tactics-gate]
    category: job-hunting
    related_skills:
      - job-hunting-resume-customizer
      - job-hunting-cover-letter
      - job-hunting-application-qa
      - job-hunting-approval-submit
---

# Risk Tactics Gate

## When this skill applies

Use this skill immediately after 05-resume-customizer, 06-cover-letter, and 08-application-qa produce their drafts, and before 10-approval-and-submit shows anything to Kene. It checks every claim-changing tactic (exact-phrase mirroring, CV title matching, added skills from 'transferable context') against evidence in memory, and flags anything unsupported. Do NOT skip this step to save a pipeline run — it is the mechanism that makes Rule 2 in shared/pipeline-rules.md real rather than aspirational.

This is the skill that exists specifically because two of the Splendor
thread's tactics are powerful *and* easy to misuse if nothing checks
them: copying a job posting's exact phrasing into the resume, and
adjusting the displayed job title to match the posting. The thread's own
text gates both with "only if it's genuinely accurate" — this skill is
that gate, implemented as an actual check instead of a good intention.

## What it checks

For every tactic application in the drafts it receives — from
`05-resume-customizer`, `06-cover-letter`, and `08-application-qa` alike
— verify:

### 1. Exact-phrase mirroring
- Is there a specific line in the base resume, portfolio, or STAR bank
  (`07-context-architect`'s files) that supports this claim?
- When `target-profile.yaml`'s `profile_stage` is `first_time`, three
  further sources count as legitimate homes for that evidence: school
  records and coursework, documented extracurricular or volunteer work,
  and `memory/interests-profile.md` entries — the same widened Phase 1
  list `07-context-architect` uses for this stage. **The bar itself does
  not move.** "I organized the fundraiser" still needs the number that
  makes it real, exactly as an unquantified resume bullet would fail
  this gate at any `profile_stage`. What widens is the set of sources
  for the same standard of evidence, because a first-time applicant's
  available evidence differs in kind, not in rigour. See
  `onboarding/references/starting-out-track.md`.

  **One qualification on the third source.** `interests-profile.md`
  deliberately carries no evidence bar — entries are admissible on Kene's
  say-so, by design. That is fine as a source and it means the entry
  needs the one bar such a file *can* have: a time bar. **An entry past
  its 12-month reconfirmation interval does not pass this gate until it
  is reconfirmed** (`capability:interests_profile`, "Aging"). Not because a
  stale interest is likely false — it usually isn't — but because this
  is the point where it stops being an internal note and gets said to an
  employer as something Kene currently does. "He mentioned it, turned
  out he stopped two years ago" is a credibility cost paid in the room,
  and it is cheap to avoid.
- **Pass** → leave the mirrored phrase in, note the supporting evidence
  in the change-log.
- **Fail** → see "Fail handling" below before doing anything else.

### 2. CV title matching
- Does Kene's actual documented scope of responsibility in the relevant
  role genuinely match the target title, not just the seniority level?
  ("Analytics Lead, Operations" needs evidence of operations-specific
  analytics leadership, not just "was a lead somewhere.")
- **Pass** → apply the title, but always keep `title_original` and
  `title_displayed` both visible in the change-log — this is flagged for
  Kene's eyes even when it passes, because it's the single tactic most
  likely to raise a question in an interview if it's ever off by more
  than it should be. **Mark it `[BORDERLINE PASS]` instead of a plain
  `[PASS]`** when the equivalence rests on inference or interpretation
  rather than a direct, explicit statement already in memory (memory
  documents responsibilities that *imply* the title's scope but never
  states the equivalent title outright) — a plain `[PASS]` is for the
  case where memory already says something close to the target title in
  so many words. See `references/moa-cross-check.md` for what happens
  with a `[BORDERLINE PASS]` at approval time — short version: Kene gets
  a ready-to-paste prompt for a second model's opinion, entirely his
  call whether to use it.
  When marking `[BORDERLINE PASS]`, record the **role envelope** in the
  change-log entry alongside the STAR snippet: the actual title held,
  tenure, reporting line, direct reports, and the sibling bullets from
  that same role. `10-approval-and-submit` builds the paste-ready prompt
  from that envelope, not from the snippet alone — the reason is in
  `references/moa-cross-check.md`, and it is the difference between a
  second opinion that can see scope and one that can only see tone.
  Nothing from adjacent roles or the wider career arc goes in.
- **Fail** → keep the original title. Never apply "close enough." See
  "Fail handling" below.

### 3. Skills added via "transferable context"
- Same evidence check as #1, applied to `05-resume-customizer` Phase 1
  and `08-application-qa` step 4.

### 4. Values-alignment claims
- Does the specific value-to-story mapping actually reflect something
  Kene did, or is it a plausible-sounding sentence with no real anchor?
  Fail anything that isn't traceable to a specific memory entry.

## Fidelity mode (read before evaluating anything)

Read `shared/target-profile.yaml`'s `fidelity_mode` before running any
check above — it decides what a FAIL actually *does*, not whether checks
run. Every check in "What it checks" always runs and always gets logged,
in every mode; mode only changes the consequence of a FAIL. `strict` is
the default for any pipeline that hasn't run `07-context-architect`
Phase 0.5 yet — never assume `balanced` or `embellish` in the absence of
an explicit, confirmed setting.

- **`strict`** (default) — the fail-handling behavior described below,
  unchanged: strip or weaken the claim, log the gap. This is the only
  mode this file described before `fidelity_mode` existed, and is what
  Rule 2 assumes unless Kene has explicitly confirmed otherwise.
- **`balanced`** — the tactic is still applied even without evidence, but
  every such application gets an explicit `[UNVERIFIED]` line in the
  change-log (see "Output" below), and `10-approval-and-submit` must
  surface those lines to Kene before he can approve — this is an
  additional, non-skippable display requirement in that skill for
  exactly this case, not optional formatting. Kene is deciding per
  application, with the gap visible, instead of the gate deciding for
  him.
- **`embellish`** — the tactic is applied without evidence and without a
  per-application flag. **Still log every application in this mode to the
  change-log exactly as thoroughly as any other mode** — the only thing
  `embellish` changes is that the check no longer blocks or flags the
  output; it does not exempt this skill from recording what was actually
  claimed. That record is the only thing that would let Kene reconstruct,
  months later, what he told a specific employer if an interviewer asks
  about it.

Never let a downstream skill (`05-resume-customizer`, `06-cover-letter`,
`08-application-qa`, `10-approval-and-submit`) read `fidelity_mode`
directly and change its own behavior based on it — this gate is the only
place that setting has an effect, so there is exactly one place in the
pipeline to look if you ever need to know why a claim went out the way it
did.

## Fail handling

A FAIL is never just a passive downgrade waiting to be noticed at
approval time — it gets surfaced the moment it's discovered. The first
part of this is identical in every fidelity mode; the modes diverge only
at the very last step — what happens to the claim itself.

**Every mode, first:**

- **Interactive session (Kene present in the chat right now):** ask him
  directly, in that same turn, whether the missing evidence actually
  exists but simply hasn't been captured in memory yet — a specific
  question about the specific claim, not a generic "any evidence for
  this?" If he supplies it on the spot, hand it to `07-context-architect`
  to confirm-and-write (Rule 5 still applies — this skill never writes
  memory itself), then re-check the tactic against the newly-written
  fact before finalizing.
- **Unattended run (cron pipeline sweep, `job #3` in `cron/cron-jobs.md`):**
  do not block the run waiting for an answer that can't arrive mid-cron-
  session.
- **Either way**, immediately insert a row into the `open_gaps` table
  (`shared/applications_db_schema.sql`) — `application_id`, `company`,
  `role_title`, `claim_text`, `missing_evidence`, `fidelity_mode_at_flag`,
  `flagged_at`. This is what makes the gap visible to Kene the next time
  context-architect runs, rather than waiting silently until this
  specific application reaches approval. This happens in every fidelity
  mode; the mode changes what the *application* does with the claim, not
  whether the gap gets tracked as a gap. Also still record the outcome in
  the per-application change-log (see "Output" below) — that's the final,
  application-specific record `10-approval-and-submit` shows Kene, on top
  of, not instead of, the earlier surfacing.

  **Never write this to `~/.hermes/memories/MEMORY.md` directly** —
  earlier drafts of this pipeline did, and that both violated Rule 5
  (`shared/pipeline-rules.md`: only `07-context-architect` writes memory,
  and only after Kene confirms a fact) and risked hitting `MEMORY.md`'s
  hard ~2,200-character cap during an unattended run, with no one present
  to consolidate when the write failed. The `open_gaps` table has no such
  ceiling, and it's the pattern this schema already uses for every other
  running list in this pipeline. `07-context-architect` is the only skill
  that reads `open_gaps` back into a form Kene sees in chat.

**Then, where the modes actually diverge — what happens to the claim
itself:**

- **`strict`**: strip the phrase back to nothing, or substitute a weaker
  true claim if one exists, for *this* application only. The unverified
  version never reaches the resume, cover letter, or answer text at all.
- **`balanced`**: the tactic **may** still be applied as originally
  drafted — but only if it's plausible given what Kene has actually
  described about his background (this is not license to invent
  something with no relationship to his real experience; it's for the
  genuine gray area, like a skill he's clearly used informally but never
  logged a STAR story for). Mark it `[UNVERIFIED]` rather than `[PASS]`
  in the change-log, with the same specificity a PASS entry gets (what
  claim, what's actually missing) — never blend it in indistinguishably
  — and `10-approval-and-submit` must surface that line before Kene can
  approve.
- **`embellish`**: the same as `balanced` — applied if plausible, never
  invented from nothing — except the `[UNVERIFIED]` line is recorded in
  the change-log for the audit trail only; it doesn't interrupt or gate
  the approval flow in `10-approval-and-submit` the way `balanced` does.

Never apply a failed tactic *silently*, in any mode — "probably fine"
without surfacing it is not what `balanced` or `embellish` mode means.
The difference between the modes is who absorbs the judgment call:
`strict` makes the pipeline absorb it (nothing unverified ever goes out);
`balanced` and `embellish` hand the judgment call to Kene — explicitly,
per-application, in `balanced`; implicitly, by his having opted into the
mode itself, in `embellish` — but neither mode means the pipeline itself
decides an unverified claim is "probably fine" and lets it through
without a record of what was actually claimed. This is the one place in
the pipeline where "probably fine" isn't good enough, because it's the
one place where being wrong costs Kene his credibility with a specific
employer, not just a rejected application.

## Output

Once every tactic has been checked (whatever the mix of PASS/BORDERLINE
PASS/FAIL/UNVERIFIED — this is about the check having *run*, not about
everything passing), write `status='staged'` to this application's row
in `shared/applications_db_schema.sql`. This is the formal checkpoint
between "built" and "actually pinged to Kene" — `10-approval-and-
submit` is the only skill that moves a posting from `staged` to
`awaiting_approval`, and only once the Telegram message has actually
gone out. This distinction matters most for the optional parallel
pipeline sweep (`00-orchestrator/references/parallel-pipeline-sweep.md`),
where this skill may be running inside a delegated subagent that has no
way to message Kene itself — but it's the correct checkpoint in the
default serial flow too, not something gated behind parallel mode being
on.

A change-log block appended to the application package:

```
RISK TACTICS APPLIED  (fidelity_mode: strict)
- [PASS] Exact phrase: "<phrase>" — evidence: <resume/story bank line>
- [BORDERLINE PASS] Title: "<original>" → "<displayed>" — evidence: <line>
  implies but doesn't state the equivalence — see references/moa-cross-
  check.md for a second-opinion prompt if you want one before approving
- [FAIL] Skill "X" claimed by JD, no evidence found — left as genuine gap
  (logged to open_gaps, <date>)
```

```
RISK TACTICS APPLIED  (fidelity_mode: balanced)
- [PASS] Exact phrase: "<phrase>" — evidence: <resume/story bank line>
- [PASS] Title: "<original>" → "<displayed>" — evidence: <line>
- [UNVERIFIED] Skill "X" claimed by JD, no evidence found — applied
  anyway per fidelity_mode: balanced (logged to open_gaps,
  <date>) — Kene, you're vouching for this one yourself
```

```
RISK TACTICS APPLIED  (fidelity_mode: embellish)
- [PASS] Exact phrase: "<phrase>" — evidence: <resume/story bank line>
- [PASS] Title: "<original>" → "<displayed>" — evidence: <line>
- [UNVERIFIED] Skill "X" claimed by JD, no evidence found — applied
  anyway per fidelity_mode: embellish (logged to open_gaps,
  <date>) — recorded for the audit trail, not gated at approval
```

`10-approval-and-submit` surfaces this block to Kene alongside the
resume/cover letter, always — the mode line at the top is not
decorative, it's so a `balanced`- or `embellish`-mode change-log is never
mistaken for a `strict`-mode one at a glance. Every PASS is a claim he's
implicitly vouching for by approving; every FAIL (`strict`) is an honest
gap, already surfaced once via the handling above, that he can address
before sending, or not; every UNVERIFIED (`balanced`/`embellish`) is a
claim he is *explicitly* vouching for, with the gap named plainly rather
than smoothed over — the label exists precisely so it never reads like a
PASS.

## Why this gate is not scored (S5)

`08-application-qa` now revises to a threshold instead of rejecting at
one. The obvious next move is to do the same here. **Don't.**

The distinction is what the two gates measure. Quality is a spectrum: an
answer can be a 6.5 and become an 8 with one focused revision, and
rejecting it outright wastes work. Honesty is not a spectrum. A claim is
either supported by something in the record or it isn't, and "mostly
supported" is the exact failure mode this gate exists to catch.

Scoring an honesty check invites two specific failures:

- **Threshold drift.** Any number can be argued down over time, especially
  by the agent that just wrote the claim. A binary rule cannot be
  negotiated with.
- **Aggregate laundering.** A composite score lets a strong Evidence
  reading offset a weak Fabrication reading. Those must never offset —
  one fabricated claim is disqualifying regardless of how good the rest
  of the document is.

So this gate stays binary on everything it currently gates: exact-phrase
mirroring, title equivalence, quantification, and evidence sourcing.

The one thing worth borrowing is the *loop*, not the score. A fail here
should return the specific failing claim to `05-resume-customizer` or
`06-cover-letter` for a targeted fix and re-gate, rather than dropping
the whole package. Same iteration cap and the same reasoning: three
failed attempts on one claim means the evidence isn't there, and the
honest outcome is to drop the claim and tell Kene — not to keep rewording
it until it slips past.

