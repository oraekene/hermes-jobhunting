-- Job-hunting pipeline database schema — Addendum 3 (career path planner)
-- Run after applications_db_schema_addendum_2.sql. One new table — the
-- plan document itself lives in shared/career_path_plans/{plan_id}.md
-- (same cache-file convention as company research); this table is only
-- for the progress-tracking state a static markdown file can't hold
-- well: per-item status over time.

CREATE TABLE IF NOT EXISTS career_path_plan_progress (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id               TEXT NOT NULL,     -- matches the
                                              -- shared/career_path_plans/
                                              -- {plan_id}.md filename
    target_title          TEXT NOT NULL,
    selection_mode        TEXT NOT NULL,     -- higher_seniority | adjacent |
                                              -- different | manual
    target_job_zone       INTEGER,
    current_job_zone      INTEGER,
    stepping_stone_titles TEXT,              -- JSON array, empty if a
                                              -- direct (single-hop) plan
    roadmap_items         TEXT NOT NULL,     -- JSON array of
                                              -- {item, status, leverage_rank}
                                              -- — status: open | in_progress |
                                              -- resolved
    created_at            TIMESTAMP NOT NULL,
    last_reevaluated_at   TIMESTAMP,
    status                TEXT NOT NULL DEFAULT 'active',
                                              -- active | achieved | abandoned
    achieved_at           TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_career_path_plan_status ON career_path_plan_progress(status);
