# Task B merge — status

Base tree is package A (`job_hunting_interim-2_upgraded-3`, post B1–B21).
Package B (`job_hunting_skill_ADDENDUM-26`) folds into it.

## Structural finding

The two packages share **zero file paths**. B is not a parallel copy of A —
it is an addendum layer: `ADDENDUM.md` files that attach to A's existing
skill directories, plus ten standalone new skills. So most of the merge is
additive, and the reconciliation work is concentrated in eleven `ADDENDUM.md`
files whose content has to be written into the corresponding `SKILL.md`
rather than left as a second document a reader has to know to open.

## Carried across as-is

- 9 new skills from B: 14, 16, 17, 18, 19, 20, 21, 22, onboarding
- `shared/` union — 5 SQL addenda, 6 templates, 4 reference docs
- `hermes-capability-audit.md`
- `07-context-architect/references/content-model-overlap.md`

## Already reconciled

- **13/15-interview-prep** — name collision resolved by merge; A is the
  spine, B's intel layer folded in. Record in `15-interview-prep/`.

## Addendum folds

| Layer | Lines | Status |
|---|---|---|
| 00-orchestrator | 16 | folded — fresh-install routing now goes via `onboarding` |
| 01-job-discovery | 18 | folded — calibration inheritance stated at the filter step |
| 08-application-qa | 13 | folded — template check added as step 0 |
| 09-risk-tactics-gate | 22 | folded — widened `first_time` evidence sources, bar unchanged |
| 10-approval-and-submit | 18 | folded — site-access model 3 made explicit |
| 05-resume-customizer | 31 | folded — `first_time` format branch + template precedence |
| 06-cover-letter | 26 | folded — template check + `first_time` narrative shape |
| 03-resume-match | 64 | folded — both calibration gates, independent not sequential |
| 12-company-research | 76 | folded — sentiment research + new cache section |
| 07-context-architect | 98 | folded — calibration-aware Phase 1.5, `profile_stage`, derived indexes |
| cron-jobs-addendum | 104 | folded — renumbered 9-14 to 10-15; job 16 added |
| README-addendum | 767 | folded — history split to ADDENDUM-CHANGELOG.md, install unified |

## Convention

Folded content is written into the host file at the point it applies, not
appended as a trailing section. Each `ADDENDUM.md` is preserved verbatim
under `.merge-history/addenda/` so any fold can be audited against its
source. Nothing is deleted.

## Defect found and fixed during the merge

The B21 path-qualification pass doubled six paths where a reference was
already skill-qualified but wrapped across a line — `06-cover-letter/\n
06-cover-letter/references/...`. The regex saw the second half as a bare
`references/` path and qualified it again. Repaired in all six files
across the merged tree and both source packages.
