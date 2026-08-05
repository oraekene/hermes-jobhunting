---
name: job-hunting-orchestrator
description: "Run, check, or manage the job-hunting pipeline end to end"
metadata:
  hermes:
    tags: [job-hunting, orchestrator, blueprint]
    category: job-hunting
    related_skills:
      - job-hunting-discovery
      - job-hunting-jd-parser
      - job-hunting-approval-submit
      - job-hunting-analytics
    blueprint:
      schedule: "30 7,10,13,16,19,22 * * 1-6"   # ~30min after each discovery-scan tick — see cron/cron-jobs.md job #3
      deliver: telegram
      prompt: "Process every application currently at 'discovered' status: run each through JD parsing, resume match, keyword analysis, resume customization, cover letter, application Q&A, and the risk-tactics gate, in that order. Stop each one at 'staged' and hand off to job-hunting-approval-submit for the Telegram review ping. Never call the submit action from this job — see shared/pipeline-rules.md Rule 1."
      no_agent: false
---

# Job-Hunting Orchestrator

## When this skill applies

Use this skill when Kene wants to run, check, or manage the job-hunting pipeline as a whole — starting a new job search session, asking 'what's staged for review', 'run the pipeline on this posting', 'how many applications are pending approval', or any request that spans more than one stage of job discovery, resume tailoring, cover letters, or application Q&A. This is the entry point that routes work to the other job-hunting/* skills in order and enforces the approval boundary. Do NOT use this for a single narrow task that clearly belongs to one stage only (e.g. 'just parse this JD') — call that stage's skill directly instead.

This is the front door to the whole pipeline. It exists so Kene can say
"find me jobs" or "process this posting" once, instead of invoking eight
skills by name every time.

Read `../shared/pipeline-rules.md` before doing anything else in this
skill or any skill it calls. Those rules are not optional.

## Pipeline stages, in order

| # | Skill | Input | Output |
|---|-------|-------|--------|
| 1 | `01-job-discovery` | search config / cron trigger | new posting(s), deduped against memory |
| 2 | `02-jd-parser` | posting URL or text | structured JD analysis |
| 3 | `03-resume-match` | JD analysis + base resume | match score + gaps |
| 4 | `04-keyword-analysis` | JD text + resume text | keyword JSON report |
| 5 | `05-resume-customizer` | all of the above | tailored `.docx` resume |
| 6 | `06-cover-letter` | all of the above | cover letter |
| 7 | `08-application-qa` | JD + application questions | drafted answers |
| 8 | `09-risk-tactics-gate` | everything from 5–7 | flags every risky claim for review |
| 9 | `10-approval-and-submit` | approved package | fills the form, waits for the Telegram tap, submits |
| 10 | `capability:interview_prep` | `interview_request_at` set on an application, or Kene asks directly | prep brief + flashcard deck (build phase); live practice session on request (study phase — see that skill's Part 3) |
| — | `07-context-architect` | run once up front, and again whenever a gap is found | builds/updates the memory + STAR bank that stages 3–8 all read from |
| — | `12-company-research` | run once per **company** (cached, not once per application) | employer research cache that 5, 6, 7's variant selection, and 7(app-qa) all read from — also read by 13's interviewer-research step |
| — | `11-analytics-and-learning` | runs after every outcome, and weekly via cron | funnel metrics + tactic effectiveness + skill updates |

## Running a full cycle

1. If `MEMORY.md` / `USER.md` / the STAR bank don't exist yet or look thin,
   run `onboarding` first — same trigger condition as before, one extra
   hop. `onboarding` runs `07-context-architect`'s Phase 0-4 as its own
   Session 1 and then continues through the rest of the settings catalog
   on a paced schedule, so setup isn't treated as finished the moment
   Phase 4 ends. Every later stage depends on this.
2. Right after stage 2 (`02-jd-parser`), check whether
   `shared/company_research_cache/{company_slug}.md` exists and is fresh
   (`12-company-research`'s own cache rule) — run it if not, before
   proceeding to stage 3. This is a per-company cache check, not a
   per-application step; skip it entirely when a fresh cache already
   exists for this employer.
3. For a single posting Kene pastes in: run stages 2 → 9 in order.
4. For discovery mode (cron-driven): stage 1 finds candidate postings,
   filters against the daily cap (`README.md`), then queues each one
   through 2 → 9. Never skip the queue to "save time" — the daily cap
   exists for a reason (see Rule 3 in pipeline-rules.md). **Default is
   serial** — one posting at a time, in order. An optional, opt-in
   parallel mode exists for stages 2–9 specifically (`references/
   parallel-pipeline-sweep.md`, via `delegate_task`) — off by default,
   genuinely faster when several postings are queued, and genuinely
   more moving parts; read that file's own honesty section on what I
   couldn't fully verify about it before turning it on.
5. After stage 9, whatever Kene decides (approve / reject / edit-then-approve)
   gets logged by `11-analytics-and-learning` immediately, not batched for later.
6. Stage 10 (`capability:interview_prep`) runs independently of the 2→9 flow —
   it's triggered by `interview_request_at` being set (its own cron gate,
   see `cron/cron-jobs.md` job #9) or by Kene asking directly, not by
   this skill chaining into it after stage 9. Route a direct request
   ("help me prep for the Acme interview") there without running the
   rest of this list first.

## What this skill must never do

Never call stage 9's submit action directly. Never let a cron job move a
staged application into "sent" on its own. If asked to "just auto-send
these," refuse and point back to `pipeline-rules.md` Rule 1 — that's the
one thing this system doesn't do, by design.

## Status queries

"What's pending?" / "How many staged today?" → read
`shared/applications_db_schema.sql`-backed DB (see `11-analytics-and-learning`)
and report counts by status: `discovered`, `building`, `staged`,
`awaiting_approval`, `approved_sent`, `rejected_by_kene`. Don't guess —
query the DB.

## Dry-run before pointing this at real employers (D8)

```
python 00-orchestrator/scripts/dry-run.py --skill-dir .
```

Runs the pipeline's invariants against a fixture posting in a throwaway
database. No network, and it never touches `shared/applications.db`.
Nineteen checks in two phases.

**Static — package integrity.** Frontmatter parses on all 25 skills; no
description exceeds 60 characters (the skill index truncates at 57, and
over that the trigger class is invisible *silently* — the skill simply
stops being selected); no description wastes the budget on boilerplate;
no dangling `related_skills` edge, since `build_edges` forms an edge only
where both endpoints exist and a typo produces no error; no duplicate
skill names or missing `metadata.hermes`; every reference path resolves;
no duplicate cron job labels and the numbering is contiguous; every
`shared/*.sql` is in the migration chain or explicitly superseded; every
`.py` parses.

**Runtime — fixture pipeline.** The migration chain applies from scratch,
the superseded `_3.sql` stays out of it, three discovery sources produce
one application with three recorded URLs, a skipped overqualification
gate is distinguishable from a passed one, nothing sits at `submitted`
without an approval decision, and soft-deleted journal entries leave the
live set.

The static phase makes D6, D7 and the reference-path work into *enforced*
invariants rather than one-time fixes. Each was corrected once by hand;
nothing stopped the next edit from reintroducing it, and every one of
those failures is silent.

Run it after any schema change, after editing a gate, and before a first
real run.

**It earns its place.** On its first execution it caught a live bug:
`journal-export.py` was probing for `created_at` and `entry`, while
`career_journal` actually uses `entry_at` and `raw_text`. Cron job 17
would have failed every night with "unexpected career_journal shape" —
and because that job also runs `qmd embed`, the retrieval index would
have quietly stopped updating too. Nothing else in the package would have
noticed.

## Hired — pause, then resume higher (`/pause`, `/resume`)

### Pausing

Triggered by Kene accepting an offer, or by asking directly. Six things
happen, and the order matters:

1. **Stop the discovery jobs** — 1, 2, 3, 10, 13. Record which in
   `pipeline_pause.paused_jobs` so resume restores exactly what was
   stopped rather than guessing. Jobs 8, 8b, 8c and 17 keep running:
   backups and index freshness are not search activity.
2. **Resolve in-flight applications.** Anything at `staged` or
   `submitted` needs a decision, not silent abandonment — withdraw,
   or leave running if he wants to see it through. An application left
   staged for two years is noise that will confuse the next resume pass.
3. **Snapshot the profile** into `profile_snapshot`. This is what makes
   resume work: the diff against it two years later is the answer to
   "what changed", and Kene will not remember.
4. **Record the accepted role** — `07-context-architect` writes the new
   title, employer and comp under Rule 5, and `employment_status` moves
   to `employed`.
5. **Set `resume_at`.** Kene's call: six months, two years, "remind me
   when I ask". Default suggestion is 18 months, which is roughly when
   the market's picture of you goes stale.
6. **Keep `16-career-pulse` running.** This is the part that makes the
   pause worth having. The journal keeps accumulating through the whole
   employed period, which is precisely the material the resume pass
   needs — and the reason it is not sitting idle.

### Resuming

Cron job 18 checks daily for a `pipeline_pause` row whose `resume_at` has
passed and `resumed_at` is NULL. It does **not** restart discovery. It
opens a conversation, because two years of a career happened and the
profile that generated the old searches is out of date in ways only Kene
can confirm.

The resume pass, in order:

1. **Diff the journal against `profile_snapshot`.** What was worked on,
   what shipped, what scope grew. This is the evidence base, and it
   exists only because the journal kept running.
2. **Propose STAR entries and domain-knowledge additions** from that
   period, through `07-context-architect`'s normal confirm-before-write.
   Two years of journal is usually several strong stories the bank has
   never seen.
3. **Establish the new seniority floor.** Job zone actually held, title,
   confirmed comp. Confirmed, never inferred — see below.
4. **Re-run Phase 1.5** against the updated profile. New title variants,
   and adjacency computed from where Kene is *now* rather than where he
   was. A Lead's adjacent titles are not an Analyst's.
5. **Recalibrate upward** — see the next section.
6. **Refresh the résumé** against the new record, and re-run the
   skill-drift check: two years of drift is the norm, not the exception.
7. **Only then restart the paused jobs**, restoring exactly the set
   recorded at pause.

### Recalibrating upward — the missing half of the schedule

`dynamic-target-calibration`'s `auto_relax_schedule` bends one way. The
longer a search runs while unemployed, the wider the net gets — lower
`match_score.minimum`, more tolerance. That is right for that situation
and it is only half a career.

There is no inverse, and its absence is why the pipeline would happily
show a Lead the Analyst roles it showed them three years ago:
`match_score` measures *fit*, and a role you could do easily fits
extremely well. Fit is not the same as advancement, and nothing was
measuring the difference.

`seniority_floor` is that inverse:

- **Job zone floor.** Roles below the level actually held are not
  surfaced by default. Gate 2's `title_delta` already computes this and
  already flags `[OVERQUALIFIED]` — it simply had no *current* level to
  compare against while `job_zone` came only from the original profile.
- **Comp floor.** Confirmed comp at the accepted role becomes the new
  `salary_floor` basis, so `comp_delta` measures against what Kene now
  earns rather than what he once asked for.
- **Adjacency shifts up with him.** Phase 1.5 computes adjacent titles
  from the current profile, so the same machinery that found lateral
  moves at Analyst finds them at Lead — including the next step up,
  which was never reachable from the old profile's embedding.

Two guards, because this is the one setting that can silently shrink
discovery to nothing:

- **Confirmed, never inferred.** A floor written from a title the
  pipeline guessed at could cut Kene off from most of the market without
  ever saying so.
- **A floor is not a hard filter.** A deliberate step sideways or down —
  a smaller company, a domain change, a better team — is a real and
  reasonable choice. Below-floor roles are flagged and de-prioritised,
  not deleted, and `[STRETCH]`'s counterpart tag says why a role was
  ranked low so Kene can overrule it.

**One standing exemption, and only one.** A `capability:career_planning`
stepping stone can deliberately sit below the floor — sector switches and
management-track entry both routinely cost a level for a year or two, and
that is the case Step 3.5 exists to plan for rather than to prevent. The
exemption is by record, not by override: it applies only to postings
matching that specific hop's title, only while its plan is `active` with
`active_search_status = 'searching'`, and only where
`career_path_plan_stepping_stones.seniority_floor_exemption = 1` — which
is set when Kene answers the comp-regression question in Step 3.5, not as
a side effect of accepting a plan. Exempted postings are surfaced
normally and tagged with the plan they belong to, so an intentional step
down never reads as the pipeline forgetting his level. Everything outside
that hop stays under the floor, and the exemption dies with the plan.

