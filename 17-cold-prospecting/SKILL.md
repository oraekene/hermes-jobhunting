---
name: job-hunting-cold-prospecting
description: "Pitch a company or person with no posted opening"
metadata:
  hermes:
    tags: [job-hunting, cold-prospecting]
    category: job-hunting
    related_skills:
      - job-hunting-social-discovery-outreach
      - job-hunting-contact-enrichment
      - job-hunting-company-research
---

# Cold Prospecting

## When this skill applies

Use this skill when Kene wants to reach a company or individual who hasn't posted an opening at all — proposing himself for an existing role variant, pitching a role/function that doesn't currently exist there but that he could fill, or offering a standalone service (consulting, a specific build, an audit, marketing, virtual-assistant work, or anything else he can credibly do). Distinct from 14-social-discovery-outreach, which is triggered by a posting; this skill is triggered by Kene identifying a target himself, with no posting involved. Reuses 14's platform-capability-matrix and cold-dm-email-schema rather than duplicating them — this skill's own job is the catalog of what's being pitched and the research behind who it's being pitched to. Do NOT draft any pitch — role-fit, role-creation, or service — from raw memory-bank content directly; every claim about Kene traces to a confirmed shared/pitch-catalog.yaml entry, and every claim about the target traces to actual research, never invention.

Origin: Kene's request for outreach that isn't anchored to any posting at
all — identifying a company or person and proposing (a) himself for a
role that exists there in some form, (b) a role that doesn't exist there
yet but that his skills could justify, or (c) a standalone service, of
any kind, professional or otherwise.

## Why this needed to be its own skill, not a mode flag on 14

`14-social-discovery-outreach` has an anchor for everything it drafts —
a posting, with a stated CTA. This skill has none. That single
difference changes what has to exist before a draft can be honest:
there's no external document to check a claim against, so the *evidence
structure itself* has to be built first, not assumed. That's the catalog
below — it's not bureaucracy for its own sake, it's the thing standing in
for "the JD" in every other skill's fidelity check.

What this skill deliberately **reuses rather than rebuilds**:
`14-social-discovery-outreach/references/platform-capability-matrix.md`
(send-tier logic is identical — a cold pitch DM has the exact same
per-platform constraints as a cold job-lead DM) and `cold-dm-email-
schema.md` (same record shape, extended with a few fields below, not
replaced).

## The three pitch modes

- **`role_fit`** — "I could do [title/variant] for you," where that
  function plainly already exists at the target (an obvious role at a
  company that size, or a task an individual visibly already needs done
  based on what they publicly do). Closest to an ordinary speculative
  application — just aimed at "no posting" instead of "posting closed."
- **`role_creation`** — proposing a role or task-set that doesn't
  currently exist at the target, built from Kene's own skills against a
  gap the research turned up. The higher-risk mode — see the target-claim
  gate below before drafting anything in this mode.
- **`service`** — offering a discrete deliverable rather than an
  ongoing role: an audit, a build, a campaign, a strategy document,
  virtual-assistant work, or something entirely outside Kene's tracked
  professional history (the wildcard case — see below). Structurally the
  closest to freelance/consulting sales outreach.

All three draft through the same pipeline; the mode only changes which
catalog entries get pulled and how the message frames the ask.

## The pitch catalog — my strong opinion on how content gets generated

Kene's question was genuinely open — user-authored, schema-driven, fully
auto-generated, or some mix. Here's the actual recommendation, and why:

**Don't fully auto-generate a pitch straight from the memory bank, per
target, with nothing durable in between.** Two concrete failure modes if
that's the design: claims about the same underlying skill get worded
differently across dozens of pitches with nothing keeping them
consistent (a real credibility risk if two targets ever compare notes,
and a real drift risk over time even if they don't); and nothing stops a
highly persuasive one-off pitch from overreaching, because unlike a JD-
matched application there's no external requirement to check the claim
against — the pitch is the only anchor, so if generation invents the
anchor too, there's nothing left gating it.

**Don't make Kene hand-write every pitch either** — that throws away
exactly the leverage a memory-bank-driven system exists to provide.

**The actual recommendation**: a confirmed, reusable **catalog** of
"sellable units," built once (with Hermes proposing candidates from the
full memory bank — STAR stories, domain-knowledge, project history —
the same `taxonomy_suggested`-then-confirm pattern `07-context-architect`
already uses for title variants), then every per-target pitch is
*generated fresh*, but only ever by **selecting and recombining
confirmed catalog entries against target research** — never by
inventing a new capability claim at draft time. This is the exact same
shape `05-resume-customizer`/`06-cover-letter` already use (compose from
evidence, don't invent), just with the catalog standing in for the
resume/STAR-bank and target research standing in for the JD.

Catalog entry shape (`shared/pitch-catalog.yaml.template`):

```yaml
- id: ""
  category: ""            # held | adjacent | wildcard — see below
  title: ""                # what this unit is called, e.g. "AI PM /
                             # generalist contractor", "job-application
                             # automation build", "prediction-market
                             # strategy consulting"
  pitch_type: ""           # role_fit | role_creation | service — which
                             # mode(s) this entry is usable in; some
                             # entries fit more than one
  one_line_pitch: ""
  evidence: []             # STAR-bank / domain-knowledge references —
                             # required for held and adjacent, may be
                             # empty for wildcard (see below, this is the
                             # important exception, not an oversight)
  target_customer_profile: ""   # what kind of company/individual this
                                  # tends to fit, used to pre-filter
                                  # which entries even get considered for
                                  # a given researched target
  rate_or_terms: ""         # optional — hourly, project-based, salary
                             # range; most relevant for service entries
  status: "active"          # active | paused | retired
  confirmed_at: null
```

### The three categories, and why `wildcard` needs different handling

- **`held`** — something Kene already professionally does, directly
  evidenced in the existing memory bank (AI PM work, the specific
  platforms he's built, etc.). Fidelity-checkable the normal way.
- **`adjacent`** — transferable but not literally his current title —
  same evidence requirement, just a looser mapping (this is functionally
  identical to `target-profile.yaml`'s existing `title_variants` with
  `source: taxonomy_suggested`, just extended past job titles to
  services and bespoke roles).
- **`wildcard`** — anything with **zero grounding** in the tracked
  memory bank — Kene's own example of an unrelated blue-collar skill is
  the clearest case, but this also covers any service he can do that
  simply never came up in a job-hunting conversation before. This
  category can't be fidelity-checked algorithmically at all — there's no
  evidence to check it against, on purpose, because the skill itself was
  never tracked. That means the entire honesty burden shifts to Kene's
  own confirmation. **Recommendation: wildcard entries get a distinct,
  slightly heavier confirmation step** than held/adjacent — not just
  "does this look right" but an explicit "you're telling me you can
  actually deliver this, confirmed?" — and pitches built from a wildcard
  entry get a `[WILDCARD]` tag carried all the way through to the
  approval message, so Kene is never approving one of these on autopilot
  alongside a routine, evidence-backed one.

## Target research — extends, doesn't replace, `12-company-research`

When the target is a **company**, this skill uses the exact same
`shared/company_research_cache/{company_slug}.md` cache `12-company-
research` already builds and maintains — no reason to duplicate it just
because this research run wasn't triggered by a JD. Same 90-day
freshness rule, same file shape, same non-negotiable rule carried over
verbatim: **"never fabricate a finding... a hook built on a fabricated
detail is worse than a generic one."**

When the target is an **individual** — genuinely new territory, no
existing skill does this — `references/target-research.md` defines the
same discipline applied to a person: public professional footprint,
publicly stated needs or pain points (their own posts/content, if
they've said something like "I wish I had time for X"), and the same
honest-gap default: if nothing solid turns up, the record says so
explicitly rather than guessing.

**Where the target is a company but no specific person is known yet**
(the common case for a `manual_request`-triggered pitch that starts
from "I want to reach Company X," not from a named individual):
`22-contact-enrichment` runs its Part A/B — identifying who at that
company is the actual hiring-manager/decision-maker-equivalent for what
this pitch is about, then enriching them with a verified email. Same
priority rule as `14-social-discovery-outreach`: the decision-maker-
equivalent contact is primary; a recruiter/gatekeeper-track contact, if
one also surfaces, is staged as its own separate outreach.

## The target-claim gate (new — this is the important addition)

`09-risk-tactics-gate` checks claims **about Kene**. Nothing in the
existing pipeline checks claims **about the target**, because no other
skill drafts content that makes any — a resume doesn't assert anything
about the employer. A `role_creation` pitch does, by construction
("I noticed you don't have X yet") — and that's a claim about a
stranger's business Hermes has no first-hand knowledge of.

**Rule: every statement in a pitch about the target's situation, needs,
or gaps must trace to something actually present in that target's
research record, and must be framed as a hypothesis, not an assertion.**
"I noticed [specific, research-backed observation] — is that something
worth exploring?" clears the gate. "You clearly need X" does not, even
if it's probably true, because "probably true" isn't the same standard
this pipeline uses anywhere else for a claim in an outward-facing
document. This matters most for `role_creation`, some for `service`,
least for `role_fit` (which mostly just needs the target to plausibly be
the kind of place/person that has that role at all — a much lower bar
than diagnosing a specific unmet need).

## Using Hermes to its actual limits

Kene asked for this explicitly, so a direct opinion: the highest-leverage
place to push automation here isn't the send step — the platform matrix
already shows that's mostly closed off, and fighting that is a losing
match against ToS, not a real capability gap. The leverage is upstream,
in research and iteration, where Hermes-native features actually apply:

- **Subagent delegation for parallel research.** Researching ten
  prospects sequentially is slow for no reason — spin up one subagent
  per target (isolated context, so personalization from target A never
  leaks into target B's draft) to run target-research in parallel, then
  a single pass to draft from the completed records.
- **Cron-scheduled prospecting cadence**, not just reactive drafting —
  "find and research N new targets a week" as its own scheduled job
  (see `cron-jobs-addendum.md`'s new entry), so the catalog gets exercised
  continuously instead of only when Kene thinks to ask.
- **The self-improving loop, applied to the catalog itself.** Once
  enough `social_outreach` rows exist with `pitch_mode` and
  `catalog_entry_ids` populated, `11-analytics-and-learning`'s existing
  correlation approach (tactic flags against outcomes) applies directly
  to "which catalog entry, in which mode, against which target profile,
  gets a reply" — proposed as a `skill_self_edits`-style suggestion
  ("entries tagged `service` are getting real replies on individual
  targets, `role_creation` pitches to companies aren't — want to pull
  back on those?"), never silently acted on.

None of this is about pushing further past what platforms allow — it's
about not wasting the parts of Hermes that were never platform-
constrained to begin with.

## Reference files

- `references/target-research.md` — individual-target research process
  (company-target research reuses `12-company-research` as-is).
- `../14-social-discovery-outreach/references/platform-capability-matrix.md`
  — reused, not duplicated.
- `../14-social-discovery-outreach/references/cold-dm-email-schema.md` —
  reused, extended with `pitch_mode` and `catalog_entry_ids` (see
  `shared/applications_db_schema_addendum_2.sql`).
- `../22-contact-enrichment/SKILL.md` — identifies and enriches a
  contact when a target is a company but no specific person is known
  yet.

## Wiring: `21-output-templates`

Same check `14-social-discovery-outreach` does before drafting: consult
`shared/output-templates.yaml` for an `artifact_type: cold_dm`/
`cold_email` entry whose `parameters` name a matching `pitch_mode`
and/or `shared/pitch-catalog.yaml` entry. A matched template guides
structure for that pitch; unmatched drafting proceeds exactly as
described above.

## Warm names before cold ones

`journal_collaborators` holds people Kene has actually worked with,
extracted from journal entries and confirmed by him. Check it before
building a cold list — a former colleague at a target company is a
categorically better route than a stranger, and this skill has been
ignoring one while working hard on the other.

Two rules. **Only `confirmed = 1` rows**: extraction is heuristic, and
contacting someone because a regex found a name is worse than not
contacting them. And **the outreach acknowledges the history** — reaching
out to someone you worked with for two years in the register of a cold
pitch is worse than saying nothing, because it reads as not remembering
them.
