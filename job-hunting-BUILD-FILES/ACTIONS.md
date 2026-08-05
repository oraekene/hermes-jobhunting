# Manual actions — what you do, in order

Answers to questions 1 and 2 first, then the runbook.

---

## Answers

**1. `licence_client.py`** — noted, that closes E6. No further action.

**2. Comparison of the two uploaded files:**

| File | Same as project copy? | Verdict |
|---|---|---|
| `build.py` | **No** — differs at lines 388–394 and 443–474 | **Newer, and it fixes more than you asked about.** It adds the entire `stamp-installer` command that I flagged as missing. It also already contains the corrected E7 audit: sentence-level measurement, a `most explanatory files` breakdown, and a "How to read this" block that states the measure's own limits. `build.py` is fully current — both E7 and the stamping gap are closed in it. |
| `manifest.yaml` | **Yes — byte-identical** (md5 `9e181d16…` on both) | **Not updated. E7 is still half-done here.** |

So the E7 prose correction did not land. `manifest.yaml` still carries **two** stale claims, and
`BUILD.md` carries a third:

- `manifest.yaml` line ~298, `strip_rationale.description`: still says *"an audit of the real
  package found 16 candidate headings across 16 files"* — the exact sentence the per-sentence
  measurement was written to replace.
- `manifest.yaml` line ~308, `watermark.description`: still says the mark is *"whitespace patterns,
  **comment ids**, a per-seat salt in a **config value**."* Both of those were **rejected** — comment
  ids sit in the token stream the agent reads and can surface in a customer's cover letter, and
  config values get rewritten within days so the mark degrades to a *wrong* seat. The `applies_to`
  and `note` fields directly below are correct; the description above them contradicts them.
- `BUILD.md` line 22: same "16 candidate headings across 16 files" claim.

Nothing breaks because of these — no checker reads a description field. But this is the same class
of defect (`compile_scripts` specced, not built) that `check_build.py` exists to catch, and anyone
reading the manifest to understand the design learns two things that aren't true.

---

# The runbook

Throughout, `PKG` = the project root directory.
Run everything from PowerShell. Substitute `python` for `python3` if that's what your install uses.

---

## Step 1 — Restore the directory structure of the build outputs ⚠️ do this first

**Why.** Every build output was downloaded into one flat folder. I can tell because the project
snapshot preserves subdirectories as underscores — `shared/applications_db_schema_20.sql` shows up
as `..._shared_applications_db_schema_20.sql`, two levels deep — but every build file shows up as
`job-hunting-BUILD-FILES_<basename>` with no intermediate segments. So `index.js`, `msg.py`,
`permissions.py`, `release.yml` and the rest are all sitting side by side at one level.

**What that breaks.** `check_build.py` looks for its test suites at specific relative paths:

```
shared/scripts/msg.py
shared/scripts/test_msg.py
permissions/scripts/test_permissions.py
federated/scripts/test_federated.py
```

None of those resolve in a flat folder, so `check_build.py` reports missing suites that are
actually present. The Worker won't deploy either — `wrangler.toml` expects `src/index.js`.

**Do this.** Rebuild the tree. Two destinations, and the split matters:

**(a) Files that ship inside the package** — move these into `PKG`:

```
PKG\permissions\SKILL.md                        (the SKILL.md currently sitting in the build folder)
PKG\permissions\scripts\permissions.py
PKG\permissions\scripts\test_permissions.py
PKG\permissions\references\arming-flow.md
PKG\shared\messages.yaml
PKG\shared\scripts\msg.py
PKG\shared\scripts\test_msg.py
PKG\federated\arms.yaml
PKG\federated\scripts\client.py
PKG\federated\scripts\aggregate.py
PKG\federated\references\how-it-works.md
PKG\gates.yaml
PKG\settings.yaml
PKG\flows.yaml
PKG\onboarding.yaml
PKG\patterns.yaml
PKG\manifest.yaml
PKG\graph.json
```

`manifest.yaml` confirms this: `registries: {gates: gates.yaml, settings: settings.yaml,
flows: flows.yaml, graph: graph.json}` are declared as package-root paths, and `permissions` is
listed as a **core skill** with `in_degree: 0`.

**(b) Files that stay in the build/infra folder** — keep in `job-hunting-BUILD-FILES\`, but restore
the worker and workflow nesting:

```
job-hunting-BUILD-FILES\worker\src\index.js
job-hunting-BUILD-FILES\worker\src\delivery.js
job-hunting-BUILD-FILES\worker\src\crypto.js
job-hunting-BUILD-FILES\worker\test\run.js
job-hunting-BUILD-FILES\worker\wrangler.toml
job-hunting-BUILD-FILES\.github\workflows\release.yml
```

Everything else — `build.py`, all six `check_*.py`, `extract_graph.py`, `build_docs.py`,
`apply_preflight.py`, `installer.py`, `test_installer.py`, `install-check.py`,
`test_install_check.py`, `simulate.py`, `sweep.py`, `bandit.py`, `unit_economics.py`, the three
server `.sql` schemas, `addendum_21.sql`, and all the `.md` specs — stays flat at the build folder
root. That's where they were.

**Verify:** `python3 check_build.py` from the build folder should stop complaining about missing
suites.

---

## Step 2 — Replace `build.py` with the version you just uploaded

The uploaded one is newer. Copy it over the project copy. Then confirm:

```powershell
python3 build.py --help
```

You should see `stamp-installer` in the list of commands. If you don't, you copied the wrong file.

---

## Step 3 — Fix the three stale claims (5 minutes)

**3a. `manifest.yaml`, `strip_rationale.description`.** Replace the first sentence and a half:

> ~~MEASURED, and less valuable than first assumed. An audit of the real package found 16 candidate
> headings across 16 files — the design reasoning is woven inline rather than sitting in liftable
> sections…~~

with:

> MEASURED, and less valuable than first assumed. A sentence-level audit of the real package found
> 696 explanatory sentences out of 4,476 (16%) against only 16 liftable sections — the design
> reasoning is woven inline rather than sitting in liftable blocks…

**3b. `manifest.yaml`, `watermark.description`.** Replace:

> ~~Per-licence invisible markers — whitespace patterns, comment ids, a per-seat salt in a config
> value.~~

with:

> Per-licence invisible markers — trailing-whitespace patterns only. Comment ids and config-value
> salts were both rejected: comments sit in the token stream the agent reads and can surface in a
> customer's generated document, and config values are rewritten within days so the mark degrades
> into a wrong seat rather than no seat.

**3c. `BUILD.md` line 22.** Same substitution as 3a.

**Then re-run** `python3 build.py audit --src <PKG>` and confirm the printed figures match what you
just wrote. If they don't, use the printed ones — the code is the source of truth, not my numbers.

---

## Step 4 — Add the unstamped-installer guard to `check_build.py`

Still missing. This is the guard that stops you shipping an installer that can't verify anything.

Add a function alongside the existing `check_stages` / `check_watermark_scope`:

```python
def check_installer_stamped(root: Path):
    dist = root / "dist" / "installer.py"
    if not dist.is_file():
        return                                   # nothing published yet, fine
    text = dist.read_text(encoding="utf-8")
    if 'os.environ.get("JH_PUBLIC_KEY", "")' in text:
        FAIL.append("dist/installer.py ships with no baked-in verification key — "
                    "run: build.py stamp-installer --public-key <base64>")
```

Call it from `main()` with the others. **Verify it works** by deliberately copying an unstamped
`installer.py` to `dist\installer.py` and confirming `check_build.py` fails. A guard you haven't
seen fire is a guard you don't have.

---

## Step 5 — Resolve `test_federated.py`

`check_build.py` lists `federated/scripts/test_federated.py` in its `SUITES` array. The file isn't
anywhere in the project. Two options:

- **If you have it** (21 tests were reported passing), put it at
  `PKG\federated\scripts\test_federated.py`.
- **If you don't**, delete that line from `SUITES` in `check_build.py` — but note you then have no
  test coverage on the federated client, and the six behaviours it was covering (a retired approach
  never re-chosen, an offline ledger not being an error, counts-only payloads, single-tier winners
  held back, thin cells inheriting, decay-triggered retirement) are all unverified.

I'd re-generate it rather than delete the line.

---

## Step 6 — Run the preflight patcher against your real package

```powershell
cd job-hunting-BUILD-FILES
python3 apply_preflight.py --root .. --dry-run
```

Read the output. Then:

```powershell
python3 apply_preflight.py --root .. --apply
```

**What it handles automatically (3 of 6):**

- **Preflight 1** — adds `profile_stage` to `shared/target-profile.yaml.template`. It tries three
  filename variants, so it'll find yours.
- **Preflight 2** — copies `addendum_21.sql` to
  `PKG\shared\applications_db_schema_addendum_21.sql`. I checked this path against how your
  existing addenda are actually named and it's correct — your chain really is flat under `shared/`.
  **`addendum_21.sql` must be sitting next to `apply_preflight.py` when you run it**, or it reports
  "not found" and skips.
- **Preflight 4** — adds `social_listening` to the `sources.yaml` type enum.

Every file it edits gets backed up to `<file>.pre21.bak` first, and it's idempotent — running twice
says "already present" rather than duplicating.

**Send me the dry-run output before you apply if you want a second pair of eyes on it.**

---

## Step 7 — The three preflight fixes that need your judgement

`apply_preflight.py` reports on these but won't touch them, because each needs a decision about
your own prose.

### 7a. Preflight 3 — convert 19 core→addon references to capability contracts

**Status: not started.** No `requires_capability` anywhere in the package.

`PREFLIGHT.md` §3 has the full table: which file, which line, which capability replaces it. **12 are
in prose, 7 are in `related_skills:` frontmatter.** The frontmatter ones matter more than they look
— addon compatibility is computed from exactly that metadata.

The confirmed frontmatter offenders:

| File | Declares | Should become |
|---|---|---|
| `12-company-research/SKILL.md` | `job-hunting-interview-prep` | capability `interview_prep` |
| `12-company-research/SKILL.md` | `job-hunting-cold-prospecting` | capability `cold_outreach` |
| `16-career-pulse/SKILL.md` | `job-hunting-interests-profile` | capability `interests_profile` |

Work through `PREFLIGHT.md` §3 file by file. The rule: **core names a capability, never an addon
skill, and always has a defined useful path when the capability is absent.** A dangling reference in
a markdown skill doesn't error — it produces a skill that reads convincingly and silently does less.

### 7b. Preflight 5 — trace `daily_staging_cap`

**Status: unchanged.** The key still appears in `shared/tier-config.yaml` and nowhere else in the
package.

Open `00-orchestrator/SKILL.md` and find where it enforces the daily cap. One of three things is
true, and you need to know which:

1. It reads the key under a different name → rename one side so they match.
2. It reads a hardcoded number → wire it to the key.
3. It doesn't actually enforce → that's the real bug, and it's the one that matters.

**Do not ship any sending gate as toggleable until this is resolved.** `gates.yaml` sets
`cap_applies: true` on every one of them and `check_gates.py` enforces that — but the enforcement is
only as real as the key being read. In auto-approve mode this cap is the only thing between a bug
and a day of unreviewed applications going out under a customer's name.

### 7c. Preflight 6 — install the new `install-check.py`

**Status: the package still ships the old one.** Different md5 from the rebuilt version; it has no
`check_environment` function and no container detection.

```powershell
copy job-hunting-BUILD-FILES\install-check.py PKG\00-orchestrator\scripts\install-check.py
```

Then run the test suite against it and confirm all 13 cases pass:

```powershell
python3 job-hunting-BUILD-FILES\test_install_check.py
```

---

## Step 8 — Full green run

From the build folder:

```powershell
python3 extract_graph.py          # regenerate graph.json against the now-patched package
python3 check_gates.py
python3 check_flows.py
python3 check_manifest.py
python3 check_onboarding.py
python3 check_patterns.py
python3 check_build.py
python3 build_docs.py             # the leak check
python3 test_install_check.py
python3 test_installer.py
python3 ..\permissions\scripts\test_permissions.py
python3 ..\shared\scripts\test_msg.py
python3 ..\shared\scripts\msg.py check
cd worker && node test\run.js
```

`extract_graph.py` first, because the preflight edits changed the frontmatter it reads and a stale
`graph.json` is a wrong one.

**Everything must pass before you build a bundle.** If `check_manifest.py` now complains about the
capability contracts, that's Step 7a talking to you.

---

## Step 9 — Only then: keys, stamp, deploy

```powershell
node worker\scripts\keygen.js          # generates the Ed25519 pair
python3 build.py stamp-installer --public-key <THE_BASE64_PUBLIC_HALF> --out dist\installer.py
python3 check_build.py                 # must now pass the Step 4 guard
```

Publish the printed sha256 next to the download link so a customer can check what they ran.

Then `DEPLOY.md` steps 3–6, plus the two things that document doesn't yet cover:

- **Create the ten Bachs products** — five SKUs × two currency variants (NGN-primary and
  USD-primary). The customer never sees a product id; your server picks from `cf-ipcountry`. That
  routing is what protects the 4.3× price gap.
- **Write the customer path into `DEPLOY.md`**, which is still missing: buy → licence key by email
  → download installer → `installer.py --key LIC-xxxx` → activated, downloaded, verified, checked.
  Right now the only occurrence of `LIC-` in that file is a negative test payload.

Also refresh `STATUS.md` — it has zero mentions of `installer`, `stamp`, `compile_scripts` or
`LEGAL`, so it still describes the pre-audit state.

---

## Summary of manual actions

| # | Action | Effort |
|---|---|---|
| 1 | Restore build-output directory structure | 30 min |
| 2 | Copy in the newer `build.py` | 1 min |
| 3 | Fix 3 stale claims (`manifest.yaml` ×2, `BUILD.md` ×1) | 5 min |
| 4 | Add unstamped-installer guard to `check_build.py`, prove it fires | 20 min |
| 5 | Restore or drop `test_federated.py` | varies |
| 6 | Run `apply_preflight.py` (preflight 1, 2, 4) | 10 min |
| 7a | Convert 19 core→addon refs to capabilities | 2–3 hrs |
| 7b | Trace `daily_staging_cap` | 30 min |
| 7c | Install new `install-check.py` | 5 min |
| 8 | Full checker run, all green | 20 min |
| 9 | Keygen, stamp, Bachs products, deploy | half a day |

Steps 1 and 7b are the two I'd not skip. Step 1 because every verification you run until it's done
gives you an answer about a folder layout rather than about your code. Step 7b because it's the only
item on this list where being wrong sends real applications to real employers.
