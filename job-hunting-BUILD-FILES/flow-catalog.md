# Flow Catalog — 38 canonical flows, 8 variation axes

Every flow validated by `check_flows.py` against `graph.json`, `gates.yaml` and `settings.yaml`: every skill named exists, every gate exists, every axis resolves. **25/25 skills and 38/38 gates are covered** — nothing in the package is unreachable from a documented flow, and no flow names something that isn't there.

## Why 38 and not thousands

A full cartesian product of branch points, gate states and setting values runs into the tens of thousands, and 95% of those differ by one number. This catalog is canonical flows times *named axes* instead. A permutation earns its own line only when it changes which skills run or which gates fire — never when it only changes a threshold.

So `fidelity_mode` is an axis on six flows rather than six duplicated flows, and the axis table at the end says exactly what each value changes.

## Families

| Family | Flows | Covers |
|---|---|---|
| setup | 4 | Getting a person running |
| core | 6 | Discovery through to a submitted application |
| outreach | 6 | Reaching people who have not posted a job |
| interview | 4 | From invite to offer |
| direction | 4 | Deciding what to aim at |
| assets | 4 | Public artefacts and presence |
| learning | 5 | The tool improving and maintaining itself |
| failure | 5 | What happens when something goes wrong |

24 of the 38 are marked for the demo script.

## The flows

### Setup

#### `FLOW-A1` First install, experienced candidate  ·  *demo*

**Trigger** — install_state: no target-profile.yaml and no STAR bank

Session one, run to completion: pair the approval channel, then Phase 0-4 of the career interview, then the handful of settings the pipeline cannot run without. Everything else is spread across the following fortnight.

- **Steps** — `onboarding` → `07-context-architect`
- **Gates** — `GATE-DM-PAIRING`, `GATE-INSTALL-INTEGRITY`, `GATE-MEMORY-WRITE`, `GATE-STAR-WRITE`, `GATE-FACT-CONFLICT`, `GATE-TARGET-PROFILE-WRITE`
- **Produces** — target-profile.yaml, USER.md, MEMORY.md, star-story-bank.md, one configured source
- **Varies by** — `profile_stage`
- **Leads to** — `FLOW-B1`

#### `FLOW-A2` First install, first-time entrant  ·  *demo*

**Trigger** — install_state: ingestion returns empty or education-only

A genuinely different first session, not a lower bar on the same one. Interests and coursework carry the weight that work history carries elsewhere, and the match thresholds start lower because entry-level postings overstate their own requirements.

- **Steps** — `onboarding` → `07-context-architect` → `20-interests-profile`
- **Gates** — `GATE-DM-PAIRING`, `GATE-MEMORY-WRITE`, `GATE-TARGET-PROFILE-WRITE`, `GATE-SENSITIVE-DISCLOSURE`
- **Produces** — target-profile.yaml with profile_stage first_time, interests profile, thresholds pre-set 55/35
- **Varies by** — `profile_stage`
- **Leads to** — `FLOW-B1`
- ⚠️ **Blocked** — profile_stage has no field in the shipped template — see settings-registry.md

#### `FLOW-A3` Paced advanced settings, sessions 2..N

**Trigger** — utterance: any later session, paced by observed cadence

Spread over one to two weeks, ordered by dependency and payoff. Pitch catalog seeding is deliberately last and gets its own session.

- **Steps** — `onboarding`
- **Gates** — `GATE-TARGET-PROFILE-WRITE`, `GATE-CALIBRATION-CHANGE`, `GATE-TIER-CONFIG-CHANGE`
- **Produces** — tier-config, further sources, calibration, career-pulse cadences
- **Varies by** — `active_tier`, `calibration_mode`

#### `FLOW-A4` Adding one job source

**Trigger** — utterance: add this board / watch this company's careers page

Its own micro-flow, run any time, distinct from onboarding the person. The posted_at method matters more than the URL — it is what makes the speed metric honest.

- **Steps** — `01-job-discovery`
- **Gates** — `GATE-TARGET-PROFILE-WRITE`
- **Produces** — new sources.yaml entry with a posted_at method
- **Varies by** — `discovery_mode`

### Core

#### `FLOW-B1` Scheduled discovery to staged application  ·  *demo*

**Trigger** — cron: discovery every 3h, sweep on its own cadence

The spine. A posting appears, is parsed, scored, researched, tailored, gated for evidence, and arrives as one message asking approve, edit or skip. Nothing between the posting appearing and that message needs you.

- **Steps** — `01-job-discovery` → `02-jd-parser` → `12-company-research` → `03-resume-match` → `04-keyword-analysis` → `05-resume-customizer` → `06-cover-letter` → `08-application-qa` → `09-risk-tactics-gate` → `10-approval-and-submit` → `11-analytics-and-learning`
- **Gates** — `GATE-RESEARCH-FETCH`, `GATE-SITE-SESSION`, `GATE-SUBMIT-APPLICATION`
- **Produces** — tailored docx, cover letter, answers, change-log, approval message
- **Varies by** — `fidelity_mode`, `discovery_mode`, `active_tier`, `match_score.minimum`, `match_score.stretch.floor`, `overqualification_tolerance`
- **Leads to** — `FLOW-B5`, `FLOW-D1`, `FLOW-G1`
- **Variants**
  - *strict fidelity* — unsupported claims stripped, gap written to open_gaps, nothing held for review
  - *balanced fidelity* — claims applied and tagged UNVERIFIED, held for review before the approval message
  - *stretch match* — scores 50-70 staged and tagged STRETCH in the approval message
  - *parallel sweep* — build phase delegated across postings, status flows building to staged to awaiting_approval

#### `FLOW-B2` Applying to a posting you found yourself  ·  *demo*

**Trigger** — utterance: pasted URL or job description

The same pipeline entered halfway. Skips discovery and the daily cap entirely — a posting you brought is never rationed.

- **Steps** — `02-jd-parser` → `12-company-research` → `03-resume-match` → `04-keyword-analysis` → `05-resume-customizer` → `06-cover-letter` → `08-application-qa` → `09-risk-tactics-gate` → `10-approval-and-submit`
- **Gates** — `GATE-RESEARCH-FETCH`, `GATE-SUBMIT-APPLICATION`
- **Produces** — same package as FLOW-B1
- **Varies by** — `fidelity_mode`

#### `FLOW-B3` Score a role without applying  ·  *demo*

**Trigger** — utterance: how well do I match this

Read-only. Produces a score and the specific gaps behind it, and stops. Often the honest answer to "should I bother with this one."

- **Steps** — `02-jd-parser` → `03-resume-match`
- **Produces** — match score, gap list
- **Varies by** — `match_score.minimum`
- **Leads to** — `FLOW-B2`, `FLOW-E3`

#### `FLOW-B4` Edit before approving  ·  *demo*

**Trigger** — utterance: reply 'edit' to an approval message

An edit re-enters the evidence gate rather than bypassing it, and the edit itself is logged — the learning loop needs to know which packages needed changing.

- **Steps** — `10-approval-and-submit` → `09-risk-tactics-gate` → `11-analytics-and-learning`
- **Gates** — `GATE-SUBMIT-APPLICATION`
- **Produces** — revised package, outcome logged as edited_then_sent

#### `FLOW-B5` Skip or ignore a staged application

**Trigger** — utterance: reply 'skip', or silence

Silence is never consent. The application sits, and it is counted as a decision you made rather than one the system made for you.

- **Steps** — `10-approval-and-submit` → `11-analytics-and-learning`
- **Gates** — `GATE-SUBMIT-APPLICATION`
- **Produces** — status stays awaiting_approval, decision logged

#### `FLOW-B6` Answering a long application form  ·  *demo*

**Trigger** — handoff: posting carries free-text questions

Answers are recomposed from confirmed stories. Where no story covers the question, the gap is surfaced rather than invented, and the question joins the bank for next time.

- **Steps** — `08-application-qa` → `07-context-architect` → `09-risk-tactics-gate`
- **Gates** — `GATE-MEMORY-WRITE`
- **Produces** — drafted answers drawn from the STAR bank
- **Varies by** — `fidelity_mode`

### Outreach

#### `FLOW-C1` Reply to a hiring post found on social  ·  *demo*

**Trigger** — cron: social listening scan

A post asking for candidates becomes a drafted response with the post it answers attached. What the tool may do with it depends entirely on the platform, read live from the capability matrix rather than assumed.

- **Steps** — `14-social-discovery-outreach` → `22-contact-enrichment` → `09-risk-tactics-gate` → `10-approval-and-submit`
- **Gates** — `GATE-SOCIAL-POLL`, `GATE-SEND-DM`, `GATE-PUBLIC-REPLY`, `GATE-PLATFORM-PREREQ`
- **Produces** — drafted reply or DM, tagged by channel
- **Varies by** — `fidelity_mode`, `platform_send_tier`
- **Variants**
  - *tier 1 platform* — send path exists, message goes out on per-message approval
  - *tier 2/3 platform* — draft only, cued to you to send by hand regardless of approval
  - *public reply* — labelled REPLY, goes up under your name where the whole thread sees it

#### `FLOW-C2` Cold pitch to a company with no opening  ·  *demo*

**Trigger** — utterance: reach out to X, or the prospecting cadence cron

Every claim about their situation traces to a line in that company's own research record, and is framed as a hypothesis rather than an assertion.

- **Steps** — `17-cold-prospecting` → `12-company-research` → `22-contact-enrichment` → `09-risk-tactics-gate` → `10-approval-and-submit`
- **Gates** — `GATE-RESEARCH-FETCH`, `GATE-ENRICHMENT-LOOKUP`, `GATE-PAID-SPEND`, `GATE-SEND-EMAIL`
- **Produces** — pitch drawn from the catalog, evidence-traced
- **Variants**
  - *role_fit* — "I could do X for you" — familiar, low friction, the default volume
  - *role_creation* — asks them to accept a diagnosis of their own business first — deliberately a small minority of weekly volume
  - *wildcard entry used* — WILDCARD tag carried through to the approval message so approval is never given on autopilot

#### `FLOW-C3` Finding a real person behind a company name  ·  *demo*

**Trigger** — handoff: company and role known, name and email are not

Hiring manager first, recruiter-track staged separately and framed differently. Neither is ever asserted with certainty — the output is a confidence-scored hypothesis with its sources attached.

- **Steps** — `22-contact-enrichment`
- **Gates** — `GATE-ENRICHMENT-LOOKUP`, `GATE-PAID-SPEND`, `GATE-API-KEY-CONNECT`
- **Produces** — identified person with confidence score and cited evidence, verified email
- **Varies by** — `tier3_monthly_budget_usd`
- **Variants**
  - *free cascade only* — public sources, self-hosted tools, then rotated free tiers — 325+ lookups a month at zero cost
  - *paid tier reached* — asks, with the price, and only if a budget above zero was set

#### `FLOW-C4` LinkedIn stranger, connect then message  ·  *demo*

**Trigger** — handoff: target identified on LinkedIn, no existing connection

Two gates in sequence, and the second cannot fire until the platform prerequisite clears. A drafted message sits below sendable until the connection is actually accepted, no matter how ready it is.

- **Steps** — `14-social-discovery-outreach`
- **Gates** — `GATE-LINKEDIN-CONNECT`, `GATE-PLATFORM-PREREQ`, `GATE-SEND-DM`
- **Produces** — connection request with note, then a message once accepted
- **Varies by** — `platform_send_tier`

#### `FLOW-C5` InMail instead of connect-and-wait

**Trigger** — utterance: target worth a metered credit

Buys skipping the wait, at the cost of a plan-gated credit. One per recipient — no follow-up without a reply. Unavailable until your subscription tier is set, which is the honest default rather than an error.

- **Steps** — `14-social-discovery-outreach`
- **Gates** — `GATE-SEND-INMAIL`
- **Produces** — one InMail, credit decremented
- **Varies by** — `plan`, `platform_send_tier`

#### `FLOW-C6` Seeding the pitch catalog

**Trigger** — utterance: its own dedicated session, never folded into general setup

A genuinely creative pass, not a checkbox. Stretch entries get a visibly heavier confirmation than held ones — an explicit "you are telling me you can actually deliver this."

- **Steps** — `17-cold-prospecting` → `07-context-architect`
- **Gates** — `GATE-PITCH-CONFIRM`, `GATE-PITCH-WILDCARD`
- **Produces** — catalog entries with evidence and target personas

### Interview

#### `FLOW-D1` Interview invite to prep brief  ·  *demo*

**Trigger** — external: interview_request_at set, by email scan or by you

Fires on the invite arriving, not on you remembering to ask. Where three likely questions have no story on file, the brief says exactly that rather than filling the space.

- **Steps** — `11-analytics-and-learning` → `13-interview-prep` → `12-company-research`
- **Gates** — `GATE-INBOX-SCAN`, `GATE-RESEARCH-FETCH`, `GATE-CALENDAR-CREATE`
- **Produces** — prep brief, flashcard deck, interviewer research, optional calendar block
- **Leads to** — `FLOW-D2`, `FLOW-D3`

#### `FLOW-D2` Live practice session  ·  *demo*

**Trigger** — utterance: 'quiz me' / 'practise for Thursday'

The study phase, separate from the build phase. Runs on the deck already built, and works by voice as readily as by text.

- **Steps** — `13-interview-prep`
- **Produces** — practice run with feedback against your own stories

#### `FLOW-D3` Later round or a changed format

**Trigger** — external: a later round's details arriving by email

A second round is a different interview, not the same one again — panel, format and depth all move.

- **Steps** — `13-interview-prep` → `11-analytics-and-learning`
- **Gates** — `GATE-INBOX-SCAN`
- **Produces** — updated brief for the new format and panel

#### `FLOW-D4` Offer comparison and decision  ·  *demo*

**Trigger** — external: an offer arrives

The other end of the pipeline and the higher-stakes decision. Built as a workbook you can change the assumptions in, not as prose that argues for an answer.

- **Steps** — `10-approval-and-submit` → `11-analytics-and-learning`
- **Produces** — comparison workbook, outcome logged

### Direction

#### `FLOW-E1` Plan a path to a target role  ·  *demo*

**Trigger** — utterance: what would it take to become a X

Ends in one confirmed target, which then becomes what the whole discovery pipeline runs against. Two hops maximum; a third rests on a profile nobody can predict.

- **Steps** — `19-career-path-planner` → `07-context-architect` → `12-company-research`
- **Gates** — `GATE-TARGET-PROFILE-WRITE`, `GATE-RESEARCH-FETCH`
- **Produces** — confirmed target title, stepping-stone plan, gap list
- **Varies by** — `stepping_stone.max_hops`, `stepping_stone.allow_comp_regression`, `stepping_stone.liquidity_probe`
- **Leads to** — `FLOW-B1`
- **Variants**
  - *allow_comp_regression ask* — steps that pay less are shown with the reasoning
  - *allow_comp_regression never* — silently removes most sector switches and management-track entries
  - *liquidity probe off* — taxonomy signals only — a plan can point at a title with no live market

#### `FLOW-E2` Build or refresh the interests profile

**Trigger** — utterance: setup, or something interest-shaped mentioned in passing

Recording is free and unrestricted. Whether a sensitive entry ever appears in an outward document is a separate decision, asked at the moment of use, every time.

- **Steps** — `20-interests-profile` → `07-context-architect`
- **Gates** — `GATE-MEMORY-WRITE`, `GATE-SENSITIVE-DISCLOSURE`
- **Produces** — interests profile with sensitive entries tagged

#### `FLOW-E3` Career pulse journal check-in  ·  *demo*

**Trigger** — cron: journal cadence

Raw entries are stored immediately; anything that looks like a durable career fact goes through confirmation before it reaches memory. A quantified claim heard in a voice note is read back before it is written.

- **Steps** — `16-career-pulse` → `07-context-architect`
- **Gates** — `GATE-MEMORY-WRITE`, `GATE-VOICE-NUMBER-ECHO`, `GATE-FACT-CONFLICT`
- **Produces** — journal entry stored raw, candidate facts routed to confirmation

#### `FLOW-E4` Profile monitor picks up a change

**Trigger** — cron: explicit-channel monitor cadence

Watches the profiles you named. Surfaces, never writes — every candidate fact goes through the same confirmation as one you mentioned yourself.

- **Steps** — `16-career-pulse` → `07-context-architect`
- **Gates** — `GATE-SITE-SESSION`, `GATE-MEMORY-WRITE`
- **Produces** — diff surfaced, candidate fact routed to confirmation

### Assets

#### `FLOW-F1` Build and publish a portfolio page  ·  *demo*

**Trigger** — utterance: a role asks for a portfolio, or you want a link

Six blocks, every one drawn from already-confirmed memory. Built locally first — going public is its own decision, made after you have looked at it.

- **Steps** — `23-portfolio-onepager` → `09-risk-tactics-gate`
- **Gates** — `GATE-PORTFOLIO-PUBLISH`
- **Produces** — one page from confirmed memory, optionally at a public URL

#### `FLOW-F2` LinkedIn profile audit and rewrite  ·  *demo*

**Trigger** — utterance: audit my LinkedIn

Every proposed line traces to the same confirmed material a resume draws on. Approval is per change, because your network sees the edit activity.

- **Steps** — `24-linkedin-profile-optimizer` → `09-risk-tactics-gate`
- **Gates** — `GATE-PROFILE-EDIT`
- **Produces** — proposed changes, one at a time, against current text
- **Varies by** — `fidelity_mode`

#### `FLOW-F3` Save a named output template

**Trigger** — utterance: always write cover letters for X like this

The one confirmed-write file that does not route through the memory skill, deliberately — a formatting preference is not a career fact.

- **Steps** — `21-output-templates`
- **Gates** — `GATE-OUTPUT-TEMPLATE-WRITE`
- **Produces** — named template applied to future outputs of that type

#### `FLOW-F4` Share an outcome milestone  ·  *demo*

**Trigger** — external: response rate crosses 2x your stated baseline over 10+ applications

Triggered on a personal multiple, not an absolute number, so it means something regardless of your field. Capped at one ask a fortnight and suppressed entirely after two you ignore.

- **Steps** — `11-analytics-and-learning`
- **Gates** — `GATE-TESTIMONIAL-POST`
- **Produces** — drafted post in your own voice, every figure traced to a row

### Learning

#### `FLOW-G1` Weekly self-improvement review  ·  *demo*

**Trigger** — cron: Monday morning

Correlates your tactics against your real outcomes and proposes specific, evidence-backed edits — with the numbers behind each one. Two proposals a week, not eight, because a review that surfaces eight teaches you to approve all of them without reading.

- **Steps** — `11-analytics-and-learning`
- **Gates** — `GATE-SKILL-EDIT`
- **Produces** — eight correlation results, staged edit proposals, weekly digest
- **Varies by** — `calibration_mode`
- **Variants**
  - *rotation group released* — only this week's group of proposals surfaces, the rest wait with their detection date recorded
  - *effect size grew* — a queued proposal is promoted to the next release regardless of its group

#### `FLOW-G2` Quarterly optimiser run

**Trigger** — utterance: manual, quarterly, never scheduled

Deliberately manual and deliberately scoped to the three writing skills. The risk gate is excluded — an optimiser whose constraint checks cannot see content is the wrong tool to point at the one skill whose value is being conservative.

- **Steps** — `11-analytics-and-learning`
- **Gates** — `GATE-GEPA-DEPLOY`
- **Produces** — evolved and baseline files to diff by hand

#### `FLOW-G3` Ghost check and outcome nudge

**Trigger** — cron: daily

Scans for outcomes first so the daily ask is scoped to what has no email trace at all — a verbal offer from a call, or real silence.

- **Steps** — `11-analytics-and-learning`
- **Gates** — `GATE-INBOX-SCAN`
- **Produces** — outcomes logged from email, a short ask about the genuinely untrackable remainder

#### `FLOW-G4` Pause and resume the search  ·  *demo*

**Trigger** — utterance: pause for two weeks

Discovery stops. Conversation does not, and the journal keeps running — a pause is about the searching, not about you disappearing.

- **Steps** — `00-orchestrator`
- **Gates** — `GATE-PIPELINE-PAUSE`
- **Produces** — discovery stopped with a visible expiry

#### `FLOW-G5` Adding a new capability

**Trigger** — utterance: can it also do X

Defaults to writing an addendum rather than rewriting a working file, so hand-tuned behaviour is never silently replaced.

- **Steps** — `18-skill-composer`
- **Gates** — `GATE-SKILL-COMPOSER-WRITE`
- **Produces** — drafted addendum, reviewed before install

### Failure

#### `FLOW-H1` The posting disappeared before approval  ·  *demo*

**Trigger** — external: re-verification before the approval message

Three signals, and the third catches most real cases: a 404, a page that now says closed, and a redirect to the board index where the fetch succeeds and only the content tells you. A pulled posting is information, not a decision — and it must not count as a non-reply, or every response rate you measure is understated.

- **Steps** — `10-approval-and-submit` → `11-analytics-and-learning`
- **Produces** — dropped from the queue, reported in the digest not as a ping

#### `FLOW-H2` The evidence gate refuses a claim  ·  *demo*

**Trigger** — handoff: a tactic with no supporting line in memory

The gap goes to a worklist, never into memory as an invented fact. The memory interview picks it up on its next run, which is how a refused claim becomes a real story rather than a permanent blocker.

- **Steps** — `09-risk-tactics-gate` → `07-context-architect`
- **Gates** — `GATE-FIDELITY-MODE`
- **Produces** — tactic dropped or flagged by mode, gap written to open_gaps
- **Varies by** — `fidelity_mode`
- **Leads to** — `FLOW-E3`

#### `FLOW-H3` Submit blocked by the safety hook  ·  *demo*

**Trigger** — external: a submit-shaped click with no approval recorded

The hook trusts the recorded decision, never the conversation. It fails closed on every branch it can see — and fails open, silently, on any tool name it was never told about, which is why the form is not opened at all until the toolset is confirmed watched.

- **Steps** — `10-approval-and-submit`
- **Gates** — `GATE-SUBMIT-APPLICATION`, `GATE-DANGEROUS-COMMAND`
- **Produces** — blocked, with the specific reason

#### `FLOW-H4` Partial install

**Trigger** — install_state: one skill installed without shared/

The worst failure available here is not a crash. It is a skill that reads convincingly with no rules, no database and no profile behind it — which is why this is checked at first run of every session.

- **Steps** — `00-orchestrator`
- **Gates** — `GATE-INSTALL-INTEGRITY`
- **Produces** — stop, with the missing file named

#### `FLOW-H5` Restore from backup

**Trigger** — utterance: data loss or a bad migration

States what will be overwritten and from when, before it runs. Backups themselves are unattended and need no gate; restores are not and do.

- **Steps** — `00-orchestrator`
- **Gates** — `GATE-BACKUP-RESTORE`
- **Produces** — state restored from a named date

## Variation axes

These are the axes. Everything else in the settings registry changes a number, not a shape.

| Axis | Values | What it changes | Flows |
|---|---|---|---|
| `fidelity_mode` | strict, balanced, embellish | whether an unsupported claim is stripped, held for review, or logged and passed | 6 |
| `profile_stage` | experienced, first_time | which first session runs at all, and the starting match thresholds | 2 |
| `discovery_mode` | poll_only, open_web, open_web_excluding | whether the open-web sweep runs as a second, slower cadence | 2 |
| `calibration_mode` | manual, auto, hybrid | whether threshold changes are staged for approval or applied directly | 2 |
| `active_tier` | starter, pro, max | how many packages reach your queue per day | 2 |
| `overqualification_tolerance` | strict, balanced, relaxed | whether roles below your level are staged at all | 1 |
| `stepping_stone.allow_comp_regression` | ask, never, allow | whether sector switches and management-track entries appear in a plan | 1 |
| `platform_send_tier` | tier_1, tier_2, tier_3 | whether the tool may send at all, or only draft and cue | 3 |

`platform_send_tier` is the one axis that is not a setting. It is read live from the capability matrix per Rule 6, which is why a flow's send behaviour can change without anyone changing a setting — and why the matrix has its own re-verify cadence.

## Two things worth noting

**`FLOW-A2` is currently blocked.** The first-time-entrant onboarding track depends on `profile_stage`, which has no field in the shipped template. Until that is added, a first-time entrant silently runs `FLOW-A1` instead and gets thresholds tuned for someone with a career. It is the first thing to fix, because it is the first thing a new user hits.

**The failure family is five flows and no other artefact describes them.** A posting pulled before approval, a refused claim, a blocked submit, a partial install, a restore. These are the flows a user actually hits in week one, they are where trust is won or lost, and documentation that only covers the happy path leaves them to be discovered live.

## What this completes

All three lists now exist and cross-reference each other:

| Artefact | Contents |
|---|---|
| `graph.json` + `package-schematic.html` | 247 nodes, 2,366 edges |
| `gates.yaml` | 38 gates, 4 classes, 8 packs |
| `settings.yaml` | 111 keys scanned, 22 user-facing |
| `flows.yaml` | 38 flows, 8 axes |

Four checkers keep them honest: `extract_graph.py`, `check_gates.py`, `extract_settings.py`, `check_flows.py`. Re-run them after any change to the package and drift shows up as a failure rather than as a wrong sentence in the manual.
