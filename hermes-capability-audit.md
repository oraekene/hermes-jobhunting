# Hermes Agent Capability Audit — what else could help, across the whole tool

Kene asked me to actually go read Hermes's own documentation rather than
work from what this pipeline had already touched on in passing (mostly
subagents, cron, and voice, each mentioned once for a specific feature).
This is that pass, done properly, mapped against every stage of the
tool — including an honest account of where a capability *doesn't*
clearly help, since a list where everything benefits from everything
isn't a useful list.

## The capabilities, briefly, before mapping them

- **Subagent delegation (`delegate_task`)** — spawns isolated child
  agents for parallel work. Inherits the parent's toolset (can't grant
  itself more access than the parent has), defaults to 3 concurrent
  (configurable, no hard ceiling), and comes in two roles: leaf
  subagents (default — can't delegate further, can't call `memory` or
  `clarify`) and orchestrator subagents (`role="orchestrator"`, can
  delegate again, up to `max_spawn_depth`). Can be routed to a cheaper/
  faster model for cost control on high-volume batch work. **Hermes's
  own guidance, worth repeating because it's exactly right**: use
  `delegate_task` for subtasks needing reasoning/judgment, and
  `execute_code` for mechanical, scripted, deterministic work — the two
  aren't interchangeable, and reaching for delegation on something
  that's really just a calculation wastes a whole child-agent turn on
  work a script would do faster and identically every time.
- **`execute_code`** — programmatic, deterministic tool calling. The
  right tool for math, structured extraction, and anything with one
  correct answer that doesn't need judgment.
- **Scheduled tasks (cron)** — natural-language or cron-expression
  scheduling, can attach specific skills, deliver results to any
  connected platform, supports pause/resume/edit. Already used
  extensively in this pipeline (`cron/cron-jobs.md` plus this package's
  jobs 9-12).
- **Checkpoints** — automatic snapshot of the working directory before
  file changes, `/rollback` to undo. Not currently referenced anywhere
  in this pipeline's design.
- **Memory** — two curated files (`MEMORY.md` ~2,200 chars,
  `USER.md` ~1,375 chars, injected every session) plus FTS5 full-text
  search over the complete session archive (`session_search` — fast,
  keyword-based, returns actual past messages, not summaries). A
  background self-improvement pass after a turn "may quietly save a
  memory or update a skill" — this is the native mechanism underneath
  what this pipeline calls `skill_self_edits`; it wasn't invented for
  this tool, it's Hermes's own architecture being pointed at job-hunting
  specifically. One optional external memory provider (Mem0, Honcho,
  and others) can layer semantic (not just keyword) retrieval on top,
  one at a time.
- **Voice** — STT (local Whisper, free, or cloud providers) and TTS
  across CLI, Telegram/Discord/WhatsApp/Slack/Signal voice notes
  (auto-transcribed), and live Discord voice channels. Already
  documented in depth in `07-context-architect/references/
  voice-interview-mode.md` and now reused by `16-career-pulse`.
- **Browser/form automation** — already the mechanism behind
  `10-approval-and-submit`'s form-fill.
- **MCP connectors** — Nous's approved catalog plus third-party (Postiz/
  PostFast for content scheduling, Composio for broader API wrappers,
  generic connectors for Google Drive/Gmail/etc.).
- **Multi-platform gateway** — Telegram, Discord, WhatsApp, Slack,
  Signal. This pipeline currently only uses Telegram; the others exist
  if ever wanted, not a recommendation to add them now.

## Stage-by-stage map

| Stage | Capability | Why it actually helps here |
|---|---|---|
| `01-job-discovery` | Subagent delegation | Scanning N sources (boards, APIs, `social_listening` platforms) is currently implied sequential. One subagent per source, run concurrently, cuts wall-clock time on a full discovery pass with no change to what gets found. |
| `02-jd-parser` | `execute_code` | Structured field extraction from a JD is closer to parsing than judgment once the JD text is in hand — worth checking whether the mechanical parts (pulling out salary figures, location, req IDs) are being done as full LLM reasoning turns when a scripted extraction would be faster and more consistent. |
| `03-resume-match` | `execute_code` | The scoring *math* itself (and, per this audit, the new `title_delta`/`comp_delta` overqualification calculations) is deterministic arithmetic once the inputs are known — a natural `execute_code` job, not a reasoning job, and more auditable as a script than as an LLM doing mental math. |
| `07-context-architect` Phase 1.5 | `execute_code` | Embedding-similarity search over ~50k title records is vector math — the LLM's job is deciding what to do with the ranked results (which to propose, how to explain them to Kene), not computing cosine similarity itself. |
| `09-risk-tactics-gate` | Subagent delegation | On a batch-application day, the fidelity check for each application is an independent, narrowly-scoped task — parallelizable the same way `12-company-research` targets are, rather than gating applications one at a time. |
| `10-approval-and-submit` | Checkpoints | Currently unused anywhere in this pipeline. Worth adopting deliberately: if a form-fill run corrupts a generated resume file or partially writes something mid-submission, `/rollback` is a real, already-built safety net rather than something this pipeline would need to invent. |
| `11-analytics-and-learning` | Native self-improvement + `execute_code` | The `skill_self_edits` pattern this pipeline leans on repeatedly (calibration recalibration, pitch-catalog tuning, query tuning) isn't a pattern invented for job-hunting — it's Hermes's own background self-improvement mechanism, pointed at this domain. The actual correlation math behind it (tactic-vs-outcome, catalog-entry-vs-reply-rate) belongs in `execute_code`, not eyeballed by an LLM turn. |
| `12-company-research` (+ its Addendum) | Subagent delegation | Multi-source research (Glassdoor, Reddit, LinkedIn, company blog, social) per company is exactly the "research N things in parallel, get structured summaries back" pattern Hermes's own delegation docs use as their canonical example. |
| `15-interview-prep` | Subagent delegation + voice | The new three-scope intel scrub (general/industry/company) is three independent research passes — same parallelization case as company research. Voice already wired via the reused `voice-interview-mode.md` setup for the mock drill. |
| `14-social-discovery-outreach` | Subagent delegation + MCP (Postiz/PostFast) | Query-driven multi-platform scanning parallelizes the same way job-source scanning does. The `quote`/`post` stubs, when they become a real feature, are exactly what Postiz/PostFast are built for — noted in that skill's stub section already. |
| `16-career-pulse` | Voice + external memory provider | Voice already wired. Worth flagging separately: journal entries accumulate for years, and FTS5's keyword search is fast but literal — "when did I last deal with a conflict like this" needs semantic matching, not keyword overlap. An optional external memory provider (Mem0-class) is the documented way to add that without replacing the built-in FTS5 layer, worth considering once the journal has real volume behind it, not on day one. |
| `17-cold-prospecting` | Subagent delegation + cron + native self-improvement | Already built this way in this audit's first pass — included here for completeness of the map, not as a new suggestion. |

## What I would *not* bother wiring up

Being honest about the other side of this, since a capability audit that
finds a use for everything isn't a credible one:

- **Subagent delegation for `05-resume-customizer`/`06-cover-letter`**
  — these are single-artifact, judgment-heavy, inherently sequential
  drafting tasks. Generating three parallel draft variants and picking
  one is a real pattern elsewhere, but nothing in this pipeline's design
  asked for multiple drafts per application, and adding it here would be
  building capability nobody requested rather than fixing a real gap.
- **Checkpoints for anything except `10-approval-and-submit`'s form-fill
  step** — most of this pipeline's file writes are additive/append-only
  by design (Rule 4's "log every attempt") rather than destructive
  edits, so there's little for a rollback to meaningfully undo elsewhere.
- **Multi-platform gateway expansion (Discord/WhatsApp/Slack/Signal)**
  — genuinely available, but nothing in this conversation asked to move
  approvals off Telegram, and adding channels without a stated reason
  just multiplies where Rule 1's approval message could get missed.
- **External memory provider for anything except `16-career-pulse`'s
  journal** — the rest of this pipeline's memory needs (STAR bank,
  domain-knowledge, target-profile) are already well-served by curated
  files plus confirm-before-write; semantic retrieval solves a "search
  years of raw text" problem the journal specifically has and the rest
  of the system mostly doesn't.
