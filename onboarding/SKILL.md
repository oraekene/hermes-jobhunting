---
name: job-hunting-onboarding
description: "Set up or reconfigure the job-hunting pipeline"
metadata:
  hermes:
    tags: [job-hunting, onboarding]
    category: job-hunting
    related_skills:
      - job-hunting-context-architect
      - job-hunting-orchestrator
      - job-hunting-skill-composer
---

# Onboarding

## When this skill applies

Use this skill on a fresh install (no target-profile.yaml, no STAR bank, or both look empty/thin) or when Kene explicitly asks to set up or reconfigure the pipeline from scratch. Sequences every setting in references/settings-catalog.md into a paced rollout — a minimum runnable subset first, everything else spread adaptively over the following sessions. Reuses 07-context-architect's Phase 0-4 as the core of the first session rather than duplicating it; this skill's own job is everything Phase 0-4 doesn't already cover (tier, sources, calibration, career-pulse, voice, and anything else in the catalog) plus the pacing/style layer around all of it. Distinct from sources.yaml's own narrower 'onboarding a new source' micro-flow, which is about adding one source, not setting up the person.

Origin: Kene asking directly whether this tool has an onboarding process
at all. Honest answer, worth stating plainly rather than assumed: **no,
not before this pass.** The closest thing that existed was `07-context-
architect`'s Phase 0-4 (target profile + career-content interview) —
genuinely substantial, but scoped to career content and a handful of
target-profile fields, run as a single "before everything else" pass,
not paced, and not covering the rest of the settings surface this
package has accumulated across every addendum since (calibration,
pitch catalog, career-pulse, voice, tiers, sources). This skill is the
layer that actually makes the whole catalog a deliberate, paced
experience instead of either a wall of questions on day one or a pile of
silent defaults nobody chose.

## The two tiers, and why the split is exactly the runnable/not-runnable line

`references/settings-catalog.md` tags every setting **SIMPLE** or
**ADVANCED** using one test: *does the pipeline produce a staged,
approvable application without it?* That's not an arbitrary difficulty
split — it's the actual functional boundary. Everything SIMPLE happens
in the first session, uninterrupted, because there's no honest way to
"ease into" a resume with no title to target or a search with no source
to pull from. Everything ADVANCED can wait, because the pipeline is
genuinely useful — genuinely running — without it.

### Session 1 — the SIMPLE tier, run to completion

**First, which track.** Before Phase 0 starts in earnest: ask directly
whether this is someone with prior work history or a first-time
entrant to the workforce (a soft signal — Phase 1 ingestion coming back
empty or education-only — can suggest a default, never assume one).
This sets `profile_stage`, and it changes what "SIMPLE tier" actually
means for the rest of this session — see `references/starting-out-
track.md` for the full second track. Everything below this point
describes the `experienced` track; `first_time` has its own version of
Session 1 in that reference file, not repeated here.

Pair the approval channel first if it isn't already (nothing else
matters until this exists), then run `07-context-architect` Phase 0
through 4 essentially as that skill already specifies — this skill
doesn't re-implement Phase 0-4, it just guarantees this is where
onboarding actually starts, and adds the handful of SIMPLE-tagged items
Phase 0-4 doesn't already own (confirming at least one `sources.yaml`
entry, checking `fidelity_mode`/`discovery_mode` landed on a value even
if it's just the sensible default). One session, not spread out — this
is the one part of onboarding that isn't paced, because a half-set-up
profile isn't a smaller version of the pipeline, it's a non-functional
one.

### Sessions 2 through N — the ADVANCED tier, spread over 1-2+ weeks

Everything else in the catalog, introduced a little at a time rather
than dumped. Genuinely paced by cadence detection (below), not a fixed
"one topic per day" script — 1-2 weeks is a reasonable planning
assumption, not a hard timeline this skill enforces. Order within the
advanced tier: roughly follows dependency and payoff — `tier-config`
and additional `sources.yaml` entries early (cheap, immediately
useful), `dynamic-target-calibration` and `career-pulse` cadences next
(meaningfully change ongoing behavior), `pitch-catalog` seeding last
and explicitly as its own dedicated session per that file's own
guidance, never folded into a general "let's cover a few more settings"
turn — seeding the catalog is a genuinely creative pass, not a
checkbox.

## Cadence detection — how Hermes decides the pace, not a fixed schedule

Signals available without asking Kene to self-report a preference he
may not have introspected on: how often he initiates sessions with
Hermes at all, how long his replies tend to run (a few words vs.
paragraphs suggests something different about how much back-and-forth
he wants in one sitting), and whether he answers a setting question
immediately or comes back to it later in the same session. None of
these need a formal scoring system — this is exactly the kind of
"workflow pattern" `USER.md` already has room for
(`07-context-architect/SKILL.md`'s own description of what belongs
there: "communication preferences... and workflow patterns"), so
onboarding's read on Kene's cadence gets written there like any other
preference, confirmed the normal way, and every later session (not just
onboarding) benefits from it existing.

**If genuinely uncertain after the first session or two, ask directly**
rather than guessing indefinitely — "want me to keep the setup
questions coming a few at a time like this, or would you rather do a
longer session and get the rest out of the way?" is a fair, low-cost
question, and a stated preference always outranks an inferred one.

### What this actually looks like, concretely — one plausible run

Worth grounding the abstract tier/pacing design in an example, the same
way the calibration doc's worked example made that system concrete —
this is illustrative, not a script to reproduce exactly:

- **Day 1**: approval channel paired, Phase 0-4 run to completion in one
  sitting (SIMPLE tier). By the end of this session, `01-job-discovery`
  through `10-approval-and-submit` can genuinely run.
- **Day 2-3**: Kene comes back with short, quick replies and a gap of
  only a day — read as "wants to keep moving," so the next session
  covers `tier-config` and 2-3 more `sources.yaml` entries in one short
  batch rather than trickling one setting at a time.
- **~Day 8-10**: `dynamic-target-calibration` and `career-pulse`
  cadences — introduced with more framing than the tier question got,
  since these genuinely change ongoing behavior rather than being a
  one-line pick.
- **~Day 12-14, as its own dedicated session**: `pitch-catalog` seeding,
  kept separate per that file's own guidance rather than folded into a
  "few more settings" turn.
- If instead Kene had gone quiet for a week after Day 1, the read would
  differ — a longer gap suggests infrequent, deliberate sessions, so the
  next touchpoint bundles more of the advanced tier into one sitting
  rather than assuming he'll be back again tomorrow for a few more.

The tier boundary (SIMPLE vs. ADVANCED) doesn't move in any version of
this; only the grouping and spacing of the ADVANCED items do.

## Language and presentation — deliberately unspecified here, on purpose

**This skill does not prescribe wording, tone, or exact medium for any
onboarding question.** That's a genuine design choice, not an
oversight: a fixed script would fight the same personalization this
whole pacing system exists to provide. What's fixed is *what* needs a
confirmed value (the catalog) and *when* it's in scope (the tier
split) — *how* it gets asked is Hermes's judgment call each time,
informed by whatever's already been observed about Kene in that
session and prior ones. Concretely, this means: text or voice (voice
notes already work throughout, per `voice-interview-mode.md`, no reason
onboarding should be the exception), terse or explanatory (a field
like `fidelity_mode` genuinely benefits from the side-by-side comparison
Phase 0.5 already writes out; a field like `active_tier` probably
doesn't need nearly that much framing), and delivered as a batch of
related questions or spread one at a time — all of that is a live
judgment call, not a script to follow.

## Where this plugs into existing rules

Nothing in this skill writes a confirmed fact on its own — every SIMPLE
and ADVANCED item still lands through whichever skill actually owns
that file (`07-context-architect` for target-profile.yaml/memory,
`16-career-pulse`'s own confirm flow for its settings, and so on). This
skill's job is sequencing and pacing *when* each owning skill's own
confirm-before-write step gets triggered — it's a scheduler sitting in
front of Rule 5, not an exception to it.

## Distinct from `sources.yaml`'s own onboarding note

Worth flagging so the two don't get confused: `shared/sources.yaml`
already has its own "Onboarding a new source" section — that's about
adding **one job source**, run any time, by anyone, well after initial
setup. This skill is about onboarding **the person**, once, at the
start. Same word, different scope; this skill's SIMPLE tier includes
running that source-onboarding flow for at least one source, but this
skill doesn't replace or duplicate that flow's own logic.

## Reference files

- `references/settings-catalog.md` — the full enumeration, SIMPLE/
  ADVANCED-tagged, organized by owning file.
- `references/starting-out-track.md` — the `profile_stage: first_time`
  track for someone with no or thin work history: a genuinely different
  Session 1, not a lower bar on the same one.
