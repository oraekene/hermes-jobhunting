---
name: job-hunting-career-path-planner
description: "Plan a path from current role to a target job title"
metadata:
  hermes:
    tags: [job-hunting, career-path-planner]
    category: job-hunting
    related_skills:
      - job-hunting-context-architect
      - job-hunting-interests-profile
      - job-hunting-career-pulse
---

# Career Path Planner

## When this skill applies

Use this skill when Kene wants to plan a path from where he is now to a specific target role — 'what would it take to become a [title]', 'show me a path to more senior roles', 'what jobs could I move into that I've never done', 'what career would actually suit me'. Distinct from 01-job-discovery/03-resume-match, which find and score postings against titles already in target-profile.yaml — this skill is for choosing a NEW target and mapping what closes the gap to it, before it's ever added as something to search for. Offers five ways to land on a target: higher seniority of the current title, an adjacent/variant role at a chosen seniority, a genuinely different role at a chosen seniority (via a real transferable-skills engine, not embedding similarity — see mode (c)), a title Kene types in directly, or a target suggested by his interests profile regardless of current title (mode (e), the one mode that doesn't require an existing title to anchor from). Produces a gap analysis and a roadmap, not just a title — reuses gap-analysis-engine.md's method and title-taxonomy.md's database for most of what it needs, extended with a new O*NET Content Model overlap engine and a RIASEC interest-fit engine specifically where those weren't the right tool.

Origin: Kene asking directly whether this exists already. Honest
answer: **not as its own feature.** Real building blocks exist —
`title-taxonomy.md`'s O*NET-anchored database and embedding search
(Phase 1.5), `gap-analysis-engine.md`'s confidence-scoring method, and
`shared/dynamic-target-calibration.md`'s `title_delta` seniority-delta
calculation — and this skill assembles them for modes (a), (b), and
Step 2 rather than inventing anything parallel. Mode (c) needed one
genuinely new piece — a follow-up question surfaced exactly that gap;
see that mode's own section and `07-context-architect/references/
content-model-overlap.md` for what's actually new versus what's an
extension of infrastructure `title_taxonomy_builder.py` already pulls.

## Step 1 — Choosing the target

Five modes, all ending in one confirmed target title plus its
`job_zone`:

### (a) Higher seniority, same title/family

Kene picks a seniority level above his current one (`job_zone` scale,
1-5, same axis `title-taxonomy.md` and the calibration addendum already
use — no second seniority scale invented here). Resolves to the title
string at that `job_zone` within Kene's **current occupational
family** — the taxonomy record his current title already maps to, one
or more `job_zone` bands up. Simplest mode: one family, one axis moved.

### (b) Adjacent/variant role at a chosen seniority

Kene picks a seniority level first (not necessarily higher — could be
lateral), independent of any specific title. This skill queries
`title-taxonomy.md`'s database for titles **at that `job_zone`**,
ranked by embedding similarity to Kene's current title/skills, filtered
to a **high-similarity band** — genuinely adjacent, not just anything
at that level. Presents a short list; Kene picks one. **Worth being
precise about what's new here versus what Phase 1.5 already does**:
Phase 1.5 (in `07-context-architect`) searches for titles similar to
Kene's *skills*, regardless of seniority, to expand what he already
targets. This mode fixes seniority *first*, then searches — a different
query shape against the same database, not a new database.

### (c) Genuinely different role at a chosen seniority

Kene asked directly whether a complete transferable-skills matching
system already existed for this mode. It didn't — `title-taxonomy.md`'s
existing Phase 1.5 match is whole-profile text-embedding similarity,
which is the right tool for mode (b) but the wrong one here by
construction: it scores overall profile-text closeness, not specific
skill overlap, and those two things are exactly what diverge in a
genuinely-different-role case. Built from scratch instead, reusing
existing infrastructure rather than adding parallel infrastructure:
`07-context-architect/references/content-model-overlap.md`'s
`transferable_skill_score`, computed over O*NET's standardized Content
Model elements (the same fixed ~120-element set every occupation is
already rated against) rather than free-text similarity. This mode
queries for occupations at the chosen `job_zone` ranked by
**high `transferable_skill_score` specifically where whole-text
embedding similarity is low** — that divergence is the actual signal
mode (c) needs, not an incidental side effect. Presents a short list;
Kene picks one, with each candidate's rationale citing the specific
element-level overlap and its evidence, not a bare similarity number.
Flagged distinctly from modes (a)/(b) in the output regardless — even a
principled transferable-skills case is still a bigger leap than "you've
basically already done a version of this."

### (d) Manual entry

Kene types the title directly. Skip the taxonomy search; still resolve
it against the taxonomy database if a matching record exists (for
`job_zone` and requirements data), or proceed with a lower-confidence,
`02-jd-parser`-style seniority read if it doesn't.

### (e) Suggested by interests — the one mode with no current-title anchor

Modes (a)-(c) all anchor on a current title in some way; mode (d) skips
the search but still assumes Kene already knows what he wants. This
mode exists for neither of those — added specifically for `20-interests-
profile`'s target audience, someone who may have no held title to
anchor from at all. Queries every occupation at a chosen (or
unspecified — see below) `job_zone` ranked purely by
`20-interests-profile/references/riasec-mapping.md`'s `interest_fit_score` against Kene's
derived RIASEC vector, independent of both the embedding-similarity and
transferable-skill scores modes (b)/(c) use. Genuinely a discovery
mode, not a refinement of an existing idea — the point is surfacing
targets Kene might never have thought to search for.

**Where "current title" would normally set the seniority anchor**: for
someone with a real employment history, `job_zone` still defaults from
the current title as usual. For someone with none, that default doesn't
exist — `20-interests-profile/references/riasec-mapping.md`'s honest fallback is deriving a
starting `job_zone` from education level/life stage instead (O*NET's
own `job_zone` 1-2 bands are explicitly "little or no prior experience"
territory, a reasonable anchor for this case), surfaced to Kene as an
assumption to confirm or correct, not asserted silently.

**For `target-profile.yaml`'s `profile_stage: first_time` specifically,
this mode is the default suggested starting point**, not just an
available option — see `onboarding/references/starting-out-track.md`.
Running this mode to a confirmed target first, then letting `01-job-
discovery` through `10-approval-and-submit` run against that target, is
a more honest sequence for this profile stage than pointing a
near-empty `title_variants` list at discovery and hoping something
reasonable turns up.

## Step 1.5 — Interest-fit, applied across every mode

Not its own mode — a scoring dimension layered onto whichever mode
Kene actually used. Every candidate target, from any of the five modes
above, gets `20-interests-profile/references/riasec-mapping.md`'s `interest_fit_score`
attached alongside whatever score got it onto the list in the first
place (embedding similarity for (b), `transferable_skill_score` for
(c), nothing but the interest score itself for (e)). Deliberately kept
as its own visible number, never folded into the other scores —
`riasec-mapping.md`'s own reasoning applies directly here: "would you
enjoy this," "could you actually do this," and "does your overall
profile read similar to this" are different questions worth seeing
separately, and a candidate that scores well on capability but poorly
on interest-fit is a genuinely different kind of result than one that
scores well on both.

## Step 2 — Gap analysis against the chosen target

Reuses `gap-analysis-engine.md`'s actual scoring method, pointed at a
different input than it was originally built for: instead of scoring
Kene's existing material against `question_bank.yaml` entries, it scores
his current profile (STAR bank, domain-knowledge, resume) against the
**target occupation's own requirements record** (O*NET's skills/
knowledge/tasks data, where the target resolved to a real taxonomy
entry) — same confidence-scoring logic, different right-hand side of
the comparison.

Output: which requirements are already well-evidenced, which are
partial (some evidence, not enough to satisfy the same quantification
bar `07-context-architect` Phase 2 already enforces), and which have no
evidence at all — the same three-way split Phase 1.5 already produces,
just against a single chosen target instead of the whole question bank.

## Step 3 — The roadmap, not just the gap list

A gap list alone isn't a path. For each unresolved-or-partial
requirement:

- **What would close it** — a project, a certification, a role-internal
  scope change, or (for genuinely thin gaps) simply more time in the
  current role. Concrete, not "gain more experience."
- **Leverage-ranked**, not listed in taxonomy order — a gap that also
  shows up in three other likely target titles is worth more than one
  that only matters for this specific role.
- **Gap class, before anything else** — every unresolved requirement is
  classified `self_closable` / `role_gated` / `tenure_gated` /
  `credential_gated` per `references/stepping-stone-engine.md` §1. This
  is what decides whether a roadmap item can close the gap at all, or
  whether only a different role can. A `role_gated` gap ("has managed
  people", "has owned a budget") does not belong on a roadmap, because
  no amount of Kene's own effort closes it — it belongs to Step 3.5.
- **Multi-hop check** — see Step 3.5 below. Previously a single bullet
  keyed off a `job_zone` delta; now a real engine, because the
  intermediate role is the part of a career plan people actually act on.
- **Pay trajectory**: target's disclosed/estimated compensation band
  (where the taxonomy record or `12-company-research`-style market data
  has it) against Kene's current `salary_floor` — a realistic number,
  not a motivational one.
- **Rough timeline**: qualitative, not a false-precision date — tied to
  how many roadmap items are open and their typical acquisition time,
  not a guess dressed up as a forecast.

## Step 3.5 — Stepping stones: the next role, not the eventual one

Nobody applies to the role they want in five years. They apply to the
next one. This step decides what the next one is, and it is specified in
full in `references/stepping-stone-engine.md` — summarised here to the
five things that change how the rest of this skill behaves.

**1. Four triggers, not one.** The old rule fired only on a `job_zone`
delta of more than one band. It now also fires on the presence of any
`role_gated` or `credential_gated` gap **regardless of `job_zone`** (the
most common real case, and the one the old rule missed entirely — Analyst
→ Analytics Lead is often one band, and "has never managed anyone" is not
closable by a side project), on domain distance for a mode (c) target,
and on gap density. It also **declines to propose a hop** when every gap
is `self_closable` — "this is a direct move, the list is long but you can
close all of it from here" is a real finding, not a failure to produce
one.

**2. Candidates are scored on two sides, and the scores multiply.** A
hop has to be reachable from where Kene is *and* carry him toward the
target. `reachability × bridge_value`, a product rather than a sum, so
that a candidate closing nothing cannot rank on easiness alone.
`bridge_value` — of the gaps Kene cannot close where he is, how many does
this role structurally hand him — is the term the old design had no
equivalent of and where most of the value sits.

**3. Four disqualifying checks.** Monotonicity (a hop harder to reach
than the target is not a hop), non-regression (a hop paying below
`salary_floor` is allowed but is priced explicitly and asked as its own
question, and carries a scoped exemption from addendum 13's
`seniority_floor`), market liquidity (a live read-only posting census in
Kene's actual market, since a role nobody hires for is not a plan), and
dwell time (how long the hop must be held before it evidences what it was
chosen for).

**4. The roadmap is now hop-scoped.** Step 2 runs once per hop and once
for the target; `career_path_plan_roadmap_items` rows carry a `hop_id`,
and **the active roadmap is the current hop's roadmap**. Target-level
items stay visible and tracked in their own section. This is the change
with the most day-to-day effect: it is the difference between a list Kene
can start on Monday and a list of things needed for a role two moves
away.

**5. Three paths, then one recommendation.** The direct path is always
generated and always shown, even when triggers fired. This is what makes
the `one-three-one-rule` adoption below real rather than formal — a
choice between one option and nothing is a rubber stamp.

Hop lifecycle (`achieved` vs. `matured`, plus `skipped`, `substituted`,
`abandoned`), the re-plan triggers, and the opportunistic-advancement
handling are all in the engine doc §6. The one worth knowing here:
**landing the hop role is `achieved`; having got what the role was
chosen for is `matured`**, and only the second closes the hop.

## Step 3, extended — secondary enrichment from public role-transition accounts

**This section is additive only. Read that as a hard guarantee, not a
preference.** Everything in Step 3 above — the gap-analysis-derived
roadmap — is the primary process and stays the primary process
regardless of anything below. If the sources in this section have
nothing for a given target (likely for niche, cross-domain, or
blue-collar targets that aggregator sites simply don't cover), Step 3's
output is exactly what it would have been without this section existing
at all. Nothing here ever narrows, gates, or replaces a primary-sourced
roadmap item.

What it adds, when it finds something: real people's own accounts of
how they actually got into the target role — certifications they
obtained, projects they completed, connections/networks they built,
experience they gained, tasks they took on, and mindset or approach
shifts they describe having to make. Sourced from two kinds of place:
career-path aggregator sites/repos that specifically collate this
(Teal HQ's career paths, the developer-roadmap/roadmaps.sh project,
jobroadmaps.com, and Hermes should actively watch for and add others in
this same category, not treat this as a fixed three-site list), and the
general scrub — YouTube, Reddit, LinkedIn, Facebook, Instagram, TikTok,
personal/company/career blogs, articles — reusing exactly
`13-interview-prep/references/interview-intel-research.md`'s sourcing
discipline (same "never fabricate," same source-count/confidence-note
convention) rather than inventing a second research process. Full
source list, extraction checklist, and the cache shape are in
`references/role-transition-intel.md`.

Every finding this section adds to the roadmap gets tagged
`[COMMUNITY-REPORTED]` and lives in its own labeled section (see Step
4's record shape below) — visually and structurally separate from the
primary leverage-ranked list, on purpose, so the "secondary, never
limiting" rule is enforced by the artifact's own shape, not just stated
in prose.

## Step 4 — Tracking the plan over time

A plan that's written once and never revisited is a snapshot, not a
path. **Correction from an earlier pass, worth stating plainly**: this
was originally described as "lightweight progress tracking" alongside a
cache-file record — Kene asked for full tracking instead, and the
earlier design genuinely was lightweight (one table, roadmap items
packed into a single JSON column overwritten in place on every
re-evaluation, no history of what changed or what evidence resolved
anything). `shared/applications_db_schema_addendum_4.sql` replaces it
with six normalized tables, and the relationship between the database
and the human-readable record flips accordingly: **the database is now
the source of truth for tracking state; `shared/career_path_plans/
{plan_id}.md` is a generated, human-readable rendering of that state**,
regenerated whenever something changes — not hand-maintained, and not
where progress is actually tracked.

What the six tables actually capture that the old single table
couldn't:

- **`career_path_plans`** — the plan's header/metadata (one row),
  including `active_search_status` (Step 5's decision, tracked as a
  real field rather than only reflected as a side effect on
  `target-profile.yaml`) and `superseded_by_plan_id`, so abandoning one
  plan for a related one leaves a real trail instead of an orphaned row.
- **`career_path_plan_stepping_stones`** — one row per hop for a
  multi-hop plan, each with its **own** status — a two-hop plan can now
  show "stepping stone achieved, final target still open" as a real,
  queryable state, not something inferred from prose. **Extended by
  `applications_db_schema_addendum_14.sql`** with the two-sided scores
  and their rationale, dwell estimate and its driver, comp band and
  regression consent, the scoped `seniority_floor` exemption, liquidity
  probe results, community corroboration, and the widened status enum —
  see Step 3.5. Addendum 14 also adds `career_path_plan_paths` (every
  candidate route considered, including the direct one and the rejected
  alternatives with their reasons, so "why this route" stays answerable
  a year later) and `career_path_plan_hop_gaps` (what each hop is
  actually *for*, which is what `matured` is checked against — without
  it, `achieved` can only ever mean "he took the job").
- **`career_path_plan_roadmap_items`** — one row per item, not a JSON
  blob: `category`, `source` (`primary` vs. `community_reported`,
  mirroring Step 3's tagging), and critically
  `resolved_by_evidence_ref` — which specific STAR-bank entry,
  domain-knowledge entry, interests-profile entry, or journal entry
  actually closed this item. The old design could say an item was
  "resolved"; this one can say *why*.
- **`career_path_plan_roadmap_item_history`** — every status
  transition, timestamped, with what triggered it
  (`career_pulse_cascade` / `cron_reevaluation` / `manual` /
  `journal_surfaced`). The old table only ever showed current state;
  this is the actual audit trail.
- **`career_path_plan_reevaluations`** — one row per re-evaluation run
  (cron job 14 or manual), not a single `last_reevaluated_at` timestamp
  overwritten each time. Makes "how has this plan's picture changed
  over the last six months" an answerable query, not a lost history.
- **`career_path_plan_application_links`** — once Step 5 promotes a
  plan to an active search, this links the real `applications` rows
  that come out of it back to the plan — so a plan's progress can
  eventually roll up actual interview requests and offers, not just
  roadmap-item completion.

**One honest cost of this change, not glossed over**: the migration
comment in `applications_db_schema_addendum_4.sql` drops the old
`career_path_plan_progress` table outright rather than attempting an
automatic data migration — the shapes are different enough (a JSON
blob's items have no `category` or `resolved_by_evidence_ref` to
migrate into the new columns) that a safe automatic copy isn't really
possible. Anyone who already seeded a plan under the earlier design
loses that plan's tracking history when this migration runs; they don't
lose the plan's existence, since `shared/career_path_plans/{plan_id}.md`
still holds the content and can be re-ingested into the new tables by
hand if that's worth doing for an active plan.

The rendered `.md` record's shape is otherwise unchanged from before —
still readable as a snapshot, just generated from the tables above
rather than being the tracked artifact itself:

```markdown
# Career path — [target title]

plan_id: [slug]
created_at: 2026-07-25
selection_mode: higher_seniority | adjacent | different | manual | interest_led
current_title: [Kene's current title, or "none — job_zone assumed from
  education/life stage, confirmed" for mode e with no work history]
  (job_zone: [N])
target_title: [chosen target] (job_zone: [N])
interest_fit_score: [from riasec-mapping.md, present regardless of
  which mode selected the target]
path_label: direct | recommended | alternative  # which of the three
  routes was chosen — the other two stay in career_path_plan_paths with
  their rejection reasons
stepping_stones: [] # rendered from career_path_plan_stepping_stones,
  each with its own status — empty list for a direct single-hop plan.
  Per hop: title (job_zone), status, reachability/bridge_value with
  their evidence, residual gap count, estimated dwell + its driver,
  comp band (and [COMP REGRESSION — ACCEPTED] where it applies),
  liquidity count, [COMMUNITY-CORROBORATED ×N] where present
current_hop: [which hop the active roadmap below belongs to, or
  "target" for a direct plan]

## Why this target
[one or two sentences — the taxonomy/transferable-skill match rationale
for modes a-c, "manually specified" for mode d, or the specific
interest-profile entries driving the suggestion for mode e]

## Gap analysis
- Well-evidenced: [requirements already backed by the STAR bank/
  domain-knowledge]
- Partial: [some evidence, not enough to clear the quantification bar]
- No evidence: [genuine gaps]

## Roadmap — current hop (leverage-ranked)
[The active list. For a multi-hop plan this is hop 1's roadmap, not the
target's — see Step 3.5 (4).]
1. [item] — closes: [which gap(s)] — class: [self_closable|tenure_gated]
   — status: [open|in_progress|resolved] — resolved by: [evidence_ref,
   if resolved] — [CARRIES FORWARD] if also required by the target
2. ...

## Roadmap — later hops and final target
[Tracked, visible, and deliberately not what Kene is being asked to work
on now. Same fields. Empty for a direct plan, in which case the section
above is the whole roadmap.]

## What this hop is for
[From career_path_plan_hop_gaps — the role_gated/credential_gated
requirements this hop exists to grant, each with evidenced_at or "not
yet". All evidenced + dwell elapsed is what moves the hop from
`achieved` to `matured`.]

## Paths considered
[From career_path_plan_paths — all three, including the direct path,
each with its scores and, for the two not taken, the rejection reason.
The recommendation and the conditions that would change it, per the
one-three-one framing below.]

## Community-reported paths (secondary, supplementary — see Step 3 extended)
[Only present if role-transition-intel found something for this
target. Never affects the Roadmap section above.]
- Certifications reported: [...]
- Projects reported: [...]
- Connections/networks reported: [...]
- Experience reported: [...]
- Tasks reported: [...]
- Mindset/approach shifts reported: [...]
- Sources: [aggregator sites / general scrub, with confidence note]

## Pay trajectory
[target band vs. current salary_floor, where available]

## Timeline (qualitative)
[rough estimate, tied to open roadmap-item count, not a false-precision date]

## Re-evaluation history
[rendered from career_path_plan_reevaluations — one line per run: date,
what triggered it, items resolved that run]
```

It plugs into two things already built:

- **`16-career-pulse`'s career-event cascade** already re-fires Phase
  1.5 on a confirmed profile change — this skill adds one more
  consumer to that same trigger: an active plan's gap list re-evaluates
  against the updated profile, a new row lands in
  `career_path_plan_reevaluations`, and any roadmap item the new
  evidence actually closes gets a `resolved` status change logged to
  `career_path_plan_roadmap_item_history` with `resolved_by_evidence_ref`
  pointing at whatever confirmed fact closed it — not left stale, and
  now not left unexplained either.
- **Journal entries as progress signals** — a `16-career-pulse` journal
  entry that reads like it resolves a specific roadmap item ("finally
  shipped the thing I needed for X") gets cross-checked against any
  active plan's open items, same "surface, don't silently write" Rule 5
  discipline as everything else that skill produces — and if confirmed,
  the journal entry itself becomes that item's `resolved_by_evidence_ref`.

## Step 5 — Closing the loop: does this become an active search?

A plan existing doesn't mean `01-job-discovery` should start surfacing
postings for it — that's a separate decision this skill asks for
explicitly rather than assumes. Once a plan is drafted:

**On a multi-hop plan, the title to search for is the current hop's, not
the target's.** Worth stating plainly, because the original version of
this step only knew about the final target and would have pointed
discovery at a role two moves away while the actionable one went
unsearched. Which title gets proposed follows `current_hop`: hop 1 while
hop 1 is open, the target once the last hop matures. The question below
is asked about that title, and asked again at each hop transition —
which is a real transition worth a confirmation anyway, not extra
friction.

Where the hop sits below addendum 13's `seniority_floor`, promoting it to
an active search is also what activates its `seniority_floor_exemption`,
scoped to that hop's title alone and only while the plan is active. The
floor stays fully in force for everything else, and the exemption dies
with the plan.

- **"Search for this now, alongside your current targets"** — the
  title gets proposed to `07-context-architect` as a new
  `title_variants` entry, `source: path_planned` (a new provenance
  value alongside `held`/`applied`/`taxonomy_suggested` — same
  confirm-before-write step, same audit trail, just a different origin
  worth being honest about: this one came from a chosen aspiration, not
  from something Kene already did or the taxonomy noticing a skills
  match). Reasonable even with real gaps still open — plenty of people
  land a stretch role while still closing the last item or two.
- **"Not yet — keep this as a plan I'm working toward"** — the plan
  stays in `career_path_plans/`, tracked and re-evaluated as usual, but
  nothing changes about what `01-job-discovery` searches for until
  Kene says otherwise, or until the gap analysis re-evaluates clean
  enough that this skill proactively asks again.

Either way, this is a question asked once per plan, at creation and
again at any major re-evaluation milestone — never inferred, never
silently added to the active search on the roadmap's own say-so.

## Where this plugs into existing rules

The Step 5 write is a `07-context-architect` confirm-before-write
action like any other — this skill proposes, it doesn't write
`target-profile.yaml` itself, same Rule 5 boundary every other skill in
this package respects.

## How detailed this can actually get — using what Hermes already has

- **Subagent delegation** for researching stepping-stone/target roles
  in parallel — which now has real work to do: the engine scores a
  candidate pool, and each candidate needs its own gap analysis,
  liquidity probe and market-signal read. One subagent per candidate,
  fanned out, is the difference between a usable Step 3.5 and one that
  takes long enough that Kene stops running it. Same delegation caveat
  as everywhere else in this package: subagents never write memory, and
  every candidate they return is a proposal Kene confirms. Also for
  `references/role-transition-intel.md`'s
  secondary-source scrub specifically — one subagent per source
  category (aggregator sites, social/video, blogs/articles) run
  concurrently rather than sequentially, same parallel-research pattern
  `12-company-research` and `13-interview-prep`'s intel scrub already
  use.
- **Voice**, reusing `voice-interview-mode.md` again, for walking
  through a completed plan out loud rather than reading a document cold.
- **Cron**, tied to the same cadence `16-career-pulse`'s profile-monitor
  jobs already run on, for periodic re-evaluation of an active plan
  without Kene having to remember to ask.

## Reference

- `07-context-architect/references/title-taxonomy.md`,
  `07-context-architect/references/gap-analysis-engine.md`, and `shared/dynamic-target-
  calibration.md`'s `title_delta` — the pre-existing infrastructure this
  skill composes rather than re-derives (modes a/b, Step 2).
- `07-context-architect/references/content-model-overlap.md` — the
  transferable-skills engine built for mode (c) specifically.
- `20-interests-profile/references/riasec-mapping.md` — the interest-fit
  engine behind mode (e) and Step 1.5.
- `references/role-transition-intel.md` — the secondary-source scrub for
  Step 3's extended section, and (new) the intermediate-title extraction
  behind the engine's community-corroboration pass.
- `references/stepping-stone-engine.md` — Step 3.5 in full: gap
  classification, the four triggers, two-sided scoring, the four
  validation checks, per-hop gap analysis, and the hop lifecycle.
- `shared/applications_db_schema_addendum_4.sql` — the full tracking
  schema this skill needs (supersedes the earlier `_3.sql` single-table
  design — see Step 4).
- `shared/applications_db_schema_addendum_14.sql` — the stepping-stone
  extension to that schema: candidate paths, per-hop scores and gaps,
  hop-scoped roadmap items.

## Presenting a path choice (S11)

Use `communication/one-three-one-rule` when this skill hands Kene a
choice between paths: one issue, three options, one recommendation with
its conditions stated.

The failure mode this guards against is specific to this skill. Path
analysis produces a lot of legible material — gap lists, transition
intel, timelines — and it is easy for a thorough analysis to end without
a recommendation, which quietly returns the hardest part of the work to
the person who asked for help with it. Naming a preferred path, and
saying what would change it, is the part that makes the analysis useful.

Same framing as the offer stage in `10-approval-and-submit`; deliberately
the same structure rather than a second one, so a decision looks the same
wherever in the pipeline it surfaces.

## Read the journal before advising a move

`16-career-pulse` holds the only longitudinal evidence about how the
current role is actually going, and this skill has been deciding whether
to move without it.

Before any path recommendation, ask `16-career-pulse` for its
stay-or-go summary: what has grown, what has stalled, what recurs
unresolved. Treat it as evidence for Kene's judgement, not as an input to
a verdict — this skill names a preferred path and the conditions that
would change it (see the one-three-one framing above), and "the journal
says you are unhappy" is not a condition it is entitled to assert.
