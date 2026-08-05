# Answer Variants — Same Question, Different Contexts

Origin: Kene's observation that a single question bank entry
("Why do you want to work here?") doesn't have one right answer — the
honest, well-targeted answer for a Series A fintech startup is a
different answer than for a Fortune 500 bank, even though it's
word-for-word the same question. This file defines which contextual
dimensions actually change the required answer, and how the variant is
stored so `08-application-qa` can pull the right one instead of the
generic one.

## Which dimensions actually matter (and which don't)

Not every dimension changes every question — that's the key design
constraint, otherwise this becomes a combinatorial explosion (100
questions × 5 industries × 4 seniority bands × 3 company sizes... is
6,000 variant slots, most of them identical to their neighbor). The
dimensions below are ordered by how often they actually change the
*content* of a good answer, not just its tone:

1. **Company stage/size** — this is the single highest-impact
   dimension. "Why do you want to work here?" at a 20-person startup
   should talk about ownership, ambiguity, and building something from
   scratch. At a 50,000-person enterprise, the same question should
   talk about scale, process maturity, and cross-functional impact.
   Answering the startup version at an enterprise reads as naive;
   answering the enterprise version at a startup reads as someone who
   wants bureaucracy. Bucket as: **early-stage (<50 people), growth
   (50–500), enterprise (500+)**.

2. **Seniority/level of the role applied for** — changes *scope* of the
   answer, not just tone. "Describe a time you handled conflict" at IC
   level should center on the conflict itself and how Kene personally
   resolved it. At a manager/lead level, the same question should show
   how he mediated *between other people's* conflict, not just his own.
   Bucket as: **individual contributor, first-line lead/manager,
   senior/director+**.

3. **Industry/regulatory context** — mostly matters for
   compliance-adjacent questions ("how do you handle sensitive data",
   "describe your approach to risk") more than for generic behavioral
   questions. Finance/healthcare answers should reference process and
   auditability; a scrappy consumer-tech answer to the same question
   can reference speed and iteration. Doesn't need to vary the *whole*
   bank — flag per-question whether industry actually changes the
   answer (most behavioral questions don't; compliance/risk/technical
   questions usually do).

4. **Function of the role** (engineering vs. product vs. ops, etc.) —
   matters when Kene is applying across functions (he does, given his
   PM + developer + generalist range per his own background) more than
   it would for someone with one fixed title. A "tell me about a
   technical decision you made" answer should pull a different STAR
   story depending on whether the audience is evaluating him as an
   engineer or as a PM directing engineers.

5. **Remote vs. hybrid vs. on-site** — narrow but real: questions like
   "how do you stay productive/communicate with your team" have a
   genuinely different good answer for a fully-remote/async-first
   company versus an in-office one. Low-frequency dimension — only a
   handful of questions in the bank actually need this split.

6. **Mission-driven/nonprofit vs. commercial** — narrow but sharp when
   it applies: "why this company" for a nonprofit or B-corp genuinely
   wants a values-alignment answer; the same question at a purely
   commercial company wants a career/growth/impact answer. Don't force
   this split onto questions that don't need it.

7. **Employment type** (full-time vs. contract/freelance) — directly
   relevant given Kene's own mixed profile (freelance AI PM work
   alongside a self-built project portfolio). "How do you manage your
   workload" or "what's your availability" reads differently for a
   contract engagement than a full-time role; a contract-specific
   variant should lean into the freelance-portfolio framing rather than
   a single-employer narrative.

## Jurisdiction-dependent questions aren't a variant — they're a fact lookup

Worth calling out as a **separate, non-narrative category**, not one
more item on the list above: "Are you legally entitled to work in the
UK?" and "Will you now or in the future require sponsorship to work in
the US?" aren't different *stories* the way a company-stage or
seniority variant is — they're different countries' legal questions
with a factually correct answer that either exists in
`shared/target-profile.yaml` or doesn't. There's no good "startup
version" vs. "enterprise version" of a work-authorization answer; there's
just the correct answer for whichever country this posting is in.

Tag these in the question bank schema as `jurisdiction_dependent: true`
rather than giving them a `variant_dimensions` list. This matters
operationally: `08-application-qa` and the gap-analysis engine
(`gap-analysis-engine.md`) should never try to synthesize a "STAR story"
for one of these or treat an unanswered one as a narrative interview
gap — the only real gap possible here is `target-profile.yaml` itself
missing the relevant country's work-authorization facts, which is a
data-entry task, not an interview question about Kene's experience.
`question_bank_crawler.py`'s curate step flags likely candidates
automatically (a keyword check for "sponsorship," "legally entitled to
work," "work authorization," "visa" in the canonical text) for
confirmation during the human review pass — not a fully automatic tag,
since a false negative here (missing one) is worse than a false
positive (over-flagging one that turns out to need a real answer).

**Geography as a *story* dimension, distinct from the above, stays
excluded**: general interview-answer content rarely needs to change by
country the way it needs to change by company stage or seniority — the
work-authorization questions above are the one place geography
genuinely changes what's correct, and that's a fact lookup, not a
narrative choice.

## Per-question dimension tagging (not every question needs every split)

Each question bank entry (`shared/question_bank.yaml`) gets a
`variant_dimensions` field listing *only* the dimensions that actually
change its answer, decided once during the curation pass in
`question-bank-pipeline.md`:

```yaml
- id: qb_0001
  canonical_text: "Why do you want to work here?"
  category: motivation
  variant_dimensions: [company_stage, mission_driven]
  # seniority/function/remote don't meaningfully change THIS question

- id: qb_0002
  canonical_text: "Describe a time you handled conflict with a colleague."
  category: behavioral_conflict
  variant_dimensions: [seniority]
  # company stage doesn't change a conflict story; seniority does
  # (own conflict vs. mediating others')

- id: qb_0003
  canonical_text: "How do you approach data privacy and sensitive information?"
  category: compliance
  variant_dimensions: [industry]

- id: qb_0004
  canonical_text: "Will you now or in the future require sponsorship to work in this country?"
  category: work_authorization
  jurisdiction_dependent: true
  variant_dimensions: []   # never populated — this pulls from
                           # target-profile.yaml per-country, not a
                           # STAR-story variant
```

This keeps the interview from asking about dimensions that don't matter
for a given question — the Phase 3 interview loop only asks "which
[dimension] variant" for questions that actually declared that
dimension.

## Where the variant answers live

Extend `memory/star-story-bank.md`'s structure (loaded as a skill
reference, same as today) with a **variant table per question ID**
rather than a single free-text answer per question:

```markdown
## qb_0001 — Why do you want to work here?

| Variant | Answer |
|---|---|
| early-stage | [STAR-flavored answer emphasizing ownership/ambiguity/building from scratch] |
| growth | [answer emphasizing scaling systems that already work] |
| enterprise | [answer emphasizing cross-functional impact at scale] |
| mission_driven | [answer emphasizing values alignment, cites specific mission language] |
```

`08-application-qa`'s existing Step 3 ("Select the story") gets one new
sub-step inserted before it: **read the target company's stage/mission
signals from the job posting** (already being parsed by `02-jd-parser`
— this doesn't need new ingestion, just a new field read from data
already collected), pick the matching variant row, and only fall back
to a default/generalized answer if no variant has been filled in yet —
which itself is a gap the interview loop should flag (see
`gap-analysis-engine.md`).

## Interview loop change (07-context-architect Phase 3)

When a gap surfaces for a question that has `variant_dimensions` set,
the interview asks once per relevant, *actually-differing* value — not
every combinatorial cell. E.g. for `qb_0001` above with
`[company_stage, mission_driven]`, that's up to 4 short questions
total (early-stage / growth / enterprise / mission_driven), asked as
one batch turn ("give me your answer to 'why do you want to work here'
for: (a) a small early-stage startup, (b) a big established company,
(c) a mission-driven nonprofit") rather than three separate interview
turns — keeps this from ballooning the interview length, which is the
same concern driving the gap-analysis system in the next file.
