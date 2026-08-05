# Content Model Overlap — a real transferable-skills matching engine

Answers Kene's direct question for `19-career-path-planner` mode (c):
**does a complete transferable-skills matching system already exist in
this pipeline?** No — and it's worth being precise about why, because
the honest answer isn't "nothing exists," it's "something exists and
it's the wrong tool for this specific job by construction, not by
omission." Extends `title-taxonomy.md`'s infrastructure rather than
replacing it or building parallel infrastructure alongside it.

## What exists today, and exactly why it can't do mode (c)'s job

`title-taxonomy.md`'s Phase 1.5 match is real, working, and the right
tool for mode (b) — but look at how it's actually built: each
occupation's `tasks`/`knowledge`/`skills`/`abilities` fields are
**free-text lists, concatenated into one blob and embedded as a single
vector** (that file's own words: "concatenate tasks + knowledge +
skills + abilities into one text blob per occupation"). Kene's side
works the same way — one embedding built from the whole of
`domain-knowledge.md` + the STAR bank + his resume. Matching is then
whole-vector cosine similarity.

That's a **profile-similarity** score, not a **skill-transfer** score,
and the two genuinely diverge exactly where mode (c) lives: two
occupations can share almost no vocabulary, task framing, or industry
context — scoring far apart on whole-blob similarity — while still
overlapping heavily on three or four *specific* skills or abilities
that would transfer perfectly well. Whole-text embedding similarity
structurally can't surface that case, because the signal gets diluted
into an aggregate. Adding a seniority tag to this query, as Kene
suggested might already be all that's needed, would filter the *wrong*
candidate set by seniority — it wouldn't fix the underlying reason mode
(c) needs a different mechanism in the first place.

## The piece that makes this fixable without new infrastructure

O*NET doesn't only publish free-text task/skill descriptions — it also
publishes, per occupation, numeric **Importance** and **Level** ratings
against a **fixed, standardized set of ~120 elements** (35 Skills, 52
Abilities, 33 Knowledge domains, plus Work Activities and Work Styles),
each with a stable Element ID. This is O*NET's actual Content Model,
and it's specifically built for the thing whole-text embeddings can't
do: because "Active Listening" (Element ID `2.A.1.a`) means the exact
same thing and is scored the exact same way for every one of the
~1,016 O*NET occupations, two occupations' Content Model ratings are
**directly, numerically comparable** regardless of how different their
titles, industries, or task descriptions read in prose.

`title_taxonomy_builder.py` already pulls O*NET data for every
occupation in scope — this is an additional endpoint call per
occupation (O*NET's Web Services has dedicated Skills/Abilities/
Knowledge/Work Activities/Work Styles report endpoints), not a new data
source, and it stores as an additive field on the exact same record
`title-taxonomy.md` already defines:

```yaml
# addition to the existing record schema in title-taxonomy.md —
# nothing else on that record changes
content_model:
  skills:     [{element_id: "2.A.1.a", name: "Active Listening", importance: 4.2, level: 3.8}, "..."]
  abilities:  [{element_id: "1.A.1.a.1", name: "Oral Comprehension", importance: 3.9, level: 3.5}, "..."]
  knowledge:  [{element_id: "2.C.1.a", name: "Administration and Management", importance: 3.7, level: 3.2}, "..."]
  # Work Activities / Work Styles follow the same {element_id, name,
  # importance, level} shape
```

## Building Kene's own Content Model vector — derived, not a new interview

The important design choice: **this doesn't require interviewing Kene
about 120 abstract elements he's never heard of.** He's already
answered the questions that matter — `domain-knowledge.md` and the STAR
bank already hold evidence-cited, confirmed proficiency claims. This
engine's only new step is **mapping what's already confirmed onto the
nearest O*NET element(s)**, not eliciting anything new:

1. For each existing `domain-knowledge.md`/STAR-bank entry, propose a
   mapping to the closest Content Model element(s) — a semantic-
   matching step (judgment, not arithmetic — a `delegate_task`-scale
   job, not `execute_code`), producing candidate `{element_id,
   evidence_ref}` pairs.
2. **Batched confirmation, once** — not a new open-ended interview,
   closer to Phase 1.5's existing "here's a suggestion with cited
   evidence, confirm or correct" pattern, reviewed as one pass rather
   than 120 separate questions.
3. Store the confirmed mapping as a derived index, not a new memory
   file requiring its own upkeep — it's a projection of
   `domain-knowledge.md`/the STAR bank onto O*NET's element space, and
   it goes stale (and gets flagged for re-mapping) exactly when those
   source files change, via the same career-event cascade
   `16-career-pulse` already fires for Phase 1.5.

## The actual score — this is the arithmetic step, and it's simpler than embeddings

Once both sides exist as `{element_id: rating}` vectors over the *same*
fixed ID space, the overlap computation is exact-match arithmetic, not
approximate-nearest-neighbor search — a genuinely simpler operation
than what mode (b)'s embedding query needs, and a clean `execute_code`
job per `hermes-capability-audit.md`'s rule of thumb (mechanical,
deterministic work belongs there, not in a reasoning turn):

- `transferable_skill_score` = weighted overlap between Kene's rated
  elements and a candidate occupation's rated elements, restricted to
  elements both sides actually have a rating for (no invented overlap
  on elements neither side evidences).
- Compute this **independently of whole-text embedding similarity** —
  the two scores are meant to diverge sometimes, and the divergence
  itself is informative: high `transferable_skill_score` + low
  whole-text similarity is precisely the "non-obvious but real"
  candidate mode (c) exists to surface. High on both is really a mode
  (b) candidate that happened to also clear this check. Low on both is
  correctly excluded from either mode.
- Every element that contributes meaningfully to the score carries its
  `evidence_ref` forward — so a mode (c) result reads "strong overlap
  because your [STAR story/domain-knowledge entry] evidences [element],
  which this target role rates as important," never a bare number.

## Where this plugs in

- `19-career-path-planner` mode (c) queries this score directly (at the
  chosen `job_zone`, ranked by `transferable_skill_score`, independent
  of the embedding-similarity band mode (b) uses) — see that skill's
  own mode (c) section for the updated description.
- Step 2's gap analysis, for a mode (c) plan specifically, can now cite
  *why* a "no title-similarity" target still made sense as a candidate
  in the first place, using the same element-level evidence.
- Re-computation is tied to the same trigger `07-context-architect/
  ADDENDUM.md` already wires Phase 1.5 to — one re-run point, not a
  second cascade to keep in sync with the first.
