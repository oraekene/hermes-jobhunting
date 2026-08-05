# InMail Credits — the actual bypass for LinkedIn's connect-first requirement

## What InMail actually is, precisely (this wasn't in the matrix before)

InMail is LinkedIn's own paid feature for messaging someone you're not
connected to — no connection request, no accept step, straight to
their inbox. It comes bundled with a Premium-tier subscription, not
sold standalone:

| Plan | InMail credits/month | Rollover cap | Approx. monthly cost |
|---|---|---|---|
| Premium Career | 5 | 15 | ~$29.99 |
| Premium Business | 15 | 45 | higher tier, check current pricing |
| Sales Navigator Core | 50 | 150 | ~$119.99 |
| Recruiter Lite | 30 | 120 | ~$169.99 |

Figures current as of this check (mid-2026) — re-verify against
LinkedIn's own Premium/Sales Navigator pricing pages at the same
quarterly cadence as the rest of this matrix; LinkedIn adjusts credit
allotments and pricing without much notice, and none of this is
purchasable outside a subscription (LinkedIn's own help pages state
directly that additional credits can't be bought outside the monthly
allotment on Premium/Sales Navigator — only Recruiter's enterprise tier
sells extra packs under contract terms, not relevant at Kene's scale).

**A credit is refunded if the recipient responds within 90 days** —
accept, decline, or reply all count as a response for refund purposes;
only genuine silence costs a permanent credit. **No follow-up InMail is
possible to the same person until they've replied once** — this is the
detail that most changes drafting strategy, not just budget: an InMail
gets exactly one shot, so `cold-dm-content-formula.md`'s length table
already reflects this (subject under 60 chars, body under 500 — the
whole ask has to land in one message, no soft first-touch-then-nudge
sequence the way a connected DM could use).

**Open Profile** is a free adjacent path worth tracking separately: a
Sales Navigator subscriber can message any Premium member who's enabled
"Open Profile," at zero credit cost. Genuinely useful when it applies,
but coverage is partial (only reaches Open-Profile-enabled members) —
never assumed as the primary path, checked opportunistically.

## Budget file — `shared/inmail-credits.yaml.template`

Same shape `shared/enrichment-tier-usage.yaml.template` already
established for tracked, cycle-resetting budgets — reused rather than
inventing a new pattern for what's structurally the same problem (a
capped monthly allowance that needs used/remaining tracking and a
reset date that isn't necessarily the 1st of the month).

```yaml
# shared/inmail-credits.yaml — mirrors enrichment-tier-usage.yaml's
# shape. Auto-updated by 14-social-discovery-outreach on send, not a
# confirm-gated preference file. Kene sets plan/monthly_allowance once
# (matches his actual LinkedIn subscription); everything else tracks
# itself.

plan: null                    # premium_career | premium_business |
                                # sales_navigator_core | recruiter_lite |
                                # none — "none" means InMail routes are
                                # simply unavailable, connection-flow.md
                                # is the only LinkedIn-stranger path
monthly_allowance: null        # set from the table above once Kene
                                # confirms his actual plan
rollover_cap: null
used_this_cycle: 0
available_this_cycle: null     # derived, kept as a field so a draft
                                # step can check availability without
                                # recomputing every time
cycle_resets_at: null
credits_refunded_this_cycle: 0  # incremented when a 90-day-window
                                  # reply is detected — see below
open_profile_used_this_cycle: 0  # tracked separately, doesn't touch
                                   # the credit balance
last_updated_at: null
```

## Routing — how a draft picks connection-flow vs InMail vs Open Profile

Added to `platform-capability-matrix.md`'s LinkedIn section as explicit
routing logic, checked in this order for any `stranger`-relationship
LinkedIn target with `contact_priority: hiring_manager` or
`decision_maker` (InMail is deliberately not the default path for
lower-priority/recruiter-track targets — it's a scarce, one-shot
resource, spent on primary targets):

1. **Open Profile check** — if the target's profile shows Open Profile
   enabled, route here first (free, no credit spent).
2. **InMail** — if `inmail-credits.yaml`'s `available_this_cycle > 0`
   and the target is a high-priority contact, route here. The one-shot
   constraint means this only makes sense when the pitch is genuinely
   ready to be a complete, self-contained ask — not for a target still
   mid-research.
3. **Connection-flow** (`linkedin-connection-flow.md`) — the default
   fallback, no cost, no credit scarcity, works for any target
   regardless of priority tier.

`routing.send_method` in the schema gains a LinkedIn-specific value:
`inmail_api_pending_approval` doesn't exist (no self-serve send API for
InMail was found for individual/Sales-Navigator-tier accounts — this
stays a UI action Kene sends himself or via `computer-use` on his own
session, same approval-then-execute shape as the connection-request
send in `linkedin-connection-flow.md`, not a new automation risk
category). Record it as `send_method: computer_use_approved` or
`manual_cued`, same values connection-flow uses, with `connection.
required: false` and a new `inmail_used: true` flag distinguishing it
from a connection-gated send in the outcome record.

## Refund tracking

`connection`-block-style, added alongside the InMail send record:
`inmail_sent_at`, `inmail_reply_deadline` (`sent_at + 90d`),
`inmail_credit_refunded` (bool, set on `outcome.replied_at` populating
within that window). Doesn't need its own cron job — `11-analytics-
and-learning`'s existing outcome-tracking pass already visits every
`social_outreach` row with a pending outcome; this just adds one more
field it checks while it's there.

## Signup — this is a Kene decision, not an automated one

Nothing here signs Kene up for a plan on its own initiative — same
Rule 11 spirit `output-templates.yaml` already uses (a preference about
how the pipeline operates, confirmed directly). The realistic flow:
Kene decides whether the ROI of a Premium tier is worth it (weigh
against `11-analytics-and-learning`'s reply-rate data once enough
connection-flow volume exists to know whether the connect-and-wait
path is actually the bottleneck it might be), subscribes himself
through LinkedIn's own checkout, then tells Hermes his plan — which
populates `inmail-credits.yaml`'s `plan`/`monthly_allowance` fields and
switches the routing logic above from "InMail unavailable" to live.
