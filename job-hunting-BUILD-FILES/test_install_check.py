#!/usr/bin/env python3
"""
test_install_check.py — exercise every path in install-check.py.

Builds synthetic installs on a temp filesystem: healthy, partial, drifted,
unpaired, tampered, unlicensed, containerised. Asserts the right code fires and
— just as important — that no internal name reaches the user-facing text.

    python3 test_install_check.py
"""
import importlib.util, re, shutil, sqlite3, sys, tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location("ic", Path(__file__).parent / "install-check.py")
ic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ic)

# same detector build_docs.py uses — user-facing text must not leak internals
LEAK = re.compile(
    r"(\b\d{2}-[a-z][a-z0-9-]{3,}\b|\bGATE-[A-Z-]+\b|\bFLOW-[A-Z]\d+\b"
    r"|\b[a-z][a-z0-9_-]*\.(yaml|md|sql|py|db)\b|\bRule \d+\b"
    r"|\bschema_version\b|\bschema_expected\b|\bdaily_staging_cap\b"
    r"|\bGATEWAY_[A-Z_]+\b)")

CORE = ["00-orchestrator", "07-context-architect", "10-approval-and-submit"]
MANIFEST = """
core:
  skills:
""" + "".join(f"    - {{id: {s}}}\n" for s in CORE) + """
addons:
  - id: addon-outreach
    skills: [14-social-discovery-outreach]
    provides_capabilities: [social_listening, cold_outreach]
"""
TIER = """
active_tier: starter
tiers:
  starter:
    daily_staging_cap: 15
"""


def build(tmp: Path, *, complete=True, cap=True, addon=False,
          db=True, expected=True, drift=False) -> Path:
    root = tmp / "pkg"
    if root.exists():
        shutil.rmtree(root)
    for d in ["shared", "security", "cron", "templates"]:
        (root / d).mkdir(parents=True)
    for f in ["pipeline-rules.md", "site-access-model.md", "applications_db_schema.sql"]:
        (root / "shared" / f).write_text("x")
    if cap:
        (root / "shared" / "tier-config.yaml").write_text(TIER)
    (root / "manifest.yaml").write_text(MANIFEST)
    skills = CORE if complete else CORE[:1]
    if addon:
        skills = skills + ["14-social-discovery-outreach"]
    for s in skills:
        (root / s).mkdir(parents=True, exist_ok=True)
        (root / s / "SKILL.md").write_text("x")
    if db:
        con = sqlite3.connect(root / "shared" / "applications.db")
        con.executescript("""
          CREATE TABLE schema_version (filename TEXT PRIMARY KEY, note TEXT);
          CREATE TABLE applications (id INTEGER PRIMARY KEY, profile_stage TEXT);
          INSERT INTO schema_version VALUES ('applications_db_schema.sql','base');
        """)
        if expected:
            con.executescript("""
              CREATE TABLE schema_expected (migration TEXT, object TEXT, kind TEXT,
                                            PRIMARY KEY (migration, object));
              CREATE TABLE schema_drift (checked_at TEXT DEFAULT (datetime('now')),
                                         migration TEXT, object TEXT, kind TEXT,
                                         present INTEGER,
                                         PRIMARY KEY (migration, object));
              INSERT INTO schema_expected VALUES
                ('applications_db_schema.sql','applications','table'),
                ('applications_db_schema.sql','applications.profile_stage','column');
            """)
            if drift:
                con.executescript("""
                  INSERT INTO schema_version VALUES ('applications_db_schema_addendum_4.sql','x');
                  INSERT INTO schema_expected VALUES
                    ('applications_db_schema_addendum_4.sql','career_path_plans','table');
                """)
        con.commit(); con.close()
    return root


PAIRED = {"GATEWAY_PAIRED_USER": "u1"}
CASES, FAILED = [], []


def case(name, *, env=PAIRED, policy=None, state=None, expect_codes=(),
         expect_exit=0, container=False, **kw):
    tmp = Path(tempfile.mkdtemp())
    root = build(tmp, **kw)
    pol = Path(policy) if policy else tmp / "outside" / "policy.yaml"
    st = Path(state) if state else tmp / "state" / "digest"
    e = dict(env)
    if container:
        e["HERMES_TERMINAL_BACKEND"] = "container"
    rep, facts = ic.run(root, root / "shared" / "applications.db", pol, st, e)
    text = ic.render(rep, facts)
    codes = {c for c, _ in rep.findings}
    ok = True
    for want in expect_codes:
        if want not in codes:
            FAILED.append(f"{name}: expected {want}, got {sorted(codes) or 'none'}")
            ok = False
    if rep.exit_code() != expect_exit:
        FAILED.append(f"{name}: exit {rep.exit_code()}, expected {expect_exit}")
        ok = False
    leaks = [m.group(0) for m in LEAK.finditer(text)]
    if leaks:
        FAILED.append(f"{name}: internal names in user text: {sorted(set(leaks))}")
        ok = False
    CASES.append((name, sorted(codes), rep.exit_code(), "ok" if ok else "FAIL"))
    shutil.rmtree(tmp, ignore_errors=True)
    return text


def main():
    case("healthy", addon=True, expect_exit=0)
    case("partial install", complete=False, expect_codes=["E01"], expect_exit=2)
    case("no database", db=False, expect_codes=["E02"], expect_exit=2)
    case("pre-21 database", expected=False, expect_codes=["W01"], expect_exit=1)
    case("recorded but missing", drift=True, expect_codes=["W01"], expect_exit=1)
    case("no cap", cap=False, expect_codes=["E05"], expect_exit=2)
    case("unpaired", env={}, expect_codes=["E03"], expect_exit=2)
    case("allow-all enabled", env={"GATEWAY_ALLOW_ALL_USERS": "true"},
         expect_codes=["E03"], expect_exit=2)
    case("addon absent", expect_codes=["W02"], expect_exit=1)
    case("addon present", addon=True, expect_exit=0)
    case("container", addon=True, container=True,
         expect_codes=["N01"], expect_exit=0)

    # policy tampering needs two runs sharing one state file
    tmp = Path(tempfile.mkdtemp())
    root = build(tmp)
    pol = tmp / "outside" / "policy.yaml"
    pol.parent.mkdir(parents=True)
    pol.write_text("auto_approve: false\n")
    st = tmp / "state" / "digest"
    ic.run(root, root / "shared" / "applications.db", pol, st, PAIRED)   # session start
    pol.write_text("auto_approve: true\n")                              # injected change
    rep, facts = ic.run(root, root / "shared" / "applications.db", pol, st, PAIRED)
    codes = {c for c, _ in rep.findings}
    ok = "E04" in codes and rep.exit_code() == 2
    if not ok:
        FAILED.append(f"policy tampering: expected E04/exit 2, got {sorted(codes)}")
    CASES.append(("policy tampering", sorted(codes), rep.exit_code(),
                  "ok" if ok else "FAIL"))

    # policy inside the working directory
    root2 = build(tmp)
    inside = root2 / "shared" / "policy.yaml"
    inside.write_text("x")
    rep2, f2 = ic.run(root2, root2 / "shared" / "applications.db", inside,
                      tmp / "s2", PAIRED)
    codes2 = {c for c, _ in rep2.findings}
    ok2 = "W03" in codes2
    if not ok2:
        FAILED.append(f"policy inside root: expected W03, got {sorted(codes2)}")
    CASES.append(("policy inside working dir", sorted(codes2), rep2.exit_code(),
                  "ok" if ok2 else "FAIL"))
    shutil.rmtree(tmp, ignore_errors=True)

    print(f"{'case':<28}{'codes':<26}{'exit':>5}  result")
    for n, c, x, r in CASES:
        print(f"{n:<28}{','.join(c) or '-':<26}{x:>5}  {r}")
    print()
    if FAILED:
        for f in FAILED:
            print("FAIL  " + f)
        sys.exit(1)
    print(f"{len(CASES)} cases pass, no internal names in user-facing text")


if __name__ == "__main__":
    main()
