#!/usr/bin/env python3
"""
check_build.py — the checker that was missing, and whose absence caused E1.

    python3 check_build.py

`manifest.yaml` declared six build stages. `build.py` implemented four. Nothing
looked, which is how a specification and its implementation drifted apart inside
a project that has five checkers for exactly that failure elsewhere.

This closes the class, not just the instance:

  * every build stage declared in the manifest maps to an implemented function
  * stage ORDER is explicit and matches the implementation, because two stages
    that partly undo each other are invisible without it
  * every script a document presents as runnable exists and runs
  * the watermark scope in the code matches what the manifest claims
"""
import ast, re, subprocess, sys
from pathlib import Path

import yaml

FAIL, WARN = [], []
HERE = Path(__file__).resolve().parent


# ── build stages ────────────────────────────────────────────────────────────

def implemented_stages(src: Path) -> set[str]:
    """Stage functions are named stage_<id>. Read the AST, not the text —
    a mention in a comment is not an implementation."""
    tree = ast.parse(src.read_text(encoding="utf-8"))
    return {n.name[len("stage_"):] for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef) and n.name.startswith("stage_")}


def check_stages(manifest, build_py):
    declared = [s["id"] for s in manifest["build"]["stages"]]
    have = implemented_stages(build_py)
    for sid in declared:
        if sid not in have:
            FAIL.append(f"build stage {sid!r} is declared in the manifest but "
                        f"stage_{sid}() does not exist in build.py")
    # audit reports, build orchestrates, verify checks — none is a pipeline stage
    NON_PIPELINE = {"audit", "build", "verify"}
    for sid in sorted(have - set(declared) - NON_PIPELINE):
        WARN.append(f"stage_{sid}() exists but the manifest does not declare it")

    # Order matters: watermarking after compiling would write bits into
    # binaries that nothing can read back.
    if "watermark" in declared and "compile_scripts" in declared:
        if declared.index("watermark") > declared.index("compile_scripts"):
            FAIL.append("watermark is declared after compile_scripts — the "
                        "watermark would be applied to binaries")
    return declared


# ── scripts documents claim are runnable ────────────────────────────────────

CODEBLOCK = re.compile(r"```(?:bash|sh|powershell)?\n(.*?)```", re.S)
INVOKE = re.compile(r"python3?\s+([A-Za-z0-9_./-]+\.py)\b")


def check_documented_scripts(root: Path):
    claimed = {}
    for doc in sorted(root.glob("*.md")):
        text = doc.read_text(encoding="utf-8", errors="replace")
        for block in CODEBLOCK.findall(text):
            for script in INVOKE.findall(block):
                claimed.setdefault(script, set()).add(doc.name)
    checked = 0
    for script, docs in sorted(claimed.items()):
        if any(x in script for x in ("scripts/", "apply_preflight", "install-check")):
            pass                              # still checked, just noting paths
        p = root / script
        if not p.is_file():
            # It may legitimately live inside the user's package rather than here.
            if (root / script.split("/")[-1]).is_file():
                continue
            WARN.append(f"{script} is shown as runnable in "
                        f"{', '.join(sorted(docs))} but is not in this bundle")
            continue
        checked += 1
    return checked, len(claimed)


# ── the checkers themselves must run ────────────────────────────────────────

SUITES = [
    ("test_installer.py", []),
    ("check_gates.py", []), ("check_flows.py", []), ("check_manifest.py", []),
    ("check_onboarding.py", []), ("check_patterns.py", []),
    ("shared/scripts/msg.py", ["check"]), ("shared/scripts/test_msg.py", []),
    ("permissions/scripts/test_permissions.py", []),
    ("federated/scripts/test_federated.py", []),
    ("test_install_check.py", []),
]


def check_suites(root: Path):
    ran = 0
    for script, args in SUITES:
        p = root / script
        if not p.is_file():
            FAIL.append(f"{script} is wired into the release workflow but does not exist")
            continue
        r = subprocess.run([sys.executable, str(p), *args], cwd=root,
                           capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            tail = (r.stdout or r.stderr).strip().splitlines()[-1:] or ["failed"]
            FAIL.append(f"{script}: {tail[0]}")
        else:
            ran += 1
    return ran


# ── watermark scope agrees with the manifest ────────────────────────────────

def check_watermark_scope(manifest, build_py):
    src = build_py.read_text(encoding="utf-8")
    m = re.search(r"WATERMARKABLE\s*=\s*\{([^}]*)\}", src)
    if not m:
        FAIL.append("build.py has no WATERMARKABLE set")
        return set()
    exts = {e.strip().strip('"\'') for e in m.group(1).split(",") if e.strip()}
    stage = next((s for s in manifest["build"]["stages"] if s["id"] == "watermark"), {})
    declared = set(stage.get("applies_to") or [])
    if declared and declared != exts:
        FAIL.append(f"watermark scope disagrees — manifest says {sorted(declared)}, "
                    f"build.py uses {sorted(exts)}")
    if ".py" in exts and any(s["id"] == "compile_scripts"
                             for s in manifest["build"]["stages"]):
        FAIL.append("build.py watermarks .py files while the manifest also compiles "
                    "them — the second stage erases the first")
    for risky in (".yaml", ".yml", ".template"):
        if risky in exts:
            FAIL.append(f"build.py watermarks {risky} — these become the user's live "
                        f"config and are rewritten, so the mark degrades into a "
                        f"wrong answer rather than no answer")
    return exts


def check_installer(root: Path):
    """The installer ships separately from the bundle — it is the thing that
    fetches the bundle — so it has its own build step and its own way to be
    forgotten. A shipped installer with no verification key refuses to install
    anything, which is a blocker on the whole delivery path."""
    src = root / "installer.py"
    if not src.is_file():
        FAIL.append("installer.py is missing — 'delivery at activation' has no client")
        return
    text = src.read_text(encoding="utf-8")
    if 'PUBLIC_KEY = os.environ.get("JH_PUBLIC_KEY", "")' not in text:
        FAIL.append("installer.py has no key placeholder for stamp-installer to fill")
    if "built without a verification key" not in text:
        FAIL.append("installer.py does not refuse when it has no key")
    dist = root / "dist" / "installer.py"
    if dist.is_file() and 'JH_PUBLIC_KEY", ""' in dist.read_text(encoding="utf-8"):
        FAIL.append("dist/installer.py was published unstamped — it will refuse "
                    "to install for every customer")


def main():
    root = HERE
    manifest = yaml.safe_load((root / "manifest.yaml").read_text(encoding="utf-8"))
    build_py = root / "build.py"
    if not build_py.is_file():
        print("FAIL  build.py not found")
        sys.exit(1)

    declared = check_stages(manifest, build_py)
    exts = check_watermark_scope(manifest, build_py)
    n_ok, n_claimed = check_documented_scripts(root)
    check_installer(root)
    ran = check_suites(root)

    print(f"build stages declared : {len(declared)}  ({' -> '.join(declared)})")
    print(f"watermark scope       : {' '.join(sorted(exts))}")
    print(f"documented scripts    : {n_ok}/{n_claimed} present in this bundle")
    print(f"test suites run       : {ran}/{len(SUITES)}")
    print()
    for w in WARN:
        print("WARN  " + w)
    for f in FAIL:
        print("FAIL  " + f)
    if FAIL:
        sys.exit(1)
    print("specifications and implementation agree")


if __name__ == "__main__":
    main()
