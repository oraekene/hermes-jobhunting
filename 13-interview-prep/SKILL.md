---
name: job-hunting-interview-prep
description: "Build interview prep briefs, flashcards, and drills"
metadata:
  hermes:
    tags: [job-hunting, interview-prep, blueprint]
    category: job-hunting
    related_skills:
      - job-hunting-company-research
      - job-hunting-context-architect
      - job-hunting-analytics
    blueprint:
      schedule: "0 9,15 * * 1-6"   # twice daily, business hours — see cron/cron-jobs.md job #9
      deliver: telegram
      prompt: "For every application where interview_request_at is set and either last_interview_prep_at is null or a newer interview_detail email_insights row exists, build (or refresh) the prep brief and flashcard deck per job-hunting-interview-prep's Part 1 and Part 2, then stamp last_interview_prep_at. Deliver each brief as its own Telegram message, not batched. Never start a live study session from this job — that's Part 3, on-request only."
      no_agent: false
---

# Interview Prep

## When this skill applies

Use this skill once an employer has requested an interview, to build a prep brief and spaced-repetition flashcards, and to run live practice/quiz sessions on request. Triggers: interview_request_at newly set on an application (cron), a later round's interview details arriving by email, 'help me prep for the <company> interview', 'quiz me for <company>'. Do NOT use this to research a company from scratch (that's 12-company-research, already cached and reused here) or to draft new STAR stories (that's 07-context-architect) — this skill assembles and rehearses what already exists, it doesn't originate new career content.

This was a stub (see `HERMES_UPGRADE_CHANGELOG.md` for when it was
built out). The seam it plugs into hasn't changed since the stub was
written: `12-company-research`'s own "What this skill does not do"
section and `shared/email-insight-extraction.md` both named this exact
gap before there was anything here to fill it. What follows is the real
skill.

## Two separate things this skill does — don't conflate them

1. **Build** (Part 1 + Part 2) — assembling the brief and creating
   flashcards. This can run unattended, triggered by cron. Nothing here
   needs Kene present.
2. **Study** (Part 3) — an actual practice session, question-by-question,
   graded on Kene's free-text answers. This is `memento-flashcards`'
   own interaction model and it is **inherently live** — it cannot run
   from a cron job, because it needs Kene's answer before it can grade
   it and move to the next question. Never attempt to "batch" a study
   session or simulate Kene's answers to pre-fill the review.

Getting this boundary right matters the same way it mattered for
`10-approval-and-submit`'s delegate_task boundary — a build step that
accidentally waits on live input stalls a cron job; a study session that
accidentally runs unattended isn't a study session, it's the agent
grading itself.

## Trigger conditions

- **Cron** (see frontmatter blueprint, and `cron/cron-jobs.md` job #9):
  gated by `13-interview-prep/scripts/interview-prep-wake-gate.py`,
  which wakes when an application has `interview_request_at` set and
  either has never had a brief built, or has a newer
  `interview_detail` row in `email_insights` than its last build —
  which is how a second/third round with fresh interviewer or format
  details gets a refreshed brief instead of a stale one. This is a pure
  DB-state check, no network calls, so unlike the discovery wake-gate it
  has no "source type I can't cheap-check" caveat — when it says skip,
  that's a confirmed skip.
- **On request**: `00-orchestrator` routes "help me prep for the Acme
  interview" or similar here. If no brief has been built yet for that
  application, run Part 1 + Part 2 first, then offer Part 3.
- **On request, study only**: "quiz me for Acme" when a brief already
  exists — skip straight to Part 3.

## Part 1 — Build the prep brief

Inputs, all already sitting in the pipeline's own data — this stage
originates nothing new about Kene's career, it assembles what's already
there:

- `12-company-research`'s cache for this employer (`shared/
  company_research_cache/{company_slug}.md`). Check freshness per that
  skill's own 90-day rule; re-run its research process if stale rather
  than duplicating that logic here.
- Every `email_insights` row for this `application_id` with `category
  IN ('interview_detail', 'feedback')` — interviewer name(s), stated
  format, focus areas, round number, platform, anything a human already
  told Kene in writing.
- `09-risk-tactics-gate`'s change-log for the actual package sent for
  this application — what claims were made, which tactics were applied
  (exact-phrase mirrors, a title match, anything `[UNVERIFIED]`). An
  interviewer can ask about anything on the resume Kene actually sent;
  he should walk in knowing exactly what that was, not re-reading his
  own resume cold.
- `02-jd-parser`'s original structured JD analysis for this
  application — the stated requirements and culture signals this
  specific interview is likely to probe.
- `shared/question_bank.yaml` for this company/title, **and**
  `07-context-architect/references/gap-analysis-engine.md`'s output for
  this specific application — gaps that engine already flagged are
  exactly what an interviewer is likely to probe.
- `shared/interview_intel_cache/` — the role/industry/company interview
  scrub described below. New; see `references/interview-intel-research.md`.

Note on the company cache: as of the addendum pass it also carries
candidate/employee sentiment from Glassdoor, Reddit, and social sources
(see `12-company-research/ADDENDUM.md`), plus reported interview style.
This stage inherits that for free — do not re-research it from scratch.

### Interview intelligence — role, industry, and company scrub

Runs **before** the brief is assembled, and is cached so it is not
repeated per-application. Scrub YouTube, Reddit, LinkedIn, blogs,
professional/industry platforms, and the company's own blog, careers
pages and posts for guides, techniques, and — the part that matters
most — **actual questions asked and reportedly good answers**.

Three scopes, not one, because they are genuinely different research
passes with different cache lifetimes: this job title/role in general;
this title within this specific industry; and this specific company
where findable. See `references/interview-intel-research.md` for the
full process, cache shape, and the same never-fabricate discipline
`12-company-research` already established.

Where the same question shows up in more than one source, that is a
real signal it is worth over-preparing for.

**Never lift a reported "preferred answer" verbatim from the scrub into
the brief.** Suggested answers map to an existing
`memory/star-story-bank.md` entry or they are marked as missing — see the
reference file's own rule. If no STAR entry fits a likely question, say
so plainly rather than papering over the gap; the same
flag-it-for-the-human principle Rule 2 applies elsewhere.

### Interviewer research — new, and deliberately scoped

If an interviewer's full name is known (from an `email_insights`
`interview_detail` row — the interviewer gave Kene their own name in a
professional context), look up their **public professional
information only**: their role and background as they present it
professionally (LinkedIn-style bio, the company's own team/bio page,
anything they've published or spoken about publicly). This is the same
category of research most candidates already do themselves before an
interview — same spirit as `12-company-research`, applied to a person
instead of a company, with the same discipline:

- **Never fabricate.** If nothing public turns up beyond a name, the
  brief says so plainly — "no additional public information found on
  [name]" is a valid, honest result.
- **Never go beyond public, professional-context information.** Job
  title, professional background, public writing/talks, publicly
  stated areas of focus. Not personal life, not anything requiring a
  login or paid people-search service, not speculation about someone's
  views or character from indirect signals. If the only public
  information is thin, say it's thin — don't pad it out with inference
  presented as fact.
- **Same confidence-note discipline as `12-company-research`'s cache
  format** — state how solid the finding is, don't present a guess with
  the same weight as a confirmed fact.
- Cache the result at `shared/company_research_cache/{company_slug}
  __interviewers.md` (same directory, a distinct suffix so it never
  collides with or gets overwritten by the company-level cache file),
  keyed by interviewer name so a second round with the same person
  doesn't re-research them.

### Build steps

1. Gather the four input sources above plus interviewer research if
   applicable.
2. Write the prep brief (format below) to
   `shared/interview_prep/{application_id}_{company_slug}.md`.
3. Build the flashcard deck (Part 2).
4. Deliver the brief via Telegram — the full markdown brief plus a
   one-line pointer to Part 3 ("say 'quiz me for Acme' when you're ready
   to practice"). Use `[[as_document]]` if the brief is long enough that
   Telegram would otherwise truncate or reflow it awkwardly; a short
   brief can go inline.
5. Stamp `applications.last_interview_prep_at = now()` for this
   application — this is what stops the wake-gate from rebuilding on
   every subsequent tick until a genuinely new round's details arrive.
6. **Optional — calendar hold**: if `productivity/google-workspace` is
   installed with Calendar scope (see `security/email-integration-
   setup.md` for why this pipeline defaults to himalaya for email and
   leaves Calendar as a separate opt-in) and `interview_date` is known,
   offer to create a calendar hold — do not create it without an
   explicit yes, per that skill's own confirm-before-create rule:
   `$GAPI calendar create --summary "Interview: <Company> <Role>"
   --start <ISO8601> --end <ISO8601+1h>`. If Calendar isn't installed,
   skip this step silently — it's a nice-to-have, not a dependency.

### Brief format

```markdown
# Interview Prep — {Company} — {Role Title}

## Logistics
- Round: [phone screen / panel / technical / onsite / unknown]
- Format/platform: [Zoom / phone / on-site / unknown]
- Interviewer(s): [name(s), or "not yet known"]
- Scheduled: [date/time if known, else "not yet scheduled"]

## What they do (from company research)
[from the cache — one or two sentences]

## What's likely to come up (from the JD)
[the posting's stated requirements/culture signals most relevant to an
interview, not a re-paste of the whole JD analysis]

## What you actually claimed (from the risk-tactics gate change-log)
[every applied tactic on the sent package — exact phrases mirrored,
any title match, anything flagged UNVERIFIED — Kene should be ready to
speak to every one of these, not surprised by a question about them]

## What's already known about this interview (from email)
[every interview_detail / feedback row for this application]

## Reported questions for this role (from the intel scrub)
[cross-referenced across question_bank.yaml, gap-analysis-engine output,
and interview_intel_cache — questions appearing in more than one source
marked high-confidence, each mapped to a STAR entry or flagged as having
no matching story yet]

## Reported format signal (unconfirmed)
[anything the scrub reports about this company's process that
email_insights has not yet confirmed — e.g. "candidates report a
take-home before the onsite" — held as unconfirmed until it is]

## Interviewer notes
[public professional background if a name is known, or "no interviewer
name known yet"]

## Practice
Flashcard deck: "Interview - {Company} - {Role} - {application_id}"
({N} cards). Say "quiz me for {Company}" when ready.
```

## Part 2 — Flashcard generation (`productivity/memento-flashcards`)

**Collection naming**: `Interview - {Company} - {Role Title} -
{application_id}` — the application id keeps two applications to the
same company from colliding, and makes `delete-collection` a clean way
to retire a deck once the process for that specific application ends
(offer, rejection, or Kene says he's done with it — never delete
automatically).

**What becomes a card** — three categories, not an undifferentiated
dump of everything available:

1. **Confirmed Q&A, filtered for relevance.** Read `memory/star-story-
   bank.md`'s variant-table extension (the confirmed `qb_XXXX` answers
   `07-context-architect`'s interview loop already built) and pull the
   subset relevant to this role/company — same relevance filtering
   `07-context-architect/references/gap-analysis-engine.md` already
   applies, reused here rather than re-derived. Card front: the
   question as asked (`qb_XXXX`'s text). Card back: Kene's own
   confirmed answer (the matching variant if one exists, e.g. company-
   stage-matched; the general answer otherwise). If `shared/
   question_bank.yaml` doesn't exist yet (Kene hasn't run the one-time
   crawler setup — see `07-context-architect/references/HOW-TO-RUN.md`),
   skip this category and say so in the brief rather than erroring. If
   the Holographic memory layer is configured (optional — see
   `07-context-architect/references/holographic-memory-layer.md`),
   `fact_store(action="probe")` on the company/project name can surface
   an atomic fact worth its own card too — a supplement to the variant
   table, not a replacement for it.
2. **Company facts.** 2–4 cards built from the company-research cache —
   "What does {Company} do, in one sentence?", "What's {Company}'s
   stage/size signal?", pulling the answer straight from the cache file
   so Kene isn't caught blank on something already sitting in the
   pipeline's own data.
3. **Claims-verification cards.** One card per tactic in the
   risk-tactics-gate change-log for this application — front: "What did
   you claim about X on this resume?", back: the exact phrase/title
   used plus the evidence it was backed by (or the `[UNVERIFIED]` note
   if it wasn't). This is the category that exists specifically so Kene
   never gets asked "tell me more about X" on a claim he doesn't
   immediately recognize as his own.

**Build procedure** — call the script directly, once per card:

```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py add \
  --question "Why do you want to work here?" \
  --answer "<Kene's confirmed answer, or the relevant variant>" \
  --collection "Interview - Acme - Product Manager - 42"
```

Don't create duplicate cards on a rebuild (Part 1 step 6 above can fire
more than once per application, for later rounds) — check `memento_cards.py
list --collection "<same name>"` first and only add cards for genuinely
new content (a new claims-verification card for a tactic that wasn't in
scope at round 1, for instance), not the whole deck again.

## Part 3 — Study session (live, on-request only)

Triggered by "quiz me for {Company}" or equivalent. Follow
`memento-flashcards`'s own review flow **exactly**, without
modification:

```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py due \
  --collection "Interview - Acme - Product Manager - 42"
```

Then the exact question → wait for free-text answer → grade → tell Kene
the correct answer and how he did → rate the card → next question loop
that skill's own `SKILL.md` specifies. This skill does not reimplement
that flow or shortcut any step (skipping the "tell Kene the correct
answer" step, for instance, is explicitly called out as never-skip in
that skill's own docs). If no cards are due (everything's been reviewed
recently per the spaced-repetition schedule), say so and offer to review
anyway rather than ending the conversation flat.

## Part 3b — Questions with no story behind them

Part 1 flags likely questions that map to no `memory/star-story-bank.md`
entry. Until now that flag was the end of the road: the gap was reported
honestly and then sat there. A question you cannot answer is the most
useful thing prep can find, and it was the one thing prep did nothing
with.

Route it to `07-context-architect` as an elicitation request. **Not** to
be answered for Kene — that is the fabrication line and it does not move.
What gets supplied is *structure*, and the structure is public knowledge
about how such questions are assessed, not content about his life:

> No story on file for "a time you disagreed with a senior stakeholder
> and were later proved right."
>
> A strong answer to this needs four things: a disagreement with real
> stakes, your reasoning at the time (not with hindsight), what you
> actually did about it, and how it resolved — including whether you
> were right for the reason you thought.
>
> Two candidates from your own records that might fit that shape:
> — Journal, 2025-11-04: the forecasting methodology pushback
> — Timeline: the vendor migration you argued against in 2024
>
> Does either of these actually fit? If so, tell me what happened and
> I'll draft a STAR entry for you to confirm.

Three rules keep this on the right side of the line:

- **Candidates come from Kene's own records** — the journal, the career
  timeline, the STAR bank's existing entries — never invented and never
  drawn from the intel scrub's reported "preferred answers". The scrub
  says what other candidates reportedly said; that is other people's
  material.
- **Structure is not content.** "This question is testing whether you can
  disagree without escalating" is an observation about the question.
  "You handled that well" is a claim about Kene, and only he can make it.
- **A confirmed answer becomes a STAR entry** through
  `07-context-architect`'s normal Rule 5 write path, which means it is
  available to every future application rather than just this interview.
  This is the payoff: an unanswerable question is a permanent gap in the
  bank, and closing it once closes it for good.

If Kene says neither candidate fits and nothing else comes to mind, record
that honestly — the gap is real, and going into the interview knowing
which question you have no answer for is materially better than being
surprised by it. Do not keep pushing for a story that is not there.

## Part 4 — Post-interview

Two things, not one:

- **Log the outcome and the debrief.** The schema's existing outcome
  fields (`second_round_at`, `final_round_at`, etc.) plus a new
  `interview_debrief` entry capturing Kene's own read of how it went —
  the kind of detail the README's cross-session-recall section flags as
  easy to lose when it is only ever said in passing.
- **Draft a thank-you note** using
  `14-social-discovery-outreach/references/cold-dm-email-schema.md`
  (`trigger.type: interview_thank_you`), through whatever channel the
  interview actually used. Same draft-then-approve discipline as any
  other outreach. If that channel is LinkedIn, check the platform matrix
  first: replying in an existing thread is a different risk profile than
  cold outreach, but this skill still stages it for approval rather than
  treating the difference as licence to auto-send.

## Where this plugs in

- `applications.last_interview_prep_at` — new column, see `shared/
  applications_db_schema.sql`'s migration note if upgrading an existing
  database.
- `00-orchestrator`'s routing table now includes this stage — see that
  skill's own pipeline-stages table.
- `cron/cron-jobs.md` job #9 — the blueprint above is what
  `/suggestions accept` runs. **It does not schedule itself.**
  `tools/blueprints.py` registers a *suggestion*; `cron/suggestions.py`
  is consent-first, caps pending proposals at 5, and latches dismissals
  by `dedup_key`. Nothing here is ever auto-scheduled — this job, and the
  discovery/sweep/weekly-review blueprints alongside it, all wait in
  `/suggestions` until Kene accepts them.

  Worth stating precisely rather than loosely, because the loose version
  causes a specific failure: a user who believes four jobs are already
  running will never open `/suggestions`, will see nothing fire, and will
  conclude the pipeline is broken when it is simply waiting for consent.

## Part 3c — The pressure drill (A7)

The gap between *can recall the story* and *can hold the story up under
pressure* is exactly what a real interview tests, and Parts 3 and 3b test
only the first. A flashcard session confirms Kene knows his material. It
cannot tell him what happens when an interviewer says "that sounds like
your team's win, not yours" and waits.

Opt-in per session, never the default, never scheduled. Kene asks for it.

**How it runs.** Same voice-first interaction as Part 3
(`voice-interview-mode.md`). Kene gives a STAR answer; the drill responds
as a sceptical interviewer would, then follows the thread:

- **Attribution pressure** — "what did *you* do, specifically, as opposed
  to the team?" The single most common real follow-up and the one most
  STAR answers are weakest against.
- **Number pressure** — "where does 40% come from? Measured against
  what baseline, over what period?" Directly useful: a number Kene can't
  source is one `09-risk-tactics-gate` should have caught, and this finds
  the survivors.
- **Counterfactual** — "what would have happened if you'd done nothing?"
- **The failure ask** — "tell me about the version of this that didn't
  work."
- **Silence.** After a complete answer, the drill sometimes just waits.
  Interviewers do this and it makes people talk past their own point.

**Rules, because this mode has an obvious way to go wrong.**

1. **Sceptical, not hostile.** Sharp follow-ups on the substance of a
   claim. Never contempt, never personal, never a stress-interview
   performance. The name for this section is "pressure drill" rather than
   "hostile interviewer" deliberately — the version that simulates
   rudeness teaches nothing about the answers and just feels bad.
2. **Never against protected characteristics or personal circumstances.**
   Real interviewers occasionally ask illegal questions; simulating them
   is not preparation, it is rehearsing a bad afternoon. If Kene
   specifically wants to practise *deflecting* one, that is a different,
   narrower request he has to make explicitly.
3. **Three follow-ups maximum per story**, then stop and debrief. The
   point is finding the weak joint, not winning.
4. **It ends with what to fix, not with a score.** Which claims survived,
   which need a number, which need the "I" separated from the "we". Those
   route back to `07-context-architect` as story revisions under Rule 5 —
   this skill still originates nothing.
5. **Read the room.** If Kene is prepping for something tomorrow and the
   drill is going badly, say so plainly and stop. Shaking someone's
   confidence the night before an interview is a real cost and the drill
   is not worth it.
6. **Never from cron.** Same rule as Part 3, for stronger reasons.

**Where it gets its material.** Kene's own STAR bank, plus
`references/interview-intel-research.md`'s scrub where the target
employer is known to interview a particular way. A company reported to
press hard on metrics gets a drill weighted toward number pressure.

## What this skill does not do

Doesn't originate new STAR stories or career facts (that's still
`07-context-architect`'s job alone, per Rule 5 — if a study session
surfaces that Kene wants a genuinely new story on record, route back to
that skill, don't improvise one here). Doesn't research anything beyond
public, professional-context information about an interviewer. Doesn't
run a live study session from cron, ever. Doesn't delete a flashcard
collection automatically — that's Kene's call, once he's actually done
with a given application's process.

On interviewer research specifically, the boundary is worth stating in
both directions, because the addendum pass drew it more tightly than
this skill does: scraping an interviewer's *personal* social profiles
for prep is a meaningfully more invasive use of social discovery than
job-lead discovery, and stays out of scope. What is in scope is the
public, professional-context information described in Part 1 — the same
thing most candidates look up themselves. The two positions reconcile:
what the addendum excluded is exactly what this skill already forbids.

## Reference files

- `references/interview-intel-research.md` — the scrub process, cache
  shape, and sourcing discipline for role/industry/company interview
  intelligence.
- `07-context-architect/references/voice-interview-mode.md` — reused for
  the live drill interaction pattern rather than defining a second
  interview-style interface.
- `14-social-discovery-outreach/references/cold-dm-email-schema.md` — the
  thank-you-note record shape.
