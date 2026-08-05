#!/usr/bin/env python3
"""
bandit.py — the federated learning core, as a runnable reference.

Four mechanisms, each answering one of the four problems:

  cell sparsity      -> HierarchicalPosterior  (partial pooling up a hierarchy)
  model heterogeneity-> stratified evidence + a two-tier promotion rule
  continuous peeking -> mSPRT always-valid confidence sequences
  monoculture        -> exploration floor, equivalence-class randomisation,
                        adoption-vs-performance decay detection

Nothing here needs a server to run. A node with no ledger connection uses an
uninformative prior and behaves exactly like today's siloed system, which is
the fallback property that makes the whole thing safe to ship.
"""
from __future__ import annotations
import math, random
from dataclasses import dataclass, field

# ── context ──────────────────────────────────────────────────────────────────
# Five context dimensions, ordered by how strongly each is expected to moderate
# WHICH TACTIC WINS. Order is the whole design: only the top levels ever carry
# independent posteriors; the rest inherit until they earn their own.
HIERARCHY = ["global", "ats_platform", "industry", "seniority_band", "application_channel"]


def cell_path(ctx: dict) -> list[str]:
    """Ordered list of cell keys from most general to most specific."""
    path, parts = ["global"], []
    for dim in HIERARCHY[1:]:
        if dim not in ctx:            # an unspecified dimension is not a level;
            break                     # it means "ask at the more general cell"
        parts.append(f"{dim}={ctx[dim]}")
        path.append("|".join(parts))
    return path


# ── partial pooling ──────────────────────────────────────────────────────────
@dataclass
class Evidence:
    """Beta-Binomial sufficient statistics, stratified by model tier."""
    successes: float = 0.0
    trials: float = 0.0
    by_tier: dict = field(default_factory=dict)   # tier -> (succ, trials)

    def add(self, success: bool, tier: str = "unknown", weight: float = 1.0):
        self.successes += weight * bool(success)
        self.trials += weight
        s, t = self.by_tier.get(tier, (0.0, 0.0))
        self.by_tier[tier] = (s + weight * bool(success), t + weight)

    def tiers_won(self, baseline_rate: float) -> int:
        """How many model tiers independently show this arm beating baseline.

        The outcome label is model-independent — an employer decided, not an
        LLM — so model tier is a stratum, not noise to average away. Requiring
        a win in >= 2 tiers kills 'a strong model made a weak tactic look good'.
        """
        return sum(1 for s, t in self.by_tier.values()
                   if t >= 5 and s / t > baseline_rate)


class HierarchicalPosterior:
    """Partial pooling: a cell inherits its parent until it earns its own view.

    KAPPA is the strength, in pseudo-observations, with which a parent informs
    a child. Low kappa = cells diverge fast on thin evidence. High kappa = the
    fleet mean dominates and every node behaves identically, which is the
    monoculture failure written as a hyperparameter.
    """
    KAPPA = 20.0

    def __init__(self, prior_mean: float = 0.10, prior_strength: float = 4.0):
        self.root = (prior_mean * prior_strength, prior_strength)
        self.cells: dict[tuple[str, str], Evidence] = {}

    def observe(self, arm: str, ctx: dict, success: bool,
                tier: str = "unknown", weight: float = 1.0):
        for key in cell_path(ctx):
            e = self.cells.setdefault((arm, key), Evidence())
            e.add(success, tier, weight)

    def posterior(self, arm: str, ctx: dict) -> tuple[float, float]:
        """Walk root -> leaf, each level shrinking toward its parent."""
        a, b = self.root
        for key in cell_path(ctx):
            e = self.cells.get((arm, key))
            if e is None or e.trials == 0:
                continue                      # inherit the parent unchanged
            m = a / (a + b)
            a, b = m * self.KAPPA, (1 - m) * self.KAPPA          # parent as prior
            a, b = a + e.successes, b + (e.trials - e.successes)  # local evidence
        return a, b

    def mean(self, arm, ctx):
        a, b = self.posterior(arm, ctx)
        return a / (a + b)

    def sample(self, arm, ctx):
        a, b = self.posterior(arm, ctx)
        return random.betavariate(max(a, 1e-6), max(b, 1e-6))

    def n(self, arm, ctx):
        e = self.cells.get((arm, cell_path(ctx)[-1]))
        return e.trials if e else 0.0


# ── always-valid inference ───────────────────────────────────────────────────
def prob_better(post, arm_b, arm_a, ctx, draws: int = 4000) -> float:
    """P(arm_b beats arm_a | evidence), by Monte Carlo on the two posteriors.

    This is the primary decision quantity, and deliberately so. A Bayesian
    posterior probability under a proper prior stays valid under optional
    stopping — which matters enormously here, because the loop looks every
    single week and promotes on the first thing that clears. A frequentist
    p-value under that regime is not a p-value.
    """
    hit = 0
    for _ in range(draws):
        if post.sample(arm_b, ctx) > post.sample(arm_a, ctx):
            hit += 1
    return hit / draws


def msprt_confidence(succ_a, n_a, succ_b, n_b, tau: float = 0.05) -> float:
    """Always-valid frequentist guardrail, used for GLOBAL promotion only.

    Deliberately more conservative than prob_better. A node acting on its own
    behalf may follow its posterior; pushing a change to the whole fleet is a
    higher bar and should clear an anytime-valid bound as well.

    Classical p-values are invalid when you look every week and promote on the
    first win — that is exactly what a weekly learning loop does. This bound
    holds under continuous peeking, so 'check every Monday and promote when it
    clears' is a valid stopping rule rather than a noise generator.

    Returns a value in [0,1]; treat >= 0.95 as promotable.
    """
    if n_a < 5 or n_b < 5:
        return 0.0
    p_a, p_b = (succ_a + 1) / (n_a + 2), (succ_b + 1) / (n_b + 2)
    n_eff = 1 / (1 / n_a + 1 / n_b)
    p_pool = (succ_a + succ_b + 1) / (n_a + n_b + 2)
    var = max(p_pool * (1 - p_pool), 1e-9)
    delta = p_b - p_a
    # mixture likelihood ratio against a N(0, tau^2) alternative
    root = math.sqrt(var / (var + n_eff * tau ** 2))
    lr = root * math.exp((n_eff ** 2 * tau ** 2 * delta ** 2) /
                         (2 * var * (var + n_eff * tau ** 2)))
    if delta <= 0:
        return 0.0
    return min(1.0, 1.0 - 1.0 / max(lr, 1.0))


# ── the policy ───────────────────────────────────────────────────────────────
class Policy:
    """Chooses an arm for one application.

    EPSILON is a real tax on the user: exploration means knowingly using a
    worse method on a real application, and an application is not a cheap
    repeatable trial for the person sending it. 10-15% is the defensible
    range. Never zero — a cell that stops collecting evidence cannot notice
    when the world changes underneath it, and the premise of this whole system
    is that it does.

    EQUIV_BAND costs nothing and buys most of the anti-monoculture benefit:
    among arms that are statistically indistinguishable you were choosing
    arbitrarily anyway, so choose randomly and the fleet stops converging on
    one detectable signature.
    """
    EPSILON = 0.12
    EQUIV_BAND = 0.02

    def __init__(self, post: HierarchicalPosterior, arms: list[str],
                 dead: set[str] | None = None):
        self.post, self.arms = post, arms
        self.dead = dead or set()          # negative-sharing: known-dead arms

    def live_arms(self):
        return [a for a in self.arms if a not in self.dead] or list(self.arms)

    def choose(self, ctx: dict) -> tuple[str, str]:
        arms = self.live_arms()
        if random.random() < self.EPSILON:
            return random.choice(arms), "explore"
        draws = {a: self.post.sample(a, ctx) for a in arms}       # Thompson
        best = max(draws.values())
        equiv = [a for a, v in draws.items() if v >= best - self.EQUIV_BAND]
        return random.choice(equiv), "exploit"


# ── decay detection ──────────────────────────────────────────────────────────
class DecayMonitor:
    """The failure mode nobody prices in.

    If the ledger finds the best method and pushes it everywhere, every node
    emits the same shape — and ATS filters, recruiters and detectors all learn
    population-level patterns. The more successful the convergence, the faster
    the method dies, and it dies for everyone at once.

    So: watch performance AS A FUNCTION OF ADOPTION. A negative slope with
    rising adoption is the signature, and it is distinguishable from ordinary
    noise precisely because adoption is a variable you control.
    """
    def __init__(self, window: int = 6):
        self.window, self.history = window, []

    def record(self, adoption: float, rate: float):
        self.history.append((adoption, rate))
        self.history = self.history[-self.window:]

    def decaying(self) -> bool:
        if len(self.history) < self.window:
            return False
        ad = [a for a, _ in self.history]
        rt = [r for _, r in self.history]
        n = len(ad)
        ma, mr = sum(ad) / n, sum(rt) / n
        cov = sum((a - ma) * (r - mr) for a, r in self.history)
        var = sum((a - ma) ** 2 for a in ad)
        if var < 1e-9:
            return False
        slope = cov / var
        return slope < -0.05 and ad[-1] > ad[0] + 0.15


def promotable(post, arm, baseline_arm, ctx, evidence_by_tier) -> tuple[bool, str]:
    """Global promotion requires more than a good posterior."""
    a1, b1 = post.posterior(baseline_arm, ctx)
    a2, b2 = post.posterior(arm, ctx)
    conf = msprt_confidence(a1, a1 + b1, a2, a2 + b2)
    if conf < 0.95:
        return False, f"confidence {conf:.2f} < 0.95"
    if evidence_by_tier.tiers_won(a1 / (a1 + b1)) < 2:
        return False, "wins in fewer than 2 model tiers"
    return True, f"confidence {conf:.2f}, multi-tier"
