#!/usr/bin/env python3
"""
extract_graph.py - Build the dependency graph for the job-hunting package.

Mechanical extraction only. Every edge traces to a literal string found in a
file; nothing here is inferred from judgement. Output: graph.json + report.md
"""
import json, re, os
from pathlib import Path
from collections import defaultdict

SRC = Path(".")
PREFIX = ""

# ---------------------------------------------------------------- path recovery
SUBDIRS = ("references", "scripts", "hooks", "assets", "templates",
           "addenda", "addenda-27")

def logical_path(flat: str) -> str:
    """Recover a best-effort logical path from the flattened filename."""
    rest = flat[len(PREFIX):] if flat.startswith(PREFIX) else flat
    parts = rest.split("_")
    out, i = [], 0
    # component
    if parts[0] == "":                      # _merge-history style
        out.append("_" + parts[1]); i = 2
    else:
        out.append(parts[0]); i = 1
    # optional one or two known subdirs
    while i < len(parts) - 0 and parts[i] in SUBDIRS:
        out.append(parts[i]); i += 1
    # remainder is the filename (underscores restored)
    out.append("_".join(parts[i:]))
    return "/".join(p for p in out if p)

FILES = {}
for f in sorted(os.listdir(SRC)):
    FILES[logical_path(f)] = SRC / f

# ---------------------------------------------------------------- node building
nodes, edges = {}, []
SKILL_DIR_RE = re.compile(r"^(\d{2}-[a-z0-9-]+|onboarding)$")

def add_node(nid, ntype, **attrs):
    if nid not in nodes:
        nodes[nid] = {"id": nid, "type": ntype, **attrs}
    else:
        nodes[nid].update({k: v for k, v in attrs.items() if v})
    return nodes[nid]

def add_edge(src, dst, kind, evidence=""):
    if src == dst:
        return
    edges.append({"source": src, "target": dst, "kind": kind,
                  "evidence": evidence[:160]})

TEXT = {}
for lp, real in FILES.items():
    try:
        TEXT[lp] = real.read_text(encoding="utf-8", errors="replace")
    except Exception:
        TEXT[lp] = ""

# --- components (skills + support dirs) --------------------------------------
for lp in FILES:
    comp = lp.split("/")[0]
    fname = lp.split("/")[-1]
    if SKILL_DIR_RE.match(comp):
        add_node(comp, "skill", label=comp)
    elif comp in ("shared", "security", "cron", "templates", "_merge-history"):
        add_node(comp, "area", label=comp)
    else:
        add_node("root", "area", label="package root")

    # file-level nodes
    if fname == "SKILL.md":
        continue
    if fname.endswith(".py") or fname.endswith(".sh"):
        ftype = "script"
    elif fname.endswith(".sql"):
        ftype = "schema"
    elif fname.endswith((".yaml", ".template", ".yaml.template", ".json")):
        ftype = "config"
    elif fname.endswith((".md", ".html")):
        ftype = "doc"
    else:
        ftype = "file"
    add_node(lp, ftype, label=fname, owner=comp)
    owner = comp if comp in nodes else "root"
    add_edge(owner, lp, "contains")

# ---------------------------------------------------------------- frontmatter
FM_RE = re.compile(r"^---\n(.*?)\n---", re.S)
for lp, txt in TEXT.items():
    if not lp.endswith("SKILL.md") or lp.startswith("_merge-history"):
        continue
    comp = lp.split("/")[0]
    m = FM_RE.match(txt)
    if not m:
        continue
    fm = m.group(1)
    nm = re.search(r"^name:\s*(.+)$", fm, re.M)
    desc = re.search(r"^description:\s*[\"']?(.+?)[\"']?$", fm, re.M)
    if nm:
        nodes[comp]["skill_name"] = nm.group(1).strip()
    if desc:
        nodes[comp]["description"] = desc.group(1).strip()
    # blueprint
    sched = re.search(r"schedule:\s*[\"']([^\"']+)[\"']", fm)
    if sched:
        nodes[comp]["blueprint_schedule"] = sched.group(1)
        add_node("cron", "area", label="cron")
        add_edge("cron", comp, "blueprint", sched.group(1))
    # related_skills block
    rel = re.search(r"related_skills:\s*\n((?:\s*-\s*.+\n?)+)", fm)
    if rel:
        for line in rel.group(1).splitlines():
            t = line.strip().lstrip("- ").strip()
            if t:
                nodes[comp].setdefault("declared_related", []).append(t)

# map skill_name -> component, then resolve declared relations
NAME2COMP = {v.get("skill_name"): k for k, v in nodes.items() if v.get("skill_name")}
for comp, n in list(nodes.items()):
    for target_name in n.get("declared_related", []):
        tgt = NAME2COMP.get(target_name)
        if tgt:
            add_edge(comp, tgt, "declared_related", target_name)

# ---------------------------------------------------------------- path refs
REF_PATTERNS = [
    re.compile(r"(\d{2}-[a-z0-9-]+)/(?:SKILL\.md|references/[\w.-]+|scripts/[\w.-]+)"),
    re.compile(r"\b(shared/[\w.-]+)"),
    re.compile(r"\b(security/[\w./-]+)"),
    re.compile(r"\b(cron/[\w.-]+)"),
    re.compile(r"\b(templates/[\w.-]+)"),
    re.compile(r"\breferences/([\w.-]+\.md)"),
    re.compile(r"\bscripts/([\w.-]+\.(?:py|sh))"),
]

def owner_of(lp):
    c = lp.split("/")[0]
    return c if c in nodes else "root"

filemap = {}   # basename -> logical path
for lp in FILES:
    base = lp.split("/")[-1]
    filemap.setdefault(base, []).append(lp)
    # shipped config templates are cited by their live name, e.g.
    # "shared/target-profile.yaml" for target-profile_yaml.template
    if base.endswith("_yaml.template"):
        filemap.setdefault(base.replace("_yaml.template", ".yaml"), []).append(lp)

for lp, txt in TEXT.items():
    src = owner_of(lp) if lp.endswith("SKILL.md") else lp
    body = txt
    # cross-skill references
    for m in REF_PATTERNS[0].finditer(body):
        tgt = m.group(1)
        if tgt in nodes:
            add_edge(src, tgt, "references", m.group(0))
    # bare directory-name mentions ("09-risk-tactics-gate" with no path) —
    # the form most SKILL.md prose actually uses.
    for m in re.finditer(r"(?<![\w/-])(\d{2}-[a-z][a-z0-9-]{3,})(?![\w/-])", body):
        tgt = m.group(1)
        if tgt in nodes and nodes[tgt]["type"] == "skill":
            add_edge(src, tgt, "references", tgt)
    # shared / security / cron / templates files
    for pat in REF_PATTERNS[1:5]:
        for m in pat.finditer(body):
            raw = m.group(1)
            base = raw.split("/")[-1]
            cands = filemap.get(base) or filemap.get(base + ".template") or []
            for c in cands:
                add_edge(src, c, "references", raw)
            if not cands:
                comp = raw.split("/")[0]
                if comp in nodes:
                    add_edge(src, comp, "references", raw)
    # same-directory references/scripts
    for pat in REF_PATTERNS[5:]:
        for m in pat.finditer(body):
            base = m.group(1)
            for c in filemap.get(base, []):
                add_edge(src, c, "references", base)
    # bare-basename mentions: many files are cited by filename alone.
    # Only distinctive names (>=10 chars, has an extension) to avoid noise.
    for base, cands in filemap.items():
        stem = base.replace(".template", "")
        if len(stem) < 10 or "." not in stem:
            continue
        if re.search(r"(?<![\w.-])" + re.escape(stem) + r"\b", body):
            for c in cands:
                add_edge(src, c, "references", stem)

# ---------------------------------------------------------------- SQL tables
TBL_RE = re.compile(r"CREATE\s+(TABLE|VIEW)(?:\s+IF\s+NOT\s+EXISTS)?\s+([A-Za-z_][\w]*)", re.I)
tables = {}
for lp, txt in TEXT.items():
    if not lp.endswith(".sql"):
        continue
    for kind, name in TBL_RE.findall(txt):
        tid = f"db:{name}"
        add_node(tid, "table" if kind.upper() == "TABLE" else "view",
                 label=name, defined_in=lp)
        add_edge(lp, tid, "defines")
        tables[name] = tid

# who touches which table
for lp, txt in TEXT.items():
    if lp.endswith(".sql"):
        continue
    src = owner_of(lp) if lp.endswith("SKILL.md") else lp
    for name, tid in tables.items():
        if len(name) < 5:
            continue
        if re.search(r"\b" + re.escape(name) + r"\b", txt):
            add_edge(src, tid, "touches_table", name)

# ---------------------------------------------------------------- cron jobs
cron_txt = TEXT.get("cron/cron-jobs.md", "")
JOB_RE = re.compile(r"^##\s*(\d+[a-z]?)\.\s*(.+)$", re.M)
for num, title in JOB_RE.findall(cron_txt):
    jid = f"cron:{num}"
    add_node(jid, "cronjob", label=f"job {num}: {title.strip()}")
    add_edge("cron", jid, "contains")
# link cron jobs to skills via --skill flags in the same doc
for m in re.finditer(r"--skill\s+([\w-]+)", cron_txt):
    tgt = NAME2COMP.get(m.group(1))
    if tgt:
        add_edge("cron", tgt, "schedules", m.group(1))

# ---------------------------------------------------------------- dedupe
seen, uniq = set(), []
for e in edges:
    k = (e["source"], e["target"], e["kind"])
    if k in seen:
        continue
    seen.add(k)
    uniq.append(e)
edges = uniq

graph = {"nodes": list(nodes.values()), "edges": edges}
Path("/home/claude/graph.json").write_text(json.dumps(graph, indent=2))

# ---------------------------------------------------------------- summary
by_type = defaultdict(int)
for n in nodes.values():
    by_type[n["type"]] += 1
by_kind = defaultdict(int)
for e in edges:
    by_kind[e["kind"]] += 1
print("files parsed:", len(FILES))
print("nodes:", len(nodes), dict(by_type))
print("edges:", len(edges), dict(by_kind))
