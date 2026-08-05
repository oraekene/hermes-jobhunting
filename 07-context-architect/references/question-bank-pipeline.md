# Question Bank Pipeline — Crawling Real Application Questions

Origin: Kene's request to build a bank of ~100 context-interview
questions sourced from real, currently-open job postings, refreshed in
batches (100, then another 100, then another 100) and drawn down to a
diverse top-100, rather than hand-written by guesswork.

**Yes, this is buildable, and the honest version of "yes" needs one
caveat up front**: it has to run from an environment with open internet
access — Kene's own machine or the Hermes box on Oracle Cloud — not from
inside a sandboxed chat tool. The script in this folder
(`question_bank_crawler.py`) is written to be handed to Hermes directly
("run this crawl") or run manually with `python question_bank_crawler.py`.

## Where real application questions actually live

Two different things get conflated as "job posting questions" and they
need different sourcing:

1. **Custom screening questions** — the literal extra fields an
   employer bolts onto an application ("Why do you want to work here?",
   "Describe a time you disagreed with a manager"). These are gold —
   they're exactly what `08-application-qa` drafts answers for — but
   they only exist in structured form on ATS platforms that expose
   them.
2. **Implicit questions inside the JD body** — a job description that
   says "must be comfortable presenting to executive stakeholders" is
   implicitly going to generate an interview/application question
   about executive communication even if no explicit field asks it.
   This is a much larger and noisier source, useful for the gap-analysis
   system (see `gap-analysis-engine.md`) more than for the literal
   question bank.

### Source 1: ATS public job-board APIs (best for explicit questions)

A handful of applicant tracking systems publish **unauthenticated,
intentionally public** JSON endpoints — they want their jobs indexed by
Google, LinkedIn, and aggregators, so there's no scraping/ToS risk here
the way there is with LinkedIn or Indeed direct scraping (both of which
actively fight scraping and are not worth the legal exposure for this
project — skip them as direct crawl targets).

**Confirmed directly against Greenhouse's own official API docs**
(`github.com/grnhse/greenhouse-api-docs`, not a secondhand summary):
appending `?questions=true` to a job detail request genuinely returns
the application form's actual question fields, including free-text
prompts — this isn't an assumption or a workaround, it's the documented
behavior of a public endpoint built for exactly this kind of
consumption. Worth stating plainly because it's easy to assume
screening questions only exist inside a JS-rendered `/apply` form
(true for a generic company career page with no ATS behind it — that
case genuinely would need browser automation) — but for postings
actually hosted on Greenhouse or Lever specifically, they don't:

| ATS | Endpoint | Gives you the actual questions? |
|---|---|---|
| Greenhouse | `GET boards-api.greenhouse.io/v1/boards/{token}/jobs/{id}?questions=true` | **Yes** — `?questions=true` returns the exact custom application fields |
| Lever | `GET api.lever.co/v0/postings/{company}?mode=json` | **Yes** — posting objects include the application form's custom questions |
| Ashby | `GET api.ashbyhq.com/posting-api/job-board/{company}?includeCompensation=true` | Partial — strong on JD/comp/location text, application-form questions need the separate (less standardized) application-form endpoint |
| Workable, Recruitee, Personio | each has a public feed too | Description text reliably; questions less consistently — verify against current docs per platform, these evolve |

The discovery problem is real: none of these platforms publish a "list
every customer" endpoint, so you need a **seed list of company slugs**
per platform. Build the seed list deliberately for diversity rather than
grabbing whatever's easiest to find (see "Forcing diversity" below).

### Source 2: broad aggregators (best for volume + JD text diversity)

Adzuna (free tier, ~1,000 calls/month, 16 countries) is the best free
option for casting a wide net across industries/geographies for JD
*text* — but it gives excerpted descriptions and predicted salaries, not
structured screening questions, so treat it as a Source-2 input to the
gap-analysis system, not the literal question bank.

### Source 3: opportunistic capture from 01-job-discovery

`01-job-discovery` is already going to be reading real postings for
Kene's own applications, several times a day, forever. The cheapest
addition to this whole system is having that skill **log every distinct
custom application-question string it encounters** into
`question_bank_raw.jsonl` as a side effect of its normal run — zero extra
crawl infrastructure, and it's automatically weighted toward the roles
Kene actually applies to. This won't be diverse on its own (it's
scoped to his target roles), which is exactly why it's a *supplement*
to the deliberate crawl below, not a replacement for it.

## Forcing diversity (industry, sector, seniority, location, other context)

A crawl that just pulls "the next 100 postings" from tech-company
Greenhouse boards will produce a bank that's 90% "software engineer,
mid-level, US, remote." Diversity has to be a sampling constraint, not
a hope. Stratify the seed list across:

- **Industry/sector** — tech, healthcare, finance/fintech, retail,
  manufacturing, education, nonprofit, government/public sector,
  hospitality, logistics, energy/solar (relevant to Kene's own
  portfolio), agriculture.
- **Seniority band** — entry-level/new-grad, individual contributor
  (2–5 yr), senior IC, first-line manager, director+.
- **Function** — engineering, product, sales, marketing, operations,
  finance, HR/people, customer support, design — not just the roles
  Kene personally targets, since the bank should generalize to
  question *patterns*, not just his own titles.
- **Geography/market** — US, UK, EU, and explicitly Nigeria/African
  market postings where they exist on these platforms (smaller sample,
  but worth deliberately including — application questions from
  Nigerian or pan-African employers sometimes probe different context,
  e.g. relocation/NYSC status, local vs. diaspora experience).
- **Company stage/size** — early-stage startup vs. large enterprise
  (startups ask more "why us / why now" questions; enterprises ask more
  compliance/process-adherence questions).
- **Employment type** — full-time, contract, internship (each has a
  distinct question register).

Concretely: the crawler takes a `seed_companies.yaml` with slugs grouped
by these tags, and the batch runner pulls a fixed quota per tag combo
per 100-question batch, rather than first-N-results.

**Why broad, rather than scoped to `target-profile.yaml` from the
start**: it's tempting to only crawl industries/seniority bands Kene
is actually targeting right now — less wasted crawl effort on
questions he'll never see. Deliberately not doing that, for a
durability reason: the bank would need a full re-crawl every time
Kene's target profile changes (a career pivot, a new industry he
starts targeting), whereas a broad bank filtered for relevance at
gap-analysis time (`gap-analysis-engine.md`'s relevance score) stays
useful across profile changes — only the filter has to be rerun, not
the crawl. The cost of this choice is bounded anyway: irrelevant
questions get skipped at Phase 1.5, cheaply, without ever reaching
Kene, so "wasted" crawl effort here just means slightly more rows in
`question_bank_raw.jsonl`, not a longer interview.

## The three-batch-to-one-hundred process

1. **Batch 1 (100 raw postings)**: run the crawler against the seed
   list, extract every explicit question, normalize whitespace/casing,
   store each as `{question_text, source_platform, company_slug,
   industry_tag, seniority_tag, function_tag, geo_tag, date_crawled}`
   in `question_bank_raw.jsonl`.
2. **Batch 2 and Batch 3**: repeat against a *rotated* seed list (skip
   companies already crawled; add new ones from underrepresented tag
   combos from batch 1's coverage report). By batch 3 you have ~300 raw
   rows spanning a genuinely wide tag matrix.
3. **Cluster and dedupe**: most "unique" questions are the same
   question in different words ("Why do you want to work here?" /
   "What draws you to this role?" / "Why [Company]?"). Embed every
   question (any decent sentence-embedding model — this doesn't need a
   frontier LLM), cluster with a similarity threshold, and collapse each
   cluster to one canonical phrasing + a list of the raw variants seen
   (useful later — real employers' exact phrasing matters for
   `08-application-qa`'s "weave in keywords naturally" step).
4. **Curate to the top 100**: from the clustered set, pick the final
   list by **coverage, not just frequency** — take the highest-frequency
   canonical question from each tag combo cell first, so the top 100 is
   deliberately spread across the diversity matrix rather than just
   "the 100 most common questions overall" (which would over-index on
   whatever's most common in tech/US/mid-level, since that's the
   easiest data to get).
5. **Human pass**: Kene reviews the curated 100 once before it becomes
   the live bank — this is a cheap, high-value manual step precisely
   because everything downstream (the interview loop, the gap-analysis
   engine) trusts this list.

Output: `shared/question_bank.yaml`, structured as:

```yaml
- id: qb_0001
  canonical_text: "Describe a time you disagreed with a manager or leadership decision."
  variants_seen:
    - "Tell us about a time you pushed back on a decision from above."
    - "Give an example of when you challenged a leader's decision."
  tags:
    industry: [tech, finance, healthcare]
    seniority: [ic_senior, manager]
    function: [general]
    geo: [us, uk]
  category: behavioral_conflict
  source_count: 14
```

This is the artifact `07-context-architect` Phase 2 and the gap-analysis
engine (next file) both read from — the interview loop never invents
its own question wording; it draws from here.

## Re-crawl cadence

Two different cadences, doing two different jobs — full reasoning and
the cron wiring in `bank-refresh-automation.md`:

- **Monthly, automated, staged**: a small incremental crawl, re-clustered
  against the full raw history, diffed against the live bank, delivered
  as a digest for approval — never auto-applied. This is what actually
  catches drift in *what kinds* of questions employers ask over time
  (e.g. more AI-tool-usage questions showing up than six months ago).
- **Quarterly, deliberate, still manual**: the full three-batch process
  above, repeated — worth keeping manual because *which new companies to
  seed* is a judgment call about coverage, not something worth
  automating.

Also re-run (either cadence, immediately) when: Kene pivots target
roles/industries significantly (per `07-context-architect` Phase 0's
re-run trigger), or the gap-analysis engine repeatedly hits real
interview questions that aren't well-represented in the current bank —
a sign the bank itself has a coverage gap, distinct from Kene having an
*answer* gap.
