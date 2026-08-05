# 03-resume-match — Addendum: dynamic calibration gating (the actual wiring)

**This file exists to close a real gap.** `shared/dynamic-target-
calibration.yaml`/`.md` described what *should* consume the config from
the config's own side ("consumed by 03-resume-match") but nothing was
ever added inside a consuming skill that actually reads it. Well-
specified isn't the same as wired in — this is the fix, and it's the
only one of the three wiring addenda that carries real logic, since
`03-resume-match` is where the score this whole system gates on is
actually computed.

Extends `03-resume-match/SKILL.md` (base package, untouched) with two
steps that run immediately after `overall_match_score` is computed for
an application, before it's handed to whatever stages it for approval.

## Step 1 — Match-score gate

Read `shared/dynamic-target-calibration.yaml`'s `match_score.minimum`
and `match_score.stretch.floor`:

- `overall_match_score < stretch.floor` (or stretch disabled and
  `< minimum`) → not staged.
- `stretch.floor <= overall_match_score < minimum` (stretch enabled) →
  staged, tagged `[STRETCH]` — this tag is what
  `10-approval-and-submit`'s Telegram message surfaces, so Kene sees it
  before tapping approve.
- `overall_match_score >= minimum` → staged normally, no tag.

## Step 2 — Overqualification gate

Compute the two axes `dynamic-target-calibration.md` defines:

- `title_delta` = Kene's current O*NET `job_zone` (already available —
  `07-context-architect` computes this as part of building the profile
  embedding Phase 1.5 uses) minus the posting's `job_zone` (from the
  `title-taxonomy.md` record if the title's in it, else `02-jd-parser`'s
  own seniority read).
- `comp_delta` = `salary_floor` (or last confirmed comp, if higher)
  minus the posting's disclosed/estimated salary, as a percentage.

Gate both against `overqualification_tolerance`'s current value, per
the table in `dynamic-target-calibration.md`'s "Overqualification score"
section — `strict`/`balanced`/`relaxed` each define their own pass/flag/
drop thresholds on both axes independently; that table isn't repeated
here so there's exactly one place it can drift from.

- Passes clean → no change to staging.
- Falls in the flag range → staged with `[OVERQUALIFIED]` alongside any
  `[STRETCH]` tag already applied — both can be true on the same
  application.
- Falls beyond the tolerance's range → not staged, regardless of
  `match_score` gate's result (a job can clear the score bar and still
  be dropped here — the two gates are independent, not sequential
  overrides of each other).

## What this deliberately does not change

`03-resume-match`'s actual scoring method — how `overall_match_score`
gets computed in the first place — is untouched. This addendum only
adds what happens *after* that number exists: whether it clears a bar,
and whether a separate overqualification read clears a different one.
Keeping the two apart is the whole point of `dynamic-target-
calibration.md`'s "why match_score isn't a policy lever" section — this
file is that reasoning's actual implementation point.
