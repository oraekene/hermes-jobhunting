# Packaging — how this becomes a plugin with paid addons and safe updates

Validated by `check_manifest.py` against the graph and all three registries. The short version: **nothing is rewritten.** The skill directories, the `references/` pattern, the numbered SQL chain and the ADDENDUM layering already are an object structure — this names them so a build, an update and an addon purchase become decidable.

## The split

**Core — 17 skills** plus `shared/`, `security/`, `cron/`, `templates/`.

The split isn't taste. `shared/` is referenced by 105 distinct sources, more than every skill combined; `07-context-architect` has an in-degree of 20. Anything with that fan-in is core by definition — an addon able to modify it would be an addon able to break every other addon.

| Addon | Skills | Gates | Flows | Migrations |
|---|---|---|---|---|
| **Interview and Offer** | 1 | 0 | 4 | — |
| **Outreach and Prospecting** | 3 | 11 | 6 | 14, 15, 19, 20 |
| **Career Direction** | 2 | 1 | 2 | 6, 16 |
| **Public Presence** | 2 | 2 | 2 | 17, 18 |

Outreach is the heaviest by some distance: **11 of the 38 gates, including 5 of the 11 irreversible-external ones.** Its permission packs have to install and uninstall atomically with it, and its spending gates must go *dormant* rather than permissive when it expires. An expired addon that leaves a send path open is the worst bug available in this system.

## The packaging problem, measured

**19 references run from a core skill to a skill that belongs in an addon.** Plus 5 cross-pack addon-to-addon references. Every one of them dangles when that addon is absent — and a dangling reference in a markdown skill *does not error*. It produces a skill that reads convincingly and silently does less. That is exactly the `FLOW-H4` partial-install failure mode, except it arrives through the front door as a legitimate purchase.

The wrong fix is shuffling skills until the graph looks clean — that puts interview prep in core because the orchestrator happens to mention it, and you have no addons left to sell.

**The right fix is a capability contract.** Core never names an addon skill. It names a capability, checks whether it is present, and has defined behaviour when it is not — and that behaviour must be a real path, never an error and never silence.

| Capability | Provided by | Core references | When absent |
|---|---|---|---|
| `interview_prep` | addon-interview | 3 | interview_request_at is still recorded and the outcome still counts in analytics. |
| `social_listening` | addon-outreach | 4 | Discovery runs on its configured sources only. |
| `cold_outreach` | addon-outreach | 3 | Company research still runs and still caches — it has standalone value for applications and interviews. |
| `contact_enrichment` | addon-outreach | 1 | No lookups run. |
| `career_planning` | addon-direction | 4 | The target profile is still confirmed and edited normally. |
| `interests_profile` | addon-direction | 4 | Resume and cover-letter generation proceed without the interests source. |

Two of these are worth reading closely. **`company_research` stays in core** even though outreach leans on it, because it has standalone value for applications and interviews — an unlicensed user still gets researched applications. And **`interests_profile` absent does not disable `GATE-SENSITIVE-DISCLOSURE`**: sensitive entries may already exist from a previous licence period, and a non-negotiable gate does not expire with a subscription. The checker raises that as a warning every run, deliberately, so nobody quietly changes it.

## Degradation contracts

Decided now, per addon, because it is a schema question and not a billing one.

**Interview and Offer** — Prep briefs, flashcard decks and interviewer research are retained and remain readable. New briefs stop being generated; the interview-invite cron stops firing. interview_request_at is still recorded by core, so nothing is lost and everything resumes on repurchase.

**Outreach and Prospecting** — Pitch catalog, contact records, outreach history and reply threads are retained and readable. No new messages are drafted or sent, listening crons stop, enrichment stops. Spending gates go dormant rather than permissive — an expired addon must never leave a send path open.

**Career Direction** — Saved plans and the interests profile are retained and readable. No new plans are generated. GATE-SENSITIVE-DISCLOSURE remains active for as long as any sensitive entry exists, whether or not the addon is licensed — a non-negotiable gate does not expire with a subscription.

**Public Presence** — A published portfolio page stays published — it is on the user's own hosting and taking it down is not the vendor's decision. The manifest, artefact records and audit history are retained and readable. No new builds, no republishing, no link-rot checks.

One that isn't obvious: a **published portfolio page stays published**. It is on the user's own hosting, and taking someone's page down because a subscription lapsed is not a decision a vendor gets to make.

## Migrations

One chain, `applications_db_schema.sql then addendum.sql then addendum_2 .. addendum_20`. Next number is **21**. Every addon that adds tables takes the next number in the same chain — no parallel chains, no addon-local databases. That single shared history is why an addon can add a table core analytics later reads.

### Correction: the chain is sound; the check is not

An earlier draft of this document claimed `schema_version` was created in
addendum 7 and that addenda 1–6 recorded nothing. **That was wrong.** Addendum 7
backfills the base schema plus 1, 2, 4, 5 and 6 at the moment it creates the
ledger, and every migration from 8 to 20 records itself. `_3` is deliberately
excluded because `_4` supersedes it and asserting it would be a guess. Credit
where due — this was already designed correctly.

The residual risk is narrower and real: **the backfill asserts rather than
verifies.** It writes "these ran" without checking their tables and columns
exist, on the reasonable assumption that ordering discipline held. That
assumption is fine while you are the only installer. It stops being fine the
moment you ship, because an install interrupted mid-chain — or a restore from a
partial backup — records a clean history over a database missing objects, and
nothing notices until an unrelated query fails weeks later on a machine you
cannot inspect.

**Fix: `addendum_21` verifies instead of backfilling.** It checks every recorded
migration's objects exist by name and writes a drift report.

## Addendum layering — the update mechanism

An addon or update modifies core behaviour by shipping an ADDENDUM that layers over a host file **at load time**, never by editing the host file. Precedence, later winning:

1. core skill body
2. core addendum (shipped by a core update)
3. addon addendum, in addons[] declaration order
4. user override

- An addendum declares `host:` (the file it layers over) and `min_host_version:`.
- An addendum may add sections and replace named sections. It may not delete a section another addendum depends on.
- Two addenda replacing the same named section is a build error, not a last-one-wins silent resolution.
- Addenda are applied at load, never merged into the host on disk.

### Shipped addenda are never absorbed

27 files under `_merge-history/` are referenced by nothing live — they were absorbed into their host files during development and their originals are now unreachable. That is fine for one developer consolidating their own work. For a shipped addon it is fatal: once an addon's changes are folded into a core file, the next core update overwrites them and **the customer's paid feature silently disappears**. They will not report it as a bug; they will report that the tool got worse.

## Build pipeline

**1. validate** — run: extract_graph.py, check_gates.py, check_flows.py, check_manifest.py

**2. strip_rationale** — The single highest-value protection step, and it costs nothing. The long "why this design and not that one" prose inside each SKILL.md, the merge history and the audit files carry most of the intellectual value and none of the runtime function. The agent needs the instruction, not the reasoning behind it. Full versions stay in the private repo.

**3. compile_scripts** — Nuitka over the .py files. Markdown must stay readable to the agent; scripts need not be.

**4. watermark** — Per-licence invisible markers — whitespace patterns, comment ids, a per-seat salt in a config value. A leaked copy is traceable to the buyer. Against a few hundred users this deters sharing better than any obfuscation, because it is social rather than technical.

**5. sign** — Detached signature over the built tree; the client verifies before install.

**6. package** — run:

`strip_rationale` is the one to weight most heavily, and it costs nothing. The long "why this design and not that one" prose inside each SKILL.md, the merge history, the audit files — they carry most of the intellectual value and none of the runtime function. The agent needs the instruction, not the reasoning behind it. Stripping them cuts what a reader learns from a leaked copy by more than any encryption would, and the full versions stay in your private repo where they're still useful to you.

Skills are fetched at activation against a valid licence rather than shipped in the installer, so there is nothing to forward before activation. Licence checks happen server-side at ledger call time — never as a client-side boolean, which gets patched out in an afternoon.

## Where this leaves the build order

| | Status |
|---|---|
| Dependency graph | done — 247 nodes, 2,366 edges |
| Gate registry | done — 38 gates, 4 classes, 8 packs |
| Settings registry | done — 111 keys, 22 user-facing |
| Flow catalog | done — 38 flows, 8 axes, full coverage |
| Manifest and packaging | done — this file |
| Federated self-improvement | next |

Five checkers now keep the whole thing honest: `extract_graph.py`, `check_gates.py`, `extract_settings.py`, `check_flows.py`, `check_manifest.py`. Run them on every change and drift shows up as a build failure rather than as a wrong sentence in the manual or a broken feature in a paying customer's install.

### Six things to fix before packaging, in order

1. **`profile_stage` has no config field** — blocks `FLOW-A2` entirely; first-time entrants silently get the experienced track.

2. **`addendum_21`** — backfill `schema_version` so migration state is provable.

3. **Convert the 19 core-to-addon references** to capability checks.

4. **`social_listening` missing from the `sources.yaml` type enum** — a documented source type no validator would accept.

5. **Confirm `daily_staging_cap` is actually read** — it appears in no file but its own, and it is the last thing standing between a bug in auto-approve mode and a day of unreviewed output.

6. **Surface the container-backend caveat in the install check** — a container terminal backend silently disables one of Rule 1's three enforcement layers.
