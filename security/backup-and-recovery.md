# Backup — what is worth saving, and what isn't

Job 8 currently offers a nightly SQLite dump, marked **optional**. That is
the wrong default for the system's only durable record, and it covers one
of several things worth saving. This is the full survey.

The organising question is not "is this important?" — nearly everything
here is. It is **"if this vanished, what would it cost to get back?"**
Three answers, three policies.

---

## Tier 1 — irreplaceable. Cannot be regenerated at any price.

| Artifact | Why irreplaceable |
|---|---|
| `shared/applications.db` | Every application, outcome, timestamp and correlation. It cannot be reconstructed from anything, and losing it silently degrades job 5's learning loop with no signal that anything is wrong. |
| `memory/*.md` — MEMORY, USER, career-timeline, domain-knowledge, star-story-bank, interests-profile | Built through dozens of elicitation conversations under Rule 5's confirm-before-write. Rebuilding means running every one of those interviews again, and the answers would not be identical. |
| **The skill files themselves** | Job 5 has been editing these under `write_approval` since install. After six months the `SKILL.md` bodies encode months of outcome-driven tuning that exists nowhere else. A fresh install gets you the package, not your version of it. |
| Holographic fact store (`~/.hermes/memory/`, outside this package) | The fact graph, trust scores, and contradiction history. Same argument as `memory/*.md` and easier to forget because it lives outside the skill tree. |
| Generated artifacts actually sent — resumes, cover letters, Q&A answers | The record of what an employer actually read. Needed for consistency across applications to the same company, and `13-interview-prep`'s claims map depends on it. Regenerating produces a *different* document, which is worse than useless: it looks like the record and isn't. |

**Policy: daily, versioned, off-machine, non-optional.** Versioned matters
more than frequency here. A corrupted database faithfully replicated to a
single backup slot is not a backup — the most likely failure for
`memory/*.md` is not disk loss but a bad write that nobody notices for a
week.

---

## Tier 2 — regenerable, but you pay for it. Sometimes in money.

| Artifact | Cost to rebuild |
|---|---|
| `shared/company_research_cache/` | A research pass per company. At a few hundred companies this is hours of crawling and real API spend. |
| `shared/individual_research_cache/` | **Direct money.** Tier 2/3 enrichment providers are metered — see `enrichment-tools-pricing.md`. Losing this cache means paying for lookups already paid for. The single strongest financial argument for backing anything up here. |
| `shared/interview_intel_cache/`, `role_transition_intel_cache/` | Hours of scrubbing across YouTube, Reddit, review sites. |
| `shared/question_bank.yaml` | The full crawl in `HOW-TO-RUN.md` — a multi-batch process with a human curation pass in the middle. |
| Title taxonomy `sqlite-vec` index | O*NET ingest plus embedding of every occupation profile. Deterministic, but slow and dependency-heavy. |
| `shared/*.yaml` config — target-profile, calibration, pitch-catalog, output-templates, discovery_queries, sources | Each was seeded through a conversation, not hand-filled. Small files, disproportionate rebuild cost. |
| `~/.hermes/pending/skills/` | Staged, unapproved edits. Small window, but losing them loses proposals you were mid-way through judging. |

**Policy: weekly, versioned, off-machine.** Lower frequency is fine because
the loss is bounded and measurable. Config YAML is small enough to ride
along with Tier 1 daily — no reason to be precious about a few kilobytes.

---

## Tier 3 — derived. Do not back these up.

| Artifact | Why not |
|---|---|
| qmd index | Rebuilt by `qmd embed` in seconds to minutes. |
| `shared/journal_export/` | A projection of `career_journal`. Backing it up creates a second copy that can drift from the source and looks authoritative when it isn't. |
| Any embedding cache | Deterministic from its input. |

Backing up derived data is worse than not doing it: it consumes the same
storage and attention as real backups while offering false reassurance.

**One trap worth naming.** `journal_export/` looks like a backup of the
journal. It is not, and the direction of the dependency makes it
dangerous: if `career_journal` were lost, the next export run *deletes*
the markdown to match, because wholesale semantics mean a month absent
from the DB is absent from the export. It follows the database down.

---

## What Tier 1 needs that a dump does not give you

**Versioning, not just copying.** Keep daily snapshots for a week, weekly
for a quarter. The realistic failure is a bad write discovered late, not a
dead disk.

**Restore verification.** A backup nobody has restored is a hypothesis.
Once a quarter, restore into a scratch directory and check that the
applications table has the row count you expect. Untested backups fail at
exactly the moment they are needed.

**Integrity before copying.** `PRAGMA integrity_check` on the SQLite file
before each snapshot. Copying an already-corrupt database over the last
good one is a way to lose data that has a backup system.

**Snapshot, don't copy a live file.** SQLite's `.backup` command, or
`VACUUM INTO`, rather than `cp` on a file that may be mid-write.

**Off-machine.** A backup on the same disk covers exactly one failure mode
and not the common ones.

**Encrypt at rest.** This holds a full résumé, contact details, salary
expectations, recruiter names, and enrichment data on third parties. Same
standard `security-setup.md` applies to the live data.

---

## Items — status

| # | Item |
|---|---|
| **BK1** | [**done** — job 8 rewritten, `security/scripts/backup.sh`] Make job 8 non-optional and rename it to reflect what it covers. Add `PRAGMA integrity_check` before the snapshot; use `VACUUM INTO`, not `cp`; refuse to overwrite the last good snapshot on a failed check. |
| **BK2** | [**done** — memory, skill tree, sent artifacts in the same snapshot] Extend Tier 1 beyond the database — `memory/*.md`, the skill tree, and the sent-artifact archive. Daily, versioned. |
| **BK3** | [**done** — Holographic fact store tarred from outside the skill tree] Back up the Holographic fact store. It sits outside the skill tree, which is exactly why it gets missed. |
| **BK4** | [**done** — job 8c, `security/scripts/backup-tier2.sh`] Weekly Tier 2 job for the research caches, question bank and taxonomy index. Justified by enrichment spend alone. |
| **BK5** | [**done** — 7 daily / 13 weekly / 12 monthly, pruned in-script] Retention policy: 7 daily, 13 weekly, 12 monthly. Prune on a schedule so backups don't become the thing that fills the disk. |
| **BK6** | [**done** — job 8b, `security/scripts/verify-restore.sh`] Quarterly restore verification, wired as a real cron job with a real assertion — not a line in a runbook. |
| **BK7** | [**done** — `BACKUP_GPG_RECIPIENT`; warns loudly when unset] Encrypt at rest, keyed through the same 1Password path `api-key-setup.md` already uses. |
| **BK8** | [**done** — qmd index and `journal_export/` excluded, with reasoning inline] Explicitly exclude Tier 3 in the backup script, with the reasoning inline so nobody helpfully adds them later. |
| **BK9** | [**done** — stated in `qmd-retrieval-layer.md`] State the `journal_export` trap in `qmd-retrieval-layer.md` — it is not a journal backup and will follow the database down. |
