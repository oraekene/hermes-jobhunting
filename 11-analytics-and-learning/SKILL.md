---
name: job-hunting-analytics
description: "Log pipeline outcomes and run the improvement review"
metadata:
  hermes:
    tags: [job-hunting, analytics, self-improvement, blueprint]
    category: job-hunting
    related_skills:
      - job-hunting-approval-submit
      - job-hunting-orchestrator
      - job-hunting-career-pulse
    blueprint:
      schedule: "0 8 * * 1"   # Monday morning — see cron/cron-jobs.md job #5
      deliver: telegram
      prompt: "Run the weekly self-improvement review: pull the last 4-8 weeks of application data, run every correlation check in references/metrics-schema.md Section E, draft skill-edit proposals for anything that clears the sample-size and effect-size thresholds and enqueue them, then release only this week's rotation group per references/metrics-schema.md Section E (plus any queued proposal whose effect size has materially grown), staging released proposals via skill_manage with write_approval, and deliver the weekly digest. The daily ghost-check/outcome-nudge pass (cron/cron-jobs.md job #4) and the two monthly refresh jobs (#6, #7) are separate, more frequent jobs — set those up manually per cron/cron-jobs.md, this blueprint only covers the weekly review."
      no_agent: false
---

# Analytics & Self-Improvement Loop

## When this skill applies

Use this skill to log every pipeline event and outcome (staged, approved, sent, response, interview, offer, rejection) to the applications database, and — on the weekly cron trigger — to review accumulated data and propose evidence-based edits to the other job-hunting/* skills. Triggers: any status change in an application's lifecycle, 'how are my applications doing', 'what's my response rate', or the scheduled weekly review. This is the skill that makes 'self-improving' concrete rather than a marketing phrase.

This is where Hermes's "creates skills from experience, improves them
during use" capability actually gets used for this system, instead of
just being a nice thing Hermes can do in general.

## Continuous logging (every session, not just weekly)

Every stage in the pipeline writes to the `applications` table
(`shared/applications_db_schema.sql`) as it completes its part — see
`references/metrics-schema.md` for the full field list. This skill owns
the schema and the write discipline: if a stage's output is missing a
field this skill needs, that's a bug in the calling skill, not something
to shrug off here.

Outcome updates (a response came in, an interview got scheduled, an
offer arrived, a rejection landed) get logged the moment Kene reports
them — via a quick message to Hermes ("got a rejection from Acme," "Acme
wants a screening call Thursday"). This skill parses that into the right
DB update. It does not require Kene to fill out a form; a normal sentence
is enough. Log `outcome_source: user_reported` on every update logged
this way.

**Email-scan outcome detection (built)** — requires Hermes's bundled
`himalaya` skill configured per `security/email-integration-setup.md`.
Runs as part of the daily ghost-check cron job (`cron/cron-jobs.md` job
#3), before the "ask Kene" step, not as a separate job:

1. For every application with `sent_at` set and `outcome` still
   `'pending'`: `himalaya envelope list --folder INBOX` (or a broader
   scope if replies don't land in the `JobHunt` label — recruiter
   replies often come from a personal address, not the ATS, so don't
   restrict this pass to the `JobHunt` label the way discovery's read
   does). Gmail's IMAP server doesn't support the `SORT` capability
   `envelope search` needs, so this is a plain list, filtered
   client-side: match envelopes whose `from` contains the company's
   known domain, or whose subject/date falls after `sent_at`.
2. For each candidate envelope, `himalaya message read <id>` for the
   full content.
3. Classify the message's content against the existing `response_type`
   enum (`auto_reject / human_reply / screen_request /
   interview_request`) plus offer/no-signal. **Only write to the DB on
   a confident classification** — an auto-generated "thanks for
   applying" acknowledgment is not a response, and an ambiguous message
   should fall through to the ghost-check's normal "ask Kene" path
   rather than guessing. This mirrors the schema's own comment: an
   automated read is a judgment call that can be wrong, so silence here
   defaults to *not writing*, not to a best guess.
3.5. **Regardless of whether step 3 reached a confident classification**,
   run the insight-extraction pass described in
   `shared/email-insight-extraction.md` over the same body already read
   in step 2 — no extra `himalaya message read` call, this rides along
   on the read that already happened. An `[UNVERIFIED]`-adjacent but
   distinct concern from step 3's classification: a message can fail to
   classify as a confident outcome and still contain a genuinely useful
   detail (an interviewer's name mentioned in an otherwise ambiguous
   note, a stated deadline). Write any qualifying rows to `email_insights`
   — this table is intentionally independent of whether `response_type`
   got written, so a classification failure never costs the detail too.
4. On a confident match: write `outcome`, `response_type`,
   `first_response_at` (or the relevant later-stage timestamp for an
   interview/offer), and `outcome_source: email_scan`. Then `himalaya
   message copy <id> "JobHunt/Processed"` (creating that label if it
   doesn't exist yet) so this message is never re-scanned — copying
   rather than moving keeps it wherever it already was.
5. Anything still `pending` after this pass **and** with no
   `JobHunt/Processed` label anywhere in its history is what actually
   reaches Kene in the ghost-check ping — the daily nudge is now
   genuinely scoped to the untrackable remainder (verbal offers from a
   call, silent ghosting with no email trace) rather than everything,
   which was the original design intent noted in `cron/cron-jobs.md`
   job #4 before this was built.

This runs read-only against the inbox (`envelope list` / `message
read` / `message copy` only — no `message delete`, no `template send`
in this skill's usage here) and never drafts a reply on Kene's behalf;
that stays entirely outside this skill's authority. Writes are limited to
`applications` (step 4) and `email_insights` (step 3.5) — both are
Hermes's own local DB, nothing goes back out to the inbox or the employer.

## Weekly self-improvement review (cron-driven, see cron/cron-jobs.md)

This is **Tier 1** of this pipeline's self-improvement loop: fast, cheap,
explainable correlation nudges, running weekly, in-band. A separate,
slower, manual **Tier 2** exists for deeper evolutionary optimization
against real outcome data — see `references/gepa-self-evolution.md`
before ever reaching for it; it's a genuinely different tool with its
own real cost and a mandatory safety patch, not a bigger version of what
follows here. Nothing below assumes Tier 2 exists or has run.

1. Pull the last 4–8 weeks of data from the `applications` table.
2. Run every correlation check listed in `references/metrics-schema.md`
   Section E. Require a minimum sample size (default: 15 sent
   applications per bucket) before treating a correlation as
   actionable — small-sample noise doesn't get to rewrite a skill.
3. For each correlation that clears the sample-size bar and shows a
   meaningful effect (default threshold: 10+ percentage-point difference
   in response rate), draft a specific, small edit to the relevant
   skill file. Examples of the kind of edit this produces:
   - "Exact-phrase mirroring: last 30 sent apps show +14pp response rate
     when used vs not (n=30/27). Keep enabled, no change needed."
   - "Values-alignment section: no meaningful response-rate difference
     over 40 apps (n=22/18, Δ=2pp). Recommend downgrading to optional —
     use only when the posting's stated values are unusually specific,
     not by default."
   - "Applications sent >48h after posting show a 9pp lower response
     rate than <24h (n=35/19). Recommend `01-job-discovery` tighten its
     priority-queue window from 24h to 12h."
4. Load Hermes's bundled `software-development/hermes-agent-skill-authoring`
   skill before drafting this edit, so the proposed patch follows the same
   house style as the rest of this package (see `README.md`'s "Editing
   these skill files" section). **Then write the edit through Hermes's
   `skill_manage` tool with the `skills.write_approval` gate enabled**
   (see `security/security-setup.md` — note that gate is global, not
   scoped to this package) — the change gets staged under
   `~/.hermes/pending/skills/` and Kene reviews and approves it before it
   takes effect. Self-improvement here means "propose a tested change,"
   not "silently rewrite the pipeline's logic." Log the proposal and
   Kene's decision to `skill_self_edits` (see the SQL schema).
5. Deliver a weekly digest to Telegram: funnel counts, response/interview/
   offer rates, the correlation findings, any pending skill-edit
   proposals awaiting approval, and any `email_insights` rows (from step
   3.5, or from `01-job-discovery`'s own pass) not yet marked
   `surfaced_in_digest` — batched here rather than repeated from the
   immediate per-run digest, per `shared/email-insight-extraction.md`'s
   "Where this surfaces" section.
6. **Rate the facts that informed each resolved application** — required
   whenever the Holographic layer is configured, not optional (see
   `07-context-architect/references/holographic-memory-layer.md`). For
   every application that reached a terminal outcome this cycle, call
   `fact_feedback(action="helpful", fact_id=...)` on the atomic facts
   that informed its story selection where it drew a real response, and
   `action="unhelpful"` on a clear miss.

   **Why this is not optional.** Trust score is the *only* ranking
   dimension Holographic has. It starts at 0.5 and moves only through
   this call. Left off, every fact sits at 0.5 forever and retrieval
   ranks by relevance alone — which is the same undifferentiated store
   the memory layer was adopted to improve on. The signal is generated on
   every run regardless; the choice is whether to record it or discard
   it, and discarding it costs the layer its point.

   **What counts as a clear miss**, stated tightly because the asymmetry
   is punitive (+0.05 helpful, −0.10 unhelpful — two bad ratings undo
   four good ones): a fact is `unhelpful` only when Kene **edited it out**
   of a draft, or when `08-application-qa` or `09-risk-tactics-gate`
   rejected the claim it supported. A rejection is not a miss. Most
   applications are rejected for reasons having nothing to do with which
   story was picked, and rating facts unhelpful on outcome alone would
   drive the whole bank toward zero on a signal that is mostly noise.
   **No response is not a miss either** — it is absence of evidence, and
   it gets no rating in either direction.

   Batch this. One pass over the cycle's resolved applications, not a
   call per fact per run.

7. **Recompute fact influence** — the second ranking dimension, separate
   from trust (`07-context-architect/references/fact-influence-scoring.md`,
   `applications_db_schema_addendum_17.sql`). Same step as 6 because the
   same events are already open: as each resolved application is graded,
   write `fact_influence_events` rows for the facts that materially
   changed an output — passed or failed a claim at
   `09-risk-tactics-gate` (weight 3), survived into a staged document
   (2), drove a STAR selection over an alternative (2), or filtered a
   posting (1). Retrieval without use scores nothing; a fact probed and
   passed over is evidence *against* its influence.

   Then recompute `fact_influence` from the trailing 180 days of events —
   recompute, never increment, since a running total drifts and cannot
   implement the window without a second pass to undo itself.

   Three lines in the digest: top 5 by influence; the
   `v_low_trust_high_influence` rows; and a **count** of long-stale
   zero-influence facts. A count, never a list — zero influence means
   "not yet needed", not "dead weight", and nothing here should be shaped
   like a prune prompt.

## Reporting on demand

"How am I doing" / "what's my response rate this month" → query the DB
directly, report actual numbers, never estimate. If the sample size is
too small for a rate to mean much (e.g. 3 applications sent this week),
say so rather than presenting a noisy percentage as a trend.

## What this skill does not do

It does not change Kene's daily volume cap, does not change the
approval requirement in `10-approval-and-submit`, and does not touch
`shared/pipeline-rules.md` — those are outside its authority regardless
of what the data seems to suggest. Self-improvement here is scoped to
*which tactics and timing choices work*, not to *whether a human reviews
before sending*. Tier 2 (`references/gepa-self-evolution.md`) is
deliberately scoped even narrower than Tier 1 — it never touches
`09-risk-tactics-gate` at all, for the reason that file explains in
detail.

## `skill_self_edits` does not require curator adoption (C3)

This package references `skill_self_edits` in a dozen places, and
`README.md` recommends **not** adopting these skills into the curator.
Both are correct, and read in isolation they look contradictory — so
state the reconciliation once, here, where the self-editing actually
happens.

Autonomous rewriting by Hermes's **background review** requires curator
adoption. That is the mechanism the protection rules block on unadopted
skills.

This skill does not use that path. Job 5 writes through `skill_manage`
with `skills.write_approval`, which stages edits under
`~/.hermes/pending/skills/` for Kene to approve — a consented, foreground
path that works on unadopted skills. So the package self-improves without
ever entering the curator's candidate list, and therefore without
exposure to the 90-day archival clock or to consolidation.

Adoption buys autonomous, unattended rewriting. It costs archival and
consolidation exposure. For a 25-skill package all sharing one name
prefix, that trade is not worth taking — see `README.md`'s curator
section for the full reasoning.

## Which mechanism owns which change (R1)

Five things in and around this package can change how it behaves. They
overlap, and until this table existed nothing said which owned what — so
the same improvement could be proposed twice by two paths. That is not
merely untidy: `cron/suggestions.py` caps pending suggestions at five and
latches dismissals by `dedup_key`, so a duplicate proposal that gets
dismissed **permanently burns a slot** for something real.

| Mechanism | Cadence | Owns | Never does |
|---|---|---|---|
| **Hermes background review** | After turns | Durable facts about Kene into memory; class-level techniques into skills | Anything about *this* pipeline's thresholds or correlations — it has no access to the applications DB |
| **This skill (job 5)** | Weekly | Everything derived from outcome data: pitch selection, keyword weighting, calibration proposals, threshold tuning | Facts about Kene. Those are memory's, not a skill edit |
| **Hermes curator** | Weekly, idle-triggered | Skill lifecycle — stale, archived, consolidated | Content. And nothing at all here unless skills are adopted, which `README.md` recommends against |
| **`18-skill-composer`** | On demand | Authoring a new skill, or restructuring one, once a need is established | Detecting that need — see below |
| **`cron/suggestions.py` `usage` source** | Continuous | Noticing a recurring ask and proposing an automation for it | Writing anything; it proposes and waits |

**The rule for detection.** Recurrence detection is native and happens
twice already — the background review creates class-level skills when a
technique recurs, and the `usage` suggestion source turns a recurring ask
into a proposed job. Nothing in this package should poll for the same
signal. `18-skill-composer` runs *when those fire*; it does not hunt.
Job 16 dropped two passes on exactly this reasoning.

**The boundary that actually matters.** Memory holds who Kene is and what
state his search is in. Skills hold how to do this class of task for him.
When Kene corrects *how* something was done, the fix belongs in the skill
body — not only in memory, which is where it would otherwise land by
default and quietly fail to change behaviour.

**What the background review must not capture**, lifted from its own
instructions because this skill's proposals should honour the same
exclusions: never a negative claim about a tool ("X is broken"), because
those harden into refusals cited against itself for months after the
problem was fixed; never an environment-dependent failure; never a
transient error; never a one-off task narrative.

