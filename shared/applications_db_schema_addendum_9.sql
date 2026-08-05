-- Addendum 9 — journal soft-delete with a grace window, and retention (D4)
--
-- Two problems, one mechanism.
--
-- PROBLEM 1: deletion is currently irreversible and immediate. A mistaken
-- delete is unrecoverable except from last night's backup.
--
-- The tempting fix is a shadow archive that never deletes. That is the
-- wrong answer, because there are two reasons an entry gets deleted and
-- they want opposite things:
--   (a) it was wrong  -> recovery is welcome
--   (b) it held something Kene does not want retained -> keeping a copy
--       somewhere he cannot see or reach is the exact opposite of what he
--       asked for, however well-intentioned the copy is
-- A permanent archive serves (a) and betrays (b). Backups already serve
-- (a) properly: versioned, encrypted, under Kene's control, and — the
-- part that matters — they EXPIRE. Recovery should be bounded, not
-- eternal.
--
-- So: soft-delete with a grace window. Behaviour changes immediately,
-- the row survives briefly, then it is really gone.
--
-- PROBLEM 2 (D4): career_journal grows without bound. Check-ins run three
-- times a week indefinitely; at two years that is ~300 entries feeding
-- every export, every embed and every semantic search.
--
-- Apply after applications_db_schema_addendum_8.sql.

ALTER TABLE career_journal ADD COLUMN deleted_at TEXT;
-- NULL = live. Set = soft-deleted; excluded from export and retrieval
-- IMMEDIATELY, hard-deleted after the grace window.

ALTER TABLE career_journal ADD COLUMN delete_reason TEXT;
-- 'mistake' | 'private' | 'superseded' | NULL
-- 'private' is the one that matters: it means hard-delete on schedule and
-- do not offer recovery prompts. Kene said remove it, not remind him.

CREATE INDEX IF NOT EXISTS idx_career_journal_deleted
  ON career_journal(deleted_at);

-- D4 — rolling summarisation. Old entries collapse into one row per
-- quarter rather than accumulating individually. Same principle as
-- 07-context-architect/references/star-bank-aging.md: detail decays with
-- age, recent stays verbatim, nothing becomes invisible.
CREATE TABLE IF NOT EXISTS career_journal_summary (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  period_start  TEXT NOT NULL,          -- 'YYYY-MM-DD'
  period_end    TEXT NOT NULL,
  entry_count   INTEGER NOT NULL,
  summary       TEXT NOT NULL,
  generated_at  TEXT NOT NULL DEFAULT (datetime('now')),
  source_ids    TEXT,                   -- JSON array of collapsed career_journal ids
  UNIQUE(period_start, period_end)
);

INSERT OR IGNORE INTO schema_version (filename, note) VALUES
  ('applications_db_schema_addendum_9.sql', 'journal soft-delete + retention');
