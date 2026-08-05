# How the learning loop works

Three tiers, and only the third is new.

| Tier | What it does | Cadence | Gate |
|---|---|---|---|
| 1 | Correlates your own tactics against your own outcomes | Weekly | you approve each edit |
| 2 | Evolves the writing skills against a golden set | Quarterly, manual | you diff and apply |
| 3 | **Chooses between named approaches and measures which wins** | Every application | none — no approach may change what you are asked |

Tiers 1 and 2 can only reweight what is already written into a skill. Neither can
invent an approach. Tier 3 is the one that can, and it is the one the ledger
serves.

## What is being chosen

Six families, one arm each per application: resume structure, keyword handling,
letter opening, letter length, send timing, outreach opening.

**Every family has an incumbent, and it is what the skills already do.** The
loop can only ever measure against something, and "what we did before" is the
only baseline that means anything to a user.

**No arm may violate a gate.** An arm is a choice about phrasing, structure,
timing or channel — never about whether to ask permission. The evidence gate
applies to every arm equally, and an arm that only performs well under loosened
evidence rules is a finding about the rules, not the arm.

## Why one user cannot learn alone

200 applications a year, split across arms and platforms, does not reach the
sample sizes the analytics skill's own thresholds require. Simulated across 300
users, the siloed rule **concludes nothing 68% of the time**. That is arithmetic,
not pessimism.

So the choice was never "safe silo versus risky sharing". It was "a loop that
mostly cannot speak versus one that can, with a management problem attached".

## What the ledger sends, and what it does not

**Priors and a dead list. Never verdicts.**

A verdict cannot carry uncertainty — "this works on Greenhouse" reads identically
at twelve observations and four thousand. A prior carries its own confidence, so
a thin cell nudges and a rich cell moves, with no threshold to tune.

A verdict also stops the evidence. The moment a node accepts an answer and stops
testing, that cell stops receiving data — and you cannot detect when the answer
changes. Given that the whole premise is constant change, that is the one design
guaranteed to go wrong *and* be silent about it.

And a verdict fails hard. A poisoned entry is executed; a poisoned prior is one
input the node's own results override.

## What leaves your machine

Counts and cell keys. Arm id, model tier, successes, trials.

No employer name. No document. No text anyone wrote. Every batch is staged in a
table you can read before it is sent, which is the only form of that promise
worth believing — not a policy, but a payload you can inspect.

**Offline is the normal case.** With no ledger contact the node uses an
uninformative prior and behaves exactly like the siloed system that shipped
before any of this. Nothing degrades; it just stops improving.

## Monoculture, and why it is manageable

If everyone converged on one method, filters and detectors would learn it — and
the more successful the convergence, the faster it would die, for everyone at
once.

Three things prevent that, and they are in the design rather than bolted on:

- **An exploration floor of 12%, never zero.** A cell that stops collecting
  evidence cannot notice the world changing underneath it. It is a real tax —
  one application in eight knowingly uses a worse approach — which is why it is
  12% and not 30%.
- **Randomisation among ties.** Where two approaches are statistically
  indistinguishable, pick randomly. Free, because you were choosing arbitrarily
  among them anyway.
- **Decay detection.** Performance is tracked against *adoption*. A method
  falling as adoption rises is retired automatically — that pattern is the
  signature, and it is separable from noise precisely because adoption is a
  variable the ledger controls.

Simulation showed belief agreement reaching 100% while **behavioural diversity
stayed near 40%** — the exploration floor and tie randomisation sit between
belief and action. Belief convergence is harmless; behaviour convergence is what
gets seen.

## Share failures globally, discover successes locally

Retiring an approach is safe to share: immediately valuable, creates no shared
signature, and cannot be reverse-engineered into a fingerprint.

This applies hardest to anything about sounding human. A shared "best way to
avoid detection" is the fastest-decaying, most fingerprintable thing that could
possibly be distributed — distributing it is what kills it. So only the negative
half is shared, and each node varies its own style locally.

## Promotion rules

Before anything is published as a winner:

- **Always-valid confidence ≥ 0.95.** This runs every week and promotes on the
  first thing that clears; a classical p-value under that regime is not a
  p-value.
- **A win in at least two model tiers.** The outcome label is model-independent
  — an employer decided, not a model — but execution fidelity is not. This kills
  "a strong model made a weak approach look good".
- **At least 30 observations in the cell**, or it inherits its parent and
  publishes nothing of its own.

## Commands

```bash
client.py choose --application 42 --ats greenhouse --industry saas \
                 --seniority mid --channel direct
client.py outcome --application 42 --result response
client.py sync --dry-run          # stage without sending
client.py explain --family letter_opening --ats greenhouse
client.py status

aggregate.py --db ledger.db --dry-run --report   # weekly, server side
```

`explain` is the one worth showing a user. It prints each approach, its rate,
how many observations sit behind it, and how confident the comparison is — and
says plainly when there is not enough evidence to act on yet.
