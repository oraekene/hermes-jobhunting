---
name: job-hunting-linkedin-profile-optimizer
description: "Audit and optimize Kene's LinkedIn profile"
metadata:
  hermes:
    tags: [job-hunting, linkedin, outward-facing]
    category: job-hunting
    related_skills:
      - job-hunting-context-architect
      - job-hunting-cold-prospecting
      - job-hunting-social-discovery-outreach
      - job-hunting-portfolio-onepager
      - job-hunting-output-templates
---

# LinkedIn Profile Optimizer

## When this skill applies

Use this skill when Kene wants his LinkedIn profile audited or optimized
— full-profile review against the actual memory bank (STAR bank,
domain-knowledge, shared/pitch-catalog.yaml's confirmed personas,
target-profile.yaml) to check whether the profile itself converts a
visitor in the first few seconds, the way a landing page would. Produces
a structured audit (headline, About, Featured, Experience descriptions,
keyword coverage) plus specific rewrite drafts — never edits the live
profile without Kene's explicit approval per change. A genuinely new
feature, not an extension of 14-social-discovery-outreach or
17-cold-prospecting — those skills draft messages *to* other people;
this skill drafts Kene's own profile, a different artifact with a
different owner and a different execution model.

## Why this is its own skill, not folded into 14 or 17

Everything else in the social-outreach/prospecting family produces
content aimed *at* someone else, gated by the platform-capability
matrix's send-tier logic because sending to a stranger is the risky
part. Editing Kene's own profile isn't a "send" in that sense at all —
there's no recipient, no ToS automation risk in the same category
(LinkedIn's §8.2 restriction is about automating messaging/connection-
requests/scraping *directed at other members*, not about a member
managing their own profile fields). Folding this into `14`/`17` would
have inherited a send-tier framework built for a different risk profile
than the one this actually has.

## What "profile as landing page" actually means, made concrete

The Origami-style framing — "if someone clicks your name and can't tell
what you do in 3 seconds, you're burning the impression" — is a real
and useful lens, just needed an actual audit process behind it instead
of staying a slogan. Four things get checked, in order of how fast a
visitor actually encounters them:

1. **Photo + headline (the first ~2 seconds)** — Hermes can't audit a
   photo's quality, but it can flag if the headline is doing the
   headline's actual job: LinkedIn's default (auto-filled from current
   title/employer) is the single most common failure mode, and it says
   *what Kene's employer calls him*, not what he can do for a visitor.
   Checked against `shared/pitch-catalog.yaml`'s confirmed `held`
   entries — does the headline let a stranger self-identify as the
   `persona.who` for at least the primary offering within one read?
2. **About section (the next ~10 seconds, if the headline earned it)**
   — checked for: does the first line work if nothing after it gets
   read (most visitors don't scroll the full section); does it name
   who Kene helps and how, not just list credentials; does it use
   `persona.language_they_use` from any confirmed persona rather than
   generic industry-speak; is there a clear, single next step at the
   end (not a hard pitch — an easy one, matching `cold-dm-content-
   formula.md`'s ask-phrasing register even though this isn't outreach).
3. **Featured section** — flags if empty or stale (a landing page with
   no proof points). Suggests candidates from `star-story-bank.md`/
   confirmed catalog entries' `evidence` fields — things Kene has
   already validated as true and worth surfacing, not new claims
   invented for the profile.
4. **Experience descriptions + keyword coverage** — checked against
   `07-context-architect/references/title-taxonomy.md`'s confirmed
   title variants and `target-profile.yaml`, since this is also what
   recruiter search actually indexes on — an under-optimized profile
   doesn't just fail the 3-second test, it fails to surface in search
   at all for titles Kene would actually want to be found under.

## Multiple personas, one profile — the actual tension, named directly

Kene's catalog has multiple confirmed offerings with different personas
(`17-cold-prospecting/references/ideal-client-persona.md`). A LinkedIn
profile is one artifact, and trying to speak to every persona equally
in it tends to speak clearly to none — the same "narrowing makes
everything else work" reasoning the personas themselves are built on.
Default recommendation, surfaced as a choice for Kene rather than
decided silently: **optimize the headline/About primary framing for
whichever catalog entry is `category: held` and currently getting the
most outreach volume/reply-rate traction** (per `11-analytics-and-
learning`, once there's data), with `adjacent` offerings represented in
Featured/Experience rather than competing for the headline's limited
attention. If Kene wants a different weighting, that's his call to
make explicitly, not an inference this skill draws on its own.

## Process

1. **Input**: Kene shares his current profile (screenshot, pasted text,
   or a `computer-use`-driven read of his own logged-in profile page —
   this is Kene's own profile, so the model-3 session-driven read from
   `shared/site-access-model.md` applies with none of that file's
   messaging-specific caution, since nothing here contacts another
   member).
2. **Audit pass**: runs the four-part check above, producing a scored
   report (pass/needs-work/missing per section) — not a rewrite yet,
   an honest assessment first, same "check before asserting" discipline
   the rest of this package uses.
3. **Draft pass**: for each needs-work/missing item, drafts a specific
   replacement — a rewritten headline (2-3 variants), a rewritten About
   opening line, specific Featured candidates pulled from evidence,
   keyword additions per section. Every claim in a draft still traces
   to something in the memory bank (STAR bank, confirmed catalog
   entries) — Rule 2's no-claim-without-evidence discipline applies to
   Kene's own profile exactly as it applies to a resume, since a
   profile is also a fact-bearing document about him, not campaign
   copy exempt from the fidelity check.
4. **Confirm, then execute** — Kene reviews and approves each section's
   draft individually (not a single blanket "approve the whole
   profile" — same per-item approval spirit as everything else this
   package gates). On approval, execution is either Kene pasting it in
   himself, or `computer-use` filling the specific approved field on
   his own logged-in profile-edit page — approved-then-executed, same
   shape as `10-approval-and-submit`'s form-fill, not auto-applied.

## Cadence

Manual-triggered by default — a profile audit isn't a per-target
recurring action the way outreach is. Worth re-running after any
catalog entry's persona gets substantially rebuilt (a new `held` entry,
or an existing one's `persona.who` changing meaningfully), and
optionally on a slow cadence (quarterly, tied to the same rhythm as the
platform-matrix re-verify) as a staleness check, not a weekly cron.

## What this doesn't do

- Doesn't touch photo/banner image selection or quality — outside what
  Hermes can meaningfully evaluate visually at the fidelity this
  package holds text claims to; flagged as a gap for Kene to judge
  himself, not silently skipped without mention.
- Doesn't auto-apply anything — every field-level change is its own
  approval, per the process above.
- Doesn't invent proof points — Featured/About claims trace to
  `star-story-bank.md`/confirmed catalog `evidence`, same as a resume
  bullet would.

## Where this plugs in

- `shared/pitch-catalog.yaml` — persona fields drive headline/About
  framing.
- `17-cold-prospecting/references/segment-research.md` — corroborated
  `language_they_use` patterns inform About-section phrasing the same
  way they inform outreach copy.
- `07-context-architect/references/title-taxonomy.md`,
  `shared/target-profile.yaml` — keyword-coverage check.
- `shared/site-access-model.md` model 3 — the read/write execution
  mechanism, own-profile case.
