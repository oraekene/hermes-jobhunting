#!/usr/bin/env python3
"""
msg.py — the one place a user-visible string is allowed to come from.

    msg.py get KEY [--var name=value ...]     render one message
    msg.py check                              every message is clean
    msg.py scan PKG                           find unkeyed strings in skill files
    msg.py keys [--prefix P]                  what exists

WHY A CATALOG AND NOT JUST CAREFUL WRITING.
Three things fall out of having one file, and none of them fall out of being
careful in 137 places:

  1. Obscuring becomes enforceable. `check` fails the build if any internal name
     reaches a user-visible string. Careful writing has no failure mode; it just
     drifts.
  2. Translation is one pass over one file rather than a rewrite.
  3. Tone stays consistent. Thirty-eight gates and eight skills written by the
     same person over months still drift; a catalog does not.

WHAT IS NOT IN HERE.
Log lines, error detail for support, and anything the user never sees. Those
stay specific and keep their file paths and gate ids — that is the whole point
of splitting the two audiences.
"""
from __future__ import annotations
import argparse, re, sys
from pathlib import Path

import yaml

CATALOG = Path(__file__).resolve().parent.parent / "messages.yaml"

# Anything that would tell a user how the machine is built. Same detector the
# documentation build uses, so the two cannot disagree.
LEAK = re.compile(
    r"(\b\d{2}-[a-z][a-z0-9-]{3,}\b"           # 05-resume-customizer
    r"|\bGATE-[A-Z-]+\b|\bFLOW-[A-Z]\d+\b|\bPACK-[A-Z]+\b"
    r"|\b[a-z][a-z0-9_-]*\.(yaml|md|sql|py|db|template)\b"
    r"|\bRule \d+\b|\bapplications\.db\b"
    r"|\bskill_manage\b|\bwrite_approval\b|\bschema_version\b"
    r"|\bfidelity_mode\b|\bdaily_staging_cap\b|\bprofile_stage\b"
    r"|\bGATEWAY_[A-Z_]+\b|\bshared/|\bsecurity/)")

VAR = re.compile(r"\{(\w+)\}")


def load():
    doc = yaml.safe_load(CATALOG.read_text(encoding="utf-8"))
    flat = {}
    for group, entries in (doc.get("messages") or {}).items():
        for k, v in entries.items():
            flat[f"{group}.{k}"] = v
    return doc, flat


def render(key, variables=None):
    _, flat = load()
    entry = flat.get(key)
    if entry is None:
        # Fail loudly in development, gracefully in front of a user: a missing
        # key must never print a key name to someone who did not ask for one.
        return "Something went wrong on my side. Nothing was sent or changed."
    text = entry["text"] if isinstance(entry, dict) else entry
    for name in VAR.findall(text):
        text = text.replace("{" + name + "}", str((variables or {}).get(name, "")))
    return text.strip()


# ── checks ──────────────────────────────────────────────────────────────────

def check():
    doc, flat = load()
    fails, warns = [], []

    for key, entry in flat.items():
        text = entry["text"] if isinstance(entry, dict) else entry
        for m in LEAK.finditer(text):
            fails.append(f"{key}: internal name in user-visible text — {m.group(0)!r}")
        if isinstance(entry, dict):
            declared = set(entry.get("vars") or [])
            used = set(VAR.findall(text))
            for extra in used - declared:
                fails.append(f"{key}: uses {{{extra}}} but does not declare it")
            for unused in declared - used:
                warns.append(f"{key}: declares {unused} but never uses it")
        # A message a user reads should not be a paragraph.
        if len(text.split()) > 90:
            warns.append(f"{key}: {len(text.split())} words — probably too long to read")
        if re.search(r"\b(error|exception|failed|invalid|null|undefined)\b", text, re.I) \
                and not key.startswith("problem."):
            warns.append(f"{key}: reads like a stack trace, not a sentence")

    # Safety messages must say what happened, not merely that something did.
    for key in flat:
        if key.startswith("blocked."):
            text = render(key)
            if len(text.split()) < 8:
                fails.append(f"{key}: a refusal must explain itself")
    return fails, warns


# ── scanner ─────────────────────────────────────────────────────────────────

# Lines in a skill file that look like something the model is told to SAY.
SAY = re.compile(
    r'(?:^|\s)(?:say|tell (?:them|the user|Kene)|reply|respond|message|'
    r'report back|answer)\b[^.\n]{0,40}[:"“]', re.I)
QUOTED = re.compile(r'^\s*>\s*(.+)$')          # block quotes are usually samples


def scan(pkg: Path):
    """Find user-facing strings written inline in skill files.

    Reports only. Guessing which quoted line is an emitted message and which is
    an example would eventually rewrite an instruction, and that failure is
    silent — a skill that still reads convincingly and does something else.
    """
    hits = []
    for p in sorted(pkg.rglob("SKILL.md")):
        if "_merge-history" in p.parts:
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="replace").split("\n"), 1):
            q = QUOTED.match(line)
            if q and len(q.group(1).split()) >= 6:
                hits.append((p, i, "sample reply", q.group(1)[:60]))
            elif SAY.search(line):
                hits.append((p, i, "instruction to speak", line.strip()[:60]))
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["get", "check", "scan", "keys"])
    ap.add_argument("arg", nargs="?")
    ap.add_argument("--var", action="append", default=[])
    ap.add_argument("--prefix", default="")
    a = ap.parse_args()

    if a.cmd == "get":
        print(render(a.arg, dict(v.split("=", 1) for v in a.var)))
        return

    if a.cmd == "keys":
        _, flat = load()
        for k in sorted(flat):
            if k.startswith(a.prefix):
                print(f"  {k}")
        return

    if a.cmd == "check":
        fails, warns = check()
        _, flat = load()
        print(f"{len(flat)} messages checked")
        for w in warns:
            print("WARN  " + w)
        for f in fails:
            print("FAIL  " + f)
        if fails:
            sys.exit(1)
        print("no internal names in user-visible text")
        return

    if a.cmd == "scan":
        hits = scan(Path(a.arg))
        by_file = {}
        for p, i, kind, txt in hits:
            by_file.setdefault(p, []).append((i, kind, txt))
        print(f"{len(hits)} candidate strings across {len(by_file)} skill files\n")
        for p, rows in sorted(by_file.items(), key=lambda r: -len(r[1]))[:15]:
            print(f"  {len(rows):>3}  {p.parent.name}/{p.name}")
        print("\nThese are candidates, not findings. Move the ones that are")
        print("actually emitted into the catalog and reference them by key.")
        print("Nothing was changed.")


if __name__ == "__main__":
    main()
