#!/usr/bin/env python3
"""
check_flows.py — cross-validate flows.yaml against the other three artefacts.

    python3 check_flows.py

A flow that names a skill, gate or setting that does not exist is a flow that
will be documented, demoed and then found to be wrong. This catches that.
Also reports coverage: which skills and gates no flow exercises.
"""
import json, sys, yaml
from collections import defaultdict

FAIL, WARN = [], []

def main():
    flows_doc = yaml.safe_load(open("flows.yaml"))
    gates_doc = yaml.safe_load(open("gates.yaml"))
    sets_doc  = yaml.safe_load(open("settings.yaml"))
    graph     = json.load(open("graph.json"))

    FLOWS = flows_doc["flows"]
    SKILLS = {n["id"] for n in graph["nodes"] if n["type"] == "skill"}
    GATES  = {g["id"] for g in gates_doc["gates"]}
    SETS   = {s["key"] for s in sets_doc["settings"]}
    AXES   = set(flows_doc["axes"])

    ids = [f["id"] for f in FLOWS]
    if len(ids) != len(set(ids)):
        FAIL.append("duplicate flow ids")
    if flows_doc["meta"]["flows"] != len(FLOWS):
        FAIL.append(f"meta.flows={flows_doc['meta']['flows']} but {len(FLOWS)} defined")

    TRIGGERS = {"cron", "utterance", "handoff", "external", "install_state"}
    used_skills, used_gates = set(), set()

    for f in FLOWS:
        fid = f["id"]
        if f["trigger"]["type"] not in TRIGGERS:
            FAIL.append(f"{fid}: unknown trigger type {f['trigger']['type']!r}")
        if not f.get("steps"):
            FAIL.append(f"{fid}: no steps")
        for s in f.get("steps", []):
            if s not in SKILLS:
                FAIL.append(f"{fid}: step {s!r} is not a skill in graph.json")
            used_skills.add(s)
        for g in f.get("gates", []):
            if g not in GATES:
                FAIL.append(f"{fid}: gate {g!r} not in gates.yaml")
            used_gates.add(g)
        for a in f.get("axes", []):
            if a not in SETS and a not in AXES:
                FAIL.append(f"{fid}: axis {a!r} is neither a setting key nor a declared axis")
        for nxt in ([f["next"]] if isinstance(f.get("next"), str) else f.get("next", [])):
            if nxt not in ids:
                FAIL.append(f"{fid}: next {nxt!r} is not a flow id")
        if not f.get("doc"):
            FAIL.append(f"{fid}: missing doc scenario")

    # axis back-reference must resolve both ways
    for axis, spec in flows_doc["axes"].items():
        for fid in spec["affects"]:
            if fid not in ids:
                FAIL.append(f"axis {axis}: affects unknown flow {fid}")
            else:
                f = next(x for x in FLOWS if x["id"] == fid)
                if axis not in f.get("axes", []):
                    WARN.append(f"axis {axis} claims {fid} but that flow does not list it")

    # coverage
    uncovered_skills = sorted(SKILLS - used_skills)
    uncovered_gates  = sorted(GATES - used_gates)

    print(f"{len(FLOWS)} flows, {len(flows_doc['axes'])} axes")
    fam = defaultdict(int)
    for f in FLOWS:
        fam[f["family"]] += 1
    for k, v in sorted(fam.items()):
        print(f"  {k:<12} {v}")
    print(f"  demo flows   {sum(1 for f in FLOWS if f.get('demo'))}")
    print()
    print(f"skill coverage : {len(used_skills)}/{len(SKILLS)}")
    if uncovered_skills:
        print(f"  no flow uses : {uncovered_skills}")
    print(f"gate coverage  : {len(used_gates)}/{len(GATES)}")
    if uncovered_gates:
        print(f"  no flow fires: {uncovered_gates}")
    print()
    for w in WARN:
        print("WARN  " + w)
    for f in FAIL:
        print("FAIL  " + f)
    if FAIL:
        sys.exit(1)
    print("all cross-references resolve")

if __name__ == "__main__":
    main()
