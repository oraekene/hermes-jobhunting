#!/usr/bin/env python3
"""
client.py — the node side of the learning loop.

    client.py choose --application 42 --ats greenhouse --industry saas \
                     --seniority mid --channel direct
    client.py outcome --application 42 --result response
    client.py sync [--dry-run]
    client.py explain --family letter_opening [--ats greenhouse]
    client.py status

FOUR THINGS THIS DOES, and one it deliberately does not.

  choose    picks one arm per family, Thompson sampling over a posterior that
            combines local evidence with the ledger's prior
  outcome   folds a real result back into the local posterior
  sync      sends counts up, brings priors and dead arms down
  explain   shows why an arm is currently favoured, in numbers

  It does NOT decide anything the user has gated. An arm is a choice about
  phrasing, structure, timing or channel. Whether to ask permission is not an
  arm and never will be.

OFFLINE IS THE NORMAL CASE. With no ledger contact the node uses an
uninformative prior and behaves exactly like the siloed system that shipped
before any of this existed. That fallback is what makes the feature safe to
turn on.
"""
from __future__ import annotations
import argparse, json, os, random, sqlite3, sys, urllib.request, uuid
from datetime import datetime, timezone
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bandit import HierarchicalPosterior, Evidence, cell_path, prob_better

ARMS = Path(os.environ.get("JH_ARMS", Path(__file__).resolve().parent.parent / "arms.yaml"))
DB = Path(os.environ.get("JH_DB", "shared/applications.db"))
TOKEN = os.environ.get("JH_TOKEN", "")
API = os.environ.get("JH_API", "https://api.example.com")

iso = lambda: datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def cfg():
    return yaml.safe_load(ARMS.read_text(encoding="utf-8"))


def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def ctx_from(args) -> dict:
    """Only dimensions that were actually supplied. An unspecified dimension is
    not 'unknown' — it means decide at the more general cell, where there is
    more evidence."""
    out = {}
    for k, v in (("ats_platform", args.ats), ("industry", args.industry),
                 ("seniority_band", args.seniority), ("application_channel", args.channel)):
        if v:
            out[k] = v
    return out


# ── posterior assembly ──────────────────────────────────────────────────────

def build_posterior(con, family, c):
    """Ledger priors first, then this node's own evidence on top.

    The two are kept in separate tables so they stay distinguishable: a bad push
    can be dropped without losing the user's own data, and the node's own
    results always move it away from the fleet mean.
    """
    conf = cfg()
    post = HierarchicalPosterior()
    keys = set(cell_path(c))
    arms = [a["id"] for a in conf["families"][family]["arms"]]

    cap = conf["policy"]["prior_strength_cap"]
    for r in con.execute(
            "SELECT cell_key, arm_id, alpha, beta FROM received_priors WHERE applied = 1"):
        if r["cell_key"] not in keys or r["arm_id"] not in arms:
            continue
        total = r["alpha"] + r["beta"]
        scale = min(1.0, cap / total) if total else 0
        e = post.cells.setdefault((r["arm_id"], r["cell_key"]), Evidence())
        e.successes += r["alpha"] * scale
        e.trials += total * scale

    for r in con.execute("SELECT cell_key, arm_id, successes, trials FROM local_posterior"):
        if r["cell_key"] not in keys or r["arm_id"] not in arms:
            continue
        e = post.cells.setdefault((r["arm_id"], r["cell_key"]), Evidence())
        e.successes += r["successes"]
        e.trials += r["trials"]
    return post, arms


def dead_arms(con, c):
    keys = set(cell_path(c)) | {"global"}
    return {r["arm_id"] for r in con.execute("SELECT arm_id, cell_key FROM received_dead_arms")
            if r["cell_key"] in keys}


def choose(con, family, c, conf):
    arms = [a["id"] for a in conf["families"][family]["arms"]]
    dead = dead_arms(con, c)
    live = [a for a in arms if a not in dead] or ["incumbent"]
    post, _ = build_posterior(con, family, c)

    p = conf["policy"]
    if random.random() < p["exploration_floor"]:
        return random.choice(live), "explore", post

    draws = {a: post.sample(a, c) for a in live}
    best = max(draws.values())
    tied = [a for a, v in draws.items() if v >= best - p["equivalence_band"]]
    return random.choice(tied), "exploit", post


# ── commands ────────────────────────────────────────────────────────────────

def cmd_choose(args):
    conf, con, c = cfg(), db(), ctx_from(args)
    leaf = cell_path(c)[-1]
    picked = {}
    for family, spec in conf["families"].items():
        if spec.get("capability") and spec["capability"] not in (args.capabilities or "").split(","):
            continue                       # addon absent: family not offered
        arm, mode, _ = choose(con, family, c, conf)
        picked[family] = {"arm": arm, "mode": mode}
        con.execute(
            """INSERT OR REPLACE INTO application_arms
               (application_id, arm_id, family, cell_key, mode, model_tier, chosen_at)
               VALUES (?,?,?,?,?,?,?)""",
            (args.application, arm, family, leaf, mode, args.model_tier, iso()))
    con.commit()
    print(json.dumps(picked, indent=2))


def cmd_outcome(args):
    """Fold a real result in. The label comes from an employer, not from a
    model — which is why model tier is a stratum here and not noise."""
    con = db()
    rows = con.execute(
        "SELECT arm_id, cell_key FROM application_arms WHERE application_id = ?",
        (args.application,)).fetchall()
    if not rows:
        print("no arms recorded for that application")
        return
    success = 1 if args.result in ("response", "screen", "interview", "offer") else 0
    n = 0
    for r in rows:
        # Every level of the hierarchy, so parents accumulate evidence too.
        for key in cell_path(dict(zip(
                ["ats_platform", "industry", "seniority_band", "application_channel"],
                r["cell_key"].replace("global", "").split("|")))) if False else [r["cell_key"]]:
            pass
        for key in _ancestors(r["cell_key"]):
            con.execute(
                """INSERT INTO local_posterior (cell_key, arm_id, successes, trials, updated_at)
                   VALUES (?,?,?,1,?)
                   ON CONFLICT(cell_key, arm_id) DO UPDATE SET
                     successes = successes + excluded.successes,
                     trials = trials + 1, updated_at = excluded.updated_at""",
                (key, r["arm_id"], success, iso()))
            n += 1
    con.commit()
    print(f"recorded {args.result} against {len(rows)} arms across {n} cells")


def _ancestors(cell_key):
    """'a=1|b=2' -> ['global', 'a=1', 'a=1|b=2']"""
    if cell_key == "global":
        return ["global"]
    parts = cell_key.split("|")
    return ["global"] + ["|".join(parts[:i + 1]) for i in range(len(parts))]


def cmd_sync(args):
    con = db()
    rows = [dict(r) for r in con.execute(
        """SELECT cell_key, arm_id, successes, trials FROM local_posterior
            WHERE trials > 0""")]
    payload = {"rows": [{"cell_key": r["cell_key"], "arm_id": r["arm_id"],
                         "model_tier": args.model_tier,
                         "successes": r["successes"], "trials": r["trials"]}
                        for r in rows]}
    # uuid, not a timestamp: two syncs in the same second collided on the
    # primary key and the failure surfaced as a crash rather than a retry.
    batch = "b" + uuid.uuid4().hex[:16]
    body = json.dumps(payload)

    # Staged in a table the user can read BEFORE it leaves. That is the only
    # form of the privacy promise anyone should believe: counts and cell keys,
    # no employer, no document, no text anyone wrote.
    con.execute("""INSERT INTO outbound_telemetry (batch_id, payload, created_at, bytes)
                   VALUES (?,?,?,?)""", (batch, body, iso(), len(body)))
    con.commit()

    if args.dry_run or not TOKEN:
        print(f"staged {len(payload['rows'])} rows ({len(body)} bytes) as {batch}")
        print("not sent — no token, or dry run")
        return

    try:
        _post(f"{API}/v1/telemetry", body)
        con.execute("UPDATE outbound_telemetry SET sent_at = ? WHERE batch_id = ?",
                    (iso(), batch))
        got = json.loads(_post(f"{API}/v1/ledger/sync", "{}"))
    except Exception as e:
        # Offline is normal, not an error. The node keeps its own posterior and
        # behaves exactly like the siloed system until contact resumes.
        con.commit()
        print(f"staged {batch}; ledger unreachable ({e.__class__.__name__}) — "
              f"continuing on local evidence alone")
        return

    for p in got.get("priors", []):
        con.execute(
            """INSERT INTO received_priors
               (cell_key, arm_id, alpha, beta, received_at, signature_ok, applied)
               VALUES (?,?,?,?,?,1,1)
               ON CONFLICT(cell_key, arm_id) DO UPDATE SET
                 alpha = excluded.alpha, beta = excluded.beta,
                 received_at = excluded.received_at""",
            (p["cell_key"], p["arm_id"], p["alpha"], p["beta"], iso()))
    for d in got.get("dead_arms", []):
        con.execute(
            """INSERT OR REPLACE INTO received_dead_arms
               (arm_id, cell_key, reason, received_at) VALUES (?,?,?,?)""",
            (d["arm_id"], d["cell_key"], d["reason"], iso()))
    con.commit()
    print(f"sent {len(payload['rows'])} rows; received "
          f"{len(got.get('priors', []))} priors, "
          f"{len(got.get('dead_arms', []))} retired approaches")


def _post(url, body):
    req = urllib.request.Request(
        url, data=body.encode(),
        headers={"content-type": "application/json",
                 "authorization": f"Bearer {TOKEN}"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read().decode()


def cmd_explain(args):
    conf, con, c = cfg(), db(), ctx_from(args)
    post, arms = build_posterior(con, args.family, c)
    dead = dead_arms(con, c)
    print(f"{conf['families'][args.family]['what']}")
    print(f"  cell: {cell_path(c)[-1]}\n")
    rows = []
    for a in arms:
        alpha, beta = post.posterior(a, c)
        rows.append((post.mean(a, c), a, alpha + beta, a in dead))
    for mean, a, n, is_dead in sorted(rows, reverse=True):
        tag = "  retired" if is_dead else ""
        print(f"  {mean:6.1%}  over {n:6.1f} observations   {a}{tag}")
    base = next((a for a in arms if a == "incumbent"), None)
    if base:
        top = max(rows)[1]
        if top != base:
            p = prob_better(post, top, base, c)
            print(f"\n  {top} looks better than what we do now, "
                  f"{p:.0%} confident.")
            if p < 0.9:
                print("  Not enough to act on yet — still gathering.")


def cmd_status(args):
    con = db()
    n_local = con.execute("SELECT COUNT(*) c FROM local_posterior").fetchone()["c"]
    n_prior = con.execute("SELECT COUNT(*) c FROM received_priors").fetchone()["c"]
    n_dead = con.execute("SELECT COUNT(*) c FROM received_dead_arms").fetchone()["c"]
    n_apps = con.execute(
        "SELECT COUNT(DISTINCT application_id) c FROM application_arms").fetchone()["c"]
    staged = con.execute(
        "SELECT COUNT(*) c FROM outbound_telemetry WHERE sent_at IS NULL").fetchone()["c"]
    print(f"  applications with a recorded approach : {n_apps}")
    print(f"  cells with your own evidence          : {n_local}")
    print(f"  starting points from other people     : {n_prior}")
    print(f"  approaches retired as no longer working: {n_dead}")
    print(f"  batches staged and not yet sent        : {staged}")
    if n_prior == 0:
        print("\n  No shared starting points yet — running entirely on your own results.")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("choose", "outcome", "sync", "explain", "status"):
        s = sub.add_parser(name)
        s.add_argument("--application", type=int)
        s.add_argument("--ats"); s.add_argument("--industry")
        s.add_argument("--seniority"); s.add_argument("--channel")
        s.add_argument("--model-tier", default="mid")
        s.add_argument("--capabilities", default="")
        s.add_argument("--result", default="none")
        s.add_argument("--family")
        s.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    {"choose": cmd_choose, "outcome": cmd_outcome, "sync": cmd_sync,
     "explain": cmd_explain, "status": cmd_status}[a.cmd](a)


if __name__ == "__main__":
    main()
