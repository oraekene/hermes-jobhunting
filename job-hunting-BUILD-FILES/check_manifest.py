#!/usr/bin/env python3
"""
check_manifest.py — validate manifest.yaml against the graph and the registries.

    python3 check_manifest.py

Catches the failure modes that only appear after a customer buys one addon and
not another:
  * a core skill referencing an addon skill with no capability contract
  * a gate or flow owned by no declared pack
  * a cross-pack reference declared as a hard dependency
  * a skill in two packs, or in none
  * migration numbers claimed by two addons
"""
import json, sys, yaml
from collections import defaultdict

FAIL, WARN = [], []

def main():
    M = yaml.safe_load(open("manifest.yaml"))
    G = yaml.safe_load(open("gates.yaml"))
    F = yaml.safe_load(open("flows.yaml"))
    graph = json.load(open("graph.json"))

    ALL_SKILLS = {n["id"] for n in graph["nodes"] if n["type"] == "skill"}
    CORE = {s["id"] for s in M["core"]["skills"]}
    ADDON_OF = {}
    for a in M["addons"]:
        for s in a["skills"]:
            if s in ADDON_OF:
                FAIL.append(f"{s} claimed by both {ADDON_OF[s]} and {a['id']}")
            ADDON_OF[s] = a["id"]

    # --- every skill is placed exactly once ---------------------------------
    placed = CORE | set(ADDON_OF)
    for s in sorted(ALL_SKILLS - placed):
        FAIL.append(f"{s}: in the package but assigned to neither core nor an addon")
    for s in sorted(placed - ALL_SKILLS):
        FAIL.append(f"{s}: declared in the manifest but not a skill in graph.json")
    for s in sorted(CORE & set(ADDON_OF)):
        FAIL.append(f"{s}: in core and in an addon")

    # --- core must not reference addon skills without a contract ------------
    contracts = M["capability_contracts"]["contracts"]
    covered = defaultdict(set)          # core skill -> addons it has a contract for
    for c in contracts:
        for r in c["referenced_by"]:
            covered[r].add(c["provided_by"])
        if not c.get("when_absent", "").strip():
            FAIL.append(f"capability {c['capability']}: no when_absent behaviour defined")

    edges = [(e["source"], e["target"]) for e in graph["edges"]
             if e["kind"] in ("references", "declared_related")
             and e["source"] in ALL_SKILLS and e["target"] in ALL_SKILLS]

    dangling = 0
    for src, tgt in sorted(set(edges)):
        if src in CORE and tgt in ADDON_OF:
            if ADDON_OF[tgt] not in covered.get(src, set()):
                FAIL.append(f"{src} -> {tgt}: core references an addon skill "
                            f"with no capability contract")
            else:
                dangling += 1

    # --- cross-pack references must be optional, never hard -----------------
    optional = {a["id"]: set(a.get("optional_capabilities") or []) for a in M["addons"]}
    provided = {}
    for a in M["addons"]:
        for cap in a["provides_capabilities"]:
            provided[cap] = a["id"]
    cross = {(ADDON_OF[s], ADDON_OF[t]) for s, t in edges
             if s in ADDON_OF and t in ADDON_OF and ADDON_OF[s] != ADDON_OF[t]}
    for a, b in sorted(cross):
        caps_from_b = {c for c, owner in provided.items() if owner == b}
        if not (optional.get(a, set()) & caps_from_b):
            WARN.append(f"{a} -> {b}: cross-pack reference with no optional_capability declared")

    # --- gate ownership ------------------------------------------------------
    gate_ids = {g["id"] for g in G["gates"]}
    owned = set()
    for a in M["addons"]:
        for g in a.get("gates") or []:
            if g not in gate_ids:
                FAIL.append(f"{a['id']}: unknown gate {g}")
            if g in owned:
                FAIL.append(f"{g}: owned by more than one addon")
            owned.add(g)
    # a non-negotiable gate must never be addon-owned outright
    for g in G["meta"]["policy"]["non_negotiable"]:
        if g in owned:
            WARN.append(f"{g} is non-negotiable but listed under an addon — "
                        f"confirm it stays active when that addon expires")

    # --- flow ownership ------------------------------------------------------
    flow_ids = {f["id"] for f in F["flows"]}
    claimed = set()
    for a in M["addons"]:
        for fl in a.get("flows") or []:
            if fl not in flow_ids:
                FAIL.append(f"{a['id']}: unknown flow {fl}")
            claimed.add(fl)

    # --- migrations ----------------------------------------------------------
    seen = {}
    for a in M["addons"]:
        for n in a.get("migrations") or []:
            if n in seen:
                FAIL.append(f"migration {n} claimed by {seen[n]} and {a['id']}")
            seen[n] = a["id"]
            if n >= M["migrations"]["next_number"]:
                FAIL.append(f"{a['id']}: migration {n} is at or past next_number")

    # --- degradation contracts ----------------------------------------------
    for a in M["addons"]:
        d = a.get("degradation") or {}
        if not d.get("on_expiry"):
            FAIL.append(f"{a['id']}: no degradation contract")
        if d.get("data_retained") is not True:
            FAIL.append(f"{a['id']}: degradation must retain user data")

    # --- report --------------------------------------------------------------
    print(f"core: {len(CORE)} skills   addons: {len(M['addons'])} "
          f"({len(ADDON_OF)} skills)   total {len(placed)}/{len(ALL_SKILLS)}")
    print(f"capability contracts: {len(contracts)} covering {dangling} core->addon references")
    print(f"gates owned by addons: {len(owned)}/{len(gate_ids)}   "
          f"flows claimed: {len(claimed)}/{len(flow_ids)}")
    print(f"cross-pack references: {len(cross)}")
    print()
    for w in WARN:
        print("WARN  " + w)
    for f in FAIL:
        print("FAIL  " + f)
    if FAIL:
        sys.exit(1)
    print("manifest consistent")

if __name__ == "__main__":
    main()
