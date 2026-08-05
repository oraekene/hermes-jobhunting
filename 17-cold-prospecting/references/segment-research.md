# Segment Research — pain-point *patterns*, not one target's record

## Why `target-research.md` was deliberately narrow, and why that was right for what it was

`target-research.md` exists to ground a claim about **one specific,
named stranger** before a pitch says anything about their situation.
Its honest-gap default — "nothing self-stated found, don't invent one"
— isn't over-caution for its own sake: a wrong guess about a specific
person is presumptuous in a way a wrong guess about a market segment
isn't, and that file's whole job is protecting against exactly that. It
was never designed to answer "what do people like this generally
complain about" — that's a different question, aimed at a *category*,
not an individual, and bolting it onto `target-research.md` would have
either watered down that file's per-target rigor or left the category
question unanswered. Neither was acceptable, so it stayed out of scope
on the first pass rather than being done badly.

That gap is real, though — the Origami-style workflow's "based on their
posting history + what they complain about in comments" step is
legitimate market research, just a different shape than target-research
does. This file is that shape, built with its own honesty discipline
rather than inheriting target-research's directly (a pattern needs
*corroboration*, not the single-source honesty target-research uses,
because a pattern is a claim about many people, not one).

## What this actually does

Takes a persona's `where_they_are` (from `17-cold-prospecting/
ideal-client-persona.md`) and searches those platforms/
communities broadly — not for one named person, for **recurring
language**: what does this *kind* of person keep saying, across
multiple independent posts/comments/threads, about the problem this
persona's matched catalog entries solve.

## The corroboration rule — this is the load-bearing part

**A candidate pain point or phrase does not enter `stated_pains`/
`language_they_use` on a single sighting.** Rule, not guideline:

- **Minimum 3 independent sources** (different authors, not the same
  person posting the same complaint three times, not three replies in
  one thread that are really one conversation) using recognizably the
  same complaint or the same framing, within the current 90-day
  freshness window.
- Each corroborating instance gets logged with its source (platform +
  post/comment URL where the platform allows a stable link, or a
  paraphrased pointer where it doesn't) — auditable the same way
  `company_research_cache` entries are, not just a number.
- A pattern that clears the threshold is recorded as **corroborated**
  and becomes eligible for `stated_pains`/`language_they_use`. A
  pattern with 1-2 sightings is recorded as **candidate** — visible in
  the cache file for Kene to read, but not pulled into a persona or a
  pitch automatically. This is the direct fix for the "inferring from a
  handful of vibes" failure mode: a low-volume pattern might be real,
  but this pipeline doesn't get to decide that on Hermes's own
  authority when the whole point of Rule 8 is that claims about people
  Hermes has no first-hand knowledge of need real grounding.
- Patterns never get promoted from candidate to corroborated
  retroactively by Hermes noticing more sightings *while drafting a
  pitch* — promotion only happens during a dedicated research pass
  (manual-triggered or the weekly cron below), so "I needed this pain
  point to be true for this draft" can never be the reason it crossed
  the threshold.

## Cache

`shared/pain-point-patterns/{persona_id}.md` — one file per persona
(catalog-entry-scoped, since personas are catalog-entry-scoped), 90-day
freshness rule, same missing/fresh/stale check as every other cache in
this pipeline.

```markdown
# Pain-point patterns — [persona_id]

researched_at: 2026-07-29
platforms_searched: [linkedin comments, reddit, x replies]

## Corroborated (>=3 independent sources, usable in personas/pitches)

- pattern_id: pp-0001
  paraphrase: "manually tracking installer margins across WhatsApp and
    a spreadsheet, no single source of truth"
  language_sample: ["losing track of who owes what", "WhatsApp and a
    spreadsheet is not a system"]   # short phrases only, sourced not
                                     # invented — feeds language_they_use
  source_count: 4
  sources: [url_or_pointer, url_or_pointer, url_or_pointer, url_or_pointer]
  first_seen: 2026-06-02
  last_corroborated: 2026-07-20

## Candidate (1-2 sightings, visible but not yet usable)

- pattern_id: pp-0002
  paraphrase: "..."
  source_count: 2
  sources: [...]

## Explicitly checked, nothing found

[if a search pass genuinely turns up nothing new — logged so a future
pass knows this was actually checked, not skipped]
```

## What still doesn't happen here

- **No scraping/reading that the underlying platform's own capability
  matrix already treats as unsafe at volume.** This runs through the
  exact same read-access rules `platform-capability-matrix.md` and
  `site-access-model.md` already set — LinkedIn reads stay occasional
  and light-touch, not a tight poll loop, even in service of pattern
  research. A segment-research pass is a heavier read operation than a
  single target lookup, which if anything argues for *more* caution on
  cadence, not less.
- **No inferring a pain point from what a segment doesn't say.** Same
  rule `target-research.md` already uses, applied to patterns instead
  of individuals: absence of complaint isn't evidence of the opposite.
- **No corroborated pattern gets treated as universally true of every
  individual matching the persona.** A corroborated segment pattern
  still only licenses persona-level language (`stated_pains` on the
  catalog entry). The moment a pitch is aimed at one *named* target,
  `target-research.md`'s per-individual rule takes back over — a
  segment pattern can inform the guess but `role_creation`/`service`
  claims about that specific person still need their own individual
  grounding or honest "no self-stated signal for this specific person"
  framing. Segment research narrows the hypothesis space; it never
  substitutes for target-research's per-person check.

## Cadence

Manual-triggered by default (Kene asking, or a new persona completing
its build pass). Optional weekly cron, same shape as job 12's
target-finding pass, scoped to personas whose pattern cache is stale
(>90 days) or was never built — proposed as its own cron entry rather
than folded into job 12, since a persona-pattern refresh and a target-
finding pass answer genuinely different questions and shouldn't share
one digest message.

## Where this plugs in

- `17-cold-prospecting/references/ideal-client-persona.md` — the only
  consumer of `stated_pains`/`language_they_use`; this file is where
  those fields actually get their content, sourced not invented.
- `14-social-discovery-outreach/references/discovery-query-design.md` —
  a different tool answering a different question (finding *hiring*
  posts to discover job leads/pitch targets), reused here only for its
  query-generation mechanics, not its purpose.
- `11-analytics-and-learning` — once enough `social_outreach` rows
  reference a `pattern_id` (via `personalization_hooks`), reply-rate
  correlation per pattern becomes possible the same way it already
  works for tactics and catalog entries.
