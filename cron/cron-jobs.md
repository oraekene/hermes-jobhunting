# Cron Jobs — Job-Hunting Pipeline

Hermes's cron system runs these via its gateway daemon (`hermes gateway`
must be running — see `hermes gateway install` for a persistent service).
Every job here delivers to Telegram. Schedules use standard 5-field cron
expressions so they can be pinned to business hours in Kene's timezone
(WAT, Port Harcourt).

Per Hermes's own recommendation, pin the provider/model explicitly on
each job (`provider=... model=...`) rather than leaving it on the global
default — an unpinned job silently skips its run and alerts you if the
global default model ever changes underneath it
(`user-guide/features/cron.md`).

## Install path has changed: blueprints first, manual setup for the rest

Four jobs now ship as **blueprints** declared directly in their skill's
own frontmatter (`metadata.hermes.blueprint`, see `developer-guide/
creating-skills.md` "Blueprints"): discovery scan, the pipeline sweep,
the weekly self-improvement review, and interview-prep. Installing the
package offers all four as one-tap suggestions instead of requiring
hand-typed `hermes cron create` commands:

```bash
hermes skills install <tap>/job-hunting
# → Blueprint: 'job-hunting-discovery' is an automation (schedule 0 7,10,13,16,19,22 * * 1-6).
# → Blueprint: 'job-hunting-orchestrator' is an automation (schedule 30 7,10,13,16,19,22 * * 1-6).
# → Blueprint: 'job-hunting-analytics' is an automation (schedule 0 8 * * 1).
# → Blueprint: 'job-hunting-interview-prep' is an automation (schedule 0 9,15 * * 1-6).
#   Added to your suggestions — run /suggestions to schedule or dismiss each one.

/suggestions             # lists the four pending suggestions
/suggestions accept 1    # schedules discovery-scan
/suggestions accept 2    # schedules the pipeline sweep
/suggestions accept 3    # schedules the weekly self-improvement review
/suggestions accept 4    # schedules the interview-prep sweep
```

The remaining five jobs (#2, #4, #6, #7, #8 below) aren't blueprinted —
either because they share a skill that's already carrying a different
blueprint schedule (a skill can only declare one `blueprint:` block), or
because they're genuinely optional/conditional. Set those up with the
`hermes cron create` commands documented below, same as before.

**One follow-up step after accepting the discovery-scan and
interview-prep suggestions**: the blueprint frontmatter schema doesn't
expose a `script=` field (it only covers `schedule` / `deliver` /
`prompt` / `no_agent`), so each job's cost-control wake-gate script (see
jobs #1 and #9 below) has to be attached in a separate edit after the
job exists:

```bash
cp 01-job-discovery/scripts/discovery-wake-gate.py ~/.hermes/scripts/
hermes cron edit <discovery-scan-job-id> --script discovery-wake-gate.py

cp 13-interview-prep/scripts/interview-prep-wake-gate.py ~/.hermes/scripts/
hermes cron edit <interview-prep-job-id> --script interview-prep-wake-gate.py
```

(`hermes cron list` shows each job id if `/suggestions accept` didn't
print it back to you.)

## 1. Job discovery scan

Runs every 3 hours during business hours, Monday–Saturday — frequent
enough that a posting under 24h old is very unlikely to be missed, per
`01-job-discovery`'s speed-priority logic. **Ships as a blueprint** (see
above) — the command below is what `/suggestions accept` runs on your
behalf, shown here so the actual prompt text is visible and so you can
create it by hand if you'd rather skip the blueprint flow.

```bash
hermes cron create "0 7,10,13,16,19,22 * * 1-6" \
  "Scan configured sources for new postings, dedupe against the applications DB, cheap-filter against Kene's target profile, and queue anything that survives — respecting today's remaining daily cap. Deliver a short digest. Use [SILENT] if nothing new was found." \
  --skill job-hunting-discovery \
  --script discovery-wake-gate.py
```

**Cost control**: `--script discovery-wake-gate.py` attaches the
pre-run wake-gate covered in `01-job-discovery/SKILL.md`'s "Cost
control: the wake-gate script" section — it cheap-checks `rss` and
`email_label` sources and skips the entire LLM turn (zero token cost)
on ticks where nothing changed. Copy the script to `~/.hermes/scripts/`
first (Hermes requires cron scripts to live there); see that skill's
section for exactly what this does and doesn't cover. **One honesty
note**: I confirmed `--script` as a CLI flag paired with `--no-agent`
(pure script-only jobs) in Hermes's own docs, and confirmed the
underlying `script=` parameter for exactly this "pre-run gate on an
LLM job" pattern via the `cronjob(...)` tool-call form — I did not find
a documented CLI example combining `--script` with `--skill` (no
`--no-agent`) the way this command does. If `hermes cron create` on
your install rejects that combination, fall back to asking Hermes
directly: `cronjob(action="create", skill="job-hunting-discovery",
script="discovery-wake-gate.py", prompt="...", schedule="0
7,10,13,16,19,22 * * 1-6")` — same effect, confirmed syntax.

**Toolset scope**: this job only needs email/web/terminal access, never
browser or delegation — if you're setting `enabled_toolsets` per-job
(ask Hermes in chat, or `cronjob(action="update", job_id=..., enabled_toolsets=[...])`
— I couldn't confirm a dedicated `hermes cron edit --enabled-toolsets`
CLI flag in the docs, so use whichever of chat or the tool call actually
works on your install), scope this one to `["web", "terminal"]`. Running
this 6x/day, every unnecessary toolset in the schema is paid for on every
single tick.

## 2. Open-web discovery sweep (daily — only runs if discovery_mode allows it)

Separate job, separate cadence, deliberately not folded into job #1 — see
`01-job-discovery/SKILL.md`'s "Discovery modes" section for the full
cost/consistency reasoning behind running this slower than the core
scan. This job is a no-op (and should exit immediately, `[SILENT]`,
without spending a search/browse call) if `target-profile.yaml`'s
`discovery_mode` is `poll_only` — the schedule existing doesn't mean it
does anything at `poll_only`. Not blueprinted: `job-hunting-discovery`
already carries job #1's blueprint, and a skill can only declare one.

```
hermes cron create "0 9 * * 1-6" \
  "Check shared/target-profile.yaml's discovery_mode first. If it's poll_only, exit immediately with [SILENT] and do nothing else. Otherwise, run job-hunting-discovery's open_web_search sources only (not the declared-source list, already covered by job #1): build platform-dork queries plus a generic query from target-profile.yaml, search, visit and extract postings, resolve posted_at via the fallback chain in sources.yaml, apply exclude_domains if discovery_mode is open_web_excluding, then dedupe/filter/queue exactly as job #1 does. Deliver a short digest of what this sweep specifically found." \
  --skill job-hunting-discovery
```

If installed, `research/scrapling` (Hermes optional skill) is worth
attaching here too — several ATS-hosted career pages run behind
Cloudflare or basic anti-bot checks, and this is the job most exposed to
that (`01-job-discovery/SKILL.md`'s open-web mode section covers the
reasoning).

## 3. Pipeline sweep (process the discovery queue)

Runs shortly after each discovery scan, walks anything sitting at
`discovered` status through stages 2–9, and leaves fully-gated packages
sitting at `staged` for `10-approval-and-submit` to ping Kene about
individually, which is what actually moves a posting to
`awaiting_approval` (submission itself is never on a schedule — see
`shared/pipeline-rules.md` Rule 1). **Ships as a blueprint** on
`job-hunting-orchestrator` (see "Install path" above) — the command
below is what `/suggestions accept` runs on your behalf.

```
hermes cron create "30 7,10,13,16,19,22 * * 1-6" \
  "Run the job-hunting-orchestrator on every application currently at 'discovered' status: process through JD parsing, resume match, keyword analysis, resume customization, cover letter, application Q&A, and the risk-tactics gate. Stop each one at 'staged' and hand off to job-hunting-approval-submit for the Telegram review ping. Process applications one at a time and treat each as its own unit of work: if any stage fails for an application, leave that application's status unchanged, record the failing stage and the error in its row, and CONTINUE to the next application rather than aborting the sweep. Never leave a row in a half-processed state — an application is either fully advanced to staged or untouched at its previous status. At the end, report how many advanced, how many were skipped, and which stage each skip failed at. Never call the submit action from this job." \
  --skill job-hunting-orchestrator
```

**Optional, opt-in parallel variant** — genuinely faster with several
postings queued, genuinely more moving parts; read
`00-orchestrator/references/parallel-pipeline-sweep.md` in full,
including its honesty section on one piece of timing behavior I
couldn't fully verify without a live gateway, before switching to this:

```
hermes cron create "30 7,10,13,16,19,22 * * 1-6" \
  "Run the job-hunting-orchestrator's parallel pipeline sweep per 00-orchestrator/references/parallel-pipeline-sweep.md: first reconcile — ping Kene for anything at 'staged', and flag anything stuck at 'building' or 'staged' for longer than one full sweep cycle. Then delegate up to delegation.max_concurrent_children 'discovered' postings as a parallel batch, stages 2 through 9, marking each 'building' at dispatch. Never call the submit action from this job, and never let a delegated child attempt to message Kene." \
  --skill job-hunting-orchestrator \
  --enabled-toolsets delegation,web,terminal,browser
```

(`--enabled-toolsets` here is a deliberate exception to the "scope
tightly" cost advice given elsewhere in this file — the `delegation`
toolset has to be present for any of this to work. I couldn't confirm a
dedicated CLI flag for this the way I couldn't for `enabled_toolsets`
generally — same caveat as job #1's `--script` note; fall back to the
`cronjob(...)` tool-call form if `hermes cron create` rejects this flag.)

## 4. Ghost-check / outcome nudge

Daily. Runs the email-scan outcome pass first (see
`11-analytics-and-learning`'s "Email-scan outcome detection" section),
then flags whatever's still `pending` with no matching processed email
after 21+ days, and asks Kene for a quick status update on that
genuinely-untrackable remainder rather than assuming silence means
rejection. Not blueprinted: `job-hunting-analytics` already carries job
#5's weekly-review blueprint, and a skill can only declare one.

```
hermes cron create "0 18 * * *" \
  "Run job-hunting-analytics: first run the email-scan outcome pass using the himalaya email skill, writing any confidently-classified outcomes with outcome_source: email_scan. Then find applications with sent_at more than 21 days ago and outcome still 'pending'. Ask Kene for a quick status update on each (or mark ghosted if he confirms). Use [SILENT] if there's nothing to check." \
  --skill job-hunting-analytics
```

## 5. Weekly self-improvement review

Monday morning. The core of the learning loop — see
`11-analytics-and-learning/SKILL.md` Section "Weekly self-improvement
review" for exactly what this does. **Ships as a blueprint** (see
"Install path" above) — the command below is what `/suggestions accept`
runs on your behalf.

```
hermes cron create "0 8 * * 1" \
  "Run job-hunting-analytics's weekly self-improvement review: pull the last 4-8 weeks of application data, run every correlation check in 11-analytics-and-learning/references/metrics-schema.md Section E, draft skill-edit proposals for anything that clears the sample-size and effect-size thresholds and enqueue them, then release only this week's rotation group per 11-analytics-and-learning/references/metrics-schema.md Section E (plus any queued proposal whose effect size has materially grown), staging released proposals via skill_manage with write_approval, and deliver the weekly digest." \
  --skill job-hunting-analytics
```

Optional: make this delivery continuable (`cron.mirror_delivery` config,
or per-job `attach_to_session` if your Hermes version exposes it — check
`user-guide/features/cron.md` for the current name/availability on your
install) so a reply like "why did response rate drop this week" lands
with the digest already in context instead of starting a session with no
memory of what it just said.

## 6. Monthly question-bank refresh (trickle, staged)

Monthly, off-hours. Small incremental crawl against the ATS public APIs,
re-clustered against the full accumulated raw history, staged as a
candidate — never auto-applied to the live bank. See
`07-context-architect/references/bank-refresh-automation.md` for the full
reasoning and the diff/promote mechanics. Not blueprinted, same reason as
job #4 — `job-hunting-context-architect` isn't carrying a blueprint of
its own yet, but this and job #7 are both monthly maintenance jobs
sharing that skill, and a skill can only declare one blueprint; adding
one here would arbitrarily pick #6 or #7 over the other.

```
hermes cron create "0 5 1 * *" \
  "Run an incremental question-bank refresh per 07-context-architect/references/bank-refresh-automation.md: crawl a small batch, curate a candidate bank, diff it against the live shared/question_bank.yaml, and deliver the diff as a Telegram digest if non-trivial. Do NOT run promote without Kene's explicit approval. Use [SILENT] if the diff is empty." \
  --skill job-hunting-context-architect
```

## 7. Monthly title-taxonomy refresh (trickle, staged)

Same staged-approval shape as job #6, applied to the title-profile
database instead of the question bank — see
`07-context-architect/references/title-taxonomy.md`'s "Refresh cadence"
section. Monthly here is the incremental/scoped pass; the full quarterly
re-crawl across a wider occupation set is run manually, not on cron, for
the same "which new occupations to prioritize is a judgment call"
reasoning `question-bank-pipeline.md` already gives for its own
quarterly step.

```
hermes cron create "0 6 1 * *" \
  "Run title_taxonomy_builder.py's enrich command scoped to occupations relevant to the current target-profile.yaml (--relevant-only), re-embed, and diff the resulting market_signals against the live title_taxonomy.sqlite. Deliver a digest of what changed. Never overwrite the O*NET-sourced base layer, only the market_signals layer. Use [SILENT] if nothing changed." \
  --skill job-hunting-context-architect
```

## 8. Nightly Tier 1 backup (no-agent mode)

**Not optional.** This is the only durable record the system has, and
losing it silently degrades job #5's learning loop with no signal that
anything is wrong. Full survey of what is worth saving, and why, in
`security/backup-and-recovery.md`.

Pure script, zero LLM cost. `[SILENT]` on success, loud on failure —
which is the point: a backup job that says nothing when it breaks is
worse than no backup job.

```
hermes cron create "0 3 * * *" --no-agent \
  --script backup.sh --deliver telegram
```

The script ships at `security/scripts/backup.sh`; copy it to
`~/.hermes/scripts/` — same placement rule as job #1's wake-gate script.
Set `BACKUP_GPG_RECIPIENT` before first run, or it warns on every
snapshot that your resume, contact details and salary expectations are
sitting unencrypted.

What it does that a `cp` does not:

- **Checks `PRAGMA integrity_check` first** and aborts if it fails,
  rather than copying a corrupt database over the last good snapshot.
- **`VACUUM INTO`, not `cp`** — a consistent snapshot of a file that may
  be mid-write.
- **Versions**: 7 daily, 13 weekly, 12 monthly, pruned on schedule. The
  realistic failure is a bad write found a week later, not a dead disk,
  and a single overwritten slot cannot help with that.
- **Covers the rest of Tier 1** — `memory/`, the skill tree (job #5 has
  been editing it since install; a fresh install gets you the package,
  not your version of it), the sent-artifact archive, and the Holographic
  fact store, which lives outside the skill tree and is therefore the
  easiest thing here to forget.
- **Excludes derived data** — the qmd index and `journal_export/` are
  rebuildable, and backing them up offers false reassurance at real cost.

## 8b. Quarterly restore verification

A backup nobody has restored is a hypothesis. This one restores the
newest snapshot into a scratch directory and asserts a row count, then
deletes it.

```
hermes cron create "0 4 1 1,4,7,10 *" --no-agent \
  --script verify-restore.sh --deliver telegram
```

Deliberately a real job rather than a line in a runbook, because the
whole failure mode being guarded against is "nobody got around to it."

## 8c. Weekly Tier 2 backup

Research caches, seeded config, question bank and taxonomy index.
Regenerable, which is why this is weekly rather than nightly — but
`shared/individual_research_cache/` is built from **metered** enrichment
providers, so losing it means paying again for lookups already paid for.
`v_cost_per_outcome` (addendum 10) now measures that directly.

```
hermes cron create "0 4 * * 0" --no-agent \
  --script backup-tier2.sh --deliver telegram
```

Kept as a separate script from job 8 rather than a flag on it: Tier 1 runs
nightly and must never be skipped, Tier 2 is weekly and may be. One script
with a mode flag invites running the cheap mode out of habit.

## 9. Interview-prep sweep

Twice daily, business hours. Builds (or refreshes) a prep brief and
flashcard deck for any application with an interview request that
hasn't been processed yet, or that has a newer round's details than the
last brief covered. **Ships as a blueprint** (see "Install path has
changed" above) — the command below is what `/suggestions accept` runs
on your behalf.

```
hermes cron create "0 9,15 * * 1-6" \
  "For every application where interview_request_at is set and either last_interview_prep_at is null or a newer interview_detail email_insights row exists, build or refresh the prep brief and flashcard deck per job-hunting-interview-prep's Part 1 and Part 2, then stamp last_interview_prep_at. Deliver each brief as its own Telegram message. Never start a live study session from this job." \
  --skill job-hunting-interview-prep \
  --script interview-prep-wake-gate.py
```

**Cost control**: `--script interview-prep-wake-gate.py` attaches the
gate covered in `13-interview-prep/SKILL.md`'s "Trigger conditions" —
unlike the discovery gate, this one is a pure DB query with no external
fetch involved, so it's a strictly reliable skip/wake decision, not a
best-effort one. Copy the script to `~/.hermes/scripts/` first (see the
"One follow-up step" note above). Same honesty caveat as job #1 applies
to the `--script` + `--skill` combination here — see that job's note for
the `cronjob(...)` tool-call fallback if `hermes cron create` rejects it.

**Never delivers a live study session** — Part 3 of that skill (the
actual practice/quiz flow) needs Kene's live answers to grade against
and cannot run from cron. This job only ever does the unattended build
half.

## 10. Social listening scan

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

## 11. Career-pulse journal check-in

Cadence is Kene's own setting (`16-career-pulse/SKILL.md` — daily is the
practical ceiling, a few times a week is a reasonable default; the
example below assumes 3x/week, adjust freely). Delivers a short prompt,
not a report — this job's output is a question, not a digest.

```
hermes cron create "0 20 * * 1,3,5" \
  "Run job-hunting-career-pulse's journal check-in: send Kene a short, low-key prompt (rotate through: what got hard this week, what got resolved, what shipped, who you worked with and how it went). Store the raw response in career_journal immediately. Flag anything that reads like a durable fact and hand it to job-hunting-context-architect as a proposed addition — never write directly to MEMORY.md/USER.md/target-profile.yaml/the STAR bank. Keep the tone practical, not performative." \
  --skill job-hunting-career-pulse
```

## 12. Explicit-channel profile monitor

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

## 13. Cold prospecting cadence

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

## 14. Career path plan re-evaluation

Same cadence family as `16-career-pulse`'s weekly profile-monitor job
(job 12) — re-checks every `active`-status row in `career_path_plans`
against the current profile, logs a new row to
`career_path_plan_reevaluations` for the run itself, and updates any
`career_path_plan_roadmap_items` a new confirmed fact actually closes
(with a corresponding row in `career_path_plan_roadmap_item_history`,
`trigger: cron_reevaluation`). Never changes `title_variants` on its
own — Step 5's "search for this now" decision stays a Kene-confirmed
action regardless of how much of the roadmap closes on its own.

```
hermes cron create "0 9 * * 1" \
  "Run job-hunting-career-path-planner's re-evaluation pass: for every active row in career_path_plans, re-run the gap analysis against the current confirmed profile — once per open stepping stone and once for the final target. For each career_path_plan_roadmap_items row that new evidence closes, update its status to resolved, set resolved_by_evidence_ref to the specific confirmed fact that closed it, and log the transition to career_path_plan_roadmap_item_history with trigger=cron_reevaluation. For each career_path_plan_hop_gaps row the new evidence satisfies, set evidenced_at and evidence_ref. Where a hop is status=achieved, all its hop_gaps are evidenced, and estimated_dwell_months has elapsed since achieved_at, propose moving it to matured — never set matured directly, since maturing a hop triggers a re-plan. Log one row to career_path_plan_reevaluations per plan for this run, including items_resolved_this_run and a short gap_summary_snapshot. Never modify target-profile.yaml's title_variants from this job — that stays a Kene-confirmed action via the skill's own Step 5. Use [SILENT] if nothing changed on any active plan." \
  --skill job-hunting-career-path-planner
```

**What this job deliberately does not do: re-plan.** Per
`19-career-path-planner/references/stepping-stone-engine.md` §6.2, a
matured, skipped or substituted hop means the remaining path was scored
against a profile that no longer exists and has to be **regenerated**,
not re-scored. Regeneration re-runs the candidate search, the liquidity
probes and the three-path comparison, and ends in a one-three-one choice
— which is a conversation, not something a Monday-morning cron job should
resolve on Kene's behalf.

So this job's job is to notice and surface. It proposes the
`achieved` → `matured` transition and flags any plan whose path is stale
(a hop status changed since the last run, `16-career-pulse`'s cascade
confirmed a profile change that moves a gap classification, the monthly
taxonomy refresh materially changed the target's record, or twelve months
have passed with no hop movement at all). The regeneration itself runs
when Kene next opens the skill, and writes
`replanned_path=1` plus the `replan_trigger` that caused it.

The annual-staleness trigger is worth keeping even though nothing is
wrong when it fires. A year-old market read is stale whether or not the
plan looks healthy, and one honest re-examination beats silent
persistence.

## 15. Enrichment tier-usage cycle reset

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

## 16. Bi-monthly configuration drift check

Two working passes, plus a protection role. `job-hunting-interests-profile`,
`job-hunting-output-templates`, `job-hunting-skill-composer` and
`job-hunting-onboarding` fire rarely enough that, if adopted by the
curator, they would go stale at 30 days and be archived at 90. A cron job
that references a skill exempts it from that walk — see `README.md`'s
curator section — so this job names all four while only two do work.

Deliberately not more frequent. The improvement loop runs after every
turn via the background review; job #5 runs weekly. This is a
configuration check, and a fortnightly version would mostly generate
noise — which matters because dismissed suggestions latch by
`dedup_key` and are never re-offered, so a noisy job permanently burns
proposals it should have saved for something real.

```
hermes cron create "0 9 1 */2 *" \
  "Bi-monthly configuration drift check. Both passes read-only unless Kene confirms: (1) job-hunting-interests-profile — re-read career-pulse journal entries since the last run against memory/interests-profile.md admission criteria; propose (never write) any new entry the journal now supports. (2) job-hunting-output-templates — compare shared/output-templates.yaml against what was actually sent since the last run; flag drift where a template no longer matches practice. Use [SILENT] if both passes come back empty." \
  --skill job-hunting-interests-profile \
  --skill job-hunting-output-templates \
  --skill job-hunting-skill-composer \
  --skill job-hunting-onboarding
```

Recurrence detection is deliberately **not** a pass here. Hermes covers
it twice natively — the background review creates class-level skills
when a technique recurs, and `cron/suggestions.py`'s `usage` source turns
a recurring ask into a proposed automation. `job-hunting-skill-composer`
still runs when those fire; it just does not poll for them.

## 17. Nightly retrieval-index refresh

Keeps the qmd index honest. `qmd embed` must re-run whenever indexed files
change, and the failure is silent — a stale index answers confidently with
old content rather than erroring. Jobs 1, 2, 10, 13 and 14 all write cache
files, so one nightly re-embed covers all of them rather than appending an
embed step to five jobs.

Also refreshes the journal projection, since `career_journal` lives in
SQLite and qmd only sees files — see
`07-context-architect/references/qmd-retrieval-layer.md`.

Runs `no_agent`: this is two deterministic commands, so there is no reason
to spend a model turn on it.

```
hermes cron create "0 3 * * *" \
  "Refresh the retrieval index" \
  --script qmd-reindex.sh \
  --no-agent
```

```bash
# ~/.hermes/scripts/qmd-reindex.sh
#!/usr/bin/env bash
set -euo pipefail
cd ~/.hermes/skills/job-hunting
python3 16-career-pulse/scripts/journal-export.py \
  --db shared/applications.db --out shared/journal_export/ --quiet

# qmd is an OPTIONAL component — see README's "Optional components and
# their dependencies". No-op rather than fail nightly if never installed.
if command -v qmd >/dev/null 2>&1; then
  qmd embed
else
  echo "[SILENT] qmd not installed — journal export refreshed, index skipped"
fi
```

Up to 24 hours of index staleness is accepted deliberately. These caches
already carry their own freshness conventions — `12-company-research`'s
90-day rule, and the same convention in `13-interview-prep`'s intel scrub —
so a day-old index sits well inside the tolerance the design already
assumes. If that stops being true, move the embed into each writing job
instead; do not leave it implicit.

## 18. Pause-expiry check

Daily, cheap, almost always silent. Looks for a `pipeline_pause` row whose
`resume_at` has passed and `resumed_at` is still NULL.

It does **not** restart discovery. It opens a conversation — see
`00-orchestrator/SKILL.md`'s resume pass. Two years of a career happened
in the meantime and the profile that generated the old searches is stale
in ways only Kene can confirm; silently resuming a search calibrated to
who he was in 2026 would surface exactly the roles he has outgrown.

```
hermes cron create "0 8 * * *" \
  "Check shared/applications.db for a pipeline_pause row where resume_at has passed and resumed_at IS NULL. If none, [SILENT]. If one exists, do not restart any cron jobs — message Kene that the pause has expired and offer to run the resume pass in 00-orchestrator/SKILL.md." \
  --skill job-hunting-orchestrator
```


<!-- Jobs 19-21 arrived from ADDENDUM-27's cron-jobs-addendum.md, where they
were numbered 15-17. Those numbers were already live here (enrichment
tier-usage reset, config drift check, retrieval-index refresh), so they were
renumbered on merge rather than installed as written. They are the cron half
of the outreach send-path project and depend on
shared/applications_db_schema_addendum_19.sql's connection / x_follow_state /
ig_fb_window columns -- run that migration before creating them. -->

## 19. LinkedIn connection-flow maintenance

Date-math only, no LinkedIn read — see `14-social-discovery-outreach/references/linkedin-connection-flow.md`. Flips stale pending connection
requests to `expired` at the ~6-month mark LinkedIn's own FAQ states
(re-verify that figure at the same cadence as the platform matrix).
Acceptance detection itself deliberately stays outside this job — it's
`kene_confirmed` or a Kene-triggered `computer_use_check`, never a
scheduled LinkedIn read, per `shared/site-access-model.md`.

```
hermes cron create "0 8 * * 3" \
  "Run job-hunting-social-discovery-outreach's connection-flow maintenance pass: for every social_outreach row with connection.status=request_sent_pending_acceptance, check connection.sent_at against a 6-month window and set status=expired for anything past it. Surface a short digest of newly-expired requests only — do not re-draft or re-send automatically. This job never checks LinkedIn itself; acceptance detection stays kene_confirmed or Kene-triggered computer_use_check per 14-social-discovery-outreach/references/linkedin-connection-flow.md, never a scheduled read of LinkedIn's own pages. Use [SILENT] if nothing expired this week." \
  --skill job-hunting-social-discovery-outreach
```

## 20. X follow-state check

Re-checks `target_follows_kene` for every X target still blocked on it
— a genuine, low-risk API read (Tier 1 per the matrix), not a scraping
operation. Surfaces newly-unblocked targets; never initiates new public
engagement on its own, that stays a Kene-approved draft through the
normal Part C flow. See `14-social-discovery-outreach/references/
x-follow-pursuit.md`.

```
hermes cron create "0 8 * * 3" \
  "Run job-hunting-social-discovery-outreach's X follow-state check: for every social_outreach row with contact.platform=x and x_follow_state.target_follows_kene != true, re-check via the v2 API read. Flip follow_back_achieved_at and surface in the digest for any target newly following Kene — these become eligible for a direct DM draft. Do not initiate new engagement_attempts from this job; engagement is drafted and cued through the normal Part B/C flow, this job only reads and updates state. Use [SILENT] if nothing changed." \
  --skill job-hunting-social-discovery-outreach
```

## 21. Instagram/Facebook engagement-window cleanup

The expiry-check half only — flags a 24-hour window that opened and
closed unused. Detection of a window *opening* stays event-driven off
Kene's own business inbox, not this job; see `14-social-discovery-outreach/references/ig-fb-engagement-window.md` for why those two halves
run on genuinely different cadences.

```
hermes cron create "0 8 * * 3" \
  "Run job-hunting-social-discovery-outreach's IG/FB window cleanup: for every social_outreach row with ig_fb_window.opened_at set and expires_at passed with messages_sent_in_window=0, set window_closed_unused=true and include in the digest. Does not touch opened_at detection — that stays event-driven off Kene's own inbox per 14-social-discovery-outreach/references/ig-fb-engagement-window.md, not this job. Use [SILENT] if nothing to flag." \
  --skill job-hunting-social-discovery-outreach
```

## 22. Weekly cron health check

Reads `cron_executions` (`shared/applications_db_schema_addendum_20.sql`)
and reports what has gone silent, what keeps failing, and which
wake-gates have skipped so many ticks in a row that "working perfectly"
and "broken open" have become indistinguishable. Nothing else in this
package reads whether a scheduled job ran.

Read-only. It writes no memory and touches no application row — it is
instrumentation, and Rule 5 owns what may write facts about Kene.

Run `python3 cron/executions.py seed` once after install step 4, or every
job will report as NEVER RAN. Each job records its own tick with
`executions.py record`; a wake-gate that returns `wakeAgent: false`
records `--outcome skipped` before it exits, which is what makes a skip
distinguishable from a job that never fired at all.

```
hermes cron create "0 9 * * 1" \
  "Run job-hunting-analytics' cron health check: execute python3 cron/executions.py report against shared/applications.db and surface its output in the weekly digest. Do not attempt to repair or re-create any job — report only, Kene decides what to re-register. Use [SILENT] if the report says all jobs are within expected cadence." \
  --skill job-hunting-analytics
```

## Chaining, if you want it (optional)

`context_from` (`user-guide/features/cron.md`, "Chaining jobs with
context_from") lets one job's most recent output feed directly into the
next job's prompt as context, instead of both independently re-querying
the applications DB for the same state. Given jobs #1 and #3 already
coordinate through the DB (job #1 writes `status='discovered'` rows, job
#3 queries for them), chaining is a genuine option here — job #3 could
declare `context_from=<job-1-id>` and skip re-deriving "what's new" from
scratch. It isn't done by default in the commands above because the DB
query already does the job correctly and chaining adds a dependency
between two jobs that currently fail independently (a stalled discovery
tick doesn't stall the sweep, and vice versa) — decide deliberately
before wiring it in, don't do it just because the mechanism exists.

## Monitoring

```
hermes cron list             # see all jobs and next-run times
hermes cron status           # gateway/scheduler health
hermes cron runs <job_id>    # recent execution history for one job
```
