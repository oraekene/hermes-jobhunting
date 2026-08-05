#!/usr/bin/env python3
"""
simulate.py — does federated learning actually beat the silo?

The claim needs testing rather than asserting, so this runs the package's real
parameters: ~200 applications a year, ~10% baseline response rate, and the
learning loop's own shipped thresholds (n >= 15 per bucket, delta >= 10pp).

Three regimes compared:
  A  silo + threshold rule     what the package does today
  B  silo + Bayesian           same data, better statistics
  C  federated priors          shared prior, local posterior, local decisions

Measured over many simulated users: how often each regime identifies the truly
better tactic, how often it picks a worse one, and what it costs the user in
lost responses along the way.
"""
import random, statistics
from bandit import HierarchicalPosterior, Policy, Evidence, msprt_confidence, prob_better

random.seed(11)

APPS_PER_YEAR = 200
ATS = ["greenhouse", "lever", "workday", "ashby"]
IND = ["fintech", "health", "saas", "agency"]
SEN = ["mid", "senior"]

# Ground truth: one tactic is genuinely better, and by how much depends on the
# ATS platform. This is the effect the loop is supposed to find.
TRUE = {}
for ats in ATS:
    lift = {"greenhouse": 0.06, "lever": 0.04, "workday": -0.02, "ashby": 0.05}[ats]
    TRUE[ats] = {"baseline": 0.10, "variant": max(0.01, 0.10 + lift)}


def draw_ctx():
    return {"ats_platform": random.choice(ATS),
            "industry": random.choice(IND),
            "seniority_band": random.choice(SEN),
            "application_channel": "direct"}


def outcome(arm, ctx):
    return random.random() < TRUE[ctx["ats_platform"]][arm]


# ── A: today's rule ──────────────────────────────────────────────────────────
def run_threshold(n_apps):
    """n >= 15 per bucket and a >= 10pp gap, per 11-analytics-and-learning."""
    buckets = {}
    for _ in range(n_apps):
        ctx = draw_ctx()
        arm = random.choice(["baseline", "variant"])
        k = ctx["ats_platform"]
        b = buckets.setdefault(k, {"baseline": [0, 0], "variant": [0, 0]})
        ok = outcome(arm, ctx)
        b[arm][0] += ok
        b[arm][1] += 1
    calls = {}
    for k, b in buckets.items():
        nb, nv = b["baseline"][1], b["variant"][1]
        if nb < 15 or nv < 15:
            calls[k] = "no call"
            continue
        rb, rv = b["baseline"][0] / nb, b["variant"][0] / nv
        if abs(rv - rb) < 0.10:
            calls[k] = "no call"
        else:
            calls[k] = "variant" if rv > rb else "baseline"
    return calls


# ── B and C: Bayesian, with or without a shared prior ────────────────────────
def run_bayes(n_apps, shared_prior=None):
    post = HierarchicalPosterior()
    if shared_prior:
        # The ledger's contribution: pseudo-observations, not a directive.
        for (arm, key), (s, t) in shared_prior.items():
            e = post.cells.setdefault((arm, key), Evidence())
            e.successes += s
            e.trials += t
    pol = Policy(post, ["baseline", "variant"])
    got = 0
    for _ in range(n_apps):
        ctx = draw_ctx()
        arm, _mode = pol.choose(ctx)
        ok = outcome(arm, ctx)
        got += ok
        post.observe(arm, ctx, ok, tier="mid")
    post.realised = got
    calls = {}
    for ats in ATS:
        ctx = {"ats_platform": ats}      # decide at the level evidence supports
        p = prob_better(post, "variant", "baseline", ctx, draws=1500)
        calls[ats] = "variant" if p >= 0.90 else ("baseline" if p <= 0.10 else "no call")
    return calls, post


def build_ledger(n_users=400, apps=200):
    """What 400 users' worth of pooled evidence looks like at the ATS level."""
    agg = {}
    for _ in range(n_users):
        for _ in range(apps // 20):        # a slice each, to keep runtime sane
            ctx = draw_ctx()
            arm = random.choice(["baseline", "variant"])
            key = f"ats_platform={ctx['ats_platform']}"
            s, t = agg.get((arm, key), (0.0, 0.0))
            agg[(arm, key)] = (s + outcome(arm, ctx), t + 1)
    # ledger contributes as a PRIOR: capped strength, never raw counts, or the
    # fleet would simply overwrite the individual.
    CAP = 60.0
    out = {}
    for k, (s, t) in agg.items():
        if t == 0:
            continue
        scale = min(1.0, CAP / t)
        out[k] = (s * scale, t * scale)
    return out


def truth(ats):
    return "variant" if TRUE[ats]["variant"] > TRUE[ats]["baseline"] else "baseline"


def score(calls):
    right = sum(1 for a in ATS if calls[a] == truth(a))
    wrong = sum(1 for a in ATS if calls[a] not in ("no call", truth(a)))
    silent = sum(1 for a in ATS if calls[a] == "no call")
    return right, wrong, silent


def main():
    USERS = 300
    print(f"simulating {USERS} users x {APPS_PER_YEAR} applications/year")
    print("true lift per ATS: "
          + str({a: round(TRUE[a]["variant"] - TRUE[a]["baseline"], 3) for a in ATS}))
    print()

    ledger = build_ledger()

    def fixed(n_apps):
        """No learning at all: always the incumbent tactic. The floor."""
        got = 0
        for _ in range(n_apps):
            ctx = draw_ctx()
            got += outcome("baseline", ctx)
        return {a: "no call" for a in ATS}, got

    def thresh(n_apps):
        return run_threshold(n_apps), None

    def bayes(n_apps, led=None):
        c, post = run_bayes(n_apps, led)
        return c, post.realised

    rows = []
    for name, fn in [
        ("0  no learning (incumbent)", lambda: fixed(APPS_PER_YEAR)),
        ("A  silo + threshold rule",   lambda: thresh(APPS_PER_YEAR)),
        ("B  silo + Bayesian",         lambda: bayes(APPS_PER_YEAR)),
        ("C  federated priors",        lambda: bayes(APPS_PER_YEAR, ledger)),
    ]:
        R = W = S_ = 0
        resp = []
        for _ in range(USERS):
            calls, got = fn()
            r, w, sl = score(calls)
            R += r; W += w; S_ += sl
            if got is not None:
                resp.append(got)
        tot = USERS * len(ATS)
        rows.append((name, R / tot, W / tot, S_ / tot,
                     statistics.mean(resp) if resp else None))

    print(f"{'regime':<28}{'correct':>9}{'wrong':>8}{'no call':>9}{'responses/yr':>14}")
    for name, r, w, sl, resp in rows:
        rs = f"{resp:.1f}" if resp is not None else "n/a"
        print(f"{name:<28}{r:>8.0%}{w:>8.0%}{sl:>9.0%}{rs:>14}")

    base = rows[0][4]
    fed = rows[3][4]
    silo = rows[2][4]
    print()
    print(f"silo learning      : {silo - base:+.1f} responses/yr vs no learning "
          f"({(silo - base) / base:+.0%})")
    print(f"federated priors   : {fed - base:+.1f} responses/yr vs no learning "
          f"({(fed - base) / base:+.0%})")
    print(f"federation over silo: {fed - silo:+.1f} responses/yr "
          f"({(fed - silo) / silo:+.0%})")
    print()
    print("Read 'no call' first. The silo's real failure is not wrong answers —")
    print("it is a loop that runs every week and concludes nothing, because one")
    print("person's application volume never reaches its own evidence bar.")

if __name__ == "__main__":
    main()
