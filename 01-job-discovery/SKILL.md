---
name: job-hunting-discovery
description: "Scan job boards and alerts for new matching postings"
metadata:
  hermes:
    tags: [job-hunting, discovery, blueprint]
    category: job-hunting
    related_skills:
      - job-hunting-orchestrator
      - job-hunting-jd-parser
      - job-hunting-company-research
      - capability:social_listening
    blueprint:
      schedule: "0 7,10,13,16,19,22 * * 1-6"   # business hours, Mon–Sat, WAT — see cron/cron-jobs.md job #1
      deliver: telegram
      prompt: "Scan configured sources in shared/sources.yaml for new postings, dedupe against the applications DB, cheap-filter against Kene's target profile in shared/target-profile.yaml, and queue anything that survives — respecting today's remaining daily cap (shared/pipeline-rules.md Rule 3). Deliver a short digest. Use [SILENT] if nothing new was found."
      no_agent: false
---

# Job Discovery

## When this skill applies

Use this skill to scan configured job boards/company career pages/RSS or email alerts for new postings matching Kene's target roles, and to queue them into the pipeline. Triggers: 'check for new jobs', 'scan for postings', 'what's new today', or the scheduled cron job that runs this automatically. This skill only discovers and queues — it never parses in depth, tailors, or applies. Do NOT use this skill to process a specific job posting URL Kene already has in hand; use 02-jd-parser directly for that.

The one stage of this pipeline that's genuinely safe to run unattended,
because its only output is "here's a posting that might be worth applying
to" — nothing leaves the system and no claim about Kene is made.

## What it does

1. Read `discovery_mode` from `shared/target-profile.yaml`
   (`poll_only` / `open_web` / `open_web_excluding` — confirmed once
   through `07-context-architect` Phase 0, same as every other
   target-profile fact; see "Discovery modes" below for what each does
   and why `poll_only` is the default). This decides which of the
   sources in step 2 are actually in play for a given run.
2. Pull new postings since the last run from every in-play source listed
   in `shared/sources.yaml`. Each entry there declares its `type`
   (job board search URL, company career-page RSS, forwarded email
   alerts via Hermes's bundled `himalaya` skill, saved search export,
   Google dork, aggregator API, or an open-web sweep) and — critically —
   how to read that source's own posting-date format (see step 5). This
   skill doesn't mandate which declared sources exist; `sources.yaml`
   starts empty and grows as sources get onboarded (see that file's own
   "Onboarding a new source" section) — but it does mandate that every
   *declared* source be listed there rather than assumed. `open_web`/
   `open_web_excluding` mode adds a second, broader tier on top of the
   declared list rather than replacing it — see below.

   **Reading an `rss` source**: use Hermes's bundled `research/
   blogwatcher` skill (RSS/Atom monitoring via a CLI tool) as the
   underlying mechanism rather than hand-rolling feed parsing — it's
   already the right tool for exactly this job. See also
   `01-job-discovery/scripts/discovery-wake-gate.py`'s own RSS check,
   which does a lighter, dependency-free version of the same fetch
   specifically for the cron wake-gate's pre-run cost check (not a
   replacement for using `blogwatcher` in the actual discovery pass
   itself — the wake-gate needs zero dependencies to run cheaply on
   every tick; this step doesn't have that constraint).

   **Reading an `email_label` source**: this needs Hermes's bundled
   `himalaya` skill configured per `security/email-integration-setup.md`
   (not a third-party MCP — Hermes already ships this) — if it isn't
   set up yet, skip the source and note it in the run's digest rather
   than failing the whole scan. When it is:
   1. `himalaya envelope list --folder {handle}` (plain listing, not
      `envelope search` — Gmail's IMAP server doesn't support the
      `SORT` capability the search query DSL needs). Filter the
      returned envelopes client-side by date against `last_run_date`.
   2. For each new envelope, `himalaya message read <id>` for the full
      body.
   3. **Job-alert emails are usually digests, not one posting per
      email** — a LinkedIn/Indeed alert email typically bundles several
      postings in one message. Parse every embedded posting/link inside
      the body as a *separate* candidate, don't treat the whole email as
      a single posting. **Also run the insight-extraction pass** described
      in `shared/email-insight-extraction.md` over the body even
      though this is a discovery-side read, not just an outcome-side
      one — a digest email occasionally carries a genuinely useful aside
      (a note that a role closes in 48h, a recruiter's personal note
      above the auto-generated listing) worth surfacing even though most
      of the time there's nothing beyond the listings themselves.
   4. Once a message's postings have been extracted and queued (or
      rejected as duplicates/non-matches), `himalaya message copy <id>
      "{handle}/Processed"` (adds the Processed label without removing
      the original) so the same digest is never re-parsed on the next
      tick.
3. De-duplicate against `applications` table (`shared/applications_db_schema.sql`)

   **Match on the fingerprint, not the URL.** The base schema's dedup key
   is `UNIQUE(company, role_title, posting_url)`, which is correct for one
   source and wrong for three. Jobs 1, 2 and 10 all write here, so the
   same posting found on LinkedIn, on the company careers page, and via a
   social post passes that check three times — and then gets parsed three
   times, customised three times, and consumes three slots of the daily
   cap under Rule 3.

   Compute `posting_fingerprint` (added in
   `shared/applications_db_schema_addendum_8.sql`):

   ```
   lower(trim(company)) | normalised_role_title | lower(trim(location))
   ```

   Normalising the title is the part that needs judgement, which is why
   it lives here and not in SQL: lowercase, strip punctuation, and remove
   the decorations that vary by board — trailing "(Remote)", "- Contract",
   requisition IDs, and roman-numeral or level suffixes where the taxonomy
   confirms they are the same job zone. Use `title-taxonomy.md`'s record
   for the title where one exists; fall back to the literal normalised
   string where it does not, because a false *merge* is worse than a false
   duplicate. Two genuinely different roles collapsed into one row loses an
   application; the same role queued twice costs one wasted slot.

   On a fingerprint hit, do not create a row. Insert into `posting_sources`
   instead — the URL, which source found it, and which job discovered it —
   and leave the existing application untouched. That turns a duplicate
   from waste into data: it makes "which source produces applications that
   actually get replies" answerable, which `11-analytics-and-learning`
   cannot ask today.

   Uniqueness is deliberately not enforced in the database. Existing
   installs may already hold duplicates, and a UNIQUE index would make the
   migration fail on exactly the databases that most need it. Merging
   pre-existing duplicates is a manual pass, not something a migration
   should attempt unattended.
   by company + title + posting URL, so the same role never gets queued
   twice. For `rss`/`aggregator_api` sources specifically, the optional
   `devops/watchers` skill already implements exactly this — watermark-
   based dedup polling of RSS/Atom feeds and JSON APIs — and is worth
   installing as the underlying mechanism for those two source types
   rather than re-deriving the same watermark logic by hand; it's a
   near-exact match for what this step needs from them.
4. Cheap-filter against `shared/target-profile.yaml` — `title_variants`
   (this skill never reads `shared/dynamic-target-calibration.yaml`
   directly and does not need to: `07-context-architect`'s Phase 1.5 is
   the single re-run point that keeps `title_variants` in sync with
   calibration state — wider during an auto-relax period, unchanged
   otherwise — so the effect is inherited the next time this step reads
   a field it was already reading. One re-run point rather than three
   places that must agree is the deliberate choice here)
   (an array of objects; match against each entry's `.title` field only —
   `source`/`confidence`/`rationale` are provenance for Kene's audit
   trail, not filter inputs), seniority_band, locations (remote/hybrid/
   onsite + country/city list), salary_floor, visa_sponsorship_required,
   industries/companies to exclude. This is a structured file, not the
   prose `USER.md` — the filter needs an explicit list of acceptable
   title strings and a numeric salary floor to compare against, not a
   markdown sentence. Reject obvious non-matches here — don't waste a
   full pipeline run on them.
5. Check `posted_at` against "now," using the `posted_at.method` declared
   for that source in `sources.yaml` (relative-text-on-page, RSS
   `pubDate`, JSON-LD `datePosted`, email receipt time, aggregator field,
   the open-web fallback chain, or "none available" → fall back to
   `discovered_at`). Always store the source's original label alongside
   the parsed value in `posted_at_raw`, so a misread relative string ("2
   hours ago" resolved against the wrong clock) is auditable rather than
   silently trusted. The Splendor thread's single clearest, least
   controversial finding was that **speed matters** — rolling review
   means early applicants get seen when recruiter attention and patience
   are both highest. Postings under 24 hours old (by `posted_at`, or by
   `discovered_at` when no reliable posted-date exists — these are not
   the same claim, keep them distinguishable) get a `priority: high` flag
   that `00-orchestrator` uses to jump the queue ahead of older postings.
6. Push each surviving posting into the `discovered` queue at status
   `discovered`, respecting the day's remaining slot count (see Rule 3,
   `shared/pipeline-rules.md`, and the cap defined in `README.md`). This
   cap is shared across every source tier — `open_web`/`open_web_excluding`
   mode widens what gets *found*, never how much gets *queued* per day.
7. If running under cron, deliver a short digest to Telegram — count of
   new postings found, count queued, count skipped as duplicates/non-matches,
   plus anything the insight-extraction pass in step 2.3 flagged as
   notable. If nothing new was found, use Hermes's silent-mode marker so
   Kene isn't pinged for an empty run.

## Discovery modes

Three modes, confirmed once in `target-profile.yaml`'s `discovery_mode`
field, trading off coverage against cost/consistency/risk — see the
reasoning behind this tradeoff in full before assuming wider is strictly
better:

- **`poll_only`** (default) — only declared `sources.yaml` entries, every
  3-hour tick. Cheapest, most consistent `posted_at` accuracy (every
  source's date format is known in advance), smallest unattended
  browsing surface.
- **`open_web`** — `poll_only`, plus any `open_web_search` source(s) in
  `sources.yaml`, run on **their own cadence** (`cadence: daily` by
  default in the source entry, not the 3-hour tick) using whatever
  search/browse capability Hermes has configured — same tool-agnostic
  approach `12-company-research` already uses ("whatever search/browse
  capability is configured... this skill doesn't need a specific one").
  For each `open_web_search` source with `platform_dorks: true`, build
  one query per known ATS platform (Greenhouse, Lever, Ashby, Workday,
  SmartRecruiters, iCIMS — the same platform list
  `07-context-architect/references/question-bank-pipeline.md` already vetted for the
  question-bank crawl) plus one generic open query, all constructed from
  `target-profile.yaml`'s `title_variants`/locations at run time —
  nothing to hand-write per platform. Visit result pages and extract
  postings the same way `scrape_and_filter` sources already do.
  Several ATS-hosted career pages and job boards run behind Cloudflare
  or basic anti-bot checks; if the optional `research/scrapling` skill
  (stealth browsing, Cloudflare bypass) is installed, use it for this
  step rather than the plain browser tool. If no paid `web_search` is
  configured, the optional `research/duckduckgo-search` or `research/
  searxng-search` skills (free, keyless — either activates automatically
  via `fallback_for_tools: [web_search]` once installed) let this mode
  degrade gracefully instead of failing outright; install either one,
  not both. This
  tier runs slower and less often specifically because it's more
  expensive per run (an LLM-driven search+extract loop, vs. polling a
  known feed) and less date-reliable (see `sources.yaml`'s
  `fallback_chain` method) — daily is enough to catch the long tail of
  company career pages and niche boards nobody's going to manually
  onboard one at a time, without paying open-web cost at 3-hour cadence.
  It's also a wider unvetted-page surface touched by an unattended
  agent than a small set of previously-onboarded sources — worth
  weighing given this runs without Kene in the loop, same reasoning
  `security/security-setup.md` already applies to container isolation
  around the apply step, just applied here to discovery frequency
  instead.
- **`open_web_excluding`** — same as `open_web`, filtering out any
  domain listed in `sources.yaml`'s `exclude_domains` (a past employer,
  a board Kene's explicitly opted out of, etc.) before postings ever
  reach the dedupe/filter steps above.

**Before reaching for `open_web`**: check whether `aggregator_api`
(Adzuna, in `sources.yaml`) already covers the country/market in
question — it gives broad, multi-board coverage with a structured,
reliable `posted_at` field, at a fraction of the cost and none of the
unvetted-page exposure of a true open-web sweep. Prefer it over
`open_web_search` for anything it actually covers; reach for the open-web
tier for the genuine long tail beyond it.

## What it does not do

No JD parsing beyond the cheap filter, no resume tailoring, no contact
with the employer. If a posting looks great, it still just sits in the
`discovered` queue until `00-orchestrator` walks it through the rest of
the pipeline — this skill's job ends at "found and queued."

## Cron wiring

See `cron/cron-jobs.md` for the exact job definition. This is the job
that runs most frequently (every few hours during business hours in the
target time zone), since postings age fast.

### Cost control: the wake-gate script

Run this often, this job would otherwise pay for a full LLM agent turn
on every tick regardless of whether anything new actually exists —
Hermes's cron system supports skipping the agent turn entirely (zero
token cost) when a pre-run `script=` check reports nothing worth waking
up for. `01-job-discovery/scripts/discovery-wake-gate.py` is that check:
it cheap-checks `rss` and `email_label` sources directly (feed fetch /
`himalaya envelope list`, no LLM involved) and only tells cron to skip
the turn when every source it's able to check that way came back with
nothing new.

**Read the script's own docstring before wiring it in** — it explains
exactly which source types it can and can't cheap-check, and why it
fails *open* (wakes the agent) on anything it's unsure about, which is
the opposite failure direction from the submit-gate hook in
`security/hooks/verify-submit-approval.py` and deliberate for a
different reason: a missed cheap-check just delays discovery by one
tick, it doesn't risk anything going out unreviewed.

Wire it into the cron job definition itself — see `cron/cron-jobs.md`
job #1 for the exact `script=` parameter. If most of your
`sources.yaml` entries are types this script doesn't cheap-check
(`aggregator_api`, `open_web_search`, `google_dork`, the search-URL
types), this gate will rarely skip a turn and that's expected, not
something to debug — it's not pretending to solve cost control for
source types it can't safely evaluate without an LLM.
