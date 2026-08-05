# Parallel Pipeline Sweep via `delegate_task` (optional, opt-in, off by default)

**Read this before turning this on.** This feature genuinely speeds up
the pipeline sweep, and it also genuinely has one piece of mechanics I
could not fully resolve without a live Hermes gateway to test against —
called out precisely below, not glossed over, with a design that stays
correct either way the ambiguity resolves. Serial processing (today's
default) stays the default. Turn this on deliberately, start small, and
read the staleness safety-net section before you do.

## What this actually changes

Today, `00-orchestrator`'s pipeline sweep (cron job #3) processes every
`discovered` application through stages 2–9 **serially**, one posting
at a time, in a single agent turn. This mode instead **delegates each
posting's build phase (stages 2–9) to its own subagent**, up to
`delegation.max_concurrent_children` (default 3) running at once —
genuinely faster when several postings are queued, at the cost of real
added complexity and a mechanical wrinkle described below.

**Stage 10 never moves.** `10-approval-and-submit`'s actual Telegram
ping stays in the parent, never inside a delegated child — this isn't
new caution, it's a hard mechanical fact: leaf subagents cannot call
`send_message` (confirmed in `user-guide/features/delegation.md`'s
"Key Properties" list — `delegate_task`, `clarify`, `memory`,
`send_message`, `cronjob` are all blocked for leaf children). A child
that finished building a package has no way to actually tell Kene about
it. That's the reason the status flow below exists.

## The one thing I could not fully verify

`delegation.md` describes two different timing behaviors depending on
who's calling `delegate_task`: "Top-level model calls run in the
background automatically. Hermes returns a handle immediately so the
conversation can continue, then posts the result back as a new
message." — versus an *already-delegated* `role="orchestrator"` child,
which "waits for its own workers so it can synthesize their results
before returning" (synchronous, from that child's own perspective).

The docs are written with an interactive chat session as the mental
model — "so the conversation can continue" clearly describes a human
free to keep typing while a background task runs. What isn't explicitly
addressed anywhere I could find: whether a **cron-triggered top-level
agent turn** — which doesn't have a live human "continuing the
conversation" the way an interactive session does — gets its
`delegate_task(tasks=[...])` batch result back **within that same
triggered turn**, or whether the result genuinely arrives later as a
fresh message that only a **continuable** cron job (`cron.mirror_
delivery`/`attach_to_session` — see `cron/cron-jobs.md`) would be set up
to receive and act on. I read every relevant doc section I could find
(`delegation.md` in full, `cron.md`'s only cross-reference to
delegation, which is a toolset-cost mention with no timing detail) and
couldn't settle it from documentation alone, and had no live gateway to
dispatch an actual batch against and observe.

**The design below is built to be correct under either answer**,
rather than betting on one:

- The cron job is configured as continuable regardless (harmless if the
  batch turns out to complete synchronously within the same turn;
  required if it doesn't).
- Nothing depends on the result arriving in any particular turn. Every
  future sweep tick re-checks for anything left unfinished from a prior
  batch and finishes it, whether that's because the async result never
  got processed or because a child genuinely crashed. See "Reconcile
  before you delegate more" below — this is the load-bearing part of the
  whole design, not a footnote.

## Status flow this depends on

`shared/applications_db_schema.sql`'s `status` column now formalizes
four stages instead of jumping straight from `discovered` to
`awaiting_approval`:

```
discovered -> building -> staged -> awaiting_approval -> approved_sent / edited_then_sent / rejected_by_kene
```

- **`building`** is set by the **parent**, immediately at dispatch —
  before the delegated child has done any actual work. This is
  specifically what stops a later sweep tick from picking up the same
  `discovered` posting and delegating it a second time while the first
  batch is still in flight (or stuck).
- **`staged`** is set by the **child**, once its package clears
  `09-risk-tactics-gate`. Writing to `applications.db` is an ordinary
  file/DB operation, not one of the blocked tools, so a leaf child can
  do this even though it can't call `memory` or `send_message`.
- **`awaiting_approval`** is set by `10-approval-and-submit`, in the
  parent, once the Telegram ping is actually sent — never by a child.

## Composing each child's task — subagents know nothing

`delegation.md`'s own warning, verbatim: "Subagents start with a
completely fresh conversation. They have zero knowledge of the parent's
conversation history, prior tool calls, or anything discussed before
delegation." No automatic `MEMORY.md`/`USER.md` injection either — a
subagent's system prompt is "a focused system prompt built from your
goal and context," not the full profile system prompt a normal session
gets. Two consequences for how the parent composes each task:

1. **Paste the needed memory content directly into `context`**, don't
   assume the child can see it. The parent (a normal top-level agent)
   does have `MEMORY.md`/`USER.md`/`target-profile.yaml`/`fidelity_
   mode` available — pull the relevant excerpts and include them as
   literal text in the child's `context` field.
2. **Tell the child explicitly to read and follow the skill files**,
   rather than assuming it already knows `02-jd-parser` through
   `09-risk-tactics-gate` exist. It inherits the parent's toolsets
   (including file-reading), so an instruction like "read
   `~/.hermes/skills/job-hunting/02-jd-parser/SKILL.md` through
   `~/.hermes/skills/job-hunting/09-risk-tactics-gate/SKILL.md` in
   order and follow each one's process precisely" is something it can
   actually act on — don't rely on implicit skill discovery working the
   way it does in a normal session.

```python
delegate_task(tasks=[
    {
        "goal": "Build a complete application package for posting <id> at <Company> (<Role>) — stages 2 through 9 only, stop at the risk-tactics gate.",
        "context": f"""
Read and follow, in order: ~/.hermes/skills/job-hunting/02-jd-parser/SKILL.md,
03-resume-match, 04-keyword-analysis, 05-resume-customizer, 06-cover-letter,
08-application-qa, 09-risk-tactics-gate (all under the same job-hunting
skill directory). Posting URL: <url>. JD text: <full text>.

Target profile (from shared/target-profile.yaml): <relevant excerpt>
Fidelity mode: <strict|balanced|embellish>
Relevant STAR bank entries (from memory/star-story-bank.md): <relevant excerpt>
Company research cache, if present: <excerpt from shared/company_research_cache/{{slug}}.md>

When 09-risk-tactics-gate passes (or the posting fails and needs to stay
at 'building' with a logged reason — do NOT silently mark a failed
build as staged), write status='staged' directly to this posting's row
in shared/applications.db. Do not attempt to message Kene — you cannot,
and you shouldn't try. Your final summary should state clearly whether
the posting reached 'staged' or failed, and why.

DATABASE RULES — these are not advisory (shared/db-concurrency.md):
- YOU DO NOT WRITE TO THE DATABASE. Not your row, not any row. Reads are
  fine and unrestricted — query applications.db freely.
- Report your result by writing ONE file:
    shared/.outbox/<application_id>.<attempt>.json
  with: application_id, attempt, session_id, outcome
  ('staged'|'failed'), application_updates, child_rows (keyword_analysis
  / tactics_log / open_gaps rows), artifacts_path, and failure_stage +
  failure_reason if you failed. Anything large — a resume draft, a
  research dossier — goes to artifacts_path on disk; the outbox carries
  the path, not the content.
- The parent ingests the outbox serially and does all the writing. This
  is why there is no write contention and why you are not competing with
  the other children running right now.
- A pre_tool_call hook enforces this. If you try to write, you will be
  blocked with an explanation. Do not attempt to route around it — write
  the outbox file and say what you did in your summary.
- If you fail, say so in the outbox with outcome='failed' and a reason,
  and leave it there. Do not try to set status='failed' — the parent sets
  that during reconciliation, because the failure that matters most is
  the one where you are no longer running to report it.
""",
        "max_iterations": 40,
    }
    for posting in batch  # batch built from postings currently at 'discovered', capped at max_concurrent_children
])
```

## The pipeline-sweep job's actual prompt, in two phases, every tick

**Phase 1 — reconcile before you delegate more.** This runs on *every*
tick, unconditionally, before touching anything new:

1. Any posting at `status='staged'` — run `10-approval-and-submit`'s
   ping step for it now. This is what actually gets a completed,
   delegated build in front of Kene; nothing else does, since the child
   that built it couldn't message him itself.
2. Any posting at `status='building'` or `status='staged'` for **longer
   than one full sweep cycle plus a safety margin** (roughly 7 hours,
   given the ~3.5-hour default cadence between ticks — long enough that
   "it'll get picked up next tick" isn't a plausible explanation
   anymore) — surface this to Kene as a stuck-batch warning rather than
   silently retrying or silently ignoring it. This is the actual safety
   net for the async-timing question above: whether the ambiguity
   resolves as "same-turn" or "later message," a genuinely dropped or
   crashed result cannot silently vanish past this check for more than
   one extra tick.

3. **Ingest the outbox before anything else in this phase**
   (`shared/db-concurrency.md`, "The outbox"). Children write no SQL;
   they leave one JSON file each under `shared/.outbox/`. Read them in
   `application_id` order — not filesystem order, so a partially
   ingested batch is in a state you can reason about — and apply each in
   its own transaction, so one malformed file cannot roll back nine good
   ones. Consumed files move to `.outbox/consumed/`, malformed ones to
   `.outbox/rejected/` with the application set to `failed` and the
   reason logged. Never half-apply a file, and never guess at what a
   child meant.

   An outbox file with no corresponding DB state is exactly what a
   crashed child leaves behind, and it is a complete record of what that
   child accomplished before it died. That is what makes `vanished`
   below diagnosable rather than just labelled.

4. **Resolve stuck rows rather than only reporting them** —
   `shared/applications_db_schema_addendum_15.sql` and
   `shared/db-concurrency.md`. Warning about a stuck row every tick
   forever is not a resolution, and it was the state before addendum 15:
   a failed build and an in-flight build were the same row, told apart
   only by how long they had sat there.

   The parent — never the child — sets the terminal state:

   - Child reported a failure and the row is still at `building`: set
     `status='failed'`, record `last_failure_stage` /
     `last_failure_reason` from its summary, and close the open
     `application_build_attempts` row with `outcome='failed'`.
   - Child reported nothing at all and the row is past the stale
     threshold: same, but `outcome='vanished'` and a reason saying so.
     The distinction matters — "the JD was an image-only PDF" and "the
     child died" are different problems and only one of them is worth
     retrying.
   - `build_attempts < 3`: return the row to `discovered` so a later
     tick picks it up. Move any partial output to
     `<build_artifacts_path>.failed-{n}/` first. **A retry restarts at
     stage 2**, never mid-pipeline — resuming from the failed stage means
     trusting artifacts produced by a run that demonstrably failed.
   - `build_attempts >= 3`: leave it at `failed`, surface it to Kene
     **once** with the reason, and never retry it again. Three failures
     is information about the posting or the pipeline, and a fourth
     attempt is not the response to it.

   `failed` rows are invisible to Phase 2, which selects on `discovered`
   only, so nothing here blocks the queue.

**Phase 2 — delegate new work.** Only after phase 1: take postings at
`status='discovered'`, up to `delegation.max_concurrent_children`,
immediately mark each `building` (the race guard), then issue the
`delegate_task(tasks=[...])` batch from the snippet above.

## Rollout — don't flip this on at full volume

Start with a small batch (2, not the configured max) and watch it for a
few full cycles before trusting it at normal volume — specifically watch
for anything hitting the Phase 1 staleness warning, since that's the
signal the async-timing question above resolved less favorably than
hoped. If it never fires, you've effectively answered the open question
empirically; if it does fire occasionally, the system is already
catching and surfacing it rather than losing the posting, which is the
property this whole design was built around.

## Configuration

```yaml
# ~/.hermes/config.yaml
delegation:
  max_concurrent_children: 3      # leave at default unless you have a specific reason
  max_iterations: 50               # per child; 40 is passed explicitly per-task above, plenty for stages 2-9
```

Also configure the pipeline-sweep cron job as continuable (`cron.
mirror_delivery` or the current equivalent — check `user-guide/
features/cron.md` for the exact name on your Hermes version) — required
if the async-delivery interpretation turns out to be the correct one,
harmless if it doesn't.

## What this does not change

`enabled_toolsets` scoping (`cron/cron-jobs.md`) still applies — the
`delegation` toolset needs to be present on this job for any of this to
work, which is a deliberate exception to the "scope tightly" advice
given for the other cron jobs. Rule 1 is untouched: nothing here lets a
package reach an employer without a live Telegram approval, and the
`pre_tool_call` submit-gate hook (`security/hooks/verify-submit-
approval.py`) still applies exactly the same regardless of whether the
package was built serially or by a delegated child.

## Two-stage review, natively (R6)

This file hand-rolls delegation fan-out. Hermes ships the pattern —
`software-development/subagent-driven-development` — as execute-then-
review: a worker subagent does the task, an **independent** reviewer
subagent checks it, and the reviewer is not the agent that produced the
work.

`09-risk-tactics-gate` already *is* a review stage. Expressing it as the
review half of the native pattern rather than as a bespoke gate buys two
things beyond tidiness:

- **Independence becomes structural.** Today the same context that wrote
  the resume also gates it, and a claim that looked defensible while
  drafting tends to look defensible while checking. A reviewer subagent
  starting from the artifact and the STAR bank, without the drafting
  conversation, is a genuinely different reader — which is the entire
  point of a gate.
- **Iteration budgets stop being shared.** Each subagent gets its own
  budget, capped at `delegation.max_iterations` (default 50) against the
  parent's 500. A gate that runs inside the parent turn competes with the
  drafting work for the same budget on a twelve-application sweep.

Two numbers worth having here, since neither was written down:
`execute_code` iterations are **refunded** and do not consume budget, so
mechanical work — scoring, diffing, DB writes — is free where a
`delegate_task` round trip is not. Prefer `execute_code` for anything
deterministic and keep delegation for work that needs judgement.

What does not change: the reviewer proposes, it never submits. Rule 1's
approval boundary sits after this stage regardless of how the stage is
structured.

## Subagents must not write memory

Borrowed from OptMem's integration prompt, which states it plainly:
parallel sessions on one machine are all the same agent and may all write
memories, but **a subagent is not** — it cannot judge what is already
known, so its notes arrive duplicated and incorrectly.

This package delegates heavily: this sweep, the cold-prospecting research
fan-out, and the three-scope intel scrub all spawn workers. A
twelve-application sweep where each worker writes what it learned produces
twelve near-identical memories, and the duplicates are worse than useless
because contradiction detection then has to arbitrate between copies of
the same claim.

**Every subagent spawned by this package carries the instruction
explicitly**: it does not write to `memory/`, does not call `fact_store`
with `add`, and does not record journal entries. It returns findings to
the parent, and the parent — which has the full picture of what was
already known — decides what is worth keeping.

This holds regardless of which memory provider is configured. It is a
property of delegation, not of the backend.
