# Fact influence — separating relevance from trust

## The distinction

Holographic gives every fact a **trust score**: 0.0–1.0, default 0.5,
moved by `fact_feedback` at +0.05 helpful / −0.10 unhelpful. It is the
only ranking dimension the provider has.

Trust measures **reliability** — is this fact correct and does it hold
up. It says nothing about **importance** — does this fact change what the
pipeline produces.

The example that makes it concrete:

> "Kene's daughter is called Ada" can be perfectly trustworthy and
> completely irrelevant to a job application. "Kene will not relocate" is
> decisive. Both sit at 0.5.

Feedback alone does not fix this. Wiring `fact_feedback` on (v26) means
trust scores finally move, but they move along the reliability axis and
only ever along that axis. A retrieval ranked purely by trust returns
correct facts, in an order that has nothing to do with whether they
matter.

**Influence is the second dimension**: how often has this fact
*materially changed an output*. It is derivable from data the pipeline
already logs, which is why this is worth building rather than
approximating.

## What counts as influence

A fact influenced an output when its presence changed what was produced —
not when it was merely retrieved. The distinction is the whole design,
because retrieval counts are trivially available and completely
misleading: the most-retrieved fact in any career memory bank is
something like a current job title, which is retrieved constantly and
decides almost nothing.

Four events count, each already recorded somewhere:

| Event | Source | Weight |
|---|---|---|
| **Gate outcome changed** — a fact supplied the evidence that passed a claim through `09-risk-tactics-gate`, or was the reason one failed | `tactics_log` | 3 |
| **Went out in a document** — the fact appeared, in substance, in a resume bullet or cover-letter paragraph that survived to `staged` | `05`/`06` change-logs | 2 |
| **Story selected** — the fact drove which STAR story was chosen over an alternative | `05-resume-customizer` selection record | 2 |
| **Filtered a posting** — the fact caused a posting to be dropped or ranked down at Gate 1 or 2 | `03-resume-match` | 1 |

Weights are ordinal, not measured. They encode one judgement — that
changing a *gate decision* is a bigger deal than appearing in prose,
which is bigger than nudging a rank — and nothing finer than that.
Treating them as calibrated would be false precision, and the ranking is
insensitive to their exact values.

**Retrieval without use scores zero.** A fact probed and passed over is
evidence *against* its influence, not for it.

## Scoring

```
influence_raw   = Σ (event_weight)  over the trailing 180 days
influence_score = influence_raw / (influence_raw + k)      k = 6
```

A saturating curve, not a linear count, deliberately. Linear counts let
one heavily-reused fact dominate a ranking permanently, and the useful
signal here is categorical — *does this fact do work* — rather than how
much. The curve gives roughly 0.14 at one event, 0.5 at six, 0.77 at
twenty, and never reaches 1.

**The 180-day window is the point, not a detail.** A fact that mattered
during a management-track search two years ago and has done nothing since
should not rank above one that is deciding gates this month. Influence
decays by falling out of the window, which is a real decay function
applied to the dimension that can support one — unlike the aging work in
`fact-conflict-resolution.md`, which deliberately declines to put a decay
curve on *truth*.

## How the two dimensions combine at retrieval

**They are reported separately and never averaged into one number.**
Collapsing them recreates exactly the problem this file exists to fix: a
single score cannot say whether a fact ranked low for being unreliable or
for being unimportant, and those call for opposite responses — verify it,
or ignore it.

Retrieval ranks by relevance to the query first (that is the provider's
job and this changes none of it), then presents the two scores alongside:

```
[TRUST 0.65 · INFLUENCE 0.77] Kene will not relocate outside Rivers State
[TRUST 0.50 · INFLUENCE 0.03] Kene's daughter is called Ada
```

The four corners are all meaningful, which is the argument for keeping
them apart:

| | Low influence | High influence |
|---|---|---|
| **High trust** | Correct, decides nothing. Fine — most of memory lives here. | The load-bearing facts. Surface first. |
| **Low trust** | Ignore. | **Look at this.** A fact deciding gates that keeps getting edited out is the single most valuable thing this scoring can surface — it is wrong *and* it matters. |

That bottom-right cell is the real payoff. Neither dimension finds it
alone: trust alone flags it as unreliable among dozens of equally
unreliable trivia, and influence alone flags it as important without
noticing anything is wrong.

## Where it is computed

`11-analytics-and-learning`'s weekly pass, in the same step that emits
`fact_feedback` — the events are being read there anyway, so this is one
more aggregation over an already-open query rather than a second scan.

Recompute from events every run rather than incrementing a stored
counter. The events are the truth; a running total drifts, and it cannot
implement the trailing window without a second decay pass to undo itself.

Storage: `fact_influence` and `fact_influence_events` in
`shared/applications_db_schema_addendum_17.sql`. Same overlay pattern as
addendum 16 and for the same reason — `fact_store` is Hermes-native with
no schema this package can extend.

## Reporting

The weekly digest gains three lines, all of which answer a question that
was previously unanswerable:

- **Top 5 by influence** — which facts are actually carrying the search.
- **Low-trust, high-influence** — the bottom-right cell above. Empty most
  weeks; when it isn't, it is the most important line in the digest.
- **Zero-influence facts older than 180 days** — reported as a count, not
  a list, and **never as a deletion prompt**. See below.

## What this does not do

- **It does not delete anything, or suggest deleting anything.** A
  zero-influence fact is not dead weight — it is a fact that has not yet
  been needed, and a career memory bank exists precisely to hold things
  until the day they matter. The interest nobody asked about for three
  years is the one that lands the conversation. Influence ranks; it never
  prunes, and any future feature that reads this score as a
  garbage-collection signal has misunderstood it.
- **It does not feed back into trust.** The two stay independent by
  construction. A high-influence fact is not thereby more likely to be
  correct, and letting influence nudge trust would reintroduce the
  conflation in a subtler form.
- **It does not measure whether the influence was good.** A fact that
  reliably decides gates might be reliably deciding them *wrongly*.
  Trust, driven by `fact_feedback`, is what catches that — which is why
  both dimensions are needed and why the low-trust/high-influence cell is
  the one worth watching.
- **It is cold for the first month.** Every score is zero until events
  accumulate, and a 180-day window means it takes a quarter to say much.
  There is no way to backfill it honestly, since the events were not
  recorded before. Expect it to be uninformative early and say so rather
  than reading noise as signal.
