-- Addendum 13 — hired: pause, then resume at a higher tier
--
-- Two gaps, and the second is the interesting one.
--
-- GAP 1: nothing pauses. Kene accepts an offer and jobs 1, 2, 3, 10 and
-- 13 keep running. He gets a discovery digest on his first Monday at the
-- new job, and in-flight applications sit staged for roles he no longer
-- wants.
--
-- GAP 2: the calibration system is ASYMMETRIC and only bends one way.
-- auto_relax_schedule widens the net downward the longer a search runs
-- while unemployed. There is no inverse. Nothing narrows the net UPWARD
-- when Kene levels up: after two years as a Lead the pipeline will still
-- happily surface Analyst roles, because match_score does not know that
-- a role he could do easily is now a step backwards.
--
-- A tool for rising through a career needs the second half of that
-- schedule, not just a pause button.
--
-- Apply after applications_db_schema_addendum_12.sql.

CREATE TABLE IF NOT EXISTS pipeline_pause (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  paused_at         TEXT NOT NULL DEFAULT (datetime('now')),
  reason            TEXT,          -- 'accepted_offer' | 'manual' | 'other'
  accepted_app_id   INTEGER REFERENCES applications(id),
  resume_at         TEXT,          -- when the pipeline wakes itself
  resumed_at        TEXT,          -- NULL until it actually does
  paused_jobs       TEXT,          -- JSON array of cron job numbers stopped
  -- What the profile looked like at pause. The resume pass diffs against
  -- this to work out what actually changed, rather than asking Kene to
  -- remember two years later.
  profile_snapshot  TEXT
);

CREATE INDEX IF NOT EXISTS idx_pipeline_pause_resume ON pipeline_pause(resume_at, resumed_at);

-- Seniority floor. The upward counterpart to auto_relax_schedule's
-- downward widening: once Kene has held a level, roles below it stop
-- being surfaced as matches by default.
CREATE TABLE IF NOT EXISTS seniority_floor (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  effective_from TEXT NOT NULL,
  job_zone       INTEGER,        -- O*NET job zone actually held
  title_held     TEXT,
  comp_floor     REAL,           -- confirmed comp, the new salary_floor basis
  source_app_id  INTEGER REFERENCES applications(id),
  confirmed      INTEGER NOT NULL DEFAULT 0
  -- Rule 5: a floor is a durable career fact and Kene confirms it. It is
  -- also the one setting that can silently shrink discovery to nothing,
  -- so it is never inferred and applied in one step.
);

INSERT OR IGNORE INTO schema_version (filename, note) VALUES
  ('applications_db_schema_addendum_13.sql', 'pause on hire, resume at higher tier');
