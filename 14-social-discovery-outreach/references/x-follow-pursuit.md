# X Follow-Back Pursuit — tracking and working the constraint the matrix only named

## The constraint, precisely (updated from a re-check, not just restated)

`platform-capability-matrix.md`'s original DM row noted X can "only DM
users who follow Kene or have DMs open to everyone." A closer re-check
adds a real nuance that changes who can act on the second half of that:
X's own current DM-request settings run three ways — **Everyone**
(anyone can send a message request, even non-followers), **Verified
users and people you follow** (the default a lot of accounts sit on —
requests from unverified non-followers get silently dropped, no
notification to the sender), and **No one**. Separately, reaching a
non-follower who *does* have their setting on Everyone increasingly
depends on **Kene's own account tier** too — several current sources
describe non-follower outreach as gated behind X Premium/Pro on the
sender's side now, not just the recipient's setting being open. This
last point is under active platform change and worth a direct re-check
against X's own current help pages before relying on it — flagged here
rather than asserted as settled, same honesty standard the rest of this
matrix uses.

## What this means for pursuit, concretely

There is no path that lets Hermes *cause* a stranger to follow Kene —
nothing here claims otherwise. What's actually available is **checking
whether the constraint already doesn't apply**, and **using X's one
genuinely strong native capability (Tier 1 posting/replying) to make
organic follow-back more likely**, then tracking both instead of
re-discovering the same blocked state on every attempt.

## Tracking — extends `cold-dm-email-schema.md`

```yaml
x_follow_state:
  checked_at: null
  target_follows_kene: null       # bool | null (not yet checked) — X
                                    # v2 API read, Tier 1 per the matrix,
                                    # genuinely low-risk
  target_dm_setting: ""            # everyone | followers_and_verified |
                                    # unknown — inferred from whether a
                                    # test-relevant API field is exposed;
                                    # not always determinable without an
                                    # actual send attempt, "unknown" is
                                    # the honest default
  kene_tier_gate_applies: null      # bool | null — whether reaching a
                                    # non-follower currently requires
                                    # Kene's own paid tier; re-verify
                                    # per the note above rather than
                                    # assuming last check still holds
  engagement_attempts: []           # list of {type: reply|like|quote,
                                    # url, posted_at} — genuine public
                                    # engagement with the target's posts,
                                    # Tier 1 native capability, logged
                                    # here so the same target isn't
                                    # engaged with repeatedly on autopilot
  follow_back_achieved_at: null     # set when a later checked_at pass
                                    # finds target_follows_kene flipped
                                    # true — the actual signal that
                                    # unlocks a direct DM draft
```

## The pursuit workflow

1. **Check first, always** — a Tier 1 read (`target_follows_kene`,
   attempt to infer `target_dm_setting`) before assuming a DM needs any
   workaround at all; plenty of targets already have Everyone enabled
   and the DM just sends.
2. **If blocked and a genuine engagement angle exists** — reply to (not
   just like) a real post of theirs, using the same content-formula
   register rules as a cold DM's hook (specific, checkable, not
   "great post!"). This is Tier 1 native capability already, not a new
   automation surface. Logged to `engagement_attempts`, capped at a
   small number per target (2-3) — repeated public replies to the same
   stranger reads as pursuit, not engagement, well before it'd read
   that way to X's own spam detection.
3. **Re-check on a cadence, not continuously** — a target who doesn't
   follow back after one genuine engagement attempt isn't re-checked
   daily; folds into the same weekly connection-flow-maintenance-style
   pass as `linkedin-connection-flow.md`'s cron job, just checking
   `target_follows_kene` instead of LinkedIn acceptance.
4. **If never unblocked** — stays a draft-only Tier 3 cued target
   indefinitely (email, if `22-contact-enrichment` can find one, is
   very often the better fallback than continuing to pursue an X
   follow-back with no organic signal it's working).

## New cron job

```
hermes cron create "0 8 * * 3" \
  "Run job-hunting-social-discovery-outreach's X follow-state check: for every social_outreach row with contact.platform=x and x_follow_state.target_follows_kene != true, re-check via the v2 API read. Flip follow_back_achieved_at and surface in the digest for any target newly following Kene — these become eligible for a direct DM draft. Do not initiate new engagement_attempts from this job; engagement is drafted and cued through the normal Part B/C flow, this job only reads and updates state. Use [SILENT] if nothing changed." \
  --skill job-hunting-social-discovery-outreach
```

Shares its weekly slot with the LinkedIn connection-flow maintenance
job and the IG/FB window check below — three small, read-mostly state
checks, reasonable to run back-to-back rather than each claiming its
own cron entry and digest message.

## Where this plugs in

- `platform-capability-matrix.md` — X's DM row gets a note pointing
  here instead of stating the constraint as a dead end.
- `14-social-discovery-outreach/SKILL.md` Part C — the engagement-
  attempt replies route through Part C's existing public-reply
  drafting/approval flow, not a new mechanism.
