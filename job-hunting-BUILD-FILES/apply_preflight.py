#!/usr/bin/env python3
"""
apply_preflight.py — apply the preflight fixes to your actual working tree.

    python3 apply_preflight.py --root . --dry-run
    python3 apply_preflight.py --root . --apply

Fixes 1, 2 and 4 are mechanical and applied here. Fixes 3, 5 and 6 need
judgement about your own prose, so this reports exactly what to change and
where, and changes nothing.

Every edit is backed up to <file>.pre21.bak before it is touched, and --dry-run
shows the whole plan without writing anything.
"""
from __future__ import annotations
import argparse, json, re, shutil, sys
from pathlib import Path

CHANGES, REPORTS, SKIPPED = [], [], []


def note(kind, msg):
    (CHANGES if kind == "change" else REPORTS if kind == "report" else SKIPPED).append(msg)


# ── fix 1 — profile_stage in target-profile.yaml ────────────────────────────

PROFILE_STAGE_BLOCK = '''# Asked first at onboarding — it routes the whole first session and pre-sets
# the match thresholds in dynamic-target-calibration.yaml. Confirmed the same
# way as every other field here; never hand-edited.
#   experienced - prior paid work history to draw on
#   first_time  - entering the workforce, or switching with no prior history
#                 in the target field. Pre-sets minimum 55 / stretch floor 35.
profile_stage: ""

'''


def fix_profile_stage(root: Path, apply: bool):
    for name in ("target-profile.yaml.template", "target-profile_yaml.template",
                 "target-profile.yaml"):
        p = root / "shared" / name
        if p.is_file():
            break
    else:
        note("skip", "fix 1: shared/target-profile.yaml.template not found")
        return
    text = p.read_text(encoding="utf-8", errors="replace")
    if re.search(r"^\s*profile_stage\s*:", text, re.M):
        note("skip", "fix 1: profile_stage already present")
        return
    m = re.search(r"^seniority_band\s*:", text, re.M)
    if not m:
        note("report", f"fix 1: no seniority_band anchor in {p.name} — "
                       f"add the profile_stage block by hand at the top")
        return
    new = text[:m.start()] + PROFILE_STAGE_BLOCK + text[m.start():]
    note("change", f"fix 1: insert profile_stage above seniority_band in {p.name}")
    if apply:
        shutil.copy2(p, p.with_suffix(p.suffix + ".pre21.bak"))
        p.write_text(new, encoding="utf-8")


# ── fix 2 — addendum_21 ─────────────────────────────────────────────────────

def fix_addendum_21(root: Path, apply: bool, source: Path):
    dst = root / "shared" / "applications_db_schema_addendum_21.sql"
    if dst.exists():
        note("skip", "fix 2: addendum_21 already present")
        return
    if not source.is_file():
        note("report", f"fix 2: {source} not found next to this script")
        return
    note("change", "fix 2: add shared/applications_db_schema_addendum_21.sql "
                   "(migration verification + applications.profile_stage)")
    if apply:
        shutil.copy2(source, dst)


# ── fix 4 — social_listening in the sources enum ────────────────────────────

def fix_social_listening(root: Path, apply: bool):
    for name in ("sources.yaml.template", "sources_yaml.template", "sources.yaml"):
        p = root / "shared" / name
        if p.is_file():
            break
    else:
        note("skip", "fix 4: shared/sources.yaml.template not found")
        return
    text = p.read_text(encoding="utf-8", errors="replace")
    if "social_listening" in text:
        note("skip", "fix 4: social_listening already in the enum")
        return
    m = re.search(r"^(\s*type:\s*\S+\s*#.*open_web_search)(.*)$", text, re.M)
    if not m:
        note("report", "fix 4: could not find the type enum comment — add "
                       "`social_listening` to it by hand")
        return
    add = (" |\n"
           "                            # social_listening (requires "
           "capability:social_listening\n"
           "                            # — skipped with a notice when unavailable)")
    new = text[:m.end(1)] + add + text[m.end(1):]
    note("change", "fix 4: add social_listening to the sources type enum")
    if apply:
        shutil.copy2(p, p.with_suffix(p.suffix + ".pre21.bak"))
        p.write_text(new, encoding="utf-8")


# ── fix 3 — the 19 capability conversions (report only) ─────────────────────

SKILL_CAP = {
    "13-interview-prep": "interview_prep",
    "14-social-discovery-outreach": "social_listening",
    "17-cold-prospecting": "cold_outreach",
    "22-contact-enrichment": "contact_enrichment",
    "19-career-path-planner": "career_planning",
    "20-interests-profile": "interests_profile",
}
CORE = {"00-orchestrator", "01-job-discovery", "02-jd-parser", "03-resume-match",
        "04-keyword-analysis", "05-resume-customizer", "06-cover-letter",
        "07-context-architect", "08-application-qa", "09-risk-tactics-gate",
        "10-approval-and-submit", "11-analytics-and-learning", "12-company-research",
        "16-career-pulse", "18-skill-composer", "21-output-templates", "onboarding"}


def _skill_names(root: Path) -> dict:
    """frontmatter `name:` -> directory id, so related_skills can be resolved."""
    out = {}
    for d in sorted(root.iterdir()):
        f = d / "SKILL.md" if d.is_dir() else None
        if not f or not f.is_file():
            continue
        m = re.search(r"^name:\s*(\S+)", f.read_text(encoding="utf-8",
                                                      errors="replace"), re.M)
        if m:
            out[m.group(1)] = d.name
    return out


def report_capability_refs(root: Path):
    hits = []
    names = _skill_names(root)          # frontmatter uses names, prose uses ids
    addon_names = {n: d for n, d in names.items() if d in SKILL_CAP}
    for skill in sorted(CORE):
        f = root / skill / "SKILL.md"
        if not f.is_file():
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        lines = text.split("\n")
        in_fm, fm_end = text.startswith("---"), 0
        if in_fm:
            fm_end = text.index("\n---", 3)
        for i, ln in enumerate(lines):
            pos = sum(len(x) + 1 for x in lines[:i])
            fmline = in_fm and pos < fm_end
            for addon, cap in SKILL_CAP.items():
                if addon in ln:
                    hits.append((skill, addon, cap, i + 1,
                                 "frontmatter" if fmline else "prose", ln.strip()[:70]))
            if fmline:
                for nm, d in addon_names.items():
                    if re.search(r"(?<![\w-])" + re.escape(nm) + r"(?![\w-])", ln):
                        hits.append((skill, d, SKILL_CAP[d], i + 1,
                                     "frontmatter", ln.strip()[:70]))
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    root = Path(a.root).expanduser().resolve()
    if not root.is_dir():
        print(f"not a directory: {root}")
        sys.exit(2)
    if not (root / "shared").is_dir():
        print(f"no shared/ under {root} — is this the package root?")
        sys.exit(2)

    apply = bool(a.apply)
    here = Path(__file__).resolve().parent

    fix_profile_stage(root, apply)
    fix_addendum_21(root, apply, here / "addendum_21.sql")
    fix_social_listening(root, apply)

    print(f"root: {root}")
    print(f"mode: {'APPLY' if apply else 'dry run — nothing written'}\n")

    print(f"MECHANICAL FIXES  ({len(CHANGES)} to make, {len(SKIPPED)} skipped)")
    for c in CHANGES:
        print("  + " + c)
    for s in SKIPPED:
        print("  . " + s)
    for r in REPORTS:
        print("  ! " + r)

    hits = report_capability_refs(root)
    pairs = {(h[0], h[1]) for h in hits}
    print(f"\nFIX 3 — CAPABILITY CONVERSIONS")
    print(f"  {len(hits)} line occurrences across {len(pairs)} skill relationships, by hand")
    print("  Core must name a capability, never an addon skill. Replace each")
    print("  reference below with `capability:<name>` and give it a defined")
    print("  path for when the capability is absent.\n")
    fm = [h for h in hits if h[4] == "frontmatter"]
    print(f"  {len(fm)} in frontmatter — these matter most, addon compatibility")
    print(f"  is computed from exactly that metadata.\n")
    for skill, addon, cap, ln, where, txt in hits:
        print(f"  {skill:<24} L{ln:<5} {where:<12} -> capability:{cap}")

    print("\nFIX 5 — daily_staging_cap")
    found = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix in (".md", ".py", ".yaml", ".template"):
            try:
                if "daily_staging_cap" in p.read_text(encoding="utf-8", errors="replace"):
                    found.append(p.relative_to(root))
            except OSError:
                pass
    print(f"  named in {len(found)} file(s): {', '.join(map(str, found)) or 'none'}")
    if len(found) <= 1:
        print("  Only its own config file names it. Trace how the orchestrator")
        print("  actually enforces the cap before any sending gate ships as")
        print("  toggleable — this cap is the last thing between a bug in")
        print("  auto-approve mode and a day of unreviewed applications.")

    print("\nFIX 6 — container backend notice")
    ic = root / "00-orchestrator" / "scripts" / "install-check.py"
    print(f"  replace {ic.relative_to(root) if ic.exists() else '00-orchestrator/scripts/install-check.py'}")
    print("  with the tested install-check.py from this bundle (13 cases pass).")

    if not apply:
        print("\nNothing was written. Re-run with --apply to make the mechanical")
        print("changes; each edited file is backed up to <file>.pre21.bak first.")


if __name__ == "__main__":
    main()
