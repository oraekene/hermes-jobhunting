# Site Access Model — who's actually logged in when this pipeline reads a site

Answers a direct question honestly: **no, this was never explicitly
specified.** Phrases like "browser-read fallback" and "LinkedIn people
search" appear across `platform-capability-matrix.md`,
`10-approval-and-submit`, `12-company-research`, and
`22-contact-enrichment`'s Part A without ever pinning down *whose
session* those reads actually happen under. That's a real gap, not a
detail that didn't matter — for a site like LinkedIn specifically, most
of what's useful is only visible when logged in at all, so the earlier
design was quietly assuming *something* worked without saying what.

## Four access models, and which sites/actions actually get which

### 1. No login — genuinely public pages

Company sites, most of Reddit, GitHub, press releases, most of a
LinkedIn profile's headline-level info. No session of any kind needed;
already how `12-company-research` and Tier 0 of `22-contact-enrichment`
mostly operate. Cleanest model — no risk, no credential of any kind.

### 2. OAuth-app — a sanctioned, ToS-compliant delegation, not a login

X's DM API, Reddit's API: Kene explicitly authorizes a registered app
(via OAuth) to act within specific, platform-defined bounds. **This is
not "Hermes logging into Kene's account"** — it's the mechanism these
platforms built specifically so third-party tools don't have to. Already
the model `14-social-discovery-outreach`'s Tier 1 send capability
assumes for X; worth being explicit that this is architecturally
distinct from everything below, not just administratively different.

### 3. Kene's own already-authenticated session, driven via `computer-use`

**This is the actual answer to "would it be easier from a logged-in
account," and the specific mechanism that gets the benefit without the
downside.** For sites that don't offer (2) but are genuinely limited
without being logged in — LinkedIn's search and full-profile views
chief among them — the right model isn't Hermes independently
establishing or storing Kene's credentials. It's Hermes driving *Kene's
own, already-logged-in browser*, on his own machine, via the
Hermes-native bundled `computer-use` skill (confirmed in the official
skills catalog crawl: "drive the user's desktop in the background —
clicking, typing, scrolling, dragging — without stealing the cursor,
keyboard focus, or switching virtual desktops / Spaces," cross-platform).

Why this is the right answer rather than just "yes, use his login":

- **No new credential-security surface.** Nothing about Kene's LinkedIn
  password or session cookie needs to be stored, transmitted, or
  managed by this pipeline at all — the session already exists in his
  own browser, under his own OS-level authentication.
- **It genuinely is him, at his direction** — a person driving their
  own logged-in LinkedIn session is completely unremarkable, which is a
  different thing from an unattended script hitting the same session
  on a schedule.
- **Still bound by the same automation-pattern caution `platform-
  capability-matrix.md` already established** — this doesn't license
  unattended, scheduled, high-frequency use just because the mechanism
  changed. `computer-use`-driven LinkedIn reads stay occasional and
  light-touch, same posture the matrix already specifies, run when
  Kene's actually at his machine rather than as a background cron job
  hitting his session while he's away.

**This model is described above for reads.** It also now covers one
narrow, explicitly bounded *send* case — see model 4's update below for
why that's a deliberate carve-out, not a quiet expansion of what
"reads are fine" was ever meant to cover.

### 4. Avoid — no safe option exists, with one narrow, named exception

The default here remains: automated messaging/connection-request
behavior on LinkedIn (already Rule 6), and the browser-extension mode
of third-party finder tools (already `22-contact-enrichment/references/linkedin-methods.md`)
stay off-limits regardless of which access model would technically make
them easier. That default did not change.

**One narrow, explicitly authorized departure from it**: LinkedIn
connection-request sends and InMail sends, specifically, may run via
model 3 (`computer-use` on Kene's own session) under
`send_method: computer_use_approved` — see `platform-capability-
matrix.md`'s updated LinkedIn rows and `14-social-discovery-outreach/references/linkedin-connection-flow.md`. This is Kene's own explicit, direct decision to accept a
documented residual risk (behavioral-pattern detection applies
regardless of session ownership — see that file's full reasoning), not
a reinterpretation of the underlying policy risk as smaller than
described above. Three things keep this a narrow exception rather than
a general reopening of "Avoid" for LinkedIn sends:

- **Every send is individually approved by Kene first** — nothing here
  runs unattended or on a schedule, same constraint model 3 already
  applies to reads, just extended to this one send action.
- **Only these two actions** (connection-request notes, InMail) are
  covered. Ordinary DMs to strangers remain fully in "Avoid" with no
  execution path — see the matrix's stranger-DM row, unchanged.
- **Paced, not batched-and-fired** — human-like variable delay between
  approved sends, staying under the matrix's documented per-platform
  volume notes, not "approve fifty and let them all fire back to back."

## What this changes, concretely

`platform-capability-matrix.md` gets one more column (`access_model`)
alongside its existing tier ratings — a platform's send-tier and its
read-access-model are independent facts, and conflating them was part
of what left this underspecified before. `10-approval-and-submit`'s
form-fill step — which already has to interact with an actual logged-in
application portal to submit anything — was implicitly already using
something like model 3; this document just makes that explicit rather
than leaving it assumed. `22-contact-enrichment`'s Part A LinkedIn step
and `12-company-research`'s occasional LinkedIn reads both now cite this
file directly rather than each independently hand-waving "a browser
read." The one send exception (connection-request/InMail, model 3,
per-message approved) is the first time this file's access models have
governed a *send* rather than a read — worth flagging as a real
category shift for this document, not an incremental addition.
