-- Addendum 20 — cron execution ledger
--
-- Twenty-three scheduled jobs, and nothing in the package reads whether
-- any of them ran. Every failure mode of a cron job is silent by
-- construction: a job that errors, a job whose schedule was never
-- registered, a job whose wake-gate skips every single tick, and a job
-- working perfectly on a quiet week all look identical from here --
-- nothing in the digest, nothing in the DB.
--
-- That is a specific problem for THIS package rather than a general
-- nicety. Jobs 1 and 9 carry wake-gates that deliberately suppress the
-- agent turn, and the gates FAIL OPEN. A gate that started erroring in
-- the skip direction would look exactly like a quiet market, and the
-- symptom -- postings sitting unseen -- is the thing 01-job-discovery
-- leads with as the cost it exists to avoid.
--
-- SKIPPED MUST BE DISTINGUISHABLE FROM DONE. This package already got
-- that right for gate outcomes (_6), journal soft-deletes (_9) and the
-- proposal-release rotation, and got it wrong exactly once
-- (last_used_at). So `outcome` is an explicit enum, never a NULL:
--
--   ran        -- the agent turn happened and completed
--   skipped    -- a wake-gate returned wakeAgent:false. NOT a failure;
--                 it is the gate doing its job and costing zero tokens
--   failed     -- the turn started and errored
--   gate_error -- the wake-gate itself errored. Fails open, so the agent
--                 still woke, but the CHEAP path is broken and the job is
--                 now paying full price on every tick. Distinct from
--                 'ran' precisely because the outcome looks identical
--
-- Deliberately NOT here: token cost. It is not reliably available at
-- this layer, and a column that is populated sometimes is worse than a
-- column that does not exist -- shared/cost-model.md owns spend.

CREATE TABLE IF NOT EXISTS cron_executions (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  job_label       TEXT    NOT NULL,          -- '1', '8b', '19' — matches cron/cron-jobs.md's headings
  job_name        TEXT,                      -- human label, for digests
  started_at      TEXT    NOT NULL,          -- ISO8601 UTC
  finished_at     TEXT,                      -- NULL while in flight
  outcome         TEXT    NOT NULL
                  CHECK (outcome IN ('ran','skipped','failed','gate_error')),
  detail          TEXT,                      -- error text, or the gate's reason for skipping
  UNIQUE (job_label, started_at)
);

CREATE INDEX IF NOT EXISTS idx_cron_exec_job_time
    ON cron_executions(job_label, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_cron_exec_outcome
    ON cron_executions(outcome, started_at DESC);

-- Expected cadence, so "has not run" is answerable rather than guessed.
-- A job absent from this table has never been registered at all, which is
-- a different failure from a job that ran and failed.
CREATE TABLE IF NOT EXISTS cron_job_expectations (
  job_label            TEXT PRIMARY KEY,
  job_name             TEXT NOT NULL,
  max_silence_hours    INTEGER NOT NULL,     -- longer than this without ANY row = stale
  skip_streak_warn     INTEGER NOT NULL DEFAULT 10  -- consecutive skips before flagging
);

INSERT OR IGNORE INTO schema_version (filename, note) VALUES
  ('applications_db_schema_addendum_20.sql', 'cron execution ledger + expected cadence');
