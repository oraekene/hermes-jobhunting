#!/usr/bin/env python3
"""
sweep.py — the central design dial: how strongly should the ledger speak?

Prior strength (pseudo-observations the ledger contributes per cell) trades
decision quality against fleet homogeneity. Low: nodes learn alone and mostly
conclude nothing. High: nodes converge on one answer and every application in
the fleet carries the same signature.

Also reports AGREEMENT — the share of nodes picking the same arm in a cell.
That is the monoculture measure, and it is the thing that decays a tactic once
ATS filters and detectors see enough of it.
"""
import random, statistics, simulate as S
from bandit import Evidence, HierarchicalPosterior, Policy, prob_better

def ledger_at(cap, users=400):
    agg = {}
    for _ in range(users):
        for _ in range(10):
            ctx = S.draw_ctx()
            arm = random.choice(["baseline", "variant"])
            key = f"ats_platform={ctx['ats_platform']}"
            s, t = agg.get((arm, key), (0.0, 0.0))
            agg[(arm, key)] = (s + S.outcome(arm, ctx), t + 1)
    out = {}
    for k, (s, t) in agg.items():
        if t:
            sc = min(1.0, cap / t)
            out[k] = (s * sc, t * sc)
    return out

def behavioural_diversity(post, n=400):
    """Belief convergence is harmless. BEHAVIOUR convergence is what gets seen.

    Measured as the share of applications not using the single modal arm, once
    the exploration floor and equivalence-class randomisation have had their
    say. This is the number a detector or an ATS filter would actually observe.
    """
    pol = Policy(post, ["baseline", "variant"])
    picked = [pol.choose(S.draw_ctx())[0] for _ in range(n)]
    modal = max(picked.count("variant"), picked.count("baseline"))
    return 1 - modal / n


def run(cap, users=200):
    led = ledger_at(cap) if cap else None
    resp, right, wrong, picks, div = [], 0, 0, {a: [] for a in S.ATS}, []
    for _ in range(users):
        calls, post = S.run_bayes(S.APPS_PER_YEAR, led)
        resp.append(post.realised)
        div.append(behavioural_diversity(post))
        r, w, _ = S.score(calls)
        right += r; wrong += w
        for a in S.ATS:
            ctx = {"ats_platform": a}
            picks[a].append("variant" if post.mean("variant", ctx) > post.mean("baseline", ctx)
                            else "baseline")
    tot = users * len(S.ATS)
    agree = statistics.mean(
        max(p.count("variant"), p.count("baseline")) / len(p) for p in picks.values())
    return (statistics.mean(resp), right / tot, wrong / tot, agree,
            statistics.mean(div))

random.seed(7)
print(f"{'ledger strength':>16}{'resp/yr':>10}{'correct':>10}{'wrong':>8}"
      f"{'belief agree':>14}{'behav. diversity':>18}")
for cap in [0, 20, 60, 150, 400, 2000]:
    r, c, w, ag, dv = run(cap)
    label = "silo (none)" if cap == 0 else f"{cap} pseudo-obs"
    print(f"{label:>16}{r:>10.1f}{c:>10.0%}{w:>8.0%}{ag:>13.0%}{dv:>17.0%}")
print()
print("Belief agreement and behavioural diversity are different things, and the")
print("distinction is the whole anti-monoculture argument. Nodes may agree on")
print("what works while still not all doing it, because the exploration floor")
print("and equivalence-class randomisation sit between belief and action.")
print("Belief convergence is harmless. Behaviour convergence is what gets seen.")
