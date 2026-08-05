# The qmd retrieval layer

Search across the research caches. Read-only, additive, and deliberately
scoped: qmd finds documents, it does not store facts and it does not
manage anything.

## The problem it solves

This package generates five growing markdown corpora:

```
shared/company_research_cache/{company_slug}.md
shared/individual_research_cache/{handle_slug}.md
shared/interview_intel_cache/{title_slug}.md
shared/role_transition_intel_cache/{target_title_slug}.md
shared/career_path_plans/{plan_id}.md
```

Every one is written once and read back **only by the exact key that wrote
it**. Nothing in the package queries across any of them. After a year of
daily discovery that is hundreds of documents, each individually
retrievable and collectively opaque.

Three consequences, and the third costs real money:

1. Cross-corpus questions are unanswerable — "which researched companies
   describe themselves as remote-first", "have I seen this interview
   format before".
2. `interview_intel_cache` is keyed by `title_slug`, so "Analytics Lead",
   "Head of Analytics" and "Analytics Manager" build three
   non-communicating caches with heavily overlapping content. The
   role-general scope was specifically meant to be reusable; slug keying
   defeats that.
3. `individual_research_cache` is keyed by handle. The same recruiter as
   `@jane_smith` on X and `jane-smith-recruiting` on LinkedIn produces two
   files, two research passes, and **two enrichment API spends**, with no
   signal they are one person. Exact-key lookup structurally cannot catch
   this, and it recurs on every duplicate.

## Scope — three collections, nothing else

```bash
qmd collection add shared/company_research_cache    --name company-research
qmd collection add shared/individual_research_cache --name people-research
qmd collection add shared/interview_intel_cache     --name interview-intel

qmd context add qmd://company-research  "Per-employer research: mission, stage, news, values language, candidate and employee sentiment, reported interview style"
qmd context add qmd://people-research   "Per-person research on recruiters, hiring managers and cold-outreach targets"
qmd context add qmd://interview-intel   "Interview intelligence by role, industry and company: reported questions, formats and preparation guidance"

qmd embed
```

`qmd context add` reportedly makes a substantial difference to retrieval
quality, so treat it as required rather than optional.

Deliberately **not** indexed:

| Target | Why not |
|---|---|
| Holographic `fact_store` | Atomic facts with `contradict`, `probe`, `reason`, trust scoring. Different layer — qmd has no fact model and no write path. Not a competitor. |
| `shared/applications.db` | Structured relational queries. Not a search problem. |
| Title taxonomy vector index | Purpose-built for occupation similarity. See "Two vector stacks" below. |
| `memory/star-story-bank.md` | See "The STAR bank" below — top-k retrieval is the wrong shape for story selection. |

`career_path_plans` and `role_transition_intel_cache` are left out for now
simply because they are small and plan-keyed lookup works. Add them if
they grow.

## Which mode to use

| Mode | Pipeline | Latency | Use for |
|---|---|---|---|
| `qmd search` | BM25 only, no models | ~0.2s | Exact names, company slugs, identifiers |
| `qmd vsearch` | Semantic vector | ~3s | Concept lookup where phrasing varies |
| `qmd query` | Hybrid + rerank | ~2-3s warm, **~19s cold** | Conceptual questions where quality matters |

Cold start matters here. Cron jobs run intermittently and will hit cold
models nearly every time. Either run the HTTP daemon
(`qmd mcp --http --daemon`) and accept a supervised process, or default
unattended jobs to `qmd search` and reserve `qmd query` for interactive
use. **Do not put a 19-second cold start inside a per-application loop.**

## Index staleness — the main hazard

`qmd embed` must be re-run whenever indexed files change, and the failure
is silent: a stale index answers confidently with old content rather than
erroring. Cron jobs 1, 2, 10, 13 and 14 all write cache files.

Handled by **cron job 17**, which re-embeds nightly. That accepts up to 24
hours of staleness in exchange for one job instead of an embed step
appended to five. The trade is acceptable because these caches carry their
own freshness conventions anyway — `12-company-research`'s 90-day rule and
the same convention in `13-interview-prep`'s intel scrub — so a day-old
index is well inside the tolerance the design already assumes.

If that ever stops being true, move the embed into each writing job
instead. Do not leave it implicit.

## The journal bridge

`career_journal` lives in SQLite and qmd only sees files. Journal semantic
recall was the original motivation for wanting qmd at all, so the gap
matters.

`16-career-pulse/scripts/journal-export.py` projects the table to
`shared/journal_export/{YYYY-MM}.md`, one file per month, regenerated
wholesale on every run.

Three deliberate choices:

- **Projection, not a second source of truth.** The DB stays
  authoritative. The export is disposable — delete it and re-run. Nothing
  ever writes back, so the two cannot diverge in any way that matters.
- **Monthly grouping, not per-entry.** qmd chunks at ~900 tokens with 15%
  overlap, so a month of short entries lands in one or two chunks and
  keeps neighbouring entries in the same window. That is what makes "what
  was going on around then" answerable rather than returning one isolated
  line.
- **Not a backup, and the direction matters.** If `career_journal` were
  lost, the next export run *deletes* the markdown to match, because a
  month absent from the DB is absent from the export. It follows the
  database down rather than surviving it. See
  `security/backup-and-recovery.md`.
- **Wholesale regeneration.** Stale months are deleted before rewriting,
  so an edited or removed entry cannot survive in the export.

Add it as a fourth collection once the journal has enough entries to be
worth searching:

```bash
qmd collection add shared/journal_export --name journal
qmd context add qmd://journal "Career journal check-ins: what got hard, what resolved, what shipped, who was worked with"
```

## Two vector stacks — the decision, stated

`title_taxonomy_builder.py` already builds embeddings (`fastembed`) into a
`sqlite-vec` `vec0` index. Adding qmd means a second embedding system.
That was worth checking rather than assuming, and the corpora are
**genuinely disjoint**:

| | Taxonomy index | qmd |
|---|---|---|
| **Corpus** | O*NET occupation profiles — titles, tasks, knowledge, skills, abilities, plus observed market title strings and tools | User-generated research documents |
| **Origin** | Public reference data | Produced by this pipeline |
| **Query shape** | "Which occupations are similar to this profile?" — ranking over a fixed reference set | "Which of my documents discuss X?" — retrieval over a growing corpus |
| **Lifecycle** | Rebuilt on a monthly/quarterly refresh cadence | Re-embedded nightly as caches are written |
| **Consumer** | Phase 1.5 adjacent-title expansion, one caller | Any skill asking a cross-corpus question |

Zero corpus overlap, zero query overlap, zero duplicated work. **Decision:
keep both.** The real cost is dependency surface — `fastembed` on the
Python side and Node ≥ 22 on the qmd side — not redundancy. If dependency
count is the binding constraint on your install, drop qmd rather than the
taxonomy index: the taxonomy has one well-defined consumer and no
substitute, while qmd's value is breadth.

## The STAR bank

Not indexed, on purpose, and the reasoning is worth recording because the
obvious move is to index it.

`memory/star-story-bank.md` is loaded whole into context. That does not
scale, but the current design has a real virtue: with every story present,
the model compares all of them and picks the best fit. Top-k retrieval
returns the most textually *similar* stories, and the best story for a
question is often not the most similar one — a question about handling
conflict may be best answered by a story that never uses the word.

So retrieval is the wrong shape here. See
`star-bank-aging.md` for the approach that fits.
