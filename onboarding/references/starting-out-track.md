# The "Starting Out" Track — a genuinely different first path, not a lowered bar

The dedicated pass flagged as owed in `20-interests-profile/SKILL.md`.
Worth being precise about what's actually being solved before the
mechanics, because the audience Kene named (secondary schools,
universities, youth groups, churches and mosques, and adults with thin
history, long gaps, or a stale career) is really **three different
situations**, and conflating them would produce a worse design than
treating them separately.

## Three situations, not one — and two of them are mostly already solved

1. **No or thin work history** (students, first-time job seekers). The
   real gap. Nothing in this pipeline before now has a coherent answer
   for someone with nothing in the traditional sense to ingest in
   `07-context-architect` Phase 1. **This document is mostly about this
   case.**
2. **Long gap between roles.** Mostly already solved —
   `shared/dynamic-target-calibration.yaml`'s `employment_status` +
   `auto_relax_schedule` exists specifically for this, tuned in weekly
   increments up to 26 weeks. One real gap worth naming: that schedule
   tops out at ~6 months, and a genuine long-gap case (multi-year — care
   responsibilities, recovery, other reasons) needs a longer curve, plus
   a different qualitative flag than "still job hunting the same lane" —
   see this doc's small addition to that file, below. Otherwise, not
   redesigned here; it doesn't need to be.
3. **Career pivot — experienced, but wants something different and more
   enjoyable.** Also mostly already solved, as of last round:
   `19-career-path-planner` modes (c)/(e) and the whole interests-profile
   feature exist specifically for this. This person has a full career's
   worth of evidence, just pointed at the wrong target. Not redesigned
   here either.

So the actual new work is situation 1, and it's a bigger adaptation than
a setting or two, because the pipeline's default shape assumes
professional evidence exists to ingest, gate, and score against — true
almost everywhere, from `07-context-architect`'s Phase 1 through
`03-resume-match`'s scoring to `05-resume-customizer`'s format
assumptions.

## The core design decision: a `profile_stage` flag, not a lower bar anywhere

Added to `target-profile.yaml` (via `07-context-architect`'s Phase 0,
same confirm-before-write discipline — asked directly, never inferred
and silently set, even though a soft signal can *suggest* a default —
see "Detection" below):

```yaml
profile_stage: "experienced"   # experienced | first_time |
                                # returning_after_gap | career_pivot
```

`returning_after_gap` and `career_pivot` mostly just confirm which
existing mechanism applies (calibration's relax schedule; mode c/e
respectively) — they're not new tracks. `first_time` is the one that
actually changes behavior across several skills, detailed below.
**Nowhere does `first_time` mean "accept weaker evidence" — it means
"accept a wider range of legitimate evidence sources, at the same
rigor."** A school fundraiser someone organized and can quantify is a
perfectly real STAR entry; a vague claim without specifics still isn't,
regardless of `profile_stage`. That distinction matters enough to
repeat at every point below where it'd be easy to blur.

## Detection — suggested, never assumed

Asked directly, early in `onboarding`'s first session, before Phase 0
starts in earnest: some version of "have you worked before, or would
this be your first real step into it?" A soft signal can pre-fill a
suggested answer (Phase 1's resume/portfolio ingestion coming back
empty or education-only is a reasonable trigger to *suggest*
`first_time` as the default to confirm) — but it's always a confirm,
never a silent inference, same Rule 5 discipline as everything else
this pipeline writes.

**Institutional/facilitator context, flagged not built**: Kene's named
audience includes schools, universities, youth groups, and religious
organizations — settings where a counselor, teacher, or group leader
may be setting this up for many people at once, not each person
self-directing individually. A cohort-level default (a facilitator sets
`profile_stage: first_time` once for a whole group rather than each
student confirming it) is a reasonable extension of this design, not a
different one — but it's flagged here rather than built, because it
opens a genuinely separate question this pass doesn't answer: who has
access to a facilitator-managed account's data, and under what
authority. Worth its own pass once that use case is actually being
built toward.

## What actually changes when `profile_stage: first_time`

### `07-context-architect` — a widened Phase 1, not a lowered one

Ingestion sources beyond "resume/portfolio" (which may not exist at
all): school records/transcripts, coursework projects, extracurriculars,
sports and competitions, volunteer and community work, family or
household responsibilities taken on, self-taught skills. The
Quantification gate (Phase 2) applies exactly as before — "organized
the school's fundraiser" still needs the specific number that makes it
real, same as any resume bullet would. What's different is the source
list feeding *into* that gate, not the gate itself.

`memory/interests-profile.md` (`20-interests-profile`) moves from
advanced-tier, deferred content to **co-primary with domain-knowledge/
the STAR bank, elicited in the same first pass** — for someone with
little formal work history, hobbies, side projects, and things people
have noticed about them often *are* the richest available evidence,
not a supplement to something more substantial. `onboarding/references/
settings-catalog.md`'s tag for that file already flagged this
possibility; this document is where it becomes concrete rather than a
caveat.

### `09-risk-tactics-gate` — same rigor, wider accepted evidence tiers

Needs to treat school/coursework/volunteer/interests-profile evidence
as legitimate tiers to check a claim against, not just
employer-verified work history. No change to the actual honesty
standard — a claim still needs to trace to something real and specific.

### `05-resume-customizer` / `06-cover-letter` — a genuine format branch

Reverse-chronological work history is the wrong default shape for
someone who doesn't have one. `profile_stage: first_time` switches the
default to a skills/projects-led (functional or combination) format,
with an Interests/Activities section as standard rather than the niche
addition it is for `experienced` — flagged already in `20-interests-
profile/SKILL.md`, now the concrete trigger for it. Cover letters shift
narrative shape correspondingly: not "in my N years doing X," but "here
is what I've built, learned, and care about, and why it points at this."

### `dynamic-target-calibration` — a different default starting point, for a real, nameable reason

Worth stating the reason plainly rather than just the number: entry-
level postings are well-documented to list requirements — "2+ years'
experience" on a role titled "entry level" is the classic case — that
don't actually reflect what's needed to do the job. A first-time
seeker scored against that text at the same `match_score.minimum: 70`
default as an experienced applicant would get filtered out of almost
everything, not because their fit is actually worse, but because the
postings' own text systematically overstates the bar. `profile_stage:
first_time` sets a different default (`minimum: 55`, `stretch.floor:
35` — starting points, not researched constants, same status as the
existing schedule's own numbers) for this reason specifically, not as a
general "go easier" adjustment. `overqualification_tolerance` is
effectively moot for this segment and can be left at its default
without consequence — this profile stage essentially never trips that
gate in the other direction.

### `19-career-path-planner` — mode (e) becomes the suggested starting point

Not the only option, but the default suggestion: for someone with
nothing to anchor modes (a)-(c) on, running mode (e)
(`20-interests-profile`-driven discovery) first, landing on a
confirmed target, *then* letting the regular 01-11 pipeline run against
that target, is a more honest sequence than pointing a nearly-empty
`title_variants` list at `01-job-discovery` and hoping something
reasonable turns up.

## What "the first milestone" means for this track — the actual SIMPLE-tier redefinition

`onboarding`'s existing SIMPLE tier test — "does the pipeline produce a
staged, approvable application without it?" — is the right test for
`experienced`, and the **wrong first goal** for `first_time`, not just a
harder one to hit. Producing a thin, generic application from someone
with nothing built up yet serves them worse than helping them build
real direction first. Track B's own SIMPLE tier, run to completion in
session 1 same as Track A's:

1. Approval channel paired.
2. `interests-profile.md` elicitation (co-primary, per above).
3. Whatever education/informal evidence exists, ingested per the
   widened Phase 1 source list.
4. At least one `19-career-path-planner` mode (e) plan, generated and
   taken through Step 5 — either "search for this now" or "keep this as
   a plan I'm building toward," Kene's — sorry, *the person's* — choice
   either way.

A first staged application becomes available once a target exists, and
is explicitly framed as the *second* milestone for this track, not a
day-one requirement.

## Tone — the one thing that matters as much as any mechanism above

Worth stating as its own principle rather than assuming it falls out of
the mechanics automatically. This pipeline's internal vocabulary —
"evidence bar," "quantification gate," "fidelity mode" — is fine
between skills; it is the wrong register for a conversation with a
17-year-old who has never done this before and may already feel like
they have "nothing to put on a resume." Concretely:

- Not: *"You don't have any work experience to draw from."*
  Instead: *"Let's build from what you've actually got — school,
  projects, things you've organized, stuff you're good at that nobody's
  asked about yet."*
- Not treating a thin `interests-profile.md`/STAR-bank as a problem to
  apologize for — it's the expected, normal starting shape for this
  track, not a deficient version of `experienced`'s.

## A consideration that deserves its own dedicated attention, flagged plainly rather than folded in here

Kene's named audience includes secondary schools — meaning some real
share of users in that setting are minors. That's a genuine, separate
product requirement, not an extension of anything above: parental/
guardian consent flows before a minor's data is collected at all, data
minimization and retention limits appropriate to a minor's information
specifically (an interests-profile entry from a 15-year-old plausibly
warrants different defaults than an adult's), age-appropriate framing
throughout — not just the encouraging-not-clinical tone above, a
stricter bar — and a clear, considered policy for what happens if
something concerning surfaces in a journal or interests conversation
with a minor, beyond what this pipeline's existing wellbeing-conscious
design already does for adults. This document doesn't attempt any of
that — it's flagged here because it's real and important, and building
toward the school/youth-group audience without addressing it directly
first would be the wrong order to do the work in.
