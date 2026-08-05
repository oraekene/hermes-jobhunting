#!/usr/bin/env python3
"""
check_gates.py — invariant checker for gates.yaml.

Run this on every change to the registry and in CI. The registry is the source
of truth for the permission UI, the info panel and the docs; a violation here
means one of those three surfaces is about to lie to a user.

    python3 check_gates.py gates.yaml
"""
import sys, yaml, collections

FAIL = []
WARN = []

def fail(m): FAIL.append(m)
def warn(m): WARN.append(m)

def main(path="gates.yaml"):
    d = yaml.safe_load(open(path))
    gates, meta = d["gates"], d["meta"]
    packs = {p["id"] for p in d["packs"]}
    ids = [g["id"] for g in gates]

    # --- identity -----------------------------------------------------------
    dupes = [k for k, v in collections.Counter(ids).items() if v > 1]
    if dupes:
        fail(f"duplicate gate ids: {dupes}")
    if meta["gate_count"] != len(gates):
        fail(f"meta.gate_count={meta['gate_count']} but {len(gates)} gates defined")
    for g in gates:
        if not g["id"].startswith("GATE-"):
            fail(f"{g['id']}: id must start with GATE-")

    # --- class rules --------------------------------------------------------
    CLASSES = {"irreversible_external", "reversible_external",
               "reversible_internal", "structural"}
    for g in gates:
        gid, cls = g["id"], g["class"]
        if cls not in CLASSES:
            fail(f"{gid}: unknown class {cls!r}")

        # An irreversible action must never be switchable off casually.
        if cls == "irreversible_external" and g.get("toggleable"):
            if not g.get("arm_required"):
                fail(f"{gid}: irreversible + toggleable requires arm_required: true")
            if not g.get("expires_days"):
                fail(f"{gid}: irreversible + toggleable requires an expiry")

        # Structural gates are not permissions and must not appear as toggles.
        if cls == "structural" and g.get("toggleable"):
            fail(f"{gid}: structural gates are never toggleable")

        # Every non-structural gate renders an info panel with both sides.
        if cls != "structural":
            p = g.get("panel") or {}
            if not p.get("when_on"):
                fail(f"{gid}: missing panel.when_on")
            if not p.get("when_off"):
                fail(f"{gid}: missing panel.when_off")
            elif g.get("values"):
                pass  # multi-value setting, not a boolean toggle
            elif g.get("toggleable") is False and "not available" not in str(p["when_off"]).lower():
                warn(f"{gid}: not toggleable but panel.when_off describes an off state")
            elif g.get("toggleable") and "not available" in str(p["when_off"]).lower():
                fail(f"{gid}: toggleable but panel.when_off says it cannot be switched off")

        # Pack membership must resolve.
        if g.get("pack") and g["pack"] not in packs:
            fail(f"{gid}: unknown pack {g['pack']}")

        # Owner must be recorded so the docs can link to it.
        if not g.get("owner"):
            fail(f"{gid}: missing owner file")

    # --- non-negotiables ----------------------------------------------------
    for gid in meta["policy"]["non_negotiable"]:
        g = next((x for x in gates if x["id"] == gid), None)
        if g is None:
            fail(f"policy names {gid} but no such gate exists")
        elif g.get("toggleable"):
            fail(f"{gid}: listed non-negotiable but marked toggleable")

    # --- volume cap ---------------------------------------------------------
    # If a sending gate can be switched off, the daily cap is the only thing
    # between a bug and a day's worth of unreviewed output.
    for g in gates:
        if g["class"] == "irreversible_external" and g.get("toggleable"):
            if g.get("cap_applies") is False and g["pack"] == "PACK-SENDING":
                fail(f"{g['id']}: sending gate is toggleable but cap_applies is false")

    # --- report -------------------------------------------------------------
    print(f"{len(gates)} gates checked")
    by = collections.Counter(g["class"] for g in gates)
    for k, v in by.items():
        print(f"  {k:<24} {v}")
    print(f"  toggleable               {sum(1 for g in gates if g.get('toggleable'))}")
    for w in WARN:
        print("WARN  " + w)
    for f in FAIL:
        print("FAIL  " + f)
    if FAIL:
        sys.exit(1)
    print("\nall invariants hold")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "gates.yaml")
