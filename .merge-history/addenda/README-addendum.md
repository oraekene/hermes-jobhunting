# Job-Hunting Skill — Addendum (social outreach, interview prep, career pulse, dynamic calibration)

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
discovery-outreach/references/discovery-query-design.md` back in v2 but
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

## What's new, and why, in one line each

- **`14-social-discovery-outreach/`** — search social platforms for job
  leads (following whatever the post itself asks for — a link or a DM),
  plus cold-DM/cold-email drafting and, on the one platform where it's
  actually possible without unacceptable ban risk, sending itself. See
  `14-social-discovery-outreach/references/platform-capability-matrix.md` for exactly what's real vs.
  aspirational per platform, verified 25 July 2026.
- **`15-interview-prep/`** — replaces the `13-interview-prep` stub with a
  working skill, built from the exact seam the stub had already
  documented plus a mock-interview drill reusing the existing voice-
  interview pattern. Flagged honestly in its own file: this wasn't built
  from Kene's Job-Ops interview design directly (not available in this
  pass) — share specifics for a tighter follow-up if the Job-Ops version
  differs in ways worth carrying over.
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

## Install (delta from the base README)

```bash
# Copy into the existing installed skill directory
cp -r 14-social-discovery-outreach 15-interview-prep 16-career-pulse \
  ~/.hermes/skills/job-hunting/
# 15-interview-prep replaces the old stub folder — remove the stub first
rm -rf ~/.hermes/skills/job-hunting/13-interview-prep

cp shared/dynamic-target-calibration.yaml.template \
   shared/pipeline-rules-addendum.md \
   ~/.hermes/skills/job-hunting/shared/
cp shared/dynamic-target-calibration.md \
   ~/.hermes/skills/job-hunting/shared/

# Seed the new config the same way target-profile.yaml was seeded —
# through 07-context-architect's interview, not by hand-filling the
# template. Copy first so there's somewhere to write:
cp ~/.hermes/skills/job-hunting/shared/dynamic-target-calibration.yaml.template \
   ~/.hermes/skills/job-hunting/shared/dynamic-target-calibration.yaml

# Extend the DB
sqlite3 ~/.hermes/skills/job-hunting/shared/applications.db \
  < shared/applications_db_schema_addendum.sql

# Register jobs 9-11 — see cron-jobs-addendum.md for exact commands
```

### v2 additions (cold prospecting)

```bash
cp -r 17-cold-prospecting ~/.hermes/skills/job-hunting/

cp shared/pitch-catalog.yaml.template ~/.hermes/skills/job-hunting/shared/
cp shared/pitch-catalog.md ~/.hermes/skills/job-hunting/shared/
# Seed via 07-context-architect, per pitch-catalog.md's "seeding" section
# — don't hand-fill the template.
cp ~/.hermes/skills/job-hunting/shared/pitch-catalog.yaml.template \
   ~/.hermes/skills/job-hunting/shared/pitch-catalog.yaml

sqlite3 ~/.hermes/skills/job-hunting/shared/applications.db \
  < shared/applications_db_schema_addendum_2.sql

# Register job 12 — see cron-jobs-addendum.md
```

### v3 additions (no DB migration needed — cache files and doc addenda only)

```bash
cp 12-company-research/ADDENDUM.md ~/.hermes/skills/job-hunting/12-company-research/
cp -r 15-interview-prep/references/interview-intel-research.md \
  ~/.hermes/skills/job-hunting/15-interview-prep/references/
cp 15-interview-prep/SKILL.md ~/.hermes/skills/job-hunting/15-interview-prep/SKILL.md
cp 14-social-discovery-outreach/references/discovery-query-design.md \
  ~/.hermes/skills/job-hunting/14-social-discovery-outreach/references/
cp shared/discovery_queries.yaml.template ~/.hermes/skills/job-hunting/shared/
cp ~/.hermes/skills/job-hunting/shared/discovery_queries.yaml.template \
   ~/.hermes/skills/job-hunting/shared/discovery_queries.yaml
# ^ this template was described in v2 but not actually shipped until
# the v8 audit pass caught it missing — see v8's changelog entry
cp 14-social-discovery-outreach/SKILL.md \
  ~/.hermes/skills/job-hunting/14-social-discovery-outreach/SKILL.md
cp 14-social-discovery-outreach/references/platform-capability-matrix.md \
  ~/.hermes/skills/job-hunting/14-social-discovery-outreach/references/
cp 14-social-discovery-outreach/references/cold-dm-email-schema.md \
  ~/.hermes/skills/job-hunting/14-social-discovery-outreach/references/
cp 16-career-pulse/SKILL.md ~/.hermes/skills/job-hunting/16-career-pulse/SKILL.md
cp shared/dynamic-target-calibration.md ~/.hermes/skills/job-hunting/shared/
cp shared/pitch-catalog.md ~/.hermes/skills/job-hunting/shared/

mkdir -p ~/.hermes/skills/job-hunting/01-job-discovery \
  ~/.hermes/skills/job-hunting/03-resume-match \
  ~/.hermes/skills/job-hunting/07-context-architect
cp 01-job-discovery/ADDENDUM.md ~/.hermes/skills/job-hunting/01-job-discovery/
cp 03-resume-match/ADDENDUM.md ~/.hermes/skills/job-hunting/03-resume-match/
cp 07-context-architect/ADDENDUM.md ~/.hermes/skills/job-hunting/07-context-architect/

cp hermes-capability-audit.md ~/.hermes/skills/job-hunting/
```

### v4 additions

```bash
cp -r 18-skill-composer ~/.hermes/skills/job-hunting/
cp -r onboarding ~/.hermes/skills/job-hunting/
cp -r 19-career-path-planner ~/.hermes/skills/job-hunting/
cp 00-orchestrator/ADDENDUM.md ~/.hermes/skills/job-hunting/00-orchestrator/

mkdir -p ~/.hermes/skills/job-hunting/shared/career_path_plans
# schema for career_path_plans: install applications_db_schema_addendum_4.sql
# instead of _3.sql below — see v8's changelog. _3.sql is left in the
# package for historical reference only, do not run it on a fresh install.
```

### v5 additions (no DB migration — one new cache-file convention)

```bash
cp 07-context-architect/references/content-model-overlap.md \
  ~/.hermes/skills/job-hunting/07-context-architect/references/
cp 07-context-architect/ADDENDUM.md ~/.hermes/skills/job-hunting/07-context-architect/
cp 19-career-path-planner/SKILL.md ~/.hermes/skills/job-hunting/19-career-path-planner/
cp 19-career-path-planner/references/role-transition-intel.md \
  ~/.hermes/skills/job-hunting/19-career-path-planner/references/
mkdir -p ~/.hermes/skills/job-hunting/shared/role_transition_intel_cache
```

### v6 additions (no DB migration — new memory file + derived index only)

```bash
cp -r 20-interests-profile ~/.hermes/skills/job-hunting/
cp 19-career-path-planner/SKILL.md ~/.hermes/skills/job-hunting/19-career-path-planner/
cp 07-context-architect/ADDENDUM.md ~/.hermes/skills/job-hunting/07-context-architect/
cp shared/pipeline-rules-addendum.md ~/.hermes/skills/job-hunting/shared/
cp onboarding/references/settings-catalog.md ~/.hermes/skills/job-hunting/onboarding/references/

touch ~/.hermes/memories/interests-profile.md
# Seed via 20-interests-profile's elicitation, run through
# 07-context-architect same as every other memory file — don't hand-fill.
```

### v7 additions (no DB migration)

```bash
cp onboarding/references/starting-out-track.md \
  ~/.hermes/skills/job-hunting/onboarding/references/
cp onboarding/SKILL.md ~/.hermes/skills/job-hunting/onboarding/
cp onboarding/references/settings-catalog.md \
  ~/.hermes/skills/job-hunting/onboarding/references/
cp 07-context-architect/ADDENDUM.md ~/.hermes/skills/job-hunting/07-context-architect/
cp 19-career-path-planner/SKILL.md ~/.hermes/skills/job-hunting/19-career-path-planner/
cp shared/dynamic-target-calibration.yaml.template shared/dynamic-target-calibration.md \
  ~/.hermes/skills/job-hunting/shared/

mkdir -p ~/.hermes/skills/job-hunting/09-risk-tactics-gate \
  ~/.hermes/skills/job-hunting/05-resume-customizer \
  ~/.hermes/skills/job-hunting/06-cover-letter
cp 09-risk-tactics-gate/ADDENDUM.md ~/.hermes/skills/job-hunting/09-risk-tactics-gate/
cp 05-resume-customizer/ADDENDUM.md ~/.hermes/skills/job-hunting/05-resume-customizer/
cp 06-cover-letter/ADDENDUM.md ~/.hermes/skills/job-hunting/06-cover-letter/
```

### v8 additions

```bash
# Full career-path tracking — supersedes _3.sql. If _3.sql was already
# run on this install, back up any career_path_plan_progress data you
# want to keep before running this; the migration drops that table.
sqlite3 ~/.hermes/skills/job-hunting/shared/applications.db \
  < shared/applications_db_schema_addendum_4.sql
cp 19-career-path-planner/SKILL.md ~/.hermes/skills/job-hunting/19-career-path-planner/
cp cron-jobs-addendum.md ~/.hermes/skills/job-hunting/

# Audit fixes
cp shared/discovery_queries.yaml.template ~/.hermes/skills/job-hunting/shared/
cp ~/.hermes/skills/job-hunting/shared/discovery_queries.yaml.template \
   ~/.hermes/skills/job-hunting/shared/discovery_queries.yaml
cp 14-social-discovery-outreach/references/discovery-query-design.md \
   14-social-discovery-outreach/references/cold-dm-email-schema.md \
  ~/.hermes/skills/job-hunting/14-social-discovery-outreach/references/
```

### v9 additions

```bash
cp -r 21-output-templates ~/.hermes/skills/job-hunting/
cp shared/output-templates.yaml.template ~/.hermes/skills/job-hunting/shared/
cp ~/.hermes/skills/job-hunting/shared/output-templates.yaml.template \
   ~/.hermes/skills/job-hunting/shared/output-templates.yaml
# Empty by default — seeded entirely through 21-output-templates'
# conversation, never proactively elicited by onboarding.

cp shared/pipeline-rules-addendum.md ~/.hermes/skills/job-hunting/shared/

mkdir -p ~/.hermes/skills/job-hunting/08-application-qa
cp 08-application-qa/ADDENDUM.md ~/.hermes/skills/job-hunting/08-application-qa/
cp 06-cover-letter/ADDENDUM.md ~/.hermes/skills/job-hunting/06-cover-letter/
cp 05-resume-customizer/ADDENDUM.md ~/.hermes/skills/job-hunting/05-resume-customizer/
cp 14-social-discovery-outreach/SKILL.md \
  ~/.hermes/skills/job-hunting/14-social-discovery-outreach/SKILL.md
cp 17-cold-prospecting/SKILL.md ~/.hermes/skills/job-hunting/17-cold-prospecting/
cp onboarding/references/settings-catalog.md \
  ~/.hermes/skills/job-hunting/onboarding/references/
```

### v10 additions

```bash
cp -r 22-contact-enrichment ~/.hermes/skills/job-hunting/

cp shared/enrichment-tier-usage.yaml.template ~/.hermes/skills/job-hunting/shared/
cp ~/.hermes/skills/job-hunting/shared/enrichment-tier-usage.yaml.template \
   ~/.hermes/skills/job-hunting/shared/enrichment-tier-usage.yaml

sqlite3 ~/.hermes/skills/job-hunting/shared/applications.db \
  < shared/applications_db_schema_addendum_5.sql

cp 14-social-discovery-outreach/SKILL.md \
   14-social-discovery-outreach/references/cold-dm-email-schema.md \
  ~/.hermes/skills/job-hunting/14-social-discovery-outreach/references/
cp 14-social-discovery-outreach/SKILL.md \
  ~/.hermes/skills/job-hunting/14-social-discovery-outreach/SKILL.md
cp 17-cold-prospecting/SKILL.md ~/.hermes/skills/job-hunting/17-cold-prospecting/
```

### v11 additions

```bash
cp 22-contact-enrichment/SKILL.md ~/.hermes/skills/job-hunting/22-contact-enrichment/
cp 22-contact-enrichment/references/enrichment-tools-pricing.md \
   22-contact-enrichment/references/free-tier-rotation.md \
   22-contact-enrichment/references/api-key-setup.md \
   22-contact-enrichment/references/linkedin-methods.md \
  ~/.hermes/skills/job-hunting/22-contact-enrichment/references/

cp shared/enrichment-tier-usage.yaml.template ~/.hermes/skills/job-hunting/shared/
cp ~/.hermes/skills/job-hunting/shared/enrichment-tier-usage.yaml.template \
   ~/.hermes/skills/job-hunting/shared/enrichment-tier-usage.yaml
cp shared/enrichment-provider-keys.yaml.template ~/.hermes/skills/job-hunting/shared/
cp ~/.hermes/skills/job-hunting/shared/enrichment-provider-keys.yaml.template \
   ~/.hermes/skills/job-hunting/shared/enrichment-provider-keys.yaml

# Install the two Hermes-official skills this pass wires in
hermes skills install official/research/domain-intel
hermes skills install official/research/parallel-cli
hermes skills install official/security/1password

cp onboarding/references/settings-catalog.md \
  ~/.hermes/skills/job-hunting/onboarding/references/
cp cron-jobs-addendum.md ~/.hermes/skills/job-hunting/
```

### v12 additions

```bash
cp 21-output-templates/SKILL.md ~/.hermes/skills/job-hunting/21-output-templates/
cp shared/output-templates.yaml.template ~/.hermes/skills/job-hunting/shared/

cp shared/site-access-model.md ~/.hermes/skills/job-hunting/shared/
cp 14-social-discovery-outreach/references/platform-capability-matrix.md \
  ~/.hermes/skills/job-hunting/14-social-discovery-outreach/references/
cp 22-contact-enrichment/SKILL.md ~/.hermes/skills/job-hunting/22-contact-enrichment/
cp 12-company-research/ADDENDUM.md ~/.hermes/skills/job-hunting/12-company-research/
mkdir -p ~/.hermes/skills/job-hunting/10-approval-and-submit
cp 10-approval-and-submit/ADDENDUM.md ~/.hermes/skills/job-hunting/10-approval-and-submit/

# Only if not already installed from a prior v11 step
hermes skills install official/computer-use
```

## What deliberately isn't in this addendum yet

- The actual cold-DM/cold-email **content formula** (opener, value-prop
  structure, ask phrasing — the outreach equivalent of `06-cover-letter/
  06-cover-letter/references/cover-letter-formula.md`). `cold-dm-email-schema.md` is
  structure-only on purpose, per Kene's own note that the content rules
  are coming separately — it slots into `message.body_draft`'s
  generation step without any schema change once it arrives.
- Kene's actual Job-Ops interview-prep design, if it differs from what's
  built here — see `15-interview-prep/SKILL.md`'s own honesty note.
- Direct API wiring for any Tier 1 platform (X) — the skill assumes
  Kene sets up his own developer credentials; nothing here provisions
  that for him.
