# Federated Self-Improvement — design, with the numbers behind it

Unlike the four artefacts before this, none of it exists in the package yet. So
rather than assert that the shared design beats the siloed one, I simulated it
under the package's own parameters — 200 applications a year, ~10% baseline
response rate, and the learning loop's shipped thresholds of n ≥ 15 per bucket
and a ≥ 10pp gap. `simulate.py` and `sweep.py` are runnable and reproduce
everything below.

You said you'd only pick the option that guarantees significantly better
results. Nothing guarantees that, and the honest answer is more useful than a
confident one, so here is what the simulation actually shows.

## The headline result

300 simulated users, one genuinely better tactic whose lift varies by ATS
platform (+6pp on Greenhouse, +4 on Lever, +5 on Ashby, −2 on Workday):

| Regime | Correct | Wrong | No call | Responses/yr |
|---|---|---|---|---|
| No learning (incumbent only) | 0% | 0% | 100% | 20.2 |
| **A** — silo + threshold rule *(today)* | 26% | 6% | **68%** | — |
| **B** — silo + Bayesian | 25% | 5% | 70% | 23.8 |
| **C** — federated priors | 24% | **0%** | 76% | 24.2 |

Read the **no call** column first, because it is the finding that matters.

**The siloed loop is not a cautious baseline. It is a loop that concludes
nothing 68% of the time.** That's not a hypothesis — it's arithmetic. 200
applications a year, split across arms and platforms, never reaches n ≥ 15 per
bucket often enough to clear its own bar. So the real choice was never "safe
silo versus risky federation." It was "a loop that mostly cannot speak versus
one that can, with a management problem attached."

The second finding is the 6% → 0% collapse in **wrong** calls. That's the
partial-pooling effect: a thin cell inherits its parent's belief instead of
over-reading twelve noisy observations. Under the silo, one user in twenty acts
confidently on a tactic that is actually worse for them.

The third is the one I want to be straight about: at a conservative prior
strength, **federation buys only about +2% in realised responses over siloed
Bayesian learning.** The big jump — +18% — is from having *any* principled
learning rather than none. Federation's value at this scale is in eliminating
confident errors and in the sparsity ceiling, not in a dramatic outcome lift.

## The design dial, and why monoculture is less scary than I said

Prior strength — how many pseudo-observations the ledger contributes per cell —
is the single dial. `sweep.py`:

| Ledger strength | Resp/yr | Correct | Wrong | Belief agreement | Behavioural diversity |
|---|---|---|---|---|---|
| silo (none) | 23.9 | 20% | 5% | 68% | 37% |
| 20 pseudo-obs | 23.8 | 24% | 1% | 78% | 38% |
| 60 pseudo-obs | 24.3 | 32% | 0% | 86% | 39% |
| 150 pseudo-obs | 24.1 | 35% | 0% | 92% | 42% |
| 400 pseudo-obs | 24.2 | **69%** | 0% | 89% | 42% |
| 2000 pseudo-obs | 24.5 | 75% | 0% | **100%** | 39% |

I was too pessimistic in the earlier message, and the last two columns are why.

**Belief agreement and behavioural diversity are different things.** At a
strength of 2000, every node in the fleet believes the same thing — and 39% of
applications still don't use the modal arm, essentially unchanged from the silo.
The exploration floor and equivalence-class randomisation sit *between belief
and action*, so convergence of belief never becomes convergence of behaviour.

That matters because behaviour is what the other side sees. An ATS filter or a
detector learns from what arrives, not from what your nodes privately think. So
you can take the decision benefit — 20% → 69% correct, 5% → 0% wrong — without
paying the signature cost, provided the two mitigations are in the design from
the start rather than bolted on. **They are not optional extras. They are what
makes the useful region of that dial usable at all.**

Start at 150 and move on evidence.

## The four problems, as implemented

`bandit.py` is the runnable reference for all four.

**Cell sparsity.** Five context dimensions, ordered by how strongly each is
expected to moderate *which tactic wins*: `global → ats_platform → industry →
seniority_band → application_channel`. A cell inherits its parent's posterior
until it has its own evidence. Ordering rather than crossing is what keeps ten
plausible dimensions from becoming 59,000 cells — every dimension stays in the
model, only the top few carry independent posteriors.

Company deliberately isn't a context dimension. It's the sparsest available and
adds almost nothing beyond what industry and ATS already capture. `ats_platform`
is the densest and highest-signal, because it's the thing that mechanically
filters and it behaves the same everywhere.

**Model heterogeneity.** Less of a problem than it looks, because *the outcome
label is model-independent* — an employer decided, not an LLM. Model choice
affects execution fidelity, not label validity. So tier is a stratum, and global
promotion requires a win in ≥ 2 tiers, which kills "a strong model made a weak
tactic look good" directly.

**Continuous peeking.** The primary decision quantity is a Bayesian posterior
probability, which stays valid under optional stopping given a proper prior —
and the loop looks *every week* and promotes on the first thing that clears, so
a p-value under that regime isn't a p-value. Global promotion additionally has
to clear an anytime-valid frequentist bound: a node acting for itself may follow
its posterior, but pushing to the whole fleet is a higher bar.

**Monoculture.** Exploration floor at 12% — never zero, because a cell that
stops collecting evidence can't notice the world changing, and the premise of
this whole feature is that it does. Equivalence-class randomisation, which costs
nothing in expected performance because you were choosing arbitrarily among ties
anyway. And decay detection that watches performance *as a function of
adoption*: a negative slope against rising adoption is the signature, and it's
separable from noise precisely because adoption is a variable you control.

ε is a real tax — 12% means one application in eight knowingly uses a
worse method, and an application isn't a cheap repeatable trial for the person
sending it. 10–15% is the defensible range. Diversity should come from the
equivalence band, which is free, not from raising ε, which isn't.

## Share failures globally, discover successes locally

The asymmetry holds up and I'd apply it hardest to AI detection.

Never push "the current best way to sound human" as shared config. It is the
fastest-decaying, most fingerprintable artefact you could distribute, and
distributing it is what kills it. Negative results — *this pattern is now being
flagged* — are safe to share, immediately valuable, create no shared signature,
and can't be reverse-engineered into a detector target.

`dead_arms` is a first-class table for that reason, not an afterthought. Where
confidence is low anywhere in the system, share only the negative half.

## What the ledger sends

Priors and dead lists. Never verdicts. Three reasons, and the second is the one
that would have bitten your original design:

1. **A verdict can't carry uncertainty.** "Tactic B works on Greenhouse
   mid-level" reads identically at n=12 and n=4,000. A prior carries its own
   confidence, so a thin cell nudges and a rich cell moves — no threshold to
   tune.
2. **A verdict stops the evidence.** Your framing was that a node "doesn't need
   to run tests since it knows what works." The moment a node stops testing, the
   cell stops receiving data, and you cannot detect when the answer changes.
   Given that your whole premise is constant change, that's the one design
   guaranteed to go wrong *and be silent about it*.
3. **A verdict fails hard.** A poisoned or mistaken entry is executed. A
   poisoned prior is one input the node's own accumulating evidence overrides.

A node cut off from the ledger falls back to an uninformative prior and behaves
exactly like today's siloed system. That property is what makes this safe to
ship — and it's also why the ledger is the right thing to put behind the
licence, since it's the one component a copied client genuinely cannot have.

## Three tiers of variant generation

The existing two can only reweight tactics already written into a skill.
Neither can invent one.

| Tier | What it is | Cadence | Gate |
|---|---|---|---|
| 1 | Correlation over your own outcomes | Weekly | `GATE-SKILL-EDIT` |
| 2 | GEPA optimiser over the three writing skills | Quarterly, manual | `GATE-GEPA-DEPLOY` |
| 3 | Research-driven candidate generation | Weekly, user-toggleable | proposes only |

**Tier 3 proposes into `arm_candidates` and never edits anything.** Research
generates hypotheses; data selects among them. Without that separation you get a
system rewriting itself on what was upvoted last week — fashion with citations.

Sources, in descending order of signal: **ATS vendor changelogs** (Greenhouse,
Lever, Workday, Ashby — when a parser changes, this is where it's announced, and
it's low-noise and free); **your own fleet's failure data**, where a sudden drop
in one ATS cell is the earliest reliable signal that something changed, earlier
than anyone posting about it and something no competitor has; then `last30days`
and general social scraping, which tell you what people *believe* rather than
what changed.

## Supply chain

A ledger that auto-updates every node is a target, and it's gameable by anyone
running fake nodes to poison a cell. So: every push signed and verified before
apply; node reputation down-weighting outliers; and the split you already
agreed — **config updates auto-push, skill-logic edits stay human-gated**.
`received_priors` is kept separate from `local_posterior` so a bad push can be
dropped without losing the user's own data.

## Privacy

Channel A carries counts, cell keys, arm ids and model tier. No documents, no
employer names, no text anyone wrote. `outbound_telemetry` stages every payload
before it leaves, in a table the user can read — which is the only form of that
promise anyone should believe.

## Files

| File | What it is |
|---|---|
| `bandit.py` | Hierarchical posterior, Thompson policy, sequential test, decay monitor |
| `simulate.py` | Silo vs federated under the package's real parameters |
| `sweep.py` | The prior-strength dial against homogeneity |
| `ledger-schema.sql` | Central tables plus local `addendum_22` |

## The recommendation

Build it, with the shared layer supplying priors rather than decisions, starting
at strength 150, with the exploration floor and equivalence band present from
day one rather than added later.

Not because federation is dramatically better on outcomes — at your likely scale
it's worth a few percent. Because the siloed loop concludes nothing two thirds
of the time, because pooling is the only thing that fixes that, and because the
one cost I was most worried about turns out to be avoidable by construction.
