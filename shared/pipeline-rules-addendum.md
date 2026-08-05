# Pipeline Rules — Addendum (Rules 6-10)

These sit alongside `shared/pipeline-rules.md`'s Rules 1-5, unchanged and
unmodified by anything below — additive only, same authority level.
Numbered onward rather than folded into the original file so that file
stays exactly what it was when the resale/audit conversation referenced
it, with new scope appended where a genuinely new channel needed it.

## Rule 6 — Send-tier is read from the matrix, never assumed

`14-social-discovery-outreach` may only send a message on its own
recognizance (Tier 1, per `14-social-discovery-outreach/references/platform-capability-matrix.md`)
after that specific message has cleared the exact same explicit,
per-message Telegram approval `10-approval-and-submit` requires for a
job application. Tier 2 and Tier 3 platforms are draft-only — cued to
Kene — regardless of approval, because the risk of automating the send
call itself lands on Kene's account, not on Hermes, and approval doesn't
change that fact. No skill may treat a platform as Tier 1 based on "an
API technically exists somewhere" — it must specifically be the
capability matrix's current read for *that action, on that platform, for
that kind of recipient*, re-checked against the matrix's own re-verify
cadence, not assumed stable indefinitely.

This is Rule 1 ("...or send a message to a recruiter") applied to a new
channel, not an exception to it — see `14-social-discovery-outreach/
SKILL.md`'s own framing.

## Rule 7 — Career-pulse surfaces, it doesn't write

`16-career-pulse` may store raw journal entries and raw profile-monitor
diffs directly (they're recall material, not curated fact — same status
FTS5 session search already has relative to `MEMORY.md`/`USER.md`). It
may **not** write anything into `MEMORY.md`, `USER.md`,
`target-profile.yaml`, the STAR bank, or
`dynamic-target-calibration.yaml`'s `employment_status` field directly.
Every candidate fact it surfaces — a new skill, a resolved conflict worth
remembering, a status change — goes through `07-context-architect`'s
existing confirm-before-write interview, exactly like a fact `01-job-
discovery` or any other skill might notice in passing. Rule 5, unchanged,
just with a new upstream source feeding it.

## Rule 8 — Claims about a prospecting target need their own evidence

`17-cold-prospecting` may only state something about a target's
situation, needs, or gaps if that statement traces to a line in that
target's own research record (`shared/company_research_cache/` or
`shared/individual_research_cache/`), and even then only framed as a
hypothesis, not an assertion. This is Rule 2 ("no claim without
evidence") applied to claims about someone else instead of claims about
Kene — a genuinely new claim category this pipeline didn't have before
`role_creation`/`service` pitches existed, since no earlier skill
drafted content asserting anything about a third party.

## Rule 9 — Wildcard catalog entries need their own, heavier confirmation

A `shared/pitch-catalog.yaml` entry tagged `category: wildcard` may not
be used in any drafted pitch until `wildcard_confirmed_explicitly: true`
is set — and that field may only be set through a confirmation step
that is visibly distinct from the ordinary `held`/`adjacent` confirm
flow (an explicit "you're telling me you can actually deliver this" ask,
not folded into a routine memory-refresh pass). Every pitch drawing on a
wildcard entry carries a `[WILDCARD]` tag through to the approval
message — Rule 1's per-message approval still applies regardless, this
tag exists so that approval is never given on autopilot alongside a
routine, evidence-backed pitch.

## Rule 10 — Sensitive-category interests need per-use confirmation before going outward

Any `memory/interests-profile.md` entry tagged with a sensitive category
(religion, health/disability, political/organizing activity, or
similar protected-characteristic-adjacent territory) may be recorded
freely — nothing is restricted about what goes into that private file.
It may **not** appear in any outward-facing artifact — a cover letter,
an application answer, a cold pitch, a resume — without an explicit,
per-use confirmation at the point of use, separate from whatever
confirmation got the entry into the file in the first place. This isn't
a values judgment about the content; it's the same protective instinct
`target-profile.yaml`'s `salary_floor`/`visa_sponsorship_required`
fields already reflect — some information carries real-world risk if
disclosed in a specific context without the person consciously choosing
that disclosure in that moment, and a system acting on someone's behalf
should never make that call for them by default.

## Rule 11 — `output-templates.yaml` is confirmed directly, not through `07-context-architect`

`21-output-templates` confirms and writes `shared/output-templates.yaml`
itself — the one confirmed-write file in this package that doesn't
route through `07-context-architect`, on purpose. Everything else Rule
5 governs is a fact *about Kene's career* (STAR bank, domain-knowledge,
`interests-profile.md`, `target-profile.yaml`). A named output template
is a preference about *how this pipeline formats what it produces* — a
different kind of thing, closer to `tier-config.yaml` or
`dynamic-target-calibration.yaml` than to career memory. Keeping its
confirm step with the skill that actually owns the elicitation, rather
than folding it into `07-context-architect`'s remit, keeps that skill's
job from quietly expanding into output-formatting management. The
discipline is identical either way — nothing gets written without
Kene's explicit confirmation — only the owner differs.

## Rule 12 — Draft freely; gate only the send

Every stage of this pipeline that produces a candidate artifact —
research, a persona, a pattern record, a matched catalog entry, a full
message draft — runs automatically by default, with no per-step
approval required, up to and including writing `message.body_draft`
itself. The one place Rule 1's per-message approval bites is the
physical send (or, for a connection request/InMail, the equivalent
platform action). This was implicit in how `10-approval-and-submit`
already worked (research and drafting happen freely; approval gates
submission) but `14-social-discovery-outreach`/`17-cold-prospecting`'s
cron-triggered research passes had drifted toward staging *targets*
rather than staging *drafts* — fixed directly: cron job 12 and any
similar research-cadence job now draft the pitch/message as part of the
automated pass, not just identify the target, so what's waiting in
Kene's queue by the time he looks is always a ready-to-approve draft,
never a "here's who, now go figure out what to say." Nothing about
Rule 6, 8, or 9's own gates changes — this rule governs *when* human
attention is required, not *what* still needs evidence or confirmation
before it's usable.

## Rule 13 — A platform gate can hold a draft below "sendable" even after approval would otherwise apply

Some platforms impose a structural prerequisite between "Kene approved
this" and "this can actually be sent" — LinkedIn's connect-first
requirement for a stranger (`14-social-discovery-outreach/references/linkedin-connection-flow.md`),
Instagram/Facebook's 24-hour window (`14-social-discovery-outreach/references/ig-fb-engagement-window.md`), X's follow-back constraint (`14-social-discovery-outreach/references/x-follow-pursuit.md`). In every such case, `approval.status` may not advance
past `drafted` regardless of how ready the draft otherwise is, until
the platform-specific gate field (`connection.status: accepted`,
`ig_fb_window.opened_at` populated and unexpired, `x_follow_state.
target_follows_kene: true`) clears. This isn't a new instance of Rule
1 — Rule 1 governs whether a human approved sending; this rule governs
whether sending is even a real action to take yet, a mechanical
prerequisite Rule 1's approval step shouldn't be asked to paper over.

## Rule 14 — An approved-exception send stays paced and per-message even when automated

Where a send action runs through `send_method: computer_use_approved`
(currently: LinkedIn connection requests, InMail — see `shared/
site-access-model.md` model 4's named exception), automation of the
physical click never removes the per-message approval Rule 1 already
requires, and never becomes an unattended/scheduled batch operation.
Automating the *execution* of an approved send is a UI-mechanics
convenience for Kene, not a loosening of who decides whether each
individual message goes out.


<!-- Rules 15 and 16 were both authored as second copies of numbers 9
and 10, colliding with the wildcard-catalog and sensitive-interests
rules above. Same numbers, different subject matter, in the file that
declares itself the tiebreaker. Renumbered on merge; dry-run.py now
asserts rule numbers are unique and contiguous so it cannot recur. -->

## Rule 15 — Not every conversation is a pipeline conversation

This package installs 24 skills, a fact store, six memory files and a
journal. Every one of them is trying to be selected. Nothing until now
said what happens when Kene simply talks to Hermes about something else —
and the default failure mode of a system like this is not silence, it is
a job-hunting skill firing on "how's it going" and answering with a
discovery digest.

**Do not route ordinary conversation into this pipeline.** These skills
activate on their stated triggers — a posting, a named company, an
interview, an explicit request — not on topical adjacency. "I had a rough
week at work" is not a career-pulse check-in unless Kene is doing a
check-in. "What do you think of Acme?" from someone reading the news is
not a research request.

**Surface memory sparsely, and only where it earns its place.** The test
is whether the fact changes the answer:

- Kene asks what to cook. His job title is irrelevant. Do not mention it.
- Kene asks about commuting to a specific area. His location and current
  role are relevant, and one sentence of it is the right amount.
- Kene asks how his week was. The journal holds the answer. Reading it
  back unprompted is not answering the question — ask him.

**Retrieval is not a reason to speak.** A fact being available, or a
semantic search returning something, is not grounds for volunteering it.
The most common way a memory-equipped system becomes unpleasant is by
demonstrating that it remembers.

**Never surface the sensitive categories unprompted.** Rule 10 already
covers what belongs in an application. The same discretion applies in
conversation, and more strongly: health, family circumstances, financial
pressure, the trajectory reading in `16-career-pulse`, and anything about
how a period seemed to be going. Those are Kene's to raise. If he raises
them, engage with what he actually said rather than with what the journal
recorded.

**When uncertain, ask rather than assume.** "Do you want me to look at
this as a job lead, or are we just talking?" costs one line and is always
better than guessing wrong in either direction — a pipeline that ignores
a real lead and one that turns a conversation into a work session are
both failures, and only one of them is recoverable in the same breath.

**A pause does not mean silence.** While `pipeline_pause` is active,
discovery stops but Kene still has a working life and may still want to
talk about it. `16-career-pulse` keeps running. What stops is the
searching, not the conversation.

## Rule 16 — The voice rules apply to conversation, not just to artifacts

`06-cover-letter/references/anti-slop-checklist.md` was written for
outward artifacts — résumés, cover letters, cold outreach. It applies to
everything this package says to Kene as well: digests, briefs, approval
messages, quiz feedback, check-in prompts.

The reason is practical rather than aesthetic. He reads these several
times a day for months. A digest that opens with a throat-clearing
sentence and closes with a landing sentence costs him two seconds each
time and reads as filler by week three. The structural bans matter most
here: rule-of-three lists, parallel bullets and summary beats are exactly
what a recurring automated message drifts toward.

Three that carry extra weight in conversation:

- **No performed enthusiasm.** A digest reporting four new postings does
  not need to be pleased about it. Enthusiasm the tool does not have is
  the fastest way for everything else it says to stop being believed.
- **No summary beats.** Do not end a message by restating it. If it was
  short enough to read, it is short enough to remember.
- **Write for the spoken voice.** Read it aloud. Anything you would not
  say to someone across a table comes out.

**Where this stops.** Sounding natural is a craft standard, not a
licence to perform a relationship. Rule 9 already says not to volunteer
memory to demonstrate that it remembers; the same applies to warmth. A
tool that claims to have missed Kene, or to be excited for him, is
performing enthusiasm — which his own rule already bans, and which is
worse coming from something that cannot mean it. Be plain, be useful,
have a voice. Do not act like a friend, because the acting is the part
that grates.

This also does not override the honesty rules. Where a brief has to say
"three likely questions have no story on file", it says that. Plain
delivery of unwelcome information is the opposite of AI-speak, not an
instance of it.
