# Cold DM / Email / Reply Record — official schema

**Status: confirmed, and now extended.** Kene reviewed the original
shape and it stands as the official schema going forward — extend it
(new fields, new enum values) rather than replace it, which is what
everything below does. The content-generation formula that was the one
piece still coming separately now exists —
`cold-dm-content-formula.md` — and slots into the generation
step exactly as originally planned.

That resolved one gap; a completeness pass turned up others worth
naming explicitly rather than leaving implied:

1. **Content formula** — resolved, see above.
2. **Connection-prerequisite workflow** — `contact.relationship` was a
   static snapshot with no state machine behind it. Resolved by the new
   `connection` block below and `linkedin-connection-flow.md`.
3. **Send-path diversity within one platform** — LinkedIn alone now has
   three real send paths (connection-gated DM, InMail, Open Profile),
   not one. Resolved by `routing.send_method`'s expanded values and
   `inmail-credits.md`.
4. **Platform-gate tracking on X and IG/FB** — the matrix named these
   constraints without tracking state against them. Resolved by the new
   `x_follow_state` and `ig_fb_window` blocks below.
5. **Length calibration** — `platform_char_limit` existed as a field
   with nothing populating it from real numbers. Resolved by
   `cold-dm-content-formula.md`'s length table.

One schema for both DMs and emails, distinguished by `message.channel`,
because they share almost every field — a cold email is structurally a
cold DM with a subject line and looser length limits.

```yaml
# social_outreach record shape — illustrative only. Actually persisted
# as the social_outreach SQL table (shared/applications_db_schema_
# addendum.sql, extended in _addendum_2.sql) — there is no separate
# shared/social_outreach.schema.yaml file; this YAML block is here to
# show the shape readably, not to name a real file to create.
# Mirrors the applications table's discipline: every attempt logged
# (Rule 4), nothing sent without approval (Rule 1), no claim without
# evidence (Rule 2, via fidelity_check below).

id: null                        # autoincrement, mirrors applications.id

# --- Where this came from ---
trigger:
  type: ""                      # social_listening_post | manual_request |
                                 # application_followup | referral_ask |
                                 # interview_thank_you (see 13-interview-prep)
  source_platform: ""           # x | reddit | linkedin | instagram | tiktok |
                                 # email | null (manual_request may have none)
  source_url: ""                # the actual post/thread, if applicable
  source_cta_type: ""           # apply_link | dm_instructions |
                                 # email_instructions | unclear | n/a
  source_cta_context: ""        # what the post itself asked for/of whom —
                                 # the ground truth this specific draft is
                                 # shaped around, not a generic template

# --- Who it's going to ---
contact:
  platform: ""                  # x | reddit | linkedin | instagram | tiktok | email
  handle_or_address: ""
  display_name: ""
  profile_url: ""
  role_guess: ""                 # free text, e.g. "VP Engineering",
                                  # "Technical Recruiter" — kept as-is
  contact_priority: ""           # hiring_manager | decision_maker |
                                  # recruiter_track | unclassified —
                                  # set by 22-contact-enrichment's Part A
                                  # classification; hiring_manager and
                                  # decision_maker are the primary
                                  # target throughout 14/17, recruiter_track
                                  # is legitimate but never primary by default
  identification_confidence: ""  # confident | best_guess — never
                                  # asserted as certain; see
                                  # 22-contact-enrichment's Part A
  company: ""
  relationship: ""              # stranger | inbound_invited | 1st_degree |
                                 # warm_intro

# --- Classification, from platform-capability-matrix.md ---
routing:
  send_tier: null                # 1 | 2 | 3
  send_method: ""                # api_direct_pending_approval |
                                  # manual_cued | computer_use_approved
                                  # — the last one added for the
                                  # approved-then-executed LinkedIn
                                  # connection-request/InMail send path,
                                  # see linkedin-connection-flow.md and
                                  # inmail-credits.md; still always
                                  # "approved, then executed," never
                                  # unattended
  inmail_used: false              # true if this send used an InMail
                                  # credit instead of a connection-gated
                                  # DM — see inmail-credits.md
  matrix_checked_at: null        # so a stale tier read is auditable, same
                                  # spirit as posted_at_raw in applications

# --- LinkedIn connect-first gate — only populated when
# --- contact.platform: linkedin and contact.relationship: stranger,
# --- and connection.required: true (InMail/Open Profile sends leave
# --- this block at its inert default). See
# --- linkedin-connection-flow.md for the full state machine.
connection:
  required: false
  status: "not_connected"        # not_connected | note_drafted |
                                  # note_awaiting_approval |
                                  # request_sent_pending_acceptance |
                                  # accepted | declined | expired |
                                  # withdrawn
  note_draft: ""                  # <=300 chars
  note_char_count: null
  approval_sent_at: null
  approval_decided_at: null
  send_method: ""                  # computer_use_approved | manual_cued
  sent_at: null
  check_method: ""                  # kene_confirmed | computer_use_check
  last_checked_at: null
  accepted_at: null
  expires_at: null
  free_tier_note_quota_used: null

# --- InMail credit accounting — only populated when
# --- routing.inmail_used: true. See inmail-credits.md.
inmail:
  sent_at: null
  reply_deadline: null             # sent_at + 90d
  credit_refunded: false
  open_profile_send: false          # true if this used the free
                                     # Open-Profile path instead of a
                                     # metered credit

# --- X follow-back state — only populated when contact.platform: x.
# --- See x-follow-pursuit.md.
x_follow_state:
  checked_at: null
  target_follows_kene: null
  target_dm_setting: ""              # everyone | followers_and_verified
                                      # | unknown
  kene_tier_gate_applies: null
  engagement_attempts: []
  follow_back_achieved_at: null

# --- Instagram/Facebook 24-hour window state — only populated when
# --- contact.platform: instagram or facebook. See
# --- ig-fb-engagement-window.md.
ig_fb_window:
  opened_at: null
  expires_at: null
  message_tag_used: ""
  messages_sent_in_window: 0
  window_closed_unused: false

# --- The message itself ---
message:
  channel: ""                    # dm | email | reply | quote | post
                                  # — quote and post are schema stubs
                                  # only, reserved for a future personal-
                                  # branding feature; 14-social-discovery-
                                  # outreach implements dm/email/reply
                                  # today, not quote/post
  subject: ""                    # email only
  body_draft: ""
  personalization_hooks: []      # e.g. ["their post about X", "mutual
                                  # connection Y", "shared STAR story Z"] —
                                  # what makes this not a template
  char_count: null
  platform_char_limit: null      # null if not applicable (email)
  linked_application_id: null    # FK to applications.id, if this outreach
                                  # is tied to a specific staged/sent app

# --- Rule 2, applied to outreach the same as any resume claim ---
fidelity_check:
  risk_gate_pass_count: 0
  risk_gate_fail_count: 0
  fidelity_mode_at_draft: ""     # copied from target-profile.yaml at draft
                                  # time, same audit-trail reasoning
                                  # applications.exact_phrase_count etc. use

# --- Approval & delivery (Rule 1) ---
approval:
  status: "drafted"              # drafted | awaiting_approval | approved |
                                  # api_sent | cued_delivered_by_user |
                                  # skipped
                                  # GATE: if connection.required: true,
                                  # status may not advance past "drafted"
                                  # until connection.status: "accepted" —
                                  # see linkedin-connection-flow.md. The
                                  # DM can be drafted immediately
                                  # (draft-ahead), it just can't move
                                  # toward being sent until the
                                  # connection exists.
  approval_sent_at: null
  approval_decision: ""          # approve | edit | skip
  approval_decided_at: null
  sent_at: null
  sent_via: ""                   # api | manual — mirrors send_method once
                                  # it's actually resolved, not just planned

# --- Outcome (Rule 4) ---
outcome:
  replied_at: null
  reply_type: ""                 # no_reply | auto_reply | human_reply |
                                  # led_to_application | led_to_referral
  led_to_application_id: null
  outcome_updated_at: null
```

## Design notes on the schema's own field choices

These predate the content formula and stay true now that it exists —
they're about why the *data shape* looks the way it does, not about
content rules, which is exactly why they read as reasonable now instead
of being superseded by `cold-dm-content-formula.md`:

- `personalization_hooks` is deliberately a list, not a free-text
  paragraph — `11-analytics-and-learning` can eventually correlate hook
  *type* against reply rate the same way it already correlates tactic
  flags on `applications` against outcomes, once there's enough volume
  logged. Worth keeping the vocabulary for hook types small and
  consistent from the start (a short enum, not open text) if that
  analysis is ever wanted. The content formula's hook section (see
  "Hook" in `cold-dm-content-formula.md`) is what actually populates
  this field now — the field's shape was speculative when written, the
  formula is what makes it real.
- `source_cta_context` intentionally stores what the *post* asked for,
  not a paraphrase of Hermes's interpretation of it — keeps the record
  honest about whether the outreach actually matched what was requested.
- This table lives alongside `applications` in the same SQLite file — see
  `shared/applications_db_schema_addendum.sql`, extended for everything
  in this pass by `shared/applications_db_schema_addendum_6.sql`.
