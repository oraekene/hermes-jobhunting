-- applications_db_schema_addendum_21.sql
--
-- Two jobs, both preflight for shipping:
--   1. Verify the migration ledger against reality instead of trusting it.
--   2. Record profile_stage, which eight skills read and no config file holds.
--
-- Verification, not backfill. addendum_7's backfill ASSERTS that 1, 2, 4, 5, 6
-- ran; every migration from 8 onward records itself. That discipline is sound
-- and this file does not second-guess it. What it adds is a check that the
-- objects those migrations were supposed to create actually exist — because
-- once this ships you cannot open a customer's database and look.

-- ── 1. migration drift ─────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS schema_drift (
  checked_at TEXT NOT NULL DEFAULT (datetime('now')),
  migration  TEXT NOT NULL,
  object      TEXT NOT NULL,
  kind        TEXT NOT NULL,     -- table | column | index | view
  present     INTEGER NOT NULL,  -- 0 = recorded as applied but missing
  PRIMARY KEY (migration, object)
);

-- The expected-object map. One row per object a migration is responsible for.
-- Every future migration appends its own rows here as well as recording itself
-- in schema_version — a migration that declares nothing cannot be verified.
CREATE TABLE IF NOT EXISTS schema_expected (
  migration TEXT NOT NULL,
  object    TEXT NOT NULL,
  kind      TEXT NOT NULL,
  PRIMARY KEY (migration, object)
);

INSERT OR IGNORE INTO schema_expected (migration, object, kind) VALUES
  ('applications_db_schema.sql',            'applications',                    'table'),
  ('applications_db_schema.sql',            'weekly_metrics_snapshots',        'table'),
  ('applications_db_schema.sql',            'skill_self_edits',                'table'),
  ('applications_db_schema.sql',            'email_insights',                  'table'),
  ('applications_db_schema.sql',            'open_gaps',                       'table'),
  ('applications_db_schema_addendum.sql',   'social_outreach',                 'table'),
  ('applications_db_schema_addendum.sql',   'career_journal',                  'table'),
  ('applications_db_schema_addendum.sql',   'profile_monitor_events',          'table'),
  ('applications_db_schema_addendum.sql',   'interview_debrief',               'table'),
  ('applications_db_schema_addendum_2.sql', 'social_outreach.pitch_mode',      'column'),
  ('applications_db_schema_addendum_2.sql', 'social_outreach.catalog_entry_ids','column'),
  ('applications_db_schema_addendum_2.sql', 'social_outreach.target_type',     'column'),
  ('applications_db_schema_addendum_4.sql', 'career_path_plans',               'table'),
  ('applications_db_schema_addendum_4.sql', 'career_path_plan_stepping_stones','table'),
  ('applications_db_schema_addendum_4.sql', 'career_path_plan_roadmap_items',  'table'),
  ('applications_db_schema_addendum_5.sql', 'social_outreach.contact_priority','column'),
  ('applications_db_schema_addendum_5.sql', 'social_outreach.identification_confidence','column'),
  ('applications_db_schema_addendum_6.sql', 'applications.overqualification_gate','column'),
  ('applications_db_schema_addendum_6.sql', 'applications.title_delta',        'column'),
  ('applications_db_schema_addendum_6.sql', 'applications.comp_delta_pct',     'column'),
  ('applications_db_schema_addendum_7.sql', 'schema_version',                  'table');

-- Tables recorded as applied whose table is missing.
INSERT OR REPLACE INTO schema_drift (migration, object, kind, present)
SELECT e.migration, e.object, e.kind,
       CASE WHEN EXISTS (SELECT 1 FROM sqlite_master
                         WHERE type = 'table' AND name = e.object)
            THEN 1 ELSE 0 END
FROM   schema_expected e
JOIN   schema_version  v ON v.filename = e.migration
WHERE  e.kind = 'table';

-- Columns are checked by the caller via PRAGMA table_info, which SQL alone
-- cannot express portably. install-check.py reads schema_expected WHERE
-- kind='column' and writes its findings back into schema_drift.

CREATE VIEW IF NOT EXISTS v_schema_problems AS
SELECT migration, object, kind, checked_at
FROM   schema_drift
WHERE  present = 0;

-- ── 2. profile_stage ───────────────────────────────────────────────────────
--
-- Read by eight skills, asked first at onboarding, and it pre-sets the match
-- thresholds to 55/35 rather than 70/50 — but no config file ever held it.
-- Recording it here as well as in target-profile.yaml means analytics can
-- segment by it, which is the whole point of tracking a first-time entrant's
-- funnel separately: their baseline response rate is not the same population.

ALTER TABLE applications ADD COLUMN profile_stage TEXT;

CREATE INDEX IF NOT EXISTS idx_applications_profile_stage
  ON applications(profile_stage);

INSERT OR IGNORE INTO schema_expected (migration, object, kind) VALUES
  ('applications_db_schema_addendum_21.sql', 'schema_drift',              'table'),
  ('applications_db_schema_addendum_21.sql', 'schema_expected',           'table'),
  ('applications_db_schema_addendum_21.sql', 'applications.profile_stage','column');

INSERT OR IGNORE INTO schema_version (filename, note) VALUES
  ('applications_db_schema_addendum_21.sql',
   'Migration verification (schema_expected/schema_drift) and applications.profile_stage.');
