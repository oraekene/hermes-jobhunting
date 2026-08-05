# Gap-Analysis Engine — Ask Only What's Actually Missing

Origin: Kene's proposal to cross-reference the question bank, memory,
and full profile documents (CV/portfolio) against each other, so the
interview only asks about genuine information gaps — not every bank
question that happens to lack a verbatim stored answer, and not
questions that don't even apply to him. Goal stated explicitly: keep
interview length down to what's actually needed to answer any real
application question with high confidence, not hours of exhaustive
Q&A.

**This is a good instinct and worth building** — it's the same
principle production RAG/knowledge-base bootstrap systems use
(retrieve-then-verify-then-fill-only-the-hole), applied to Kene's own
career narrative instead of a document corpus. The existing
`07-context-architect` Phase 2/3 already does a narrower version of
this for STAR stories (the Quantification gate) — this generalizes that
pattern across the whole question bank rather than just quantification.

## The three things that have to combine, and why none of them alone is enough

- **The question bank** (`shared/question_bank.yaml`) — what employers
  actually ask.
- **Memory + full profile** (`MEMORY.md`, `USER.md`, the STAR bank,
  `domain-knowledge.md`, `career-timeline.md`, plus raw CV/portfolio
  ingested in Phase 1) — what's already known about Kene.
- **Relevance to Kene specifically** — a bank question can have zero
  stored answer and still not be a gap, if it's simply inapplicable
  (e.g. a healthcare-compliance question when Kene has never worked in
  healthcare and isn't targeting it — `shared/target-profile.yaml`
  already knows his target industries).

Using only bank-vs-memory (no relevance filter) over-asks: it'd
interview him on every industry variant of every question, most of
which he'll never actually need. Using only relevance (no confidence
check) under-asks: it'd assume anything "roughly covered" in his resume
is fully answerable, missing the exact cases Phase 2's Quantification
gate already catches today (a vague claim isn't a real answer).

## Per-question-variant scoring

**First, a carve-out**: any question tagged `jurisdiction_dependent:
true` (`answer-variants.md`) skips this scoring entirely — it's never a
narrative gap. Check `target-profile.yaml` directly for the relevant
country's work-authorization facts; if present, high-confidence and
done, no interview turn. If missing, the "gap" is a one-line addition to
`target-profile.yaml` itself (a fact Kene states once, reusable across
every application to that country), not a STAR-story interview question
— route it there instead of into Phase 3's interview worklist.

For every other `(question_id, variant)` pair that's actually relevant
given `target-profile.yaml` (skip variants for industries/stages Kene
isn't targeting — cross-reference `variant_dimensions` from
`answer-variants.md` against his real target list, don't score
variants he'll never need), compute two scores during Phase 2:

**Relevance score** — does this question/variant even apply to him?
Derived from `target-profile.yaml` (industries, seniority band, company
stage preferences) plus what's actually present in his ingested
CV/portfolio (e.g. a "describe your experience with regulated
industries" question is irrelevant if neither his target profile nor
his history touches a regulated industry). Low relevance → skip
entirely, don't even attempt synthesis, don't ask.

**Confidence/completeness score** — for questions that pass the
relevance bar, attempt to synthesize an answer from memory right now,
the same way `08-application-qa` would at application time, and
self-assess against the same schemas Phase 2 already checks against
(the Quantification gate's own logic, generalized):
- Is there a specific, on-point STAR story or fact to draw from, or
  would synthesis have to generalize/pad from something adjacent?
- Does it carry a number where the downstream schemas require one
  (05/06's own requirements, exactly as today's Quantification gate
  already checks)?
- Is it a variant-specific claim (per `answer-variants.md`) where only
  the *default* variant is filled in and the specific one asked for
  isn't?

Score low confidence when synthesis would have to invent, generalize
past what's actually stored, or fall back to a variant that doesn't
match. High confidence only when a synthesized answer would satisfy the
downstream schema **verbatim**, matching the existing Phase 3 bar
exactly ("05/06's own requirements are met, or Kene has explicitly said
no number exists").

## What actually becomes an interview question

**Gap = relevant AND low-confidence.** Only that intersection surfaces
in Phase 3. Concretely, run this as a Phase 1.5 step, right after
ingestion and before the existing Phase 2 analysis, so Phase 2/3 already
receive a pre-filtered worklist instead of walking the entire bank live
in front of Kene:

1. For every bank question × relevant variant: attempt synthesis
   silently (no interview turn yet).
2. Score confidence/completeness per the schema-match test above.
3. Anything that synthesizes with high confidence: **write it straight
   to the STAR bank / domain-knowledge file now**, tagged
   `source: gap_analysis_synthesis` — Rule 5 still applies (Phase 4
   synthesis, confirmation gate), but the confirmation for a
   high-confidence synthesized answer can be batched ("here are 40
   answers I'm confident about, confirm/edit any of these") rather than
   interviewed one at a time, since Kene isn't generating new
   information here, just approving what was already derivable.
4. Anything low-confidence-but-relevant: this is the actual interview
   worklist — feeds Phase 3 exactly like today's flagged gaps
   (unexplained transitions, missing STAR categories, quantification
   gaps) do, just with the question bank as an additional gap source
   alongside the existing ones.
5. Anything low-relevance: logged (for the question bank itself — see
   `question-bank-pipeline.md`'s "bank coverage gap" note) but never
   surfaces as an interview question.

This means the interview length scales with **how much of Kene's real
profile is actually thin**, not with the size of the question bank —
adding more questions to the bank over time (Kene's stated worry about
"hours long interviews") doesn't linearly grow the interview, because
most new bank questions will either be irrelevant to him or already
answerable from what's already been captured.

## Re-run cadence

Re-run gap-analysis (not necessarily a full interview) whenever:
- the question bank refreshes (quarterly, per
  `question-bank-pipeline.md`) — new bank questions need a
  relevance/confidence pass, but this should surface as a short "N new
  gaps found" batch, not a full re-interview;
- `target-profile.yaml` changes (new target industry/seniority band
  changes which variants are even relevant);
- `03-resume-match` or `09-risk-tactics-gate` hits a live application
  question that wasn't in the bank at all — that's a signal both for
  "add this to the bank" (feed back into
  `question-bank-pipeline.md`'s Source 3 capture) and for an immediate,
  single-question gap-fill turn right then, rather than waiting for the
  next scheduled pass.

## One honest limitation

Confidence scoring here is being done by the same LLM that will later
draft the application answer — it's self-assessing its own future
synthesis quality, not an independent check. That's an acceptable
approximation (it mirrors what the existing Quantification gate already
does for STAR stories), but it means the gap-analysis engine will
systematically under-flag cases where the *model* is overconfident
about a thin answer, not just cases where Kene's actual profile is
thin. Keep Phase 3's existing bar — "satisfies downstream schemas
verbatim" — as a hard mechanical check rather than a vibe check, since
that's what keeps this self-assessment honest.
