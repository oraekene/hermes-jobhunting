#!/usr/bin/env python3
"""test_federated.py — the loop, end to end, including the cases that matter."""
import json, os, random, sqlite3, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(tempfile.mkdtemp())
NODE_DB = ROOT / "applications.db"
LEDGER = ROOT / "ledger.db"
random.seed(5)
CASES, FAILED = [], []

def check(n, c, extra=""):
    CASES.append((n, bool(c), extra))
    if not c: FAILED.append(n)

LOCAL = """
CREATE TABLE application_arms (application_id INTEGER, arm_id TEXT, family TEXT,
  cell_key TEXT, mode TEXT, model_tier TEXT, chosen_at TEXT,
  PRIMARY KEY (application_id, family));
CREATE TABLE local_posterior (cell_key TEXT, arm_id TEXT, successes REAL DEFAULT 0,
  trials REAL DEFAULT 0, updated_at TEXT, PRIMARY KEY (cell_key, arm_id));
CREATE TABLE received_priors (cell_key TEXT, arm_id TEXT, alpha REAL, beta REAL,
  received_at TEXT, signature_ok INTEGER, applied INTEGER DEFAULT 0,
  PRIMARY KEY (cell_key, arm_id));
CREATE TABLE received_dead_arms (arm_id TEXT, cell_key TEXT, reason TEXT,
  received_at TEXT, PRIMARY KEY (arm_id, cell_key));
CREATE TABLE outbound_telemetry (batch_id TEXT PRIMARY KEY, payload TEXT,
  created_at TEXT, sent_at TEXT, bytes INTEGER);
"""
SERVER = """
CREATE TABLE cell_evidence (cell_key TEXT, arm_id TEXT, model_tier TEXT,
  successes REAL, trials REAL, n_nodes INTEGER DEFAULT 0, updated_at TEXT,
  PRIMARY KEY (cell_key, arm_id, model_tier));
CREATE TABLE priors (cell_key TEXT, arm_id TEXT, alpha REAL, beta REAL,
  strength_cap REAL, tiers_won INTEGER, published_at TEXT, signature TEXT,
  PRIMARY KEY (cell_key, arm_id));
CREATE TABLE dead_arms (arm_id TEXT, cell_key TEXT, reason TEXT, evidence_n INTEGER,
  declared_at TEXT, signature TEXT, PRIMARY KEY (arm_id, cell_key));
CREATE TABLE adoption_history (arm_id TEXT, cell_key TEXT, week TEXT,
  adoption REAL, success_rate REAL, PRIMARY KEY (arm_id, cell_key, week));
"""
sqlite3.connect(NODE_DB).executescript(LOCAL)
sqlite3.connect(LEDGER).executescript(SERVER)

ENV = {**os.environ, "JH_DB": str(NODE_DB), "JH_ARMS": str(HERE.parent / "arms.yaml")}
def cli(*a):
    r = subprocess.run([sys.executable, str(HERE / "client.py"), *a],
                       capture_output=True, text=True, env=ENV)
    return r.returncode, (r.stdout + r.stderr).strip()

# ── client ──────────────────────────────────────────────────────────────────
rc, out = cli("choose", "--application", "1", "--ats", "greenhouse",
              "--industry", "saas", "--seniority", "mid", "--channel", "direct")
picked = json.loads(out) if rc == 0 else {}
check("choose returns one arm per family", rc == 0 and len(picked) >= 5,
      f"{len(picked)} families" if rc == 0 else "command failed")
check("capability-gated family withheld", "outreach_opening" not in picked,
      "the outreach addon was not declared present")

rc, out = cli("choose", "--application", "2", "--ats", "greenhouse",
              "--capabilities", "cold_outreach")
check("capability-gated family offered when licensed",
      "outreach_opening" in json.loads(out))

con = sqlite3.connect(NODE_DB)
n = con.execute("SELECT COUNT(*) FROM application_arms WHERE application_id=1").fetchone()[0]
check("choice recorded against the application", n >= 5)
cell = con.execute("SELECT cell_key FROM application_arms LIMIT 1").fetchone()[0]
check("cell key is the full context",
      cell == "ats_platform=greenhouse|industry=saas|seniority_band=mid|application_channel=direct")

cli("outcome", "--application", "1", "--result", "response")
rows = con.execute("SELECT cell_key, successes, trials FROM local_posterior").fetchall()
check("outcome credits every level of the hierarchy",
      any(r[0] == "global" for r in rows) and any("|" in r[0] for r in rows),
      "parents accumulate evidence, which is what makes thin cells usable")
check("a success is recorded as one", all(r[1] <= r[2] for r in rows))

cli("outcome", "--application", "2", "--result", "rejection")
g = con.execute("SELECT SUM(successes), SUM(trials) FROM local_posterior WHERE cell_key='global'").fetchone()
check("a rejection counts as a trial and not a success",
      g[1] > g[0] and g[0] > 0,
      f"{g[0]:.0f} successes over {g[1]:.0f} trials")

# ── offline ─────────────────────────────────────────────────────────────────
rc, out = cli("sync", "--dry-run")
check("sync stages before it sends", "staged" in out)
staged = con.execute("SELECT payload FROM outbound_telemetry").fetchone()[0]
p = json.loads(staged)
check("payload carries counts only",
      all(set(r) == {"cell_key","arm_id","model_tier","successes","trials"} for r in p["rows"]),
      "no employer, no document, no text anyone wrote")
check("staged payload is readable by the user", len(staged) > 0)

env2 = {**ENV, "JH_TOKEN": "t", "JH_API": "http://127.0.0.1:9"}
r = subprocess.run([sys.executable, str(HERE / "client.py"), "sync"],
                   capture_output=True, text=True, env=env2)
check("unreachable ledger is not an error",
      r.returncode == 0 and "continuing on local evidence" in r.stdout,
      "offline is the normal case, not a failure")

# ── dead arms are honoured ──────────────────────────────────────────────────
con.execute("INSERT INTO received_dead_arms VALUES ('brief','global','underperforms','x')")
con.commit()
seen = set()
for i in range(60):
    _, o = cli("choose", "--application", str(100 + i), "--ats", "greenhouse")
    seen.add(json.loads(o)["letter_length"]["arm"])
check("retired arm is never chosen", "brief" not in seen, f"saw {sorted(seen)}")

# exploration floor means the incumbent is not the only thing ever picked
check("exploration keeps trying alternatives", len(seen) >= 2, f"saw {sorted(seen)}")

# ── aggregation ─────────────────────────────────────────────────────────────
S = sqlite3.connect(LEDGER)
def ev(cell, arm, tier, s, t):
    S.execute("INSERT OR REPLACE INTO cell_evidence VALUES (?,?,?,?,?,1,'x')",
              (cell, arm, tier, s, t))
# a clear winner, visible in two tiers
ev("global", "incumbent", "mid", 40, 400); ev("global", "incumbent", "frontier", 10, 100)
ev("global", "mirror_headings", "mid", 60, 300); ev("global", "mirror_headings", "frontier", 22, 100)
# a clear loser
ev("global", "short_direct", "mid", 4, 300)
# a winner visible in only ONE tier
ev("global", "front_load_quantified", "mid", 70, 300)
# a thin cell that must publish nothing of its own
ev("ats_platform=lever", "mirror_headings", "mid", 2, 5)
S.commit()

sys.path.insert(0, str(HERE))
import aggregate
out = aggregate.run(str(LEDGER), dry_run=False)
pub = {(c, a): (up, won) for c, a, al, be, up, won in out["published"]}
check("winner beats the incumbent", pub[("global","mirror_headings")][0] >= 0.95)
check("winner confirmed across model tiers", pub[("global","mirror_headings")][1] >= 2)
check("single-tier winner is held back",
      any("front_load_quantified" in h[1] for h in out["held"]),
      "a strong model making a weak tactic look good is the failure this stops")
check("loser is retired", ("global","short_direct","underperforms") in
      [(c,a,w) for c,a,w in out["retired"]])
check("thin cell publishes nothing of its own",
      any(h[0] == "ats_platform=lever" for h in out["held"]))
check("priors are capped in strength",
      all(al + be <= aggregate.STRENGTH_CAP + 1e-6
          for _, _, al, be, _, _ in out["published"]))

# decay: performance falling as adoption rises
for i, (ad, rate) in enumerate([(0.1,0.20),(0.2,0.19),(0.35,0.16),
                                (0.5,0.13),(0.65,0.10),(0.8,0.07)]):
    S.execute("INSERT OR REPLACE INTO adoption_history VALUES (?,?,?,?,?)",
              ("mirror_headings","global",f"w{i}",ad,rate))
S.commit()
out2 = aggregate.run(str(LEDGER), dry_run=False)
check("decaying method is retired as adoption rises",
      ("global","mirror_headings","detected") in [(c,a,w) for c,a,w in out2["retired"]],
      "the more successful the convergence, the faster the method dies")

w = max(len(n) for n,_,_ in CASES)
for n, ok, extra in CASES:
    print(f"  {n:<{w}}  {'ok  ' if ok else 'FAIL'}{'  '+extra if extra else ''}")
print()
if FAILED:
    print(f"{len(FAILED)} failed: {FAILED}"); sys.exit(1)
print(f"{len(CASES)} checks pass")
