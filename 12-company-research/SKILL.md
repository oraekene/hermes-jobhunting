---
name: job-hunting-company-research
description: "Research an employer beyond what the job posting says"
metadata:
  hermes:
    tags: [job-hunting, company-research]
    category: job-hunting
    related_skills:
      - job-hunting-discovery
      - capability:interview_prep
      - capability:cold_outreach
---

# Company Research

## When this skill applies

Use this skill to gather and cache what's publicly known about a specific employer — mission/values language beyond what the JD quotes, recent news (funding, launches, leadership changes), product/market position, and company stage — for use by resume tailoring, cover letters, application Q&A, and STAR-story-variant selection. Triggers: being handed a company name by 02-jd-parser's output, 'research this company', or any downstream skill needing a fact it doesn't have cached. Runs once per company, not once per application — check the cache first. Do NOT use this to verify claims about Kene himself (that's 09-risk-tactics-gate) — this skill only researches the employer.

Origin: a gap found by checking the built pipeline against
`06-cover-letter/references/cover-letter-formula.md`'s own requirement
for the Hook paragraph — "something concrete (a product, a mission, a
public challenge they're facing)." **No skill anywhere in the pipeline
actually goes and finds that.** `02-jd-parser` only captures values
language the posting itself states verbatim; everything past that has
been an unstated dependency on whatever the model already happens to
know about the company. This skill makes that dependency explicit and
real.

## Cache first, always

Research is per-**company**, not per-application — if Kene applies to
the same company twice, don't re-research. Check
`shared/company_research_cache/{company_slug}.md` first:

- **Missing** → run the research process below.
- **Present, `researched_at` within 90 days** → use as-is.
- **Present, older than 90 days** → re-run, since funding/leadership/
  product-stage signals go stale (a "Series A startup" from 14 months
  ago may not be one anymore).

## Research process

1. Start from what `02-jd-parser` already extracted for this
   application — company name, stated values, section headers. Don't
   re-derive what's already sitting in the JD analysis.
2. Gather, using whatever search/browse capability is configured
   (Nous Tool Gateway's web search if Kene's on a paid Nous Portal
   plan, or the same browser-automation tooling already wired in for
   `10-approval-and-submit`'s form-filling, pointed at read-only pages
   instead — either works, this skill doesn't need a specific one).
   Two optional skills worth having installed for this step specifically:
   `research/scrapling` (stealth browsing, Cloudflare bypass) for
   JS-heavy About/Values pages that a plain fetch can't render, and
   `research/parallel-cli` (agent-native web search, deep research, and
   enrichment) as a premium alternative to generic web search if
   configured — neither is required, both just make this step more
   reliable/deeper when available:
   - The company's own About/Mission/Values page, if distinct from what
     the JD already quoted. **Record the company's own primary domain**
     while you're there (e.g. `acme.com`, not the job board's domain the
     posting was found on) — step 2.5 below needs it, and nothing
     upstream of this skill captures it as structured data today.
   - Recent news — funding round, product launch, layoffs, leadership
     change — **scoped to roughly the last 12 months**; older news is
     usually stale enough to skip.
   - A one-line plain-language summary of what the company actually
     makes or does, independent of its own marketing language.
   - Rough company stage/size signal (headcount order of magnitude,
     funding stage if known, public vs. private) — this directly feeds
     the `company_stage` dimension in
     `07-context-architect/references/answer-variants.md`, and is also
     what step 2.5 below cross-checks its own signal against.
   - Named competitors or market position, if findable without
     stretching.

### Step 2.5 — Passive domain signal (optional, `research/domain-intel`)

If the `research/domain-intel` optional skill is installed, run it
against the domain recorded in step 2 — this is entirely passive
(certificate-transparency logs, WHOIS, DNS; no port scanning, no active
probing beyond one TLS handshake) and free, so there's no cost reason to
skip it when it's available. If it isn't installed, skip this step
entirely and say nothing about it in the cache file — don't apologize
for a capability that was never claimed.

1. `python3 SKILL_DIR/scripts/domain_intel.py whois <domain>` — read
   `creation_date` if present, and compute how long ago that was
   yourself; the script reports days remaining until *expiration*, not
   age since creation.
2. If `whois` fails outright, times out, or has no `creation_date` field
   (some registrars format output outside what the script's regex
   expects, and WHOIS's TCP:43 is blocked on some networks — an absence
   here is a coverage gap, not a signal by itself, and should never be
   read as suspicious on its own), fall back to
   `python3 SKILL_DIR/scripts/domain_intel.py ssl <domain>` and use
   `not_before` as a **weaker, secondary** proxy — a fresh SSL
   certificate is at least as likely to be an ordinary renewal on a
   long-standing domain as evidence of a newly-registered one, so label
   it accordingly if this is the only signal available.
3. **Cross-check the age against the stage/size signal from step 2
   before writing anything** — this is the step that actually makes the
   signal useful rather than noisy. A domain registered a few months ago
   is unremarkable for a company step 2 already identified as an
   early-stage startup; the same finding for a posting claiming to be
   from an established/enterprise employer is the combination worth
   flagging. Age alone, with no context, produces false alarms on
   ordinary new companies.
4. Write a plain-language note, never a verdict. No "SCAM" flag, no
   percentage score — something like "domain registered ~3 weeks ago,
   which is unusual paired with this posting's claim of being an
   established 500-person company; worth a second look before investing
   time" or, the ordinary case, "domain registered 2014, consistent with
   an established company; no notable signal." Kene makes the call, this
   skill surfaces what it found.

2.6. **Candidate and employee sentiment.** Alongside the sources above,
   pull from Glassdoor and similar review aggregators, Reddit (company-name
   searches and relevant subreddits), LinkedIn posts and comments
   mentioning the company from people who *don't* work there — the
   company's own page is already covered by the About/Mission step — and
   general social search. Three things to look for:

   - What it is actually like working there, from people who have: pace,
     management style, how decisions get made. The things a mission
     statement would never say about itself.
   - What they actually look for in candidates, by role or title where
     findable — patterns across interview reviews and hiring posts, not
     a restatement of the JD's requirements.
   - Interview process and style: format, number of rounds, reputation
     for speed, technical depth, whatever candidates have reported. This
     overlaps `capability:interview_prep`'s deeper role-specific scrub, but the
     company-general slice belongs here, in the shared cache, because it
     is useful the moment a company name exists rather than only once an
     interview is scheduled.

   Where a source genuinely needs a logged-in read to be useful —
   LinkedIn especially — `shared/site-access-model.md` says which access
   model applies. Review-aggregator content is self-selected by nature;
   people with strong opinions post more than people with none. That
   caveat is already stated in "What this skill does not do" below and
   is not loosened here — it now simply has something to attach to.

2.7. **Video sources** (`media/youtube-content` — transcripts, summaries).
   Text search misses a whole class of high-signal material: earnings
   calls, conference talks by people on the team, engineering-blog video
   posts, and founder interviews. A hiring manager's conference talk says
   more about how they think than any About page will.

   Transcripts, not viewing — this is a text pipeline. Worth the pass
   when the company is public (earnings calls state strategy and headcount
   plans directly) or when a named interviewer has spoken publicly. Not
   worth it as a default sweep on every company: the yield is
   concentrated in a small number of targets and the cost is not.

   Same sourcing discipline as everything else here: a claim from a
   transcript is attributed to the talk, and an unclear transcript is a
   gap, not a licence to paraphrase loosely.

3. **Never fabricate a finding.** If nothing turns up beyond the JD
   itself, the cache file says so explicitly — "no additional signal
   found beyond the JD" is a valid, honest result and downstream skills
   need to know that rather than getting a confident-sounding paragraph
   built on nothing. A hook built on a fabricated detail is worse than
   a generic one; it's a fabrication risk in exactly the kind of
   external-facing document this pipeline already gates carefully.
4. Write `shared/company_research_cache/{company_slug}.md`:

```markdown
# Acme Corp

researched_at: 2026-07-24

## What they do
[one or two plain-language sentences]

## Stage/size signal
[e.g. "Series B, ~180 employees per LinkedIn, per a Feb 2026
TechCrunch funding piece" — cite what kind of source, not a fabricated
specific if the signal is genuinely weak: "no reliable signal found;
treat as unknown, don't assume a variant"]

## Recent news (last ~12 months)
- [item, with rough date]

## Values/mission language beyond the JD
[only if genuinely found beyond what 02-jd-parser already captured —
otherwise: "nothing beyond the JD's own stated values"]

## Competitors / market position
[if findable]

## Domain signal (optional — only present if `research/domain-intel` is installed)
[plain-language note per step 2.5 — e.g. "domain registered 2014,
consistent with an established company; no notable signal," or the
flagged case with the cross-check against the stage/size signal above.
Omit this section entirely rather than including it empty if the skill
isn't installed.]

## Candidate/employee sentiment (Glassdoor, Reddit, social)
[summarised, sourced by source-type rather than URL-dumped — "multiple
Glassdoor reviews describe a fast-paced, self-directed culture" beats a
single quote]

### What they reportedly look for in candidates
[by role/title where findable, otherwise general]

### Interview process/style, as reported
[format, rounds, pace, difficulty — company-general; the role-specific
version lives in capability:interview_prep's intel scrub]

### Confidence note for this section
[thin / well-sourced / mixed. Self-selected review-site content defaults
toward "mixed" unless corroborated across independent sources.]

## Confidence note
[how solid is this overall — thin/well-sourced/mixed]
```

Deliberately one new section in the **same** cache file, not a separate
sentiment cache. Every existing consumer already reads this file, so
`06-cover-letter`'s hook, `05-resume-customizer`'s stage-informed bullet
selection, `07-context-architect`'s `company_stage`-variant answers and
`08-application-qa`'s motivation and cultural-fit questions all get
richer input the next time they read it, with no change to any of their
own files.

## Where this plugs in

- **`06-cover-letter`**: the Hook paragraph draws from this cache
  instead of an unstated assumption. If the cache says "nothing beyond
  the JD," the Hook falls back to the JD's own stated mission/values
  language rather than inventing specificity — a generic-but-honest
  hook beats a fabricated-but-specific one.
- **`05-resume-customizer`**: the stage/size signal helps decide which
  achievements to foreground (scale-oriented wins for an enterprise
  target, ownership/ambiguity-oriented wins for an early-stage one) —
  same logic as the variant system, applied to bullet selection instead
  of a stored answer.
- **`07-context-architect`'s answer-variants system**: when a bank
  question's `variant_dimensions` includes `company_stage`, this
  skill's stage/size signal is what picks the variant — falling back to
  whatever the JD text alone implies only when this cache has no
  reliable signal.
- **`08-application-qa`**: for the `motivation/career goals` and
  `cultural fit` question categories specifically (not behavioral/
  technical questions, which draw from the STAR bank regardless of
  employer) — "why do you want to work here," "what interests you about
  our mission," "how would you approach [X] here" all read this cache
  before drafting.
- **`09-risk-tactics-gate`**: out of scope for that skill's actual job
  (it verifies claims *about Kene*, not about the employer) — but worth
  a light manual gut-check when reviewing a draft: does a claim like
  "I noticed you recently launched X" match what this cache actually
  found, not a plausible-sounding guess. Not a formal gate, just worth
  knowing the cache exists as a place to check.
- **`10-approval-and-submit`**: if step 2.5's domain signal came back
  flagged as notable (not the ordinary "no signal" case), that note
  goes into the Telegram approval message, near the top, before the
  usual package review — Kene should see it before deciding, not have
  to go dig for it. Say nothing extra when the signal is unremarkable;
  a flag on every application trains Kene to ignore all of them.
- **`capability:interview_prep`**: reads this cache for the company snapshot in
  the prep brief, and for named-interviewer research it does on its own
  (see that skill's own "Interviewer research" section) — a distinct,
  narrower capability than what this skill does, scoped to public
  professional information about a person rather than a company.

## What this skill does not do

Doesn't scrape behind logins, doesn't treat Glassdoor-style review
aggregators as reliable — if used at all, flag them explicitly as "a
review-site signal, treat with the same skepticism as any self-selected
sample" rather than presenting them as fact. Step 2.5's domain signal is
informational only — it never blocks the pipeline or forces a decision;
Kene weighs it the same way he weighs everything else this skill
surfaces. Researching a *specific named interviewer* is
`13-interview-prep`'s job, not this skill's — this skill stays scoped to
the employer as an organization.
