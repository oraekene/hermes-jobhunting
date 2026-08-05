-- Addendum 15 — failure semantics for a partially-built application
--
-- The pipeline is eight stages and had no definition of what a row looks
-- like when stage 6 fails. There was no 'failed' status, no attempt
-- counter, and no rule about what a rerun does with partial artifacts
-- already on disk.
--
-- What existed was good as far as it went: parallel-pipeline-sweep.md
-- formalised discovered -> building -> staged, told children not to mark
-- a failed build as staged, and surfaced anything stuck longer than a
-- sweep cycle as a warning. So a failure was VISIBLE. It was not
-- RESOLVABLE — a failed build and an in-flight build were the same row
-- in the same state, distinguishable only by how long they had sat
-- there.
--
-- See shared/db-concurrency.md for the rules these columns implement,
-- including the one that is not schema: a child never sets 'failed'
-- itself. It reports the failure and leaves the row at 'building'; the
-- parent sets 'failed' during reconciliation. A crashed child cannot
-- report anything, and a status only a healthy child could set would be
-- exactly wrong for the case that matters most.
--
-- Apply after applications_db_schema_addendum_14.sql.
--
-- NOT IDEMPOTENT — ALTER TABLE ADD COLUMN has no IF NOT EXISTS form in
-- SQLite. Running this twice errors on the ALTER block. That is a safe,
-- visible no-op failure, but run it once.

-- 'failed' joins the status vocabulary:
--   discovered -> building -> staged -> awaiting_approval ->
--       approved_sent | edited_then_sent | rejected_by_kene
--   building -> failed  (set by the PARENT, during reconciliation)
--   failed -> discovered (a retry, under the three-attempt cap)
--
-- Status is not constrained by CHECK anywhere in this schema and is not
-- constrained here either — consistent with the existing design, and it
-- keeps this migration from failing on installs holding legacy values.

ALTER TABLE applications ADD COLUMN build_attempts INTEGER NOT NULL DEFAULT 0;
    -- Incremented by the PARENT at dispatch. Deliberately not by the
    -- child: the child that most needs counting is the one that died
    -- before it could count anything.

ALTER TABLE applications ADD COLUMN building_started_at TEXT;
    -- Set in the same guarded UPDATE that sets status='building'. The
    -- stuck-batch check currently infers elapsed time from other
    -- columns; this makes it a direct read.

ALTER TABLE applications ADD COLUMN last_failure_stage TEXT;
    -- '02-jd-parser' ... '09-risk-tactics-gate'. Which stage, by name.

ALTER TABLE applications ADD COLUMN last_failure_reason TEXT;
    -- The child's own words. Free text on purpose — the useful reasons
    -- ("JD was a PDF with no text layer and OCR returned nine words")
    -- are not enumerable in advance, and an enum here would throw away
    -- the only diagnostic information the run produced.

ALTER TABLE applications ADD COLUMN last_failure_at TEXT;

ALTER TABLE applications ADD COLUMN build_artifacts_path TEXT;
    -- Where partial output landed. On a retry, prior artifacts are MOVED
    -- to <path>.failed-{n}/ rather than deleted: a rerun starts from
    -- stage 2 regardless (resuming mid-pipeline means trusting artifacts
    -- from a run that demonstrably failed), and the old artifacts are
    -- the best evidence of what went wrong.

CREATE INDEX IF NOT EXISTS idx_applications_failed
    ON applications(status, build_attempts);
CREATE INDEX IF NOT EXISTS idx_applications_building
    ON applications(status, building_started_at);

-- Per-attempt history. applications above holds only the LAST failure;
-- three attempts failing three different ways is the interesting case
-- and the columns above cannot express it.
CREATE TABLE IF NOT EXISTS application_build_attempts (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  application_id  INTEGER NOT NULL REFERENCES applications(id),
  attempt_number  INTEGER NOT NULL,
  started_at      TEXT NOT NULL DEFAULT (datetime('now')),
  ended_at        TEXT,
  outcome         TEXT,        -- 'staged' | 'failed' | 'abandoned' | 'vanished'
                               -- 'vanished' = the parent found it stale with
                               -- no report at all. Distinct from 'failed',
                               -- which means the child said so.
  failure_stage   TEXT,
  failure_reason  TEXT,
  delegated       INTEGER NOT NULL DEFAULT 0,
                               -- 1 if built by a subagent. Lets
                               -- 11-analytics-and-learning answer whether
                               -- the parallel sweep fails more often than
                               -- serial building — a question worth being
                               -- able to ask before trusting it at volume.
  artifacts_path  TEXT
);

CREATE INDEX IF NOT EXISTS idx_build_attempts_app
    ON application_build_attempts(application_id, attempt_number);

INSERT OR IGNORE INTO schema_version (filename, note) VALUES
  ('applications_db_schema_addendum_15.sql', 'failure semantics: failed status, attempt counter and per-attempt history');
