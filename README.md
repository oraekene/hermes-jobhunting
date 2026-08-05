# Job-Hunting Skill Package for Hermes Agent

A 25-skill pipeline that turns Kene's original 6-7 prompts + the
Splendor thread's tactics into a Hermes-native system: discovers
postings, tailors every application, stops for a one-tap Telegram
approval before anything is ever sent, gets measurably better over time
from its own outcome data, and builds a prep brief + practice flashcards
the moment an interview is actually on the calendar.

**The one sentence that matters most**: this system automates everything
up to the click. It never automates the click itself. See
`shared/pipeline-rules.md` Rule 1 for why, and the earlier conversation
for the reasoning behind that line.

## Recent additions

- **Importance as a ranking dimension** (`fact-influence-scoring.md`,
  `_17.sql`) — trust measures whether a fact is *correct*; nothing
  measured whether it *matters*. Influence counts only events where a
  fact changed an output, never retrieval counts. The two scores are
  reported separately and never averaged, because the payoff is the
  corner neither finds alone: low trust + high influence is a fact
  deciding gates that keeps getting edited out. `fact_feedback` is now
  on by default — until it was, trust scores never moved off 0.5.
- **`23-portfolio-onepager`** — one public page generated from confirmed
  memory, versioned per target role, verified by `09-risk-tactics-gate`
  before publishing. Deliberately not a site builder.
- **DB ownership enforced, not instructed** — subagents no longer write
  SQL at all: each leaves one JSON file in `shared/.outbox/` and the
  parent ingests them serially, which takes write contention to roughly
  zero and makes row ownership structural. `security/hooks/verify-db-ownership.py`
  backstops it. **If you sync this folder with Syncthing/Dropbox, read
  `shared/db-concurrency.md`'s sync section before enabling WAL** — WAL's
  `-wal`/`-shm` sidecars replicated by a file-level syncer can tear the
  database, which is worse than the failure WAL fixes.
- **The audit's open infrastructure items** — concurrency (`shared/db-concurrency.md`:
  WAL, busy timeout, `BEGIN IMMEDIATE`, and subagent row ownership — the
  parallel sweep had multiple writers on one SQLite file and SQLite's
  default on a held lock is to *fail* the write, not wait); build failure
  semantics (`_15.sql`); fact aging (`07-context-architect/references/fact-conflict-resolution.md`
  — `last_confirmed_at` was written in two places and read in none);
  install verification (`00-orchestrator/scripts/install-check.py` —
  nothing previously checked that Rule 1's submit hook was actually
  registered); a model-spend cost model (`shared/cost-model.md`); and the
  interview pressure drill (`13-interview-prep` Part 3c). See
  `AUDIT-TRIAGE.md` and `ADDENDUM-CHANGELOG.md` v24.

- **The stepping-stone engine (`19-career-path-planner` Step 3.5)** — the
  intermediate-role part of a career plan, which had been *recorded*
  rather than built: one bullet keyed off a `job_zone` delta, and four
  columns to store the answer. The piece that was missing turns out to be
  a classification, not an algorithm — **not every gap can be closed
  outside a role.** A certification is `self_closable`; "has managed
  people" is `role_gated` and no amount of Kene's own effort closes it.
  That distinction is what a stepping stone is *for*, and without it the
  feature was seniority interpolation. Everything else follows:
  role-gated gaps now trigger a hop regardless of `job_zone` (the most
  common real case, which the old rule missed entirely), candidates are
  scored on two sides that multiply rather than sum, four checks can
  disqualify a path outright, the roadmap becomes hop-scoped so the
  active list is the one Kene can start on Monday, and a hop that has
  been *landed* is distinguished from one that has *done its job*.
  Three paths are always generated including the direct one, which is
  what makes the `one-three-one-rule` adoption real rather than formal.
  See `19-career-path-planner/references/stepping-stone-engine.md` and
  `shared/applications_db_schema_addendum_14.sql`.
- **Skill-coverage cross-check** — a direct re-check against the
  original gap-analysis's own skills-catalog table found that 7 of 13
  listed skills (`research/blogwatcher`, `devops/watchers`, `research/
  duckduckgo-search`, `research/searxng-search`, `research/parallel-cli`,
  `security/1password`, `software-development/hermes-agent-skill-
  authoring`) had been discussed during earlier phases and never
  actually written into any file, and `research/scrapling` was only
  partly wired in. All fixed, in the files each was originally meant
  for (`01-job-discovery`, `02-jd-parser`, `12-company-research`,
  `security/email-integration-setup.md`) — see
  `HERMES_UPGRADE_CHANGELOG.md`'s "Post-roadmap" entry for the full
  accounting.
- **Optional parallel pipeline sweep via `delegate_task`** (opt-in, off
  by default) — the last item on the original roadmap. Delegates
  stages 2–9's build phase across postings in parallel instead of
  serial, up to `delegation.max_concurrent_children`. One honestly
  unresolved piece of mechanics, documented rather than glossed over:
  whether a cron-triggered top-level agent's `delegate_task` batch
  result arrives within the same turn or genuinely later as a fresh
  message — the docs are framed around interactive sessions and don't
  address cron-triggered timing explicitly, and there was no live
  gateway available to test it directly. The design is built to be
  correct either way: every sweep tick reconciles anything left
  unfinished from a prior batch before delegating new work, and a
  posting stuck at `building` or `staged` for more than one full sweep
  cycle gets surfaced as a stuck-batch warning rather than silently
  lost — turning a genuine unresolved question into a bounded, visible
  failure mode instead of a silent one. Formalizes a `building` →
  `staged` → `awaiting_approval` status flow that closes a real race
  condition (a later sweep tick re-delegating a posting still in
  flight) and fixes stale `awaiting_approval` terminology that had
  crept into several files. See `00-orchestrator/references/parallel-
  pipeline-sweep.md`.
- **MoA cross-check for borderline title-matches** (optional,
  human-initiated) — the original idea was for `09-risk-tactics-gate` to
  automatically reach for a Mixture-of-Agents second opinion on its
  riskiest tactic. Checking the actual mechanics ruled that out on two
  independent, verified grounds: `/moa` is parsed only from human-typed
  input (confirmed by reading `cli.py`'s own slash-command dispatch
  code — an agent's own output is never re-parsed as a command), and
  `delegate_task`'s model override is a global `config.yaml` setting,
  not something a specific call can request — setting it to a MoA
  preset would silently apply MoA's extra cost to any other delegated
  work in the pipeline too. What shipped instead: title-match calls that
  rest on inference rather than an explicit memory statement now get
  marked `[BORDERLINE PASS]`, and `10-approval-and-submit`'s Telegram
  message includes a ready-to-paste `/moa <question>` prompt right next
  to the flag — Kene's call whether to use it, same as the mechanism
  actually is. See `09-risk-tactics-gate/references/moa-cross-check.md`.
- **Tier 2 self-improvement: GEPA-based evolutionary optimization
  (optional, manual, `05`/`06`/`08` only)** — built after reading the
  actual `hermes-agent-self-evolution` source directly, which
  surfaced three real gaps versus its own documentation: the fitness
  metric actually wired into the optimization loop is a keyword-overlap
  heuristic, not the "LLM-as-judge" scoring `PLAN.md` describes (its
  `LLMJudge` class is imported but never called); the constraint
  validator checks only size/growth/emptiness/frontmatter-structure —
  **zero content-safety checks**, confirmed by reading
  `constraints.py` in full; and there's no auto-generated PR, just two
  local markdown files a human has to actually read. `09-risk-tactics-
  gate` is deliberately excluded from this feature entirely — the
  missing content-safety net makes it the wrong first skill to point an
  evolutionary optimizer at. A mandatory safety-anchor patch (exact code
  given) closes part of that gap for the three skills this *does*
  cover. New `build_gepa_golden_set.py` derives evaluation examples from
  real `applications.db` outcomes (interview/screen requests) rather
  than synthetic guesses — tested against synthetic data, including a
  full round-trip through the real dataset-loader schema. See
  `11-analytics-and-learning/references/gepa-self-evolution.md` for
  everything, including why this is quarterly/on-demand and deliberately
  has no cron job anywhere.
- **Passive domain-age signal in `12-company-research`** (optional,
  `research/domain-intel` skill) — a new anti-scam safety check, entirely
  passive (certificate-transparency logs, WHOIS, one TLS handshake — no
  port scanning). Verified against the actual skill's source (its exact
  CLI output fields, not just its catalog description) rather than
  assumed. Deliberately cross-checks domain age against the company
  stage/size signal already gathered in step 2, rather than flagging age
  alone — a new domain is unremarkable for an already-identified
  early-stage startup and only worth a note when it doesn't match what
  the posting claims (an established/enterprise employer on a
  months-old domain, for instance). Never a hard block; surfaces as a
  plain-language note, and only reaches Kene via the
  `10-approval-and-submit` Telegram message when there's actually
  something worth a second look — not on every application.
- **Optional Holographic memory layer for the STAR bank** — a parallel,
  atomic-fact layer alongside `memory/star-story-bank.md`, off by
  default, config-gated. Built after actually running Hermes's
  `plugins/memory/holographic` source directly, not just reading its
  docs — which surfaced a real, worth-knowing limitation: its
  `contradict` action is good at catching two facts about the same
  entity that read as *completely different characterizations*, but
  (tested directly) does **not** reliably catch the more common risk —
  the same claim restated with one number changed, since near-identical
  phrasing keeps its content-similarity score too high to trigger.
  `07-context-architect`'s Phase 4 now does a direct probe-and-read
  check as the actual defense, with `contradict` as a cheap supplementary
  pass, not the primary guarantee its own tool description implies. See
  `07-context-architect/references/holographic-memory-layer.md` for the
  full mechanics, a real entity-extraction quirk and its fix, and why
  NumPy needs to be installed explicitly (`contradict` silently returns
  nothing without it — the one action here that doesn't degrade
  gracefully).
- **`13-interview-prep` built out (was a stub)** — the pipeline is now a
  real 13 stages, not 12 + a documented placeholder. Once
  `interview_request_at` is set on an application, this stage assembles
  a prep brief (company research, every `interview_detail`/`feedback`
  email insight, exactly what `09-risk-tactics-gate` actually claimed on
  the sent package, and — new — deliberately scoped public-professional-
  info research on the named interviewer if one's known) and builds a
  `productivity/memento-flashcards` deck for practice. Building the
  brief can run unattended (new cron job #9, ships as a fourth
  blueprint); actually studying the cards is structurally a live,
  on-request-only conversation — `memento-flashcards`' own review flow
  needs Kene's real answer before it can grade and continue, so it
  can't run from cron, and the skill is explicit about not blurring that
  line. Multi-round interviews (phone screen → onsite → final) trigger a
  brief *refresh*, not just a one-time build, keyed off new
  `interview_detail` rows arriving after the last build — see
  `applications.last_interview_prep_at` in the schema (migration note
  included, since this is a column added to a table that already exists
  on anyone's running install, not a new table).
- **Hermes-capability upgrade pass** — five changes made after a full
  audit against Hermes's actual mechanisms (self-improvement loop,
  memory, cron, hooks, skills catalog): (1) fixed a real bug —
  `09-risk-tactics-gate` no longer writes "open gaps" into `MEMORY.md`
  (violated Rule 5, risked hitting `MEMORY.md`'s hard character cap
  during unattended cron runs); it writes to a new `open_gaps` DB table
  instead. (2) the approval screenshot in `10-approval-and-submit` now
  uses Telegram's `[[as_document]]` delivery directive so it doesn't get
  lossy-recompressed right when legibility matters most. (3)
  `01-job-discovery`'s cron job now has a `wakeAgent` pre-run cost-
  control gate (`01-job-discovery/scripts/discovery-wake-gate.py`) that
  skips the LLM turn entirely on ticks where nothing new exists. (4) a
  `pre_tool_call` hook (`security/hooks/verify-submit-approval.py`) adds
  a third, purpose-built enforcement layer on Rule 1, checking the DB
  directly before letting a submit click through. (5) Hermes's bundled
  `creative/humanizer` skill is now wired into `05`/`06`/`08`'s output
  passes, plus a job-application-specific anti-slop checklist for
  `06`/`08`. The three highest-traffic cron jobs (discovery scan,
  pipeline sweep, weekly self-improvement review) also now ship as
  Hermes **blueprints** — one-tap `/suggestions accept` instead of
  hand-typed `hermes cron create` commands, which matters directly for
  the resale idea below. See `cron/cron-jobs.md`'s "Install path has
  changed" section for the mechanics, and ask for the full gap-analysis
  document this came from if you want the reasoning behind each change,
  or the deeper (opt-in, not yet built) upgrades it also identified.
- **`fidelity_mode`** (`shared/target-profile.yaml`) — how strict
  `09-risk-tactics-gate` is about requiring evidence before applying a
  claim-changing tactic. `strict` (default) / `balanced` / `embellish`.
  See `shared/pipeline-rules.md` Rule 2.
- **Adjacent-title expansion via a title taxonomy** — `07-context-architect`
  Phase 1.5 now cross-references Kene's actual skills/scope against a
  full title-profile database (O*NET-anchored, market-signal-enriched,
  embedding-searched) to suggest titles he's never held but could
  credibly target. See `07-context-architect/references/title-taxonomy.md`.
- **`discovery_mode`** (`shared/target-profile.yaml`) — `poll_only`
  (default) / `open_web` / `open_web_excluding`. Adds an optional,
  slower-cadence open-web sweep on top of the declared-source list, plus
  a structured `aggregator_api` (Adzuna) middle ground. See
  `01-job-discovery/SKILL.md`'s "Discovery modes" section.
- **Email insight extraction** — reading a job-alert or reply email now
  also extracts interview details, feedback, deadlines, and action items
  into `email_insights`, surfaced in digests and intended as input to a
  future interview-prep stage. See `shared/email-insight-extraction.md`.

## What the addendum pass added, one line each

Carried over from the merged addendum package. Full version history for
that work is in `ADDENDUM-CHANGELOG.md`.

- **`14-social-discovery-outreach/`** — search social platforms for job
  leads (following whatever the post itself asks for — a link or a DM),
  plus cold-DM/cold-email drafting and, on the one platform where it's
  actually possible without unacceptable ban risk, sending itself. See
  `14-social-discovery-outreach/references/platform-capability-matrix.md` for exactly what's real vs.
  aspirational per platform, verified 25 July 2026.
- **`13-interview-prep/`** — the addendum shipped this as a separate
  `15-interview-prep` intended to replace a stub. By merge time the base
  skill was no longer a stub but a full three-part implementation, so the
  direction reversed: `13-interview-prep` is the spine and the addendum's
  interview-intelligence scrub, sentiment inheritance, cross-referenced
  question sourcing and post-interview stage folded into it. The record is
  in `.merge-history/15-interview-prep/`.
- **`16-career-pulse/`** — scheduled journal check-ins, explicit-channel
  profile monitoring (LinkedIn/GitHub/portfolio/blog), and the event
  cascade that fires when a confirmed career update should ripple into
  title-taxonomy re-expansion and calibration re-evaluation. Never writes
  memory directly — everything routes through `07-context-architect`,
  same as always (Rule 5, and see the new Rule 7 below).
- **`shared/dynamic-target-calibration.yaml.template` +
  `.md`** — the match-score minimum/stretch system, an overqualification
  score (new — nothing like it existed before this), and
  `employment_status` tracking with a manual/auto/hybrid calibration
  mode. The `.md` file directly answers every open question from the
  original design conversation (overqualification scoring, how title-
  variant mapping actually works today, how employment status gets
  tracked, manual-vs-auto) — worth reading before the `.yaml`, not after.
- **`shared/pipeline-rules-addendum.md`** — Rules 6 and 7, both narrow
  extensions of Rule 1 and Rule 5 to the new channels above, not new
  categories of rule.
- **`shared/applications_db_schema_addendum.sql`** — `social_outreach`,
  `career_journal`, `profile_monitor_events`, `interview_debrief`. Run
  after the base schema; nothing in it is altered.
- **`cron-jobs-addendum.md`** — jobs 9-11, same conventions as the
  existing `cron/cron-jobs.md`.

## Known gaps, deliberately still open

- The actual cold-DM/cold-email **content formula** (opener, value-prop
  structure, ask phrasing — the outreach equivalent of `06-cover-letter/references/cover-letter-formula.md`). `cold-dm-email-schema.md` is
  structure-only on purpose, per Kene's own note that the content rules
  are coming separately — it slots into `message.body_draft`'s
  generation step without any schema change once it arrives.
- Kene's actual Job-Ops interview-prep design, if it differs from what's
  built here — see `13-interview-prep/SKILL.md`'s own honesty note.
- Direct API wiring for any Tier 1 platform (X) — the skill assumes
  Kene sets up his own developer credentials; nothing here provisions
  that for him.

## Install


```bash
# 1. Install Hermes if not already installed
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash

# 2. Drop this whole folder into Hermes's skills directory
cp -r job-hunting ~/.hermes/skills/job-hunting

# 3. Seed memory (do this via 07-context-architect's interview loop,
#    don't hand-copy the templates — the interview is what confirms each
#    fact instead of assuming it). Phase 0 of that interview produces
#    both ~/.hermes/memories/USER.md AND shared/target-profile.yaml
#    together — copy target-profile.yaml.template to target-profile.yaml
#    first so the skill has somewhere to write. Phase 0.5, right after,
#    asks a single question — strict, balanced, or embellish fidelity
#    mode (see 09-risk-tactics-gate's "Fidelity mode" section) — and
#    writes the answer into target-profile.yaml's fidelity_mode field.
#    Strict is the default if you skip it.
#    In a Hermes chat session:
/job-hunting-context-architect

# 3b. Set up at least one discovery source. Copy sources.yaml.template to
#     sources.yaml and either hand-fill an entry per shared/sources.yaml's
#     own instructions, or ask Hermes to onboard one interactively:
#     "onboard this new source: <url>" — it can inspect the page/feed and
#     propose the entry for you to confirm, same interview pattern as
#     context-architect. Any source needing account-level access (email
#     alerts) needs a one-time setup first: Hermes's bundled himalaya
#     email skill (a Gmail App Password, no Google Cloud project) plus
#     a filter created once by hand in Gmail's own settings — see
#     security/email-integration-setup.md.

# 4. Create the applications database, then apply the schema addenda
#    IN ORDER. _3.sql is superseded by _4.sql and is kept for historical
#    reference only — do NOT run it on a fresh install.
cd ~/.hermes/skills/job-hunting/shared
sqlite3 applications.db < applications_db_schema.sql
sqlite3 applications.db < applications_db_schema_addendum.sql
sqlite3 applications.db < applications_db_schema_addendum_2.sql
sqlite3 applications.db < applications_db_schema_addendum_4.sql   # full career-path tracking
sqlite3 applications.db < applications_db_schema_addendum_5.sql
sqlite3 applications.db < applications_db_schema_addendum_6.sql   # overqualification gate outcome
sqlite3 applications.db < applications_db_schema_addendum_7.sql   # migration ledger — every future migration records itself here
sqlite3 applications.db < applications_db_schema_addendum_8.sql   # cross-source posting dedup
sqlite3 applications.db < applications_db_schema_addendum_9.sql   # journal soft-delete + retention
sqlite3 applications.db < applications_db_schema_addendum_10.sql  # enrichment spend joined to outcomes
sqlite3 applications.db < applications_db_schema_addendum_11.sql  # posting disappearance handling
sqlite3 applications.db < applications_db_schema_addendum_12.sql  # journal-derived features
sqlite3 applications.db < applications_db_schema_addendum_13.sql  # pause on hire, resume at higher tier
sqlite3 applications.db < applications_db_schema_addendum_14.sql  # stepping-stone engine
sqlite3 applications.db < applications_db_schema_addendum_15.sql  # build failure semantics
sqlite3 applications.db < applications_db_schema_addendum_16.sql  # fact aging + supersession
sqlite3 applications.db < applications_db_schema_addendum_17.sql  # fact influence scoring
sqlite3 applications.db < applications_db_schema_addendum_18.sql  # portfolio artifacts + link health
sqlite3 applications.db < applications_db_schema_addendum_19.sql  # outreach send path (renumbered from ADDENDUM-27's _6 on merge)
sqlite3 applications.db < applications_db_schema_addendum_20.sql  # cron execution ledger

# Concurrency. NOT optional if you ever enable the parallel sweep — see
# shared/db-concurrency.md. journal_mode is a property of the FILE, so
# this is set once and persists; the other pragmas are per-connection and
# live in the open_db() helper in that file.
sqlite3 applications.db "PRAGMA journal_mode=WAL;"
# If _3.sql was already run on an existing install, back up any
# career_path_plan_progress data you want before running _4.sql — that
# migration drops the table rather than converting it.
#
# _14.sql and _15.sql use ALTER TABLE ADD COLUMN, which SQLite has no
# IF NOT EXISTS form for. Running either twice errors on its ALTER
# block. That is a visible, safe no-op — nothing is written and nothing
# is corrupted — but they are the two files here that are not
# idempotent. Run each once.
#
# 4b. Verify the install actually took. This is read-only and repairs
# nothing — it checks the things an install can silently skip: the
# submit hook's registration (Rule 1's third layer), shared/ being
# present at all (Rule 0), the full schema chain, and WAL.
python3 00-orchestrator/scripts/install-check.py

# 5. Set up security (DM pairing, container backend, skill write-approval,
# and the submit-gate hook) — see security/security-setup.md for the full
# config, this is the short version:
hermes pairing approve telegram <your-pairing-code>
hermes config set skills.write_approval true   # global — gates EVERY skill write, not just this package
mkdir -p ~/.hermes/agent-hooks
cp security/hooks/verify-submit-approval.py ~/.hermes/agent-hooks/job-hunting-verify-submit-approval.py
# then add the pre_tool_call hooks: block in ~/.hermes/config.yaml —
# see security/security-setup.md section 3 for the exact YAML and the
# hooks_auto_accept note (required for this to fire on unattended runs).

# 6. Register the cron jobs. Four jobs — discovery scan, pipeline sweep,
# weekly self-improvement review, interview-prep sweep — ship as
# blueprints and show up as suggestions automatically once the skill
# folder is installed:
/suggestions              # (in a Hermes chat session) lists the four pending suggestions
/suggestions accept 1
/suggestions accept 2
/suggestions accept 3
/suggestions accept 4
# Then attach each job's cost-control wake-gate script (blueprints don't
# carry a script= field yet — see cron/cron-jobs.md's "Install path" note):
cp 01-job-discovery/scripts/discovery-wake-gate.py ~/.hermes/scripts/
hermes cron edit <discovery-scan-job-id> --script discovery-wake-gate.py
cp 13-interview-prep/scripts/interview-prep-wake-gate.py ~/.hermes/scripts/
hermes cron edit <interview-prep-job-id> --script interview-prep-wake-gate.py
# Every other job (open-web sweep, ghost-check, the monthly refreshes, the
# backup trio, social listening, career-pulse, prospecting, career-path
# re-evaluation, the outreach send-path jobs 19-21, and the rest) isn't
# blueprinted — see cron/cron-jobs.md for each exact command. Do not count
# them from here; cron-jobs.md is the register and this line is not.

# 7. Seed the config files that ship as templates. Every one of these is
#    seeded through a conversation, never hand-filled — the elicitation is
#    what confirms each fact instead of assuming it. Copy first so there
#    is somewhere to write:
cp shared/discovery_queries.yaml.template        shared/discovery_queries.yaml
cp shared/dynamic-target-calibration.yaml.template shared/dynamic-target-calibration.yaml
cp shared/pitch-catalog.yaml.template            shared/pitch-catalog.yaml
cp shared/output-templates.yaml.template         shared/output-templates.yaml
cp shared/enrichment-provider-keys.yaml.template shared/enrichment-provider-keys.yaml
cp shared/enrichment-tier-usage.yaml.template    shared/enrichment-tier-usage.yaml
# Seeded by: 07-context-architect (calibration, pitch catalog),
# 21-output-templates (output templates, empty by default and populated
# only through its own conversation), 22-contact-enrichment (both
# enrichment files — keys go in 1Password, never in the YAML).

# 8. OPTIONAL COMPONENTS — see "Optional components and their
#    dependencies" below. Skip this step entirely and everything above
#    still works; the two features it enables degrade to absent, not
#    broken.

# 9. Confirm the gateway is running so cron actually fires
hermes gateway install
```

The remaining cron jobs — 10 through 16, covering social listening,
career-pulse check-ins and profile monitoring, cold prospecting, career-path
re-evaluation, enrichment cycle reset, and the bi-monthly configuration
drift check — are not blueprinted. `cron/cron-jobs.md` carries the exact
command for each. Job 16 is worth registering even if the others wait:
it is what keeps four rarely-fired skills from being archived if you
ever hand this package to the curator.

## Optional components and their dependencies

The core pipeline needs Hermes, Python and SQLite. Two features carry
dependencies beyond that, and both are genuinely optional — neither is
required for an application to be discovered, tailored, gated and
submitted.

### Title taxonomy vector index — recommended

Powers `07-context-architect`'s Phase 1.5 adjacent-title expansion, which
is what keeps `target-profile.yaml`'s `title_variants` wider than the
titles Kene already thought of.

```bash
pip install fastembed sqlite-vec --break-system-packages
```

Without it, `title_taxonomy_builder.py`'s embed stage cannot run. Phase
1.5 falls back to the titles already recorded — narrower discovery, not a
broken pipeline.

### qmd retrieval layer — optional

Cross-corpus search over the research caches. Full scope and reasoning in
`07-context-architect/references/qmd-retrieval-layer.md`.

```bash
# Node >= 22 is required
node --version
brew install sqlite    # macOS only — system SQLite lacks extension loading
curl -fsSL https://raw.githubusercontent.com/tobi/qmd/main/install.sh | sh

cd ~/.hermes/skills/job-hunting
qmd collection add shared/company_research_cache    --name company-research
qmd collection add shared/individual_research_cache --name people-research
qmd collection add shared/interview_intel_cache     --name interview-intel
qmd context add qmd://company-research  "Per-employer research: mission, stage, news, values language, candidate and employee sentiment, reported interview style"
qmd context add qmd://people-research   "Per-person research on recruiters, hiring managers and cold-outreach targets"
qmd context add qmd://interview-intel   "Interview intelligence by role, industry and company: reported questions, formats and preparation guidance"
qmd embed
```

Cron job 17 keeps the index fresh and **no-ops cleanly if qmd is absent**,
so skipping this does not produce a nightly failure.

### If dependency count is your binding constraint

These are two separate embedding stacks — `fastembed` here, qmd's own
models there — over genuinely disjoint corpora, so neither duplicates the
other's work. But if you can only carry one: **keep the taxonomy index and
drop qmd.** The taxonomy has one well-defined consumer and no substitute;
qmd's value is breadth, and its absence costs you cross-corpus questions
you can still answer by hand.

## Folder layout

```
job-hunting/
├── README.md                      # this file
├── 00-orchestrator/                # entry point — routes stage to stage;
│   │                                 # carries the pipeline-sweep blueprint
│   └── references/
│       └── parallel-pipeline-sweep.md  # optional delegate_task-based
│                                         # parallel sweep, off by default
├── 01-job-discovery/                # cron-eligible: find & queue postings;
│   │                                 # carries the discovery-scan blueprint
│   └── scripts/
│       └── discovery-wake-gate.py   # cron wakeAgent cost-control gate —
│                                     # see 01-job-discovery/SKILL.md
├── 02-jd-parser/                   # Chat 1, unchanged
├── 03-resume-match/                 # Chat 2, unchanged
├── 04-keyword-analysis/             # Chat 3A, unchanged (+ JSON schema reference)
├── 05-resume-customizer/            # Chat 3B + Splendor tactics, docx output,
│                                     # + humanizer pass (Phase 7)
├── 06-cover-letter/                  # Chat 4 + Splendor's 5-paragraph formula,
│   │                                 # + humanizer pass
│   └── references/
│       ├── cover-letter-formula.md
│       └── anti-slop-checklist.md   # job-application-specific AI-tell list,
│                                     # used by 06 and 08
├── 07-context-architect/            # Chat 5A, now writes into Hermes memory
│   └── references/                   # question bank crawl+curate, title
│                                     # taxonomy build+embed+query, answer
│                                     # variants, gap-analysis engine, voice
│                                     # interview mode, optional Holographic
│                                     # memory layer (off by default) — see
│                                     # that skill's own "Reference files"
│                                     # section
├── 08-application-qa/                # Chat 5B, unchanged + humanizer pass
├── 09-risk-tactics-gate/             # NEW — verifies exact-phrase/title tactics,
│   │                                 # fidelity_mode-aware (see its own
│   │                                 # "Fidelity mode" section); flags gaps
│   │                                 # into the open_gaps DB table, not MEMORY.md
│   └── references/
│       └── moa-cross-check.md       # optional, human-initiated second
│                                     # opinion on borderline title-matches
├── 10-approval-and-submit/           # NEW — the human-click boundary,
│                                     # now enforced by 3 independent layers
├── 11-analytics-and-learning/        # NEW — metrics + self-improvement loop,
│   │                                 # now also runs email-insight extraction;
│   │                                 # carries the weekly-review blueprint
│   ├── references/
│   │   └── gepa-self-evolution.md   # optional Tier 2: evolutionary
│   │                                 # optimization for 05/06/08 only,
│   │                                 # manual/quarterly, never cron
│   └── scripts/
│       └── build_gepa_golden_set.py # builds Tier 2's eval dataset from
│                                     # real applications.db outcomes
├── 12-company-research/              # NEW — cached employer research (per-
│                                     # company, feeds 05/06/07/08 — see
│                                     # that skill's own "Where this plugs
│                                     # in" section); also read by 13's
│                                     # interviewer-research step; step 2.5
│                                     # adds a passive domain-age signal
│                                     # (optional research/domain-intel skill)
│                                     # surfaced to Kene via 10's approval
│                                     # message when flagged
├── 13-interview-prep/                # NEW — prep brief + memento-flashcards
│   │                                 # deck once interview_request_at is
│   │                                 # set; live study session on request
│   └── scripts/
│       └── interview-prep-wake-gate.py  # cron wakeAgent gate — pure DB
│                                         # query, see that skill's own
│                                         # "Trigger conditions" section
├── shared/
│   ├── pipeline-rules.md            # the hard rules everything else obeys
│   ├── applications_db_schema.sql   # includes open_gaps and
│   │                                 # last_interview_prep_at — see the
│   │                                 # file's own migration note if
│   │                                 # upgrading an existing database;
│   │                                 # status flow now formalizes
│   │                                 # discovered -> building -> staged
│   │                                 # -> awaiting_approval (see the
│   │                                 # column's own comment)
│   ├── email-insight-extraction.md  # what counts as a notable email
│   │                                 # detail, shared by 01/11's email reads
│   ├── tier-config.yaml             # daily staging cap
│   ├── target-profile.yaml.template # structured target profile — copy to
│   │                                 # target-profile.yaml, filled via
│   │                                 # 07-context-architect's Phase 0
│   │                                 # (Phase 0.5 for fidelity_mode)
│   ├── sources.yaml.template        # discovery source config — copy to
│   │                                 # sources.yaml, grows as sources are
│   │                                 # onboarded (see file's own notes)
│   ├── company_research_cache/      # per-company .md files (12), plus
│   │                                 # per-interviewer {slug}__interviewers.md
│   │                                 # files (13)
│   └── interview_prep/              # per-application prep briefs (13)
├── 14-social-discovery-outreach/    # social job leads + cold DM/reply drafting
│   └── references/
│       ├── platform-capability-matrix.md  # per-platform send tier — read
│       │                                    # before touching any platform
│       ├── cold-dm-email-schema.md
│       └── linkedin-methods.md
├── 16-career-pulse/                 # journal check-ins; career-event cascade
│   └── scripts/
│       └── journal-export.py        # projects career_journal to markdown so
│                                     # qmd can index it — DB stays canonical
├── 17-cold-prospecting/             # pitching with no posted opening
├── 18-skill-composer/               # add/modify a skill in this pipeline
├── 19-career-path-planner/          # current role -> target title, via
│                                     # stepping stones where the gap is
│                                     # role-gated rather than self-closable
├── 20-interests-profile/            # hobbies, side projects, RIASEC vector
├── 21-output-templates/             # saved formats for outward artifacts
├── 22-contact-enrichment/           # verified contact details, tiered by cost
├── 23-portfolio-onepager/           # one public page, generated from
│                                     # confirmed memory. NOT a site builder
├── 24-linkedin-profile-optimizer/    # audits Kene's OWN profile as a
│                                     # landing page. NOT outreach to others
├── onboarding/                      # fresh install; paced settings rollout
├── cron/cron-jobs.md                # every scheduled job — 4 of them
├── cron/executions.py               # execution ledger: what ran, what
│                                     # went silent, which gate is stuck
│                                     # install as one-tap blueprint
│                                     # suggestions, the rest stay manual
├── templates/                       # starter files to COPY and fill. Not
│   ├── MEMORY.md                    # runtime state — the live copies sit
│   ├── USER.md                      # in memory/ once seeded.
│   ├── career-timeline.md
│   ├── domain-knowledge.md
│   └── star-story-bank.md
├── ADDENDUM-CHANGELOG.md            # addendum package v2-v12 history
├── hermes-capability-audit.md
└── security/
    ├── security-setup.md            # DM pairing, command approval,
    │                                 # pre_tool_call hook, containers
    ├── backup-and-recovery.md       # what is worth saving, in three tiers
    ├── email-integration-setup.md   # use the bundled himalaya skill, not
    │                                 # a third-party MCP — and why
    ├── hooks/
    │   └── verify-submit-approval.py  # pre_tool_call submit-gate hook —
    │                                     # layer 3 of Rule 1's enforcement
    └── scripts/
        ├── backup.sh                # cron 8, nightly Tier 1
        ├── backup-tier2.sh          # cron 8c, weekly Tier 2
        └── verify-restore.sh        # cron 8b, quarterly restore check
```

`00-orchestrator/scripts/dry-run.py` — run after any schema change and
before a first real run. 19 invariants, no network, throwaway database.

**Created at runtime, not shipped**: `shared/applications.db`, the five
`*_cache/` directories, `shared/journal_export/`, and the qmd index. All
derived or generated — `security/backup-and-recovery.md` sorts which are
worth backing up, and most are not.

## Where every advanced Hermes feature you asked about actually gets used

You asked me to name every point of use for these, not just describe them
in the abstract. Here's the consolidated map — each line points at the
file that implements it.

### 1. Self-improving skill loop + full analytics

- `11-analytics-and-learning/references/metrics-schema.md` — every metric
  tracked (funnel, timing, tactic flags, outcome rates, correlation
  checks, system health).
- `shared/applications_db_schema.sql` — the DB those metrics live in.
- `11-analytics-and-learning/SKILL.md` — the weekly cron job that runs
  correlation checks against real outcome data and proposes specific,
  evidence-backed edits to other skills (e.g. "drop values-alignment by
  default," "tighten the speed window") via `skill_manage`, staged for
  Kene's approval rather than applied silently.
- `cron/cron-jobs.md` job #5 — the schedule that triggers this.

### 2. Agent-curated memory

- `07-context-architect/SKILL.md` — the only skill allowed to write new
  facts, and only after Kene confirms them (Rule 5).
- `templates/USER.md` — durable identity facts (~500-token budget).
- `templates/MEMORY.md` — standing instructions + current strategy
  notes the self-improvement loop updates over time.
- `templates/star-story-bank.md`, `templates/career-timeline.md`,
  `domain-knowledge.md.template` — the full narrative database, loaded
  as skill references by `06-cover-letter` and `08-application-qa`, and
  by `13-interview-prep`'s flashcard build (the confirmed `qb_XXXX`
  variant-table answers specifically — see that skill's Part 2).
- `07-context-architect/references/holographic-memory-layer.md` —
  optional, off by default: a parallel atomic-fact layer alongside the
  files above, for when the STAR bank has grown past hand-checking size.
  Read this before enabling it — it documents a tested limitation in the
  provider's own `contradict` action, not just its advertised behavior.
- `09-risk-tactics-gate/SKILL.md` — reads memory to verify every
  claim-changing tactic before it's applied.

### 3. Cross-session recall (FTS5 session search — distinct from curated memory above)

This is for "did we already deal with this?" recall from raw past
conversations, not the concise curated facts in MEMORY.md/USER.md.
Concrete points of use:

- **Dedup beyond the DB**: if Kene once said in passing "I don't want to
  work for [company] again" and that never got written into MEMORY.md as
  a standing instruction, `01-job-discovery` can still catch it by
  searching session history for the company name before queuing a
  posting.
- **Consistency across applications**: `08-application-qa` can search
  past sessions for how a similar question was answered at a different
  company, so Kene's story about the same project doesn't drift or
  contradict itself across applications months apart.
- **Recovering informal interview feedback**: if Kene mentions "they said
  my system-design answer was thin" in a normal chat rather than a
  formal outcome update, `11-analytics-and-learning` can retrieve that
  later via session search when reviewing why a particular application
  stalled, even though it was never logged as a structured DB field.
- **Resolving ambiguity in memory**: if two entries in the STAR bank seem
  to describe the same project differently, `07-context-architect` can
  scroll back to the original conversation where the story was built to
  see exactly what was said, rather than guessing which version is right.
- **"What did we decide about X"**: any time Kene asks the pipeline to
  recall a past decision (e.g. "did we already agree on a title-matching
  rule for PM roles?") — this is a direct `session_search` (discover
  mode) call, not a memory lookup.

### 4. Cron scheduler for unattended automation

- `cron/cron-jobs.md` — the register of every scheduled job, with exact
  schedules and commands. It is the single source of truth for what runs
  and when; this section deliberately does not re-list them, because a
  second copy of that list is what went stale here before (it named nine
  jobs long after there were more than twice that).
- Jobs 1, 3, 5, and 9 ship as **blueprints** (`metadata.hermes.blueprint`
  in each skill's own frontmatter) rather than requiring hand-typed
  `hermes cron create` commands: installing the package offers all four
  as one-tap `/suggestions accept` prompts. See `cron/cron-jobs.md`'s
  "Install path has changed" section for exactly what that looks like
  and why every other job stays manual (mainly: a skill can only
  carry one blueprint, and several of these jobs share a skill with one
  that's already carrying a schedule).
- Jobs 1 and 9 each carry a `wakeAgent` pre-run gate script that skips
  the LLM turn entirely — zero token cost — on ticks where a cheap check
  confirms there's nothing to do:
  `01-job-discovery/scripts/discovery-wake-gate.py` (source-fetch based,
  fails open on anything it can't verify) and
  `13-interview-prep/scripts/interview-prep-wake-gate.py` (pure DB
  query, so its skip decisions are strictly reliable rather than
  best-effort — see that skill's own "Trigger conditions" section for
  why the two gates are built differently on purpose).
- The one thing deliberately **excluded** from cron: the actual submit
  action. Everything that reaches a real employer still needs a live,
  same-day Telegram tap — seeing why is the whole point of Rule 1. That
  boundary is now enforced three ways, not two — see section 5 below.

### 5. Security — command approval, DM pairing, container isolation

- `security/security-setup.md` — the full mapping, but in short:
  DM pairing controls who can approve/submit (critical if this is ever
  resold — one paired identity per customer); dangerous-command approval
  is the technical backstop behind `10-approval-and-submit`'s own review
  step, independent of it; a `pre_tool_call` hook
  (`security/hooks/verify-submit-approval.py`) adds a third, purpose-
  built layer specifically for this pipeline's submit action, checking
  the applications DB directly rather than relying on a generic pattern
  list; container isolation (Docker) is where the actual browser/
  form-filling runs, so a hostile job-posting page can't reach Kene's
  host machine or credentials.

### Added in the merge pass — Hermes skills adopted since

Same rule as the map above: each line names where the capability is
actually used, not what it is.

| Skill | Where it is used |
|---|---|
| `productivity/ocr-and-documents` | `02-jd-parser` step 1 (PDF job specs), `07-context-architect` Phase 1 (PDF resume/portfolio intake). Text layer first, OCR as fallback, and OCR'd figures get confirmed before they are written — a misread "32%" as "3.2%" is worse than a failed read. |
| `productivity/nano-pdf` | `05-resume-customizer` — fix a caught typo in place rather than regenerating and re-rolling wording already approved. |
| `research/qmd` | `07-context-architect/references/qmd-retrieval-layer.md` — cross-corpus search over the three research caches. Optional; cron 17 keeps the index fresh and no-ops if absent. |
| `media/youtube-content` | `12-company-research` step 2.7, `13-interview-prep`'s intel scrub. Transcripts only, and conditional on the target rather than a default sweep. |
| `social-media/xurl` | Named in `14-social-discovery-outreach`'s capability matrix as the X path for reply/DM/search. Deliberately **not** used for the quote/post stubs — that scope boundary is the skill's own. |
| `research/arxiv`, `github/codebase-inspection` | `13-interview-prep`, role-conditional branches triggered off the JD parser's classification. |
| `security/unbroker` | `16-career-pulse` — quarterly audit of what a recruiter finds when they search Kene. Own footprint only. |
| `finance/excel-author` | `10-approval-and-submit`'s offer stage — total comp across base, bonus, equity, vesting and COL. Models equity under three assumptions, produces no single score. |
| `communication/one-three-one-rule` | Offer decisions and `19-career-path-planner`. One issue, three options, one recommendation with its conditions stated. |
| `software-development/subagent-driven-development` | `parallel-pipeline-sweep.md` — `09-risk-tactics-gate` as the review half of the native two-stage pattern, so independence is structural rather than aspirational. |
| `mcp/mcp-oauth-remote-gateway`, `mcp/mcporter` | `security/security-setup.md` — headless OAuth, set up before the pipeline depends on a connector. |

**Considered and declined**, so the reasoning is not lost: `research/llm-wiki`
(the title taxonomy and question bank already are an interlinked KB with
their own build pipeline and vector index — this would be a second system
over the same corpus); `productivity/telephony` (voice drills are already
covered by `voice-interview-mode.md` without a Twilio dependency, and
call-recording law varies by jurisdiction); `mlops/instructor` (`guidance`
is used in fifteen places and works — swapping it would touch every JSON
schema here for a lateral gain); and **a Notion or Airtable mirror of the
applications DB** (A11) — the pitch is a nicer view of data the pipeline
already holds, and the price is a second copy of the system's only
durable record, kept in step by a sync process. `shared/db-concurrency.md`
covers what replicating this database costs in the Syncthing case, and a
hosted mirror is the same shape of problem with an API in the middle: two
places that disagree, and no answer to which one is right. If a nicer
view is what's wanted, read from the DB — `11-analytics-and-learning`
already reports from it on demand.

## Curator, adoption, and what can quietly disappear

Hermes ships a curator: an idle-triggered maintenance pass that runs
roughly weekly and can mark skills stale, archive them, or consolidate
them. It matters for this package because 24 skills all named
`job-hunting-*` are an unusually visible target for it, and because the
way you install them decides how much reach it has.

**Curator management is opt-in per skill.** The on-disk field is
`created_by: agent` in `~/.hermes/skills/.usage.json`, but despite the
name it is a policy flag, not provenance — it means "autonomous curation
may mutate or archive this," and you set it with `hermes curator adopt
<name>`. Skills you place by hand are *eligible* but not *managed*: the
curator's candidate list does not include them until you adopt them.

### The recommended posture

**Do not bulk-adopt this package.** Three consequences follow from
leaving the 25 skills unadopted, and all three are what you want:

| Behaviour | Unadopted | Adopted |
|---|---|---|
| Background review may rewrite the skill autonomously | No | Yes |
| Inactivity archival (stale 30d → archived 90d) | Never | Yes, unless cron-referenced |
| Eligible for consolidation into an umbrella skill | Never | Yes, if `curator.consolidate` is on |

The package still improves while unadopted. Job 5's weekly review writes
through `skill_manage` with `skills.write_approval`, which is a
consented, staged path and needs no adoption at all. Adoption buys
autonomous rewriting; it costs exposure to archival and consolidation.
Adopt selectively if you want it — `11-analytics-and-learning` is the
plausible candidate — not across the board.

### Why bulk adoption is specifically risky here

`curator.consolidate` is **off by default; leave it off.** When on, the
consolidation pass looks for prefix clusters and asks what umbrella
class they serve. Every skill here shares the `job-hunting-` prefix, so
they form one 23-member cluster, and the pass is explicitly instructed
that pairwise distinctness is *not* grounds for declining to merge. It
also rewrites cron job skill references to follow a consolidation, so
the scheduled jobs keep running against a merged skill that has lost the
per-stage detail. Nothing is deleted — archived skills go to
`~/.hermes/skills/.archive/` and are restorable — but the failure is
silent, which is the expensive part.

Two exemptions exist if you do adopt. Pinning a skill blocks archival
and consolidation, but it also blocks the background review's writes, so
it buys safety by removing the reason to adopt. Cron-referenced skills
are never auto-transitioned *and* stay writable, which is the only
combination that gets both — see `cron/cron-jobs.md`, where job 16
exists partly to keep the four rarely-fired skills referenced.

### The gap `skills.write_approval` does not close

`write_approval: true` gates every `skill_manage` write behind your
approval. It does **not** gate archival, which runs through a separate
path. So the gate protects you from unwanted edits while leaving an
adopted skill fully exposed to being archived out of the index after 90
days of inactivity. Two separate controls, one of which is a gate. Full
detail in `security/security-setup.md`.

## Editing these skill files

If you're adding a new stage or substantially rewriting an existing
`SKILL.md` in this package, load Hermes's bundled `software-development/
hermes-agent-skill-authoring` skill first — it's the house style this
whole ecosystem's `SKILL.md` files (frontmatter shape, progressive-
disclosure conventions, when to split something into `references/`)
already follows, and every file in this package was written/edited with
it loaded rather than reinventing conventions Hermes already has
opinions about. This applies to `skill_manage`-driven self-edits too
(`11-analytics-and-learning`'s Tier 1 proposals, and Tier 2's GEPA
output before it's hand-applied) — the same house style should hold
regardless of whether a change came from a person or from the
self-improvement loop.

## On the resale idea

The tier config (`shared/tier-config.yaml`) gives you the "10-20 → 100-200
per day" lever you described — it's just wired to staging volume, not
submission volume, per the earlier conversation. Happy to pick the
pricing/packaging discussion back up whenever you want; the technical
piece that made it safe to build is done.
