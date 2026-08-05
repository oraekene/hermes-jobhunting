# Settings Catalog — every configurable parameter in the full package

The master list `onboarding/SKILL.md` works from. Organized by the file
that actually owns each setting, not by onboarding session — where a
given setting gets asked is a pacing decision (see the main skill file),
not a property of the setting itself.

**Tags**: **SIMPLE** = part of the minimum subset the pipeline needs to
run at all (produce at least one staged, approvable application).
**ADVANCED** = everything else — has a working default, or genuinely
optional, or only matters once a specific addendum feature gets used.

## Bootstrap prerequisite (Hermes-level, not a skill setting)

- **Approval channel paired** (Telegram, by default in this package) —
  **SIMPLE**. Nothing in this pipeline can reach `10-approval-and-
  submit`'s human-click boundary without this. Not a skill setting to
  ask about conversationally — a literal pairing step that has to
  happen before onboarding's conversational part is even useful.

## `shared/target-profile.yaml` (owned by `07-context-architect`, Phase 0/0.5)

- `profile_stage` — **SIMPLE**, and asked *before* anything else in
  this list — routes to one of two Session 1 shapes entirely (see
  `starting-out-track.md`). `experienced` is the default
  suggestion when Phase 1 ingestion finds real work history; nothing
  below this line assumes which value was confirmed.
- `seniority_band` — **SIMPLE**. Nothing downstream can filter postings
  without it.
- `locations.*` (remote_ok/hybrid_ok/onsite_ok/countries/cities) —
  **SIMPLE**. Same reason.
- `salary_floor.*` — **SIMPLE** in the sense that it should be asked,
  but an explicit "no floor set yet" is a valid, working answer — not
  blocking, just worth surfacing early rather than defaulting silently.
- `visa_sponsorship_required` — **ADVANCED** (defaults to
  "not yet confirmed," `null`, which is itself a valid working state —
  `01-job-discovery` just doesn't filter on it until set).
- `industries_exclude` / `companies_exclude` — **ADVANCED**, empty list
  is a fine default.
- `fidelity_mode` — **SIMPLE to have a value** (every application needs
  one), but genuinely **defaults to `strict` without being asked** if
  Kene doesn't have a strong preference — Phase 0.5 already documents
  this exact default behavior.
- `discovery_mode` — **SIMPLE to have a value**, defaults to
  `poll_only`.
- `title_variants` — **SIMPLE**, at least one `source: held` or
  `source: applied` entry needed before `01-job-discovery` has anything
  to search for. The Phase 1.5 `taxonomy_suggested` expansion is
  **ADVANCED** — genuinely useful, not blocking.

## `~/.hermes/memories/USER.md` / `MEMORY.md` (owned by `07-context-architect`)

- Core identity/role/location/non-negotiables prose — **SIMPLE**,
  written together with target-profile.yaml's Phase 0.
- Standing instructions ("never apply to X," strategy notes) —
  **ADVANCED**, accumulates over time, nothing to front-load.

## `memory/star-story-bank.md`, `domain-knowledge.md`, `career-timeline.md`
## (owned by `07-context-architect`, Phase 1-4)

- Base resume/portfolio ingestion — **SIMPLE**, Phase 1 can't run
  without source material.
- Enough STAR entries to satisfy the Quantification gate for at least
  the *currently targeted* title variants — **SIMPLE**, in the sense
  that `05-resume-customizer`/`06-cover-letter` need this to produce a
  real first application. Full bank coverage across every possible
  question-bank category — **ADVANCED**, an ongoing, never-quite-"done"
  process this pipeline (and now `16-career-pulse`'s journal) keeps
  building.

## `memory/interests-profile.md` (owned by `07-context-architect`, elicited by `20-interests-profile`)

- The six-category elicitation pass — **ADVANCED** for `profile_stage:
  experienced` (the pipeline runs a first application without it), but
  **SIMPLE, co-primary with the STAR bank** for `profile_stage:
  first_time` — formalized in `starting-out-track.md` rather
  than left as the caveat it was before that document existed. Same
  underlying test as everywhere else in this catalog, it just resolves
  differently depending on which track this person is actually on.

## `shared/sources.yaml`

- At least one declared source, or `discovery_mode: open_web` with at
  least one `open_web_search` entry — **SIMPLE**, `01-job-discovery`
  produces nothing otherwise.
- Additional declared sources, `exclude_domains` — **ADVANCED**.
- `social_listening` sources (`14-social-discovery-outreach`) —
  **ADVANCED**, an explicitly opt-in expansion.

## `shared/tier-config.yaml`

- `active_tier` — **ADVANCED**, `starter` is a sensible default nobody
  needs to consciously choose on day one.

## `shared/dynamic-target-calibration.yaml`

- Every field here — **ADVANCED**. The shipped template's defaults
  (`calibration_mode: hybrid`, `match_score.minimum: 70`,
  `stretch.floor: 50`, `overqualification_tolerance: balanced`,
  `employment_status: unspecified`) are all workable out of the box;
  nothing here blocks first use. **Exception**: `match_score.minimum`/
  `stretch.floor`'s *starting* values are pre-set differently when
  `profile_stage: first_time` (55/35 instead of 70/50) — set once
  automatically from that flag, per `starting-out-track.md`,
  not a second question asked here.

## `shared/pitch-catalog.yaml` (only relevant once `17-cold-prospecting` is used)

- Every entry — **ADVANCED**, and specifically *deferred* rather than
  just optional: `shared/pitch-catalog.md`'s own seeding guidance
  already recommends this happens as its own separate session, not
  bundled into general onboarding.

## `shared/discovery_queries.yaml` (only relevant once `14-social-discovery-outreach` is used)

- Manual queries, example-guided seeding — **ADVANCED**. Hermes-
  generated queries have a working default (drafted from whatever
  `target-profile.yaml` already has) so this isn't blocking even for
  first use of that skill.

## `16-career-pulse` settings

- Journal cadence — **ADVANCED**, defaults to a reasonable few-times-
  a-week rhythm if never explicitly set.
- Explicit-channel monitoring list (which profiles to watch) —
  **ADVANCED**, empty list is valid — nothing to monitor until Kene
  names something.
- Voice STT/TTS provider (`stt.provider`/`local.model`/`tts.provider`)
  — **ADVANCED**, `local`/`small`/`edge` (free, no API key) is a
  working default per `voice-interview-mode.md`'s own setup checklist.

## Cron cadences (`cron/cron-jobs.md` + `cron-jobs-addendum.md`)

- Every job's schedule — **ADVANCED**. Shipped defaults are reasonable
  starting points; none need to be hand-tuned before first use.

## `18-skill-composer` — nothing to configure

No settings of its own; it's a tool-authoring capability, not a
pipeline preference.

## `shared/output-templates.yaml` (owned by `21-output-templates`)

- Every named template — **ADVANCED**, and never even a default-empty
  question at onboarding: this is authored entirely on Kene's own
  initiative, whenever he wants a specific structure for a specific
  kind of output, not something onboarding proactively elicits like it
  does `title_variants` or `fidelity_mode`. Empty is the correct
  starting state, not a gap to fill.

## `shared/enrichment-provider-keys.yaml` / `enrichment-tier-usage.yaml` (owned by `22-contact-enrichment`)

- Connecting a paid provider API key — **ADVANCED**, entirely opt-in,
  never elicited proactively (same posture as `output-templates.yaml`
  above). The free-tier cascade works with zero connected keys; paid
  providers only ever become reachable once Kene explicitly connects
  one via `22-contact-enrichment/references/api-key-setup.md`'s flow.
- `tier3_monthly_budget_usd` — **ADVANCED**, defaults to `$0` (Tier 3
  spend is opt-in by design, not a setting onboarding surfaces).

## Everything else

Anything genuinely new — a setting introduced by a future addendum, or
by `18-skill-composer` authoring a new skill — gets added to this file
as part of that addition, tagged SIMPLE/ADVANCED by the same test used
above: does the pipeline produce a staged, approvable application
without it? If yes, ADVANCED. If the answer is genuinely no, SIMPLE —
and that should be a rare, deliberately scrutinized tag to add, not a
default.
