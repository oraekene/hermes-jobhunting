---
name: job-hunting-context-architect
description: "Build or update durable career context and STAR bank"
metadata:
  hermes:
    tags: [job-hunting, context-architect]
    category: job-hunting
    related_skills:
      - job-hunting-resume-match
      - job-hunting-application-qa
      - job-hunting-career-pulse
      - capability:interests_profile
---

# Context Architect

## When this skill applies

Use this skill to build or update Kene's durable career context — target profile, career timeline, STAR behavioral story bank, and domain-knowledge documentation — by ingesting his resume/portfolio and interviewing him to fill narrative gaps. Triggers: first-time pipeline setup, 'update my career story bank', 'update my target roles', 'I want to add a new story about X', or when 03-resume-match / 09-risk-tactics-gate flags a gap this skill needs to resolve. Do NOT use this for a single application's content (that's 05/06/08) — this skill produces the reusable source-of-truth that those skills read from.

Origin: Kene's original "Chat 5A." Same ingestion → gap-analysis →
interview → synthesis structure, but the destination changes: instead of
three one-off markdown documents, the output now lives in Hermes's actual
memory system, so every later skill and every future session reads from
it automatically instead of Kene re-pasting it per chat.

**Only this skill writes new facts into memory (Rule 5,
`shared/pipeline-rules.md`).** Every other skill reads memory; none of
them invent and persist claims about Kene's career on their own.

## Where things live

- **`~/.hermes/memories/USER.md`** — who Kene is, in the ~500-token
  budget Hermes reserves for durable user facts: role, location,
  seniority, target industries, non-negotiables (salary floor, remote
  preference). Keep this to the facts every single pipeline run needs.
- **`shared/target-profile.yaml`** — the structured, machine-readable
  version of the same target-profile facts (title variants, seniority
  band, locations, salary floor, visa sponsorship, exclusions,
  `fidelity_mode`, `discovery_mode`). `USER.md` is prose for context;
  this file is what `01-job-discovery`'s cheap filter, any per-source
  query-builder, and `09-risk-tactics-gate`'s fail handling actually
  parse. All of it is written together from the same confirmed
  interview — see "Phase 0" and "Phase 0.5" below. Never write to this
  file except through this skill, and never maintain a second copy of
  any of its settings elsewhere — this file is the single source of
  truth for every one of them.
- **`~/.hermes/memories/MEMORY.md`** — durable facts and lessons that
  aren't strictly "who Kene is" but should always be in context: active
  job-search constraints, current strategy adjustments from the
  self-improvement loop (see `11-analytics-and-learning`), standing
  instructions ("never apply to companies X/Y," "always ask before
  matching a title above current level"). Nothing else writes here except
  through this skill (Rule 5) — see the `open_gaps` table below for the
  one thing that used to live here and doesn't anymore.
- **`open_gaps` table** (`shared/applications_db_schema.sql`) — every gap
  `09-risk-tactics-gate` has flagged, unresolved. This is a worklist this
  skill reads at the start of every run, not just a note to itself — see
  "When to re-run" below. It lives in the DB rather than in `MEMORY.md`
  on purpose: `09-risk-tactics-gate` writes it unattended, during cron
  runs, and `MEMORY.md`'s hard character cap plus its "only
  context-architect writes, only after confirmation" discipline (Rule 5)
  make it the wrong place for an append-only list nobody's there to
  consolidate at 2am.
- **`memory/star-story-bank.md`** (this pipeline's own file, loaded as a
  skill reference rather than crammed into the tight MEMORY.md budget) —
  the full Behavioral Examples Database: Problem-Solving Cases,
  Leadership & Strategy, Project Management, Team Collaboration &
  Conflict. This is what `06-cover-letter` and `08-application-qa` pull
  concrete stories from. Every story's Result/Outcome must carry a
  **Quantified Outcome** field — see "Quantification gate" below; this
  isn't a separate invented rule, it's this skill's obligation to
  satisfy what `05-resume-customizer` Phase 5 and `06-cover-letter`'s
  formula paragraph 3 already require downstream.
- **`memory/domain-knowledge.md`** — Technical Expertise, Industry
  Knowledge, Market Analysis Experience, Product Knowledge, each mapped
  to proficiency level and the specific project that proves it.
- **`memory/career-timeline.md`** — the full Career Journey Document:
  timeline table, motivations, transitions, the "Spark" for each pivot.
- **`shared/question_bank.yaml`** — the curated bank of real application
  questions sourced from currently-open job postings (built and
  refreshed via `references/question-bank-pipeline.md` and its crawler
  script, not hand-written). This skill reads it in Phase 1.5; it never
  writes to it — the bank's own curation process is a separate,
  quarterly-cadence job, distinct from this skill's per-run cycle.
- **`memory/star-story-bank.md`**'s variant table extension — per
  `references/answer-variants.md`, several bank questions carry more than
  one valid answer depending on company stage, seniority of the role, or
  other context. Those live as extra rows under the same story entry,
  not as separate stories.
- **Holographic memory layer** (optional, config-gated — off by default)
  — a parallel, atomic-fact layer alongside `star-story-bank.md`/
  `domain-knowledge.md`/`career-timeline.md`, not a replacement for any
  of them. See `references/holographic-memory-layer.md` before turning
  this on — it documents a real, tested limitation in the `contradict`
  action worth knowing before trusting it for anything.

Large narrative content stays in these dedicated files rather than
MEMORY.md/USER.md, because Hermes caps those at roughly 800 and 500
tokens respectively — they're for what must always be in context, not
for the full story bank. Skills that need the full bank load these files
as references, same pattern as any other skill's `references/` folder.

## Process

### Phase 0 — Target profile (run before everything else)

Produce `shared/target-profile.yaml` and the corresponding `USER.md`
bullets together, in one pass:

1. **Auto-suggest**: draft candidate values from Kene's resume/portfolio/
   notes and, if he mentions it, his recent job-search history — title
   variants he's actually held or applied to (`source: held` /
   `source: applied`), an inferred seniority band, a plausible salary
   floor for that band/market. Present these as suggestions, never write
   them yet.
1.5. **Adjacent title expansion** (runs after Phase 1 ingestion has
   populated `domain-knowledge.md` and the STAR bank, so this step has
   real evidence to reason from — not a first-pass guess): cross-reference
   Kene's actual skills, scope of responsibility, and STAR stories against
   `references/title-taxonomy.md`'s title-profile database to surface
   titles he's **never held or applied to** but could credibly target —
   e.g. "you've never held 'Product Marketing Manager,' but your STAR
   bank shows go-to-market messaging work across two stories and
   stakeholder-facing launches in a third — add this as a target title
   variant?" Each suggestion carries `source: taxonomy_suggested`, a
   `confidence` score, and a one-line `rationale` citing the specific
   evidence — never just the title on its own. Same rule as everything
   else in this phase: suggest, never write until Kene confirms. This
   only widens what `01-job-discovery` searches *for*; it changes nothing
   about `09-risk-tactics-gate`'s evidence requirement at application
   time — a taxonomy-suggested title still has to pass the CV-title-
   matching check on its own merits before it's ever displayed on a
   resume for a specific posting. Full method in
   `references/title-taxonomy.md`.
2. **Manual confirm/override**: ask Kene to confirm or correct each
   field — this is the one place in the pipeline where a short, direct
   Q&A ("remote-only, or hybrid okay? visa sponsorship required, yes/no/
   don't know yet? how should job discovery search — only declared
   sources, or also a broader open-web sweep?") is faster and more
   honest than trying to infer it. `discovery_mode` gets asked here
   alongside the rest — see `shared/target-profile.yaml.template`'s
   comments for the exact options to present. `fidelity_mode` gets its
   own dedicated question in Phase 0.5, immediately after — that's a
   risk trade-off worth explaining properly on its own, not folded into
   this quick pass.
3. **Write only after confirmation**, same as every other fact this
   skill handles (Rule 5). Stamp `last_confirmed_at`.
4. **Re-run cadence**: once at first-time setup, and again only on an
   explicit trigger — Kene asks to update it, or `03-resume-match`/
   `09-risk-tactics-gate` surfaces a repeated mismatch pattern that
   suggests the profile has drifted. This is deliberately *not* a
   background watcher on every memory change: target-profile facts
   (salary floor, visa status, title ambitions, discovery mode) are
   deliberate, relatively rare decisions Kene should consciously make,
   not something silently re-inferred in the background. A
   repeated-mismatch signal should prompt Hermes to *suggest* a re-run in
   chat, not trigger one unattended. Adjacent-title expansion specifically
   also re-runs whenever `references/title-taxonomy.md`'s database
   refreshes and flags a new high-confidence match against Kene's existing
   evidence — surfaced as a suggestion the next time Phase 0 runs, never
   applied unattended. Fidelity mode has its own, separate re-run rule —
   see Phase 0.5 and "When to re-run" below.

### Phase 0.5 — Fidelity mode (run once, right after Phase 0)

This is a preference, not a fact about Kene's career — so unlike every
other field in this file, there's nothing to auto-suggest from the
resume. Ask directly, and explain before asking, using something close
to the wording below (adapt tone, keep the content):

> `09-risk-tactics-gate` checks every claim this pipeline adds to a
> resume, cover letter, or answer — exact phrases copied from the
> posting, a matched job title, a skill pulled from "related experience"
> — against your actual documented history. Three ways it can handle a
> claim it can't verify:
>
> **Strict** (the default): anything it can't back up with a real line
> from your resume, portfolio, or story bank just doesn't go out. It gets
> stripped or softened to something true, and logged as a gap for you to
> fill in later if you want to. Nothing unverifiable ever reaches an
> employer.
>
> **Balanced**: it can still apply a plausible claim it can't fully
> verify — but never quietly. It gets tagged UNVERIFIED in the review
> you already see before every send, so you're the one deciding, claim
> by claim, not the pipeline deciding for you.
>
> **Embellish**: the same plausible-claim latitude as Balanced, but the
> UNVERIFIED tag is recorded for your own audit trail rather than held
> up as a separate approval-time flag each time. You're trusting the
> pipeline with the gray area up front, by choosing this mode, instead
> of reviewing each one individually.
>
> Which do you want as your default? You can change this anytime by
> asking me to re-run this step.

**Side-by-side, so the choice is concrete rather than abstract** — same
posting, same gap (JD wants "stakeholder management," Kene's resume/
story bank has nothing that directly says that):

| | `strict` output | `balanced` output | `embellish` output |
|---|---|---|---|
| Resume bullet | Left as-is; no stakeholder-management line added. | May add a bullet along the lines of "Managed cross-functional stakeholder relationships across product and engineering" if that's a plausible read of documented project work — never invented from nothing. | Same as `balanced` — added if plausible, never invented from nothing. |
| Change-log Kene sees | `[FAIL] "Stakeholder management" — no evidence found, left as genuine gap` | `[UNVERIFIED] "Stakeholder management" — no direct evidence, applied anyway — you're vouching for this one yourself` | Same `[UNVERIFIED]` line, recorded for the audit trail — but `10-approval-and-submit` doesn't hold up approval on it the way `balanced` does. |
| `open_gaps` table row | Same entry logged regardless of mode. | Same entry logged regardless of mode. | Same entry logged regardless of mode. |
| What Kene is approving | A resume that says only what's already backed by memory. | A resume with one clearly-marked claim he's personally standing behind, unbacked by a logged story — reviewed and vouched for at approval time. | A resume with one clearly-logged claim he already agreed, by choosing this mode, to stand behind without a separate per-application review. |

Every mode still runs the check — see `09-risk-tactics-gate`'s own
"Fidelity mode" section for exactly how the branch works downstream.
What's genuinely at stake in the choice: `strict` means every claim
could hold up if an interviewer asks "tell me more about that" — because
every claim traces to something real. `balanced` and `embellish` trade
some of that certainty for a fuller-looking application on genuine
gray-area skills; the risk they introduce is specifically an
interview-credibility risk, on whatever's tagged UNVERIFIED, not a
paperwork risk — it doesn't get caught by an ATS, it gets caught by a
follow-up question from a human. `balanced` keeps Kene reviewing that
trade-off application by application; `embellish` means he's already
made the call in advance, for every application, until he changes the
setting. That's Kene's call to make with the trade-off named plainly,
not a default the pipeline should quietly pick for him.

Write the choice to `shared/target-profile.yaml`'s `fidelity_mode`
field, stamp `last_confirmed_at`, only after he confirms — same Rule 5
discipline as every other fact this skill writes. If he doesn't have a
strong preference, `strict` is the sensible default to write, not
`balanced` or `embellish` — those should be something someone opts into,
not defaults into by declining to answer.

### Phase 1 — Ingestion

Read base resume, portfolio, any notes Kene provides.

### Phase 1.5 — Question-bank cross-reference & gap analysis

Full method in `references/gap-analysis-engine.md`; summary here:

Before interviewing Kene about anything, silently attempt to synthesize
an answer to every *relevant* question in `shared/question_bank.yaml`
(relevance filtered against `shared/target-profile.yaml` — don't even
attempt industries/stages he isn't targeting) from what Phase 1 just
ingested plus existing memory. Score each attempt for
schema-satisfying confidence, exactly the bar Phase 3 already uses for
the Quantification gate. This step exists specifically to keep the
interview short: it's what lets Phase 3 ask only about genuine gaps
instead of walking the whole bank out loud.

- **High confidence** → do not ask; queue for the batched confirmation
  step at the end of Phase 4 instead of an interview turn.
- **Low confidence, relevant** → this is what actually populates Phase
  3's worklist, alongside the existing gap sources (unexplained
  transitions, missing STAR categories, quantification gaps).
- **Low relevance** → log for the bank's own coverage report; never
  surfaces to Kene.

For any bank question tagged with `variant_dimensions`
(`references/answer-variants.md`), score and gap-check each relevant
variant separately — a question can be high-confidence for one variant
(e.g. the enterprise version of "why do you want to work here") and a
genuine gap for another (the early-stage-startup version), and only the
latter goes to Phase 3.

Questions tagged `jurisdiction_dependent: true` skip this scoring
entirely — those are `shared/target-profile.yaml` fact lookups, not
narrative gaps, and a missing one routes to a one-line profile update,
never to an interview turn (`references/gap-analysis-engine.md`).

### Phase 2 — Analysis

Map career timeline, flag every un-explained transition as a gap (the
"Spark" check), flag missing STAR categories — Team Conflict and
Failure/Recovery are almost never in a resume and are explicitly checked
for.

**Quantification gate.** For every achievement surfaced during ingestion
or the interview, check whether it already matches what downstream
skills actually need to use it:

- `05-resume-customizer` Phase 5 requires a **number** on every major
  bullet where evidence supports one — percentage, dollar amount, time
  saved, records processed, team size, or scope.
- `06-cover-letter`'s formula (paragraph 3, "The Story") requires **one
  numbered example** — its own reference example is "built dashboards
  that reduced reporting time by 30%," not "I have dashboard experience."
- `08-application-qa` only ever pulls a story that already exists in the
  bank verbatim — it does not invent detail on the spot — so if the bank
  entry is vague, every answer built from it inherits that vagueness.

If Kene states an achievement in vague terms ("grew sales a lot,
quickly, and it helped revenue"), that is a **flagged gap**, exactly like
an unexplained transition — not something to write to the bank as-is and
let a downstream skill discover the gap later. Note precisely what's
missing (the metric, the timeframe, or the downstream result) so the
interview loop asks for the specific missing piece, not a repeat of the
whole story.

The only acceptable resolution other than a real number is Kene
explicitly confirming no number exists or was ever tracked — that's a
legitimate answer (not every achievement is quantifiable, especially in
the Team Collaboration & Conflict category), and it gets written as an
honest qualitative claim, not left as an open gap forever.

### Phase 3 — Interview loop

Max 3 specific questions per turn, never generic ("What was the specific
conflict during the Rice Anchor project?" not "Tell me about your
leadership"). For a quantification gap specifically, ask for the exact
missing figure(s) directly ("What was the percentage growth, and over
what time period?"), not a re-ask of the whole story. Continue until
every target document has enough material **to satisfy the schemas above
verbatim** — not a subjective "enough," but "05/06's own requirements are
met, or Kene has explicitly said no number exists" — then ask for
confirmation before writing anything.

The worklist itself now comes from Phase 1.5 (question-bank gaps) as
well as the sources already listed above — same 3-per-turn discipline
applies regardless of source. When a gap has multiple relevant
variants (`references/answer-variants.md`), ask for all of them in one
batched turn ("give me your answer to X for: an early-stage startup, a
big established company, and a mission-driven org") rather than
spreading one underlying question across several separate turns — this
is what keeps a large question bank from turning into an hours-long
interview.

**Input mode**: questions are delivered as text by default (skimmable,
rereadable — several bank questions are dense enough to benefit from
that). Kene can answer by typing or by sending a voice note
interchangeably, turn by turn, with no mode switch required — Hermes
transcribes incoming voice messages automatically whenever `stt` is
configured, regardless of the reply-mode setting. See
`references/voice-interview-mode.md` for setup and honest accuracy
expectations by language; this is an available option throughout, not a
separate flow to opt into.

**Voice answers containing a number get echoed back before anything is
treated as final** — this interview's entire point is feeding exact
figures into the Quantification gate above, and a mis-transcribed "25%"
heard as "225%" would silently corrupt the one thing that gate exists
to protect. Any voice-derived answer containing a number, date, or
percentage gets read back as transcribed text ("Just to confirm — 25%
growth over 6 months, is that right?") before Phase 4 writes it
anywhere. Same "confirm before writing" discipline the rest of this
skill already uses, just applied at the transcription boundary too, not
only at the final write.

### Phase 4 — Synthesis

Only after Kene confirms, write the confirmed material into the files
above. Nothing goes into memory from inference alone — inferred "Key
Learnings" get surfaced as a question in the interview loop, not written
straight to memory. A STAR bank entry does not get written with an
unresolved quantification gap silently left blank; it either carries the
number, or carries Kene's explicit "no number exists" confirmation.

**If the Holographic memory layer is configured** (optional — see
`references/holographic-memory-layer.md`, off by default): once a story
is confirmed and about to be written, first `fact_store(action="probe",
entity='"<Project/Company Name>"')` (quote the name — see that
reference file's entity-extraction note) to pull every existing fact
already linked to this project or company, and **read the results
directly** for anything that conflicts with the claim about to be
written — a different duration, team size, or outcome number for what's
supposed to be the same project. This direct read is the actual check;
`contradict` alone is not reliable for exactly this case (see that
file's "contradict trap" section — tested, not assumed). Only after that
read comes back clean does this count as confirmed enough to write.
Then decompose the finalized story into its 2–4 atomic claims and
`fact_store(action="add", category="project")` each one, and run
`fact_store(action="contradict", category="project")` as a supplementary
second pass before moving on (the tool doesn't expose a tunable
threshold — see the reference file for why that doesn't change the
conclusion above).

## When to re-run

- Before the pipeline's first-ever use.
- Whenever `03-resume-match` or `09-risk-tactics-gate` hits a gap with no
  supporting evidence in memory — query `open_gaps WHERE resolved = 0`
  first; that's the standing worklist, not something to rediscover from
  scratch each time. Once Kene supplies the missing evidence (or
  explicitly confirms none exists) and it's written into the STAR bank /
  `domain-knowledge.md`, mark that row `resolved = 1, resolved_at = now()`
  — the row stays as a historical record, it just stops showing up in the
  worklist.
- Whenever Kene mentions a new project, story, or transition unprompted.
- For the target profile specifically: only on explicit request or a
  suggested re-run after a repeated-mismatch signal (see Phase 0.4) —
  never as a background trigger on arbitrary memory changes.
- For fidelity mode specifically: only on explicit request ("switch me
  to balanced," "go back to strict"). There is no signal this skill
  should ever infer a fidelity-mode change from — it's a deliberate,
  named preference, not something a mismatch pattern implies.
- Whenever `shared/question_bank.yaml` refreshes (quarterly, per
  `references/question-bank-pipeline.md`) — re-run Phase 1.5 only, as a
  quick "N new gaps found" pass, not a full re-interview. Also re-run
  Phase 1.5 immediately, for the single question involved, whenever
  `03-resume-match` or `09-risk-tactics-gate` hits a live application
  question that isn't in the bank at all yet.

## `profile_stage` — a second shape for Phases 1-4

`onboarding` sets `target-profile.yaml`'s `profile_stage` field
(`experienced` | `first_time` | `returning_after_gap` | `career_pivot`)
before Phase 0 runs in earnest. For `first_time` specifically:

- **Phase 1's ingestion sources widen** beyond resume and portfolio, to
  school records, coursework, extracurriculars, volunteer and community
  work, and self-taught skills.
- **Phase 2's quantification gate applies at the same rigour** to that
  wider source list. Not a relaxed bar on wider sources — the same bar,
  more places to meet it from.
- **`memory/interests-profile.md` elicitation moves from a deferred,
  advanced-tier pass to co-primary with the STAR bank** in the same
  first session.

The other three stages leave Phases 1-4 unchanged. Full reasoning and
the rest of what shifts pipeline-wide is in
`onboarding/references/starting-out-track.md`; this skill's part is the
source list and sequencing, not the whole adaptation.

Ownership works as it does with `16-career-pulse`: `capability:interests_profile`
runs the elicitation and proposes entries — first-pass interview plus
ongoing journal-surfaced candidates — and this skill remains the only
one that writes `interests-profile.md`. Rule 5 unchanged. One genuine
departure worth stating plainly, because it breaks the pattern every
other memory file here follows: **`interests-profile.md` entries carry no
quantification or evidence bar.** That skill's "Admission criteria"
section explains why importing the STAR-bank standard would be the wrong
call.

## Derived indexes this skill keeps current

Two mappings are maintained here rather than recomputed by their
consumers, both built as batched propose-and-confirm passes rather than
new interviews, and both re-derived on the existing career-event cascade
that already fires Phase 1.5 — one more consumer of that trigger, not a
second trigger to keep in sync:

- **Content Model mapping** (`references/content-model-overlap.md`) —
  already-confirmed `domain-knowledge.md` and STAR-bank entries mapped
  onto O*NET's standardised Content Model elements. Feeds
  `capability:career_planning`'s mode (c). This skill does not compute the
  overlap scores — that skill does, as an `execute_code` job — it only
  owns keeping the mapping current.
- **RIASEC vector**
  (`capability:interests_profile/references/riasec-mapping.md`) — same
  batched-confirm, same re-derivation trigger.

Both follow the split that governs everything else here: this skill
writes confirmed facts, other skills read them.

## Document intake — PDFs (S1)

Phase 1 ingests the resume and portfolio. Both usually exist as PDFs,
and nothing said how one gets read.

Use `productivity/ocr-and-documents`: `pymupdf` for a text layer,
`marker-pdf` for scanned or image-only documents. Same ordering rule as
`02-jd-parser` — text layer first, OCR as fallback, and flag when OCR
was used.

The flag matters more here than anywhere else in the pipeline. Phase 2's
quantification gate asks whether a claim carries the number that makes it
real. An OCR'd resume can drop or corrupt exactly those numbers — a
"32%" that reads as "3.2%" is worse than one that failed to read at all,
because it is confidently wrong and will be reused for years. When a
figure comes from OCR, confirm it against Kene before it is written under
Rule 5, rather than treating it as ingested fact.

Offer letters at `10-approval-and-submit` are the third PDF surface, and
the same rule applies with more force: an OCR'd compensation figure is
never confirmed fact.

## Gap-driven elicitation from interview prep

`capability:interview_prep` Part 3b routes questions with no matching STAR entry
here. These are the highest-yield elicitation prompts available, because
the gap is evidenced rather than guessed: a real interviewer for a real
application is likely to ask this, and there is nothing on file.

Handle them as a normal Phase 2 elicitation with two differences:

- **Lead with the question's structure**, not with an open prompt.
  "Tell me about a disagreement" gets a vague answer; "this question is
  testing whether you can disagree without escalating, and it needs your
  reasoning *at the time* rather than with hindsight" gets a usable one.
- **Offer candidates from existing records** — journal entries, timeline
  events, adjacent STAR entries that might extend. Recognition is easier
  than recall, and the journal exists precisely so this does not depend
  on memory.

Same quantification gate as everything else here: a confirmed story needs
the number or the outcome that makes it real. Same Rule 5 write path. The
resulting entry is a permanent addition to the bank, not an
interview-specific artifact — which is what makes this worth doing
properly rather than answering the question and moving on.

## Reference files

- `references/qmd-retrieval-layer.md` — cross-corpus search over the
  research caches: scope, which collections, why the fact store and
  taxonomy index are excluded, and how index staleness is handled.
- `references/star-bank-aging.md` — the fixed reading budget over the STAR
  bank: recent stories verbatim, older ones collapsed, every story still
  represented.

- `references/title-taxonomy.md` + `references/title_taxonomy_builder.py` —
  how the title-profile database behind Phase 1.5's adjacent-title
  expansion gets built, embedded, queried, and kept fresh.
- `references/question-bank-pipeline.md` + `references/question_bank_crawler.py`
  + `templates/seed_companies.yaml` — how `shared/question_bank.yaml`
  gets built and refreshed from real, currently-open postings.
- `references/answer-variants.md` — which contextual dimensions
  (company stage, seniority, industry, etc.) actually change a good
  answer, and how variant answers are stored.
- `references/gap-analysis-engine.md` — the full Phase 1.5 method: how
  relevance and confidence combine to decide what actually becomes an
  interview question.
- `references/voice-interview-mode.md` — Hermes's built-in voice
  capabilities, honest accuracy expectations by language, and setup for
  answering interview questions by voice note.
- `references/holographic-memory-layer.md` — the optional atomic-fact
  layer alongside the STAR bank: setup, the fixed category enum, a real
  entity-extraction quirk and its fix, and a tested limitation in the
  `contradict` action worth knowing before trusting it for anything.
