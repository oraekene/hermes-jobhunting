# Hermes-capability upgrade changelog — Phase 1 + Phase 2

Source: a full audit of `job_hunting_skill` against Hermes's actual
mechanisms (self-improvement loop, memory, cron, hooks, delegation, the
full bundled + optional skills catalog — cloned and read from
`NousResearch/hermes-agent`, `hermes-agent-self-evolution`, and
`autonovel` directly, plus the complete Hermes docs site). The full
gap-analysis this came from covers a lot more than what's implemented
here — this file only tracks what actually shipped.

Phases 3–4 from that analysis (Holographic memory provider, GEPA-based
evolutionary self-improvement, MoA cross-checking on the risk gate,
`delegate_task` parallelization of the pipeline sweep, building out
`13-interview-prep`, `research/domain-intel` anti-scam checks) were
implemented one at a time, deliberately, as their own follow-up passes.
Item 13 was the last one on the original roadmap.

## Post-roadmap — skill-coverage cross-check (found real gaps, fixed them)

After finishing all 13 roadmap items, a direct cross-check against the
original gap-analysis's own §1.9 skills-catalog table (every bundled/
optional skill judged to have a genuine fit) found that **7 of the 13
listed skills had been discussed in reasoning during earlier phases and
never actually written into any file** — a real process gap, not a
documentation nitpick. Specifically: `research/blogwatcher`, `devops/
watchers`, `research/duckduckgo-search`, `research/searxng-search`, and
`research/parallel-cli` were named as recommendations for
`01-job-discovery`/`12-company-research` during Phase 1/2 and Phase
4-item-10 work but silently dropped when that work got scoped down to
just the wake-gate script; `security/1password` was consciously
deferred once ("not in the numbered phase list") and never revisited;
`software-development/hermes-agent-skill-authoring` and `email/
agentmail` (the latter needing to be documented as *ruled out*, not
adopted) were never written into the package at all.
`research/scrapling` was half-done — present in `cron/cron-jobs.md`
but missing from `02-jd-parser` and `12-company-research`, where it had
also been identified as relevant.

**Fixed, all in their originally-identified locations**:

- `01-job-discovery/SKILL.md` — `research/blogwatcher` as the
  underlying mechanism for reading `rss` sources; `devops/watchers` as
  the underlying watermark-dedup mechanism for `rss`/`aggregator_api`
  sources in the dedupe step; `research/scrapling` for `open_web`
  mode's anti-bot-protected pages; `research/duckduckgo-search`/
  `research/searxng-search` as free keyless fallbacks for the same
  mode.
- `02-jd-parser/SKILL.md` — `research/scrapling` as a retry step before
  falling back to asking Kene to paste JD text manually.
- `12-company-research/SKILL.md` — `research/scrapling` for JS-heavy
  About/Values pages; `research/parallel-cli` as a premium research
  option.
- `security/email-integration-setup.md` — `security/1password` as an
  upgrade path for the `passwd.cmd` credential step; `email/agentmail`
  documented explicitly as the wrong shape for this pipeline (its own
  inbox, not read access to Kene's existing one) rather than left
  unaddressed.
- `README.md` — new "Editing these skill files" section pointing at
  `software-development/hermes-agent-skill-authoring` as the house
  style this package's own `SKILL.md` files follow, including for
  future `skill_manage`-driven self-edits from either self-improvement
  tier.

## Phase 4, item 13 — parallel pipeline sweep via `delegate_task` (optional, off by default)

The item that came with the most genuine, irreducible mechanical
uncertainty of the whole project — worth documenting precisely rather
than picking an answer and hoping.

**What's actually uncertain, and why it couldn't be resolved further**:
`delegation.md` describes top-level `delegate_task` calls as running
"in the background automatically... so the conversation can continue,"
with the result posted back "as a new message" — language clearly
written around an interactive session where a human is present to see
that new message arrive. Whether a **cron-triggered** top-level agent
turn — no live human "continuing the conversation" — gets a
`delegate_task(tasks=[...])` batch's result within that same triggered
turn, or whether it genuinely requires a continuable session
(`cron.mirror_delivery`/`attach_to_session`) to receive a later message,
isn't addressed by any doc section I could find, including `cron.md`'s
one and only cross-reference to delegation (a toolset-cost mention with
no timing detail). No live Hermes gateway was available to dispatch an
actual batch and observe. Two other things WERE confirmed directly,
though, and shaped the design regardless of how the timing question
resolves: leaf subagents cannot call `send_message` (so stage 10's
Telegram ping structurally cannot happen inside a delegated child, confirmed
in `delegation.md`'s "Key Properties" list), and subagents get zero
automatic context — no conversation history, no memory injection, "a
focused system prompt built from your goal and context" only.

**The design is built to be correct under either answer to the open
question, not to bet on one**:

- A new `status` value, `building`, joins the existing `staged` (which
  the schema had anticipated in its own comment but no skill had ever
  actually written to) — set by the **parent**, immediately at
  dispatch, before a delegated child does any work. This closes a real
  race condition: without it, a later sweep tick's `WHERE
  status='discovered'` query could re-delegate a posting whose first
  batch is still in flight or stuck.
- `09-risk-tactics-gate` now writes `status='staged'` once every tactic
  check has run (whatever the outcome) — a child can do this since
  writing to `applications.db` isn't one of the blocked tools, even
  though it can't call `memory` or `send_message`. This is wired in
  generally, not gated behind parallel mode — it's the correct
  checkpoint in the default serial flow too.
- `10-approval-and-submit` now writes `status='awaiting_approval'`
  explicitly once the Telegram message has actually sent — distinct
  from `staged`, and fixed several places where "stop at
  'awaiting_approval'" language had crept in as if stage 9 set that
  status directly (it doesn't; only an actual sent ping does).
- **Every sweep tick reconciles before delegating anything new**: pings
  Kene for anything already at `staged`, and flags anything stuck at
  `building`/`staged` for longer than one full sweep cycle (~7 hours,
  generous margin over the ~3.5-hour default cadence) as a stuck-batch
  warning. This is the actual safety net — whichever way the timing
  question resolves, a genuinely dropped or crashed result cannot
  silently vanish past this check for more than one extra tick, and the
  rollout guidance explicitly recommends starting at a small batch size
  and watching for this warning as an empirical answer to the open
  question.

**What shipped**:

- **New**: `00-orchestrator/references/parallel-pipeline-sweep.md` — the
  full design, the honesty section on the timing question, the exact
  `delegate_task` call shape (including composing self-contained
  `context` since subagents get no automatic memory/skill-discovery),
  the two-phase (reconcile, then delegate) sweep prompt, and rollout
  guidance.
- **`shared/applications_db_schema.sql`** — `status` column comment
  formalizes the full `discovered -> building -> staged ->
  awaiting_approval -> ...` flow. No migration needed (existing
  installs already have a free-text `status` column; new values need no
  `ALTER TABLE`, unlike the earlier `last_interview_prep_at` column
  addition).
- **`09-risk-tactics-gate/SKILL.md`**, **`10-approval-and-submit/
  SKILL.md`** — the `staged`/`awaiting_approval` checkpoints wired in
  precisely, and stale terminology fixed everywhere it had drifted
  (the blueprint prompt in `00-orchestrator/SKILL.md`, `cron/
  cron-jobs.md` job #3's command).
- **`00-orchestrator/SKILL.md`** — step 4 of "Running a full cycle"
  points at the optional mode; status-query reporting now includes
  `building`.
- **`cron/cron-jobs.md`** — job #3 now documents both the default
  serial command and the opt-in parallel variant side by side.
- **`README.md`** — folder layout and "Recent additions" updated to
  match.

## Phase 4, item 12 — MoA cross-check for borderline title-matches (human-initiated)

The original recommendation assumed `09-risk-tactics-gate` could
automatically reach for a Mixture-of-Agents second opinion on a
borderline title-match. Verifying the actual mechanics — not just the
feature's own docs — ruled that out on two independent grounds, each
confirmed by reading real source rather than assumed:

1. **`/moa <prompt>` is parsed only from human-typed chat input.** Read
   `hermes-agent/cli.py`'s slash-command dispatch directly
   (`_looks_like_slash_command`, `_should_handle_model_command_inline`,
   and the surrounding UI-thread input handling) — there's no path by
   which an agent's own generated text gets re-interpreted as a slash
   command. A skill's instructions cannot have the model "type" `/moa`
   and have it take effect.
2. **`delegate_task`'s model override is global, not per-call.**
   `delegation.model`/`delegation.provider` in `config.yaml` applies to
   every subagent spawned by anything — there's no parameter on the
   `delegate_task` tool call itself to route just one specific child
   through a different model. Setting it globally to a MoA preset would
   silently apply MoA's extra reference-model cost to any other
   delegated work in this pipeline (relevant given `delegate_task`
   parallelism for the pipeline sweep is a separate, possible future
   item — this would have created a real, silent cost-multiplication
   conflict between the two features).

**What shipped instead, once the constraint was clear**: title-match
calls get a new distinction — `[BORDERLINE PASS]` (equivalence rests on
inference, not an explicit memory statement) versus a plain `[PASS]`
(memory already states something close to the target title outright).
`10-approval-and-submit`'s Telegram message includes a ready-to-paste
`/moa <question>` prompt directly next to any `[BORDERLINE PASS]` flag —
MoA stays exactly what it mechanically is, a human choosing a model for
one hard question, not something this pipeline pretends to automate
around a mechanism that doesn't support that shape of automation. Never
fires during unattended cron runs (there's no one there to act on it) —
a flag from a cron-driven sweep just surfaces the same way at the next
live approval message, same as any other change-log entry.

- **New**: `09-risk-tactics-gate/references/moa-cross-check.md` — the
  full mechanical reasoning above, the exact recommended MoA preset
  config (tuned for a short PASS/FAIL judgment specifically —
  `reference_max_tokens: 400`, `reasoning_effort: high` on all three
  slots — not the profile's general-purpose default preset), and what
  this deliberately does not do.
- **`09-risk-tactics-gate/SKILL.md`** — the CV title-matching check and
  the Output section's worked example both updated with the new
  `[BORDERLINE PASS]` classification.
- **`10-approval-and-submit/SKILL.md`** — step 4 now includes the
  ready-to-paste MoA prompt alongside a flagged entry, not just the tag.
- **`README.md`** — folder layout and "Recent additions" updated to
  match.

## Phase 4, item 11 — GEPA-based Tier 2 self-improvement (optional, manual)

The deepest item so far, and the one where reading the actual source
mattered most — `PLAN.md`/`README.md` describe a considerably more
automated, more rigorously-scored system than what's actually wired up
in `evolve_skill.py`. Three specific gaps found by reading
`evolution/core/fitness.py`, `constraints.py`, and `evolve_skill.py`
directly:

1. The metric actually passed to `dspy.GEPA(metric=...)` is a
   keyword-overlap heuristic (`skill_fitness_metric`) — not the
   three-dimension "LLM-as-judge" scoring `PLAN.md` describes. The more
   sophisticated `LLMJudge` class is imported in `evolve_skill.py` and
   **never called**.
2. `ConstraintValidator.validate_all()` runs exactly four mechanical
   checks (size, growth %, non-empty, frontmatter structure) and
   **nothing about content** — no check would catch an evolved skill
   becoming more permissive. `run_test_suite()` exists as a method but
   is never invoked from the actual `evolve()` flow either, despite a
   `--run-tests` CLI flag that threads a value into config nothing
   downstream reads.
3. There's no auto-generated PR — `pr_builder.py` is in `PLAN.md`'s file
   tree but never imported; the real output is
   `output/<skill>/<timestamp>/{baseline,evolved}_skill.md` +
   `metrics.json`, and a human has to read the diff themselves.

**Decisions made because of these findings, not despite them**:

- **Scope narrowed to `05-resume-customizer`, `06-cover-letter`,
  `08-application-qa` only** — `09-risk-tactics-gate` is explicitly
  excluded. The missing content-safety net makes the pipeline's one
  integrity-critical gate the wrong place to point an evolutionary
  optimizer that (as shipped) cannot tell a legitimate improvement from
  a quietly-loosened evidence requirement.
- **A mandatory safety-anchor constraint patch** — exact code given for
  a new `_check_safety_anchors` method plus the one-line wiring into
  `validate_all()` — checks that mentions of `09-risk-tactics-gate` and
  the `invent`/`fabricat` word stems don't *decrease* in frequency
  between baseline and evolved text. A frequency floor, not a perfect
  guarantee, but it turns "zero content checks" into "one specific,
  known, checkable floor" — framed as non-negotiable before running this
  on any of the three in-scope skills, not an optional hardening step.
- **New**: `11-analytics-and-learning/scripts/build_gepa_golden_set.py`
  — builds the evaluation dataset from real `applications.db` outcomes
  (`response_type IN ('interview_request', 'screen_request')`) rather
  than synthetic guesses, reading only structured columns already in the
  schema (never a raw JD/resume text, since neither is persisted there —
  deliberately not started here either). Refuses to write a dataset
  under 12 qualifying applications. Tested: the too-few-samples refusal
  path, the success path against synthetic data, and a full round-trip
  through the real `EvalExample`/`GoldenDatasetLoader` schema (verified
  directly, working around this sandbox not having `dspy` installed by
  testing the dataclass logic in isolation).
- **New**: `11-analytics-and-learning/references/gepa-self-evolution.md`
  — the full setup, including the path workaround `find_skill()`
  requires (it only searches under `{path}/skills/`, which this
  package's flat `NN-stage-name/` layout doesn't match — solved with a
  small symlink workspace, documented exactly), and the manual,
  `skill_manage`-gated deployment step. No cron job or blueprint exists
  for this anywhere — deliberately manual, quarterly-or-on-demand only.
- **`11-analytics-and-learning/SKILL.md`** — the weekly review section
  now opens by naming itself "Tier 1" and pointing at Tier 2 by
  reference, so neither section reads as if the other doesn't exist.
- **`README.md`** — "Recent additions" and the folder layout diagram
  updated to match.

## Phase 4, item 10 — domain-intel anti-scam signal in `12-company-research`

Read the actual `optional-skills/research/domain-intel/scripts/
domain_intel.py` source from `hermes-agent` before writing this — not
just its catalog description — specifically to get the exact JSON field
names right (`whois`'s `creation_date` vs. `expiration_days_remaining` —
the script only computes days remaining until *expiry*, never age since
creation, so that calculation has to happen in the skill's own
instructions) and to confirm `available` (checks whether a domain is
free to register) is the wrong command for this use case — `whois` +
`ssl` are the relevant ones. Live-testing the actual network calls
wasn't possible in this sandbox (WHOIS's TCP:43 and the DoH endpoints
aren't in the environment's allowed egress list — confirmed by trying,
not assumed), so this one leans on precise source-reading rather than a
live-run confirmation the way the Holographic and wake-gate work did.

**What shipped**:

- **`12-company-research/SKILL.md`** — step 2 now explicitly records the
  company's own primary domain (nothing upstream captured this as
  structured data before). New step 2.5: run `whois`, compute age from
  `creation_date` (falling back to `ssl`'s `not_before` — flagged
  explicitly as a weaker proxy — only if WHOIS fails or is blocked), and
  **cross-check the age against the stage/size signal already gathered
  in step 2** before writing anything, rather than flagging domain age
  in isolation. A new domain is unremarkable for a company step 2
  already identified as early-stage; the same finding paired with a
  claimed established/enterprise employer is the combination actually
  worth a note. Entirely optional — skipped silently if
  `research/domain-intel` isn't installed, never an apology for a
  capability that was never claimed.
- Cache file template — new "Domain signal" section, omitted entirely
  (not left empty) when the skill isn't installed.
- **`10-approval-and-submit`** — step 4 now leads the Telegram approval
  message with the domain-signal note when (and only when) it's flagged
  as notable. Deliberately not shown on every application — a signal
  attached to everything trains a person to stop reading it.
- Fixed a stale claim while in this file: "What this skill does not do"
  used to say no interview-prep stage existed yet to use interviewer
  research — no longer true since Phase 3. Updated to correctly point at
  `13-interview-prep`'s own, narrower interviewer-research capability
  instead.
- **`README.md`** — folder layout and "Recent additions" updated to
  match.

## Phase 4, item 9 — Holographic memory layer for the STAR bank (optional)

The first Phase 4 item. Unlike Phases 1–3, this one changed shape
partway through building it, because I tested the actual mechanism
instead of trusting its own description.

**What happened**: the original gap-analysis recommended Holographic
specifically for its `contradict` action — "automated detection of
conflicting facts," proposed as a direct fix for `07-context-architect`'s
own named problem ("if two entries in the STAR bank seem to describe
the same project differently"). Before writing that into the skill, I
cloned `plugins/memory/holographic` from `hermes-agent`, stubbed its one
internal dependency (`hermes_state.apply_wal_with_fallback`) enough to
run `store.py`/`retrieval.py` standalone, and fed it two facts about the
same project with a conflicting duration (near-identical phrasing, "3
months" vs. "actually took 6 months"). **`contradict` found nothing**,
at the default threshold and at one three times lower. The mechanism is
`entity_overlap × (1 − content_similarity)` — built to catch two facts
about the same entity that read as *entirely different characterizations*
(which it did catch, in a follow-up test: "is a mid-size logistics
company" vs. "went through layoffs, now a struggling startup" — same
company), not a single specific detail changed inside otherwise similar
phrasing, which is the more common real risk for a STAR bank. Also found:
`contradict` returns an empty list (not an error) without NumPy
installed — the one action here that doesn't degrade gracefully the way
`probe`/`related`/`reason` do — and a genuine entity-extraction bug
(sentence-initial capitalization merges into the following entity name,
so the same project name can resolve to two different entity strings
depending on where it sits in a sentence; quoting the name in the fact
text avoids it, verified).

**What shipped, adjusted accordingly**:

- **New**: `07-context-architect/references/holographic-memory-layer.md`
  — full write-up: setup, the fixed `user_pref|project|tool|general`
  category enum, the entity-extraction quirk and its fix, the
  `contradict` limitation with the actual test numbers, and the
  workflow that doesn't depend on `contradict` being reliable: probe for
  existing facts about the project/company, **have the model read them
  directly and compare**, then run `contradict` as a cheap supplementary
  pass afterward — not the primary check.
- **`07-context-architect/SKILL.md`** — "Where things live" and the
  Reference files list point to the new file; Phase 4 (Synthesis) now
  runs the probe-and-read check before writing a confirmed story,
  decomposes it into 2–4 atomic facts afterward, and runs `contradict`
  as the secondary pass. Off by default, config-gated, never a
  replacement for `star-story-bank.md` itself.
- **Light, non-blocking mentions** added to `05-resume-customizer` (a
  quick number cross-check at the Quantification phase),
  `06-cover-letter` (a supplementary `probe` when picking Paragraph 3's
  story), `08-application-qa` (a supplementary `reason` across
  company + topic), `13-interview-prep` (an extra flashcard from a
  surfaced atomic fact), and `11-analytics-and-learning` (an optional,
  low-priority `fact_feedback` trust-scoring tie-in to the weekly
  review). None of these block or restructure the skill they're in —
  every one degrades to "proceed exactly as before" if the layer isn't
  configured or turns up nothing.
- **`README.md`** — "Recent additions," section 2's memory map, and the
  folder layout diagram updated to match.

## Phase 3 — `13-interview-prep` built out (was a stub)

The sole Phase 3 item from the original gap-analysis roadmap: the
highest-value net-new stage, using inputs that were already accumulating
unused (`12-company-research`'s cache, `email_insights` rows, the
question-bank's confirmed answers).

- **New**: `13-interview-prep/scripts/interview-prep-wake-gate.py` — a
  cron `wakeAgent` gate that's pure DB query (no network fetch), so
  unlike the discovery gate its skip decisions are strictly reliable,
  not best-effort. Tested against four scenarios: nothing to do, a fresh
  never-prepped interview request, an already-prepped application with
  no new signal, and a later round's `interview_detail` email arriving
  after the last build (this last case is what makes the trigger
  multi-round-aware rather than one-shot).
- **`13-interview-prep/SKILL.md`** — full rewrite. Structured around a
  hard split: **Build** (Parts 1–2, assembling the brief and the
  `productivity/memento-flashcards` deck — unattended-safe) vs. **Study**
  (Part 3, the actual practice session — inherently live, since
  memento's own review flow needs Kene's real free-text answer before it
  can grade and move to the next card; this skill does not reimplement
  or shortcut that flow). Adds a new, deliberately scoped capability:
  interviewer research, limited to public professional-context
  information only, same never-fabricate/state-confidence discipline as
  `12-company-research`, cached separately
  (`{company_slug}__interviewers.md`) so it never collides with the
  company-level cache.
- **`shared/applications_db_schema.sql`** — new
  `applications.last_interview_prep_at` column, with an explicit
  migration note (`ALTER TABLE ... ADD COLUMN`) since — unlike the
  Phase 1 `open_gaps` table, which was brand new — this is a column
  added to a table that already exists on any running install.
- **`00-orchestrator`** — stage 10 now routes here instead of saying
  "stub only, not routed."
- **`cron/cron-jobs.md`** — new job #9 (interview-prep sweep, twice
  daily), added as a fourth blueprint alongside discovery/sweep/weekly-
  review.
- **`README.md`** — top framing, folder layout, section 4, the install
  steps, and the memory-map section all updated to match.

## Phase 1 + Phase 2

Source: a full audit of `job_hunting_skill` against Hermes's actual
mechanisms (self-improvement loop, memory, cron, hooks, delegation, the
full bundled + optional skills catalog — cloned and read from
`NousResearch/hermes-agent`, `hermes-agent-self-evolution`, and
`autonovel` directly, plus the complete Hermes docs site). The full
gap-analysis this came from covers a lot more than what's implemented
here — this file only tracks what actually shipped.

Phases 3–4 from that analysis (Holographic memory provider, GEPA-based
evolutionary self-improvement, MoA cross-checking on the risk gate,
`delegate_task` parallelization of the pipeline sweep, building out
`13-interview-prep`, `research/domain-intel` anti-scam checks) are **not**
in this pass — each is a real design decision, not a pure improvement
with no tradeoff, so they're documented but not built.

## 1. Fixed: `09-risk-tactics-gate` writing directly to `MEMORY.md`

**Real bug, not a style nit.** Two independent problems with the old
behavior: it violated `shared/pipeline-rules.md` Rule 5 (only
`07-context-architect` writes memory, and only after Kene confirms a
fact — this was an unattended cron write from a different skill), and it
risked hitting `MEMORY.md`'s hard ~2,200-character cap during an
unattended pipeline sweep, with no one there to consolidate when the
write failed.

- `shared/applications_db_schema.sql` — new `open_gaps` table.
- `09-risk-tactics-gate/SKILL.md` — "Fail handling" now inserts a row
  into `open_gaps` instead of appending to `MEMORY.md`.
- `07-context-architect/SKILL.md` — "Where things live" and "When to
  re-run" now point at `open_gaps WHERE resolved = 0` instead of
  `MEMORY.md`'s old "Open gaps" section; marks rows `resolved = 1` once
  Kene supplies the missing evidence.
- `shared/pipeline-rules.md` — Rule 5 reworded so it no longer
  contradicts what the skills actually do.
- `templates/MEMORY.md` — the old "Open gaps" section replaced
  with a pointer to the DB table.
- `11-analytics-and-learning/references/metrics-schema.md` — the "Open
  gaps in memory" metric now queries `open_gaps` and correctly credits
  `09-risk-tactics-gate` as the flagger (`07-context-architect` resolves,
  it doesn't flag).

## 2. Fixed: approval screenshot delivery

`10-approval-and-submit`'s filled-form screenshot now carries the
`[[as_document]]` directive so Telegram doesn't lossy-recompress it to
~200 KB / 1280px right when legibility matters most (Hermes's Deliverable
Mode: absolute path + directive = file attachment, not an inline image
bubble). No change needed for the `.docx` resume — documents already
bypass the lossy image path.

## 3. Added: `wakeAgent` cost-control gate for discovery

`01-job-discovery`'s cron job pays for a full LLM turn every tick — up to
6x/day — regardless of whether anything new exists. New pre-run script
cheap-checks the sources it can (`rss`, `email_label`) and tells Hermes's
cron system to skip the agent turn entirely (zero token cost) when
nothing changed. Fails *open* (wakes the agent) on anything it can't
verify — a missed cheap-check costs one delayed tick, not a suppressed
posting.

- New: `01-job-discovery/scripts/discovery-wake-gate.py`.
- `01-job-discovery/SKILL.md` — new "Cost control: the wake-gate script"
  section.
- `cron/cron-jobs.md` job #1 — wired in via `--script`.
- Tested against: missing config, unreachable feed, a genuine new item,
  and the same feed confirmed unchanged on a second run. See the
  script's own docstring for exactly which source types it does and
  doesn't cover.

## 4. Added: `pre_tool_call` submit-gate hook (third enforcement layer on Rule 1)

The existing two layers (this skill's own approval-message step, and
Hermes's generic dangerous-command approval list) both stay. This adds a
third, purpose-built layer: a shell hook that vetoes a submit-shaped
browser click outright unless the applications DB shows
`approval_decision = 'approve'` for the exact application
`10-approval-and-submit` says it's working on. Fails *closed* — the
opposite direction from item 3, deliberately, because the cost of a
false negative here (an unreviewed application going out) is much higher
than the cost of a false positive (a re-click after checking why).

- New: `security/hooks/verify-submit-approval.py`.
- `10-approval-and-submit/SKILL.md` — writes
  `shared/.active_application/<session_id>.json` before opening a form
  (step 2); "Why this is a technical boundary" now describes all three
  layers.
- `security/security-setup.md` — new section 3 with the exact
  `config.yaml` hook entry, the consent-model mechanics
  (`shell-hooks-allowlist.json`, the three non-interactive escape
  hatches), and the "a crashed hook is not the same as a blocked one"
  caveat. Old section 3 (Container isolation) renumbered to 4.
- Tested against: a non-watched tool, a watched tool with no submit
  keyword, a submit-shaped click with no marker file, and a submit-shaped
  click with a valid marker + approved DB row.

## 5. Added: `creative/humanizer` in the persuasive-writing stages

Hermes's bundled humanizer skill is now an explicit pass in
`05-resume-customizer` (Phase 7), `06-cover-letter`, and
`08-application-qa` — phrasing only, same boundary in all three: if a
suggested change would alter what a sentence actually *claims*, it
doesn't get applied; that's `09-risk-tactics-gate`'s job.

- New: `06-cover-letter/references/anti-slop-checklist.md` — a
  job-application-specific companion list (banned openers/closers,
  self-description words used in place of a concrete example),
  structurally inspired by `autonovel`'s `ANTI-SLOP.md` pattern but
  original content for this domain. Referenced by both `06` and `08`.

## 6. Added: blueprints for the three highest-traffic cron jobs

Discovery scan, pipeline sweep, and the weekly self-improvement review
now ship as Hermes **blueprints** (`metadata.hermes.blueprint` in each
skill's own frontmatter) — one-tap `/suggestions accept` instead of
hand-typed `hermes cron create` commands. Directly relevant to the
resale idea in `README.md`.

- `01-job-discovery/SKILL.md`, `00-orchestrator/SKILL.md`,
  `11-analytics-and-learning/SKILL.md` — blueprint frontmatter added;
  YAML validated to parse correctly.
- `cron/cron-jobs.md` — rewritten around this: "Install path has
  changed" section up top, each of the three blueprinted jobs marked as
  such, the remaining five documented honestly as staying manual (mainly
  because a skill can only carry one blueprint, and several jobs share a
  skill that's already carrying a different schedule).
- `README.md` — install steps, folder layout diagram, and the capability
  map (sections 4 and 5) updated to match. Also fixed a pre-existing
  numbering error in the old section 4 (it said "five jobs" and
  mislabeled them — there are actually eight).

## 7. Documented: `enabled_toolsets` and `context_from`

Recommended, not force-applied — `cron/cron-jobs.md` explains where each
would help (toolset scoping on the high-frequency discovery job;
`context_from` chaining discovery → sweep) and is explicit about which
parts of this I could confirm as documented CLI flags versus which I
could only confirm via the `cronjob(...)` tool-call form, rather than
inventing flag syntax I hadn't verified.

## Honesty notes carried into the docs themselves

A few things worth knowing before you rely on any of this, all called
out at the point of use rather than buried here:

- The `--script` CLI flag is confirmed for `--no-agent` jobs; I did not
  find a documented example combining it with `--skill` the way job #1's
  command does. A `cronjob(...)` tool-call fallback is given alongside it.
- `enabled_toolsets`/`context_from` are confirmed via the `cronjob(...)`
  tool-call form, not confirmed as dedicated CLI flags.
- The submit-gate hook's tool-name/keyword matching is a heuristic, not
  semantic page understanding — tune `WATCHED_TOOLS`/`SUBMIT_KEYWORDS`
  against your actual ATS platforms if you see false positives/negatives.
- A crashed or timed-out hook is **not** the same as a hook that blocked
  — Hermes logs a warning and continues the agent loop either way. Test
  the hook standalone before trusting it in production.
