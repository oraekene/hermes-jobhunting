# Fact conflict resolution and aging

How this pipeline decides which of two contradicting facts is true, and
when a fact stops counting as current.

## The gap this closes

`last_confirmed_at` existed in four places before this file: written by
`07-context-architect` at Phase 0 and Phase 0.5, declared null in
`target-profile.yaml.template` and
`dynamic-target-calibration.yaml.template`.

**Nothing read it.** Not one query, not one rule, not one skill. The
package had a timestamp on its facts and no behaviour attached to it.

That mattered because the pipeline's memory is append-only by design and
correctly so — `07-context-architect`'s Rule 5 discipline means facts are
added on confirmation and nothing silently overwrites. The cost of
append-only is that a superseded fact and a current fact sit side by side
looking identical. Kene's salary floor from eighteen months ago and his
salary floor from last week are both true statements that were confirmed;
only one of them is true now.

The rest of the package's memory work sharpened *retrieval*: the
holographic layer, qmd's document search, the taxonomy's vector index,
STAR-bank compression. All of it makes finding facts better and none of
it makes stale facts stop being returned. Better retrieval over unaged
memory returns the wrong answer faster.

## Rule 1 — More recent confirmation wins

**When two facts about the same entity and attribute conflict, the one
with the later `last_confirmed_at` is authoritative. The older is marked
superseded, not deleted.**

That is the whole primary rule, and on its own it closes most of the
problem using a field that already exists and is already written.

Three parts worth stating precisely:

- **Same entity, same attribute.** "Kene's salary floor" is an attribute.
  "Kene wants to work in fintech" and "Kene wants to work in climate
  tech" are *not* a conflict — a person can want both, and treating
  preferences as single-valued is how a system talks itself into deleting
  true things. Conflict detection applies to attributes the schema treats
  as single-valued, and everything else accumulates.
- **Superseded, never deleted.** A superseded fact keeps its row, gains
  `superseded_by` and `superseded_at`, and drops out of default reads.
  It stays queryable, because "what did I think my floor was last year"
  is a real question and because a wrong supersession has to be
  recoverable.
- **Confirmation, not observation.** `last_confirmed_at` moves when Kene
  confirms a fact, not when the pipeline reads or re-derives it. A fact
  the system re-inferred from the same stale source is not fresher for
  having been looked at again.

### Ties and near-ties

Equal timestamps, or two confirmations inside the same session: **do not
resolve automatically.** Surface both to Kene and ask. This is rare
enough that asking costs nothing, and a coin-flip between two facts he
confirmed minutes apart is a coin-flip on which one he meant.

## Rule 2 — Durable and volatile facts age differently

A continuous decay score would be false precision here — there is no
principled half-life for "prefers remote work," and inventing one
produces numbers that look meaningful and aren't. A **binary flag** with
a stated reconfirmation interval says exactly as much as is actually
known.

Every fact carries `volatility`:

| Class | Reconfirm | Examples |
|---|---|---|
| `durable` | Never, unless contradicted | Degrees, past employers, roles held, shipped projects, certifications earned, languages |
| `volatile` | Per the interval below | Salary floor, location, visa status, remote preference, availability, current title, target titles, interests, tools in active use |
| `contextual` | Per-use | Anything true only relative to a specific application or employer |

`durable` facts are the majority of the STAR bank and most of the resume
base. They do not need aging and should not get it — a 2019 project
shipped in 2019 forever, and a system that asks Kene to reconfirm his
degree annually will train him to click through confirmations without
reading them, which costs more than it buys.

Default reconfirmation intervals, all overridable:

```yaml
fact_aging:
  volatile_reconfirm_months: 12
  high_churn_reconfirm_months: 6    # salary floor, availability,
                                    # current title, visa status
  interests_reconfirm_months: 12    # see 20-interests-profile
  stale_action: flag                # flag | prompt | suppress
```

`stale_action: flag` is the default deliberately. `suppress` — dropping
stale facts from reads — is tempting and wrong: a stale fact is usually
*mostly* right, and silently withholding Kene's salary floor because it
was confirmed thirteen months ago degrades every downstream decision to
protect against a smaller error. Flagging tells the truth, which is that
the fact is probably still good and nobody has checked.

## Rule 3 — A stale fact is labelled, not hidden

When a `volatile` fact past its interval is read:

- It is still returned. It is the best available answer.
- It is tagged `[LAST CONFIRMED: 2025-03-14 — 16 months ago]` at the
  point of use.
- If it is load-bearing for a decision Kene is being asked to make now —
  a salary floor in an offer comparison, visa status in a risk-gate pass
  — that decision includes a one-line reconfirmation prompt.

The label matters more than the prompt. A visible timestamp on a fact
that turns out to be wrong lets Kene catch it in the moment; a silent
one does not.

## Rule 4 — Urgency is derived, never stored

The audit's fourth distinction, and the one where the correct answer is
to build nothing.

A fact's urgency is a function of what is being decided, and the same
fact is urgent in one context and irrelevant in the next. Visa status is
decisive when filtering postings and noise when drafting a STAR answer.
Storing an urgency score would freeze a context-dependent judgement into
a context-free column, and every consumer would then have to work around
it.

Urgency is computed at read time from the query — which is what the
holographic layer's probe-and-read already does. No schema, no column,
no maintenance.

## Interaction with existing memory work

- **`star-bank-aging.md`** handles compression of the STAR bank —
  *how much of a story is retained*, on a chronological gradient. This
  file handles *whether a fact is still true*. Orthogonal, and both
  apply: a 2019 STAR story is compressed by the aging doc and is
  `durable` here, so it is never reconfirmed.
- **`holographic-memory-layer.md`**'s `contradict` tool was adopted for
  this job and, on direct testing, missed the case it was adopted for.
  This file is why that is survivable: supersession by timestamp is
  deterministic and does not depend on a semantic contradiction detector
  working. `contradict` stays as a best-effort surfacing aid for
  conflicts that are *not* same-attribute, where timestamps say nothing.
- **`qmd-retrieval-layer.md`** indexes research caches, not facts, and is
  unaffected. Cache freshness is already handled by the 90-day convention.

## Schema

An important constraint shapes this: **the facts themselves are not in a
database this package owns.** `fact_store` is a Hermes-native tool with
its own storage, exposing `add` / `probe` / `contradict` / `reason` /
`update` and no schema this package can extend. The rest of the
pipeline's memory lives in YAML and markdown files. There is no
`facts` table to ALTER.

So the aging metadata lives in two places, matching where the facts do:

**1. Per-entry, in the memory files themselves.** For YAML-backed memory
(`target-profile.yaml`) and markdown memory (`interests-profile.md`,
`domain-knowledge.md`), each entry carries its own `last_confirmed_at`
and `volatility`. `target-profile.yaml` already had a single file-level
`last_confirmed_at`; it keeps that and gains per-field stamps, because
one timestamp on a file containing both a visa status and a list of
title variants tells you almost nothing about either. This is where most
of the value is, and it needs no schema at all.

**2. `shared/applications_db_schema_addendum_16.sql`** — a
`fact_aging_overlay` table keyed by a stable fact reference, holding the
metadata for facts that live in `fact_store` where we cannot attach it
directly, plus `fact_supersession_log` so a wrong supersession can be
traced and reversed.

An overlay is admittedly a compromise. It can drift from `fact_store` if
a fact is deleted through the tool directly, and the reconcile pass in
the addendum's comments exists because of that. The alternative — putting
aging metadata inside the fact text where `fact_store` would index it as
content — is worse: it pollutes semantic search with timestamps and makes
every probe result noisier. A drift-prone sidecar that keeps retrieval
clean is the better trade here, and the drift is detectable.

## What this does not do

- **It does not detect conflicts the schema cannot see.** Two facts that
  contradict each other in meaning but not in attribute — "available
  immediately" and "started a new role last month" — are invisible here.
  That is what a human reading two facts side by side is for, and the
  package is honest elsewhere that this remains the primary mechanism.
- **It does not reconfirm anything automatically.** Every reconfirmation
  is a question to Kene under Rule 5. A system that refreshed its own
  timestamps would be recording that it had checked, not that he had.
- **It does not make old facts wrong.** The single most likely misuse of
  this machinery is treating `stale` as `false`. A twelve-month-old
  salary floor is very probably still the salary floor. The flag means
  unverified, and nothing stronger.
