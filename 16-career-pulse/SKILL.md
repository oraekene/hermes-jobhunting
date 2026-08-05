---
name: job-hunting-career-pulse
description: "Keep the career memory bank current between searches"
metadata:
  hermes:
    tags: [job-hunting, career-pulse]
    category: job-hunting
    related_skills:
      - job-hunting-context-architect
      - job-hunting-analytics
      - capability:interests_profile
      - capability:career_planning
---

# Career Pulse

## When this skill applies

Use this skill for anything that keeps Kene's memory bank current between job searches, not just when a specific application surfaces a discrepancy: a scheduled journal check-in, a scan of his explicitly-connected career profiles (LinkedIn, portfolio, GitHub, blog) for changes, or a career-event trigger (new job, new skill, completed project, job loss) that should cascade into other parts of the pipeline. Triggers: the journal cadence cron firing, the profile-monitor cadence cron firing, or Kene mentioning a career update in passing conversation. Do NOT write anything to MEMORY.md/USER.md/target-profile.yaml/the STAR bank directly — this skill surfaces candidate updates, 07-context-architect is still the only skill that writes confirmed facts (Rule 5), unchanged.

Origin: Kene's point that the memory bank should get updated on more than
just "when a discrepancy forces it" — a scheduled rhythm for capturing
both the stuff that lives on explicit platforms (LinkedIn, GitHub,
portfolio) and the stuff that only ever gets said out loud (a resolved
conflict, a lesson learned, a win nobody wrote down anywhere).

Three jobs, each on its own cadence, all feeding the same downstream
target: `07-context-architect`'s confirm-before-write interview.

## 1. The journal check-in

A scheduled, conversational prompt (cron-triggered, cadence Kene sets —
daily is the max useful frequency, a few times a week is a reasonable
default) asking some rotation of: what got hard this week, what got
resolved, what shipped, who you worked with and how it went, what you'd
do differently. Not a form — a normal chat turn, kept short.

- **Raw entries are stored immediately**, before any confirmation step,
  in a new `career_journal` table (see the schema addendum) — this
  mirrors the README's existing distinction between curated memory
  (`MEMORY.md`/`USER.md`, confirmed facts only) and raw session recall
  (FTS5 search over everything actually said). A journal entry has value
  as raw recall even before anything in it becomes a durable fact.
- **Candidate facts get surfaced, not written.** After each entry (or
  batched weekly — Kene's call), this skill flags anything that reads
  like a durable fact ("shipped the migration solo," "picked up
  Kubernetes on that project," "resolved the recurring conflict with
  [vendor] by...") and hands it to `07-context-architect` as a proposed
  addition — same confirm-before-write discipline as every other memory
  write, Rule 5 unchanged.
- **Tone matters here specifically**: keep prompts practical and
  low-key, not performative ("crush any wins lately?") — this runs
  often enough that a forced-upbeat tone gets grating fast, and a bad
  week is exactly as useful to log as a good one.
- **Voice, not just text.** A real week's worth of detail — a conflict
  that took three conversations to resolve, a project that shipped
  after a genuine scramble — is exhausting to type out, especially on
  Kene's Windows/i3 laptop or via Telegram on a phone. Reuses exactly
  the setup `07-context-architect/references/voice-interview-mode.md`
  already documents and configures, not a second voice integration:
  Telegram voice notes are transcribed automatically (`stt.enabled:
  true` by default, `faster-whisper` `local`/`small` model, no API key
  needed) the moment `stt` is configured, regardless of any other mode
  setting — so a journal check-in already works by voice the day that
  file's setup checklist is followed, no separate journal-specific
  voice work required. Same non-default-but-always-available posture
  that file recommends: prompts arrive as text (skimmable, re-readable
  before answering), Kene replies however's easier in the moment —
  typed or a voice note, no mode switch needed.
- **The one safeguard carried over, not re-invented**: voice-interview-
  mode.md's rule that any voice-derived answer containing a number,
  date, or percentage gets echoed back for an explicit confirm before
  anything downstream treats it as fact applies here with equal force —
  a journal entry mentioning "cut latency by 40%" is exactly the kind of
  detail that later becomes a STAR-bank figure, and a mis-transcribed
  number is a mistake that looks identical to a correct one on the page.
  Qualitative journal content (most of it) doesn't need this extra step;
  anything with a figure in it does.

## 2. Explicit-channel monitoring

For each profile Kene explicitly connects (LinkedIn, portfolio site,
GitHub, blog, anything else he names), a lower-frequency scheduled check
for changes since last read, surfaced as a diff digest — "your GitHub
shows two new merged PRs on [repo] since last check, want these folded
into domain-knowledge.md?" — never auto-applied, same Rule 5 discipline.
Feeds two things downstream: ordinary profile updates (as above) and,
where a diff specifically looks status-shaped, employment-status signals
— see "Tracking employment status" below, which now treats this section
as one of its four sources rather than a separate pass.

- **LinkedIn specifically**: this is a *read*, not a send, so it doesn't
  carry the same ban risk `capability:social_listening`'s matrix
  documents for LinkedIn messaging — but scheduled, repeated automated
  reads of the same profile still resemble bot traffic at high enough
  frequency. Prefer LinkedIn's own data-export feature on a monthly-ish
  cadence, or an occasional Kene-triggered fetch of a URL he hands over,
  over a tight automated poll loop.
- **GitHub/portfolio/blog**: no comparable risk, safe to poll more often
  via normal fetch/API means.

## 3. Career-event cascade

The actual point of all this collection: once `07-context-architect`
confirms a genuinely profile-changing fact (new role, new skill, a
completed project that changes Kene's seniority signal, a role ending),
that confirmation should trigger more than just a memory write. This
isn't new philosophy — `07-context-architect/references/title-taxonomy.md`
already documents an "immediately, either cadence: when Kene's target
profile changes significantly" trigger for Phase 1.5's re-run. This
skill is what actually fires that trigger from a `career_journal` or
profile-monitor event instead of only from a hand-edited
`target-profile.yaml`:

- Re-run Phase 1.5 (adjacent/higher-title expansion) against the updated
  profile.
- Flag `shared/dynamic-target-calibration.yaml` for re-evaluation (see
  `shared/dynamic-target-calibration.md`) — a profile-strength change is
  a different trigger than an employment-status change, and both are
  handled there, not here; this skill's job is just to fire the signal.
- If the event is specifically a role change (new job or a role ending),
  prompt Kene directly for `employment_status` — see below.

### Tracking employment status

Answering directly: this is **never inferred and auto-written**. Four
soft signals feed a *prompt*, never a silent conclusion — three from
before, plus explicit-channel monitoring (section 2) now doing its
share too, since Kene specifically wanted status-tracking routed through
there as well, not left to journal/DB signals alone:

- An `applications` row hitting `outcome: offer_accepted` — a strong
  signal, but not proof Kene started, or that he didn't already have a
  separate role end independently.
- Kene stating it directly in a journal entry or ordinary conversation
  (session search catches this even if it's said in passing, same
  pattern the README already describes for other informal disclosures).
- A long stretch with no journal activity and no application outcomes at
  all — the weakest signal, used only to justify asking, never to
  assume an answer.
- **Explicit-channel monitoring itself surfacing a status-shaped
  change** — a LinkedIn headline switching to "Open to work," a current-
  position field changing, a portfolio's "currently at ___" line
  updating. This is section 2's normal diff-digest mechanism, just
  treated as a status signal specifically when the diff looks like one,
  not a separate monitoring pass.

On any of these, the journal cadence (or a separate, lighter monthly
check if the journal itself has gone quiet) asks plainly: **"Still on
the hunt for [current target], or has anything changed since we last
talked?"** — confirmed answer writes `employment_status` and
`status_changed_at` in `dynamic-target-calibration.yaml`, same
confirm-before-write discipline as everything else here. Keep this
question neutral and practical — it's a status check, not a moment to
editorialize either way.

## Reference

- `shared/dynamic-target-calibration.yaml.template` /
  `shared/dynamic-target-calibration.md` — what actually consumes
  `employment_status` and profile-change signals; this skill only
  produces them.

## Deleting an entry, and why there is no permanent archive

Deleting a journal entry soft-deletes it: `deleted_at` is set, and the
entry disappears from the export, the qmd index and every retrieval path
**that same day**. The row survives for a 30-day grace window, then is
really gone.

The obvious alternative — copy deleted entries somewhere permanent so
nothing is ever lost — was considered and rejected, because there are two
reasons an entry gets deleted and they want opposite things:

- **It was wrong.** Recovery is welcome.
- **It held something Kene does not want retained.** Keeping a copy
  somewhere he cannot see or reach is the exact opposite of what he
  asked for, however well-intentioned the copy is, and however
  unreachable it is claimed to be.

A permanent archive serves the first case and betrays the second. And
"somewhere Hermes can never touch" is harder to guarantee than it sounds:
Hermes has filesystem and shell access, so any local path is reachable,
and any cloud store whose credentials the agent holds is reachable too.
Genuine unreachability means credentials the agent never sees — which is
a real option, but it is a *backup* decision, not a journal feature.

Accidental loss is already covered, and covered better:
`security/backup-and-recovery.md` keeps 7 daily, 13 weekly and 12 monthly
versioned snapshots, encrypted, under Kene's control. The important
property there is the one an archive lacks — **they expire**. Recovery
should be bounded, not eternal.

`delete_reason: private` is the flag that matters. It means hard-delete on
schedule and never prompt about recovery. Kene said remove it, not remind
him about it.

## Journal retention

Check-ins run three times a week indefinitely. At two years that is
roughly 300 entries feeding every export, every embed and every semantic
search.

Entries older than four quarters collapse into one
`career_journal_summary` row per quarter — count, date range, a summary,
and the ids of the entries it replaced. Recent quarters stay verbatim.
Same principle as `07-context-architect/references/star-bank-aging.md`:
detail decays with age, nothing becomes invisible, and the collapsed
period is still searchable as a period.

Collapsing is a **propose-and-confirm** step under Rule 5, not an
automatic rewrite. The journal is Kene's own account of his working life;
summarising four quarters of it without asking is not a maintenance task.

## What a recruiter finds when they search you (S9)

This package spends real effort finding information about other people —
`capability:contact_enrichment` runs `sherlock` across hundreds of platforms and
buys lookups from data brokers. The inverse was never asked: **what does
a hiring manager find when they run the same search on Kene?**

Recruiters do search. Data-broker profiles are a routine result, and they
routinely carry an outdated employer, a wrong location, or a home address
Kene never chose to publish. None of that is illegal for them to hold; it
is simply available, and it shapes an impression before any conversation.

`security/unbroker` submits opt-out and removal requests to data-broker
sites. Run it as a **standing quarterly item**, not a one-off: brokers
re-scrape, so a removal is a maintenance task rather than a fix.

Two boundaries worth naming, because this could easily overreach:

- **Kene's own footprint only.** The same removal machinery pointed at
  anyone else — a recruiter, a competitor for a role — is not a
  job-hunting feature and is not in scope here.
- **Removal, not curation.** Correcting a wrong employer on a broker
  profile is reasonable. Scrubbing accurate history is a different
  activity, and one this skill should not quietly become a tool for.

Pairs naturally with the existing check-in: the journal already asks what
changed in Kene's working life, and a changed employer is exactly what a
stale broker profile will still be showing.

### How a quarter actually gets collapsed

The schema for this is in `applications_db_schema_addendum_9.sql`
(`career_journal_summary`); this is the process.

1. **Select** entries older than four full quarters that are not already
   collapsed and not soft-deleted.
2. **Draft one summary per quarter.** What was worked on, what got hard,
   what resolved, who recurred. Preserve any entry that
   `07-context-architect` already promoted to a durable fact — those are
   load-bearing and must survive verbatim in the summary text.
3. **Propose, don't apply.** Show Kene the quarter, the entry count, and
   the draft summary. Rule 5 applies with more force than usual here: the
   journal is his own account of his working life, and collapsing four
   quarters of it without asking is not a maintenance task.
4. **On confirmation**, write the `career_journal_summary` row with
   `source_ids`, and only then mark the source entries collapsed. Keep
   the source rows — collapsing is a read-side change, and `source_ids`
   is what makes it reversible.
5. **Re-export and re-embed** so the qmd index reflects the collapse
   rather than continuing to serve the uncollapsed months.

Never collapse the most recent four quarters, whatever the volume. Recent
detail is what the check-ins are for.

## What the journal is for, beyond feeding the pipeline

Until now the journal was an *input*: it fed the STAR bank, the
career-event cascade, calibration. Every one of those serves a job
search. None of them serves Kene between searches, which is when he is
actually writing the entries.

Seven uses, all drawn from data already in `career_journal`. Each is
**on request** unless stated — the journal is a record, and a record that
starts generating unsolicited conclusions about you is a different and
worse thing.

### 1. Self-assessment and promotion case

"Write my performance review" and "build my case for promotion" are the
same evidence-assembly problem as a résumé, from the same store — and
both are things Kene would otherwise reconstruct from memory once a year,
badly, under time pressure.

Pull the period's entries, group by theme rather than chronology, and
lead each with the outcome. Apply the **same quantification gate** the
STAR bank uses: a claim without its number goes back for the number
rather than into the document. Write to `self_assessments` so next
year's can reference what last year's claimed — a promotion case that
contradicts the previous review is a real risk and nothing else would
catch it.

Purpose changes the framing, not the evidence: a review looks backward at
delivery, a promotion case argues you are already operating at the next
level. Same entries, different argument.

### 2. Stay-or-go signal

`capability:career_planning` decides whether to move without ever reading the
journal, which holds the only longitudinal evidence available.

On request, summarise the trajectory: what has grown, what has stalled,
what keeps recurring unresolved. Present it as **material for Kene's
judgement, never as a recommendation**. "Scope has grown, the same
blocker has recurred for eight months" is an observation he can act on.
"You should leave" is a conclusion this tool has no standing to draw
about someone's career.

### 3. Skill drift

Entries stop mentioning a technology; the base résumé still leads with
it. `journal_skill_mentions` tracks mentions per quarter, and the check
compares the last four quarters against what the résumé foregrounds.

Two directions, both worth surfacing: something prominent on the résumé
that the work stopped involving (a claim aging into a liability), and
something the work now involves heavily that the résumé does not mention
at all (the more common and more costly case).

Surface, never auto-edit. The résumé is `05-resume-customizer`'s and
Rule 5 applies.

### 4. Recurring collaborators

Names recur in journal entries. That is a warm network, and
`capability:cold_outreach` currently reaches for cold contacts while it sits
unused.

`journal_collaborators` records name, first and last seen, mention count
and what they worked on together. **The `confirmed` column is the point:**
extraction is heuristic, and reaching out to someone on the strength of a
name a regex found is exactly the failure this guards against. An
unconfirmed row is a candidate; only a confirmed one is a contact, and
confirmation is Kene's.

Handing `capability:cold_outreach` a warm name is materially different from
handing it a cold one — the outreach should say so rather than
approaching a former colleague like a stranger.

### 5. Trajectory over time — deliberately narrow

The journal makes shifts in tone and content visible across months.
That is genuinely useful and it is also the place in this package where
overreach would do the most harm, so the scope is tight:

- **On request only.** No monitoring, no background pass, no alert.
- **No score, no metric, no threshold.** A number attached to how someone
  has been feeling invites tracking it, and this tool is not equipped for
  that to go well.
- **No diagnosis, no clinical language.** Not burnout, not depression,
  not anything with a name. This is a text pattern in a work journal, not
  an assessment of a person, and the difference matters.
- **Reflect, don't conclude.** "The last two months mention the same
  blocker and less about shipping than the six before" is an observation
  Kene can weigh. Anything that reads as a verdict on his state is out of
  scope, and if he wants to talk about how he is doing, a person is the
  right audience for that, not this.

### 6. Salary and negotiation evidence

An offer negotiation or a raise conversation needs scope growth since the
last one, with dates. The journal has exactly that and nothing reads it.

On request, assemble what changed since a stated date — new
responsibilities, headcount, systems owned, outcomes delivered — into the
evidence block `10-approval-and-submit`'s offer stage uses. Same
quantification gate. This is the strongest use of the journal that
produces money rather than clarity.

### 7. Résumé freshness

Nothing compares journal content against the base résumé's last update.
Quarterly, on request: has anything happened that the résumé does not
reflect? A résumé that silently ages between searches is the failure the
journal exists to prevent, and it was going unchecked.

---

**A note on what these have in common.** All seven read the journal and
none of them write to it. The journal stays what it is — Kene's own
record, appended by him. These are readings of it, and a reading that
started editing the record would be the end of it being trustworthy.

