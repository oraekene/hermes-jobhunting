# Interview Intelligence Research

Scrubs what's publicly known about interviewing for a given role — not
what the company is like generally (that's `12-company-research`'s job,
including its new sentiment section), specifically what the *interview
itself* tends to look like: questions asked, formats used, what a good
answer reportedly contains.

## Three scopes, cached separately, because they decay at different rates

1. **Role/title, general** — e.g. "AI Product Manager interview
   questions" with no industry or company attached. Broadest, most
   stable, longest cache life.
2. **Role/title within an industry** — e.g. "AI PM interview, fintech."
   Narrower, moderately stable.
3. **Role/title at a specific company**, where findable — the narrowest
   and most valuable when it exists, but often thin or absent for
   smaller/less-reviewed employers. Absence here is expected and fine;
   don't force a finding.

## Cache

`shared/interview_intel_cache/{title_slug}.md` (scope 1),
`shared/interview_intel_cache/{title_slug}__{industry_slug}.md`
(scope 2), `shared/interview_intel_cache/{title_slug}__{company_slug}.md`
(scope 3). Same 90-day freshness convention as the company cache — check
before re-running, re-run if stale (interview formats and question
trends do shift, if more slowly than company news).

## Sources

YouTube (mock-interview and "questions they asked me" videos), Reddit
(role-specific and company-specific subreddits/threads), LinkedIn posts
and articles, professional/industry blogs and forums, and the company's
own careers page/engineering blog/hiring posts where scope 3 applies.

## What to actually extract

- Guides, tutorials, techniques, tips — general prep material for this
  role/context.
- **Actual questions reportedly asked**, verbatim where a source states
  one plainly, tagged with which scope and how many independent sources
  corroborate it (one report is a data point; the same question showing
  up across several independent threads is a real signal).
- **Reportedly good/preferred answers or answer structures** — the
  *shape* of what worked (e.g. "candidates report structuring the system-
  design answer around trade-offs, not just a final design"), not a
  specific person's specific verbatim answer presented as Kene's own
  material to recite.

## The rule that matters most here

**A reported "preferred answer" is a structural cue, never a script.**
This skill's whole job upstream of the brief (`15-interview-prep/
SKILL.md` step 3) is mapping likely questions to Kene's *own* STAR-bank
entries — this cache tells it which questions and what shape of answer
tends to land, it never supplies the answer content itself. Handing Kene
someone else's reported answer to recite would be a fidelity problem
worse than anything `09-risk-tactics-gate` normally has to catch — it's
not embellishing Kene's own background, it's rehearsing someone else's.
Same "never fabricate/never launder a finding into something it isn't"
discipline the company-research skill already established, applied here
to a different failure mode.

## Cache record shape

```markdown
# [Title] interview intelligence — [scope: general | industry:X | company:Y]

researched_at: 2026-07-25

## Reported format
[rounds, typical structure, take-home or not, pace — "no reliable
signal found" is a valid result]

## Frequently reported questions
- [question] — reported by [N] independent sources
- ...

## Reported answer shape (not verbatim content)
[what tends to work, structurally — e.g. "quantify impact even when the
question doesn't ask for a number," "name trade-offs before committing
to one design"]

## Prep guides/techniques worth knowing about
[links/summaries, paraphrased per this pipeline's copyright discipline]

## Confidence note
[thin / well-sourced / mixed]
```

## Where this plugs in

Feeds `15-interview-prep`'s brief-assembly and mock-drill steps
directly — see that skill's `SKILL.md` for exactly how the three scopes
get cross-referenced against `question_bank.yaml` and
`gap-analysis-engine.md`'s output for a specific application.
