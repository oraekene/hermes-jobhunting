# Build pipeline — measured against your real package

`build.py` and `.github/workflows/release.yml`. Every number below comes from
running it on the actual 171 files, not from an estimate.

## What the build does

| Stage | What | Result on your package |
|---|---|---|
| 1 validate | every checker, then refuse on failure | 5 checkers + 2 test suites |
| 2 exclude | history, audits, merge records | **171 → 137 files, 1,505 → 1,229 KB** |
| 3 strip | marked rationale only | 0 KB — see below |
| 4 watermark | two independent channels | 115 files carry the seat |
| 5 sign | detached signature over a hash manifest | verified on rebuild |

## Correction: `strip_rationale` is worth much less than I told you

I called it "the single highest-value protection step, and it costs nothing."
**Running it on your package proves that wrong**, and you should know before
spending time on it.

The audit found **696 explanatory sentences out of 4,476 (16%) against only 16
liftable sections** — one each. Your design reasoning is not sitting in tidy
"Why this design" sections that a build can lift out. It is woven inline,
sentence by sentence, into the instructions themselves. Stripping it would mean
rewriting 137 files by hand, and every edit risks removing an instruction that
happens to explain itself.

**What actually delivers is exclusion: 34 files, 276 KB, 18% of the package** —
`_merge-history/`, the audit files, the changelogs, the superseded skills. That
is where your accumulated reasoning lives, it is one line of configuration, and
it is already done.

So: keep `<!--rationale-->` markers available for new writing, mark blocks as
you touch files anyway, and do not schedule a marking pass. The 18% is the win.

## Watermarking, and its honest limits

Two independent channels, because one is fragile.

**Channel 1 — trailing whitespace.** One bit per eligible line, payload repeated
so partial edits survive. High capacity, applies to 115 files.

Chosen over the obvious alternatives for a reason worth stating: **the agent
reads these files.** Zero-width characters and HTML comments both sit in the
token stream and can surface in generated output. A cover letter carrying an
invisible tracking character is a far worse problem than the piracy it was
meant to deter. End-of-line whitespace carries no semantic content and cannot
be echoed.

**Channel 2 — build-generated index.** The build writes `.package-index`, whose
entry *order* encodes the seat, plus a salt. The format is entirely ours, so
this survives whitespace normalisation and reformatting.

### Tested against escalating removal

| Attack | Result |
|---|---|
| Only the SKILL.md files copied out | **traced** |
| A single file leaked | **traced** |
| 20% of lines rewritten | **traced** |
| `.package-index` deleted | **traced** (whitespace) |
| Trailing whitespace stripped | **traced** (index) |
| Whitespace stripped **and** salt line deleted | **traced** (ordering) |
| Whitespace stripped **and** index re-sorted | **not traced** |
| Different seat | correctly distinguished |

**The last row is the honest limit.** Two commands — strip trailing whitespace,
re-sort the index — defeat both channels. Nothing client-side survives someone
who knows what to look for.

But that is not your threat model. **Your threat is a buyer forwarding a folder
on WhatsApp, and that person does not run `sed`.** Against the actual risk, two
layered channels are comfortably enough, and the deterrent works because it is
social: someone who knows their copy is traceable does not send it to fifteen
friends.

## Signing

Detached signature over a manifest of per-file SHA-256 hashes. `verify` reports
`intact` or names every modified and missing file. Swap the HMAC for Ed25519 in
production and pin the public key in the client.

## GitHub Actions

Runs in about two minutes against a **2,000 free Linux minute** monthly
allowance on the private-repo Free plan. Roughly 1,000 builds a month; you will
not approach it.

Three deliberate choices:

- **`runs-on: ubuntu-latest`, never Windows or macOS.** They drain the free
  quota at 2× and 10×.
- **Derived artefacts are regenerated, not trusted.** `graph.json` and the
  manual are rebuilt every run, because a stale derived file is a wrong one.
- **Bundles go straight to R2, never to Actions artifacts.** The free plan gives
  500 MB shared with Packages, and per-seat bundles fill that fast. Artifacts
  are for build logs on failure, nothing else.

Secrets needed: `SIGNING_KEY`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`,
`R2_ENDPOINT`.

## Commands

```bash
python3 build.py audit  --src .                       # candidates; removes nothing
python3 build.py build  --src . --out dist --seat SEAT --key "$SIGNING_KEY"
python3 build.py verify --bundle dist --key "$SIGNING_KEY"
python3 build.py trace  --bundle leaked --seats s1,s2,s3
```

`trace` is what you run when a copy turns up somewhere it should not be. Feed it
your seat ids from `seats` in the licensing database; it names the buyer.

And then — per `LICENSING.md` — **contact them rather than revoking.** Someone
who shared a copy is still a customer.
