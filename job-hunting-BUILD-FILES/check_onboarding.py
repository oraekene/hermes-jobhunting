#!/usr/bin/env python3
"""
check_onboarding.py — validate the setup sequence against the registries.

    python3 check_onboarding.py

Catches the two ways a setup sequence goes wrong and nobody notices:
  * a setting nobody is ever asked about, which then sits at its default
    forever while the user assumes they configured it
  * a setting asked before the thing that determines its meaning or default
"""
import sys, yaml
from collections import Counter

FAIL, WARN = [], []

# A setting may not be asked before the setting it depends on.
DEPENDS = {
    "match_score.minimum":            ["profile_stage"],
    "match_score.stretch.floor":      ["profile_stage", "match_score.minimum"],
    "exclude_domains":                ["discovery_mode"],
    "title_variants":                 ["seniority_band"],
    "fidelity_mode":                  [],   # asked after the story bank, not a setting dep
    "stepping_stone.max_hops":        ["profile_stage"],
    "stepping_stone.allow_comp_regression": ["profile_stage"],
}


def main():
    ob = yaml.safe_load(open("onboarding.yaml"))
    reg = yaml.safe_load(open("settings.yaml"))
    gates = {g["id"] for g in yaml.safe_load(open("gates.yaml"))["gates"]}
    flows = {f["id"] for f in yaml.safe_load(open("flows.yaml"))["flows"]}

    ALL = {s["key"]: s for s in reg["settings"]}
    SIMPLE = {k for k, v in ALL.items() if v["tier"] == "SIMPLE"}

    order, asked_in = [], {}
    for si, sess in enumerate(ob["sessions"]):
        for st in sess["steps"]:
            if "setting" in st:
                order.append(st["setting"])
                asked_in[st["setting"]] = (si, sess["id"])
            for g in ([st["gate"]] if "gate" in st else []):
                if g not in gates:
                    FAIL.append(f"{st['id']}: unknown gate {g}")
            if "flow" in st and st["flow"] not in flows:
                FAIL.append(f"{st['id']}: unknown flow {st['flow']}")
        if "flow" in sess and sess["flow"] not in flows:
            FAIL.append(f"{sess['id']}: unknown flow {sess['flow']}")

    # every setting asked exactly once
    dupes = [k for k, n in Counter(order).items() if n > 1]
    for d in dupes:
        FAIL.append(f"{d}: asked in more than one session")
    for k in sorted(set(ALL) - set(order)):
        FAIL.append(f"{k}: in the settings registry but never asked — it will sit "
                    f"at its default forever while the user assumes otherwise")
    for k in sorted(set(order) - set(ALL)):
        FAIL.append(f"{k}: asked but not in the settings registry")

    # SIMPLE settings must all land in session 1
    s1 = ob["sessions"][0]["id"]
    for k in sorted(SIMPLE):
        if k in asked_in and asked_in[k][1] != s1:
            FAIL.append(f"{k}: SIMPLE tier but asked in {asked_in[k][1]} — the "
                        f"pipeline cannot produce an application without it")

    # dependency ordering
    pos = {k: i for i, k in enumerate(order)}
    for k, deps in DEPENDS.items():
        if k not in pos:
            continue
        for d in deps:
            if d not in pos:
                FAIL.append(f"{k} depends on {d}, which is never asked")
            elif pos[d] > pos[k]:
                FAIL.append(f"{k} is asked before {d}, which determines its meaning")

    # session-1 length sanity
    s1_steps = len(ob["sessions"][0]["steps"])
    mins = ob["sessions"][0]["target_minutes"]
    if s1_steps > 15:
        WARN.append(f"session 1 has {s1_steps} steps for {mins} minutes — "
                    f"abandonment risk")

    # baseline questions
    if not ob.get("baseline", {}).get("questions"):
        FAIL.append("no baseline capture — before/after comparison becomes impossible")
    elif not ob["baseline"].get("skippable"):
        WARN.append("baseline questions are not skippable")

    print(f"{len(ob['sessions'])} sessions, {len(order)}/{len(ALL)} settings sequenced")
    for sess in ob["sessions"]:
        n = sum(1 for st in sess["steps"] if "setting" in st)
        print(f"  {sess['id']:<11} {sess['name']:<24} "
              f"{len(sess['steps'])} steps, {n} settings, "
              f"~{sess.get('target_minutes','?')} min")
    print(f"  baseline    {len(ob['baseline']['questions'])} questions")
    print()
    for w in WARN:
        print("WARN  " + w)
    for f in FAIL:
        print("FAIL  " + f)
    if FAIL:
        sys.exit(1)
    print("sequence complete and correctly ordered")


if __name__ == "__main__":
    main()
