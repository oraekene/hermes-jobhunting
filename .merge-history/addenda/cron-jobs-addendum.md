<!-- STATUS: ABSORBED, AND DANGEROUS TO FOLLOW AS WRITTEN.
Its jobs 9-14 are live as cron jobs 10-15; running job 9 from this file
DUPLICATES the live job 10. cron/cron-jobs.md is the register. Do not run
any command in this file. -->

# Cron Jobs — Addendum (jobs 9-11)

Same conventions as `cron/cron-jobs.md`: 5-field cron, WAT, pin
provider/model explicitly, `[SILENT]` when there's nothing to report.
Numbered onward from the existing 8 jobs rather than renumbering
anything — see that file's own numbering for jobs 1-8.

## 9. Social listening scan

Mirrors job #1's cadence and shape, scoped to `social_listening` sources
only (`14-social-discovery-outreach`, Part A). Feeds `apply_link` posts
into the same queue job #1 already populates; stages `dm_instructions`/
`email_instructions` posts as outreach drafts instead.

```
hermes cron create "15 7,10,13,16,19,22 * * 1-6" \
  "Run job-hunting-social-discovery-outreach's discovery half: scan configured social_listening sources for hiring-style posts, classify each by CTA type (apply_link / dm_instructions / email_instructions / unclear). Feed apply_link posts into the standard discovery queue exactly as job #1 does. For dm_instructions/email_instructions, draft outreach records per 14-social-discovery-outreach/references/cold-dm-email-schema.md and stage for approval. Leave unclear posts flagged in the digest only. Use [SILENT] if nothing new was found." \
  --skill job-hunting-social-discovery-outreach \
  --skill job-hunting-orchestrator
```

## 10. Career-pulse journal check-in

Cadence is Kene's own setting (`16-career-pulse/SKILL.md` — daily is the
practical ceiling, a few times a week is a reasonable default; the
example below assumes 3x/week, adjust freely). Delivers a short prompt,
not a report — this job's output is a question, not a digest.

```
hermes cron create "0 20 * * 1,3,5" \
  "Run job-hunting-career-pulse's journal check-in: send Kene a short, low-key prompt (rotate through: what got hard this week, what got resolved, what shipped, who you worked with and how it went). Store the raw response in career_journal immediately. Flag anything that reads like a durable fact and hand it to job-hunting-context-architect as a proposed addition — never write directly to MEMORY.md/USER.md/target-profile.yaml/the STAR bank. Keep the tone practical, not performative." \
  --skill job-hunting-career-pulse
```

## 11. Explicit-channel profile monitor

Weekly for GitHub/portfolio/blog. LinkedIn checked far less often and
via a lighter-touch method — see `16-career-pulse/SKILL.md`'s note on
why scheduled LinkedIn polling at job-discovery-like frequency isn't
used here.

```
hermes cron create "0 9 * * 6" \
  "Run job-hunting-career-pulse's profile monitor for GitHub, portfolio, and blog only (not LinkedIn — see SKILL.md). Diff against the last recorded state, write any changes to profile_monitor_events, and surface a digest with a proposed context-architect addition for anything that reads like a durable fact. Use [SILENT] if nothing changed." \
  --skill job-hunting-career-pulse
```

```
hermes cron create "0 9 1 * *" \
  "Run job-hunting-career-pulse's LinkedIn check specifically, monthly: prefer a Kene-provided data export or a single Kene-triggered fetch over repeated automated scraping. Diff and surface exactly as the weekly job does for other channels." \
  --skill job-hunting-career-pulse
```

## 12. Cold prospecting cadence

Continuous target-finding, not just reactive drafting — see
`17-cold-prospecting/SKILL.md`'s "Using Hermes to its actual limits."
Delegates target research to parallel subagents (one per candidate
target, isolated context) rather than running research sequentially.
Deliberately does not auto-draft — this job stops at researched targets
staged for Kene to pick from, keeping `role_creation`/`wildcard` volume
under Kene's direct control per `shared/pitch-catalog.md`'s volume
guidance rather than a cron job deciding pitch volume on its own.

```
hermes cron create "0 8 * * 1" \
  "Run job-hunting-cold-prospecting's target-finding pass: identify up to 5 new candidate targets (companies or individuals) matching active shared/pitch-catalog.yaml entries' target_customer_profile fields. Delegate research for each candidate to a separate subagent in parallel, writing to shared/company_research_cache/ or shared/individual_research_cache/ per 17-cold-prospecting/references/target-research.md. Stage researched targets with suggested pitch_mode and catalog_entry_ids for Kene to review — do not draft or send anything automatically. Use [SILENT] if no qualifying candidates were found." \
  --skill job-hunting-cold-prospecting
```

## 13. Career path plan re-evaluation

Same cadence family as `16-career-pulse`'s weekly profile-monitor job
(job 11) — re-checks every `active`-status row in `career_path_plans`
against the current profile, logs a new row to
`career_path_plan_reevaluations` for the run itself, and updates any
`career_path_plan_roadmap_items` a new confirmed fact actually closes
(with a corresponding row in `career_path_plan_roadmap_item_history`,
`trigger: cron_reevaluation`). Never changes `title_variants` on its
own — Step 5's "search for this now" decision stays a Kene-confirmed
action regardless of how much of the roadmap closes on its own.

```
hermes cron create "0 9 * * 1" \
  "Run job-hunting-career-path-planner's re-evaluation pass: for every active row in career_path_plans, re-run the gap analysis against the current confirmed profile. For each career_path_plan_roadmap_items row that new evidence closes, update its status to resolved, set resolved_by_evidence_ref to the specific confirmed fact that closed it, and log the transition to career_path_plan_roadmap_item_history with trigger=cron_reevaluation. Log one row to career_path_plan_reevaluations per plan for this run, including items_resolved_this_run and a short gap_summary_snapshot. Never modify target-profile.yaml's title_variants from this job — that stays a Kene-confirmed action via the skill's own Step 5. Use [SILENT] if nothing changed on any active plan." \
  --skill job-hunting-career-path-planner
```

## 14. Enrichment tier-usage cycle reset

Daily check, not monthly — provider billing cycles reset on their own
account-creation date, not the 1st, so a fixed monthly cron would drift.
Checks each `shared/enrichment-tier-usage.yaml` provider's
`cycle_resets_at` against the current date; zeroes `used_this_cycle`
(and `tier3_spent_this_cycle_usd`) for anything past its reset date, and
sets the next `cycle_resets_at`. Read-only otherwise — never touches
`monthly_allowance`, `tier3_monthly_budget_usd`, or
`enrichment-provider-keys.yaml`.

```
hermes cron create "0 6 * * *" \
  "Run job-hunting-contact-enrichment's cycle-reset check: for every entry in shared/enrichment-tier-usage.yaml, compare cycle_resets_at against today. For any entry past its reset date, zero used_this_cycle (and tier3_spent_this_cycle_usd for the Tier 3 budget entry) and advance cycle_resets_at by one month from that date. Never modify monthly_allowance, tier3_monthly_budget_usd, or shared/enrichment-provider-keys.yaml. Use [SILENT] if nothing needed resetting today." \
  --skill job-hunting-contact-enrichment
```
