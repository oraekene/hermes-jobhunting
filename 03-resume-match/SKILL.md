---
name: job-hunting-resume-match
description: "Score the base resume against a parsed job description"
metadata:
  hermes:
    tags: [job-hunting, resume-match]
    category: job-hunting
    related_skills:
      - job-hunting-jd-parser
      - job-hunting-keyword-analysis
      - job-hunting-resume-customizer
      - job-hunting-context-architect
---

# Resume & Job Match Analysis

## When this skill applies

Use this skill to score how well Kene's base resume matches a parsed job description's requirements, identify gaps, and recommend what to emphasize. Triggers: 'how well do I match this role', 'score this against my resume', or being handed a JD analysis by 02-jd-parser. Do NOT use this for ATS keyword scoring specifically (that's the separate, stricter 04-keyword-analysis) — this skill is a holistic human-style fit assessment, not a keyword count.

Origin: Kene's original "Chat 2," unchanged in substance. This stage is
deliberately the harshest one in the pipeline — it's the reality check
that keeps every later, more persuasive stage honest.

## Process

Given the JD analysis (from `02-jd-parser`) and Kene's base resume /
memory profile (from `07-context-architect`):

1. Score match 0–100% per requirement: direct skill match, transferable
   skill, or no match.
2. Identify gaps between qualifications and requirements plainly — don't
   soften this for encouragement's sake.
3. Suggest what to emphasize and what's genuinely missing.
4. Flag red flags: seniority mismatch, industry mismatch, missing
   licensure/certification the posting treats as mandatory, etc.
5. Calculate an overall match score.
6. Recommend specific resume modifications for `05-resume-customizer` to
   act on.

**Be realistically critical** — score the way an experienced interviewer
would, not the way a motivational coach would. A gap correctly flagged
here is a gap `09-risk-tactics-gate` doesn't have to catch later.

## Calibration gates — run after the score exists, before staging

`shared/dynamic-target-calibration.yaml` described what should consume
it from the config's own side; this is the consuming end. Both gates run
once `overall_match_score` is computed and before the application is
handed on for staging. Neither touches how the score is computed — that
separation is the point of `dynamic-target-calibration.md`'s "why
match_score isn't a policy lever" section, and this is where that
reasoning becomes behaviour.

### Gate 1 — Match score

Read `match_score.minimum` and `match_score.stretch.floor`:

- Below `stretch.floor` — or below `minimum` with stretch disabled →
  not staged.
- Between `stretch.floor` and `minimum`, stretch enabled → staged,
  tagged `[STRETCH]`. `10-approval-and-submit`'s Telegram message
  surfaces that tag, so Kene sees it before tapping approve.
- At or above `minimum` → staged normally, untagged.

### Gate 2 — Overqualification

Compute the two axes:

- `title_delta` — Kene's current O*NET `job_zone` (already computed by
  `07-context-architect` as part of the profile embedding Phase 1.5
  uses) minus the posting's `job_zone`, taken from the
  `title-taxonomy.md` record where the title appears in it, otherwise
  from `02-jd-parser`'s own seniority read.
- `comp_delta` — `salary_floor`, or last confirmed comp if higher, minus
  the posting's disclosed or estimated salary, as a percentage.

Gate both against the current `overqualification_tolerance` using the
threshold table in `dynamic-target-calibration.md`'s "Overqualification
score" section. `strict` / `balanced` / `relaxed` each set their own
pass, flag and drop thresholds on the two axes independently. The table
is deliberately not repeated here so there is exactly one place it can
drift from.

- Clean → staging unchanged.
- Flag range → staged with `[OVERQUALIFIED]`, alongside `[STRETCH]` if
  that also applied. Both can be true of the same application.
- Beyond tolerance → not staged, **regardless of what Gate 1 decided**.
  The two gates are independent, not sequential overrides: a posting can
  clear the score bar and still be dropped here.

### Gate 2 requires inputs that do not always exist

Both axes assume an employment history. `title_delta` needs Kene's
*current* O*NET `job_zone`; `comp_delta` needs `salary_floor` or a last
confirmed comp. Three `profile_stage` values can leave one or both
undefined, and `first_time` leaves both.

`starting-out-track.md` states that `overqualification_tolerance` is
"effectively moot" for `first_time` — that a first-time applicant
essentially never trips this gate. That is correct as a judgement about
*outcomes* and is not a specification of *behaviour*. Nothing said what
the computation does when its inputs are absent, and there are three
different things it could do:

- **Error on a null** — the sweep dies mid-application, and job 3 has no
  partial-run failure semantics to catch it.
- **Coerce nulls to zero** — `comp_delta` becomes `0 − posting_salary`,
  a large negative, which reads as "pays far above floor" and passes.
  The gate then always passes and is dead code that looks live.
- **Skip the gate** — the correct behaviour, but only if it is written
  down and logged.

The middle case is the dangerous one precisely because it looks like it
works. It produces the right verdict for the wrong reason, and it would
keep producing a verdict if `salary_floor` were later set to something
real but the `job_zone` were still missing.

### The rule

Evaluate the two axes **independently**, and skip an axis whose inputs
are undefined rather than substituting a value:

| Condition | `title_delta` | `comp_delta` |
|---|---|---|
| No current `job_zone` on the profile | **skip** | evaluate if comp available |
| No `salary_floor` and no confirmed comp | evaluate if `job_zone` available | **skip** |
| `profile_stage: first_time` | **skip** | **skip** |

A skipped axis is not a pass and not a fail — it is absent. If both are
skipped, Gate 2 does not run, and Gate 1's decision stands alone.

**Log the skip.** Write `overqualification_gate: skipped` with the reason
to the applications DB row rather than leaving it null, so
`11-analytics-and-learning` can distinguish "evaluated and cleared" from
"never evaluated." Those correlate very differently against outcomes, and
a null cannot tell them apart.

**Re-evaluate when the inputs arrive.** The moment `07-context-architect`
records a first confirmed role — which is exactly `16-career-pulse`'s
career-event cascade — `job_zone` and comp become available and this gate
starts applying normally. No separate trigger is needed; it inherits the
one that already exists. What must not happen is the gate staying
permanently skipped because `profile_stage` was never updated off
`first_time` after the first job.

## Logging

Write `overall_match_score` to the applications DB
(`shared/applications_db_schema.sql`) against this posting's row —
`11-analytics-and-learning` correlates this score against real outcomes
over time to check whether the score is actually predictive, and
recalibrates if it isn't.
