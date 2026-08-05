# Connecting Paid Provider API Keys

Answers a direct question: no, this didn't exist before this pass.
Built now, using a real Hermes-native mechanism rather than inventing
credential storage from scratch.

## The mechanism: the official `1password` optional skill, not a plaintext config file

Hermes ships an official optional skill (`security/1password` —
`hermes skills install official/security/1password`) specifically for
setting up the 1Password CLI (`op`) and using it to read/inject secrets
into commands. This is the right home for provider API keys — **never**
`shared/enrichment-tier-usage.yaml` or any other file this package
already writes to, all of which are plain-text config meant to be
read/edited freely and are the wrong place for a credential regardless
of how convenient it would be to add one more field there.

## Setup — conversational, same register as everything else this package elicits

When Tier 2/3 needs a provider Kene hasn't connected yet, or when Kene
says something like "let's connect my Hunter account":

1. If the `1password` skill isn't installed, this skill asks Kene to
   install it (`hermes skills install official/security/1password`) —
   a one-time step, not something this skill does on his behalf without
   him knowing a new skill got installed.
2. Kene provides the API key however's easiest — pasted directly (least
   preferred, transient), or already stored in his own 1Password vault
   (preferred — nothing new to paste, this skill just needs the item
   reference).
3. This skill records **only the 1Password item reference**, never the
   raw key value, in `shared/enrichment-provider-keys.yaml` (ships as
   `.yaml.template`, copy before first use):

```yaml
connected_providers:
  # - provider: "hunter"
  #   op_item_reference: "op://Private/Hunter API/credential"
  #   connected_at: ""
  #   status: "active"   # active | revoked | expired
last_updated_at: null
```

4. At the point of actual use, this skill invokes `op` (via the
   1Password skill) to inject the real key into the specific API call —
   the key exists in memory for that one call and nowhere else in this
   pipeline's own files.

## What this changes about Tier 2/3 selection

`22-contact-enrichment/SKILL.md`'s Part B checks
`enrichment-provider-keys.yaml` before attempting any Tier 2/3 provider
beyond the free tiers already covered by rotation:

- A provider with `status: active` here is usable up to whatever its
  own account allows (free tier limits still tracked in
  `enrichment-tier-usage.yaml`; a connected paid plan simply removes
  that provider's ceiling).
- A provider with no connected key is skipped for anything beyond its
  free tier — this skill never prompts to connect a key mid-lookup;
  it either uses what's already connected or falls through to the next
  tier/provider.
- Revoking access is the same conversation in reverse — Kene says
  "disconnect Hunter," this skill sets `status: revoked` and stops
  attempting `op` lookups for that item reference.

## Why this matters practically, not just as a security nicety

`shared/enrichment-tier-usage.yaml`'s `tier3_monthly_budget_usd`
(`22-contact-enrichment/SKILL.md`'s Part B) governs *whether* Tier 3
spend is allowed at all — this file governs *which specific paid
providers* are even reachable once that budget exists. Connecting a key
here doesn't itself authorize spend; the budget cap still gates it. The
two systems are deliberately separate — one answers "can I use this
provider," the other answers "how much am I allowed to spend using it."
