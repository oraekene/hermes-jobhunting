# LinkedIn Connection Flow — the connect-then-message state machine

## The gap this closes

`cold-dm-email-schema.md`'s `contact.relationship` field
(`stranger | inbound_invited | 1st_degree | warm_intro`) was a
snapshot, not a workflow — it recorded the relationship at draft time
and stopped there. For a `stranger` target on LinkedIn specifically,
that's actually not enough to act on: you cannot send a standard DM to
a stranger at all. Something has to connect first, that connection has
to be accepted, and only then does the drafted DM become sendable. This
file is that missing middle — a real state machine, not a label.

**This is separate from the InMail path** (`inmail-credits.md`), which bypasses the connect-first requirement entirely at
the cost of a credit. A target with `contact_priority: hiring_manager`
and no InMail budget available routes through this flow; one with
InMail budget available skips straight to that file's path. Routing
logic lives in the updated `platform-capability-matrix.md`.

## States

```
not_connected
  → note_drafted
  → note_awaiting_approval
  → request_sent_pending_acceptance
      → accepted → dm_draft_unlocked
      → declined
      → expired          (~6 months, no action taken by either side)
      → withdrawn         (Kene pulls it back manually)
```

`dm_draft_unlocked` is the only state from which
`14-social-discovery-outreach`'s normal Part B drafting/approval flow
for the actual DM is allowed to proceed for a `stranger`-relationship
LinkedIn target. Nothing skips this — a DM draft for a not-yet-
connected LinkedIn stranger can exist (nothing stops Hermes from
writing it in advance, see "draft-ahead" below) but its own
`approval.status` cannot move past `drafted` until the linked
connection record reaches `accepted`.

## Schema extension — new `connection` block

Added to `cold-dm-email-schema.md`'s `social_outreach` record,
populated only when `contact.platform: linkedin` and
`contact.relationship: stranger`:

```yaml
connection:
  required: true                 # false for 1st_degree/warm_intro
                                  # targets, or non-LinkedIn platforms —
                                  # this whole block is inert otherwise
  status: "not_connected"        # not_connected | note_drafted |
                                  # note_awaiting_approval |
                                  # request_sent_pending_acceptance |
                                  # accepted | declined | expired |
                                  # withdrawn
  note_draft: ""                 # <=300 chars, built by
                                  # cold-dm-content-formula.md's
                                  # connection-note variant (own
                                  # register rules — see below, a
                                  # connection note is not a shrunk DM)
  note_char_count: null
  approval_sent_at: null
  approval_decided_at: null
  send_method: ""                # computer_use_approved | manual_cued
                                  # — see "How the send actually
                                  # happens" below
  sent_at: null
  check_method: ""                # kene_confirmed | computer_use_check
  last_checked_at: null
  accepted_at: null
  expires_at: null                 # sent_at + ~6 months, LinkedIn's own
                                    # FAQ figure as of this check — see
                                    # re-verify note below
  free_tier_note_quota_used: null  # only tracked if Kene's account is
                                    # non-Premium; see inmail-credits.md's
                                    # sibling budget-tracking pattern
```

Extends the schema exactly as its own header instructs ("extend it...
rather than replace it") — no existing field changes shape.

## Draft-ahead is fine; sending is what's gated

Nothing about honest evidence or personalization requires waiting for
acceptance to *write* the DM — the persona/target-research/segment-
research material that would inform the DM's content is already
available at connection-request time. Drafting the DM immediately
(status: `drafted`, sitting inert) means zero latency between
acceptance and Kene being able to approve-and-send the actual message —
the only thing acceptance unlocks is `approval.status` being allowed to
advance past `drafted` for that record. This is a genuine efficiency
gain over waiting to draft until after acceptance, with no honesty cost
either way.

## How the send actually happens — the resolution of the automation-scope disagreement

Two things were true at once in that conversation, worth restating
plainly because they resolve each other rather than conflicting:
automating the request send carries a real, documented risk regardless
of whose session drives it (LinkedIn's own User Agreement §8.2 names
"cloud" tools *and* other automation together, and the detection
signals that actually get accounts restricted — send velocity,
acceptance-rate drop-off, near-identical note text across many sends,
skipping the profile-view-before-connect pattern a real human
exhibits — are behavioral, not session-provenance-based, so running
from Kene's own logged-in machine via `computer-use` closes the
IP/device-fingerprint gap real third-party tools like HeyReach got
flagged on, but doesn't close the behavioral-pattern gap, which is the
one LinkedIn's own acceptance-rate throttling and the roughly 23%
restriction-rate figure are actually about). And separately: the
outcome Kene actually asked for as the fallback — draft automatically,
gate only the physical send behind his approval — is also exactly the
general principle he set for the rest of this pipeline ("automation
should stop at the point of sending... it should auto draft, only not
auto send"). Those aren't in tension. The design below is the fallback
he named, not a downgrade from what he asked for — it's the same
principle applied consistently to this one extra step, on the argument
that this step is, mechanically, also a send.

**`send_method: computer_use_approved`** — the actual behavior:

1. Note gets drafted automatically (`cold-dm-content-formula.md`'s
   connection-note formula, below), no manual trigger needed.
2. Cued to Kene, same one-message-per-contact Telegram format Part B
   already uses for Tier 2/3 DMs — platform, target, the note text
   exactly as it would be typed, one line naming what prompted this
   target (persona match / manual_request / discovered posting).
3. On explicit "approve," `computer-use` drives Kene's own logged-in
   LinkedIn session (session model 3, `site-access-model.md`) to open
   the target's profile, click Connect, paste the approved note, and
   send — run only when Kene is actually at his machine, per that
   file's existing constraint, never as an unattended background job.
   This is mechanically identical to what `10-approval-and-submit`
   already does for filling and submitting an application form after
   approval — same tool, same session model, same "approved, then
   executed" shape, just a different target site.
4. Volume stays paced like a human would pace it even though the click
   itself is automated — natural variable delay between sends within
   an approved batch, not a tight loop, and daily/weekly volume stays
   under `platform-capability-matrix.md`'s existing per-platform notes
   on safe send rates (LinkedIn's own soft caps run roughly 100-200
   invitations/week depending on account standing — re-verify this
   figure at the same cadence as the rest of the matrix, LinkedIn
   adjusts it without much notice).

**`send_method: manual_cued`** remains available as a fallback (Kene
pastes and sends by hand) for whenever he'd rather not have `computer-
use` touch LinkedIn at all for a given batch — both paths write to the
same `connection` block, `send_method` just records which happened.

This is a genuine escalation from the original all-Tier-3-is-draft-only
posture, and it's worth being honest that it raises Kene's own account
risk somewhat above the zero-touch draft-only baseline — the mitigation
is real (his own session, paced sends, per-message approval, note
variation rather than one template blasted verbatim) but not a
guarantee. `site-access-model.md`'s "Avoid" category is updated to
reflect this as a deliberate, approved exception, not a blanket rule
change — see that file's update below.

## Connection-note register — distinct from the DM formula

`cold-dm-content-formula.md`'s hook/value-prop/ask/sign-off structure
is built for a DM, not a 300-character note whose entire job (per every
source on this) is "give a real reason to accept," not to pitch:

- **No ask, no value-prop.** A connection note that pitches inside 300
  characters reads as presumptuous before any relationship exists at
  all — the actual conversation happens after acceptance, in the DM.
- **One real, checkable reason to connect** — the same hook material
  cold-dm-content-formula.md uses, compressed to a single clause: "saw
  your post about X" / "researching Y, your work on Z looks relevant."
- **No sign-off needed** — name is already attached to the request.
- Target: 120-180 characters even though the cap is 300 — every
  sourced figure agrees shorter outperforms filling the field, and
  leaving headroom protects against name/company personalization
  variables pushing a template over the limit.
- **Free-tier accounts get roughly 5 personalized notes/month** before
  LinkedIn requires note-less requests (a 2024-era change per current
  sourcing) — `free_tier_note_quota_used` tracks this if Kene's account
  isn't on a paid tier, so the drafting step knows whether a note is
  even an option for a given send without checking LinkedIn's UI by
  hand each time.

## Detecting acceptance — no API, so two real methods, not one assumed

- **`kene_confirmed`** — the default. The cued approval message's
  `mark_as_sent` reply option (already Part B's pattern) gets a second
  option once a request is sent: a later "connected" reply Kene sends
  whenever he notices the acceptance (LinkedIn's own notification, or
  next time he's in his network tab) — zero extra polling, purely
  event-driven off something Kene was going to see anyway.
- **`computer_use_check`** — optional, for volume: a periodic,
  Kene-triggered (not cron-scheduled, per `site-access-model.md`'s
  existing "occasional, light-touch, run when Kene's actually at his
  machine" constraint — this specifically should not become a
  background poll loop) check of the "My Network → Sent invitations"
  page, diffing against the last recorded state to find newly-accepted
  requests in bulk. Reserve this for when the pending-request count
  makes `kene_confirmed` genuinely tedious, not as the default.

## Expiry

LinkedIn's own connections FAQ states invitations expire after six
months, with up to two reminder notifications sent to the recipient
before that — treated here as the authoritative figure over the
several conflicting third-party outreach-tool blogs that claim
requests never expire (worth a periodic spot-check against LinkedIn's
own help pages directly, same re-verify discipline as the platform
matrix, rather than trusting either side of that disagreement
indefinitely). A weekly check flips `expired` for any
`request_sent_pending_acceptance` record past `sent_at + 6mo` with no
`accepted_at` — folds into the new cron job below rather than getting
its own separate schedule.

## New cron job

```
hermes cron create "0 8 * * 3" \
  "Run job-hunting-social-discovery-outreach's connection-flow maintenance pass: for every social_outreach row with connection.status = request_sent_pending_acceptance, check connection.sent_at against a 6-month window and set status=expired for anything past it. Surface a short digest of newly-expired requests only — do not re-draft or re-send automatically. This job never checks LinkedIn itself; acceptance detection stays kene_confirmed or Kene-triggered computer_use_check per linkedin-connection-flow.md, never a scheduled read of LinkedIn's own pages. Use [SILENT] if nothing expired this week." \
  --skill job-hunting-social-discovery-outreach
```

Deliberately date-math-only, no LinkedIn read at all — keeps the one
LinkedIn-touching part of this system (the acceptance check) fully
under Kene's direct trigger, consistent with `site-access-model.md`'s
existing caution about scheduled LinkedIn access.

## Where this plugs in

- `14-social-discovery-outreach/references/cold-dm-email-schema.md` —
  the `connection` block above.
- `14-social-discovery-outreach/references/platform-capability-matrix.md`
  — LinkedIn's "Send connection request" row (new) and the updated
  access-model note.
- `shared/site-access-model.md` — the "Avoid" category's LinkedIn
  automated-connection-request entry, updated to name this flow as the
  approved exception.
- `shared/pipeline-rules-addendum.md` — Rule 12/13 (draft-freely /
  connection-gates-DM-readiness) codify this file's two core
  behaviors as pipeline-wide rules, not just LinkedIn-specific notes.
