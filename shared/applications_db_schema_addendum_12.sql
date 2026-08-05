-- Addendum 12 — journal-derived features
--
-- The journal has been a pipeline INPUT: it feeds the STAR bank, the
-- career-event cascade, calibration. Almost none of its value to Kene
-- directly was built. These tables back the features that change that.
--
-- Apply after applications_db_schema_addendum_11.sql.

-- Recurring collaborators, derived from journal entries. Warm network,
-- which 17-cold-prospecting currently has no access to while it reaches
-- for cold contacts.
CREATE TABLE IF NOT EXISTS journal_collaborators (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  name           TEXT NOT NULL,
  first_seen_at  TEXT NOT NULL,
  last_seen_at   TEXT NOT NULL,
  mention_count  INTEGER NOT NULL DEFAULT 1,
  context_note   TEXT,          -- what they worked on together, in Kene's words
  confirmed      INTEGER NOT NULL DEFAULT 0,
  -- Names are extracted heuristically and CONFIRMED before use. An
  -- unconfirmed row is a candidate, never a contact — reaching out to
  -- someone on the strength of a name a regex found is the failure mode
  -- this column exists to prevent.
  UNIQUE(name)
);

-- Skills mentioned in journal entries over time. Feeds drift detection:
-- the resume still leads with something the work stopped involving.
CREATE TABLE IF NOT EXISTS journal_skill_mentions (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  skill         TEXT NOT NULL,
  period        TEXT NOT NULL,       -- 'YYYY-Qn'
  mention_count INTEGER NOT NULL DEFAULT 1,
  UNIQUE(skill, period)
);

-- Self-assessment / promotion-case documents generated from the journal.
-- Kept so a later one can reference what the previous one claimed.
CREATE TABLE IF NOT EXISTS self_assessments (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  period_start  TEXT NOT NULL,
  period_end    TEXT NOT NULL,
  purpose       TEXT,        -- 'performance_review' | 'promotion_case' | 'raise_case'
  document_path TEXT,
  generated_at  TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(period_start, period_end, purpose)
);

INSERT OR IGNORE INTO schema_version (filename, note) VALUES
  ('applications_db_schema_addendum_12.sql', 'journal-derived features');
