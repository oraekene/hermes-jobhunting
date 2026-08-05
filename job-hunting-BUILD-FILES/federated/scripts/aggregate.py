#!/usr/bin/env python3
"""
aggregate.py — the weekly job that turns pooled counts into priors.

    aggregate.py --db ledger.db [--dry-run] [--report]

This is the piece that makes the ledger worth having. Without it the server
collects evidence and never says anything back.

FOUR RULES, each answering one of the four problems.

  sparsity     partial pooling — a cell inherits its parent until it has its
               own evidence, so a thin cell nudges and a rich cell moves
  heterogeneity a variant must win in >= 2 model tiers before it goes global,
               because the outcome label is model-independent but execution
               fidelity is not
  peeking      an always-valid bound, because this runs EVERY WEEK and promotes
               on the first thing that clears — a p-value under that regime is
               not a p-value
  monoculture  performance is tracked against ADOPTION, and a method decaying
               as adoption rises is retired rather than defended

WHAT IT PUBLISHES. Priors and a dead list. Never verdicts. A prior carries its
own confidence and a node's own results still move it away from the fleet mean;
a verdict does neither, and stops the cell collecting evidence at exactly the
moment you most need to know whether the answer has changed.
"""
from __future__ import annotations
import argparse, json, sqlite3, sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bandit import msprt_confidence

KAPPA = 20.0            # strength with which a parent informs a child
STRENGTH_CAP = 150.0    # how loudly the ledger speaks — see sweep.py
MIN_TRIALS = 30         # below this a cell publishes nothing of its own
MIN_TIERS = 2
PROMOTE_AT = 0.95
DECAY_SLOPE = -0.05
DECAY_ADOPTION_RISE = 0.15
BASELINE = "incumbent"

iso = lambda: datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parent(cell_key):
    if cell_key == "global":
        return None
    parts = cell_key.split("|")
    return "|".join(parts[:-1]) if len(parts) > 1 else "global"


def depth(cell_key):
    return 0 if cell_key == "global" else cell_key.count("|") + 1


def load(con):
    ev = defaultdict(lambda: defaultdict(lambda: [0.0, 0.0]))   # cell -> arm -> [s,t]
    tiers = defaultdict(lambda: defaultdict(dict))              # cell -> arm -> tier
    for r in con.execute(
            "SELECT cell_key, arm_id, model_tier, successes, trials FROM cell_evidence"):
        a = ev[r["cell_key"]][r["arm_id"]]
        a[0] += r["successes"]; a[1] += r["trials"]
        tiers[r["cell_key"]][r["arm_id"]][r["model_tier"]] = (r["successes"], r["trials"])
    return ev, tiers


def pooled(ev, cell, arm, prior_mean=0.10, prior_strength=4.0):
    """Walk root -> cell, shrinking toward the parent at each step."""
    chain, c = [], cell
    while c:
        chain.append(c); c = parent(c)
    chain.reverse()
    a, b = prior_mean * prior_strength, (1 - prior_mean) * prior_strength
    for key in chain:
        s, t = ev.get(key, {}).get(arm, [0.0, 0.0])
        if t == 0:
            continue
        m = a / (a + b)
        a, b = m * KAPPA, (1 - m) * KAPPA
        a, b = a + s, b + (t - s)
    return a, b


def tiers_won(tiers, cell, arm, baseline_rate):
    won = 0
    for tier, (s, t) in tiers.get(cell, {}).get(arm, {}).items():
        if t >= 5 and s / t > baseline_rate:
            won += 1
    return won


def decaying(con, cell, arm):
    rows = con.execute(
        """SELECT adoption, success_rate FROM adoption_history
            WHERE cell_key = ? AND arm_id = ? ORDER BY week DESC LIMIT 6""",
        (cell, arm)).fetchall()
    if len(rows) < 6:
        return False
    ad = [r[0] for r in rows][::-1]
    rt = [r[1] for r in rows][::-1]
    n = len(ad)
    ma, mr = sum(ad) / n, sum(rt) / n
    var = sum((x - ma) ** 2 for x in ad)
    if var < 1e-9:
        return False
    slope = sum((a - ma) * (r - mr) for a, r in zip(ad, rt)) / var
    return slope < DECAY_SLOPE and ad[-1] > ad[0] + DECAY_ADOPTION_RISE


def run(db_path, dry_run=False):
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    ev, tiers = load(con)
    published, retired, held = [], [], []

    for cell in sorted(ev, key=depth):
        arms = ev[cell]
        total = sum(t for _, t in arms.values())
        if total < MIN_TRIALS and cell != "global":
            held.append((cell, "thin", total))
            continue

        ba, bb = pooled(ev, cell, BASELINE)
        base_rate = ba / (ba + bb)

        for arm in arms:
            a, b = pooled(ev, cell, arm)
            n = a + b

            if decaying(con, cell, arm):
                retired.append((cell, arm, "detected"))
                if not dry_run:
                    con.execute(
                        """INSERT OR REPLACE INTO dead_arms
                           (arm_id, cell_key, reason, evidence_n, declared_at, signature)
                           VALUES (?,?,?,?,?,?)""",
                        (arm, cell, "detected", int(n), iso(), "unsigned"))
                continue

            # Losing badly is worth sharing and costs nothing. Negative results
            # create no shared signature and cannot be reverse-engineered into
            # a fingerprint — share failures globally, discover successes locally.
            down = msprt_confidence(a, n, ba, ba + bb)
            if arm != BASELINE and down >= PROMOTE_AT:
                retired.append((cell, arm, "underperforms"))
                if not dry_run:
                    con.execute(
                        """INSERT OR REPLACE INTO dead_arms
                           (arm_id, cell_key, reason, evidence_n, declared_at, signature)
                           VALUES (?,?,?,?,?,?)""",
                        (arm, cell, "underperforms", int(n), iso(), "unsigned"))
                continue

            up = msprt_confidence(ba, ba + bb, a, n)
            won = tiers_won(tiers, cell, arm, base_rate)
            if arm != BASELINE and up >= PROMOTE_AT and won < MIN_TIERS:
                held.append((cell, f"{arm}: wins but only in {won} model tier(s)", n))
                # Still published as a prior — just not celebrated as a winner.

            scale = min(1.0, STRENGTH_CAP / n) if n else 0
            alpha, beta = a * scale, b * scale
            published.append((cell, arm, alpha, beta, up, won))
            if not dry_run:
                con.execute(
                    """INSERT OR REPLACE INTO priors
                       (cell_key, arm_id, alpha, beta, strength_cap, tiers_won,
                        published_at, signature)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (cell, arm, alpha, beta, STRENGTH_CAP, won, iso(), "unsigned"))

    if not dry_run:
        con.commit()
    con.close()
    return {"published": published, "retired": retired, "held": held}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="ledger.db")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()

    out = run(a.db, a.dry_run)
    print(f"{'DRY RUN — nothing written' if a.dry_run else 'published'}")
    print(f"  priors written   {len(out['published'])}")
    print(f"  approaches retired {len(out['retired'])}")
    print(f"  cells held back  {len(out['held'])}")

    if a.report:
        if out["retired"]:
            print("\nRETIRED")
            for cell, arm, why in out["retired"]:
                print(f"  {cell:<40} {arm:<24} {why}")
        winners = [p for p in out["published"] if p[1] != BASELINE and p[4] >= PROMOTE_AT]
        if winners:
            print("\nBEATING THE INCUMBENT")
            for cell, arm, al, be, up, won in sorted(winners, key=lambda r: -r[4]):
                flag = "" if won >= MIN_TIERS else "   (one model tier only — holding)"
                print(f"  {cell:<40} {arm:<24} {up:.0%}{flag}")
        if out["held"]:
            print("\nHELD BACK")
            for cell, why, n in out["held"][:12]:
                print(f"  {cell:<40} {why} (n={n:.0f})")


if __name__ == "__main__":
    main()
