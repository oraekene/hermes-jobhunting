# Cold DM / Email Content Formula — the piece `cold-dm-email-schema.md` deferred

**Status: this is that piece.** `cold-dm-email-schema.md` is confirmed
as the *data shape*; its own note names exactly one thing still
missing — "the actual content-generation formula for
`message.body_draft`... opener/hook, value-prop structure, ask
phrasing, sign-off convention." This file is that formula, the direct
outreach equivalent of `06-cover-letter/references/cover-letter-
formula.md`. The schema doesn't change to accommodate it, per its own
note — this slots into the generation step the schema already has a
slot for.

## What was actually missing, precisely (audit, not vibes)

Worth being exact about this rather than waving at "content rules
aren't done yet," since three genuinely different gaps were hiding
under that one sentence:

1. **No structural formula** — no opener/hook → value-prop → ask →
   sign-off breakdown for `message.body_draft`, the thing this file
   now provides.
2. **No banned-phrase / register rules** — nothing telling a draft *not*
   to sound like a template ("I noticed your profile," "I'd love to
   pick your brain") — also this file, see the register rules below.
3. **No per-platform tone/length calibration** — `platform_char_limit`
   existed as a field to *record* a limit, but nothing populated it
   from real numbers or adjusted drafting to fit inside one — this
   file's length table fixes that.

Two more completeness gaps exist in the schema *beyond* content, worth
naming honestly since they were folded into "not built" without being
separated out:

4. **No connection-prerequisite modeling** — `contact.relationship` is
   a static snapshot, not a workflow; see `linkedin-connection-flow.md`, which extends the schema with a `connection`
   block (this is the multi-step-workflow gap, a different kind of
   incompleteness than the content-formula gap — see that file for the
   full audit of what it specifically adds).
5. **No send-path diversity within a single platform** — the schema
   assumed one send method per platform (`api_direct_pending_approval`
   vs `manual_cued`), but LinkedIn alone now has three real send paths
   (connection-gated DM, InMail, Open Profile message) with different
   cost/availability/approval shapes; see `inmail-credits.md`
   and the updated `platform-capability-matrix.md`.

Items 4 and 5 are handled in their own files rather than here, because
they're workflow/routing gaps, not content-generation gaps — mixing
them into this formula would make one file responsible for two
different kinds of incompleteness.

## Structural formula — four parts, every channel

```
[HOOK]  → [VALUE-PROP] → [ASK] → [SIGN-OFF]
```

### 1. Hook (1-2 sentences)

Must anchor to something in `message.personalization_hooks` — never a
generic opener. Concretely, the hook is **one specific, checkable
thing**: a line from their post, a detail from `target-research.md`'s
"what they do," a corroborated pattern from `segment-research.md`'s
`language_they_use` (quoted back in spirit, not verbatim — paraphrase
their framing, don't lift their exact sentence), or the actual CTA
context (`trigger.source_cta_context`) if this is a `dm_instructions`-
triggered draft.

**Banned openers** (any of these in a draft is an automatic rewrite,
not a stylistic nitpick — this is the concrete fix for "doesn't sound
like a LinkedIn message"):
- "I noticed your profile" / "I came across your profile"
- "I'd love to pick your brain"
- "I hope this message finds you well" / any well-wish opener
- "I know this is out of the blue, but"
- Restating the recipient's job title back to them as if it were an
  observation ("I see you're a VP of Engineering at X" — they know
  their own title; this isn't personalization, it's proof the message
  is templated)

### 2. Value-prop (1-3 sentences)

States what Kene actually brings, pulled from the matched
`pitch-catalog.yaml` entry's `one_line_pitch` and, if the persona has
one, framed against `persona.likely_objection` — preempting the
objection reads as more credible than a straight capability list.
`role_creation`/`service` pitches route any claim about the *target*
through Rule 8 before it reaches this section — hypothesis framing
("noticed X — worth exploring?"), never assertion.

### 3. Ask (1 sentence, always)

One concrete, low-friction next step — never "let me know your
thoughts" (too vague to act on) and never a hard pitch-close in the
first message of a sequence. A reply-triggered `dm_instructions` draft
mirrors whatever ask the original post specified rather than
substituting a generic one.

### 4. Sign-off

Name, one-line credibility marker if it isn't already visible on
profile (skip if redundant — recipient can already see Kene's name/
headline on most platforms), no "Best regards" formality on DM
channels; email keeps a conventional sign-off, per the schema's own
`channel` split.

## Register rules — what makes it not sound like a LinkedIn message

- **Contractions on.** Formal register is itself a tell.
- **No stacked qualifiers** ("I just wanted to reach out to see if
  maybe..."). State the thing.
- **Sentence fragments are fine** if a full sentence would sound stiffer
  — match how the recipient's own `language_they_use` reads, when a
  corroborated persona sample exists.
- **No emoji, no exclamation-point enthusiasm** unless the persona's own
  sourced language uses them (rare, and only ever sourced, never
  assumed).
- One idea per message. A hook that also tries to be the value-prop
  reads as trying too hard to fit everything into the first touch.

## Length table — per channel, sourced, re-verify quarterly like the platform matrix

| Channel | Hard platform cap | Practical target | Source note |
|---|---|---|---|
| LinkedIn connection note | 300 characters (all account tiers) | 120-180 characters | Free accounts are additionally capped at roughly 5 personalized notes/month as of the 2024 change — after that, requests must go note-less. Re-verify before relying on the free-tier figure; it's the kind of quota LinkedIn adjusts without much notice. |
| LinkedIn DM (1st-degree) | ~8,000 characters | Under 400 characters | Technical ceiling is generous; every source agrees shorter drastically outperforms longer here regardless of ceiling. |
| LinkedIn InMail | 200-char subject / ~1,900-2,000-char body | Subject under 60 chars, body under 500 | See `inmail-credits.md` — InMail is also one-shot (no follow-up InMail without a prior reply), which changes drafting strategy, not just length: the ask has to be worth the entire credit in one message, no room for a soft first-touch. |
| X DM | Platform-enforced, generous | Under 280 characters (norm-matched to the platform's own voice, not a hard cap) | |
| Reddit DM | Platform-enforced, generous | Under 500 characters | Draft-only per the matrix; length still matters for the cued message Kene actually sends. |
| Cold email | N/A | 100-150 words | Looser than any DM channel — `message.subject` gets its own line-item check (under 50 characters, specific not generic) since subject is most of what determines an open. |

`message.char_count`/`platform_char_limit` in the schema get populated
from this table at draft time, not left null for channels that have a
known limit — closes gap #3 from the audit above.

## Per-trigger-type variation

- **`dm_instructions`/`email_instructions`** (Part B, posting-triggered)
  — hook is the post's own CTA context, ask mirrors what the post
  requested. Least discretion, most externally anchored.
- **`manual_request` / cold-prospecting pitch** (17-cold-prospecting) —
  hook draws from target-research/segment-research per the persona
  fields; value-prop pulls the matched catalog entry; `[WILDCARD]`-
  tagged pitches (Rule 9) get the same formula but the approval message
  still carries the tag regardless of how polished the draft reads.
- **`reply_instructions`** (Part C, public) — same formula, but written
  knowing it's visible to the whole thread, not just the recipient; the
  hook can reference the post directly since replying *is* engaging
  with it publicly, not "noticing" it from the outside.

## Where this plugs in

- `14-social-discovery-outreach/SKILL.md` Part B/C — this is the
  drafting step's actual content logic, replacing "whatever general
  drafting judgment this skill already applies."
- `21-output-templates/references/elicitation-checklists.md`'s
  `cold_email`/`cold_dm` entry — this file is now the **base default**
  a saved template can `append` to or `replace`, per that file's
  existing `application_mode` dial; update that checklist's "no fixed
  formula exists yet" line to point here.
- `17-cold-prospecting/references/ideal-client-persona.md` — supplies
  `likely_objection`/`language_they_use` this formula consumes directly.
- `11-analytics-and-learning` — once enough outreach volume exists,
  this file (not just catalog entries or queries) becomes eligible for
  its own `skill_self_edits`-staged tuning, per `pitch-catalog.md`'s
  existing note that the content formula is tracked separately from
  catalog-level performance so a wording problem and a positioning
  problem never get conflated.
