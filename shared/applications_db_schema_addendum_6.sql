-- Addendum 6 — overqualification gate outcome
--
-- C1: Gate 2 in 03-resume-match needs a current O*NET job_zone and a
-- salary_floor. profile_stage: first_time has neither, and two other
-- stages can be missing one. A skipped axis must be distinguishable
-- from an evaluated-and-cleared one: those correlate very differently
-- against outcomes, and a NULL cannot tell them apart.
--
-- Apply after applications_db_schema_addendum_5.sql.

ALTER TABLE applications ADD COLUMN overqualification_gate TEXT;
-- 'clean' | 'flagged' | 'dropped' | 'skipped' | NULL (not yet reached)

ALTER TABLE applications ADD COLUMN overqualification_skip_reason TEXT;
-- e.g. 'no_job_zone', 'no_salary_floor', 'profile_stage_first_time'
-- NULL unless overqualification_gate = 'skipped'

ALTER TABLE applications ADD COLUMN title_delta INTEGER;   -- NULL when axis skipped
ALTER TABLE applications ADD COLUMN comp_delta_pct REAL;   -- NULL when axis skipped

CREATE INDEX IF NOT EXISTS idx_applications_overqual_gate
  ON applications(overqualification_gate);
