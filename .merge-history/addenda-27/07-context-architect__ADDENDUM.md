<!-- STATUS: ABSORBED. This file is preserved as a record, not as instructions.
Content lives in 07-context-architect/SKILL.md (calibration-aware Phase 1.5, profile_stage, derived indexes).
Do not follow it as a procedure; the host file named above is authoritative. -->

# 07-context-architect — Addendum: calibration-aware Phase 1.5

Same honesty note as the `03-resume-match` addendum: this is the actual
wiring, not just a description of intended wiring. Extends `07-context-
architect/reference/title-taxonomy.md`'s existing Phase 1.5 (base file
untouched) with one new input.

## What changes

Phase 1.5's adjacent/higher-title expansion already runs on two
triggers per the base file: a refresh cadence, and "when Kene's target
profile changes significantly." This addendum adds a read, at the start
of any Phase 1.5 run, of `shared/dynamic-target-calibration.yaml`'s
`employment_status` and `auto_relax_schedule`:

- If `employment_status` is `unemployed`/`between_roles` and enough
  weeks have accumulated to hit an `auto_relax_schedule` step with
  `also_widen_title_taxonomy_similarity_threshold: true` (the 26-week
  step, in the shipped template), Phase 1.5's embedding-similarity
  threshold widens for that run — surfacing more tangential/adjacent
  titles than it would at the default threshold, not just accepting
  lower scores on the same titles it already found.
- Otherwise, Phase 1.5 runs exactly as `title-taxonomy.md` already
  specifies — this addendum only ever *widens* the net under a specific,
  auditable condition, never narrows it or changes anything else about
  how Phase 1.5 works.

Every proposed title variant this produces still goes through the exact
same confirm-before-write step `title-taxonomy.md` already requires —
this addendum changes how wide Phase 1.5 casts its net, not whether a
human confirms what it finds.

## Where the confirmed output goes — and why `01-job-discovery` needs no
## changes of its own

Confirmed `title_variants` land in `target-profile.yaml` exactly as
`title-taxonomy.md` already documents. `01-job-discovery` reads that
same field for what to search for — it was never going to need its own
copy of the calibration logic; it just needs to keep reading
`target-profile.yaml`, which it already does. See `01-job-discovery/
ADDENDUM.md` for that side of it, kept short on purpose because there's
genuinely little to add there.

## One more provenance value, from `19-career-path-planner`

`title_variants` entries now carry a fourth possible `source` value,
`path_planned`, alongside the base file's `held`/`applied`/
`taxonomy_suggested` — proposed when Kene deliberately chooses to start
actively searching for a target he built a career path toward (see that
skill's Step 5), rather than something the taxonomy noticed on its own
or something he already did. Same confirm-before-write step as every
other value; the only thing that changes is what gets recorded in
`rationale` — a pointer to the specific `career_path_plans/{plan_id}.md`
this came from, not a taxonomy-similarity explanation.

## New sub-phase: Content Model mapping (feeds `19-career-path-planner` mode (c))

`reference/content-model-overlap.md` adds one derived index this skill
now maintains: a mapping of existing, already-confirmed
`domain-knowledge.md`/STAR-bank entries onto O*NET's standardized
Content Model elements, built once as a batched propose-and-confirm
pass (not a new interview), and re-derived automatically whenever those
source files change — same career-event cascade trigger already firing
Phase 1.5, one more consumer of it rather than a second trigger to keep
in sync. This skill doesn't compute the actual overlap scores
(`19-career-path-planner` does, as an `execute_code` job per that
file) — it only owns keeping the mapping itself current, same
"07-context-architect writes confirmed facts, other skills read them"
split as everything else here.

## New field: `profile_stage`, and a second shape for Phase 1-4

`onboarding` sets `target-profile.yaml`'s new `profile_stage` field
(`experienced` | `first_time` | `returning_after_gap` | `career_pivot`)
before Phase 0 runs in earnest. For `first_time` specifically, Phase
1's ingestion sources widen beyond resume/portfolio (school records,
coursework, extracurriculars, volunteer/community work, self-taught
skills), Phase 2's Quantification gate applies at the same rigor to
that wider source list rather than a relaxed one, and `memory/
interests-profile.md` elicitation moves from a deferred, advanced-tier
pass to co-primary with the STAR bank in the same first session. Full
reasoning and the rest of what changes pipeline-wide is in
`onboarding/reference/starting-out-track.md` — this skill's own role in
it is just Phase 1-4's source list and sequencing, not the whole
adaptation.

Same ownership split as `16-career-pulse`: `20-interests-profile` runs
the elicitation and proposes entries (first-pass interview, plus
ongoing journal-surfaced candidates), this skill is still the only one
that actually writes `interests-profile.md`, Rule 5 unchanged. One
thing worth flagging explicitly since it's a real departure from how
every other memory file in this package works: `interests-profile.md`
entries carry **no quantification/evidence bar** — see that skill's own
"Admission criteria" section for why the STAR-bank standard would be
the wrong bar to import here. Also feeds a second derived index,
alongside the Content Model mapping above: `20-interests-profile/
reference/riasec-mapping.md`'s RIASEC vector, same batched-confirm,
same re-derivation trigger.
