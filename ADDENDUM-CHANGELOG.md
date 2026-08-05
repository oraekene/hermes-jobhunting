# Addendum changelog — v2 to v28

## v28 — 2 August 2026: ADDENDUM-27 folded; the outreach send path lands

Originated as ADDENDUM-27's own `README-addendum.md` **v13** (29 July).
That package ran an independent version line reaching v13 while this one
was already at v27 — **the numbers are not comparable**, which is why this
is v28 rather than a merge of two v13s. Verbatim source preserved at
`.merge-history/addenda-27/README-addendum.md`.

**What actually differed, measured rather than assumed.** Eight of
ADDENDUM-27's ten `ADDENDUM.md` files are byte-identical to the
ADDENDUM-26 versions already folded at v-earlier; the other two differ
only in `reference/` vs `references/` spelling. Of its eleven `SKILL.md`
files, nine have counterparts here, and once path spelling is normalised
**eight diverge by nothing at all**. The ninth (`19-career-path-planner`)
diverged by 18 lines that are the older, thinner phrasing of content this
package already states more fully. So the fold is small and specific.

**A schema collision, caught by the migration chain check.**
`applications_db_schema_addendum_6.sql` existed in both packages as two
completely different migrations — 22 lines altering `applications`
(overqualification gate outcome) here, 79 lines altering `social_outreach`
and creating `x_follow_engagement_attempts` there. One filename, one chain
slot, one line in install step 4. Installing from either `shared/` silently
dropped the other. ADDENDUM-27's is now `addendum_19.sql`, **appended
rather than inserted** so a database already built from this chain applies
it forward with no renumbering of anything that already ran.

**The outreach send path, taken as one project.** Five new reference files
(`cold-dm-content-formula`, `linkedin-connection-flow`, `inmail-credits`,
`x-follow-pursuit`, `ig-fb-engagement-window`), the extended
`cold-dm-email-schema.md`, `site-access-model.md`'s model 4 carve-out,
`shared/inmail-credits.yaml.template`, migration `_19`, and cron jobs
**19–21** (numbered 15–17 in the source, where those numbers were already
live here). These do not separate: the schema's connection/x_follow_state/
ig_fb_window blocks, Rules 12–14, model 4 and the three cron jobs are one
mechanism.

**Rules 6–16, and the collision resolved.** This package's
`pipeline-rules-addendum.md` carried Rules 6–11 *and a second Rule 9 and a
second Rule 10* — different subject matter, identical numbers, in the file
that declares itself the tiebreaker. ADDENDUM-27's copy was clean 6–14 but
lacked those two rules entirely, so overwriting in either direction lost
work. Resolved as an append-only hybrid with the colliding pair renumbered
to **15 and 16**. `dry-run.py` now asserts rule numbers are unique and
contiguous.

**`24-linkedin-profile-optimizer`.** The one genuinely new skill.
ADDENDUM-27 numbered it 23, colliding with `23-portfolio-onepager`;
renumbered, and its 1,000-character frontmatter description converted to
house style (42 chars, under the index's 57-char truncation) with the
original relocated to `## When this skill applies`.

**Verifier: 19 → 24 invariants.** New: the chain is derived from `shared/`
rather than hand-listed (it had gone stale twice independently); README
step 4 must apply every migration in it; `install-check.py`'s authored
range must cover every migration on disk; rule numbers unique and
contiguous; and no file may state a stale `all N skills`/`all N jobs`
count. The last one found `00-orchestrator/SKILL.md` claiming 24.

## v27 — 31 July 2026: portfolio, properly

v26 shipped `23-portfolio-onepager` as a decision plus a scope. Four
questions exposed that the scope was right and the specification was thin
in the places that matter most.

**The CV/portfolio distinction, written down.** The difference is not
presentation, it is evidence: a CV **asserts** ("cut deploy time from 40
minutes to 6") because the format has no room for proof and the reader
has ninety seconds; a portfolio **shows** — repo, running thing,
notebook, writeup. That is the reason to build one at all, and it makes a
rule: a page carrying no artifact links is a CV with worse ATS
compatibility and should not be published.

Everything else follows. A CV is pushed to a reader holding the JD; a
portfolio is pulled by a reader who may know nothing and may have no role
in mind. A CV is frozen at send; a portfolio is live, public, and findable
by a current employer — which is why first publish raises discretion mode
once.

**Artifact links promoted from a footer list to the primary content.**
Seven types with the notes that actually matter: link the repo **root**
(a deep link into one file reads as cherry-picking); a notebook needs
outputs committed or a Colab that runs, because an `.ipynb` opening on
`import pandas as pd` is a link the reader closes; a repo needs a README
that survives thirty seconds. Link rot is checked at publish and
quarterly (`_18.sql`), and dead links are **reported, never silently
dropped** — the interesting failure is 403, not 404, since a repo flipped
private and a Colab needing access both keep a perfectly valid URL.

**Variants: two axes, not one.** "One per target-title cluster" was right
for applications and wrong for outreach. `17-cold-prospecting` has three
pitch modes and they need different pages, because the reader's question
differs — role-fit asks "could he do our job", service asks "would I hire
him for a defined piece of work", and a role-shaped page actively misreads
the second. Role-fit outreach reuses the application variant; only
role-creation and service justify their own.

Per-outreach relevance without per-outreach variants: **stable anchors**
per work item, deep-linked from outreach. The tailoring that matters is
which item they see first, and an anchor does that for free.

**Selection is Kene's (`portfolio-manifest.yaml`).** A generated pool he
never types, `always_include` / `never_include` globals where `never`
beats everything, and an ordered per-variant pick. Order is meaningful.
Two behaviours matter more than the schema: **a rebuild never silently
re-selects** — a page he curated should not rearrange itself because a new
STAR entry landed — and new material is **offered, never inserted**.

**Hosting: a default that removes the decision.** Asked once, at first
publish, never at generate. Default is Cloudflare Pages free tier, chosen
because Direct Upload needs no repo — which matters, since a
role-creation or service variant is not necessarily something to put in a
public GitHub repo, and a hosting default requiring one quietly forces a
disclosure decision.

**The skill runs the whole setup and never stores the credential.** Not
squeamishness: a Pages-scoped token can create and delete projects across
the account, and this package's folder is *synced* (v25). A token in a
file here is a token replicated to every machine that folder reaches. The
tools already solve it — `wrangler login` keeps its token in
`~/.config/`, headless uses `CLOUDFLARE_API_TOKEN` from the environment.
Kene does one thing himself: the one-time login.

**A real design (`assets/portfolio-template.html`,
`23-portfolio-onepager/references/page-design.md`).** The signature is a *receipt rail* — a
narrow left column with an index and a hairline running the item's height
and closing under its artifacts, so links read as stapled to the claim
rather than listed after it. The page's thesis, made structural. An item
with no artifacts looks visibly weaker than its neighbours, which is
correct: better feedback than a warning in a log.

Single column with a meaningful order rather than a card grid, because
cards imply parallel items to browse and this page has an argument.
Palette and type both chosen against the current AI-design defaults, with
reasoning recorded so a later edit is a decision rather than drift. Mono
marks everything that is *data* and separates it from everything that is
*claim*. Print stylesheet with URLs expanded, because a recruiter will
print it and a printed link is otherwise dead.

`_18.sql` is idempotent.


## v26 — 31 July 2026: the last five open items

Closing out `FINAL-PASS-CROSSCHECK.md`. Four small, one real.

**`fact_feedback` promoted from optional to on.** It was specified in two
places and marked "low priority, not a launch requirement" in both — so
the signal was generated on every run and discarded. Trust is the only
ranking dimension Holographic has, it starts at 0.5, and this call is the
only thing that moves it; left off, every fact sits at default forever
and the layer degrades to relevance-ranked retrieval over an
undifferentiated store, which is what it was adopted to improve on.

The grading rule is deliberately conservative about `unhelpful`, because
the feedback is asymmetric (+0.05 / −0.10, so two bad ratings undo four
good ones): only a fact Kene **edited out**, or one whose claim a gate
rejected, counts against it. **A rejected application does not**, and no
response is not a miss either — most rejections have nothing to do with
which story was picked, and rating on outcome alone would walk the whole
bank toward zero on noise. Turning it off is now `memory.fact_feedback:
false`, a decision with a stated cost rather than a default nobody
revisited.

**Fact influence (`fact-influence-scoring.md`, `_17.sql`) — the real
work.** Wiring feedback on makes trust scores move, but only along the
*reliability* axis. Nothing measured importance: "Kene's daughter is
called Ada" can be perfectly trustworthy and irrelevant, "Kene will not
relocate" is decisive, and both sat at 0.5.

Influence counts only events where a fact **materially changed an
output** — passed or failed a claim at a gate (weight 3), survived into a
staged document (2), drove a STAR selection (2), filtered a posting (1).
Not retrieval counts, which are trivially available and completely
misleading: the most-retrieved fact in any career bank is something like
a current job title, retrieved constantly and deciding almost nothing.
Retrieval without use scores zero.

Saturating curve rather than a linear count, so one heavily-reused fact
cannot dominate permanently — the signal is categorical, *does this fact
do work*, not how much. A 180-day trailing window, which is a real decay
function on the one dimension that can support one; `fact-conflict-
resolution.md` still declines to put a decay curve on *truth*.

**The two scores are never averaged.** Collapsing them recreates the
problem: a single number cannot say whether a fact ranked low for being
unreliable or unimportant, and those call for opposite responses. The
payoff is the corner neither dimension finds alone — **low trust, high
influence**: a fact deciding gates that keeps getting edited out is wrong
*and* load-bearing, and `v_low_trust_high_influence` surfaces it. Trust
alone buries it among unreliable trivia; influence alone flags it as
important without noticing anything is wrong.

Deliberately absent: any view shaped like a deletion candidate list. Zero
influence means "not yet needed", not dead weight — a career memory bank
exists to hold things until the day they matter, and the interest nobody
asked about for three years is the one that lands the conversation. The
digest reports a count, never a list.

**A11 recorded.** The Notion/Airtable mirror was decided by non-action
and never written down, so unprotected. Now in the declined block, and
the reasoning got sharper after v25: a hosted mirror is the Syncthing
problem with an API in the middle — two copies of the system's only
durable record, and no answer to which is right.

**R4.** A table in `cost-model.md` covering wake gates, `no_agent`,
`iteration_budget` and the budget together, with the ordering that
matters: each is cheaper than the one after it, only the cost model sees
the aggregate, and the fix for high spend is almost always a wake gate on
a frequent job rather than a lower budget.

**A26/A27 — decided, and built narrowly (`23-portfolio-onepager`).**
Deferred across several passes because it is the only addition that makes
a new user-facing deliverable rather than improving one. The answer is
build it: everything a one-pager needs is already confirmed memory, and
not building it means Kene hand-assembles the single most reusable
artifact in the search from a corpus this pipeline maintains.

The scope is where the judgement is. One page, static HTML, no build
step, versioned per target role — **not a site builder.** No CMS, no
themes, no sub-pages, no analytics. It writes files and prints deploy
commands; it holds no credentials and takes no provider dependency.
`09-risk-tactics-gate` runs over the page before publishing, which is the
one place that gate touches a non-application artifact and should: a
public page is read by every employer at once and outlives any single
application. Generate and publish are separate steps and publish asks.

Package is now 24 skills. `_17.sql` is idempotent.


## v25 — 31 July 2026: the three concurrency caveats, answered

v24's `db-concurrency.md` closed with three things it did not solve. All
three turned out to have real answers, and one of them was hiding a
hazard worse than the problem WAL was adopted to fix.

**Multi-host safety — a deliberate non-goal, now argued rather than
asserted.** The concurrency case for it is nil: this pipeline has exactly
one writer by design and its cron jobs run on one host. What was actually
pulling toward it is *replication* — wanting the data on a laptop as well
as the cloud instance. Different problem, different answer: sync a
`.backup` snapshot, never the live file.

**The Syncthing hazard — the important find.** Kene's Hermes instance
syncs via Syncthing, and WAL creates `-wal` and `-shm` sidecars. A
file-level syncer replicates those independently, producing torn state,
meaningless cross-host `-shm` files, or a `.sync-conflict-*` copy in
which one side's writes are silently gone. **This is worse than what WAL
fixed** — a failed write is loud and recoverable; a torn database is
neither. v24 shipped WAL without saying so. Now: an exclusion list, the
backup-snapshot pattern, and an `install-check.py` check that reads any
`.stignore` present and fails CRITICAL if it does not cover the database
— plus a scan for existing `.sync-conflict-*` files, because their
presence means it has already happened.

**Write throughput — solved structurally, via the outbox.** The previous
answer to write timeouts was "lower `max_concurrent_children`," which is
accepting a worse pipeline to work around a fixable design. Children now
write no SQL at all: one JSON file to `shared/.outbox/`, ingested by the
parent serially, one transaction per file, in `application_id` order.
File creates in distinct paths do not contend, so write contention goes
to roughly zero and concurrency is bounded by model spend and host
resources — the limits that should govern it. Two things fall out for
free: a crashed child leaves a complete record of what it did before
dying, which makes addendum 15's `vanished` outcome diagnosable rather
than merely labelled; and ingestion becomes idempotent and re-runnable.

**Ownership enforcement — `verify-db-ownership.py`.** The one flagged as
particularly important. The obvious design (parse the SQL, extract the
target id, compare) is fragile in the way that gets a control quietly
disabled — SQL arrives inside pipelines, heredocs and one-liners, and a
parser handling 90% provides 0% of the guarantee. So the predicate is
coarse and robust: **during an active sweep, only the registered writer
session may write to the DB.** Detecting write *intent* in a blob of text
is tractable; detecting *which row* is not. The outbox is what makes the
coarse rule livable — a child has no reason to write, so denying it costs
nothing.

**It fails OPEN, unlike the submit hook, deliberately.** That guards an
irreversible external action, so a false negative is unrecoverable. This
guards internal consistency, and a false positive would block a
legitimate write mid-build — manufacturing exactly the half-built
application addendum 15 exists to clean up. Getting the asymmetry
backwards either way is the mistake: a fail-closed ownership hook wedges
the pipeline on its first edge case, a fail-open submit hook is
decorative.

Worth noting what the hook is *not*: a replacement for the delegation
prompt. Blocks in `shared/.db_write_audit.jsonl` mean children are still
trying to write, which means the outbox instruction is not landing — a
prompt problem the hook is only masking.


## v24 — 31 July 2026: the audit's open items

Working from `AUDIT-TRIAGE.md`'s Bucket D. What these have in common is
that they are all **infrastructure rather than features**, which is
probably why they kept losing to capability adoptions across a dozen
versions — nothing about the package looked broken while they were
missing.

**C1 — concurrency (`shared/db-concurrency.md`, `_15.sql`).** Grep
returned zero hits for WAL, `journal_mode` or `busy_timeout` across the
whole tree, while the parallel sweep fans subagents out to write
concurrently to one SQLite file. SQLite's default on a held lock is to
**fail the write, not wait** — so a subagent's write silently failed, its
application never left `building`, and the stuck-batch check caught it
seven hours later as an anomaly. Right safety net, wrong primary
mechanism.

Three parts. The pragmas (WAL, busy timeout, `synchronous=NORMAL`,
`foreign_keys=ON`, in an `open_db()` helper rather than a README
instruction followed once). **`BEGIN IMMEDIATE`, never bare `BEGIN`** —
the least obvious rule in the file, since a deferred transaction cannot
be retried by `busy_timeout` once it holds a read lock, and so fails
instantly under exactly the contention the timeout exists for. And the
one that matters most: **row ownership.** A subagent owns exactly one
`applications` row and writes nothing else. Pragmas reduce the cost of a
collision; ownership prevents most collisions existing at all.

**C6 — failure semantics.** Same file, addendum 15. `failed` status,
`build_attempts`, per-attempt history, and the rule that **a child never
sets `failed` itself** — a crashed child cannot report anything, so a
status only a healthy child could set would be exactly wrong for the case
that matters. Retries restart at stage 2, never mid-pipeline; three
attempts then stop.

**C2 — `last_confirmed_at` made load-bearing
(`fact-conflict-resolution.md`, `_16.sql`).** It was written in two
places, declared null in two more, and **read nowhere.** More recent
confirmation wins; the older is superseded, never deleted. Durable /
volatile as a binary flag rather than a decay score, because there is no
principled half-life for "prefers remote work" and inventing one produces
numbers that look meaningful and aren't. Urgency stays derived at read
time — the correct answer there was to build nothing.

Worth noting the shape of the problem: every other memory upgrade in this
package sharpened *retrieval*. None of them made stale facts stop being
returned, and better retrieval over unaged memory returns the wrong
answer faster.

**C7 / §2.4 — `interests-profile.md`.** It has no evidence bar by design,
and `09-risk-tactics-gate` accepts it as evidence at
`profile_stage: first_time`. A time bar is the only bar such a file can
carry: 12-month reconfirmation, `Last confirmed:` separate from `Added:`,
stale entries flagged but **not usable as risk-gate evidence until
reconfirmed**. That last constraint is the one place staleness does more
than label, because it is the one place a stale entry leaves the building.

**§4.6 / §4.5 — install verification
(`00-orchestrator/scripts/install-check.py`, Rule 0).** The submit hook
is Rule 1's third enforcement layer and was registered by hand at install
step 5 with **nothing anywhere verifying it was live**. Skip the step and
Rule 1 degrades silently to an instruction in a markdown file. The check
also catches a registration pointing at a path that doesn't exist, which
is worse than no registration — it reads as correct and vetoes nothing.
Read-only by design: a safety gate that reinstalls itself is a gate
nobody has to think about. Rule 0 in `pipeline-rules.md` states the
whole-package install requirement where a partial installer would
actually hit it.

**§4.7 — cost model (`shared/cost-model.md`).** No budget, no per-job
estimate, no breaker for *model* spend anywhere, against 18 cron jobs
plus subagent fan-out plus the new stepping-stone research burst. Spend
is **estimated, not metered**, and labelled as such — a coarse estimate
catches the shape of a problem (a week of 4× builds, a re-plan that fanned
to thirty candidates) and that is what the absence of this file was
actually costing. Tiering follows deadlines: an interview is on Thursday
regardless of budget, a discovery tick can wait. Nothing here can block
`10-approval-and-submit`.

**C3** — the `13-interview-prep` line claiming blueprints ship enabled by
default, corrected to match `cron-jobs.md`.

**A7 — the pressure drill (`13-interview-prep` Part 3c).** The last
A-series item outstanding. Parts 3 and 3b test whether Kene can recall
his material; nothing tested whether it holds up when an interviewer says
"that sounds like your team's win." Named "pressure drill" rather than
"hostile interviewer" deliberately — the version that simulates rudeness
teaches nothing about the answers and just feels bad. Sceptical on
substance, three follow-ups maximum, never against protected
characteristics, never from cron, and it stops if it is going badly the
night before an interview.

`_15.sql` joins `_14.sql` as non-idempotent (`ALTER TABLE ADD COLUMN`).
`_16.sql` is fully idempotent.



## v23 — 31 July 2026: the stepping-stone engine

**"Has this already been done?"** No — and the honest version of the
answer is that it had been *recorded* rather than built.
`19-career-path-planner` Step 3 carried one bullet ("if the `job_zone`
delta is more than one band, propose one or two plausible stepping-stone
titles, resolved the same way mode (b)/(c) resolves adjacent titles") and
`career_path_plan_stepping_stones` carried four working columns. That was
enough to store a hop somebody had already decided on. There was no
trigger beyond the `job_zone` delta, no candidate-generation method
behind "resolved the same way", no check that a candidate was reachable
or that the hop was worth taking, no per-hop gap analysis, and no
lifecycle for a hop that gets skipped, substituted or overtaken.

Built out in `19-career-path-planner/references/stepping-stone-engine.md`
plus `shared/applications_db_schema_addendum_14.sql`. Six things changed
in substance:

1. **Gap classification** — `self_closable` / `role_gated` /
   `tenure_gated` / `credential_gated`. The piece the old design had no
   equivalent of, and the one the rest rests on: a `role_gated` gap
   ("has managed people", "has owned a budget") cannot be closed by any
   roadmap item, because no amount of Kene's own effort closes it. That
   is the actual reason stepping stones exist, and without the
   distinction the feature is a seniority-interpolation trick.
2. **Four triggers, not one.** The `job_zone` rule stays as the first;
   a `role_gated` gap now fires the engine **regardless of `job_zone`**,
   which is the most common real case and one the old rule missed
   completely — Analyst → Analytics Lead is often a single band. Plus
   domain distance (mode c) and gap density. With an explicit
   suppression rule: all-`self_closable` gaps produce "this is a direct
   move" rather than an invented hop.
3. **Two-sided scoring**, `reachability × bridge_value` — a product, so
   that a candidate closing nothing cannot rank on reachability alone.
   `bridge_value` (of the gaps Kene cannot close where he is, how many
   does this role structurally hand him) is where most of the value sits
   and had no representation at all before.
4. **Four disqualifying checks** — monotonicity, comp non-regression
   (allowed, but priced explicitly and asked as its own question, with a
   scoped exemption from addendum 13's `seniority_floor`), market
   liquidity via a read-only posting census in Kene's real market, and
   dwell time.
5. **Hop-scoped roadmap.** `career_path_plan_roadmap_items` gains
   `hop_id`; Step 2 runs once per hop. This is the change with the most
   day-to-day effect — the difference between a list Kene can start on
   Monday and a list of requirements for a role two moves away, which is
   the standard way career plans fail.
6. **A real lifecycle.** `achieved` → `matured` (holding the role is not
   the same as having got what the role was chosen for), plus `skipped`,
   `substituted` and `abandoned`, re-plan triggers, and
   opportunistic-advancement handling.

Two consequences elsewhere. **Step 5 is now hop-aware** — it previously
knew only about the final target and would have pointed discovery at a
role two moves away while the actionable one went unsearched. **Cron job
14 proposes rather than re-plans** — a matured hop means the remaining
path was scored against a profile that no longer exists and must be
regenerated, which ends in a one-three-one choice and is therefore a
conversation, not something a Monday cron job settles on Kene's behalf.

The three-path presentation is also what makes the existing
`one-three-one-rule` adoption (S11) real rather than formal: with a
single path there was nothing to choose between, and a choice between one
option and nothing is a rubber stamp. The direct path is now always
generated and always shown, including when triggers fired.

`_14.sql` is the one schema file in this package that is **not
idempotent** — SQLite has no `ALTER TABLE ADD COLUMN IF NOT EXISTS`, so a
second run errors on the ALTER block. Visible and safe, but worth the
note in the install section.



Version history carried over verbatim from `README-addendum.md` when the
addendum package was merged into the main package. Kept as its own file
rather than interleaved into `README.md`: it is a record of how the
addendum was built, not instructions for running the merged package.
The companion record for the base package is `HERMES_UPGRADE_CHANGELOG.md`.

## v12 — 25 July 2026: output-template modes rebuilt, site access model made explicit

**"Has this already been covered?"** Partially, not fully — said
directly rather than assumed. The earlier `21-output-templates` design
had one dial (`strictness: guide|strict`) where two independent
questions actually needed answering: *how* a template gets specified,
and *how it interacts with the built-in default*. Rebuilt as two
genuinely separate axes: **`input_method`** (`strict_outline` /
`general_instructions` / `writing_samples`) and **`application_mode`**
(`append` — layered onto the built-in structure, preserving its
established advantages — or `replace` — the built-in default isn't
consulted at all), with `strictness` remaining as a third, independent
dial on top of whichever structure results. Each of the six
combinations gets its own merge behavior spelled out; one combination
(`replace` + `general_instructions`) is flagged as genuinely
higher-risk than the other five, since it has the least to anchor a
derived structure to, and gets its own extra confirmation step rather
than being treated the same as the rest.

**"Is there a stage where users log into their accounts, and would
things be easier from a logged-in session?"** Answered honestly: this
was never explicitly specified before — several skills referenced
"browser reads" without ever saying whose session. `shared/site-
access-model.md` names four real models (no-login, OAuth-app-level
delegation, Kene's own already-authenticated session driven via the
Hermes-native bundled `computer-use` skill, and avoid) and answers the
question directly: yes, some things are genuinely easier from a
logged-in session — LinkedIn chief among them — and the right mechanism
for that is driving Kene's *own* browser via `computer-use` rather than
Hermes independently storing or managing his credentials, which gets
the capability benefit without creating a new credential-security
surface. Wired into `platform-capability-matrix.md`,
`22-contact-enrichment`'s LinkedIn identification step,
`12-company-research`, and a short `10-approval-and-submit/ADDENDUM.md`
making that skill's own already-implicit assumption explicit rather
than leaving it unstated.

**On blue-collar work and business ownership**: answered in
conversation, not built this round — see that turn's response for the
honest breakdown (blue-collar *employment* matching is well-supported
by the underlying O*NET/RIASEC infrastructure but the job-source
coverage for trades-specific channels was never verified; business
*ownership/founding* is a genuinely different problem this pipeline
doesn't currently address at all, offered as a future build rather than
assumed covered).

## v11 — 25 July 2026: closing real gaps, a full official-catalog crawl, LinkedIn specifics

Six direct questions, answered by checking rather than asserting.

**"Have you fully built the cascade?"** No — real gaps, now fixed in
`22-contact-enrichment/SKILL.md`'s Part B: the pattern-frequency table
was referenced but never written (now a real 8-row table), the catch-
all-probe algorithm was named but not specified (now a concrete step
sequence), there was no defined threshold for when Tier 1 escalates to
Tier 2 (now three explicit conditions), Tier 3 had no actual budget cap
(now `tier3_monthly_budget_usd`, defaults to `$0`, opt-in), and no
default verifier was named (now ZeroBounce's free tier, explicitly).

**"Can users connect their own paid API keys?"** No, hadn't been built
at all. Now has been — `22-contact-enrichment/references/api-key-setup.md`, using the official
Hermes `security/1password` optional skill rather than inventing
credential storage. `shared/enrichment-provider-keys.yaml` stores a
1Password item *reference* only, never a raw key, kept deliberately
separate from the budget cap above (connecting a key answers "can I use
this provider," the budget answers "how much am I allowed to spend").

**"Have you built the full email-finding comparison?"** Also had a real
gap: the token-use/bot-restriction/rate-limit comparison from the
original research got dropped when the file turned into a pure cost
ranking. Restored as its own full section in `enrichment-tools-
pricing.md`, finished now rather than waiting on bookmarks, as asked.

**"Can you get emails off LinkedIn?"** New `references/linkedin-
methods.md` — direct disclosure (profile contact info, self-shared in
posts), third-party finders in API mode (low risk, what this pipeline
uses), the same tools' browser-extension mode (real account risk,
explicitly not used, per Rule 6), and the realistic default: LinkedIn
mostly confirms *who*, the pattern-gen cascade finds the *email*.

**The official catalog crawl, both pages fetched directly**: no bundled
or optional Hermes skill does enrichment/CRM/email-finding as its core
job — confirms this skill's free-first, mostly-self-built design was
the right call. What the crawl did surface and get wired in:
`domain-intel` (the actual MX-check tool, no API key needed),
`research/parallel-cli` (the one genuinely Hermes-official enrichment-
capable skill, added to Tier 2's rotation), `security/1password` (the
API-key mechanism above), `osint-investigation` and `sherlock`
(corroboration tools, noted), and `scrapling` (stealth browser
automation with Cloudflare bypass — available, and explicitly *not*
used against LinkedIn or similar, the same restraint Rule 6 already
requires). One correction: "Explorium," described as Hermes-native in
an earlier pass, isn't in either official catalog — recorded as
third-party/unconfirmed instead.

Also new: cron job 14, a daily (not monthly — provider cycles don't
reset on the 1st) reset check for `enrichment-tier-usage.yaml`'s
per-provider free-tier counters.

## v10 — 25 July 2026: contact enrichment (person-ID + email finding)

**`22-contact-enrichment/`** (new) — closes a gap an earlier example
glossed over rather than actually solved: given only a company name,
how do you get to a real person's name, role, and verified email. Two
parts: Part A identifies who's actually the hiring manager or decision
maker (never asserted with certainty — confidence-scored, evidence-
cited, same "hypothesis not assertion" discipline as the existing
target-claim gate), explicitly distinguishing that from recruiter-track
contacts, which stay legitimate but never primary. Part B enriches the
identified person with a verified email through a **free-first
cascade**: public sources → self-hosted tools (pattern-generation +
MX/catch-all/SMTP verification, and `theHarvester` for broader recon —
both genuinely $0, not just "free tier") → free tiers of commercial
APIs, **rotated across providers** rather than picked-one-and-exhausted
(`22-contact-enrichment/references/free-tier-rotation.md` + `shared/enrichment-tier-usage.yaml
.template` — stacking Hunter/Snov.io/GetProspect/Prospeo/Skrapp's free
allowances gets to 325+ free lookups/month before any single one runs
out) → paid, budget-capped, last resort.

`22-contact-enrichment/references/enrichment-tools-pricing.md` is the full research pass
requested — every enrichment tool found (open-source, free-tier
commercial, paid, and the one option that's packaged specifically *as*
a Hermes skill rather than a generic MCP wrapper — Explorium's GTM
plugin), ranked lowest cost to highest. One correction worth surfacing
here directly: Apollo does have a genuine $0 tier, confirming the
instinct that prompted this research — but it's been cut sharply over
2025-2026 (variously reported 100-900 credits/month, down from a former
10,000), and a non-corporate email address caps it at the lower end per
one source. Also corrected in passing: Clearbit is dead as a standalone
product (absorbed into HubSpot's Breeze Intelligence, free tools ended
April 2025) and NeverBounce dropped its free tier — both still show up
in older comparison articles.

Wired into `14-social-discovery-outreach` and `17-cold-prospecting`:
both now call this skill whenever a contact is known by company/role
but not by name, and both carry the same priority rule explicitly —
hiring manager/decision maker first, recruiter-track staged as its own
separate, differently-framed outreach, never merged or given equal
billing by default. `cold-dm-email-schema.md`'s contact block gets two
new structured fields for this (`contact_priority`,
`identification_confidence`) rather than leaving the classification
buried in free text — `applications_db_schema_addendum_5.sql` catches
the DB up to match.

## v9 — 25 July 2026: output templates

Generalizes something that already existed in narrow form: every
outward-facing artifact this pipeline produces already had exactly one
built-in structural guide (`cover-letter-formula.md`,
`cold-dm-email-schema.md`'s message shape). `21-output-templates/`
turns that into any number of named, user-authored templates per
artifact type (cover letters, application answers, resumes, cold
emails/DMs, social replies, plus an inert stub for social posts),
elicited entirely through conversation — no form — reusing each
producing skill's *existing* parameter vocabulary rather than inventing
a parallel one (checked `08-application-qa`'s and `06-cover-letter`'s
actual current files before writing the checklist, not assumed).

**On the `/learn` suggestion specifically, since it was asked for
directly**: partially right, and worth separating which part. `/learn`'s
output — a new SKILL.md — is the wrong shape for a template (a data
record an existing skill selects between, not new Hermes behavior);
using it literally would mean every named template becomes its own
skill file, real bloat, and a direct conflict with `18-skill-composer`'s
whole modify-vs-create job. `/learn`'s *source-ingestion* side — reading
a URL, a directory, a walked-through session — was the right part to
keep, and did: a pasted example or uploaded past message can seed a
template's first draft, always still confirmed conversationally before
saving.

A template governs structure only, never content — `strictness: guide`
by default, `strict` only on explicit request — and `output-
templates.yaml` is confirmed directly by this skill rather than routed
through `07-context-architect` (new **Rule 11**): a template is a
pipeline-behavior preference, not career-fact memory, a genuinely
different kind of thing from what Rule 5 already governs. Purely
additive throughout — every producing skill falls back to its existing
built-in default when nothing's been saved, so nobody who never creates
a template sees any behavior change.

## v8 — 25 July 2026: full career-path tracking, and an actual implementation audit

Two direct questions, both answered by actually checking rather than
asserting.

**"I don't want the tracking lightweight, I want full tracking."**
Fair — it was lightweight. Replaced the single `career_path_plan_progress`
table (roadmap items packed into one JSON column, overwritten in place,
no history) with six normalized tables in
`applications_db_schema_addendum_4.sql`: plan header, per-stepping-stone
status, per-roadmap-item rows (with `category` and
`resolved_by_evidence_ref` — *what specifically* closed each item, not
just that it closed), a full status-change history table, a
re-evaluation log (one row per run, not one overwritten timestamp), and
a link table connecting a plan to the real applications it eventually
produces. The `.md` plan record's relationship to the database flips
accordingly: the database is now the tracked source of truth, the
markdown is a generated rendering of it, not the other way around. One
real cost, stated plainly rather than hidden: the migration drops the
old table outright, since its shape can't be safely auto-migrated into
the new one — any plan already tracked under the old design loses its
tracking history (not its content) when this runs.

**"Are all the new skills and features fully implemented — is the
schema addendum fully implemented?"** Ran an actual audit (grepped
every table name and reference-file path mentioned in prose against
what's really on disk) rather than answering from memory. Result: every
skill folder has its `SKILL.md`, every `references/*.md` file mentioned
anywhere actually exists, and every SQL table mentioned in prose is
defined in a schema file — **with two real exceptions, both fixed**:
`shared/discovery_queries.yaml` was fully designed in `14-social-
14-social-discovery-outreach/references/discovery-query-design.md` back in v2 but
never actually shipped as a template file — described, not implemented.
Now created (`shared/discovery_queries.yaml.template`). Separately,
`cold-dm-email-schema.md` labeled its `social_outreach` example as
`shared/social_outreach.schema.yaml`, implying a standalone file that
was never meant to exist — the real persistence is the `social_outreach`
SQL table; the label was just misleading, now corrected. Everything
else checked out.

## v7 — 25 July 2026: the "starting out" track

The dedicated pass flagged as owed at the end of v6. Splits the named
audience into three actual situations rather than treating them as one:
long gaps (mostly already solved by existing calibration machinery —
one real gap closed, a 78-week tier for genuine multi-year gaps, plus a
prompt to weight recent evidence over pre-gap material rather than just
widening numeric gates further) and career pivots (already solved by
last round's modes c/e and the interests profile) needed only small
additions. **No/thin work history was the real gap** —
`onboarding/references/starting-out-track.md` is the actual new design:
a new `profile_stage` flag (`experienced` | `first_time` |
`returning_after_gap` | `career_pivot`), asked directly in Session 1,
never inferred and silently set. For `first_time` specifically: a
widened evidence-source list feeding `07-context-architect` Phase 1
*and* `09-risk-tactics-gate` (school, coursework, volunteer work,
interests-profile — same rigor, wider legitimate sources, stated
explicitly and repeatedly because it's easy to misread as a lowered
bar), `memory/interests-profile.md` promoted from deferred to
co-primary with the STAR bank, a format branch in `05-resume-
customizer`/`06-cover-letter`, `19-career-path-planner` mode (e) as the
default-suggested entry point rather than a nearly-empty
`title_variants` list, a different (reasoned, not arbitrary) starting
calibration preset, and — the actual redefinition — a genuinely
different SIMPLE tier for this track: a confirmed career-path plan
first, an application second, not the other way around. Flagged
plainly and left unbuilt on purpose: real child-safety/consent/data-
minimization requirements once secondary-school-age minors are
actually in scope, named directly as its own dedicated priority rather
than glossed over.

## v6 — 25 July 2026: interests profile

- **`20-interests-profile/`** (new) — a genuinely new memory dimension:
  hobbies, side projects (including unfinished/unmonetized ones),
  volunteer work, things Kene likes, childhood interests, and things
  others have noticed or complimented him on. Checked O*NET's actual
  Interest Profiler first (confirmed: a 30/60-item RIASEC survey, with
  a specific "Career Starter" version O*NET itself built for people
  with no work history yet — validates Kene's target audience as
  something the field already recognizes as distinct) — ours is a
  different shape on purpose: a conversation capturing specific,
  textured personal history, not a fixed abstract item bank, with **no
  quantification/evidence bar** (a deliberate, explicit departure from
  every other memory file in this package, since the whole point is
  capturing things that were never treated as professional). RIASEC
  gets reused, just not as the primary representation — same
  "rich content on top, standardized structure derived underneath for
  matching only" pattern `content-model-overlap.md` established.
  `20-interests-profile/references/riasec-mapping.md` pulls O*NET's Occupational Interests
  domain (additive to the same taxonomy record `content-model-
  overlap.md` already extended) and maps Kene's confirmed entries onto
  it, batched-confirmed once, not a second survey.
- **`19-career-path-planner`** gets a new Step 1.5 (interest-fit as a
  score layered across *every* mode, kept deliberately separate from
  capability scores — "would you enjoy this" and "could you do this"
  are different questions) and a new **mode (e)**: the one target-
  selection mode with no current-title anchor requirement at all,
  built specifically because modes (a)-(c) all assume a held title a
  first-time job seeker doesn't have.
- **Rule 10** (`pipeline-rules-addendum.md`) — sensitive-category
  interests (religion, health/disability, political activity) get
  recorded freely but need their own per-use confirmation before ever
  appearing in anything outward-facing — same protective instinct as
  the existing `salary_floor`/`visa_sponsorship_required` handling, not
  a values judgment about the content itself.
- **Honest scoping note, not fully solved here**: a genuinely complete
  onboarding experience for someone with zero work history is a bigger
  adaptation than this pass covers (the SIMPLE tier's own bar doesn't
  even apply cleanly to that user) — flagged directly in `20-interests-
  profile/SKILL.md` as worth its own dedicated design pass rather than
  stretched to fit here.

## v5 — 25 July 2026: real transferable-skills matching, secondary role-transition sources

- **The direct answer to "does a complete transferable-skills system
  exist": no.** `title-taxonomy.md`'s existing match is whole-profile
  text-embedding similarity — the right tool for mode (b), the wrong
  one for mode (c) by construction, because it scores overall
  profile-text closeness, not specific skill overlap, and those
  diverge exactly where a genuinely-different-role case lives. Built
  from scratch where needed, extending existing infrastructure rather
  than duplicating it: **`07-context-architect/references/
  content-model-overlap.md`**, a new engine over O*NET's actual
  Content Model (the ~120 standardized, numerically-rated Skills/
  Abilities/Knowledge elements every occupation is already scored
  against) — genuinely comparable across occupations regardless of
  title/domain, unlike free-text embedding similarity. Kene's own side
  of the comparison is *derived*, not a new interview: existing,
  already-confirmed `domain-knowledge.md`/STAR-bank entries get mapped
  onto the nearest O*NET elements, confirmed once in a batched pass.
  `19-career-path-planner` mode (c) now queries specifically for **high
  transferable-skill overlap where whole-text similarity is low** — the
  divergence between the two scores is the actual signal this mode
  needs.
- **Secondary role-transition sources, exactly as scoped — additive
  only.** `19-career-path-planner/references/role-transition-intel.md`
  scrubs career-path aggregator sites (Teal HQ's career paths,
  roadmaps.sh/developer-roadmap, jobroadmaps.com, and an open-ended
  "keep discovering more in this category" instruction, not a fixed
  three-site list) plus the general social/blog/article scrub, for six
  specific things: certifications, projects, connections/networks,
  experience, tasks, and mindset shifts people report. Stated as a hard
  guarantee, not a preference, because it was asked for in capitals: if
  these sources have nothing for a target, Step 3's primary
  gap-analysis-derived roadmap is exactly what it would have been
  without this section — enforced structurally, not just in prose, by
  giving community-reported findings their own clearly labeled
  `[COMMUNITY-REPORTED]` section in the plan record, never merged into
  the primary roadmap.

## v4 — 25 July 2026: skill authoring, onboarding, career path planning

- **`18-skill-composer/`** (new) — wraps Hermes's native `/learn` command
  (confirmed real, added June 2026: turns a described workflow, a
  directory, a URL, or a walked-through session into a working skill)
  with job-hunting-package-specific steering: decide modify-vs-create
  before drafting anything, enforce this package's house style (`/learn`
  has no reason to know it on its own), check every draft against Rule 1
  and Rule 5, and — worth being explicit about, since it's a documented
  real weakness, not hypothetical caution — default to non-destructive
  `ADDENDUM.md` extension rather than letting `/learn`'s own
  self-evaluation (which has a known bias toward rating its own output
  well even when it underperforms) overwrite a hand-tuned base
  `SKILL.md`.
- **`onboarding/`** (new) — answers directly: no, there wasn't a real
  onboarding process before this pass, just `07-context-architect`'s
  Phase 0-4 (career content) run as a single unpaced block. Now: a
  SIMPLE tier (the minimum that makes the pipeline produce even one
  staged application — one uninterrupted first session) and an ADVANCED
  tier (every other setting across the whole package, paced over
  following sessions, cadence read from how Kene actually interacts
  rather than a fixed schedule). `onboarding/references/settings-catalog.md` is the
  full enumeration, every setting tagged by the same test: does the
  pipeline run without it? Language, tone, and exact medium per question
  are deliberately left as Hermes's own judgment call, not scripted —
  that's stated as a design principle in the skill file itself, not an
  oversight. `00-orchestrator/ADDENDUM.md` is the one-line hook that
  routes a fresh install here first.
- **`19-career-path-planner/`** (new) — answers directly: no dedicated
  feature existed, but real infrastructure did (`title-taxonomy.md`,
  `gap-analysis-engine.md`, the calibration addendum's `title_delta`) —
  this assembles them rather than duplicating them. Four target-
  selection modes exactly as specified (higher seniority / adjacent at a
  chosen seniority / different at a chosen seniority / manual entry),
  a gap analysis reusing the existing engine pointed at a target
  occupation instead of the question bank, a leverage-ranked roadmap
  with multi-hop stepping-stone detection for large seniority jumps, and
  ongoing tracking wired into `16-career-pulse`'s existing career-event
  cascade rather than a standalone re-check mechanism (plus its own
  weekly re-evaluation cadence, cron job 13). Closes the loop
  deliberately, not automatically: Step 5 is a standing, explicit
  "search for this now, or keep it as a plan" question before a chosen
  target ever becomes a new `title_variants` entry (`source:
  path_planned`, a new provenance value alongside `held`/`applied`/
  `taxonomy_suggested` — see `07-context-architect/ADDENDUM.md`). New
  table in `applications_db_schema_addendum_3.sql` for progress state;
  the plan document itself is a fully-specified cache file, same
  convention as company research.

## v3 — 25 July 2026: interview intel, replies, voice journaling, calibration wiring fix, capability audit

No new database tables this round — everything below is either a new
cache-file convention (markdown, like the existing company-research
cache) or config already covered by earlier `.yaml` files.

- **`12-company-research/ADDENDUM.md`** (new) — extends the *base
  package's* company-research skill (not just the interview feature)
  with Glassdoor/Reddit/social candidate-sentiment research, as its own
  section in the same cache file every existing consumer already reads.
- **`15-interview-prep`** — kept as designed, extended per Kene's two
  additions: a new `13-interview-prep/references/interview-intel-research.md` scrub
  (YouTube/Reddit/LinkedIn/blogs/company pages, three cached scopes —
  role-general, role-in-industry, role-at-company — for actual reported
  questions and answer *shapes*, never scripts to recite), and the brief-
  assembly + mock-drill steps now draw on it directly.
- **`14-social-discovery-outreach`** — added `reply_instructions` as a
  third CTA classification alongside DM/email, with its own Part C and
  its own tier per platform (LinkedIn replies are Tier 1 via the
  self-serve `w_member_social` permission, even though LinkedIn DMs are
  Tier 3 — a genuinely different access tier, not a loophole). Added
  inactive `quote`/`post` schema stubs for a future personal-branding
  feature. New `14-social-discovery-outreach/references/discovery-query-design.md` — manual +
  Hermes-generated + example-guided queries, plus a self-improving query
  loop. **`cold-dm-email-schema.md` is now marked officially confirmed**,
  per Kene — extend it going forward, don't replace it.
- **`16-career-pulse`** — journal check-in now explicitly reuses
  `voice-interview-mode.md`'s exact setup (not a second voice
  integration) including its number-confirmation safeguard. Employment-
  status tracking now has a fourth signal source: explicit-channel
  monitoring itself, when a diff looks status-shaped.
- **Dynamic calibration — the honest fix.** Asked directly whether
  `dynamic-target-calibration.yaml`/`.md` were actually wired in: no,
  not before this pass — well-specified, not connected. Fixed with three
  new wiring addenda: `03-resume-match/ADDENDUM.md` (the real gating
  logic — match-score and overqualification gates, actually applied),
  `07-context-architect/ADDENDUM.md` (Phase 1.5 reads `employment_status`
  to decide when to widen its net), and `01-job-discovery/ADDENDUM.md`
  (explains why that skill needs no direct wiring — it inherits the
  effect through `target-profile.yaml`).
- **Pitch catalog** — manual entry addition alongside Hermes-proposed
  entries, and a fully specified pitch-performance self-improvement
  loop (what gets correlated, what cadence, what it's allowed to
  propose, what it deliberately doesn't touch) in `shared/pitch-
  catalog.md`.
- **`hermes-capability-audit.md`** (new, top-level) — read Hermes's own
  docs directly rather than working from what earlier passes happened to
  mention; maps every native capability (subagents, `execute_code`,
  cron, checkpoints, memory tiers, voice, MCP, multi-platform gateway)
  against every stage of the tool, including an honest section on where
  a capability *doesn't* clearly help.

## v2 — 25 July 2026: Threads/Facebook, cold prospecting

- `14-social-discovery-outreach/references/platform-capability-matrix.md`
  — added Threads and Facebook (Messenger/Pages) as their own rows.
  Headline finding: both inherit the same Meta-wide "no compliant path
  for cold DMs" restriction Instagram already had — not four separate
  gaps, one policy applied platform-wide. Threads' public-posting API is
  genuinely solid, though (Tier 1) — worth using for reach even where the
  DM side is closed.
- **New skill: `17-cold-prospecting/`** — outreach with no posting behind
  it at all: proposing Kene for an existing-style role, pitching a role
  that doesn't currently exist at the target, or offering a standalone
  service. Built around a confirmed **pitch catalog**
  (`shared/pitch-catalog.yaml.template` + `.md`) rather than generating
  claims fresh per pitch — the `.md` file is where the actual "how should
  content get created" opinion lives, worth reading in full given how
  open that question was. Introduces a new **target-claim gate** (Rule 8)
  for claims about a prospecting target's situation, and a **wildcard**
  catalog category (Rule 9) with its own heavier confirmation, for
  anything pitched with zero grounding in the tracked memory bank.
- `shared/applications_db_schema_addendum_2.sql` — extends
  `social_outreach` (from Addendum v1) with prospecting-specific columns
  rather than adding a parallel table.
- `cron-jobs-addendum.md` — job 12, a weekly prospecting cadence that
  delegates target research to parallel subagents but deliberately stops
  short of auto-drafting or auto-sending.

Adds to `job_hunting_skill/` (the HYBRID package) rather than modifying
it. Every existing file in that package is untouched; this addendum is
pure new surface area plus two small, explicitly additive rules. Merge
by copying this addendum's folders/files into the existing package at
the same relative paths — no filename collisions with the existing tree.
