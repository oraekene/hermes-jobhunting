# Role-Transition Intel — secondary, supplementary, never limiting

**Read this file's title as the whole rule, then the rest as
mechanics.** Everything below adds to `19-career-path-planner`'s Step 3
roadmap when it finds something usable, and changes nothing about that
roadmap when it doesn't. The primary process — `gap-analysis-engine.md`
scored against the target occupation's actual O*NET requirements — is
never gated, narrowed, or reordered by anything in this file. If a
target role has zero coverage across every source below, Step 3 runs
exactly as if this file didn't exist.

## Two source categories

### 1. Career-path aggregator sites/repos

Sites and repos that specifically exist to collate "how people get
from A to B" content — structured or narrative. Named explicitly
because Kene asked for them by name, but treated as a **category to
keep discovering**, not a fixed list:

- Teal HQ's career paths (`tealhq.com/career-paths/`)
- The developer-roadmap / roadmaps.sh project
- jobroadmaps.com
- **And actively watch for others in this category** — when a search
  turns up a new site doing the same kind of collation (a "career
  ladder" page, a "how to break into X" collection, an industry-specific
  roadmap project), treat it as a legitimate addition to this list going
  forward, not a one-off citation. This list is a starting point, not a
  ceiling.

### 2. General social/blog/article scrub

Same platform set `14-social-discovery-outreach`'s matrix already
covers for read access (this is pure research, not outreach — no
send-tier gating applies here, there's nothing being sent): YouTube,
Reddit, LinkedIn, Facebook, Instagram, TikTok, plus personal blogs,
company blogs, career blogs, and general articles. Same sourcing
discipline `13-interview-prep/references/interview-intel-research.md`
already established — reused directly, not reinvented:

- **Never fabricate a finding** — an honest "nothing solid found" beats
  a confident guess, same rule `12-company-research` and the interview-
  intel scrub both already carry.
- Corroboration matters — one account is a data point; the same
  reported step showing up across several independent accounts is a
  real signal, tagged as such.

## What to extract — a fixed checklist, not a vague scrub

Six categories, matching exactly what Kene asked for, so extraction is
systematic rather than whatever happens to be easy to find:

1. **Certifications** obtained, by name, where specific ones are named
   repeatedly enough to be a real signal (not every certification
   anyone's ever mentioned in passing).
2. **Projects** completed — the *kind* of project, not necessarily a
   literal copy of someone else's ("built and shipped a small internal
   tool solo" is useful; the specific tool's name usually isn't).
3. **Connections/networks built** — how people report finding their
   way in (informational interviews, a specific community, a mentor
   relationship) — this is the one category worth a light connective
   note: where a report specifically describes reaching out to people
   already in the target role, that's a natural, low-effort candidate
   for `17-cold-prospecting`'s `role_fit`-adjacent networking outreach,
   not something this skill needs to act on itself.
4. **Experience gained** — the shape of experience reported as the
   actual unlock (a specific kind of prior role, a lateral move, a
   volunteer/freelance stretch), not a generic "get more experience."
5. **Tasks completed** — specific, repeatable actions people describe
   taking on to prove readiness before the title changed.
6. **Mindset/approach shifts** — kept concrete and non-preachy: "several
   accounts describe shifting from execution framing to strategy
   framing when discussing their own work" is usable; vague self-help
   language ("believe in yourself," "think like a leader") is not
   extracted at all — if a source only offers that, it contributes
   nothing to this category, and that's a fine, honest outcome.
7. **Intermediate titles actually held** — added for
   `stepping-stone-engine.md` §3.4. The literal job title(s) a person
   held *between* the origin role and the target, with how many
   independent accounts report each one.

   Worth separating from category 4 rather than folding into it:
   "experience gained" is a description of what someone did, which is an
   interpretation, while an intermediate title is a fact about their
   résumé. It is one of the more reliable things these sources contain
   for exactly that reason, and it is the only category the engine
   consumes as a *candidate* rather than as colour.

   Two uses, both additive and both bound by the same never-limiting
   rule as everything else here. A title that also came out of the
   taxonomy candidate pool gets a corroboration flag and its frequency —
   **displayed next to the score, never folded into it**, since a
   popular route is not the same as a good one and blending the two
   hides which is which. A title the taxonomy pool *missed* is surfaced
   as a candidate tagged `[COMMUNITY-REPORTED]`, and this is where the
   category earns its place: real transitions run through titles O*NET
   models badly or not at all — hybrid roles, contract and agency
   bridges, secondments, internal-transfer titles that exist only inside
   one employer. Those appear in people's actual histories and nowhere
   in a standardised occupation taxonomy.

   Normalise lightly (strip employer names, seniority decorations and
   requisition noise) and keep the raw string alongside — an unusual
   title is sometimes the signal rather than the noise.

## Cache

`shared/role_transition_intel_cache/{target_title_slug}.md`, same
90-day freshness convention as the company/interview-intel caches.

```markdown
# [Target title] — role-transition intelligence

researched_at: 2026-07-25

## Certifications reported
- [cert] — reported by [N] independent sources

## Projects reported
- [project type/shape] — reported by [N] sources

## Connections/networks reported
- [pattern] — reported by [N] sources

## Experience reported
- [pattern] — reported by [N] sources

## Tasks reported
- [task] — reported by [N] sources

## Mindset/approach shifts reported
- [concrete, non-preachy description] — reported by [N] sources
  (omit this section entirely if nothing concrete was found — do not
  fill it with generic advice just to have an entry)

## Intermediate titles reported
- [normalised title] (raw: "[as written]") — reported by [N] sources
  (omit the section entirely where accounts describe direct moves —
  "several accounts report going straight from A to B" is itself a
  finding worth stating, and is not the same as finding nothing)

## Sources
[aggregator sites checked, platforms checked — "nothing found" is a
valid, explicitly stated result per source, not silence]

## Confidence note
[thin / well-sourced / mixed]
```

## Where this plugs in

Feeds `19-career-path-planner` Step 3's extended section directly —
each populated category above becomes a `[COMMUNITY-REPORTED]` line in
that skill's "Community-reported paths" subsection, never merged into
or substituted for the primary Roadmap section.

Category 7 additionally feeds Step 3.5's candidate generation via
`stepping-stone-engine.md` §3.4 — the one place this file's output
becomes an input to a scored decision rather than a labelled aside. The
guarantee still holds in the shape that matters: a community-sourced
candidate is scored by exactly the same two-sided function as a
taxonomy-sourced one, has to clear the same four validation checks, and
can never displace or gate a primary candidate. It can only ever add a
route that would otherwise not have been considered.
