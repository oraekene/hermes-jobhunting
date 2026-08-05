# Status — what is finished and what is not

**Short answer to "is the plugin build finished?": no.**

The *infrastructure* around the plugin is built and tested. The *plugin itself*
— your 137 skill files — has not been changed at all. Everything I produced sits
alongside it, describes it, or serves it. Nothing has been written into it.

That distinction matters, so here it is precisely.

## Built, tested, and ready to use

| Piece | Evidence |
|---|---|
| Dependency graph + interactive schematic | 247 nodes, 2,366 edges, re-runnable |
| Gate registry — 38 gates, 4 classes, 8 packs | `check_gates.py` passes |
| Settings registry — 111 keys scanned, 22 user-facing | `extract_settings.py` |
| Flow catalog — 38 flows, 8 axes | `check_flows.py`, 25/25 skills and 38/38 gates covered |
| Manifest + capability contracts | `check_manifest.py` passes |
| Onboarding sequence — 6 sessions, 22 settings | `check_onboarding.py` passes |
| Federated design + bandit + simulation | `simulate.py`, `sweep.py` |
| Injection corpus + runbook | `check_patterns.py`, 0 false positives |
| `install-check.py` | 13 test cases |
| Licensing spec + reference client | 21 self-tests |
| Build pipeline + watermarking | tested against your real 171 files |
| Cloudflare Worker — 8 endpoints | 33 tests |
| Generated user manual | leak check passes |
| Demo script, unit economics, schemas | — |

## Since the last status — five of the ten are now built

| Was | Now |
|---|---|
| 6 · bundle download | **built** — R2 streaming, entitlement re-checked from the database, per-seat build served when it exists and the template when it does not |
| 7 · email | **built** — licence delivery on purchase, payout notice on payout, via Resend |
| 8 · affiliate payout runs | **built** — monthly, thresholds, reversals netted off, no double payment |
| 9 · production crypto | **built** — Ed25519; the public key cannot forge, which HMAC could not promise |
| 10 · admin dashboard | **built** — read-only JSON views incl. trial conversion by market |

Worker tests: **52 passing**, up from 33.

Also: `apply_preflight.py` applies fixes 1, 2 and 4 to your real tree and reports
30 line occurrences across 19 relationships for fix 3.

## And now the permission-pack skill

**Built, conversational, 25 tests passing.** `permissions/` — a skill, a policy
engine, and the arming reference.

`gates.yaml` is no longer descriptive. `permissions.py` reads it and enforces
every invariant in code rather than in prose, because prose in a skill file is a
suggestion to a model and this needed to be a rule.

**One weakness surfaced while building it, and it was worth the detour.** The
typed phrase defends against a careless human and not against a prompt
injection — the phrase is written in the source, so any text that can make the
agent run a command can make it run the command *with the phrase*. And that text
can arrive inside a scraped job posting, which is untrusted input this pipeline
handles by design.

So arming now takes two steps and the second one leaves the machine: a six-digit
code goes to the approval channel — the user's phone — and must come back. It is
never returned to the calling process. Injected text cannot predict a code
generated after it was written, and cannot read a message sent to a phone.

There is a test for exactly that: *"an injection that runs the arm command
achieves nothing."*

## And the message catalog

**Built, 41 messages, 23 tests passing.** `shared/messages.yaml`,
`shared/scripts/msg.py`.

Item 9 from your original list, turned into something a build can check.
`msg.py check` fails the release if any user-visible string contains a skill
name, gate id, file path, rule number, config key or environment variable — the
same detector the documentation build uses, so the two cannot disagree.

The test suite asserts **the detector actually fires**, which matters more than
the catalog passing: a leak check that never triggers reports clean forever.

`msg.py scan` found 49 candidate strings across 9 skill files, concentrated in
the memory interview and interview prep. It reports and changes nothing —
guessing which quoted line is an emitted message and which is an example for the
model would eventually rewrite an instruction, and that failure is silent.

## And the federated loop — the last of the ten

**Built, 21 tests passing.** `federated/` — arm registry, client, aggregation.

Two real bugs surfaced in testing. The telemetry batch id was derived from whole
seconds, so two syncs in the same second collided on the primary key and the
failure surfaced as a crash rather than a retry. And the aggregation read rows
positionally where the schema could reorder underneath it.

The cases worth knowing pass: a retired approach is never chosen again; an
unreachable ledger is not an error; the payload carries counts only; a winner
visible in one model tier is held back; a thin cell publishes nothing of its
own; and a method decaying as adoption rises is retired automatically.

## Then I audited my own IP work, and found three gaps in it

Everything in `FIXES.md`. The short version:

**Two promises had not been kept.** `compile_scripts` was declared in the
manifest and absent from `build.py`; the legal layer was called "genuinely good
news" and never written. Both are closed — a bundle now contains 11 compiled
scripts and no readable source, and `LEGAL.md` is a draft for a lawyer.

**One was half-built.** "Skills fetched at activation, not shipped in the zip"
had a server and no client. `installer.py` is the other half, with 17 tests
covering the refusals that matter: a hash mismatch, an archive escaping its
destination, and an unverifiable token.

**Two build stages partly cancelled each other**, and config templates were
being watermarked despite being rewritten within days — a degraded mark points
at the wrong seat, which is worse than no mark.

**One number was an impression reported as a measurement.** The strip audit
counted headings. Measured per sentence: 696 explanatory sentences out of 4,476
against 16 liftable sections. Same conclusion, real evidence.

**The root cause was that nothing validated my specs against my code** — the
exact defect five checkers exist to catch in your package. `check_build.py`
closes it, and immediately caught a stage-ordering bug I had not spotted plus,
later, an unstamped installer that would have refused to install for every
customer.

## Nothing else is outstanding

All ten are built. What remains is yours: applying the three preflight fixes
that need judgement, creating the Bachs products, and deploying.

## Previously not built

**1. The six preflight fixes are unapplied.** `apply_preflight.py` does three of
them mechanically. Three need your hands — see below.

**Note:** `licence_client.py` has been removed. It signed with HMAC while the
Worker used Ed25519, so a reader learned the wrong model — and it was the exact
model whose weakness the Worker's own test demonstrates. `installer.py` replaces
it: one client, verifying the way the server signs.

## Roughly where that leaves you

**Everything between a payment and a working install now exists and is tested.**
A customer can buy, receive a key by email, activate, and download a
watermarked bundle. You can see your own numbers. Affiliates get paid.

All ten are built and tested. What remains is not construction: apply the three
preflight fixes that need your judgement, create the ten Bachs products, deploy,
and sell one.
