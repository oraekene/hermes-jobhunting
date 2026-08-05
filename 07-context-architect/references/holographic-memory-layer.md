# Holographic Memory Layer (optional, config-gated)

**Read this before turning this on.** Everything below was verified by
running the actual `plugins/memory/holographic` source from
`NousResearch/hermes-agent` directly — not by trusting its own
docstrings, several of which oversell what the code actually does. Where
that mattered, it's called out explicitly rather than smoothed over.

## What this is, and what it isn't

Holographic is one of Hermes's external memory providers
(`user-guide/features/memory-providers.md`) — local SQLite, FTS5, no
required dependencies (NumPy optional), entity resolution, trust
scoring, and HRR-based (Holographic Reduced Representation) compositional
retrieval. It runs **alongside** the built-in `MEMORY.md`/`USER.md`, never
replacing them — same as every other Hermes memory provider.

This is **not** a replacement for `memory/star-story-bank.md`. The
markdown file stays the actual narrative source of truth — it's what
`05-resume-customizer`, `06-cover-letter`, and `08-application-qa` read
full STAR stories from, and it's what carries the Quantified Outcome
discipline those skills require. Holographic adds a **parallel, atomic
layer**: the checkable claims *inside* a story (project name, company,
timeframe, the number itself) get stored as individual facts, which is
what makes them searchable, entity-linkable, and open to a consistency
check the flat markdown file can't offer on its own.

**Turn this on only if the STAR bank has grown past the size where
Kene (or whoever's maintaining it) can reliably eyeball it for
consistency.** For a small bank, reading the file is still faster and
more reliable than any of this.

## Setup

```bash
hermes config set memory.provider holographic
pip install numpy   # see "The contradict trap" below — do not skip this
```

Config lives in `config.yaml` under `plugins.hermes-memory-store`:

```yaml
plugins:
  hermes-memory-store:
    db_path: $HERMES_HOME/memory_store.db
    auto_extract: false   # see "Why auto_extract stays off" below
    default_trust: 0.5
    hrr_dim: 1024
```

This is a **third** SQLite database, distinct from `applications.db` and
distinct from the flat `memory/*.md` files — worth knowing so the three
data stores don't get confused with each other. `memory_store.db` holds
only what this layer explicitly adds via `fact_store`.

### Why `auto_extract` stays off

The plugin has a generic session-end auto-extraction pass (regex-matched
"I prefer X" / "we decided Y" patterns) meant for general assistant use.
It isn't tailored to career facts and isn't scoped to job-hunting
content — turned on, it would pull in noise from any ordinary
conversation in the same Hermes profile. Every fact this pipeline stores
here should be a deliberate `fact_store(action="add")` call from
`07-context-architect`, not something auto-harvested from ambient chat.

## The four things worth knowing before you rely on any of this

### 1. `category` is a fixed 4-value enum, not free text

`user_pref | project | tool | general` — that's the whole set, enforced
by the tool schema. This pipeline's mapping:

- **`project`** — atomic claims decomposed from STAR stories (the
  natural fit: STAR stories are specifically about projects/situations).
- **`general`** — atomic career-timeline/domain-knowledge facts that
  aren't project-shaped (a certification, a language, a work-
  authorization fact).
- **`user_pref` / `tool`** — not used by this pipeline today; reserved
  if a future use turns up rather than force-fit into them now.

### 2. Entity extraction is regex-based, from the fact's own text — and has a real quirk

Entities aren't tagged manually; they're extracted automatically from
whatever text you pass to `add`, by three patterns: multi-word
Title-Case phrases, anything in quotes, and "X aka Y" patterns. I tested
this directly and found a genuine gotcha: a sentence-**initial**
Title-Case word merges into the following entity phrase. `"The
Checkout Redesign project..."` extracts the entity as `"The Checkout
Redesign"` (with "The" glued on) — a *different* string from
`"Checkout Redesign"` extracted out of a sentence where it doesn't start
the sentence. Two facts about the literal same project can end up
linked to two different entity strings purely because of where the name
sits in the sentence, which quietly breaks entity-based lookup and
`contradict`'s entity-overlap check between them.

**Mitigation, verified**: wrap the entity name in double quotes inside
the fact text — `at Acme Corp, the "Checkout Redesign" project...` — the
quote-pattern extraction pulls a clean `"Checkout Redesign"` regardless
of sentence position. Do this for every project/company name when
writing a fact here.

### 3. The `contradict` trap — read this one twice

`contradict`'s own tool description calls this "automated memory
hygiene — no other memory system does this." I tested it directly
against exactly the case this feature was originally proposed for: two
facts about the same project stating a different duration ("took 3
months" vs. "actually took 6 months to complete," same project, same
company, near-identical phrasing otherwise).

**It found nothing.** Zero contradictions, at the default threshold and
at a threshold three times lower (tested by calling the plugin's
`retriever.contradict()` method directly in Python — see the note at
the end of the workflow below on why the actual `fact_store` tool can't
do this itself; the point of testing it this way was to check whether a
lower threshold would have caught this case at all, and it still
didn't). The reason is mechanical, not a bug:
`contradict`'s score is `entity_overlap × (1 − content_similarity)` —
it's built to catch facts about the same entity that are *worded very
differently* (two wildly different characterizations of the same
company, say), not a single specific detail changed inside otherwise
near-identical phrasing. Two sentences that share 90% of their words
still score as "similar" overall, even when the one word that differs is
the number that actually matters.

What it *did* catch, in the same test: two facts about the same company
with completely different framing ("is a mid-size logistics company" vs.
"went through layoffs, now a struggling early-stage startup") — that's
the case it's actually built for.

**Practical consequence for this pipeline**: don't treat `contradict`
finding nothing as "confirmed no conflicts." Use it as a supplementary,
low-cost second pass — not the primary check. The primary check is
described below.

### 4. NumPy availability changes behavior silently, and not the same way for every action

`probe`, `related`, and `reason` all degrade gracefully to a plain FTS5
keyword search when NumPy isn't installed — reduced precision, but they
still return something. `contradict` does not degrade — without NumPy
it returns an **empty list**, silently, with no error. If NumPy isn't
installed, every `contradict` call looks like "no conflicts found"
whether or not that's true. Install NumPy as part of setup, not as an
afterthought — this is the one action where skipping it produces a
result that looks identical to success.

## The actual workflow: probe-and-read first, `contradict` second

Given #3 above, the reliable consistency check is the model reading the
facts directly, not trusting an automated score. When
`07-context-architect` confirms a new or updated STAR story (Phase 2,
Quantification gate):

1. Decompose the confirmed story into 2–4 atomic facts — project/company
   name (quoted, per #2 above), role and timeframe, the quantified
   outcome itself — and `fact_store(action="add", category="project")`
   each one. `add` dedupes on exact content automatically (verified: a
   second identical `add` returns the existing `fact_id`, doesn't error
   or duplicate), so there's no need to check for an existing fact
   before adding — just add it.
2. **Before finalizing**, call `fact_store(action="probe", entity='"<Project
   Name>"', category="project")` (or `action="search"` if `probe` isn't
   turning up the right things) to pull every existing fact already
   linked to this project or company.
3. **Read what comes back and compare it to the new claim directly** —
   this is the actual check, not step 4. A returned fact stating a
   different duration, different team size, or a different outcome
   number for what's supposed to be the same project is the thing to
   catch here, and per #3 above, it's on you (the reading model) to
   notice it, not on `contradict` to flag it.
4. Then, as a supplementary pass — cheap, and it does catch a real
   category of problem even if not this one — run
   `fact_store(action="contradict", category="project")` and surface
   anything it flags too. **One more thing worth knowing**: the
   `fact_store` tool's own schema doesn't expose a `threshold`
   parameter — only `category` and `limit` reach the underlying method,
   so this always runs at the plugin's hardcoded default (0.3), not a
   tunable one. My own testing above used direct Python access to the
   plugin (to check whether a lower threshold would have caught the
   near-identical-phrasing case) — the pipeline itself can't do that
   through the tool interface, and doesn't need to: the finding stands
   regardless, since even the lower threshold I tested directly still
   missed it.
5. If step 3 or step 4 surfaces a genuine conflict, resolve it with Kene
   the same way any STAR-bank inconsistency gets resolved — the
   markdown file is still the fix of record. Then reconcile the
   fact-store side: `fact_store(action="update", fact_id=..., ...)` or
   `action="remove"` on whichever atomic fact turned out to be wrong.

## Where else this gets used (lightly, not a rewrite)

`05-resume-customizer`, `06-cover-letter`, `08-application-qa`, and
`13-interview-prep` can each optionally supplement their STAR-bank read
with `fact_store(action="probe")` or `action="reason"` (the latter for
"facts connected to both this company AND this specific skill," e.g.)
for a specific company/project — a chance to surface an atomic fact that
isn't the headline story that would otherwise get picked. This is a
supplement, not a replacement for reading the story bank directly, and
none of these skills should block on it — if Holographic isn't
configured, or `fact_store` returns nothing, proceed exactly as before.

`fact_feedback(action="helpful"/"unhelpful", fact_id=...)` is **required
once this layer is configured**, not the optional extra it was described
as through v24.

The reasoning is short: trust score is the only ranking dimension this
provider has, it starts at 0.5, and this call is the only thing that
moves it. Left unwired — which it was — every fact sits at its default
forever, and the layer degrades to relevance-ranked retrieval over an
undifferentiated store. That is what it was adopted to improve on. The
signal is produced on every run whether or not anything records it, so
the real choice is between recording it and throwing it away.

`11-analytics-and-learning` step 6 owns the call, batched per cycle. The
grading rule lives there and is deliberately conservative about
`unhelpful`, because the feedback is asymmetric (+0.05 vs −0.10): only a
fact Kene edited out, or one whose claim `08-application-qa` or
`09-risk-tactics-gate` rejected, counts against it. A rejected
application does not — most rejections have nothing to do with which
story was chosen, and rating on outcome alone would walk the entire bank
toward zero on noise.

**Turning it off is a config choice with a stated cost.** Set
`memory.fact_feedback: false` if you want it off; the layer keeps
working and trust scores stay flat forever. That is a legitimate
preference and it should be a decision, not a default nobody revisited.

## What this does not change

Rule 5 (`shared/pipeline-rules.md`) still applies exactly as written —
`07-context-architect` is the only skill that writes here, same as
`MEMORY.md`/`USER.md`/the STAR bank, and only after Kene has confirmed
the underlying fact. This layer is a different *storage location* for
facts context-architect already had authority to write, not a new
write-path for anyone else.

## Where this sits relative to the other retrieval layers

Hermes ships nine memory providers and `memory.provider` takes exactly one
value. **This package's choice is Holographic**, for the reasons above:
local, free, no external dependency, and `contradict` plus `probe` are the
two capabilities this domain actually needs. Honcho, Mem0, Hindsight and
the rest are alternatives, not companions — do not configure two.

qmd is a different thing and composes rather than competes. It is a
read-only search layer over the research cache directories; it has no fact
model, no contradiction detection and no write path. See
`qmd-retrieval-layer.md` for its scope and the reasons the fact store, the
applications DB and the taxonomy index are deliberately left out of it.

`star-bank-aging.md` covers the third layer — the fixed reading budget over
`memory/star-story-bank.md` — which is neither a fact store nor a search
index but a compression schedule.
