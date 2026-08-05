# Audit triage — `FINAL-AUDIT-merged-package.md` against `MERGED-22`

Every finding in that audit, sorted into four buckets. The verdicts below
come from grepping and reading the merged tree at the time of this pass,
not from recalling what was discussed — file and line references are given
so any of them can be re-checked directly.

One general observation before the tables. The audit is largely accurate
and its two highest-severity findings (C1 and C2) are both **completely
untouched** in the current package. The block it treats as the largest
piece of unfinished work — the A-series capability adoptions — is in fact
the block that has since been almost entirely completed. So the audit's
own priority ordering is now close to inverted, which is worth knowing
before working from it.

---

## Bucket A — superseded. Note and skip.

The finding rested on a premise that no longer holds. Nothing to do
except not act on it.

| # | Audit finding | Why it is superseded |
|---|---|---|
| §3.1 | "`qmd` appears zero times — the Phase 1 recommendation was never written in" | `qmd` now appears 81 times across the tree and has a dedicated `07-context-architect/references/qmd-retrieval-layer.md`, a config section in the README's optional components, and cron job 17 keeping the index fresh. The count the finding rests on is stale. |
| §3.3 | Three discovery paths into one queue; "deduplication across the three is asserted rather than specified" | Now fully specified. `01-job-discovery/SKILL.md:89-126` defines `posting_fingerprint` (`company \| normalised_role_title \| location`), explains why title normalisation lives in the skill rather than in SQL, and adds `posting_sources` (addendum 8) so a duplicate becomes attribution data instead of waste. It even addresses the exact failure the audit named — the URL differing across surfaces — and states the asymmetry rule ("a false *merge* is worse than a false duplicate"). |
| §5.5 | qmd's ranking has no time or importance term, so adopting it would not move the aging problem | Correct, and the package independently reached the same conclusion. qmd was scoped as a **read-only document search layer over three research cache directories**, with `fact_store`, `applications.db`, the taxonomy index and the STAR bank each explicitly excluded and each given a reason. The concern was pre-empted rather than ignored. |
| A4 | `qmd` as the local semantic-recall layer — "needs rethinking, not just implementing" | Implemented, and implemented *as the rethink the audit asked for* — scoped to document retrieval, explicitly not to memory. |
| A5 | Honcho for dialectic user modelling | Not merely unimplemented — **explicitly declined**, in `holographic-memory-layer.md:219-224`, on the correct grounds that `memory.provider` takes exactly one value and Honcho/Mem0/Hindsight are alternatives rather than companions. Re-raising it as an open gap would reverse a decision that was made deliberately. |

---

## Bucket B — already implemented. Skip.

| # | Audit finding | Where it landed |
|---|---|---|
| A8 | `ocr-and-documents` — "no PDF can enter this pipeline at all" | `02-jd-parser/SKILL.md:34-48` (PDF job specs) and `07-context-architect/SKILL.md:456-473` (PDF resume/portfolio intake, plus offer letters at stage 10). Text layer first, OCR as fallback, OCR flagged in output, and OCR'd *figures* re-confirmed before being written under Rule 5 — the "32% read as 3.2%" case the audit would have wanted covered. |
| A9 | `nano-pdf` — fix a typo without regenerating | `05-resume-customizer/SKILL.md:189-195`, with the right reason given (regeneration re-rolls wording Kene already approved). |
| A10 | `excel-author` — offer-comparison workbook | `10-approval-and-submit/SKILL.md:182-186`. Models equity under three assumptions and deliberately produces no single score. |
| A14 | `xurl` — the X stubs | `14-social-discovery-outreach/references/platform-capability-matrix.md:50`, named explicitly, with the scope boundary stated (available ≠ in scope for the quote/post stubs). |
| A15 | `youtube-content` — earnings calls, hiring-manager talks | `12-company-research/SKILL.md:144-150` and `13-interview-prep`'s intel scrub. Transcripts only, target-conditional rather than a default sweep. |
| A17 | `unbroker` — what a recruiter finds when they search you | `16-career-pulse/SKILL.md:225-231`, correctly framed as a standing quarterly item rather than a one-off, since brokers re-scrape. |
| A20 | `mcp-oauth-remote-gateway` — headless OAuth | `security/security-setup.md:217-222`, with the "set this up *before* the pipeline depends on a connector" ordering advice. |
| A22 | `one-three-one-rule` for offer decisions | `10-approval-and-submit` and `19-career-path-planner`'s S11 section. **And as of this pass it is now load-bearing rather than aspirational** — Step 3.5 generates three real paths to choose between, where previously there was one path and therefore no choice. |
| A2 | `subagent-driven-development`'s two-stage review | `00-orchestrator/references/parallel-pipeline-sweep.md:206-220`, with `09-risk-tactics-gate` cast as the review half so reviewer independence is structural. |
| C5 | Pick one semantic-memory provider, demote the rest | `holographic-memory-layer.md:219-233` states the choice plainly and says why the others are alternatives, not companions. README carries a "Considered and declined" block for `llm-wiki`, `telephony` and `instructor`. Chroma's remaining mentions are in `title-taxonomy.md` for the **vector index**, a different job, presented as a genuine either/or with a stated recommendation. |
| §3.5 | Recurrence detection | Closed in the audit's own text. `cron/cron-jobs.md:463-467` confirms it. |

---

## Bucket C — partially addressed. Reduced, not closed.

Worth reading the current implementation before acting, because the
remaining gap is narrower than the audit describes.

| # | What exists now | What is still genuinely missing |
|---|---|---|
| **C6** — failure semantics | A `discovered → building → staged → awaiting_approval` flow with the parent setting `building` at dispatch as a race guard; a Phase 1 reconcile-before-delegate pass on every tick; a stuck-batch warning at one sweep cycle plus margin (~7h); an explicit instruction not to mark a failed build as `staged`. | No `failed` status, no attempt counter, and no rule for what a rerun does with partial artifacts already on disk. The audit's "a half-built application sits in a state no stage picks up again" is now *visible* rather than silent — which is the important half — but it is still not *resolvable* by any defined mechanism. |
| **C4** — four research caches | qmd makes three of the four cross-searchable, and `qmd-retrieval-layer.md:28-38` diagnoses the addressing defects precisely: `interview_intel_cache`'s slug keying splits "Analytics Lead"/"Head of Analytics" into non-communicating caches, and `individual_research_cache`'s handle keying causes the same recruiter to be researched — and *paid for* — twice. | The addressing schemes themselves are unchanged, and nothing enforces the addendum's timing-based split between `12-company-research`'s sentiment work and `13-interview-prep`'s intel scrub. Both can still research the same thing on the same day. qmd made the caches *searchable*, not *coherent*. |
| **§5** — memory aging | `star-bank-aging.md` adds a real mechanism: OptMem-style tiered compression, recent stories verbatim, older ones collapsed, every story still represented, fixed token cost. | It covers **the STAR bank only** and disclaims the rest itself (`:83-92`): "Importance is not modelled... Urgency is not modelled." So §5.2, §5.3 and §5.4 stand as written, and §5.1 stands entirely — see C2 below. The audit's four distinctions remain three-and-a-half unaddressed. |
| **§4.4** — 57-char description collisions | Descriptions were fixed to fit the index (B1), and the orchestrator routes explicitly. | Now 23 skills competing in that namespace, and the audit's recommendation was to *test* direct invocation rather than assume. No such test exists. Low severity, still open. |

---

## Bucket D — open and relevant. This is the actual work list.

Ordered by what I would do first, which is not the audit's order.

### D1. C1 — concurrency model (high)

**Verified completely absent.** Grep across the whole tree returns zero
hits for `WAL`, `journal_mode`, `busy_timeout`, or any transaction
boundary. Meanwhile `parallel-pipeline-sweep.md` fans subagents out to
write concurrently to one SQLite file, and SQLite's default on a held
lock is to fail the write, not to wait.

The audit is right that this is the most serious gap and right that the
fix is small: `PRAGMA journal_mode=WAL`, a busy timeout, and a stated
rule that a subagent owns its `application_id` row and writes nothing
else. The third part is the one that needs writing into
`parallel-pipeline-sweep.md`'s task-composition section, since it is a
discipline rule rather than a pragma.

Worth noting the interaction with this pass's work: addendum 14 adds
tables a re-plan writes to, and the engine's §3 fan-out is one more
concurrent writer. This gap gets slightly worse, not better, with
Step 3.5 in place.

### D2. C2 — make `last_confirmed_at` load-bearing (high)

**Verified: still exactly four hits, all writes or null declarations,
zero reads** — `07-context-architect/SKILL.md:148` and `:225` write it,
`target-profile.yaml.template:76` and
`dynamic-target-calibration.yaml.template:124` declare it null.

The audit's own §5.6 point 1 is the right fix and is the cheapest
high-value change available anywhere in the package: when two facts about
the same entity conflict, the more recently confirmed wins by default and
the older is marked superseded rather than deleted. One rule, using a
field that already exists and is already being written.

Its §5.6 points 2–4 (`valid_until`, a durable/volatile flag, derived
rather than stored urgency) are a larger but coherent follow-on. The
argument for a *flag* over a continuous decay score is correct and worth
preserving — a decay score here would be false precision.

### D3. C7 / §2.4 — `interests-profile.md` has neither bar (medium)

**Both halves verified.** `20-interests-profile/SKILL.md:83-96` states
the no-evidence-bar carve-out explicitly and argues for it well. The file
format has an `Added: [date]` line and no reconfirmation field, no
supersession rule, and no aging mechanism of any kind.
`09-risk-tactics-gate/SKILL.md:37-46` does accept it as legitimate
evidence at `profile_stage: first_time`.

The audit's framing is exactly right: the gate's "the bar itself does not
move" does not resolve this, because the bar is being applied to a source
that never had one. Its proposed fix — a reconfirmation interval, since a
time bar is the only check a file with no evidence bar can have — is the
minimum. An interest recorded three years ago and abandoned two years ago
is currently indistinguishable from a live one, and it is now feeding a
verification gate.

Small addition worth making at the same time: this is also the one memory
file whose entries are most likely to *stop being true* quietly, which
makes it the natural first consumer of D2's machinery rather than a
separate mechanism.

### D4. §4.7 — no cost model (high in practice, unlisted in the audit's C-table)

**Verified absent.** `enrichment-tools-pricing.md` and
`free-tier-rotation.md` cover enrichment API spend only. There is no
budget, no per-job estimate and no circuit breaker for *model* spend
anywhere.

And the exposure has grown since the audit: it counted 16 cron jobs;
`cron/cron-jobs.md` now lists **18** (1–16 plus 8b and 8c), plus parallel
subagent fan-out, MoA advisor calls, a weekly GEPA-adjacent review, and —
new as of this pass — the stepping-stone engine's per-candidate research
fan-out, which is the single most token-hungry thing in the package when
it runs.

Two wake-gates exist and do real work, but they are per-job cost
*avoidance*, not a cost *model*. Nothing anywhere answers "what does a
month of this cost" or stops it.

### D5. §4.6 — nothing verifies the submit hook is live (high, cheap)

**Verified.** `security/hooks/verify-submit-approval.py` exists and is
registered via a manual `pre_tool_call` block in `config.yaml` at install
step 5. Nothing checks it is actually registered.

Rule 1 is the package's single most important safety boundary. If a user
skips step 5, mistypes the path, or misses the `hooks_auto_accept` note,
Rule 1 silently degrades from an enforced boundary to an instruction in a
markdown file. A startup self-check is a few lines and closes it. This
has the best severity-to-effort ratio of anything on this list.

### D6. C3 — `13-interview-prep` blueprint wording (medium, trivial)

**Verified, at `13-interview-prep/SKILL.md:382`** (line has drifted from
the audit's 333, wording unchanged): "ships enabled by default the same
way discovery/sweep/weekly-review do."

`cron/cron-jobs.md` is correct — it describes suggestions as consent-first
and notes dismissals latching by `dedup_key`. Only this line contradicts
it. The audit's point about *why* it matters is the real argument: a user
who believes four jobs are running will not check `/suggestions`, and
will conclude the pipeline is broken when nothing fires.

### D7. §4.5 — `shared/` is not part of any skill's install unit (medium)

**Verified.** `shared/pipeline-rules.md` is declared mandatory reading by
every skill and lives outside every skill directory, so
`hermes skills install` on one skill does not bring it. The package only
works installed whole and nothing in any frontmatter says so. README's
install step 2 does say "drop this whole folder in", but that is
instructions, not a declaration a partial installer would ever see.

### D8. A7 — the hostile-interviewer drill (medium)

**Verified open.** A2's two-stage review shipped; the drill did not.
`13-interview-prep` has Part 3 (a live study session over flashcards) and
Part 3b (questions with no story behind them), and no adversarial mode
anywhere — grep for hostile/grill/adversarial returns nothing in that
skill.

This is the one A-series item genuinely left behind, and it is the one
with the clearest user-facing value of the ones remaining: the gap
between "can recall the story" and "can hold the story up under pressure"
is exactly what a real interview tests.

### D9. §4.4 — test direct skill invocation (low)

Not a fix, a test. Invoke several similarly-described stages directly and
see whether the 57-character descriptions actually disambiguate. The
audit's own recommendation was to test rather than assume, and that is
still the right call.

---

## Conflicts §2.2 and §2.3 — correctly left open

Both are documented rather than fixed, and in both cases that is the
right outcome rather than an outstanding task.

**§2.2** (self-improvement requires curator adoption; adoption exposes
the package) cannot be fixed from inside the package. The audit's own
recommended posture — stay unadopted, improve through `write_approval` —
is what README carries. The one thing worth acting on is the audit's
smaller point: "self-improving" and "consented weekly proposal loop" are
used interchangeably across several files and are not the same thing.
That is a wording pass, not a design change.

**§2.3** (`contradict` is advertised as what it demonstrably is not) is
handled about as well as it can be. `holographic-memory-layer.md` §3 is
candid that direct testing found the tool misses the exact case it was
adopted for, and Phase 4's probe-and-read is the actual defence. The
audit's residual objection — that the package's contradiction detection
is therefore a human reading two facts side by side — is true and is not
obviously a defect. A human reading two facts side by side is a
reasonable primary mechanism when the automated option has been tested
and found not to work.

---

## Summary count

| Bucket | Count | Items |
|---|---|---|
| Superseded — skip | 5 | §3.1, §3.3, §5.5, A4, A5 |
| Already implemented — skip | 11 | A8, A9, A10, A14, A15, A17, A20, A22, A2, C5, §3.5 |
| Partially addressed | 4 | C6, C4, §5 (aging), §4.4 |
| Open and relevant | 9 | C1, C2, C7/§2.4, §4.7, §4.6, C3, §4.5, A7, §4.4-test |
| Open by design, correctly | 2 | §2.2, §2.3 |

The audit's own headline — "everything B1–B21 is implemented; §1.1 is the
largest block of unfinished work" — was true when written and is not true
now. §1.1 is 10-of-11 done. The unfinished work is C1, C2 and the
unlisted §4.7, all three of which are infrastructure rather than
features, which is probably why they kept losing to capability adoptions.
