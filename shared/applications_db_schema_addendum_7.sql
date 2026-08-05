-- Addendum 7 — schema migration ledger (D2)
--
-- Seven migration files now apply in order, _3.sql is superseded by
-- _4.sql and must NOT run on a fresh install, and _4.sql drops a table
-- rather than converting it. Nothing recorded which had been applied.
-- On a second machine, or six months later, the only way to answer
-- "what state is this database in" was to inspect tables and guess.
--
-- Apply after applications_db_schema_addendum_6.sql.

CREATE TABLE IF NOT EXISTS schema_version (
  filename     TEXT PRIMARY KEY,   -- e.g. 'applications_db_schema_addendum_4.sql'
  applied_at   TEXT NOT NULL DEFAULT (datetime('now')),
  note         TEXT
);

-- Backfill for databases created before this ledger existed. Every one
-- of these was required to reach this point, so recording them is a
-- statement of fact, not an assumption. _3.sql is deliberately absent:
-- it is superseded, and if it WAS run historically that is worth
-- knowing, so add it by hand rather than having this file assert it.
INSERT OR IGNORE INTO schema_version (filename, note) VALUES
  ('applications_db_schema.sql',              'base'),
  ('applications_db_schema_addendum.sql',     'backfilled by addendum_7'),
  ('applications_db_schema_addendum_2.sql',   'backfilled by addendum_7'),
  ('applications_db_schema_addendum_4.sql',   'backfilled by addendum_7; supersedes _3'),
  ('applications_db_schema_addendum_5.sql',   'backfilled by addendum_7'),
  ('applications_db_schema_addendum_6.sql',   'backfilled by addendum_7'),
  ('applications_db_schema_addendum_7.sql',   'this ledger');

-- Every future migration ends with its own INSERT here. A migration that
-- does not record itself is a migration that will be run twice.
