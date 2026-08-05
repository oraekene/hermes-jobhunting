#!/usr/bin/env python3
"""
install-check.py — runs at the first turn of every session.

Replaces the existing install-check with one that enforces preflight items 2, 5
and 6, plus the checks that were already there.

    python3 install-check.py                 # human-readable report
    python3 install-check.py --json          # machine-readable
    python3 install-check.py --root PATH --db PATH

WHY THIS RUNS EVERY SESSION AND NOT JUST ONCE
The worst failure available here is not a crash. It is a skill that reads
convincingly with no rules, no database and no profile behind it — and produces
plausible output the whole way. Nothing about that failure announces itself, so
something has to look.

WHAT IT PRINTS
Plain language only. No file paths, no skill directory names, no rule numbers,
no table names in anything a user sees. Each finding carries a short code; the
detail goes to the local log for support. --json is for the tool, not the user.

EXIT CODES
  0  everything required is present
  1  degraded — the package runs, with named capabilities unavailable
  2  blocked — do not run; something required is missing or unverifiable
"""
from __future__ import annotations
import argparse, hashlib, json, os, sqlite3, sys
from pathlib import Path

# ── findings ────────────────────────────────────────────────────────────────

BLOCK, DEGRADE, NOTE = "block", "degrade", "note"

MESSAGES = {
    # code: (severity, what the user reads)
    "E01": (BLOCK,   "Your setup is incomplete — some required parts are missing. "
                     "I have stopped rather than run on a partial install, because "
                     "a partial install produces confident answers built on nothing."),
    "E02": (BLOCK,   "I could not verify your saved data is intact. I have stopped "
                     "rather than write to it."),
    "E03": (BLOCK,   "Your approval channel is not restricted to you. Until it is, "
                     "anyone reaching it could approve applications in your name."),
    "E04": (BLOCK,   "Your settings file has changed since this session started. "
                     "I have stopped and changed nothing."),
    "E05": (BLOCK,   "Your daily limit is not readable, so I cannot tell how many "
                     "applications may be prepared. I have stopped."),
    "W01": (DEGRADE, "Some of your saved data is missing pieces it should have. "
                     "I can continue, but some history may be incomplete."),
    "W02": (DEGRADE, "One or more optional capabilities are not available on your "
                     "plan. Everything else works normally."),
    "W03": (DEGRADE, "Your settings file sits somewhere I can write to. That is "
                     "workable, but it is safer somewhere I cannot."),
    "N01": (NOTE,    "You are running inside a container. Your computer is well "
                     "protected, and one of the three checks before an application "
                     "is sent does not apply here — the other two still do."),
    "N02": (NOTE,    "No baseline recorded from before you started. Some progress "
                     "comparisons will not be available."),
}


class Report:
    def __init__(self):
        self.findings: list[tuple[str, str]] = []   # (code, detail for the log)

    def add(self, code, detail=""):
        self.findings.append((code, detail))

    def severity(self):
        sev = [MESSAGES[c][0] for c, _ in self.findings]
        if BLOCK in sev:
            return BLOCK
        if DEGRADE in sev:
            return DEGRADE
        return None

    def exit_code(self):
        return {BLOCK: 2, DEGRADE: 1, None: 0}[self.severity()]


# ── 1. completeness ─────────────────────────────────────────────────────────

REQUIRED_AREAS = ["shared", "security", "cron", "templates"]
REQUIRED_SHARED = [
    "pipeline-rules.md", "site-access-model.md", "tier-config.yaml",
    "applications_db_schema.sql",
]


def check_completeness(root: Path, manifest: dict, rep: Report):
    """shared/ sits outside every skill directory, so installing one skill
    brings none of the rules it declares it must follow."""
    missing = []
    for area in REQUIRED_AREAS:
        if not (root / area).is_dir():
            missing.append(area + "/")
    for f in REQUIRED_SHARED:
        if not (root / "shared" / f).is_file():
            missing.append("shared/" + f)
    for s in manifest.get("core", {}).get("skills", []):
        sid = s["id"] if isinstance(s, dict) else s
        if not (root / sid / "SKILL.md").is_file():
            missing.append(sid)
    if missing:
        rep.add("E01", "missing: " + ", ".join(missing))
    return missing


# ── 2. capabilities present vs declared ─────────────────────────────────────

def check_capabilities(root: Path, manifest: dict, rep: Report):
    """An absent addon is normal, not an error — but core must not be left
    referencing something that is not there."""
    unavailable = []
    for addon in manifest.get("addons", []):
        installed = all((root / s / "SKILL.md").is_file() for s in addon["skills"])
        if not installed:
            unavailable.extend(addon["provides_capabilities"])
    if unavailable:
        rep.add("W02", "unavailable capabilities: " + ", ".join(sorted(set(unavailable))))
    return sorted(set(unavailable))


# ── 3. migration ledger vs reality  (preflight item 2) ──────────────────────

def check_migrations(db: Path, rep: Report):
    """The recorded history asserts what ran. This checks it actually landed.

    Tables are cross-checked in SQL by addendum_21. Columns cannot be — PRAGMA
    table_info is not expressible portably in a query — so they are checked
    here and written back, which is the half addendum_21 explicitly defers.
    """
    if not db.is_file():
        rep.add("E02", f"database not found at {db}")
        return []
    try:
        con = sqlite3.connect(str(db))
        con.row_factory = sqlite3.Row
    except sqlite3.Error as e:
        rep.add("E02", f"cannot open database: {e}")
        return []

    def has_table(name):
        return con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (name,)).fetchone() is not None

    if not has_table("schema_version"):
        rep.add("E02", "no migration history recorded")
        con.close()
        return []
    if not has_table("schema_expected"):
        # pre-addendum_21 database: nothing to verify against, and that is a
        # statement about the installer's age, not a fault in the data.
        rep.add("W01", "migration verification not yet installed (pre-21 database)")
        con.close()
        return []

    applied = {r["filename"] for r in con.execute("SELECT filename FROM schema_version")}
    drift = []
    for r in con.execute("SELECT migration, object, kind FROM schema_expected"):
        if r["migration"] not in applied:
            continue                        # not claimed, so not drift
        obj, kind = r["object"], r["kind"]
        if kind == "table":
            present = has_table(obj)
        elif kind == "column":
            tbl, _, col = obj.partition(".")
            cols = {c["name"] for c in con.execute(f"PRAGMA table_info({tbl})")}
            present = col in cols
        else:
            continue
        if not present:
            drift.append((r["migration"], obj, kind))
        # write findings back so the report survives the process
        try:
            con.execute(
                "INSERT OR REPLACE INTO schema_drift (migration, object, kind, present)"
                " VALUES (?,?,?,?)", (r["migration"], obj, kind, int(present)))
        except sqlite3.Error:
            pass
    con.commit()
    con.close()
    if drift:
        rep.add("W01", "recorded but missing: " +
                ", ".join(f"{o} ({k})" for _, o, k in drift))
    return drift


# ── 4. daily cap is actually readable  (preflight item 5) ───────────────────

def check_cap(root: Path, rep: Report):
    """The cap is the last thing between a bug in auto-approve mode and a full
    day of unreviewed applications. Its enforcement is only as real as the key
    being read, so read it here and fail loudly if it is not there."""
    path = root / "shared" / "tier-config.yaml"
    if not path.is_file():
        rep.add("E05", "tier config missing")
        return None
    try:
        import yaml
        cfg = yaml.safe_load(path.read_text())
    except Exception as e:
        rep.add("E05", f"tier config unreadable: {e}")
        return None
    active = cfg.get("active_tier")
    tier = (cfg.get("tiers") or {}).get(active) or {}
    cap = tier.get("daily_staging_cap")
    if not isinstance(cap, int) or cap <= 0:
        rep.add("E05", f"active_tier={active!r} has no usable daily_staging_cap")
        return None
    return cap


# ── 5. approval channel is restricted ───────────────────────────────────────

def check_pairing(env: dict, rep: Report):
    """Every gate in the registry means nothing if any account can approve."""
    if str(env.get("GATEWAY_ALLOW_ALL_USERS", "")).lower() in ("1", "true", "yes"):
        rep.add("E03", "GATEWAY_ALLOW_ALL_USERS is enabled")
        return False
    if not env.get("GATEWAY_PAIRED_USER") and not env.get("GATEWAY_ALLOWED_USERS"):
        rep.add("E03", "no paired identity configured")
        return False
    return True


# ── 6. policy file integrity ────────────────────────────────────────────────

def check_policy(policy: Path, root: Path, state: Path, rep: Report):
    """The attack this defends against: text inside a scraped posting persuades
    the agent to write auto_approve into the policy file, and the submit check
    then reads that same file and waves everything through.

    Two defences. The file lives outside the agent's writable working directory,
    and its checksum is pinned at session start — a mid-session change fails
    closed rather than being trusted.
    """
    if not policy.is_file():
        return None                       # no policy yet: all gates at default
    try:
        policy.relative_to(root)
        rep.add("W03", f"policy file is inside the working directory: {policy}")
    except ValueError:
        pass                              # outside, which is what we want

    digest = hashlib.sha256(policy.read_bytes()).hexdigest()
    state.parent.mkdir(parents=True, exist_ok=True)
    if state.is_file():
        prior = state.read_text().strip()
        if prior and prior != digest:
            rep.add("E04", f"policy checksum changed mid-session "
                           f"({prior[:12]}… -> {digest[:12]}…)")
            return digest
    state.write_text(digest)
    return digest


# ── 7. execution environment  (preflight item 6) ────────────────────────────

def detect_container(env: dict | None = None) -> bool:
    env = os.environ if env is None else env
    if env.get("HERMES_TERMINAL_BACKEND", "").lower() == "container":
        return True
    if Path("/.dockerenv").exists():
        return True
    try:
        return "docker" in Path("/proc/1/cgroup").read_text() or \
               "containerd" in Path("/proc/1/cgroup").read_text()
    except OSError:
        return False


def check_environment(rep: Report, env: dict | None = None):
    """A container backend causes the container boundary to be treated as the
    security boundary, so command approval is skipped inside it. That protects
    the machine and does nothing to stop an unreviewed application reaching an
    employer — and until now, nothing said so."""
    if detect_container(env):
        rep.add("N01", "container backend detected: command-approval layer inactive")
        return "container"
    return "host"


# ── run ─────────────────────────────────────────────────────────────────────

def run(root: Path, db: Path, policy: Path, state: Path, env: dict):
    rep = Report()
    try:
        import yaml
        manifest = yaml.safe_load((root / "manifest.yaml").read_text())
    except Exception:
        manifest = {"core": {"skills": []}, "addons": []}

    missing = check_completeness(root, manifest, rep)
    caps = check_capabilities(root, manifest, rep)
    drift = check_migrations(db, rep) if not missing else []
    cap = check_cap(root, rep)
    paired = check_pairing(env, rep)
    check_policy(policy, root, state, rep)
    where = check_environment(rep, env)

    return rep, {
        "missing": missing, "unavailable_capabilities": caps,
        "schema_drift": drift, "daily_cap": cap,
        "approval_restricted": paired, "environment": where,
    }


def render(rep: Report, facts: dict) -> str:
    sev = rep.severity()
    out = []
    if sev == BLOCK:
        out.append("I cannot start this session safely.\n")
    elif sev == DEGRADE:
        out.append("Everything is running, with a couple of things worth knowing.\n")
    else:
        out.append("Everything checks out.\n")

    seen = set()
    for code, _detail in rep.findings:
        if code in seen:
            continue
        seen.add(code)
        out.append("  " + MESSAGES[code][1] + f"  [{code}]")

    if sev != BLOCK:
        cap = facts.get("daily_cap")
        if cap:
            out.append(f"\n  Up to {cap} applications will be prepared for you a day. "
                       "None of them send without your approval.")
    if sev == BLOCK:
        out.append("\n  Quote the code above if you contact support — the details "
                   "are in your local log.")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--db", default=None)
    ap.add_argument("--policy", default=None)
    ap.add_argument("--state", default=None)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    root = Path(a.root).resolve()
    db = Path(a.db) if a.db else root / "shared" / "applications.db"
    policy = Path(a.policy) if a.policy else Path.home() / ".hermes" / "job-hunting-policy.yaml"
    state = Path(a.state) if a.state else Path.home() / ".hermes" / ".session-policy-digest"

    rep, facts = run(root, db, policy, state, os.environ)

    if a.json:
        print(json.dumps({
            "severity": rep.severity() or "ok",
            "findings": [{"code": c, "detail": d} for c, d in rep.findings],
            "facts": facts,
        }, indent=2))
    else:
        print(render(rep, facts))
    sys.exit(rep.exit_code())


if __name__ == "__main__":
    main()
