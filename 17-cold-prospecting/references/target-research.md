# Individual-Target Research

**Scope note**: this file is for one specific, named person. For "what
do people like this generally complain about" — a segment/persona
question, not a named-target question — see `segment-research.md` instead; it has its own, deliberately different honesty
rule (corroboration across multiple sources, not single-source honesty)
because a pattern claim about a category and a fact claim about one
stranger carry different risks if wrong. The two files are never
substitutes for each other — segment research can narrow a hypothesis
before a specific target is even known, but once a pitch names a real
individual, this file's per-person check still applies in full.

Extends `12-company-research`'s discipline to a genuinely new entity
type: a person, not an organization. Same non-negotiable rule, carried
over verbatim: **never fabricate a finding — an honest "nothing solid
found" beats a confident guess, every time**, and matters more here than
it did for companies, because a wrong guess about a stranger's business
is impersonal; a wrong guess about a specific person reads as either
presumptuous or unsettling if it's off, even slightly.

## Cache

`shared/individual_research_cache/{handle_slug}.md` — same 90-day
freshness rule as the company cache, same "missing / fresh / stale"
check before doing any work.

## What to actually gather

Scoped tightly to what's relevant to a pitch, not a general profile:

- **Public professional footprint** — what they do, for whom, publicly
  stated (bio, "about" text, portfolio, public posts describing their
  own work).
- **Self-stated needs or gaps**, only if the person has said something
  themselves that plausibly points to one — "I wish I had time to..." /
  "still haven't figured out..." / a visible struggle named in their own
  content. This is the only legitimate source for a `role_creation`
  hypothesis about an individual; inferring a gap from silence (they
  *don't* mention doing X, therefore they must need X) is exactly the
  kind of unfounded inference `17-cold-prospecting`'s target-claim gate
  exists to block.
- **Scale/context signal** — solo operator vs. team, roughly how
  established, what stage — same purpose the company cache's stage/size
  signal serves, just for a person's operation instead of a company's.

## What NOT to gather

- Nothing behind a login, nothing scraped from a platform whose ToS this
  pipeline already treats as off-limits for automation (see
  `14-social-discovery-outreach`'s matrix — the same "don't automate what
  the platform doesn't sanction" logic applies to reading someone's
  private-adjacent content, not just to messaging them).
- Nothing personal and unrelated to the pitch (family, health, anything
  outside their public professional/creative footprint) — this research
  step exists to ground a business pitch, not to build a personal
  dossier. If a detail wouldn't belong in the eventual pitch or its
  reasoning, it doesn't belong in this cache either.

## Record shape

```markdown
# [Handle/name]

researched_at: 2026-07-25
platform_source: [where the public footprint was found]

## What they do
[one or two plain-language sentences, from their own stated description]

## Self-stated needs/gaps (only if genuinely present)
[quote-free paraphrase of what they've said, or: "nothing self-stated
found — role_creation pitches to this target should not claim a
specific gap"]

## Scale/context signal
[solo / small team / established — or "no reliable signal, treat as
unknown"]

## Confidence note
[thin / well-sourced / mixed — same convention as the company cache]
```

## Where this plugs in

Feeds `17-cold-prospecting`'s target-claim gate directly — any
`role_creation` or `service` pitch drafted against an individual target
reads this cache first, and anything the draft says about that person's
situation has to trace back to a line in it.
