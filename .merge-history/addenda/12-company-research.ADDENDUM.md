# 12-company-research — Addendum: culture & candidate-sentiment research

Extends `12-company-research/SKILL.md` (base package, untouched) with a
new research category. Not a new skill, not a new cache file — this
plugs into the **same** `shared/company_research_cache/{company_slug}.md`
file the base skill already produces, as a new section, because the
whole point (per Kene) is that this should benefit the tool generally,
not live as an interview-only side-cache duplicate of research that's
already happening.

## New sources to pull from, alongside what the base skill already gathers

Glassdoor and similar review aggregators, Reddit (company-name searches,
relevant subreddits), LinkedIn (posts/comments mentioning the company
from people who don't work there — not the company's own page, which
the base skill's "About/Mission" step already covers), and general social
search — for:

- What it's actually like working there, from people who have — pace,
  management style, how decisions get made, anything a mission statement
  wouldn't say about itself.
- What they actually look for in candidates, by role/title where
  findable — patterns across interview reviews and hiring posts, not
  just the JD's stated requirements.
- Interview process and style specifically — format, number of rounds,
  reputation for being fast/slow, technical depth, anything candidates
  have reported. (This overlaps with `15-interview-prep`'s deeper
  role/title-specific scrub — see that skill's Phase 0 — but the
  company-specific slice of it belongs here, in the shared cache,
  since it's useful the moment a company name exists, not only once an
  interview is scheduled.)

## The one rule this inherits unchanged

**Same non-negotiable carried over verbatim from the base skill: never
fabricate a finding.** Review-aggregator content is also self-selected
by nature (people with strong opinions post more than people with none)
— the base skill already flags this exact caveat for Glassdoor-style
sources in its own "What this skill does not do" section; this addendum
doesn't loosen that, it just gives the caveat somewhere to actually
attach to, since before this addendum nothing was pulling from those
sources at all. Where a source (LinkedIn especially) genuinely needs a
logged-in read to be useful, see `shared/site-access-model.md` for which
access model applies — not assumed or left unstated here.

## Cache format — one new section, same file

```markdown
## Candidate/employee sentiment (Glassdoor, Reddit, social)
[summarized, sourced by source-type not URL-dumped — "multiple Glassdoor
reviews describe a fast-paced, self-directed culture" beats a single
quote]

### What they reportedly look for in candidates
[by role/title where findable, otherwise general]

### Interview process/style, as reported
[format, rounds, pace, difficulty — company-general; see
15-interview-prep for the role-specific version]

### Confidence note
[thin / well-sourced / mixed — same convention as the rest of the file.
Self-selected review-site content should default toward "mixed" unless
corroborated across multiple independent sources.]
```

## Why this benefits the whole tool without touching every consumer

Because this is a new section in the **same** cache file every existing
consumer already reads, nothing downstream needs to be individually
rewired: `06-cover-letter`'s Hook, `05-resume-customizer`'s
stage-informed bullet selection, `07-context-architect`'s
`company_stage`-variant answers, and `08-application-qa`'s
motivation/cultural-fit questions all get richer input automatically the
next time they read this cache, without any of those skills' own files
needing to change.
