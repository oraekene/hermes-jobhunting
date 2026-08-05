---
name: job-hunting-social-discovery-outreach
description: "Find job leads on social platforms and draft outreach"
metadata:
  hermes:
    tags: [job-hunting, social-discovery-outreach]
    category: job-hunting
    related_skills:
      - job-hunting-discovery
      - job-hunting-contact-enrichment
      - job-hunting-cold-prospecting
---

# Social Discovery & Cold Outreach

## When this skill applies

Use this skill to search social platforms (X/Twitter, Reddit, LinkedIn, Instagram, Facebook, Threads, TikTok) for job leads and hiring posts, and to draft or send cold outreach — DMs, emails, and public replies — to individual recruiters/hiring contacts. Triggers: a hiring-style post found on social media, a request to cold-DM/cold-email/reply to a specific contact, or a request to search a platform for open roles. Reads references/platform-capability-matrix.md before touching any platform to decide direct-send vs cued-draft for that platform+action. Does NOT override shared/pipeline-rules.md Rule 1 — every send, on every platform, still needs Kene's explicit per-message Telegram approval; this skill only changes *how* an approved message reaches the platform (API call vs a drafted message Kene pastes himself), never *whether* it needs approval. Also holds inactive stubs for quote-posting and original posting, reserved for a future personal-branding/content-creation feature — do not build those out under this skill without an explicit separate request.

Origin: Kene's request to (1) extend job discovery/application onto social
platforms, following whatever instruction the posting itself gives —
DM if it says DM, open the link if it gives a link — and (2) build cold
DM/email outreach, sent by Hermes directly where that's actually possible,
drafted-and-cued where it isn't.

This is two jobs sharing one skill because they share the same first
question for every platform: **what can actually be automated here, and
what can't** — see `references/platform-capability-matrix.md`, which this
skill treats as the single source of truth and re-reads every time rather
than assuming last month's answer still holds (platform policy changes
faster than this file will).

## Part A — Social job discovery

A new source type, `social_listening`, extends `01-job-discovery`'s
`sources.yaml` rather than replacing anything there: platform, search
terms/hashtags/subreddits, poll cadence — same shape as any other source
entry, just a new `type`.

Every post this turns up gets classified before anything else happens:

- **`apply_link`** — the post links to an actual application (job board,
  ATS, company careers page). Treat exactly like any other discovered
  posting: `posting_url` feeds the existing `01-job-discovery` →
  `02-jd-parser` → ... → `10-approval-and-submit` pipeline unchanged,
  `source_board` set to the platform name. Nothing new to build here —
  this is just a new *source*, not a new *path*.
- **`dm_instructions`** — the post says some version of "DM me" /
  "message me directly." Hand off to Part B with the post's own CTA
  preserved as `trigger_context` (see the schema file) — what the poster
  actually asked for is the ground truth for how that specific outreach
  gets shaped, not a generic cold-DM template.
- **`email_instructions`** — same as above, routed as a cold email
  instead.
- **`reply_instructions`** — the post asks for a public reply instead of
  a private one — "comment your portfolio," "reply with your resume
  link," "drop your GitHub below." Hand off to the new Part C, not
  Part B — a public comment is a structurally different artifact (it's
  visible to everyone reading the thread, not just the poster) and gets
  its own drafting/approval flow, even though it shares the same
  personalization step as a DM.
- **`unclear`** — ambiguous CTA, or a personal/informal post that reads
  like a lead but doesn't commit to a channel. Staged as a flagged
  discovery in the normal digest for Kene to read and decide on by hand.
  No auto-action.

### How discovery actually searches — queries aren't fixed

Social posts don't use consistent language for "we're hiring" or "I need
someone" the way a job board listing does — the phrasing space is huge
and often oblique ("looking for someone who can just handle this,"
"anyone good with X want to help out"). A fixed keyword list would miss
most of it. Three query sources feed `social_listening`, not one:

- **Manual** — Kene sets exact queries/hashtags/subreddits himself,
  full control, always available regardless of the other two.
- **Hermes-generated** — drafted from Kene's full profile/memory bank
  (titles, skills, domains), deliberately broad and creative rather than
  literal, since the target phrasing is unknown in advance.
- **Example-guided** — Kene pastes real example posts he's seen (leads
  or near-misses), and Hermes generates queries by generalizing from
  what actually worked as an example, not by re-searching the example's
  exact words.

All three coexist rather than picking one — see
`references/discovery-query-design.md` for the generation process, the
self-improving query loop, and the reasoning for keeping manual override
always available regardless of how good the automated side gets.

## Part B — Cold outreach

Where `contact.handle_or_address` isn't already known, `22-contact-
enrichment` supplies it — both who the contact actually is
(hiring-manager/decision-maker/recruiter-track, per that skill's Part A)
and their verified email (Part B). **Hiring manager and decision maker
are the primary target throughout this skill, not recruiter-track** —
when both get identified for the same opportunity, the primary draft
targets the former; a recruiter-track contact is staged as its own
separate, differently-framed outreach, never merged into one message
and never given equal billing by default.

Every draft is built the same way regardless of platform — pull
personalization hooks from `07-context-architect`'s memory
(`domain-knowledge.md`, STAR bank, and now `16-career-pulse`'s journal for
anything more recent than the last memory refresh), run any factual claim
through `09-risk-tactics-gate` exactly like a resume/cover-letter claim
would (Rule 2 doesn't stop applying just because the artifact is a DM
instead of a document), then classify against the capability matrix to
decide the send path. **Before any of that**: check `shared/output-
templates.yaml` for an `artifact_type: cold_dm`/`cold_email` entry
matching this draft's `trigger.type`/`contact.relationship` — no fixed
content formula exists as a base default yet for this artifact type (per
`21-output-templates/references/elicitation-checklists.md`), so a matched
template *is* the structural guide; unmatched drafts proceed with
whatever general drafting judgment this skill already applies.

### The three send tiers

1. **Tier 1 — API-send-capable, approval-gated.** An official, ToS-
   compliant API exists for sending *this kind* of message to *this kind*
   of recipient. Hermes composes the message, sends Kene the same kind of
   per-message Telegram approval `10-approval-and-submit` already uses,
   and only calls the send API on an explicit "approve" reply tied to
   that specific message. Today (see the matrix) this is realistically
   just X/Twitter DMs, and only if Kene has set up paid API access
   himself — nothing here ships that access for him.
2. **Tier 2 — technically sendable, policy-risky.** An API exists and
   could technically fire the send call, but doing so for *unsolicited
   cold* outreach specifically falls outside that platform's acceptable-
   use policy (Reddit's compose endpoint is the clearest example — see
   the matrix). This skill does not automate sending here, approval or
   not, because the suspension risk lands on Kene's actual account, not
   on Hermes. Draft only, handed to Kene as a cued message.
3. **Tier 3 — no send capability, period.** No API, official or
   unofficial-but-safe, for this action on this platform (LinkedIn cold
   messaging, Instagram/Facebook cold DMs, TikTok DMs entirely). Draft
   only, cued.

**Tier 2 and Tier 3 get identical treatment on purpose** — the
distinction between "can't" and "can-but-shouldn't" matters for *why*
this skill behaves the way it does, not for *what* Kene experiences.
Either way he gets a fully drafted, personalized message and sends it
himself.

### Cued handoff format (Tier 2 / Tier 3)

One Telegram message per contact, not a batch digest — same "each
application gets its own message and its own explicit reply" discipline
`10-approval-and-submit` already uses, extended here to outreach:

- Platform + contact handle/profile link
- The full drafted message text, ready to paste with zero edits needed
- One line naming which post/CTA prompted this (so Kene isn't
  re-deriving context from a stale memory of scrolling social media)
- A `mark_as_sent` reply option — once Kene pastes and sends it himself,
  he confirms back so the outcome gets logged (Rule 4 applies to outreach
  the same as applications: every attempt gets logged, not just the ones
  that worked)

### Volume discipline

Even on Tier 1, this skill inherits `shared/tier-config.yaml`'s spirit:
volume caps govern how many outreach drafts get *prepared* per day, never
how many get *sent* — sending was never unattended to begin with. On
Tier 2/Tier 3 platforms specifically, keep per-platform daily draft
volume low regardless of the general tier config, because the platforms
themselves rate-limit and pattern-detect low-karma/new-relationship
outbound messaging (see the matrix's per-platform notes) — a volume this
skill *could* draft is not the same as a volume Kene could safely send
even by hand.

## Part C — Public replies

For `reply_instructions` posts specifically: the post asked for a public
comment, not a private message — check `shared/output-templates.yaml`
for an `artifact_type: social_reply` match the same way Part B does,
then draft (personalization hooks, `09-risk-tactics-gate` check), and
route through the capability matrix's **reply/comment** action for that
platform, which is not always the same tier as that platform's DM
action. Notably: LinkedIn's DM
tier is 3 (no accessible send path at all), but commenting under Kene's
own identity uses a genuinely self-service permission
(`w_member_social`) LinkedIn makes available without partner approval —
so LinkedIn replies sit at **Tier 1**, even though LinkedIn DMs don't.
See the matrix's updated rows before assuming a platform's DM tier
carries over to its reply tier; it usually doesn't.

Cued handoff for any reply that lands at Tier 2/3 follows the exact same
one-per-contact format Part B uses, just labeled `[REPLY]` instead of
`[DM]`/`[EMAIL]` so Kene knows this one is going up publicly, under his
name, visible to everyone in the thread — worth a slightly more careful
read before approving than a private message would need.

## Stubs — reserved for a future personal-branding feature

Two action types are defined in the schema (`quote` and `post` in
`cold-dm-email-schema.md`'s `message.channel` enum) but **not
implemented** by this skill — no drafting logic, no send-tier wiring, no
approval flow. They're placeholders for a later, separate feature: Kene
building an original-content/personal-branding presence rather than
outreach to a specific contact. Worth noting now, not building now: this
is exactly the use case the posting-scheduler MCPs (Postiz, PostFast) —
mentioned in the matrix as *not* useful for DM-sending — are actually
built for. When that feature gets scoped, start there rather than
wiring quote/post through this skill's send-tier logic, which was
designed for 1:1 outreach, not content publishing.

## Where this plugs into existing rules

`shared/pipeline-rules.md` Rule 1 already reads "...or send an email, or
send a message to a recruiter" — this skill is that rule's existing scope
applied to a new channel, not an exception carved out for it. See
`shared/pipeline-rules-addendum.md` for the two small, additive rules
this skill needs (a send-tier rule and a claims-in-DMs rule) — additive
because Rule 1 through Rule 5 already cover everything else without
modification.

## Reference files

- `references/platform-capability-matrix.md` — what's actually true today,
  per platform, per action (DM, reply, and read), with sourcing notes
  and a re-verify cadence.
- `references/discovery-query-design.md` — how `social_listening` queries
  actually get built (manual, Hermes-generated, example-guided) and the
  self-improving query loop.
- `../22-contact-enrichment/SKILL.md` — how a missing `contact.
  handle_or_address` gets identified and enriched, hiring-manager/
  decision-maker prioritized throughout.
- `references/cold-dm-email-schema.md` — **the confirmed, official
  schema** for every outreach record (DM, email, and now reply). Kene
  confirmed this shape stands as-is; only the content-generation rules
  that fill `message.body_draft` are still coming separately — the
  schema itself doesn't change when they arrive.
