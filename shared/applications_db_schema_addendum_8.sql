-- Addendum 8 — cross-source posting deduplication (D5)
--
-- The base schema already has a dedup key:
--   UNIQUE INDEX idx_dedupe ON applications(company, role_title, posting_url)
--
-- That key works for one source. Three now feed the same queue — job 1
-- (boards/feeds), job 2 (open-web sweep) and job 10 (social listening) —
-- and because posting_url is part of the key, the SAME job found on
-- LinkedIn, on the company careers page, and via a social post creates
-- three rows that all pass the uniqueness check. Every downstream stage
-- then runs three times: three JD parses, three resume customisations,
-- three entries in the daily cap under pipeline-rules Rule 3.
--
-- The fix is a URL-independent fingerprint. Uniqueness is deliberately
-- NOT enforced at the database level: existing installs may already hold
-- duplicate rows, and a UNIQUE index would make this migration fail on
-- exactly the databases that need it most. The skill does the lookup;
-- the index makes it fast.
--
-- Apply after applications_db_schema_addendum_7.sql.

ALTER TABLE applications ADD COLUMN posting_fingerprint TEXT;
-- lower(trim(company)) || '|' || normalised role_title || '|' || lower(trim(location))
-- Normalised role_title: lowercased, punctuation stripped, and the
-- seniority/level suffixes that vary by board removed ("(Remote)",
-- "- Contract", roman numerals, req IDs). 01-job-discovery owns the
-- normalisation rule; it lives with the skill, not in SQL, because it
-- needs the title taxonomy to do it well.

CREATE INDEX IF NOT EXISTS idx_applications_fingerprint
  ON applications(posting_fingerprint);

-- Every URL a given posting was seen at, and which source found it.
-- Kept as rows rather than a delimited column so "which source actually
-- produces applications that get replies" becomes answerable — that is a
-- question 11-analytics can use and currently cannot ask.
CREATE TABLE IF NOT EXISTS posting_sources (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  application_id INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
  posting_url    TEXT NOT NULL,
  source_name    TEXT,              -- e.g. 'linkedin', 'company_careers', 'x'
  discovered_by  TEXT,              -- 'job_1_boards' | 'job_2_openweb' | 'job_10_social'
  first_seen_at  TEXT NOT NULL DEFAULT (datetime('now')),
  is_canonical   INTEGER NOT NULL DEFAULT 0,  -- the URL actually applied through
  UNIQUE(application_id, posting_url)
);

CREATE INDEX IF NOT EXISTS idx_posting_sources_app
  ON posting_sources(application_id);

INSERT OR IGNORE INTO schema_version (filename, note) VALUES
  ('applications_db_schema_addendum_8.sql', 'cross-source posting dedup');
