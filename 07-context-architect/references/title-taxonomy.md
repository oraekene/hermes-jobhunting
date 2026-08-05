# Title Taxonomy — Full JD-Profile Database for Adjacent-Title Expansion

Origin: Kene's request that Phase 1.5's adjacent-title expansion not just
match on title strings, but cross-reference his actual skills, scope, and
experience against full job profiles per title — requirements, skills,
seniority level, experience/education level, and other traits, at a scale
of "every job title in existence," searched via embeddings for the most
accurate retrieval.

**One honest framing note before the method**: "every job title in
existence" isn't a clean, finite list — informal/company-specific titles
("Growth Hacker," "Chief Vibes Officer") are unbounded, and procedurally
generating title strings (seniority prefix × function word × specialism)
produces plenty of combinations nobody has ever actually posted. The
useful version of "very large" isn't a round number chosen up front; it's
however many *real* titles the method below actually surfaces — which
comfortably reaches the tens of thousands once the crosswalk and the
crawl layer are both running, without ever inventing a title nobody uses.

## Build method: hybrid, not crawl-only or database-only

You asked directly whether to (a) crawl postings and rank by frequency,
(b) anchor on an existing structured database, or (c) something else.
**(c), and it's actually (a) and (b) layered, not a third separate
method** — each one alone has a real failure mode the other covers:

- **Crawl-only (a) fails on validation and cost at this scale.**
  Frequency-ranking raw postings sounds objective, but job postings are
  *marketing copy*, not job analysis — a poorly-written posting that
  keyword-stuffs "rockstar," "ninja," or a laundry list of nice-to-haves
  pollutes the frequency count exactly as much as a well-written one.
  Doing this cleanly for tens of thousands of titles, from scratch, with
  no ground truth to validate against, is a large, expensive, and
  noisy undertaking.
- **Database-only (b) fails on granularity and freshness.** Structured
  government/EU occupation databases are well-validated but coarse —
  they classify by *occupation*, not by the specific title strings
  companies actually post today ("Senior Growth Product Manager" vs.
  "Product Manager, Platform" both collapse to one O*NET code), and their
  update cycles are slower than the market's.
- **The hybrid**: anchor every profile on a structured occupational
  database (the validated, stable base layer), then use the *existing*
  crawl infrastructure this pipeline already built for the question bank
  (`question-bank-pipeline.md`, `question_bank_crawler.py`) to layer
  current-market signal on top — specific tools/frameworks, salary
  ranges, and the actual title strings employers are using right now.
  Two layers, kept distinguishable, not merged into one undifferentiated
  blob.

## Layer 1 — the structured anchor: O*NET (+ ESCO for non-US/multilingual)

**O*NET** (developed for the US Department of Labor by the North Carolina
Department of Commerce, free public Web Services API, no key required for
basic access) is the right anchor:

- ~1,016 detailed occupations, each covering a cluster of real job
  titles — the database crosswalks each occupation to its actual
  alternate/sample titles, so the ~1,000 structured occupations expand to
  well over 50,000 specific title strings without any crawling at all.
- Each occupation already carries almost everything Kene asked for in a
  "full profile": Tasks, Knowledge, Skills, Abilities, Work Activities,
  Work Context, Job Zone (a five-to-four-level education/experience/
  training banding — exactly the "seniority level" and "experience/
  education requirements" fields Kene wants), and Related Occupations.
- It already does frequency-based market signal for one specific field:
  "Hot Technologies" are software/tools flagged specifically because
  they show up often in real employer job postings — this is O*NET's own
  version of method (a), already done, already validated, for the one
  field where postings genuinely are the right source (specific tools),
  vs. the fields where a validated occupational analysis is the right
  source (tasks, abilities, education banding).
- It updates on a rolling basis (hundreds of occupations refreshed every
  few months, full database releases a few times a year) — not
  instantaneous, but far more current than "static reference book."
- It crosswalks to **ESCO** (the EU's multilingual skills/competences/
  occupations classification) directly — worth pulling in specifically
  for non-US postings or when Kene's search expands outside the US/UK,
  since ESCO's skills taxonomy is built to be language-independent in a
  way O*NET's isn't.

Pull this via O*NET's Web Services API (`services.onetcenter.org`) into a
local `title_taxonomy_core.jsonl` — one record per O*NET-SOC code, with
its full content-model fields and its list of alternate titles. This is
the base layer every profile is built from, and it's the layer that never
gets silently overwritten by a crawl — crawl-sourced fields live in a
separate layer (below) precisely so a bad crawl batch can never corrupt
the validated base.

## Layer 2 — market-freshness enrichment via the existing crawl

For each O*NET occupation Kene might plausibly care about (filtered by
relevance the same way Phase 1.5 already filters the question bank —
don't enrich occupations wildly outside his domain), run the *existing*
crawl infrastructure against its representative title strings:

- Reuse `question_bank_crawler.py`'s ATS fetchers (Greenhouse, Lever,
  Ashby, extendable to Workable/Recruitee/Personio) plus Adzuna (free
  tier, ~1,000 calls/month, 16 countries, structured JD text + salary) —
  same sources already vetted for the question-bank crawl, now pointed at
  title/skill extraction instead of screening-question extraction.
- From each batch of live postings under a given occupation, extract:
  specific tools/technologies mentioned (supplements O*NET's own Hot
  Technologies with anything newer than its last update), a rough salary
  band, and the *exact title strings* actually in use this month — this
  is where "Senior Growth Product Manager" as a real, current string
  enters the taxonomy, distinct from the O*NET "Marketing Managers"
  occupation it rolls up to.
- Write these as a `market_signals` block on the occupation's record —
  never overwrite or merge into the O*NET-sourced fields. Every field in
  a profile stays tagged with its provenance (`onet` / `esco` /
  `market_signals`), the same discipline `title_variants` entries already
  use (`source: held` / `applied` / `taxonomy_suggested`).

## Record schema

```yaml
onet_soc_code: "11-2021.00"
onet_title: "Marketing Managers"
alternate_titles_onet: ["Marketing Director", "Brand Manager", "..."]
job_zone: 4   # education/experience/training band, per O*NET's own scale
tasks: ["...", "..."]
knowledge: ["...", "..."]
skills: ["...", "..."]
abilities: ["...", "..."]
education_typical: "Bachelor's degree"
experience_typical: "Several years in a related occupation"
esco_crosswalk: "http://data.europa.eu/esco/occupation/..."
market_signals:
  last_crawled_at: "2026-07-01"
  current_title_strings_seen: ["Senior Growth Product Manager", "..."]
  tools_seen: ["...", "..."]           # supplements onet hot_technologies
  hot_technologies_onet: ["...", "..."]
  salary_band_observed: {currency: "USD", low: 0, high: 0, sample_size: 0}
  source_count: 0
embedding_id: "tt_0001"   # row key in the vector store, see below
```

## Storage and retrieval: correcting an assumption, then the real options

**Worth being precise here before recommending anything**: Hermes's core,
built-in long-term memory is deliberately keyword-based (SQLite FTS5 /
BM25) — its own design explicitly avoids vector databases and embeddings
for the default memory path. A 50,000-row semantic taxonomy doesn't get
vector search "for free" from that system. There are two real ways to add
it, both genuinely available, with a real tradeoff between them:

- **`mlops/chroma`** (Hermes's bundled optional skill, `pip install
  chromadb`) — turnkey embedding database purpose-built for exactly this,
  least wiring to get working, but it's a new dependency/service surface
  on top of everything else this pipeline already runs.
- **`fastembed` + `sqlite-vec`** (a SQLite extension that adds vector
  columns/ANN search to an ordinary SQLite file) — no separate service,
  fully local, and — this is the reason to prefer it here specifically —
  every other piece of state in this pipeline already lives in one
  SQLite file (`applications.db`); adding the taxonomy as a `sqlite-vec`
  table keeps that same one-file, zero-server architecture instead of
  introducing a second storage paradigm. At this scale (tens of
  thousands, not millions, of rows) brute-force/ANN search in sqlite-vec
  is comfortably fast enough — this isn't a case where Chroma's extra
  machinery buys real performance headroom.

**Recommendation: `fastembed` + `sqlite-vec`**, specifically for
consistency with how the rest of this pipeline is built, not because
Chroma is worse in general. If Kene is already comfortable with Chroma
for something else, that's a fine reason to prefer it instead — this
isn't a close-call-either-way situation reversed by convenience.

```
pip install fastembed sqlite-vec
```

- One embedding model run once per taxonomy record (concatenate tasks +
  knowledge + skills + abilities into one text blob per occupation,
  embed with a small local model — `BAAI/bge-small-en-v1.5` via
  `fastembed` is a reasonable default: no API key, ~130MB, CPU-friendly).
- Store alongside `title_taxonomy_core.jsonl` in a `title_taxonomy.sqlite`
  file, one `sqlite-vec` virtual table (`vec0`) keyed by `embedding_id`.

## The actual cross-reference (Phase 1.5's adjacent-title expansion)

1. Build one embedding from Kene's current `domain-knowledge.md` +
   STAR-bank entries + resume — same embedding model as above, so the
   vectors are comparable.
2. Query the `sqlite-vec` table for the top-K nearest title profiles by
   cosine similarity.
3. For each candidate above a confidence threshold, check it against
   `shared/target-profile.yaml`'s existing `title_variants` — skip
   anything already listed with `source: held` or `source: applied`
   (nothing to suggest, he already covers it).
4. For genuinely new candidates, draft the suggestion with a rationale
   that names the *specific* matching evidence (which STAR story, which
   domain-knowledge entry) — never just "this title scored 0.81," always
   "this title scored high because your STAR bank shows X."
5. Hand the drafted list to Phase 0 step 1.5 as written in
   `07-context-architect/SKILL.md` — suggest only, confirm before write,
   same as every other fact this skill touches.

## Calibration-aware widening

At the start of any Phase 1.5 run, read
`shared/dynamic-target-calibration.yaml`'s `employment_status` and
`auto_relax_schedule`:

- If `employment_status` is `unemployed` or `between_roles` and enough
  weeks have accumulated to reach an `auto_relax_schedule` step carrying
  `also_widen_title_taxonomy_similarity_threshold: true` — the 26-week
  step in the shipped template — the embedding-similarity threshold
  widens for that run. That surfaces genuinely more tangential adjacent
  titles, rather than merely accepting lower scores on the same titles
  the run already found.
- Otherwise Phase 1.5 runs exactly as specified above. This only ever
  widens the net, under a specific and auditable condition; it never
  narrows it and changes nothing else about how Phase 1.5 works.

Every title variant this produces still passes through the same
confirm-before-write step required everywhere else in this file. What
changes is how wide the net is cast, not whether a human confirms what
it catches.

Confirmed `title_variants` land in `target-profile.yaml` as documented
above, and `01-job-discovery` reads that same field — which is why it
needs no copy of the calibration logic of its own.

### When two producers propose the same title (R5)

Three things now write `title_variants`, all through the same
confirm-before-write gate: Phase 1.5's taxonomy expansion, calibration-
driven widening, and `19-career-path-planner`'s `path_planned` entries.
Three producers into one field is fine; three producers with no stated
precedence is how the same title arrives twice in one confirmation batch,
or how a confirmed entry gets its `rationale` silently overwritten by a
weaker one.

The rule is precedence by evidence strength, strongest first:

| Precedence | `source` | Why it wins |
|---|---|---|
| 1 | `held` | Kene actually held this title. Not a suggestion. |
| 2 | `applied` | He chose to apply under it — a decision already made. |
| 3 | `path_planned` | A deliberate target from a confirmed career-path plan. Intentional, but prospective. |
| 4 | `taxonomy_suggested` | Inferred from embedding similarity. Weakest, and the only one nobody decided. |

Three consequences:

- **A stronger source overwrites a weaker one's `rationale`**, and says so
  in the confirmation. A title that arrived as `taxonomy_suggested` and is
  later actually held becomes `held` — the record should reflect that.
- **A weaker source never overwrites a stronger one**, and never
  re-proposes a title already present at higher precedence. Silently
  dropping it is correct here: re-asking about a title Kene already
  confirmed is noise, not diligence.
- **Same-precedence collisions in one batch collapse to one proposal**
  with both rationales shown, not two confirmations for one title.

Precedence governs the *record*, never the gate. Every one of the four
still requires confirmation before it is written; nothing here creates a
path that writes `title_variants` unattended.

### A fourth `source` value

`title_variants` entries may now carry `source: path_planned` alongside
`held` / `applied` / `taxonomy_suggested`. It is proposed when Kene
deliberately decides to start actively searching for a target he built a
career path toward (`19-career-path-planner`'s Step 5), rather than
something the taxonomy noticed by itself or something he has already
done. Same confirm-before-write step; the only difference is what goes
in `rationale` — a pointer to the specific
`shared/career_path_plans/{plan_id}.md` it came from, not a
similarity explanation.

## Refresh cadence

Mirrors the question-bank pattern in `bank-refresh-automation.md`,
because the underlying problem is the same shape (a large curated
dataset that needs monthly light refresh and quarterly deliberate
re-crawl):

- **Monthly, automated, staged**: re-pull O*NET's incremental occupation
  updates (it publishes what changed), re-crawl `market_signals` only for
  occupations Kene's current target profile actually touches, diff
  against the live taxonomy, deliver as a digest — never auto-applied.
- **Quarterly, deliberate**: full re-crawl of `market_signals` across a
  wider occupation set (not just Kene's current targets — same
  "durability across profile pivots" reasoning `question-bank-pipeline.md`
  already uses for its own broad-crawl choice), plus a full O*NET
  database sync if a new full release shipped that quarter.
- **Immediately, either cadence**: when Kene's target profile changes
  significantly, or when Phase 1.5 keeps failing to find a good match for
  a title he mentions by hand — a sign of a genuine coverage gap in the
  taxonomy, not just a search-tuning problem.

## Reference files

- `title_taxonomy_builder.py` — pulls the O*NET base layer, runs the
  crawl-enrichment layer (reusing `question_bank_crawler.py`'s fetchers),
  builds embeddings, and exposes the `query` command Phase 1.5 calls.
