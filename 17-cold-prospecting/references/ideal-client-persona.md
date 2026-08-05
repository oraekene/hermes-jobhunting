# Ideal-Client Persona — one per catalog entry, built fine-grained

Direct answer to a direct request: yes, `target_customer_profile` was
always the right *slot* for "who is this for" — Kene confirmed as much.
What was missing was depth. A one-line filter string ("small-to-mid
teams that need one person to own an AI feature") is enough to pre-
filter prospecting targets, which is all it was built to do. It is not
enough to draft a pitch that reads like it was written for one specific
person rather than a category. This file is the process that builds the
detailed version — **one persona per catalog entry, not one persona for
Kene overall**, because Kene has multiple sellable units
(`shared/pitch-catalog.yaml`) and a Sales Navigator subscriber and a
solo Nigerian solar-hardware founder are not the same ideal client even
if both could plausibly buy "AI PM / generalist contractor" time.

## Why per-entry, not per-Kene

The Origami-prompt version of this (paste one LinkedIn URL, get one
ideal client) assumes a single offering. Kene's actual catalog already
has three-plus live entries across `held`/`adjacent`/`wildcard`
categories, each with a genuinely different buyer. Collapsing them into
one persona would either force a lowest-common-denominator description
useless for personalization, or silently privilege whichever offering
happened to be top of mind when the persona got written. Neither is
acceptable given this pipeline's evidence discipline elsewhere — a
persona is exactly the kind of thing that quietly goes stale and
misleads every pitch built on it if it isn't scoped tightly.

## The persona schema — extends `pitch-catalog.yaml`'s entry shape

`target_customer_profile` stops being a single free-text string and
becomes a structured block. Existing entries with only the free-text
version keep working (treated as `summary` with every other field
empty) — this is additive, not a breaking migration; `07-context-
architect` upgrades an entry to the full structure the next time it's
touched, not in a forced batch pass.

```yaml
target_customer_profile:
  summary: >                        # the original one-liner, kept —
                                     # still what gets shown in fast
                                     # contexts like the weekly
                                     # target-finding cron digest
  persona:
    who: ""                          # one concrete role/title/situation,
                                      # not a category — "solo Nigerian
                                      # solar-hardware importer running
                                      # their own WhatsApp storefront,"
                                      # not "small business owners"
    company_context: ""              # team size, stage, funding
                                      # posture, geography — whatever
                                      # actually narrows it; "n/a" for
                                      # individual/wildcard entries
    stated_pains: []                  # list of pain-point IDs from
                                      # shared/pain-point-patterns/
                                      # (see segment-research.md) — not
                                      # free text invented at persona-
                                      # build time; every entry here
                                      # must trace to a corroborated
                                      # pattern record, same evidence
                                      # discipline as `evidence:` above
    buying_trigger: ""                # what event/state makes this
                                      # person actually receptive right
                                      # now, if known — "just missed a
                                      # deadline," "posted about doing
                                      # X manually," "n/a — no reliable
                                      # trigger signal, treat as always-
                                      # relevant" (the honest-gap default
                                      # this pipeline uses everywhere
                                      # else applies here too)
    likely_objection: ""              # the first thing this persona
                                      # would push back on — used by the
                                      # content formula's value-prop
                                      # framing, not a hard requirement
    where_they_are: []                # platforms/communities/hashtags —
                                      # feeds discovery-query-design.md
                                      # and segment-research.md directly,
                                      # not duplicated logic
    language_they_use: []             # short list of actual phrases/
                                      # vocabulary this persona uses for
                                      # their own problem — sourced from
                                      # segment-research.md's corroborated
                                      # pattern records, never invented;
                                      # this is what makes drafted copy
                                      # sound like their words, not
                                      # Kene's or a generic template's
  built_at: null
  built_from: ""                     # "hermes_proposed" | "kene_authored"
  confirmed_at: null                  # same Rule 5 confirm-before-write
                                      # discipline as everything else in
                                      # this file — persona is a fact
                                      # about the pitch catalog, goes
                                      # through 07-context-architect
```

## How a persona actually gets built — Hermes proposes, Kene confirms

Same `taxonomy_suggested`-then-confirm shape `07-context-architect`
already uses for title variants, applied here:

1. **Trigger**: a new catalog entry gets confirmed (`held`/`adjacent`),
   or Kene explicitly asks to deepen an existing entry's persona.
   `wildcard` entries get personas too, once `wildcard_confirmed_
   explicitly: true` is set — building a detailed persona for an
   unconfirmed wildcard would be effort spent on a claim Kene hasn't
   even committed to yet.
2. **Draft pass**: Hermes proposes `who`/`company_context`/
   `buying_trigger`/`likely_objection`/`where_they_are` from the
   catalog entry's own `evidence` and `one_line_pitch` — this part is
   genuinely inferential (Hermes reasoning about who plausibly buys
   this), so it's clearly labeled a draft, not a finding.
3. **Grounding pass**: `stated_pains` and `language_they_use` are *not*
   drafted from inference — they're populated by running `17-cold-
   segment-research.md` against the draft
   persona's `where_they_are` list, and only entries that clear that
   file's corroboration threshold get pulled in. If segment research
   turns up nothing corroborated yet, both fields ship empty rather
   than filled with a guess — same honest-gap convention as the rest of
   this pipeline, and worth restating because it's the single easiest
   place for this feature to quietly drift into inventing detail that
   sounds specific but isn't sourced.
4. **Confirm**: `07-context-architect` runs the normal interview —
   Kene reviews the full block, edits or approves each field, sets
   `confirmed_at`. Nothing in `persona` is usable by a draft until this
   step completes, mirroring how `wildcard_confirmed_explicitly` gates
   catalog entries generally.

## Multiple offers, multiple personas — the actual mechanism

Nothing new has to be invented for "extract and define all of Kene's
offers": `shared/pitch-catalog.yaml` is already a list, and the
`taxonomy_suggested` proposal pass in `17-cold-prospecting/SKILL.md`'s
catalog section already draws candidate entries from the *full* memory
bank (STAR bank, domain-knowledge, project history) rather than one
offer at a time. What changes here is just that every candidate entry,
once confirmed, automatically queues for its own persona-build pass
(step 2 above) rather than the catalog stopping at `title`/
`one_line_pitch`/`target_customer_profile.summary`. A weekly digest
(piggybacking on cron job 12's existing cadence) surfaces any confirmed
catalog entry whose `persona.confirmed_at` is still null, so this
doesn't silently stall if Kene confirms a new offering and moves on
without immediately building it out.

## Where this plugs in

- `shared/pitch-catalog.yaml.template` — the schema itself.
- `17-cold-prospecting/references/segment-research.md` — the only
  legitimate source for `stated_pains`/`language_they_use`.
- `14-social-discovery-outreach/references/cold-dm-content-formula.md` —
  consumes `likely_objection`/`language_they_use` directly when drafting
  the actual message body.
- `17-cold-prospecting/SKILL.md`'s target-claim gate (Rule 8) — a
  `stated_pains` entry used in a pitch is a claim about the *target*,
  not about Kene, so it's still bound by "hypothesis, not assertion"
  framing even though it traces to a confirmed persona field.
