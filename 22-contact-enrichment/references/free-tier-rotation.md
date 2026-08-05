# Free-Tier Rotation — combining several small free allowances into one larger one

The mechanism behind Part B Tier 2 in `22-contact-enrichment/SKILL.md`.
No single vendor's free tier is generous enough to rely on alone (50-100
lookups/month, typically) — but nothing stops combining several
different vendors' free tiers, since they're independent accounts with
independent quotas. Rotating across them is just bookkeeping, not a
loophole in any provider's terms — each one is used exactly as offered,
within its own stated free allowance.

## Tracking

Ships as `shared/enrichment-tier-usage.yaml.template` (copy to
`enrichment-tier-usage.yaml` before first use):

```yaml
providers:
  - name: "hunter"
    monthly_allowance: 50
    used_this_cycle: 0
    cycle_resets_at: null
  # ...one entry per rotated provider — see the template file for the
  # complete starting set (hunter, snov, getprospect + its separate
  # verification pool, prospeo, skrapp, apollo, and the free verifiers
  # zerobounce/kickbox)
last_updated_at: null
```

## Selection order within Tier 2

Not round-robin, not always the same provider first — pick whichever
provider currently has the most remaining `used_this_cycle` headroom
for that lookup, so a rotation doesn't accidentally exhaust one
provider early in the month while others sit unused. Rollover-eligible
providers (Skrapp, GetProspect) are worth spending down *last* within
their own cycle, since unused credits there survive into the next
period rather than being lost.

## What this doesn't do

Doesn't create a single combined "pool" across providers — each has its
own data coverage and accuracy profile (see `enrichment-tools-
pricing.md`), so a miss on one provider is still worth trying on
another even within the same lookup, not just spreading load evenly.
Rotation optimizes for *not running out*, not for picking the single
best answer — Part B's verification step (mandatory regardless of
which tier found the candidate) is what actually protects quality.
