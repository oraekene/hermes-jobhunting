#!/usr/bin/env python3
"""test_msg.py — the catalog must stay clean and must stay honest."""
import importlib.util, sys
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "msg", Path(__file__).resolve().parent / "msg.py")
msg = importlib.util.module_from_spec(spec); spec.loader.exec_module(msg)

CASES, FAILED = [], []
def check(n, c, extra=""):
    CASES.append((n, bool(c), extra))
    if not c: FAILED.append(n)

doc, flat = msg.load()
fails, warns = msg.check()

check("catalog is clean", not fails, "; ".join(fails[:2]))
check("catalog is not trivially small", len(flat) >= 35)

# the detector must actually fire, or "clean" means nothing
for bad in ["Blocked by Rule 1", "see gates.yaml", "GATE-SEND-DM refused",
            "05-resume-customizer failed", "set fidelity_mode",
            "GATEWAY_ALLOW_ALL_USERS", "shared/pipeline-rules.md"]:
    check(f"detector catches {bad!r}", msg.LEAK.search(bad))
check("detector spares ordinary prose",
      not msg.LEAK.search("I stopped before sending this application."))

# every refusal has to explain itself
for k in [k for k in flat if k.startswith("blocked.")]:
    check(f"{k} explains itself", len(msg.render(k).split()) >= 8)

# variables resolve, and an unknown one does not print braces at a user
out = msg.render("permissions.armed",
                 {"label": "sending", "days": 30, "until": "2026-09-03"})
check("variables substitute", "{label}" not in out and "sending" in out)
out = msg.render("permissions.armed", {})
check("missing variable leaves no braces", "{" not in out)

# a missing key must never show a key name to someone who did not ask for one
check("unknown key degrades gracefully",
      "nope" not in msg.render("nope.nothing") and
      len(msg.render("nope.nothing").split()) >= 6)

# the tone rules the catalog sets for itself
check("no message says 'error' to a user",
      not any("error" in msg.render(k).lower() for k in flat
              if not k.startswith("problem.")))
check("problem messages carry a quotable code",
      all("{code}" in (flat[k]["text"] if isinstance(flat[k], dict) else flat[k])
          or "container" in k or "changed" in k
          for k in flat if k.startswith("problem.")))

w = max(len(n) for n, _, _ in CASES)
for n, ok, extra in CASES:
    print(f"  {n:<{w}}  {'ok  ' if ok else 'FAIL'}{'  ' + extra if extra else ''}")
print()
for x in warns: print("WARN  " + x)
if FAILED:
    print(f"\n{len(FAILED)} failed: {FAILED}"); sys.exit(1)
print(f"{len(CASES)} checks pass")
