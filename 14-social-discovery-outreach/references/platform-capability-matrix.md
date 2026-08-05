# Platform Capability Matrix — what Hermes can actually do, per platform

**Companion file, read together with this one**:
`shared/site-access-model.md` — this file rates *send* tiers (DM/reply/
post); that file answers the separate, previously-unspecified question
of *whose session* a read action actually happens under (no login /
OAuth-app / Kene's own session via `computer-use` / avoid). The two are
independent facts about a platform, not the same rating twice.

**Verified**: 25 July 2026. **Re-verify cadence**: quarterly, same rhythm
as `07-context-architect/references/title-taxonomy.md`'s quarterly
re-crawl — platform DM/automation policy moves faster than most of this
pipeline, so treat anything here older than a quarter as "check before
relying on it," not "still true." Log the re-verify date at the bottom
of this file each time it's redone.

## First, the honest baseline: what Hermes ships with, natively

Out of the box, Hermes Agent's only *native, bundled* social capability is
posting to X — nothing else, not even reading. Everything else in this
matrix requires one of:

- An **MCP connector** Kene installs and configures himself (from Nous's
  approved catalog, or a third party like Postiz/PostFast/Composio) — and
  it matters *which kind*: Postiz and PostFast are content-scheduling
  tools (draft/schedule/publish **posts**, across many platforms) — as of
  this check, neither exposes a 1:1 **DM-send** tool, only publishing.
  Composio's platform toolkits are broader API wrappers and *may* expose
  some messaging actions on some platforms (worth checking Composio's
  specific tool list per platform before assuming DM-send is included —
  coverage varies tool to tool, this wasn't independently confirmed for
  DMs specifically).
- **Direct API wiring** Kene sets up himself with his own developer
  credentials for that platform (the only path for X DM sending — see
  below).
- **Browser automation** (Hermes's own browser/form-fill tool, the same
  one `10-approval-and-submit` uses to fill application forms) — this is
  how *reading*/searching a platform's web UI is possible even where no
  API exists, but it is explicitly **not** used for automating sends on
  any platform whose ToS prohibits automated messaging (see per-platform
  notes) — using it that way would just be automation with extra steps,
  not a loophole around the policy.

## The matrix

| Platform | Action | Official API path | Tier | Why |
|---|---|---|---|---|
| **X / Twitter** | Send DM | v2 API DM endpoints exist; requires a paid developer tier (Basic and up) and Kene's own app credentials — nothing ships this for him | **1** | Genuinely an official, ToS-sanctioned send path, if Kene sets up API access. Can only DM users who follow Kene or have DMs open to everyone — and reaching a non-follower with open DMs increasingly also depends on Kene's own account tier (X Premium/Pro), per current sourcing — re-verify this specific point each pass, it's moving. See `x-follow-pursuit.md` for tracking and the one legitimate lever (public engagement) for closing this gap. |
| **X / Twitter** | Search / read tweets, replies | v2 API, generous read tiers | **1 (read)** | Straightforward, low-risk. Includes the `target_follows_kene` check `x-follow-pursuit.md` uses. |
| **X / Twitter** | Reply / quote / post | Native bundled Hermes skill | **1** | Ships out of the box already. |
| **LinkedIn** | Send DM to a non-connection (stranger) | No public self-serve send API. LinkedIn's User Agreement (§8.2) explicitly bans third-party tools that automate messaging, connection requests, or scraping — "cloud" tools included, not just browser extensions | **3** | This isn't a gray area at the policy level — real vendors (HeyReach, for one) have been cease-and-desisted mid-2026, and independent testing puts account-restriction rates around 23% within 90 days for automation users generally. The risk lands on Kene's actual professional profile. Draft-only by default. A stranger's DM becomes sendable only once `connection.status: accepted` (`linkedin-connection-flow.md`) or via InMail/Open Profile below — never as a direct send to an unconnected stranger. |
| **LinkedIn** | Send connection request, with personalized note | Same §8.2 restriction names connection-request automation explicitly, not just messaging — this is not a lesser-restricted action than the DM row | **3, with an approved bounded exception** | Officially, still no safe self-serve path — the underlying risk (behavioral pattern detection: send velocity, acceptance-rate drop-off, note-template similarity) applies regardless of whose session drives it. Kene has weighed that risk directly and authorized a bounded exception: `send_method: computer_use_approved` — note drafted automatically, Kene approves each one individually, `computer-use` executes on his own logged-in session at human-like pacing, never unattended/scheduled. This closes the IP/device-fingerprint gap third-party cloud tools get flagged on but does **not** close the behavioral-pattern gap — treated as accepted residual risk, not zero risk. Full design in `linkedin-connection-flow.md`. |
| **LinkedIn** | Send InMail (Premium/Sales Navigator credit) | No self-serve send API for individual or Sales Navigator-tier accounts either (only enterprise Recruiter partner integrations get any API access, under contract) — still a manual UI action even though it bypasses the connection prerequisite | **3** | Same execution model as the connection-request exception above (`computer_use_approved` or `manual_cued`, always approved-then-executed). What InMail actually buys is skipping the connect-and-wait step entirely, at the cost of a metered, plan-gated credit — not a lower automation-risk send. One-shot per recipient (no follow-up InMail without a prior reply). Full mechanics, credit tiers, and budget tracking in `inmail-credits.md`. |
| **LinkedIn** | Comment on a public post, under Kene's own identity | `w_member_social` — "permission to post, comment, and like on behalf of a member" — is genuinely part of LinkedIn's **self-service Open Permissions** tier, no partner approval needed. A materially different access tier from messaging, which sits behind Restricted Permissions/partner approval | **1** | Worth being precise about *why* this differs from the DM row: it isn't that commenting is "less against the rules" than DMing — it's that LinkedIn built and ships a self-serve API specifically for this action, the same way it does for posting, while messaging was never offered at that access level to begin with. Ordinary spam/pattern detection still applies at high volume, same as any platform — this isn't a license to comment at bulk. |
| **LinkedIn** | Read/search postings, browse profiles | No bulk-safe path | **3 (for anything at bot-like frequency/volume)** | Occasional manual-triggered reads are fine; scheduled, repeated scraping carries the same detection risk as messaging automation. Treat `social_listening` polling of LinkedIn as low-frequency and light-touch, not a tight poll loop. |
| **Instagram / Facebook (Meta)** | Send DM, cold (recipient hasn't messaged first) | Meta Graph API messaging only works inside a 24-hour window **opened by the recipient**, or via a small set of approved message tags for narrow non-promotional cases — there is genuinely no compliant API path for outbound cold DMs in 2026 | **3** | Confirmed from multiple current sources: any tool offering "DM people who haven't engaged with you" is either scraping (ban risk) or misrepresenting what it does. Not a Hermes limitation specifically — nobody has this path. |
| **Instagram / Facebook** | Comment on someone else's public post | Graph API's comment endpoints are built around managing/moderating comments **on your own content** (replying to comments people leave on you), not posting fresh comments on a stranger's post — this wasn't independently confirmed as a genuine self-serve action the way LinkedIn's `w_member_social` is | **3 (unconfirmed access — treat as unavailable until verified otherwise)** | Less clear-cut than LinkedIn's case; worth a dedicated re-check before ever assuming this row moves to Tier 1. |
| **Instagram / Facebook** | Reply within an open conversation | Graph API, `instagram_business_manage_messages` scope | **1 (but not this use case)** | Only matters if a contact messages Kene first; irrelevant to cold outreach. |
| **Facebook (Messenger/Pages)** | Send DM, cold | Same Send API/24-hour-window architecture as Instagram — a recipient must have messaged the Page in the last 24h, or fall under one of a shrinking set of non-promotional Message Tags (several legacy tags retired April 2026). One direct source put it plainly: "compliant cold outreach is not possible." | **3** | Structurally identical reasoning to Instagram/Facebook above, worth its own row since Kene asked for it explicitly — this is the Page/Messenger side specifically, not the personal-profile side (personal-profile automation is even less sanctioned than Page messaging, not more). |
| **Threads** | Send DM, cold | No separate Threads DM API — Threads DMs route through the **Instagram Messaging API**, inheriting Instagram's exact same 24-hour-window rule | **3** | Not an independent gap — it's the Instagram restriction one layer removed. |
| **Threads** | Post / reply / quote | Real, functional Graph-based API (launched 2024, generally available) — publish, reply-chain, carousels, up to 250 posts/24h per profile | **1** | Genuinely solid for the same reason X's native posting is Tier 1 — this is publishing, not messaging, and Meta built it to be used. |
| **Threads** | Search / read | **No native search endpoint as of this check** — the API can read reply/conversation threads it already knows about but can't query the platform generally the way X's or Reddit's read APIs can | **3 (browser-read fallback only)** | Meta has signaled search is coming; re-verify next quarterly pass rather than assuming this stays true. |
| **TikTok** | Send DM | No public DM API at all, for anyone, as of mid-2026 | **3** | Not a policy restriction to route around — the capability doesn't exist externally yet. |
| **TikTok** | Search / read | Limited public API surface; browser-read is the practical fallback | **3 (draft/read-assist only)** | |
| **Reddit** | Send DM (`/api/compose`) | Official OAuth endpoint exists, PRAW wraps it cleanly | **2** | Technically a real send call — but Reddit's Responsible Builder Policy explicitly prohibits "spamming... through automated... direct messages" and requires "a user's explicit consent to engage in private communications." Separately and mechanically: fresh/low-karma accounts get instantly blocked from DMing strangers regardless of policy. Even a single, well-personalized, low-volume message in response to someone's own "DM me" post sits closer to the policy's intent than automation does — but automate the *sending call* and this stops being that. Draft-only, cued, one at a time. |
| **Reddit** | Read / search posts, comment on a public thread | Official API, generous limits | **1 (read)** / **2 (commenting under Kene's own account, since it's public and attributable — route through the same approval step as everything else, on principle, not because the API forbids it)** | |
| **X / Twitter** | Reply / DM / search | `social-media/xurl` — the bundled X CLI: post, reply, search, DM, media | **1** | Ships out of the box. Named explicitly here because "native bundled Hermes skill" left the reader to guess which one, and the guess a reader makes is a third-party scheduler like Postiz — which is a materially different access and trust decision. **`xurl` also covers quote and original posting, and this skill deliberately does not use it for those** — see the stub note in `14-social-discovery-outreach/SKILL.md`. Capability being available is not scope. |
| **LinkedIn** | Send DM/InMail to a non-connection | No public self-serve send API. LinkedIn's User Agreement (§8.2) explicitly bans third-party tools that automate messaging, connection requests, or scraping — "cloud" tools included, not just browser extensions | **3** | This isn't a gray area at the policy level — real vendors (HeyReach, for one) have been cease-and-desisted mid-2026, and independent testing puts account-restriction rates around 23% within 90 days for automation users generally. The risk lands on Kene's actual professional profile. Draft-only, always. |

## What this means concretely for Part A/B of the main skill

- The only platform where "Hermes sends the DM itself, no per-message
  approval" is realistic today is **X**, and only after Kene
  deliberately sets up paid API access — it is not a default capability
  of this skill or of Hermes. LinkedIn's connection-request and InMail
  paths now have an automated execution route too
  (`computer_use_approved`), but that route always stops at Kene's
  per-message approval first — mechanically automated, never
  unattended, a different thing from X's API path being able to fire
  without a human step per send.
- **Reddit** sits in the interesting middle: technically automatable,
  deliberately not automated by this skill, because the platform's own
  policy language draws the line at "automated," not at "assisted."
- **LinkedIn DM-to-a-stranger, Instagram/Facebook (cold), Threads
  (cold), and TikTok** are draft-only with no execution path at all
  short of Kene doing it by hand, for structural reasons that don't
  change with a better tool or a cleverer prompt — there's no send path
  to wire up, or the one that exists explicitly excludes this use case.
  LinkedIn is the one partial exception in this group: a stranger's DM
  becomes reachable via the connection-request or InMail routes above,
  which do have an approved execution path, just not a direct one.
  Notably, every Meta-owned surface (Instagram, Facebook, Threads)
  shares one underlying restriction, not four separate ones — fixing
  one doesn't fix the others because there's nothing broken to fix,
  it's a single deliberate policy Meta applies platform-wide.
- **Posting/replying publicly** (as opposed to DMing) is the one place
  Threads is actually strong — real API, generally available. Worth
  remembering for `17-cold-prospecting`: a well-placed public reply to
  someone's own post can sometimes do the job a cold DM can't reach,
  without touching the DM restriction at all.
- **A platform's reply/comment tier is not always its DM tier** — treat
  these as two separate lookups, never assume one from the other.
  LinkedIn is the clearest case: DM is Tier 3, but commenting is Tier 1,
  because LinkedIn ships a genuine self-serve API for the latter and
  never did for the former. Instagram/Facebook go the other way on
  uncertainty — DM's restriction is confirmed and explicit, but
  cold-commenting-on-a-stranger's-post wasn't independently confirmed
  either way, so it's held at Tier 3 until it is.

## Re-verify log

- 2026-07-25 — initial build (X, Reddit, LinkedIn, Instagram/Facebook,
  TikTok), sourced from current platform documentation and 2026
  automation-policy coverage.
- 2026-07-25 — added Threads and Facebook (Messenger/Pages) explicitly.
- 2026-07-25 — added reply/comment as its own action row, separate from
  DM, for LinkedIn and Instagram/Facebook. Next check: ~October 2026.
- 2026-07-29 — split LinkedIn's single DM/InMail row into three
  (stranger-DM, connection-request, InMail), added the approved
  `computer_use_approved` execution exception for connection requests,
  added InMail's plan-tier/credit mechanics, updated X's DM row with
  the account-tier nuance on messaging non-followers. See
  `linkedin-connection-flow.md`, `inmail-credits.md`, `x-follow-pursuit.md`.
