# Settings Registry — every configurable parameter, cross-checked against its readers

`settings.yaml` is the machine-readable source of truth. It shares the panel schema with `gates.yaml` (`panel.when_on` / `panel.when_off`), so the info panel is one system rendering two registries, not two systems.

## Scope

| | |
|---|---|
| Config files | 11 |
| Keys found | 111 |
| User-facing settings | 22 |
| Auto-managed (never asked) | 28 |

The gap between 111 keys and 22 settings is the point. Most keys in these files are bookkeeping the tool writes itself — cycle reset dates, usage counters, last-confirmed timestamps — or structural shape inside a list item. Presenting those as settings would bury the ones that matter.

## Tiers

- **SIMPLE** — the pipeline cannot produce a staged application without it
- **ADVANCED** — has a working default, or only matters once one feature is used
- **AUTO** — written by the tool, never asked

## The settings

| Setting | Tier | File | Default | Bound gate |
|---|---|---|---|---|
| `profile_stage` ⚠️ | SIMPLE | `shared/target-profile.yaml` | `experienced` | `GATE-TARGET-PROFILE-WRITE` |
| `seniority_band` | SIMPLE | `shared/target-profile.yaml` | *(empty)* | `GATE-TARGET-PROFILE-WRITE` |
| `locations` | SIMPLE | `shared/target-profile.yaml` | — | `GATE-TARGET-PROFILE-WRITE` |
| `salary_floor` | SIMPLE | `shared/target-profile.yaml` | — | `GATE-TARGET-PROFILE-WRITE` |
| `visa_sponsorship_required` | ADVANCED | `shared/target-profile.yaml` | — | `GATE-TARGET-PROFILE-WRITE` |
| `fidelity_mode` | SIMPLE | `shared/target-profile.yaml` | `strict` | `GATE-FIDELITY-MODE` |
| `discovery_mode` | SIMPLE | `shared/target-profile.yaml` | `poll_only` | `GATE-TARGET-PROFILE-WRITE` |
| `title_variants` | SIMPLE | `shared/target-profile.yaml` | `[]` | `GATE-TARGET-PROFILE-WRITE` |
| `industries_exclude` ⚠️ | ADVANCED | `shared/target-profile.yaml` | `[]` | `GATE-TARGET-PROFILE-WRITE` |
| `companies_exclude` ⚠️ | ADVANCED | `shared/target-profile.yaml` | `[]` | `GATE-TARGET-PROFILE-WRITE` |
| `active_tier` | ADVANCED | `shared/tier-config.yaml` | `starter` | `GATE-TIER-CONFIG-CHANGE` |
| `calibration_mode` | ADVANCED | `shared/dynamic-target-calibration.yaml` | `hybrid` | `GATE-CALIBRATION-CHANGE` |
| `match_score.minimum` | ADVANCED | `shared/dynamic-target-calibration.yaml` | `70` | `GATE-CALIBRATION-CHANGE` |
| `match_score.stretch.floor` | ADVANCED | `shared/target-profile.yaml` | `50` | `GATE-CALIBRATION-CHANGE` |
| `overqualification_tolerance` | ADVANCED | `shared/dynamic-target-calibration.yaml` | `balanced` | `GATE-CALIBRATION-CHANGE` |
| `employment_status` | ADVANCED | `shared/dynamic-target-calibration.yaml` | `unspecified` | `GATE-CALIBRATION-CHANGE` |
| `stepping_stone.max_hops` ⚠️ | ADVANCED | `shared/target-profile.yaml` | `2` | `GATE-TARGET-PROFILE-WRITE` |
| `stepping_stone.allow_comp_regression` ⚠️ | ADVANCED | `shared/target-profile.yaml` | `ask` | `GATE-TARGET-PROFILE-WRITE` |
| `stepping_stone.liquidity_probe` ⚠️ | ADVANCED | `shared/target-profile.yaml` | `True` | `GATE-TARGET-PROFILE-WRITE` |
| `tier3_monthly_budget_usd` | ADVANCED | `shared/enrichment-tier-usage.yaml` | `0` | `GATE-PAID-SPEND` |
| `plan` | ADVANCED | `shared/target-profile.yaml` | — | `GATE-SEND-INMAIL` |
| `exclude_domains` | ADVANCED | `shared/sources.yaml` | `[]` | `GATE-TARGET-PROFILE-WRITE` |

## Four wiring problems the cross-check found

Each of these is the kind of thing that cannot be found by reading `settings-catalog.md`, because the catalog is exactly the document that is wrong.

### 1. `profile_stage` has no field in any config file

It is read by eight skills — `03`, `05`, `06`, `07`, `09`, `19`, `20`, plus `dry-run.py` — it is the **first question onboarding asks**, it routes the entire first session down one of two tracks, and it pre-sets the match thresholds to 55/35 instead of 70/50. `shared/target-profile.yaml` does not contain it. Every one of those readers is reading a key that the shipped template never creates.

**Fix:** add `profile_stage: ""` to the template, SIMPLE tier, asked first.

### 2. `social_listening` is not in the `sources.yaml` type enum

`14-social-discovery-outreach` opens by describing it as *a new source type* extending `01-job-discovery`'s sources. The shipped template's type list is `linkedin_search_url | indeed_search_url | rss | email_label | google_dork | scrape_and_filter | export_file | aggregator_api | open_web_search` — no `social_listening`. A user configuring a source has no way to know the value is valid, and any validator written against that enum rejects it.

### 3. `daily_staging_cap` appears in no file but its own

Rule 3 is built on the daily cap, `00-orchestrator` enforces it, and `README.md` describes it. The actual key `daily_staging_cap` is named nowhere except `tier-config.yaml` itself. Either the orchestrator reads it under a different name or the enforcement reads a different value. Worth confirming before any gate is switched off, because this cap is the last thing standing between a bug in auto-approve mode and a day's worth of unreviewed output.

### 4. The whole `stepping_stone` block is undocumented

Six keys — `max_hops`, `gap_density_threshold`, `min_liquidity_postings`, `liquidity_probe`, `community_intel`, `allow_comp_regression` — are wired, read, and carry real defaults with real reasoning behind them. None appears in `settings-catalog.md`, so onboarding never mentions them and a user never learns the career planner is tunable at all.

Same shape, smaller: `industries_exclude` and `companies_exclude` are documented as ADVANCED and present in the template, but no live skill or reference names either one. Verify the discovery filter actually applies them.

## Auto-managed keys

Written by the tool, never asked, never shown as settings. Listed so nobody adds them to onboarding by accident:

```
available_this_cycle
credits_refunded_this_cycle
cycle_resets_at
entries.id.confirmed_at
entries.id.target_customer_profile.built_at
entries.id.target_customer_profile.confirmed_at
last_confirmed_at
last_recalibrated_at
last_reviewed_at
last_updated_at
open_profile_used_this_cycle
pool.artifacts.id.last_checked_at
pool.work_items.id.added_at
pool.work_items.id.last_reviewed_at
providers.name.cycle_resets_at
providers.name.used_this_cycle
recalibration_log
sources.id.posted_at
status_changed_at
tier3_cycle_resets_at
used_this_cycle
variants.slug.last_gate_pass_at
variants.slug.published_at
```

## Info-panel copy

**Whether you have prior work history** &nbsp;`profile_stage` &nbsp;⚠️ MISSING FROM CONFIG FILE

> Read by 8 skills and asked first at onboarding, but no field exists in the shipped template. Add it.

- *On / default* — Asked before anything else. It routes the whole first session and pre-sets your match thresholds — 55/35 instead of 70/50 if you are starting out, because entry-level postings systematically overstate their own requirements.
- *Off / other end* — Assumed experienced. Someone with no work history gets a search tuned for someone who has one, and sees almost nothing.

**Your seniority level** &nbsp;`seniority_band`

- *On / default* — Postings are filtered to your band before anything else runs, so the pipeline spends its daily budget on roles you could take.
- *Off / other end* — Nothing downstream can filter. Graduate roles and director roles arrive in the same queue.

**Where you will work** &nbsp;`locations`

- *On / default* — Remote, hybrid, onsite, countries and cities are all separate answers, so 'remote anywhere' and 'hybrid in Lagos only' filter differently.
- *Off / other end* — Every posting passes the location filter, including ones you could never take.

**Your minimum acceptable pay** &nbsp;`salary_floor`

- *On / default* — Postings below your floor are dropped before they cost you a review. 'No floor set yet' is a valid, working answer.
- *Off / other end* — You review applications for roles that could never pay enough, and find out at offer stage.

**Whether you need visa sponsorship** &nbsp;`visa_sponsorship_required`

- *On / default* — Roles that explicitly cannot sponsor are filtered out.
- *Off / other end* — Unset by default, and nothing filters on it. You apply to roles that will reject you at the first screening question.

**How strictly claims must be evidenced** &nbsp;`fidelity_mode`

- *On / default* — strict — every claim cites a line in your resume, portfolio or story bank. No evidence means the tactic is dropped and the gap flagged to you.
- *Off / other end* — embellish — unsupported claims still go out, logged for the audit trail but not held up for review. You may have to defend them in an interview with nothing on file.

**How widely to search** &nbsp;`discovery_mode`

- *On / default* — poll_only — only the sources you configured. Predictable, cheap, and misses anything not on those boards.
- *Off / other end* — open_web — adds a broader web sweep on a slower cadence. More coverage, more noise, more cost per day.

**Job titles to search for** &nbsp;`title_variants`

- *On / default* — You confirm each variant. Titles you actually held are suggested automatically; adjacent titles the taxonomy proposes are shown with the evidence behind them.
- *Off / other end* — Nothing to search for. Discovery returns nothing at all until at least one title exists.

**Industries to never show you** &nbsp;`industries_exclude` &nbsp;⚠️ NO READER FOUND

> Present in the config file and documented, but no live skill or reference names it. Verify the filter actually applies it.

- *On / default* — Named industries never reach your queue.
- *Off / other end* — Empty is the normal state. Everything is considered.

**Companies to never apply to** &nbsp;`companies_exclude` &nbsp;⚠️ NO READER FOUND

> Present in the config file and documented, but no live skill or reference names it. Verify the filter actually applies it.

- *On / default* — Your current employer, or anywhere you have decided against, never appears.
- *Off / other end* — Empty is the normal state.

**How many applications to prepare per day** &nbsp;`active_tier`

- *On / default* — starter — 15 a day. Enough for one person's active search, and a number you can actually review.
- *Off / other end* — max — 200 a day. Your own review throughput becomes the bottleneck, not the pipeline. Nothing sends itself at any tier.

**Whether match thresholds may adjust themselves** &nbsp;`calibration_mode`

- *On / default* — hybrid — the maths runs on schedule, each proposed change is staged, and it only takes effect once you approve it.
- *Off / other end* — auto — thresholds move on their own, logged but not approved. Your bar drifts and you find out from the results.

**Minimum match score to stage an application** &nbsp;`match_score.minimum`

- *On / default* — 70 by default, 55 if you are starting out. Below it, nothing is staged.
- *Off / other end* — Lower it and you review more, weaker matches. Raise it and a thin market produces an empty queue.

**Stretch band floor** &nbsp;`match_score.stretch.floor`

- *On / default* — 50-70 is the stretch band: staged, and tagged STRETCH in the approval message so you know it is a reach before you approve.
- *Off / other end* — Disable stretch and you only ever see comfortable matches. Most step-up roles live in this band.

**How far below your level to consider** &nbsp;`overqualification_tolerance`

- *On / default* — balanced — title-seniority and compensation deltas are weighed as two separate axes.
- *Off / other end* — relaxed — roles well below your level reach the queue. Sometimes right in a bad market, expensive in attention otherwise.

**Whether you are currently employed** &nbsp;`employment_status`

- *On / default* — Urgency and volume adapt. Being between roles changes what a sensible daily target is.
- *Off / other end* — unspecified — the pipeline runs at a neutral pace regardless of how urgent your search actually is.

**How many career moves a plan may span** &nbsp;`stepping_stone.max_hops` &nbsp;⚠️ UNDOCUMENTED IN CATALOG

> Wired and read, but absent from settings-catalog.md, so onboarding never surfaces it.

- *On / default* — Two hops. A third rests on a profile nobody can predict, and the re-plan rule would regenerate it anyway.
- *Off / other end* — Longer plans read as forecasts. They look impressive and the later hops are fiction.

**Whether a plan may include a pay cut** &nbsp;`stepping_stone.allow_comp_regression` &nbsp;⚠️ UNDOCUMENTED IN CATALOG

> Wired and read, but absent from settings-catalog.md, so onboarding never surfaces it.

- *On / default* — ask — a step that pays less is shown to you with the reasoning rather than hidden.
- *Off / other end* — never — silently removes most sector switches and management-track entries. A default that hides options is worse than one that asks.

**Check live demand for a planned role** &nbsp;`stepping_stone.liquidity_probe` &nbsp;⚠️ UNDOCUMENTED IN CATALOG

> Wired and read, but absent from settings-catalog.md, so onboarding never surfaces it.

- *On / default* — A read-only census of live postings across your sources over 90 days. Queues nothing.
- *Off / other end* — Falls back to taxonomy signals only. A plan can point at a title with no live market.

**Monthly budget for paid contact lookups** &nbsp;`tier3_monthly_budget_usd`

- *On / default* — Zero. The free cascade covers 325+ lookups a month before anything could cost money.
- *Off / other end* — Set a figure and paid lookups run automatically up to it, without asking each time.

**Your LinkedIn subscription tier** &nbsp;`plan`

- *On / default* — Sets your monthly InMail allowance so the tool knows what it is spending.
- *Off / other end* — Unset, and InMail routing is simply unavailable — every stranger routes through connect-and-wait instead. Not an error state, the honest default.

**Domains to skip in open-web search** &nbsp;`exclude_domains`

- *On / default* — Aggregator sites that republish the same postings stop cluttering the queue.
- *Off / other end* — Empty. Open-web mode surfaces duplicates from scraper sites.

## What this unlocks

- **Onboarding** — SIMPLE tier is now a checkable list rather than prose, and `profile_stage` gets a field before it is asked about.
- **Info panel** — one renderer over `gates.yaml` + `settings.yaml`.
- **Docs** — `panel.when_on` / `panel.when_off` are the worked examples, written once.
- **Flow catalog** — the variation axes are exactly the multi-value settings here: `fidelity_mode`, `discovery_mode`, `calibration_mode`, `overqualification_tolerance`, `active_tier`, `profile_stage`, `allow_comp_regression`.
