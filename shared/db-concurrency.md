# Database concurrency

Rules for writing to `shared/applications.db`. Every skill and every
subagent in this package is bound by them.

## The problem

`00-orchestrator/references/parallel-pipeline-sweep.md` fans subagents out
to build applications in parallel. Every one of them writes to a single
SQLite file. Across the whole package before this file existed, **WAL mode
was never mentioned, no transaction boundary was defined, and no busy
timeout was set.**

SQLite's default behaviour on a write that meets a held lock is to
**fail**, not to wait. It returns `SQLITE_BUSY` immediately.

So the failure mode is not corruption — SQLite is good at not corrupting
things. It is quieter and worse than that: a subagent's write silently
fails, its application never leaves `building`, and no stage picks it up
again. The pipeline's *own* stuck-batch check catches it roughly seven
hours later as an anomaly, which is the right safety net and the wrong
primary mechanism. Nothing should have failed in the first place.

One instance of this was found and fixed as a one-off — a sweep tick's
`WHERE` clause, recorded in `HERMES_UPGRADE_CHANGELOG.md`. The general
problem was never addressed. This file addresses it.

## The three settings

Set once, on every connection that writes.

```sql
PRAGMA journal_mode = WAL;      -- persistent: set once per database file
PRAGMA busy_timeout = 5000;     -- per connection: 5s, must be set every time
PRAGMA synchronous = NORMAL;    -- per connection, safe under WAL
PRAGMA foreign_keys = ON;       -- per connection; SQLite defaults it OFF
```

**`journal_mode = WAL` is a property of the file, not the connection.** Set
it once at install and it persists. Everything else has to be set on each
new connection, which is why it belongs in a helper rather than in a
README instruction people follow once.

WAL is what makes concurrent readers and one writer coexist: readers stop
blocking the writer and the writer stops blocking readers. `busy_timeout`
is what turns the remaining writer-vs-writer collision from an instant
failure into a short wait. Neither alone is sufficient — WAL without a
busy timeout still fails a second concurrent writer immediately, and a
busy timeout without WAL makes every reader a potential blocker.

`synchronous = NORMAL` is the documented safe pairing with WAL: it trades
a small durability window on power loss for a large write-throughput gain,
and losing the last few seconds of application state on a hard power cut
is a recoverable annoyance in this domain rather than a disaster.

`foreign_keys = ON` is unrelated to concurrency and is here because it is
the other per-connection pragma this package's schema assumes and SQLite
does not default. Fourteen addenda declare foreign keys that are, without
it, decorative.

Python helper — use this rather than `sqlite3.connect` directly:

```python
import sqlite3

def open_db(path, timeout_s=5.0):
    con = sqlite3.connect(path, timeout=timeout_s, isolation_level=None)
    con.execute("PRAGMA busy_timeout = 5000")
    con.execute("PRAGMA synchronous = NORMAL")
    con.execute("PRAGMA foreign_keys = ON")
    return con
```

`isolation_level=None` turns off the Python driver's implicit transaction
management, which is what lets the explicit `BEGIN IMMEDIATE` below
actually mean what it says. Left at its default, the driver opens
transactions at times of its own choosing and the ownership rule becomes
much harder to reason about.

## Row ownership — the rule that matters most

**A subagent owns exactly one `applications` row: the one for the
`application_id` it was dispatched with. It writes to that row and to
child rows keyed to it. It writes nothing else.**

This is the whole concurrency design. Pragmas reduce the cost of a
collision; ownership prevents most collisions from existing. Two
subagents that never touch the same row cannot contend for it regardless
of what SQLite is doing underneath.

What a delegated child may write:

| May write | May not write |
|---|---|
| Its own `applications` row | Any other `applications` row |
| `keyword_analysis`, `tactics_log`, `open_gaps`, `email_insights` rows keyed to its `application_id` | Anything aggregate: metrics rollups, `schema_version`, calibration state |
| `posting_sources` rows for its own posting | `career_path_plan_*` — a plan is never subagent-owned |
| — | Any row it did not create and was not dispatched to own |

Aggregate and cross-application work belongs to the parent, in a single
writer, after the batch reconciles. `11-analytics-and-learning` is a
parent-only stage for this reason and not by coincidence.

Include the ownership rule verbatim in every delegated child's `context`
field. `parallel-pipeline-sweep.md`'s "subagents know nothing" section
already establishes that a child cannot infer anything the parent does
not paste in, and this rule is no exception — a child that has not been
told it owns one row has no way to discover that it does.

## Transactions

Two shapes, and picking the wrong one is the most common way to
reintroduce the problem these pragmas solve.

**Single-statement writes need no explicit transaction.** SQLite wraps
them in one. Adding `BEGIN`/`COMMIT` around a lone `UPDATE` widens the
lock window for no benefit.

**Multi-statement writes that must land together use `BEGIN IMMEDIATE`.**

```sql
BEGIN IMMEDIATE;
  UPDATE applications SET status = 'staged' WHERE id = ?;
  INSERT INTO tactics_log (application_id, ...) VALUES (?, ...);
COMMIT;
```

`BEGIN IMMEDIATE`, not a bare `BEGIN`. A bare `BEGIN` starts a deferred
transaction that takes a read lock first and tries to upgrade to a write
lock at the first write — and an upgrade that fails **cannot be retried by
`busy_timeout`**, because the transaction is already holding a read lock
another writer needs. It returns `SQLITE_BUSY` immediately no matter how
long the timeout is. `BEGIN IMMEDIATE` takes the write lock up front,
where `busy_timeout` can do its job.

This is the single least-obvious rule in this file. A deferred transaction
looks more polite and is strictly worse under contention.

**Keep transactions short.** No network call, no LLM call, no file write
between `BEGIN` and `COMMIT`. A subagent that opens a transaction, calls a
model, and then commits holds the write lock for the length of an
inference. Build the values first, then open the transaction, then close
it.

## Status transitions are guarded, not assumed

Every status change asserts the state it expects to be moving from:

```sql
UPDATE applications
   SET status = 'building', building_started_at = datetime('now')
 WHERE id = ? AND status = 'discovered';
```

Then check the affected row count. Zero means something else already
moved the row, and the correct response is to skip the posting and log
it — never to retry, and never to force the transition. This is the
generalisation of the one-off `WHERE`-clause fix in
`HERMES_UPGRADE_CHANGELOG.md`: that fix was right, and it was applied to
one query rather than adopted as a rule.

## Failure semantics — what a half-built application is

The audit's other open finding, addressed here because it is the same
problem viewed from one stage later. The eight-stage pipeline had no
definition of what a row looks like when stage 6 fails.

`shared/applications_db_schema_addendum_15.sql` adds:

- **`status = 'failed'`** — a real terminal-until-retried state, distinct
  from `building` (in flight) and from `staged` (complete). Without it, a
  failed build and an in-flight build are the same row.
- **`build_attempts`** — incremented by the parent at dispatch, not by
  the child. A child that crashed cannot increment anything, which is
  precisely the case the counter exists to catch.
- **`last_failure_stage`** and **`last_failure_reason`** — which stage,
  and why, in the child's own words.
- **`build_artifacts_path`** — where partial output landed, so a rerun
  knows what already exists.

The rules:

1. **A rerun starts from stage 2, not from the failed stage.** Resuming
   mid-pipeline requires trusting artifacts produced by a run that
   demonstrably failed, and the stages are cheap relative to the cost of
   an application built on a half-parsed JD. Prior artifacts move to
   `build_artifacts_path` + `.failed-{n}/` rather than being deleted —
   they are the best available evidence of what went wrong.
2. **Three attempts, then stop.** At `build_attempts >= 3` the row stays
   `failed` and is surfaced to Kene once, with the reason. It is not
   retried again on any later tick. A posting failing three times is a
   signal about the posting or the pipeline, and burning tokens on a
   fourth attempt is not the response to it.
3. **`failed` rows do not block the queue.** They are skipped by the
   sweep's Phase 2 selection, which reads `discovered` only.
4. **A child never sets `failed` itself.** It reports the failure in its
   summary and leaves the row at `building`; the parent sets `failed`
   during Phase 1 reconciliation. A crashed child cannot report anything,
   so a status only a healthy child could set would be exactly wrong for
   the case that matters.
5. **The stuck-batch warning stays.** It now catches a narrower class —
   a child that vanished without the parent noticing — which is what a
   backstop should be catching.

## Where this is enforced

- `security/hooks/verify-db-ownership.py` — a `pre_tool_call` hook that
  blocks non-writer sessions from writing to the DB during an active
  sweep. Row ownership stops being instruction. See "Enforcement" below.
- `00-orchestrator/scripts/install-check.py` — fails CRITICAL if
  `journal_mode` is not WAL or the ownership hook is not registered, and
  warns if a sync-tool ignore file does not exclude the database.
- `00-orchestrator/references/parallel-pipeline-sweep.md`'s delegation
  template carries the ownership and outbox rules in each child's
  `context`. The hook is a backstop for that prompt, not a replacement —
  blocks appearing in the audit log mean the prompt is not landing.
- README install step 4 sets WAL immediately after the schema chain.

## The outbox — children do not write to the database

Everything above reduces the *cost* of write contention. The outbox
removes most of it, and it is what makes the enforcement hook below
workable rather than crippling.

**A delegated child writes no SQL. It writes one file.**

```
shared/.outbox/<application_id>.<attempt>.json
```

```json
{
  "application_id": 412,
  "attempt": 1,
  "session_id": "<child session>",
  "outcome": "staged",
  "wrote_at": "2026-07-31T14:22:09",
  "application_updates": { "status": "staged", "match_score": 78 },
  "child_rows": {
    "keyword_analysis": [ { "...": "..." } ],
    "tactics_log":      [ { "...": "..." } ],
    "open_gaps":        [ { "...": "..." } ]
  },
  "artifacts_path": "shared/builds/412/",
  "failure_stage": null,
  "failure_reason": null
}
```

The parent ingests the outbox in Phase 1 of the next tick — one session,
one connection, one transaction per file, in a loop. Reads stay direct
and unrestricted: a child queries the DB freely, because reads under WAL
contend with nothing.

**Why this is the right shape, not just a workaround:**

- **Write contention goes to approximately zero.** File creates in
  distinct paths do not contend at all. The database sees exactly one
  writer — the parent — which is what SQLite is good at. The throughput
  ceiling stops being a concurrency question.
- **`max_concurrent_children` is no longer bounded by write contention.**
  It is bounded by model spend and host resources, which are the limits
  that should actually govern it. The previous answer to write timeouts —
  "lower the concurrency cap" — was accepting a worse pipeline to work
  around a fixable design.
- **A crashed child leaves evidence.** An outbox file with no matching
  DB state is a complete record of what the child accomplished before it
  died. Compare the previous behaviour: a half-applied set of writes and
  nothing to reconstruct intent from. This makes addendum 15's
  `vanished` outcome genuinely diagnosable.
- **Ingestion is idempotent and re-runnable.** The file is the source of
  truth until consumed; a failed ingest can simply be retried. Consumed
  files move to `.outbox/consumed/` rather than being deleted, so a batch
  can be audited after the fact.
- **Ownership becomes structural.** A child that cannot write cannot
  violate row ownership. The rule stops depending on the child having
  read it.

**Ordering.** Ingest in `application_id` order, not filesystem order, so
a batch's effects are deterministic and a partially-ingested batch is in
a state you can reason about. One transaction per file — not one for the
whole batch — so a single malformed outbox file cannot roll back nine
good ones.

**Malformed or unparseable file:** move it to `.outbox/rejected/`, log
it, and set the application to `failed` with the reason. Never
half-apply, and never guess at what the child meant.

**Size.** An outbox file is small (kilobytes). If a child would produce
something large — a full resume draft, a research dossier — that goes to
`artifacts_path` on disk and the outbox carries the path. The outbox is a
transaction record, not a document store.

**The parent is still the only thing that can be a bottleneck**, and it
is a serial one: ingesting fifty outbox files is fifty short
transactions. At that scale it is milliseconds. If it ever stops being
milliseconds, batch the `child_rows` inserts with `executemany` within
each file's transaction — but measure before adding that, because it is
the kind of optimisation that is usually solving a problem nobody has.

## Enforcement — `security/hooks/verify-db-ownership.py`

Row ownership was instruction only. A child that ignored it, or never had
it pasted into its context — the likelier failure, since a subagent knows
only what the parent gave it — would write to another application's row
and succeed silently.

The hook makes it enforced, on the same footing as
`verify-submit-approval.py`. **During an active sweep, only the
registered writer session may write to `applications.db`.**

**Why that predicate and not a narrower one.** The obvious design is to
parse the SQL, extract the target `application_id`, and compare it
against the child's owned id. That is fragile in exactly the way that
gets a control quietly disabled: SQL arrives inside bash pipelines,
heredocs, Python one-liners and ORM calls, and a parser handling 90% of
that provides 0% of the guarantee, because the 10% it misses is where a
confused agent ends up. Detecting *write intent* in a blob of text is
tractable; detecting *which row* is not. The outbox is what makes the
coarse rule livable — a child has no reason to write, so denying it
writes costs nothing.

**How the sweep is signalled.** The parent writes
`shared/.db_writer_session.json` with its own session id and the
dispatched application ids at sweep start, and removes it at sweep end.
No marker means no enforcement: ordinary single-session work is
completely unaffected, which is the common case and should not pay for
this.

**It fails OPEN — the opposite of the submit hook, deliberately.** The
submit hook guards an irreversible external action, so a false negative
is unrecoverable and it fails closed. This one guards an internal
consistency property, and a false positive would block a legitimate write
mid-build, manufacturing precisely the half-built application addendum 15
exists to clean up. So: unparseable payload, missing session id, stale
marker, or a crash in the hook itself all allow the write and log it. The
only case it blocks is the unambiguous one — a sweep is active and this
session is definitively not the writer.

**Stale-marker guard.** A parent that dies mid-sweep would otherwise
leave the pipeline permanently unable to write. Markers older than 8
hours are ignored — longer than the sweep cycle plus margin, so it cannot
expire under a legitimately slow batch.

**Audit trail.** Every allow-with-reason and every block appends to
`shared/.db_write_audit.jsonl`. Worth reading after the first few sweeps:
blocks appearing there mean children are still trying to write, which
means the outbox instruction is not reaching them, which is a prompt
problem the hook is only masking.

## Syncthing and synced folders — read this before enabling WAL

**This is the one item here that can destroy data rather than merely
fail a write, and it applies to Kene's setup specifically.**

WAL mode creates two sidecar files next to the database:
`applications.db-wal` (committed transactions not yet checkpointed) and
`applications.db-shm` (a shared-memory index).

A file-level synchroniser — Syncthing, Dropbox, Google Drive, iCloud, and
anything else that replicates files independently — will treat those as
three unrelated files and sync them at three different moments. The
results range from bad to worse:

- **Torn state.** The `.db` arrives without its `-wal`, or with a `-wal`
  from a different instant. Committed transactions vanish or reappear.
- **`-shm` is not portable at all.** It is a shared-memory index whose
  contents are meaningless outside the host that created it. Copying one
  between machines is not a supported operation.
- **Conflict files.** Syncthing's response to a two-sided change is a
  `.sync-conflict-*` copy. For a document that is a nuisance; for a
  database it means one side's writes are silently gone and neither side
  is told.

This is worse than the failure mode WAL was adopted to fix. A failed
write is loud and recoverable; a torn database is neither.

**Do this:**

1. **Exclude the database and its sidecars from sync.** In Syncthing,
   add to the folder's `.stignore`:

   ```
   applications.db
   applications.db-wal
   applications.db-shm
   .outbox
   .db_writer_session.json
   .db_write_audit.jsonl
   ```

   `install-check.py` warns if it finds a `.stignore` in the tree that
   does not cover the database.

2. **If you want the data on another machine, sync a backup, not the
   live file.** `sqlite3 applications.db ".backup shared/backups/applications-$(date +%F).db"`
   produces a consistent single-file snapshot that is safe to replicate.
   Sync `shared/backups/`, never `shared/applications.db`.

3. **Do not run the pipeline on two machines against a synced copy.**
   Not "prefer not to" — the database is single-host state, and two
   Hermes instances writing to two replicas of it will diverge in ways no
   merge can fix.

## Is multi-host safety needed here? No — and that is a real answer

Worth settling rather than leaving as a caveat, because the honest answer
changes what you do about it.

**The concurrency case for it: none.** This pipeline has exactly one
writer by design — the parent, via the outbox. Its cron jobs run on one
Hermes instance. Nothing in it wants two hosts writing at once, and
building for that would mean a client/server database (Postgres) to
support a workload that has one writer. That is a large amount of
operational surface bought to solve a problem the design does not have.

**The case that is real, and is not about concurrency: replication.** A
Hermes agent on a cloud host with a laptop kept in sync is a normal and
sensible setup — it is how Kene's own environment is arranged, with
Syncthing between the two. The pull toward "make the DB work across
machines" comes from wanting the *data* in both places, not from wanting
concurrent writes.

Those are different problems and they have different answers. Backups
solve replication; nothing needs to solve concurrency.

So the position, stated plainly:

- **Single-host is the design, not a limitation to route around.** One
  machine owns `applications.db`. The Oracle Cloud instance is the
  natural choice — it is where the cron jobs run, and cron on the
  always-on host is the whole point.
- **Replicate a `.backup` snapshot, never the live file.** Consistent,
  single-file, safe to sync. Nightly is plenty.
- **Sync everything else freely.** Skills, references, YAML config,
  markdown memory, research caches, `builds/` artifacts — all of it is
  ordinary files with no locking semantics and no sidecars. The exclusion
  list is short and specific for a reason: the database and its
  companions, and nothing else.
- **If both machines truly need to act on the pipeline, use Telegram.**
  It already reaches the cloud instance from anywhere, which is what the
  laptop actually wants. Two write-capable installs is the thing to avoid.

The one genuine cost: the laptop cannot run the pipeline offline against
live data. Given that discovery, research and submission all need network
access anyway, that costs close to nothing.



- **Multi-host concurrent access.** See below — this is a deliberate
  non-goal rather than a gap, and the answer is not to make WAL work over
  a network filesystem.
- **A child writing to the DB through a tool the hook does not watch.**
  `WATCHED_TOOLS` in the hook is a list, and an unlisted tool passes
  through. Same caveat as the submit hook and the same fix: add it.
  Coverage of the tools that exist today is complete; coverage of a
  toolset you add tomorrow is your responsibility.
- **The parent violating its own rules.** The writer session is trusted
  absolutely. That is the correct place to put the trust — something has
  to be able to write — but it means a bug in parent-side ingestion is
  not caught by any of this.
