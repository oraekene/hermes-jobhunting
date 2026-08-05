# Fix plan — my errors, and how each gets closed

Eight open items. Five are code and testable, one is prose that needs a lawyer,
two are method corrections. Ordered so the guard lands first and nothing can
drift back.

Already corrected in place during the build, listed so the record is complete
and not re-fixed: the `schema_version` integrity claim (wrong, retracted in
`PACKAGING.md` and `manifest.yaml`), the USDT recommendation (withdrawn in
`PAYMENTS.md`), "6.9% is high" (contextualised against every alternative), the
opening DRM position (conceded), and five implementation bugs the test suites
caught at the time — `GATE-PORTFOLIO-PUBLISH`'s missing arm requirement, the
key-material cache in `crypto.js`, the telemetry batch-id collision, the
aggregation row factory, and the unthreaded environment in `install-check.py`.

---

## E8 · Nothing validates the specs against the code  ·  **root cause, do first**

`manifest.yaml` declares six build stages. `build.py` implements four. No
checker looks, which is precisely how the gap survived — and it is the same
class of defect I built five checkers to catch in *your* package while leaving
mine unguarded.

**Fix:** `check_build.py`. Every declared build stage must map to an
implemented function; every script a document names as runnable must exist and
must run. Wire into the release workflow beside the others.

**Done when:** removing a stage function fails the check.

---

## E1 · `compile_scripts` is specced and not built

`build.py` copies `.py` files verbatim. The manifest says they are compiled.

**Fix:** implement the stage. Nuitka when present, `py_compile` to `.pyc` as
the portable fallback, and a plain skip with a warning when neither applies —
never a silent pass, because a silent pass is what produced this.

**Done when:** a built bundle contains no readable `.py` source for the scripts,
and `check_build.py` agrees the stage ran.

---

## E4 · Watermarking config templates is worse than useless

`.yaml` and `.template` files become the user's live config and are rewritten by
the tool within days. That channel degrades to nothing on exactly the files most
likely to be shared as "here is my setup" — and worse, a half-degraded
watermark can point at the wrong seat.

**Fix:** watermark only files the tool does not rewrite. Prefer no attribution
to wrong attribution.

**Done when:** a config file round-tripped through an edit yields no trace, and
`trace` never names a seat it is not confident about.

---

## E5 · Two build stages partly cancel

Once `.py` files are compiled they are binaries, so the whitespace watermark on
them does nothing. Two stages, one of which silently undoes part of the other.

**Fix:** watermark before compiling, and drop `.py` from the whitespace channel
entirely — compiled artefacts carry the seat through the manifest and index
channels instead.

**Done when:** stage order is explicit in the manifest and enforced by the
checker.

---

## E6 · The reference client contradicts the shipping code

`licence_client.py` signs with HMAC. The Worker uses Ed25519. Anyone reading the
reference to understand activation learns the wrong model — and it is the exact
model whose weakness I wrote a test to demonstrate.

**Fix:** port the reference to Ed25519 so the two agree.

**Done when:** the selftest verifies with a public key that cannot mint, and a
token signed by another key is rejected.

---

## E7 · I reported an impression as a measurement

The strip audit counts marked blocks and heading matches. It does not measure
inline prose. I reported "16 candidates" in a way that read as a measurement of
how much reasoning the package contains, when the real basis for "the reasoning
is woven inline" was having read the files.

**Fix:** make the audit measure what it claims — a rationale/instruction ratio
per file using explicit signals — and say plainly what it cannot see.

**Done when:** `audit` reports a defensible number and names its own limits.

---

## E3 · "Delivery at activation" is half-built

The server half exists: entitlement re-checked, per-seat bundle, template
fallback. There is no client that fetches. Today a customer still receives a
folder, which is the thing this layer was supposed to prevent.

**Fix:** `installer.py` — take a licence key, fingerprint the machine, activate,
download, verify the signature, unpack, run the install check.

**Done when:** a licence key and nothing else produces a working install, and a
bad signature refuses to unpack.

---

## E2 · The legal layer was called good news and never written

I said an EULA is cheap and the only layer that works against a competitor
rather than a casual sharer — then wrote nothing. Watermarking identifies who
leaked; copyright is what lets you act on it.

**Fix:** draft `LEGAL.md` — EULA starting point, the Nigerian Copyright Act 2022
position, NCC registration, and the auto-approve acknowledgement the permission
design needs. **Explicitly a starting point for a lawyer, not final text.**

**Done when:** there is something to take to a lawyer, and the auto-approve
clause matches what the gates actually do.

---

## Status

All eight closed. `check_build.py` is the guard that keeps E1, E4 and E5 from
recurring; `test_installer.py` covers E3 and E6; the audit output now states its
own limits for E7; `LEGAL.md` is the E2 draft, and it is the one item that is
deliberately unfinished — it needs a lawyer, not another commit.

## Order

E8 → E1 → E5 → E4 → E6 → E7 → E3 → E2

The guard first so nothing regresses; the build stages next because E5 fixes the
ordering E1 depends on; then the code corrections; then the installer; then the
legal draft, which is the only item that leaves this bundle unfinished by design.
