#!/usr/bin/env python3
"""
build.py — turn the working package into a shippable, per-seat bundle.

    python3 build.py audit   --src PKG              what could be stripped, and why
    python3 build.py build   --src PKG --out DIR --seat SEATID
    python3 build.py verify  --bundle DIR           signature + manifest check
    python3 build.py trace   --bundle DIR           recover the seat from a leaked copy

FIVE STAGES, in order:
  1 validate   run every checker; refuse to build on a failure
  2 exclude    drop history, audits, merge records
  3 strip      remove explicitly marked rationale — NEVER guessed at
  4 watermark  encode the seat id invisibly, redundantly, recoverably
  5 sign       detached signature over a manifest of hashes

ON STRIPPING. The build removes only what an author has explicitly marked with
<!--rationale--> ... <!--/rationale-->. It does not guess. A heuristic that
strips headings called "Why" would eventually strip an instruction that happens
to explain itself, and the failure would be silent — a skill that still reads
convincingly and does less. `audit` exists to find candidates for a human to
mark; it never removes anything.

ON WATERMARKING. Trailing whitespace, one bit per eligible line, payload
repeated so a partial edit does not destroy it. Chosen over the obvious
alternatives for one reason: the agent READS these files, so a watermark must
be invisible to the model as well as to the reader. Zero-width characters and
HTML comments both sit in the token stream and can surface in generated output —
a cover letter carrying an invisible tracking character is a far worse problem
than the piracy it was meant to deter. End-of-line whitespace carries no
semantic content, survives copy-paste of whole files, and cannot be echoed.
"""
from __future__ import annotations
import argparse, hashlib, hmac, json, re, shutil, subprocess, sys
from pathlib import Path

EXCLUDE_DIRS = {"_merge-history", ".git", "__pycache__", ".github"}
EXCLUDE_FILES = {
    "ADDENDUM-CHANGELOG.md", "AUDIT-TRIAGE.md", "MERGE-STATUS.md",
    "hermes-capability-audit.md", "HERMES_UPGRADE_CHANGELOG.md",
    "MERGED-INTO.md", "SUPERSEDED-SKILL.md",
}
RATIONALE = re.compile(r"<!--\s*rationale\s*-->.*?<!--\s*/rationale\s*-->",
                       re.S | re.I)

# Headings that USUALLY introduce reasoning rather than instruction. Used by
# `audit` to suggest candidates. Never used by `build`.
CANDIDATE_HEADS = re.compile(
    r"^#{2,4}\s+(why\b|rationale|design (note|decision)|reasoning|背景"
    r"|trade[- ]?off|alternatives considered|history|background|"
    r"what (this )?replaces|notes? on the design)", re.I | re.M)

# E4/E5. Only files the tool does not rewrite, and only files that survive to
# the customer as text.
#   .yaml/.yml/.template become the user's LIVE config and are rewritten within
#     days — a half-degraded mark points at the wrong seat, which is worse than
#     no mark at all. Prefer no attribution to wrong attribution.
#   .py is compiled two stages later, so a whitespace mark on it is erased by
#     the same build that applied it.
WATERMARKABLE = {".md", ".sql", ".txt"}
COMPILABLE = {".py"}
FENCE = re.compile(r"^\s*(```|~~~)")


# ── watermark ───────────────────────────────────────────────────────────────

def _payload_bits(seat: str) -> list[int]:
    """32-bit seat digest + 8-bit checksum, LSB first."""
    d = hashlib.sha256(seat.encode()).digest()
    val = int.from_bytes(d[:4], "big")
    chk = sum(d[:4]) & 0xFF
    bits = [(val >> i) & 1 for i in range(32)] + [(chk >> i) & 1 for i in range(8)]
    return bits


def _eligible(lines: list[str]) -> list[int]:
    """Line indexes that may carry a bit: non-empty, outside code fences."""
    out, in_fence = [], False
    for i, ln in enumerate(lines):
        if FENCE.match(ln):
            in_fence = not in_fence
            continue
        if in_fence or not ln.strip():
            continue
        out.append(i)
    return out


def watermark_text(text: str, seat: str) -> str:
    lines = [ln.rstrip() for ln in text.split("\n")]     # normalise first
    idx = _eligible(lines)
    bits = _payload_bits(seat)
    if len(idx) < len(bits):
        return "\n".join(lines)                          # too small to carry it
    for n, i in enumerate(idx):
        if bits[n % len(bits)]:                          # repeat to survive edits
            lines[i] = lines[i] + " "
    return "\n".join(lines)


def extract_bits(text: str) -> list[int]:
    lines = text.split("\n")
    return [1 if lines[i].endswith(" ") else 0 for i in _eligible(lines)]


def trace_text(text: str, candidates: list[str]) -> tuple[str | None, float]:
    """Recover the seat by testing candidates against the recovered bitstream.

    Majority-votes across repeats, so edits to part of a file do not destroy
    attribution.
    """
    got = extract_bits(text)
    if len(got) < 40:
        return None, 0.0
    votes = [0] * 40
    counts = [0] * 40
    for n, b in enumerate(got):
        votes[n % 40] += b
        counts[n % 40] += 1
    recovered = [1 if votes[i] * 2 > counts[i] else 0 for i in range(40)]
    best, best_score = None, 0.0
    for seat in candidates:
        want = _payload_bits(seat)
        score = sum(1 for a, b in zip(recovered, want) if a == b) / 40
        if score > best_score:
            best, best_score = seat, score
    return (best, best_score) if best_score >= 0.85 else (None, best_score)


# ── second channel ──────────────────────────────────────────────────────────
# The whitespace channel dies to one command: sed -i 's/[ \t]*$//' -r .
# That is worth knowing rather than hiding. So a second, independent channel
# goes into a file the BUILD generates, where the format is entirely ours:
# the order of entries encodes the seat. It survives whitespace normalisation,
# reformatting and re-indenting, and it is removable only by someone who
# notices the file means something.
#
# Neither channel stops a determined attacker. Together they comfortably beat
# the actual threat model, which is a buyer forwarding a folder on WhatsApp —
# that person does not run sed.

def _perm(items: list[str], seat: str) -> list[str]:
    """Deterministic seat-dependent permutation. Recoverable by comparison."""
    return [x for _, x in sorted(
        (hashlib.sha256((seat + x).encode()).hexdigest(), x) for x in items)]


def write_index(out: Path, files: list[str], seat: str):
    salt = hashlib.sha256(("idx" + seat).encode()).hexdigest()[:16]
    (out / ".package-index").write_text(
        "# generated at build; do not edit\n"
        f"build_salt: {salt}\n"
        "contents:\n" + "".join(f"  - {f}\n" for f in _perm(files, seat)))


def trace_index(bundle: Path, candidates: list[str]) -> str | None:
    f = bundle / ".package-index"
    if not f.is_file():
        return None
    text = f.read_text()
    m = re.search(r"build_salt:\s*(\w+)", text)
    if m:
        for seat in candidates:                       # salt is a direct match
            if hashlib.sha256(("idx" + seat).encode()).hexdigest()[:16] == m.group(1):
                return seat
    listed = re.findall(r"^\s+-\s+(.+)$", text, re.M)
    for seat in candidates:                           # ordering survives salt removal
        if _perm(listed, seat) == listed:
            return seat
    return None


# ── stages ──────────────────────────────────────────────────────────────────

def iter_files(src: Path):
    for p in sorted(src.rglob("*")):
        if not p.is_file():
            continue
        if any(part in EXCLUDE_DIRS for part in p.parts):
            continue
        if p.name in EXCLUDE_FILES:
            continue
        yield p


def stage_validate(src: Path, skip: bool) -> list[str]:
    if skip:
        return []
    fails = []
    for chk in ["check_gates.py", "check_flows.py", "check_manifest.py",
                "check_onboarding.py", "check_patterns.py"]:
        if not (src / chk).is_file():
            continue
        r = subprocess.run([sys.executable, chk], cwd=src,
                           capture_output=True, text=True)
        if r.returncode != 0:
            fails.append(f"{chk}: {r.stdout.strip().splitlines()[-1] if r.stdout else 'failed'}")
    return fails


# E7. The audit used to count headings and I reported the number as though it
# measured how much reasoning the package contains. It did not. These are
# sentence-level signals — prose that EXPLAINS rather than INSTRUCTS — so the
# figure is at least about the right thing.
#
# It is still an estimate. It cannot tell a justification the agent needs from
# one only a reader needs, and that judgement is the entire task. The number
# says how much prose looks explanatory; it does not say how much is safe to
# remove, and nothing here should be read as if it did.
# Matched per SENTENCE, not per line start — the first version anchored to ^ and
# reported 1%, which was an artefact of the anchor rather than a fact about the
# package. Explanatory clauses live mid-sentence far more often than they open
# one.
EXPLANATORY = re.compile(
    r"\b(?:because|the reason(?:ing)?\b|rather than|as opposed to|otherwise\b"
    r"|which is why|that is why|the point (?:is|being)|note that|worth noting"
    r"|the failure mode|the risk (?:is|here)|deliberately|on purpose|by design"
    r"|we (?:chose|considered|rejected|decided)|i (?:chose|considered|decided)"
    r"|historically|in practice|the trade[- ]?off|instead of|so that\b)", re.I)

IMPERATIVE = re.compile(
    r"^\s*(?:\d+\.|[-*])?\s*(?:always|never|do not|don't|must|should|run|write|"
    r"read|check|ask|use|set|call|emit|log|record|confirm|stop|refuse|apply|"
    r"return|report|skip|include|exclude)\b", re.I | re.M)

SENTENCE = re.compile(r"(?<=[.!?])\s+|\n{2,}")


def _sentences(text: str) -> list[str]:
    body = "\n".join(ln for ln in text.split("\n")
                     if ln.strip() and not ln.lstrip().startswith(("#", "|", "```")))
    return [s for s in SENTENCE.split(body) if len(s.split()) >= 4]


def stage_audit(src: Path):
    """Report strip candidates. Removes nothing."""
    marked = marked_bytes = 0
    exp_lines = imp_lines = body_lines = 0
    head_hits = 0
    rows = []
    for p in iter_files(src):
        if p.suffix != ".md":
            continue
        t = p.read_text(encoding="utf-8", errors="replace")
        for m in RATIONALE.finditer(t):
            marked += 1
            marked_bytes += len(m.group(0))
        head_hits += len(CANDIDATE_HEADS.findall(t))

        sents = _sentences(t)
        e = sum(1 for s in sents if EXPLANATORY.search(s))
        i = len(IMPERATIVE.findall(t))
        exp_lines += e; imp_lines += i; body_lines += len(sents)
        if e:
            rows.append((p, e, i, len(sents)))
    return {"marked": marked, "marked_bytes": marked_bytes,
            "heading_candidates": head_hits, "explanatory": exp_lines,
            "imperative": imp_lines, "body": body_lines, "rows": rows}


def stage_package(src: Path, out: Path) -> int:
    """Collect the shippable tree. Exclusions happen here and nowhere else."""
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    n = 0
    for p in iter_files(src):
        dst = out / p.relative_to(src)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dst)
        n += 1
    return n


def stage_strip_rationale(tree: Path) -> int:
    """Remove explicitly marked blocks. Never guesses — see `audit`."""
    removed = 0
    for p in tree.rglob("*.md"):
        t = p.read_text(encoding="utf-8", errors="replace")
        t2 = RATIONALE.sub("", t)
        if t2 != t:
            removed += len(t) - len(t2)
            p.write_text(t2, encoding="utf-8")
    return removed


def stage_watermark(tree: Path, seat: str) -> int:
    """Channel one. Runs BEFORE compilation, and never on files the tool
    rewrites."""
    n = 0
    for p in tree.rglob("*"):
        if not p.is_file() or p.suffix not in WATERMARKABLE:
            continue
        t = p.read_text(encoding="utf-8", errors="replace")
        t2 = watermark_text(t, seat)
        if t2 != t:
            p.write_text(t2, encoding="utf-8")
            n += 1
    return n


def stage_compile_scripts(tree: Path) -> tuple[int, str]:
    """Raise the cost of reading the scripts from minutes to hours.

    Nuitka when it is available, byte-compilation as the portable fallback, and
    a LOUD skip when neither applies. A silent pass here is exactly the defect
    this stage was added to fix.
    """
    targets = [p for p in tree.rglob("*") if p.is_file() and p.suffix in COMPILABLE]
    if not targets:
        return 0, "nothing to compile"

    if shutil.which("nuitka") or shutil.which("nuitka3"):
        tool = shutil.which("nuitka") or shutil.which("nuitka3")
        done = 0
        for p in targets:
            r = subprocess.run([tool, "--module", "--quiet",
                                f"--output-dir={p.parent}", str(p)],
                               capture_output=True, text=True)
            if r.returncode == 0:
                p.unlink()
                done += 1
        return done, "nuitka"

    import py_compile
    done = 0
    for p in targets:
        try:
            py_compile.compile(str(p), cfile=str(p.with_suffix(".pyc")),
                               doraise=True, optimize=2)
            p.unlink()
            done += 1
        except Exception as e:
            print(f"  ! could not compile {p.name}: {e}")
    return done, "py_compile (install nuitka for a stronger result)"


def stage_sign(tree: Path, seat: str, key: bytes) -> int:
    """Detached signature over a manifest of per-file hashes."""
    manifest = {}
    for p in sorted(tree.rglob("*")):
        if p.is_file() and p.name not in ("MANIFEST.json", "MANIFEST.sig"):
            manifest[str(p.relative_to(tree))] = hashlib.sha256(
                p.read_bytes()).hexdigest()
    write_index(tree, sorted(manifest), seat)          # channel two
    manifest[".package-index"] = hashlib.sha256(
        (tree / ".package-index").read_bytes()).hexdigest()
    body = json.dumps({"seat": seat, "files": manifest}, sort_keys=True,
                      separators=(",", ":"))
    (tree / "MANIFEST.json").write_text(body)
    (tree / "MANIFEST.sig").write_text(
        hmac.new(key, body.encode(), hashlib.sha256).hexdigest())
    return len(manifest)


def stage_build(src: Path, out: Path, seat: str, key: bytes):
    """The pipeline, in the order the manifest declares."""
    n = stage_package(src, out)
    # stage_validate ran before this was called — see main()
    stripped = stage_strip_rationale(out)
    wm = stage_watermark(out, seat)
    compiled, how = stage_compile_scripts(out)
    signed = stage_sign(out, seat, key)
    return n, stripped, wm, compiled, how, signed


def stage_verify(bundle: Path, key: bytes):
    body = (bundle / "MANIFEST.json").read_text()
    sig = (bundle / "MANIFEST.sig").read_text().strip()
    if not hmac.compare_digest(sig, hmac.new(key, body.encode(),
                                             hashlib.sha256).hexdigest()):
        return False, ["signature does not verify"], None
    doc = json.loads(body)
    bad = []
    for rel, want in doc["files"].items():
        f = bundle / rel
        if not f.is_file():
            bad.append(f"missing: {rel}")
        elif hashlib.sha256(f.read_bytes()).hexdigest() != want:
            bad.append(f"modified: {rel}")
    return not bad, bad, doc["seat"]


# ── cli ─────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["audit", "build", "verify", "trace",
                                    "stamp-installer"])
    ap.add_argument("--src"); ap.add_argument("--out")
    ap.add_argument("--bundle"); ap.add_argument("--seat")
    ap.add_argument("--seats", help="comma-separated candidates for trace")
    ap.add_argument("--key", default="dev-signing-key")
    ap.add_argument("--public-key"); ap.add_argument("--installer", default="installer.py")
    ap.add_argument("--skip-validate", action="store_true")
    a = ap.parse_args()
    key = a.key.encode()

    if a.cmd == "audit":
        src = Path(a.src)
        r = stage_audit(src)
        files = list(iter_files(src))
        total = sum(p.stat().st_size for p in files)
        share = r["explanatory"] / max(r["body"], 1)
        print(f"package: {len(files)} files, {total/1024:,.0f} KB after exclusions\n")
        print(f"  marked and strippable now : {r['marked']} blocks "
              f"({r['marked_bytes']/1024:,.1f} KB)")
        print(f"  liftable sections         : {r['heading_candidates']} headings")
        print(f"  sentences of prose        : {r['body']:,}")
        print(f"  explanatory sentences     : {r['explanatory']:,} ({share:.0%})")
        print(f"  instruction lines         : {r['imperative']:,}")
        if r["rows"]:
            print("\nmost explanatory files:")
            for p, e, i, b in sorted(r["rows"], key=lambda x: -x[1])[:10]:
                print(f"  {e:>4} of {b:>4} sentences ({e/max(b,1):>3.0%})   "
                      f"{p.parent.name}/{p.name}")
        print(f"\nHow to read this. {share:.0%} of sentences carry an explanatory signal,")
        print(f"spread through the prose rather than gathered under headings — only")
        print(f"{r['heading_candidates']} sections could be lifted whole. That is why")
        print("marking is a per-file job and not a build setting.")
        print("\nWHAT THIS CANNOT SEE: whether a given explanation is one the agent")
        print("needs or one only a reader needs. That judgement is the whole task,")
        print("and this number does not make it. Nothing was removed.")

    elif a.cmd == "build":
        src, out = Path(a.src), Path(a.out)
        fails = stage_validate(src, a.skip_validate)
        if fails:
            print("VALIDATION FAILED — refusing to build")
            for f in fails:
                print("  " + f)
            sys.exit(1)
        n, stripped, wm, compiled, how, signed = stage_build(src, out, a.seat, key)
        print(f"built {n} files for seat {a.seat}")
        print(f"  stripped     {stripped/1024:,.1f} KB of marked rationale")
        print(f"  watermarked  {wm} files")
        print(f"  compiled     {compiled} scripts via {how}")
        print(f"  signed       {signed} entries -> {out/'MANIFEST.sig'}")

    elif a.cmd == "verify":
        ok, bad, seat = stage_verify(Path(a.bundle), key)
        print(f"seat {seat}: " + ("intact" if ok else "TAMPERED"))
        for b in bad[:20]:
            print("  " + b)
        sys.exit(0 if ok else 1)

    elif a.cmd == "stamp-installer":
        # The installer ships SEPARATELY from the bundle — it is the thing that
        # fetches the bundle, so it cannot be inside it. It therefore needs its
        # own build step, and without one it reads its verification key from an
        # environment variable that no customer will ever have set. A shipped
        # installer with no key refuses to install anything, which is a blocker
        # on the whole delivery path rather than a rough edge.
        src = Path(a.installer)
        if not a.public_key:
            print("stamp-installer needs --public-key (the Ed25519 PUBLIC half, "
                  "base64). Get it from `node worker/scripts/keygen.js`.")
            sys.exit(1)
        text = src.read_text(encoding="utf-8")
        stamped = text.replace(
            'PUBLIC_KEY = os.environ.get("JH_PUBLIC_KEY", "")',
            f'PUBLIC_KEY = os.environ.get("JH_PUBLIC_KEY", "{a.public_key}")')
        if stamped == text:
            print("could not find the key placeholder in the installer — refusing "
                  "to ship one that cannot verify")
            sys.exit(1)
        out = Path(a.out or "dist/installer.py")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(stamped, encoding="utf-8")
        digest = hashlib.sha256(out.read_bytes()).hexdigest()
        print(f"stamped {out}")
        print(f"  sha256 {digest}")
        print("  publish this alongside the download link, and publish the hash "
              "beside it so a customer can check what they ran")

    elif a.cmd == "trace":
        bundle = Path(a.bundle)
        cands = [c for c in (a.seats or "").split(",") if c]
        scores = {}
        idx = trace_index(bundle, cands)
        if idx:
            print(f"traced to seat {idx}  (index channel)")
        for p in bundle.rglob("*"):
            if p.is_file() and p.suffix in WATERMARKABLE:
                seat, score = trace_text(p.read_text(encoding="utf-8",
                                                     errors="replace"), cands)
                if seat:
                    scores[seat] = scores.get(seat, 0) + 1
        if not scores:
            if idx:
                sys.exit(0)
            print("no watermark recovered")
            sys.exit(1)
        best = max(scores, key=scores.get)
        print(f"traced to seat {best}  (whitespace channel, {scores[best]} files agree)")


if __name__ == "__main__":
    main()
