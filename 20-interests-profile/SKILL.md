---
name: job-hunting-interests-profile
description: "Capture hobbies, side projects, and personal interests"
metadata:
  hermes:
    tags: [job-hunting, interests-profile]
    category: job-hunting
    related_skills:
      - job-hunting-context-architect
      - job-hunting-career-pulse
      - job-hunting-career-path-planner
---

# Interests Profile

## When this skill applies

Use this skill to capture and maintain Kene's interests profile — hobbies, side projects, volunteer/non-profit work, things he likes, childhood interests, and things people have noticed or complimented him on — as a distinct part of the memory bank, separate from domain-knowledge.md and the STAR bank because the whole point is capturing things that ARE NOT yet professional evidence. Triggers: first-time setup (see onboarding), Kene mentioning something interest-shaped in passing, or a request to update/review the interests profile directly. Feeds 19-career-path-planner's interest-fit scoring and mode (e), plus several other pipeline stages — see 'Where this is relevant' below. Only 07-context-architect writes confirmed memory (Rule 5) — this skill proposes interests-profile.md entries through that same confirm-before-write step, it doesn't write the file itself.

Origin: Kene's request for a genuinely new dimension of the memory bank
— and worth answering his actual question directly before the design:
what does "interests" mean here, and how is this different from O*NET's
own Interest Profiler, which already exists and does something with the
same name.

## Definitions — O*NET's, and why ours is a different thing wearing a similar name

**O*NET's Interest Profiler** is a real, well-established tool: a
30- or 60-item self-report survey built on Holland's RIASEC model — six
abstract types (Realistic, Investigative, Artistic, Social,
Enterprising, Conventional). You rate a fixed bank of activity
statements ("I would like to build kitchen cabinets," "I would like to
study animal behavior"), it scores you against those six dimensions,
and it hands back a 3-letter code linked to occupations in O*NET's own
database that share that code. It's genuinely useful for what it's
built for, and worth noting one thing directly relevant to Kene's
target audience: O*NET publishes a specific "Career Starter" version of
its score report **explicitly designed for people without work
experience or who are just starting their education** — the exact
audience Kene named. So O*NET itself already treats "no work history
yet" as a distinct, real use case worth its own version, not an edge
case.

**Where ours is a different thing, on purpose**: O*NET's tool is a
fixed, abstract, one-time survey — the same 60 generic activity
statements for every person, scored down to a 3-letter code, and it
stops there; it doesn't feed anything else. Kene's version is the
opposite shape in every way that matters for this pipeline: **not a
survey, a conversation** — capturing the person's own specific,
textured history (an actual side project, an actual compliment someone
gave them, an actual thing they did as a kid), not abstract
yes/no/maybe ratings on generic activity statements. It's continuously
enriched, not a one-time snapshot. And critically, it's built inside a
pipeline that can actually *use* the result for something — a roadmap
suggestion, a cover-letter hook, a pitch-catalog entry — not just hand
back a code and stop.

**The RIASEC framework itself is still worth reusing, just not as the
primary representation** — same design choice `content-model-
overlap.md` already made for skills: capture rich, specific, evidence-
cited content as the thing Kene and this pipeline actually work with,
and derive a standardized RIASEC mapping underneath it only for the one
job standardization is actually good at — comparing against O*NET
occupations' own Interest ratings at matching time. See
`references/riasec-mapping.md`.

**Kene's own definition, confirmed as the working one**: things a
person is genuinely interested in or has a talent for that *aren't* in
a CV, a professional profile, a GitHub account, or any other career
document — specifically *because* they were never treated as
professional, or never got the chance to be. Six categories, exactly as
he named them:

1. Hobbies
2. Side projects — including ones never monetized, shown to anyone, or
   finished
3. Non-profit / volunteer work
4. Things they like — broader than an "activity," includes passive
   interests (what someone reads, watches, follows)
5. Things they liked or did as children
6. Things other people have noticed or complimented them on

## Admission criteria — deliberately lighter than domain-knowledge.md

**This is the one thing worth stating most plainly, because it's easy
to accidentally import the wrong bar from the rest of this skill
package.** `domain-knowledge.md` and the STAR bank exist to support
claims that go out to an employer, so they carry a real evidence/
quantification bar (`07-context-architect` Phase 2's Quantification
gate). **`interests-profile.md` entries don't need that bar, on
purpose** — an entry is admissible on Kene's own say-so that it's
genuine, full stop. No number required, no "prove it" step, no
downstream document depends on it being airtight the way a resume
bullet does. The only thing this skill checks is honesty (is this
actually a real interest, not something said to fill a slot), never
rigor.

## Aging — the only bar this file can have

The carve-out above is right, and it has a consequence that was never
followed through. `09-risk-tactics-gate` accepts entries here as
legitimate evidence at `profile_stage: first_time`. So this file needs
*some* check on whether an entry is still true — and because it
deliberately has no evidence bar, **a time bar is the only kind of bar it
can carry.**

The problem is specific. An interest recorded three years ago and
abandoned two years ago is currently indistinguishable from a live one.
Both are entries with an `Added:` date. One of them is about to be
offered to a hiring manager as a thing Kene does.

Per `07-context-architect/references/fact-conflict-resolution.md`:

- **Every entry is `volatile`.** Interests are among the most changeable
  facts this pipeline stores. None of them are `durable`.
- **Reconfirmation interval: 12 months** (`fact_aging.interests_reconfirm_months`).
- **Each entry carries `Last confirmed:` alongside `Added:`.** Different
  dates, and conflating them is how this gap existed in the first place.
- **Past the interval, an entry is flagged, not dropped.** It is still
  returned, tagged `[LAST CONFIRMED: 18 months ago]` at the point of use.
  A twelve-month-old interest is very probably still an interest; stale
  means unverified and nothing stronger.
- **A flagged entry may not be used as risk-gate evidence until
  reconfirmed.** This is the one place staleness does more than label,
  and the reason is that this is the one place a stale entry leaves the
  building. Everywhere else a stale fact degrades a suggestion Kene
  reviews; here it gets offered to an employer as current, and "he
  mentioned it, turned out he stopped two years ago" is a credibility
  cost paid in the room.

Reconfirmation is a question, never an inference — same Rule 5 discipline
as everything else. `16-career-pulse`'s check-in is the natural place to
ask, in batches of three or four ("still doing these?"), rather than as a
standalone chore. Keep the tone note above in force: this should read as
interest, not as an audit.

An entry Kene says he has stopped is **marked superseded with the date,
not deleted**. It is still evidence of what he used to spend time on,
which `19-career-path-planner` can use for pattern work long after it
stops being usable as outward-facing evidence.

## Elicitation

A dedicated pass, not folded into a routine memory-refresh — this
deserves its own session, run once as a real first pass (see
`onboarding`'s settings catalog) and revisited whenever Kene wants,
not on a forced cadence. Six prompts, one per category above, asked
conversationally rather than as a form — and specifically **voice-
friendly by default**, reusing `voice-interview-mode.md`'s exact setup
like every other elicitation in this package: some of this is genuinely
easier to talk through than type (a compliment someone gave you, a
thing you loved doing as a kid), and forcing it into text first is
exactly the kind of friction that makes people skip a section rather
than answer it.

**Tone matters more here than almost anywhere else in this pipeline.**
This is warmer, more personal territory than a STAR-bank interview —
keep it genuinely curious and unhurried, not clinical, and don't push
if a prompt doesn't land ("nothing comes to mind" is a complete,
acceptable answer to any of the six, not a gap to keep probing).

**Ongoing, passive enrichment**: `16-career-pulse`'s journal already
surfaces candidate facts from casual mentions — this skill is a second
consumer of that same surfacing mechanism. A journal entry that reads
as interest-shaped ("spent the weekend restoring an old motorcycle,"
"finally got back into painting") gets proposed as a candidate
`interests-profile.md` entry the same way a work-shaped entry gets
proposed as a candidate STAR-bank fact — same Rule 5 confirm-before-
write, same skill (`07-context-architect`) doing the actual writing.

## `memory/interests-profile.md` — format

```markdown
## [Category: hobby | side_project | volunteer | thing_they_like |
##  childhood | noticed_by_others]

### [Short name]
What it is: [description, in Kene's own words as much as possible]
How long / how serious: [casual vs. sustained — no rigor required,
  just honesty]
Ever used professionally: [no | partially — where/how, if so]
Sensitive category: [none | religion | health/disability | political |
  other — see shared/pipeline-rules-addendum.md's discretion rule
  before this is ever used in anything outward-facing]
Added: [date] — [elicitation session | journal-surfaced]
Last confirmed: [date] — the last time Kene actually said this is still
  true. On a new entry it equals Added; after that the two diverge, and
  the divergence is the whole point. Past 12 months this entry is
  flagged, still returned, and not usable as risk-gate evidence until
  reconfirmed.
Status: [current | superseded on [date]] — an interest he's stopped is
  kept, not deleted; it's still evidence of what he used to spend time
  on
```

## Sensitive-category handling

Some interests genuinely reveal protected-characteristic-adjacent
information — religion, health/disability, political or organizing
activity, and similar. **Nothing here is off-limits from being
recorded** — this file is private, and the whole point is capturing
things freely. What's gated is *outward-facing use*: see the new rule
in `shared/pipeline-rules-addendum.md` — any entry tagged with a
sensitive category needs its own explicit, per-use confirmation before
it ever appears in a cover letter, application answer, cold pitch, or
resume, purely to protect Kene from a discrimination-risk exposure he
didn't consciously choose to accept in that specific context. Framed
practically, not as a values statement — the same instinct behind
keeping salary and visa status as deliberate confirmations rather than
silent defaults.

## Where this is relevant across the pipeline

Asked directly to make this call — here's every point in the full tool
where an interests entry can genuinely help, and why:

- **`19-career-path-planner`** — the biggest one. Interest-fit becomes
  a cross-cutting score applied across every existing mode, plus a new
  mode (e) for interest-led discovery. See that skill's own updated
  Step 1.5.
- **`06-cover-letter`** — a real, specific interest can be a far more
  genuine "why this company" hook than manufactured enthusiasm, when it
  actually lines up (someone with a genuine, years-long interest in
  conservation applying to an environmental company has a real story to
  tell, not a performed one). Still runs through the sensitive-category
  gate like anything else headed outward.
- **`08-application-qa`** — "tell us about yourself outside work" /
  culture-fit questions have a direct, obvious source here that didn't
  exist before.
- **`13-interview-prep`** — same reasoning as cover letters and
  application Q&A, for "tell me about yourself" and rapport-building
  moments specifically.
- **`17-cold-prospecting`'s pitch catalog** — `wildcard` category
  entries (skills with zero grounding in the tracked memory bank) were,
  before this skill existed, invented ad hoc in conversation. Now they
  have a real source: an interests-profile entry Kene's already
  confirmed is genuine is a far better starting point for a wildcard
  pitch than starting from nothing. Doesn't change Rule 9's heavier
  wildcard confirmation step — an interest being logged here doesn't
  mean Kene's confirmed he wants to *sell* it as a service, that's still
  its own separate confirmation.
- **`05-resume-customizer`** — narrow, deliberate applicability: an
  "Interests/Activities" section is a genuine, common practice
  specifically for candidates with thin professional history (students,
  first-time job seekers, career changers) — not something this skill
  suggests adding to an experienced professional's resume, where it
  usually doesn't belong. Gated the same sensitive-category way as
  everything else outward-facing.
- **`16-career-pulse`** — already covered above as the passive
  enrichment source; worth listing here too since it's a two-way
  relationship, not just upstream of this skill.

## The audience this was actually asked for — an honest scoping note

Kene named a specific, important future audience: secondary schools,
universities, youth groups, churches and mosques, and people with thin
or no employment history, long gaps, or who are simply tired of their
current path and want something more enjoyable. This skill is built to
work for that audience from day one — the six elicitation categories
don't assume any prior job existed. **One real adaptation this doesn't
fully solve yet, worth being honest about rather than glossing over**:
modes (a)-(c) of `19-career-path-planner` anchor on a *current title*
that a first-time job seeker simply doesn't have. Mode (e) (below)
sidesteps that for interest-led discovery specifically, and a
reasonable `job_zone` default for someone with no title to anchor from
is derivable from education level/life stage rather than a held role —
but a genuinely complete onboarding experience for someone with zero
work history is a larger adaptation than this pass covers (the SIMPLE
tier's own definition, "produces a staged application," doesn't even
make sense as the bar for that user). Worth its own dedicated design
pass rather than a partial answer stretched to cover it here.

## Reference files

- `references/riasec-mapping.md` — how interests-profile.md entries get
  mapped to RIASEC for occupation matching, without becoming the
  primary representation.
