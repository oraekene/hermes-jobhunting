# Instagram/Facebook Engagement Window — tracking the 24-hour gate

## The constraint, restated precisely

Different mechanism from LinkedIn (connect-first) and X (follow-first):
Meta's Graph API only allows messaging within a 24-hour window **opened
by the recipient's own first message**, or via a narrow, shrinking set
of non-promotional Message Tags. There is no cold-initiation path at
all — this is the one platform in the matrix where, unlike LinkedIn
(InMail bypasses it for a fee) or X (Everyone-setting/engagement can
route around it), **no legitimate workaround exists that lets Kene
initiate.** Worth being direct about that rather than implying
tracking alone solves it — tracking here manages a window that has to
be opened by the *other* person, it doesn't create one.

## What tracking actually buys, given that

Not "make the window open" — nothing here does that. What it buys:
knowing the moment it *does* open (so the 24 hours don't quietly lapse
unused), and not re-treating an already-open window as still-blocked
and drafting nothing.

## Tracking — extends `cold-dm-email-schema.md`

```yaml
ig_fb_window:
  opened_at: null                # timestamp of the recipient's first
                                    # inbound message, read via the
                                    # instagram_business_manage_messages
                                    # scope on Kene's own business
                                    # account inbox — read-only, Tier 1
                                    # per the matrix, this is Kene's own
                                    # inbox, not a stranger's
  expires_at: null                # opened_at + 24h, computed not
                                    # separately tracked
  message_tag_used: ""             # one of Meta's current non-
                                    # promotional tags, if this send
                                    # qualifies for one instead of
                                    # riding the open window — re-verify
                                    # which tags are still valid each
                                    # quarterly pass, several were
                                    # retired in April 2026 per the
                                    # matrix's existing note
  messages_sent_in_window: 0
  window_closed_unused: false      # set true if expires_at passes with
                                    # messages_sent_in_window still 0 —
                                    # the actual failure mode worth
                                    # surfacing, not silently dropping
```

## Workflow

1. **Detection is passive, not polled at bot-like frequency** — Kene's
   own IG/FB business inbox is read via the Graph API's own messaging
   scope, which is a legitimate, sanctioned read of his own account,
   not the cold-outreach-adjacent scraping this matrix is generally
   cautious about. A short-interval check here is lower-risk than
   equivalent LinkedIn/X polling specifically because it's reading
   Kene's own inbox, not a third party's public surface — still worth
   keeping to a reasonable interval (hourly, not real-time-streaming)
   rather than treating "it's my own inbox" as license for an
   unbounded poll loop.
2. **On `opened_at` populating** — immediately surface to Kene (this is
   time-boxed, unlike every other cued handoff in this pipeline, so it
   gets the one exception to "no urgency-based shortcuts": a Telegram
   ping the moment a window opens, not batched into the next digest).
   Draft-and-cue proceeds exactly like any Tier 3 message otherwise —
   the window changes *whether sending is even possible*, not whether
   it still needs Kene's approval.
3. **`window_closed_unused` flips true** if nothing gets sent before
   `expires_at` — logged, not silently dropped, so a pattern of missed
   windows is visible to `11-analytics-and-learning` rather than just
   disappearing.

## The actual lever, since initiation can't be forced

The only thing that reliably produces an `opened_at` event on a cold
target is the target choosing to message first — which almost always
follows from *them* seeing something of Kene's (a comment, a Story
reply, a public post) and reaching out unprompted. This loops back
directly to the deferred posting/personal-branding feature (Origami
item 6, left intentionally stubbed per Kene's own call) — worth
flagging the connection now rather than rediscovering it later: IG/FB
cold outreach's only real lever and the deferred content-creation
feature are the same lever. When that feature gets built, its highest-
value use case for Instagram/Facebook specifically isn't inbound-in-
general, it's *this* — content genuinely built to make the 24-hour
window openable at all.

## New cron job

Folds into the same weekly slot as `linkedin-connection-flow.md`'s and
`x-follow-pursuit.md`'s maintenance jobs for the *expiry-check* half
(flagging `window_closed_unused`); the *detection* half (`opened_at`
firing) is event-driven off Kene's own inbox, not cron-scheduled, per
the workflow above — a genuinely different cadence for a genuinely
different reason (detection is time-sensitive, cleanup isn't), not an
oversight that these live on different schedules.

```
hermes cron create "0 8 * * 3" \
  "Run job-hunting-social-discovery-outreach's IG/FB window cleanup: for every social_outreach row with ig_fb_window.opened_at set and expires_at passed with messages_sent_in_window=0, set window_closed_unused=true and include in the digest. Does not touch opened_at detection — that stays event-driven off Kene's own inbox per ig-fb-engagement-window.md, not this job. Use [SILENT] if nothing to flag." \
  --skill job-hunting-social-discovery-outreach
```
