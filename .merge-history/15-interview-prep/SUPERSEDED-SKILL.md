---
name: job-hunting-interview-prep
description: "Build interview prep briefs, flashcards, and drills"
---

# Interview Prep

## When this skill applies

Use this skill once an application reaches interview_request_at (per shared/applications_db_schema.sql), or on direct request ('help me prep for the Acme interview'). Builds a prep brief from data this pipeline already collects — company research cache, email_insights, the JD, the resume/cover letter actually sent, and the risk-tactics change-log — then optionally runs a live mock-interview drill. Also drafts the post-interview thank-you note via 14-social-discovery-outreach's cold-dm-email-schema. Triggers: interview_request_at set on an application, or Kene asking for interview prep directly. Do NOT invent claims about Kene's background that aren't already in memory or the sent application — this skill preps him to defend what was actually said, not to improvise new material under pressure.

Replaces the `13-interview-prep` stub. **A note on origin, for honesty's
sake**: Kene asked this skill to borrow from what he'd already designed
for Job-Ops's interview feature set, but that design wasn't available to
pull from directly in this pass — this build instead follows the exact
seam the stub itself had already documented (see below), plus ordinary
interview-prep practice. If the Job-Ops version has specifics worth
carrying over — a particular drill format, a scoring rubric, question
categories — share that and this skill can be tightened to match it
rather than drift as a second, slightly different design.

## What already exists for this stage, unused until now

Exactly what the stub named, still accurate:

- `12-company-research`'s cached research for the employer (90-day
  cache) — as of this pass, that cache now also carries candidate/
  employee sentiment from Glassdoor, Reddit, and social sources (see
  `12-company-research/ADDENDUM.md`), so this skill inherits that for
  free without any change on its own end.
- Every `email_insights` row for the application where `category IN
  ('interview_detail', 'feedback')` — interviewer names, stated format,
  focus areas, anything a human already told Kene in writing.
- The original JD (`02-jd-parser`) and the resume/cover letter actually
  sent, plus `09-risk-tactics-gate`'s change-log for that application —
  worth knowing exactly which claims went out, since an interviewer may
  ask about any of them directly.
- `shared/question_bank.yaml` and `07-context-architect/references/
  gap-analysis-engine.md`'s output for that application.
- **New this pass**: `shared/interview_intel_cache/` — a role/title/
  industry-scoped scrub of what's publicly known about interviewing for
  this kind of role, and for this specific company where findable. See
  `13-interview-prep/references/interview-intel-research.md`. This is the single biggest
  addition to this skill since it was first built — everything below
  reflects it.

## Process

1. **Trigger**: `interview_request_at` gets set on an application row, or
   Kene names a company/role directly.
2. **Interview intelligence gathering** (new — runs before the brief is
   assembled, cached so it's not repeated per-application): scrub
   YouTube, Reddit, LinkedIn, blogs, professional/industry platforms,
   and the company's own blog/careers pages/posts for guides, tutorials,
   techniques, and — the part that matters most — **actual questions
   asked and reportedly good answers**, for this job title/role in
   general, for this title within this specific industry, and for this
   specific company where findable. Three scopes, not one, because
   they're genuinely different research passes with different
   cache lifetimes — see `13-interview-prep/references/interview-intel-research.md` for the
   full process, cache shape, and the same "never fabricate" discipline
   `12-company-research` already established.
3. **Assemble the brief** — one document, not a data dump:
   - Company snapshot (from the `12-company-research` cache, now
     including candidate/employee sentiment and reported interview
     style — do not re-research from scratch; that cache exists
     specifically so this stage doesn't repeat work).
   - Role recap and the specific requirements this application targeted.
   - **The claims map**: every claim `09-risk-tactics-gate` passed or
     flagged for this application (exact-phrase matches, title framing,
     any `[UNVERIFIED]`-flagged item under `balanced`/`embellish` fidelity
     mode) — Kene should walk in knowing exactly what the paper trail
     already says, so nothing he's asked about contradicts what was sent.
   - Likely questions: now three sources cross-referenced, not one —
     `question_bank.yaml` for this company/title, `gap-analysis-engine.md`'s
     output for this specific application (gaps it already flagged are
     exactly what an interviewer is likely to probe), and the new
     `interview_intel_cache` scrub's actual reported questions for this
     role/industry/company. Where the same question shows up in more
     than one source, that's a real signal it's worth over-preparing for.
   - For each likely question, a suggested answer *mapped to* an existing
     STAR-bank entry (`memory/star-story-bank.md`) — never a fresh answer
     invented for this brief, and never a "preferred answer" lifted
     verbatim from the intel scrub either (see the reference file's own
     rule on this). If no STAR entry fits a likely question, say so
     plainly rather than papering over the gap — same "flag it for the
     human instead of hiding it" principle Rule 2 already applies
     elsewhere.
   - Logistics: format, interviewer name(s), anything else pulled from
     `email_insights`, plus any reported-format signal from the intel
     scrub (e.g. "candidates report a take-home before the onsite") that
     `email_insights` hasn't confirmed yet — flagged as unconfirmed until
     it is.
4. **Optional mock-interview drill** — reuses the interaction pattern
   already built for `07-context-architect/references/voice-interview-mode.md`
   (a live back-and-forth, not a static Q&A list) rather than inventing a
   second interview-style interface. The question set the drill pulls
   from is now the same cross-referenced list built in step 3, not just
   `question_bank.yaml` alone — so a drill session is, in effect,
   rehearsing against the actual questions this role/company is reported
   to ask, not a generic behavioral-question set. Hermes asks a likely
   question, Kene answers, Hermes checks the answer against the mapped
   STAR structure (Situation/Task/Action/Result present? quantified
   where the sent resume already quantified it? consistent with the
   claims map?) and flags gaps or drift — not a pass/fail score, a
   "here's what's thin" note.
5. **Post-interview** — two things, not one:
   - Log outcome fields already in the schema (`second_round_at`,
     `final_round_at`, etc.) plus a new `interview_debrief` entry (see
     the schema addendum) capturing Kene's own read of how it went —
     this is exactly the kind of detail the README's "cross-session
     recall" section already flags as easy to lose if it's only ever
     said in passing rather than logged.
   - Draft a thank-you note using `14-social-discovery-outreach`'s
     `cold-dm-email-schema.md` (`trigger.type: interview_thank_you`) —
     same draft-then-approve discipline as any other outreach, sent
     through whatever channel the interview actually used (usually
     email, sometimes LinkedIn — check the matrix if it's LinkedIn:
     replying to an existing thread is a very different risk profile
     than cold outreach, but this skill still stages it for approval
     rather than assuming that difference makes it safe to auto-send).

## What this stage still doesn't do

Same boundary the stub already drew, worth restating: no research on
individual interviewers beyond what's already in `email_insights` or the
company-research cache (that's a `12-company-research`-adjacent gap, not
this skill's job to close by scraping someone's personal social profiles
for interview prep — a meaningfully different, more invasive use of
social discovery than job-lead discovery, and out of scope here even
though `14-social-discovery-outreach` exists).

## Reference files

- `13-interview-prep/references/interview-intel-research.md` — the new scrub process, cache
  shape, and sourcing discipline for role/industry/company interview
  intelligence.
- Reuses `07-context-architect/references/voice-interview-mode.md` for the
  drill interaction pattern rather than defining a new one.
- `14-social-discovery-outreach/references/cold-dm-email-schema.md` for
  the thank-you-note record shape.
