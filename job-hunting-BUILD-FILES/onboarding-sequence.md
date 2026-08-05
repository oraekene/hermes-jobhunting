# Onboarding Sequence

Every setting and permission pack, sequenced. Validated by `check_onboarding.py`: all 22 settings appear exactly once, all 7 SIMPLE settings land in session 1, and nothing is asked before the thing that determines its meaning.

## Two principles

**Pacing.** Session 1 asks only what the pipeline cannot run without — seven settings, about 25 minutes. Everything else spreads across the following fortnight, triggered by the user reaching the situation the setting is actually about. A wizard that asks 22 questions before showing any value gets abandoned around question nine, and the abandonment is silent.

**Ordering.** Dependency order, cheap high-information questions first. `profile_stage` is asked first because it changes what every later question means — asked fourth, three earlier answers would need revisiting.

## Sessions

| Session | When | Settings | Minutes |
|---|---|---|---|
| **Enough to run** | first install | 7 | ~25 |
| **Volume and bar** | 2-4 days after session 1, once some applications have been reviewed | 6 | ~10 |
| **Filters and edges** | week 2, or the first time a bad match appears | 4 | ~8 |
| **Permission packs** | week 2, prompted by friction rather than scheduled | 0 | ~10 |
| **Addon capabilities** | week 3, or on first use of a licensed addon | 5 | ~12 |
| **Pitch catalog** | its own session, never folded into another | 0 | ~30 |

### Enough to run

*End the session with a real application staged and waiting for approval. Not a configured tool — an actual result. That is the difference between a setup someone finishes and one they abandon.*

**Pair the approval channel.**

- *Why here* — Nothing else in the package means anything until approvals can only come from you. This is also where a multi-customer deployment gets its per-customer identity — one pairing code per customer, never a shared channel.

**Verify the install is complete.**

- *Why* — The worst failure here is not a crash. It is a skill that reads convincingly with no rules, no database and no profile behind it. Also reports which protections are active — a container backend silently disables one of the three submit-approval layers.

**Do you have prior paid work history to draw on?**

- *Why here* — It changes what every later question means and pre-sets the match thresholds. Asking it fourth would mean re-asking three earlier answers.
- *Default* — Asked before anything else. It routes the whole first session and pre-sets your match thresholds — 55/35 instead of 70/50 if you are starting out, because entry-level postings systematically overstate their own requirements.

**Hand over a resume, a LinkedIn export, or just talk.**

- *Why* — Most of the profile can be inferred and then confirmed, which is far faster than being interviewed for it. Everything inferred is read back before it is stored.
- *If not available* — With nothing to ingest, the interview covers the same ground conversationally. This is the normal path for first_time.

**Confirm your level.**

- *Default* — Postings are filtered to your band before anything else runs, so the pipeline spends its daily budget on roles you could take.

**Confirm the job titles worth searching for.**

- *Why* — Discovery returns literally nothing until at least one exists, so this is the single most load-bearing answer in the session.
- *Default* — You confirm each variant. Titles you actually held are suggested automatically; adjacent titles the taxonomy proposes are shown with the evidence behind them.

**Where will you work — remote, hybrid, onsite, and where?**

- *Default* — Remote, hybrid, onsite, countries and cities are all separate answers, so 'remote anywhere' and 'hybrid in Lagos only' filter differently.

**Is there a figure below which you would not take a role?**

- *Note* — "No floor yet" is a real, working answer and must be offered explicitly. Asking a question that has no acceptable non-answer teaches people to make something up.
- *Default* — Postings below your floor are dropped before they cost you a review. 'No floor set yet' is a valid, working answer.

**Three things you have done that you would want to be asked about.**

- *Why* — Three is enough to produce a first application and few enough to finish in one sitting. The bank grows on its own from journal entries and from gaps the evidence gate finds.

**How strictly must claims be backed by evidence?**

- *Why here* — Asked immediately after the story bank, while it is concrete what "evidence" refers to. Asked in the abstract it gets an abstract answer.
- *Default* — strict — every claim cites a line in your resume, portfolio or story bank. No evidence means the tactic is dropped and the gap flagged to you.

**Search only the boards you name, or the wider web too?**

- *Default* — poll_only — only the sources you configured. Predictable, cheap, and misses anything not on those boards.

**Add one job source.**

- *Why* — One, not five. A user who adds one working source and sees a result comes back and adds four more. A user asked for five up front adds none.

**Run discovery once, live, and stage the first application.**

- *Why* — Ending on a staged application rather than a configuration summary is the whole point of the session. It also demonstrates the submit gate on real output, which is a better explanation of it than any tooltip.

### Volume and bar

**Triggered by** — first approval decision made

**How many applications a day should be prepared for you?**

- *Why* — Meaningless before they have seen what reviewing one costs them.
- *Default* — starter — 15 a day. Enough for one person's active search, and a number you can actually review.

**Are you currently working?**

- *Default* — Urgency and volume adapt. Being between roles changes what a sensible daily target is.

**Where should the bar sit?**

- *Default* — 70 by default, 55 if you are starting out. Below it, nothing is staged.

**Should reaches be staged too, flagged as reaches?**

- *Default* — 50-70 is the stretch band: staged, and tagged STRETCH in the approval message so you know it is a reach before you approve.

**How far below your level is worth considering?**

- *Default* — balanced — title-seniority and compensation deltas are weighed as two separate axes.

**May the bar adjust itself as results come in?**

- *Default* — hybrid — the maths runs on schedule, each proposed change is staged, and it only takes effect once you approve it.

### Filters and edges

**Triggered by** — user skips three applications for the same reason

**Do you need sponsorship?**

- *Default* — Roles that explicitly cannot sponsor are filtered out.

**Anywhere that should never appear — your current employer, say?**

- *Default* — Your current employer, or anywhere you have decided against, never appears.

**Any industries to rule out?**

- *Default* — Named industries never reach your queue.

**Aggregator sites cluttering the queue?**

- *Default* — Aggregator sites that republish the same postings stop cluttering the queue.

### Permission packs

*Deliberately triggered by evidence of friction, not by the calendar. Someone who has approved fifteen packages unchanged has earned the offer; someone still editing every one has not, and offering it to them is offering to remove a check they are visibly still using.*

**Triggered by** — user approves 15+ applications without editing any

**Review the permission packs.**


**Offer batch review — approve five at once.**

- *Why* — The right answer for most people. Captures nearly all the friction reduction of auto-approve while keeping a human on every application.

**Only if asked — arm an irreversible gate.**

- *Requires* — typed confirmation, own screen, 30-day expiry, cap still applies

### Addon capabilities

**Triggered by** — addon licensed, or trial begins

**Your LinkedIn subscription tier?**

- *Note* — Unset is honest, not an error — every stranger routes through connect-and-wait instead.
- *Default* — Sets your monthly InMail allowance so the tool knows what it is spending.

**A monthly budget for paid contact lookups?**

- *Note* — Zero is the default and covers 325+ free lookups a month.
- *Default* — Zero. The free cascade covers 325+ lookups a month before anything could cost money.

**How many moves may a plan span?**

- *Default* — Two hops. A third rests on a profile nobody can predict, and the re-plan rule would regenerate it anyway.

**May a plan include a step that pays less?**

- *Default* — ask — a step that pays less is shown to you with the reasoning rather than hidden.

**Check live demand for a planned role?**

- *Default* — A read-only census of live postings across your sources over 90 days. Queues nothing.

### Pitch catalog

*A genuinely creative pass rather than a form. Held capabilities first, adjacent second, stretch entries last and with a visibly heavier confirmation — an explicit "you are telling me you can actually deliver this", because every pitch drawing on one carries that tag through to the approval message.*

**Triggered by** — user asks about outreach, or the outreach addon is licensed

**What can you deliver, with the evidence for each?**


**Anything you could deliver but have not yet?**


## Baseline capture

Without this there is no before-and-after, and the before-and-after is the most persuasive thing the tool will ever be able to say about itself. It is also what makes milestone thresholds personal rather than absolute: "twice your own baseline" means something in every field, "12% response rate" does not.

- **Roughly how many applications in the last six months?**
- **Roughly how many replies of any kind?**
- **How many interview invitations?**
- **Of those, how many felt like they went well?**  
  A self-assessment, so it is stored as a scale rather than a count and never appears in a published figure. Excellent for the private before-and-after, bad as a public statistic.
- **Any offers?**

Skippable. Fine to skip, and the consequence is stated plainly rather than hidden: milestone triggers fall back to fleet percentiles, which are weaker and arrive later.

## Three decisions worth reviewing

**Session 1 ends with a staged application, not a summary screen.** The last step runs discovery live and stages something real. That is the difference between a setup someone finishes and one they abandon — and it demonstrates the submit gate on their own output, which explains it better than any tooltip could.

**One source, not five.** Someone who adds one working source and sees a result comes back and adds four more. Someone asked for five up front adds none.

**Permission packs are offered on evidence of friction, not on a schedule.** Session 4 triggers after 15 approvals with no edits. Someone still editing every package has not earned the offer — offering it to them is offering to remove a check they are visibly still using.
