<!-- STATUS: ABSORBED. This file is preserved as a record, not as instructions.
Content lives in 16-career-pulse/SKILL.md. (Filed under shared/ in the source package, which was a misplacement -- it is a skill addendum, not a shared reference.)
Do not follow it as a procedure; the host file named above is authoritative. -->

# 16-career-pulse — Addendum

Origin: two separate things that turned out to belong in one file.

The first is a capability found in the Stage 1 Hermes source crawl —
`hindsight_reflect`, a memory operation that reasons across a whole
store rather than retrieving matches from it. Five of this skill's
seven journal uses ask a question that retrieval structurally cannot
answer, and nothing in either package had noticed the difference.

The second is a deliberate loosening of this skill's own restrictions,
in response to a direct challenge that they were too tight. That
challenge was largely correct. Four limits come off here. One stays,
and the reasoning for keeping it is written out rather than asserted,
because a rule that survives a challenge should have to show why.

## Part 1 — Hindsight recall and reflect

`plugins/memory/hindsight/__init__.py` (1,974 lines) is one of eight
memory providers Hermes ships. It exposes three tools:

| Tool | What it does |
|---|---|
| `hindsight_retain` | store |
| `hindsight_recall` | search and return ranked memories |
| `hindsight_reflect` | reason across *all* stored memories and answer |

The third has no equivalent anywhere in this package, and the gap is
not cosmetic.

Take use 3, skill drift. The question is *which technology did the work
stop involving?* No journal entry says "I stopped using Kubernetes."
The entries simply stop mentioning it. `journal_skill_mentions` counts
mentions per quarter, which answers the question well for terms already
on the list — and cannot answer it at all for a term Kene never
registered. The answer being looked for is an absence, and retrieval
finds presences.

Or use 2, the stay-or-go signal: *what has grown, what has stalled,
what recurs unresolved?* "Recurs unresolved" is a pattern distributed
across dozens of entries over many months. It is in no single row.

Both of these are reflect-shaped questions that have been getting
recall-shaped answers.

### Both tools, used fully

- **`hindsight_recall`** for anything where Kene should read his own
  words: a specific period, a named project, a collaborator, the raw
  material behind a claim. Retrieval returns entries; entries are
  evidence.
- **`hindsight_reflect`** for anything where the answer is a pattern
  across the whole store: drift, trajectory, recurrence, the shape of
  a year.

Uses 1, 2, 3, 5 and 6 draw on both. Uses 4 and 7 are retrieval
problems and stay on recall.

### Detection, not assumption

Hermes allows exactly one active memory provider, and that choice is
global — it affects everything Kene does with Hermes, not just this
package. **So this package must never require Hindsight, install it, or
change the configured provider.** It is an option Kene may already have
chosen for his own reasons; this addendum is one more reason it's a
good choice, not a dependency.

Every journal use therefore branches:

1. Check whether `hindsight_reflect` / `hindsight_recall` are available.
2. If yes, use them.
3. If no, fall back to the SQL path `SKILL.md` already describes.

Both paths produce the same output shape. The Hindsight path produces a
better answer. Neither path is ever announced to Kene as unavailable —
the SQL path always works, and "this feature needs a different memory
backend" is not a useful thing to tell someone who asked about their
own career.

### Verification is not optional

A reflect answer is a model's synthesis over months of material. It can
produce a statement no entry supports, and that statement will read
exactly like the ones that are supported.

Every reflect output must therefore:

- **cite entry dates** for each claim it makes;
- **be checked** — query `career_journal` for each cited date;
- **be pruned** — discard any claim whose citation doesn't resolve;
- **report the discard count** to Kene, because a synthesis that lost
  three of eleven claims to verification is a different object from
  one that lost none, and he should be able to see which he's holding.

This is Rule 2 applied to a new claim source. A long, fluent, confident
paragraph about eighteen months of someone's working life is precisely
the kind of output that earns trust it hasn't verified.

### Tags, if Hindsight is in use

Hindsight supports `HINDSIGHT_RETAIN_TAGS` and
`HINDSIGHT_RETAIN_OBSERVATION_SCOPES` (`per_tag` / `combined` /
`all_combinations`). Tag journal-derived memories `career-journal` and
set the scope to `per_tag`, so a reflect query over the journal doesn't
silently pull in unrelated memories from the rest of Kene's Hermes use
and present them as career evidence.

### The entity graph and use 4

Hindsight does entity resolution over a knowledge graph. Use 4 —
recurring collaborators — currently extracts names heuristically, and
`SKILL.md` is blunt about the weakness: a name a regex found is not a
contact. An entity graph resolves "Sarah", "Sarah K." and "Sarah
Kimani" to one person; a regex does not.

The `confirmed` column stays exactly as it is. Better extraction
produces a better candidate list. It does not produce a contact, and
`17-cold-prospecting` still may not treat an unconfirmed name as one.

## Part 2 — What loosens, and why

The original design gave every journal use a narrow envelope. That
envelope was drawn to prevent one specific failure — a record that
starts producing unsolicited verdicts about the person keeping it —
and in preventing it, it also prevented a lot of legitimate work.

Four changes.

### 1. The skill may draw conclusions about the work

The old rule was *reflect, don't conclude* — surface an observation,
never a verdict. Dropped as an absolute.

A tool that assembles eighteen months of evidence and then declines to
say what it sees has done the easy half and handed back the hard half.
`19-career-path-planner` already names a preferred path and states the
conditions that would change it, using the one-three-one framing. Two
skills in the same package should not hold two different standards for
the same act.

The output should be substantive, specific and as long as the material
warrants. There is no length ceiling, and brevity is not a virtue here.

### 2. Use 2 may make a recommendation

*Material for judgement, never a recommendation* becomes: a
recommendation, in the one-three-one shape the package already uses —
one issue, three options, one recommendation with the conditions that
would change it.

The condition-stating is what makes this safe rather than presumptuous.
"Stay, unless the scope conversation in Q3 goes the way the last two
did" is a recommendation Kene can argue with on its merits. "You should
leave" is a verdict with nothing to grip.

### 3. Metrics on work dimensions

*No score, no metric, no threshold* was too broad. Numbers are allowed
for work dimensions and should be used, because they are the difference
between a vague impression and a checkable claim:

- scope growth over a period
- shipping cadence, and its change
- blocker recurrence ("eleven of the last fourteen entries")
- collaborator count and turnover
- skill-mention frequency by quarter

One carve-out survives, deliberately narrowed rather than removed:
**no composite score of the person.** A "wellbeing: 4/10" or "engagement
index" is a number attached to how someone is doing, and a number
attached to how someone is doing invites tracking it week over week.
That was the real target of the original restriction, and it is worth
keeping while everything around it goes.

### 4. User-set schedules on all seven uses

*On request unless stated* is replaced by: **on request by default, and
on a user-set schedule where Kene configures one.**

The original reasoning conflated two different things. An analysis
arriving unrequested is intrusive. An analysis arriving on a cadence
the person deliberately configured is not — the consent happened at
setup and stands until revoked. A standing request is still a request.

Three of the seven are actively *better* scheduled, because they are
the classic important-but-never-urgent tasks that simply don't happen
otherwise:

- **Use 7, résumé freshness** — quarterly. Nobody has ever
  spontaneously wondered whether their résumé still matches their work.
- **Use 3, skill drift** — quarterly. Same reason, higher stakes: the
  costly direction (work involves something the résumé omits) is
  invisible from the inside.
- **Use 1, self-assessment** — annually, tied to review season.

Defaults: everything off. A schedule exists only where Kene set one.
Every scheduled delivery carries a one-line way to change the cadence
or stop it, and stopping takes one message, not a settings expedition.

### Use 5 keeps one extra step

Use 5 is trajectory over time, and it is the one place where the timing
of an arrival does its own damage independent of the content.

Schedules are allowed here like everywhere else — with one difference:
**the scheduled delivery is an offer, not the analysis.**

> "It's been six months since the last trajectory read. Want one?"

The standing configuration sets the cadence. A live yes releases the
content. This is not a softened version of the on-request rule; it's a
different mechanism that gets Kene the schedule he asked for while
removing the single case where a scheduled arrival lands badly — a
six-month retrospective showing up unannounced in a hard week.

## Part 3 — The one restriction that stays

**No clinical or diagnostic language.** Not burnout, depression,
anxiety, ADHD, autism, bipolar disorder, trauma response, or any other
term whose meaning comes from a diagnostic manual.

This survived a direct challenge, so the reasoning is written out
rather than asserted.

**The data is selected for difficulty.** The check-in prompts ask what
got hard this week. A journal built by those prompts over-represents
problems relative to a life. Any pattern-reader over that corpus finds
distress in nearly everyone, because the corpus was constructed to
collect it. The base rate is wrong before the analysis begins.

**A journal cannot run a differential.** Four months of flatness and
fatigue is produced by thyroid disease, anaemia, sleep apnoea, grief, a
bad manager, a long commute, and a dozen other things. Ruling those out
is what makes a diagnosis a diagnosis. A text corpus of work entries
contains no information about any of them.

**The label displaces the right next step.** Someone who accepts
"burnout" from a tool stops looking for the thyroid result. The
conditions above are largely treatable and the failure mode is a person
managing a wrong explanation for a year.

**Labels are sticky in a way observations aren't.** A diagnosis
reorganises how a person reads their own history, and it is very hard
to un-hear. "The same blocker appears in eleven of fourteen entries" is
something Kene can reconsider next month when the twelfth goes
differently.

**The audience is wider than Kene.** This package is built for resale,
and `20-interests-profile` names the intended audience explicitly:
secondary schools, universities, youth groups, churches and mosques.
A job-hunting tool handing teenagers mental-health labels is a
materially different proposition from one handing Kene an observation
about his own quarter.

**And the label buys nothing.** This is the load-bearing reason. Compare:

> The same blocker appears in eleven of the last fourteen entries.
> Shipping mentions have halved since March. Scope has grown in one
> direction only — headcount — while the technical surface hasn't
> moved in two quarters.

> You have burnout.

The first is longer, more specific, more checkable, and tells Kene what
to change. The second tells him what he *is*. The first is what a good
reading of a journal actually produces; the second is a compression of
it that loses every actionable detail and adds five risks.

So the line isn't *less analysis*. It's **much more analysis, in
ordinary descriptive language, about the work rather than the person.**
That is strictly more useful than the diagnostic version, which is what
makes this a restriction worth keeping rather than a limitation to
apologise for.

If Kene wants to talk about how he's doing, a person is the right
audience — and this skill saying so once, plainly, when the material
warrants it, is within scope. Naming a condition is not.

## What this addendum doesn't change

- No table in `shared/applications_db_schema_addendum.sql` changes.
- `16-career-pulse/SKILL.md` is not rewritten — house pattern, base
  file stays what it was.
- Rule 7 is untouched. Every candidate fact, including anything a
  reflect pass produces, still routes through `07-context-architect`.
  A synthesis is a weaker claim than a journal entry, not a stronger
  one, and it earns no shortcut.
- The soft-delete behaviour, the 30-day grace window and the
  four-quarter collapse floor are all unchanged.
- LinkedIn monitoring keeps its ceiling — monthly by default, weekly
  at the very most, export preferred over fetch. That was never a
  restriction on *scheduling* (cron job 11 is already monthly); it's a
  frequency and method ceiling, and the asymmetry justifies it: Kene's
  LinkedIn account is his professional identity and this package's
  primary outreach channel, while his own profile changes maybe four
  times a year. Daily polling buys nothing and risks the channel.

## Reference

- `shared/pipeline-rules-addendum.md` — Rule 7; Rule 15 on conversation
  scope, which names this skill's trajectory reading directly; and Rule
  17 on facts deleted from outside this package. **Numbering note**: the
  journey-graph rule was drafted as "Rule 15" before the merge resolved
  a collision between the two packages' addenda. It is Rule 17. Rule 15
  in the merged file is MERGED-26's conversation-scope rule — a
  different rule, and one this file's Part 2 depends on.
- `shared/pipeline-rules.md` — Rules 2 and 5.
- `hermes-capability-audit-ADDENDUM-v2.md` §A7 — the Hindsight
  findings this draws on.
- `16-career-pulse/SKILL.md` — the seven uses, and the original
  restrictions Part 2 amends.
