# Preflight — six fixes before packaging

In dependency order. Each states the evidence, the fix, and how you know it
worked. Every one was found by a checker, not by reading.

---

## 1. `profile_stage` has no config field  ·  BLOCKING

**Evidence.** Read by eight components — `03`, `05`, `06`, `07`, `09`, `19`,
`20` and `dry-run.py`. It is the first question onboarding asks. It routes the
whole first session down one of two tracks and pre-sets the match thresholds to
55/35 rather than 70/50, because entry-level postings systematically overstate
their own requirements. `shared/target-profile.yaml` does not contain it.

**Consequence.** `FLOW-A2` never runs. A first-time entrant silently gets the
experienced track and a bar tuned for someone with a career, and sees almost
nothing. It is the first thing a new user hits and the worst first impression
available.

**Fix.** Add to `shared/target-profile.yaml`, immediately above `seniority_band`
since it gates the interpretation of that field:

```yaml
# Asked first at onboarding — it routes the whole first session and pre-sets
# the match thresholds in dynamic-target-calibration.yaml. Confirmed the same
# way as every other field here; never hand-edited.
#   experienced - prior paid work history to draw on
#   first_time  - entering the workforce, or switching with no prior history
#                 in the target field. Pre-sets minimum 55 / stretch floor 35.
profile_stage: ""
```

Plus `applications.profile_stage`, which `addendum_21.sql` adds — so analytics
can segment the funnel by it. A first-time entrant's baseline response rate is
a different population, and pooling the two makes both numbers wrong.

**Verify.** `python3 extract_settings.py` shows `profile_stage` with a file and
readers rather than appearing under *documented but no config key*.

---

## 2. `addendum_21.sql` — verify the migration ledger  ·  BLOCKING

**Correction first.** I earlier claimed `schema_version` was created in
addendum 7 and that 1–6 recorded nothing. **That was wrong**, and the design was
already right: addendum 7 backfills the base schema plus 1, 2, 4, 5 and 6 when
it creates the ledger, and every migration from 8 to 20 records itself. `_3` is
deliberately excluded because `_4` supersedes it and asserting it would be a
guess.

**The real, narrower issue.** The backfill *asserts* rather than *verifies*. It
writes "these ran" without checking their tables and columns exist, on the
reasonable assumption that ordering discipline held. Fine while you are the only
installer. Not fine once you ship: an interrupted install or a partial restore
records a clean history over a database missing objects, and nothing notices
until an unrelated query fails weeks later on a machine you cannot inspect.

**Fix.** `addendum_21.sql` — ships `schema_expected` (one row per object a
migration is responsible for) and `schema_drift`, then cross-checks the ledger
against `sqlite_master`. Tested against a deliberately incomplete database: it
correctly flags addendum 4 as recorded-but-missing.

Column checks need `PRAGMA table_info`, which SQL cannot express portably, so
`install-check.py` reads `schema_expected WHERE kind='column'` and writes its
findings back into `schema_drift`.

**From here on, every migration appends its own `schema_expected` rows as well
as recording itself.** A migration that declares nothing cannot be verified.

**Verify.** `SELECT * FROM v_schema_problems` returns nothing on a healthy
install.

---

## 3. Convert 19 core-to-addon references to capability checks

**Evidence.** `check_manifest.py` counts 19 references from a core skill to a
skill that lives in an addon, plus 5 cross-pack references.

**Consequence.** Each dangles when that addon is not licensed — and a dangling
reference in a markdown skill does not error. It produces a skill that reads
convincingly and quietly does less: the same failure mode as a partial install,
arriving through the front door as a legitimate purchase.

**Fix.** Core never names an addon skill. It names a capability, checks whether
it is present, and has defined behaviour when it is not — behaviour that must be
a real path, never an error and never silence.

| Core skill | Names | Replace with | Where |
|---|---|---|---|
| `00-orchestrator` | `13-interview-prep` | `capability:interview_prep` | prose |
| `00-orchestrator` | `19-career-path-planner` | `capability:career_planning` | prose |
| `01-job-discovery` | `14-social-discovery-outreach` | `capability:social_listening` | frontmatter |
| `05-resume-customizer` | `20-interests-profile` | `capability:interests_profile` | prose |
| `07-context-architect` | `13-interview-prep` | `capability:interview_prep` | prose |
| `07-context-architect` | `19-career-path-planner` | `capability:career_planning` | prose |
| `07-context-architect` | `20-interests-profile` | `capability:interests_profile` | frontmatter |
| `09-risk-tactics-gate` | `20-interests-profile` | `capability:interests_profile` | prose |
| `10-approval-and-submit` | `19-career-path-planner` | `capability:career_planning` | prose |
| `12-company-research` | `13-interview-prep` | `capability:interview_prep` | frontmatter |
| `12-company-research` | `17-cold-prospecting` | `capability:cold_outreach` | frontmatter |
| `16-career-pulse` | `14-social-discovery-outreach` | `capability:social_listening` | prose |
| `16-career-pulse` | `17-cold-prospecting` | `capability:cold_outreach` | prose |
| `16-career-pulse` | `19-career-path-planner` | `capability:career_planning` | frontmatter |
| `16-career-pulse` | `20-interests-profile` | `capability:interests_profile` | frontmatter |
| `16-career-pulse` | `22-contact-enrichment` | `capability:contact_enrichment` | prose |
| `18-skill-composer` | `14-social-discovery-outreach` | `capability:social_listening` | prose |
| `21-output-templates` | `14-social-discovery-outreach` | `capability:social_listening` | prose |
| `21-output-templates` | `17-cold-prospecting` | `capability:cold_outreach` | frontmatter |

Twelve are in prose and seven are `related_skills:` frontmatter. The frontmatter
ones matter more than they look: addon compatibility is computed from exactly
that metadata.

**Verify.** `python3 check_manifest.py` reports 19 references covered by
contracts and no FAIL lines.

---

## 4. `social_listening` missing from the `sources.yaml` type enum

**Evidence.** `14-social-discovery-outreach` opens by describing it as *a new
source type* extending discovery's sources. The shipped template lists nine
types and this is not among them.

**Consequence.** Anyone configuring a source has no way to know the value is
valid, and any validator written against that enum rejects it.

**Fix.** Add it to the enum, and mark it capability-gated so an unlicensed
install skips a configured entry with a notice rather than failing validation:

```yaml
type: linkedin_search_url   # linkedin_search_url | indeed_search_url | rss |
                            # email_label | google_dork | scrape_and_filter |
                            # export_file | aggregator_api | open_web_search |
                            # social_listening (requires capability:social_listening
                            # — skipped with a notice when unavailable)
```

---

## 5. Confirm `daily_staging_cap` is actually read

**Evidence.** The key appears in no file except `tier-config.yaml` itself.
Rule 3 rests on the daily cap, the orchestrator enforces it, the README
describes it — but nothing names the key.

**Consequence.** Either the orchestrator reads it under another name, or the
enforcement reads a different value. Until that is resolved you do not know
whether the cap is live.

**Why this is blocking despite looking cosmetic.** The cap is the last thing
standing between a bug in auto-approve mode and a full day of unreviewed
applications going out under a user's name. `gates.yaml` sets `cap_applies:
true` on every toggleable sending gate and `check_gates.py` enforces it — but
that enforcement is only as real as the key being read.

**Fix.** Trace it, then make it explicit in the orchestrator's cap check. If
`hermes config set jobhunting.tier` is the intended path, wire that key properly
rather than leaving both routes half-described.

---

## 6. Surface the container-backend caveat in the install check

**Evidence.** A container terminal backend causes Hermes to treat the container
boundary as the security boundary and skip dangerous-command approval inside it.

**Consequence.** That removes one of Rule 1's three enforcement layers. It
protects the host machine and does nothing to stop an unreviewed application
reaching an employer — and nothing currently tells the user it happened.

**Fix.** `install-check.py` detects the backend and reports, in plain language,
which protections are and are not active. Not a refusal to run — containers are
a sensible deployment. The silent change in protection level is the problem, not
the container.

---

## Order, and why

**1 and 2 are blocking.** 1 breaks first run for an entire class of user; 2
makes every later update unverifiable. **3** is the largest change and gates the
whole addon model. **4** is a one-line fix on the same surface as 3, so do them
together. **5** must resolve before any sending gate ships as toggleable. **6**
is a message rather than a mechanism, but it is the difference between a user
knowing their protection level and assuming it.

## Files

| File | What it is |
|---|---|
| `addendum_21.sql` | Fix 2, plus `applications.profile_stage` for fix 1 |
| `check_manifest.py` | Verifies fix 3 |
| `extract_settings.py` | Verifies fix 1 |
