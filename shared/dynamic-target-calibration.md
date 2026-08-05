# Dynamic Target Calibration — reasoning, scoring definitions, worked examples

This is the doc `shared/dynamic-target-calibration.yaml.template` points
back to. It exists because the *why* behind the config is long enough
that cramming it into YAML comments would bury the config itself — same
split `shared/pipeline-rules.md` vs. each skill's own file already uses.

**Wiring status, answered directly**: as first delivered, this file and
its `.yaml` template were well-specified but not actually plugged into
anything — genuinely just a config schema and a reasoning doc, describing
who *should* consume it without any of those skills actually doing so.
Fixed now: `03-resume-match/ADDENDUM.md` is where the real gating logic
lives (the match-score and overqualification gates below, actually
applied), `07-context-architect/ADDENDUM.md` wires `employment_status`
into Phase 1.5's net-widening, and `01-job-discovery/ADDENDUM.md`
explains why that skill needs no direct wiring at all — it inherits the
effect through `target-profile.yaml` instead. This file stays the
reasoning/definitions reference; the three addenda above are where it
actually touches running behavior.

## Why `match_score` isn't a policy lever

Kene's original framing was thresholds that "keep rising" as the profile
improves — the intuition is right, but the mechanism is cleaner modeled
as two separate things than as one number that drifts:

1. **The score is always computed fresh, the same way**, by
   `03-resume-match`, comparing whatever the *current* profile is against
   a given JD. Nothing artificially inflates it. It rises on its own,
   for free, the moment the profile genuinely gets stronger — because
   scoring the same JD against a better profile produces a better score.
   No calibration logic required for this part; it falls out of how
   `03-resume-match` already works.
2. **The threshold is a policy stance**, not a measurement. "70% and up"
   is Kene (or, in `auto`/`hybrid` mode, the schedule below) deciding
   where the bar sits — a genuinely separate decision from how any one
   job happens to score against him today.

Keeping these separate avoids a real design smell: if "the threshold
rises with the profile" and "the score rises with the profile" were the
same mechanism, you'd get a system where getting better at your job
never actually opens up more roles, because the bar chases the score
upward in lockstep. Separating them means profile growth does what it
should — surface previously-out-of-reach roles as newly in-reach — while
the threshold stays a lever Kene (or the schedule) controls independently.

## Worked example, using Kene's own numbers

A posting scores 60% today, `title_delta: +1` (mildly overqualified —
see below), sitting in the stretch band (50-70) under `balanced`
overqualification tolerance. Six months of documented growth later —
logged through `16-career-pulse`, confirmed into memory by
`07-context-architect` — `03-resume-match` re-scores the *same JD*
against the *updated* profile and comes back at 73%, because two of the
three skills the posting wanted are now genuinely there. That's not the
threshold moving to let a weaker match through — it's a stronger match
clearing the same, unmoved 70% bar.

Separately, if `calibration_mode` is `auto`/`hybrid` and
`employment_status` has been `unemployed` for 16+ weeks over that same
stretch, the stretch floor may *independently* have dropped from 50 to
40 per the `auto_relax_schedule`. Both things can be true at once and
they're easy to conflate if the model doesn't keep them apart — which is
exactly why they're two different fields in the config, not one.

## Overqualification score

Nothing like this exists yet anywhere in the current pipeline (checked —
`03-resume-match` produces a fit score, not an overqualification read).
Proposed here as two independent axes, deliberately not blended into one
opaque number, so an approval message can say *which* kind of
overqualified a role is instead of just flagging it:

**`title_delta`** = Kene's current O*NET job_zone (already computed by
`07-context-architect` as part of building his profile embedding for
`title-taxonomy.md`'s Phase 1.5) minus the posting's job_zone (from the
taxonomy record if the title's in it, or `02-jd-parser`'s own seniority
read otherwise).
- ≤0 = not overqualified by title
- +1 = mildly overqualified
- +2 or more = significantly overqualified

**`comp_delta`** = Kene's `salary_floor` (or last confirmed comp, if
higher) minus the posting's disclosed/estimated salary, as a percentage.
Tracked separately from `title_delta` because the two genuinely diverge:
a loosely-titled role can pay fine despite looking senior on paper, and a
correctly-titled role can still pay well under floor — a real problem
`title_delta` alone would miss entirely.

**`overqualification_tolerance` gates on both axes independently**, not
a merged score:

| Tolerance | Stages normally if... | Flagged `[OVERQUALIFIED]` if... | Dropped if beyond... |
|---|---|---|---|
| `strict` | `title_delta ≤0` AND `comp_delta ≤0` | — (strict doesn't stage-with-flag; it either passes clean or doesn't stage) | anything past the clean case |
| `balanced` | as above | `title_delta` up to +1 OR `comp_delta` up to 15% under floor | beyond that |
| `relaxed` | as above | `title_delta` up to +2 AND/OR `comp_delta` up to 30% under floor | beyond that — relaxed widens the gate, it doesn't remove it |

## Answering the specific questions directly

**"Is there any system for scoring overqualified jobs?"** No, not
currently — the above is a new proposal, not a description of something
already built.

**"How does the scoring/mapping system for target job variants actually
work?"** It already exists, just not framed as "scoring" — it's
`07-context-architect` Phase 1.5, documented in full in
`07-context-architect/references/title-taxonomy.md`: an O*NET-anchored
(plus ESCO, plus live market-signal crawl) database of tens of thousands
of real title strings, each with a `job_zone` seniority band, queried by
embedding similarity against Kene's own profile (STAR bank +
domain-knowledge + resume). Every suggestion is confirm-before-write
(Rule 5) and tagged with the specific evidence that produced it. This
file's job isn't to replace that system — it's to (a) give it a
seniority-delta number (`title_delta`, above) to feed overqualification
scoring, and (b) make sure it actually *re-runs* when a career event
happens (`16-career-pulse`'s cascade trigger), not just on its existing
monthly/quarterly refresh cadence.

**"How do we track when a user is out of a job?"** Never by silent
inference — see `16-career-pulse/SKILL.md`'s "Tracking employment
status" section. Soft signals (an accepted-offer outcome, something said
in passing, a long quiet stretch) only ever justify *asking*, and the
answer is written only once Kene confirms it, same as every other memory
fact.

**"Manual or automatic calibration?"** Both, as `calibration_mode` —
`manual` and `auto` are the two ends Kene described, `hybrid` is the
recommended default and isn't a compromise so much as reapplying a
pattern this pipeline already trusts: `11-analytics-and-learning`
already proposes-and-stages skill edits for Kene's approval rather than
silently rewriting other skills' behavior (`skill_self_edits`). Threshold
recalibration is the same kind of self-tuning claim about "what's
working," so it gets the same treatment rather than a new, less-audited
one.

## On the specific relax schedule in the template

The numbers in `auto_relax_schedule` (8/16/26/78 weeks) are a
reasonable starting curve, not a researched constant — tune them freely.
The one design choice worth keeping regardless of the exact numbers:
**every step only ever loosens the gate, never the evidence bar** —
`fidelity_mode` and `09-risk-tactics-gate` are untouched by any of this.
A longer search should widen *which* roles get considered, not weaken
*how honest* the application to any of them is. The 78-week tier and the
`profile_stage: first_time` starting-value preset are both explained in
full, alongside the two other named audiences they were built for, in
`onboarding/references/starting-out-track.md` — not repeated here.
