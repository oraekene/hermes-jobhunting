# Pitch Catalog — reasoning, alternatives considered, practical limits

Companion to `shared/pitch-catalog.yaml.template`, same split
`dynamic-target-calibration.md` uses relative to its own `.yaml` —
the config states the shape, this states the why. Read this before
seeding the catalog for the first time.

## `target_customer_profile` got deeper, not replaced

Kene's direct feedback on the original design: the per-entry filter
field was exactly the right idea, it just needed to go further than a
one-line description. `target_customer_profile` is now a structured
persona block (`who`, `company_context`, `stated_pains`,
`buying_trigger`, `likely_objection`, `where_they_are`,
`language_they_use`) instead of a single string — see `17-cold-prospecting/references/ideal-client-persona.md` for the schema and the
propose-then-confirm build process, and `17-cold-prospecting/references/segment-research.md`
for where the sourced fields (`stated_pains`, `language_they_use`)
actually get their content from, with its own corroboration threshold
so this doesn't become a place where invented specificity sneaks past
the pipeline's evidence discipline. One persona per catalog entry, not
one for Kene overall — the whole point of the catalog already being a
list is that Kene has more than one sellable unit, and they have
different buyers.

## The three approaches actually on the table, and why the middle one wins

**Fully user-authored** (Kene writes each pitch, or a fixed set of
templates, by hand). Rejected as the primary mode — not because it's
unsafe, but because it throws away the entire point of routing this
through Hermes: no personalization leverage, doesn't scale past a
handful of targets, and every future target requires the same manual
effort as the first one.

**Fully auto-generated per target, straight from the memory bank, no
durable intermediate.** Rejected — covered in `17-cold-prospecting/
SKILL.md`'s catalog section, but worth restating the core issue plainly:
this pipeline's entire fidelity discipline (`09-risk-tactics-gate`, the
whole `fidelity_mode` system) works by checking a claim *against
something external* — a JD, a STAR story, a confirmed fact. Free
generation with no catalog removes the external thing to check against.
The system would still *look* gated (it'd still call something a
"fidelity check") while actually just checking generated text against
other generated text — a false sense of safety, arguably worse than no
gate at all because it looks like one.

**Catalog-first, generate-by-recomposition per target.** The
recommendation, and what's built. Splits the work into a slow,
Rule-5-confirmed layer (the catalog — built rarely, reused constantly)
and a fast, automatic layer (the per-target draft — generated freely,
but only ever recombining confirmed material). Same two-speed pattern
`title_variants` already uses in `target-profile.yaml`: propose-and-
confirm slowly, apply constantly.

## `role_creation` needs a lower default volume than `role_fit`

Not a hard rule, a strong recommendation: **role_creation and wildcard
pitches should be a deliberately small minority of total weekly
outreach volume**, distinct from `tier-config.yaml`'s general caps.
The reasoning is about the target's experience, not Kene's risk: a
`role_fit` pitch ("I could do X for you") is a familiar, low-friction
ask even unsolicited — recipients know how to process it instantly. A
`role_creation` pitch is asking someone to first accept a diagnosis of
their own business before considering the offer — a genuinely bigger
ask, more likely to land as presumptuous if the hit rate on "actually
correct, actually useful gap" isn't high. Keeping the volume low keeps
the average quality of each one high, which is the only thing that
makes the higher-risk mode worth using at all.

## Pitch performance — the self-improvement loop, made concrete

Kene's ask was that pitches be *fully* included in constant testing, not
just theoretically eligible for it — worth spelling out the actual
mechanism rather than leaving it as a one-line mention.

**What gets tracked**: every `social_outreach` row created by
`17-cold-prospecting` already carries `catalog_entry_ids`, `pitch_mode`,
`target_type`, and the eventual `outcome.reply_type` (see
`shared/applications_db_schema_addendum_2.sql`) — nothing new to add to
log this, the columns already exist for exactly this purpose.

**What the analysis actually correlates**, on a regular cadence (weekly
is reasonable — tie it to the existing analytics rhythm
`11-analytics-and-learning` already runs on, rather than inventing a
separate schedule):

- Reply rate **per catalog entry** — which sellable units are landing,
  which aren't.
- Reply rate **per `pitch_mode`** — is `role_fit` outperforming
  `role_creation` overall, or is it target-dependent?
- Reply rate **per `target_customer_profile` match** — is a given
  catalog entry doing better against the target profile it was written
  for than when it gets used outside that profile?
- Cross-cut by platform, since a pitch that lands well on X may not on
  Reddit even with identical content.

**What it's allowed to propose** (via `skill_self_edits`, same staged-
for-approval pattern as everything else that self-tunes here — never
silently applied): retire a consistently-flat entry, promote a
high-performing entry into more targets' consideration set, suggest a
`target_customer_profile` correction when an entry does well *outside*
its stated profile (a sign the profile description was too narrow, not
that the pitch got lucky), or flag when a whole `pitch_mode` is
underperforming broadly enough that `shared/pitch-catalog.md`'s own
volume guidance (keep `role_creation`/`wildcard` a deliberate minority)
should shift further in one direction.

**What it does not do**: rewrite `message.body_draft`'s actual wording
based on performance — that would mean the analysis loop silently
editing the content-generation formula itself, a different, larger
claim than "this catalog entry works" or "this mode underperforms."
Once the real cold-DM/email content formula exists (see the schema
file's own note on this), *that* formula file becomes eligible for the
same `skill_self_edits` treatment on its own — kept separate from
catalog-level performance tracking so a wording problem and a
positioning problem never get conflated into the same fix.

The most tempting version of "use it to its limits" is pushing harder on
automated sending — trying browser automation, unofficial tooling, or
just accepting higher ban risk to get LinkedIn/Instagram/TikTok sending
working anyway. Recommend against this directly, not on caution-for-
its-own-sake grounds but a practical one: the account that gets
restricted is Kene's actual professional identity, and a job search or
a client-facing consulting pitch is exactly the wrong context to be
rebuilding a banned LinkedIn profile in the middle of. The research/
iteration leverage described in `17-cold-prospecting/SKILL.md`'s "Using
Hermes to its actual limits" section is where the real, unclaimed
capacity is — that's the honest answer to "what hasn't been exploited
yet," not the send step.

## Seeding the catalog — two entry paths, not one

Recommend `07-context-architect` walks Kene through this once, deliberately
separate from a normal memory-refresh session — proposing `held`
entries first (should be a short, easy pass — this is just "what do you
already do, framed as sellable units instead of resume bullets"), then
`adjacent` (a genuinely creative pass, closer to how Phase 1.5 proposes
title variants), and only then asking directly whether any `wildcard`
entries are wanted at all — this shouldn't be assumed as a default just
because the schema supports it.

**Kene can also add catalog entries directly himself, any time**, not
only through this Hermes-proposed flow — a manually-added entry still
lands in the same `pitch-catalog.yaml` shape and still goes through
`07-context-architect`'s normal confirm step (same reasoning Rule 5
applies everywhere else: even something Kene wrote himself gets the
same audit trail as anything else in the catalog, if only so
`confirmed_at` means the same thing for every entry regardless of who
drafted it). The two paths aren't in tension — Hermes proposing from the
memory bank is the leverage play for entries Kene might not think to
frame as sellable on his own; manual entry is the fast path for
anything he already knows he wants to offer and doesn't need drafted
for him.
