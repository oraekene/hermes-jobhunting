-- Addendum 14 — the stepping-stone engine
--
-- Addendum 4 gave career_path_plan_stepping_stones four working columns:
-- sequence_order, title, job_zone, status. That was enough to RECORD a
-- hop somebody had already decided on. It was not enough to generate
-- one, justify one, check one is reachable, or track what happens when
-- reality diverges from it — and Step 3's rule for producing hops was a
-- single bullet keyed off a job_zone delta.
--
-- See 19-career-path-planner/references/stepping-stone-engine.md for the
-- full method. What the schema has to hold, that it did not:
--
--   1. Candidate PATHS, not just the chosen one. One-three-one (S11)
--      means presenting three routes, and "why did I rule out the
--      direct path" is a question the record should still answer in a
--      year. Rejected candidates were previously discarded at
--      presentation time.
--   2. The two-sided scores. A hop is only a hop if it is reachable
--      from here AND closes gaps toward the target. Neither term
--      existed as a column.
--   3. The gaps a hop is FOR. Without these, 'achieved' can only mean
--      "he took the job", never "the job did what it was chosen to do."
--   4. Per-hop roadmap items. The roadmap was target-scoped, so on a
--      two-hop plan every item belonged to a role two moves away.
--   5. Statuses for skipped / substituted / matured. Real careers
--      produce all three constantly and the old enum could express
--      none of them.
--
-- Apply after applications_db_schema_addendum_13.sql.

-- 1. Candidate paths. The direct path is ALWAYS one of these rows, even
-- when a hop is recommended — the comparison is the point, and a
-- recommendation with nothing to compare against is not a choice.
CREATE TABLE IF NOT EXISTS career_path_plan_paths (
  id                  INTEGER PRIMARY KEY AUTOINCREMENT,
  plan_id             TEXT NOT NULL,
  path_label          TEXT NOT NULL,   -- 'direct' | 'recommended' | 'alternative'
  hop_count           INTEGER NOT NULL DEFAULT 0,   -- 0 = direct

  -- Scores for the path as a whole. Per-hop values live on the hop rows.
  reachability_score  REAL,
  bridge_value_score  REAL,
  residual_gap_count  INTEGER,
  est_total_months    INTEGER,         -- sum of hop dwell estimates.
                                       -- Qualitative. NOT a completion date,
                                       -- and never rendered as one.

  chosen              INTEGER NOT NULL DEFAULT 0,
  chosen_at           TEXT,
  rejection_reason    TEXT,            -- why this path was not taken. Free
                                       -- text on purpose: "costs 18 months
                                       -- for one gap" is the real reason and
                                       -- no enum holds it.
  -- Set when a path is regenerated per stepping-stone-engine.md §6.2.
  -- The superseded row is KEPT — the history is the point.
  superseded_by_path_id INTEGER REFERENCES career_path_plan_paths(id),

  created_at          TEXT NOT NULL DEFAULT (datetime('now')),

  FOREIGN KEY (plan_id) REFERENCES career_path_plans(plan_id)
);

CREATE INDEX IF NOT EXISTS idx_plan_paths_plan ON career_path_plan_paths(plan_id, chosen);

-- 2. Extend the hop table in place. Existing rows keep working: every
-- added column is nullable or defaulted, and the original four are
-- untouched.
--
-- SQLite has no ADD COLUMN IF NOT EXISTS. Re-running this file will
-- error on these ALTERs; that is a safe, visible no-op failure, not
-- corruption. Skip the ALTER block on a re-run.
ALTER TABLE career_path_plan_stepping_stones ADD COLUMN path_id INTEGER REFERENCES career_path_plan_paths(id);
ALTER TABLE career_path_plan_stepping_stones ADD COLUMN reachability_score REAL;
ALTER TABLE career_path_plan_stepping_stones ADD COLUMN bridge_value_score REAL;
ALTER TABLE career_path_plan_stepping_stones ADD COLUMN residual_gap_count INTEGER;
ALTER TABLE career_path_plan_stepping_stones ADD COLUMN rationale TEXT;
    -- Element-level evidence for both scores, per content-model-overlap.md
    -- §112-115: "strong overlap because [STAR entry] evidences [element],
    -- which this role rates as important". Never a bare number.

ALTER TABLE career_path_plan_stepping_stones ADD COLUMN estimated_dwell_months INTEGER;
ALTER TABLE career_path_plan_stepping_stones ADD COLUMN dwell_driver TEXT;
    -- WHICH gap sets the dwell. "One full annual planning cycle for
    -- budget ownership." Without this the number is unfalsifiable.

ALTER TABLE career_path_plan_stepping_stones ADD COLUMN salary_band_low REAL;
ALTER TABLE career_path_plan_stepping_stones ADD COLUMN salary_band_high REAL;
ALTER TABLE career_path_plan_stepping_stones ADD COLUMN comp_regression_accepted INTEGER NOT NULL DEFAULT 0;
    -- 1 = this hop pays below the current salary_floor and Kene said yes
    -- to that specifically, as its own question. Never inferred from
    -- accepting the plan as a whole.

ALTER TABLE career_path_plan_stepping_stones ADD COLUMN seniority_floor_exemption INTEGER NOT NULL DEFAULT 0;
    -- Addendum 13's seniority_floor would otherwise filter this hop out
    -- of discovery. Scoped exemption: honoured by 01-job-discovery ONLY
    -- for postings matching this hop's title, ONLY while the plan is
    -- active and searching. Dies with the plan.

ALTER TABLE career_path_plan_stepping_stones ADD COLUMN liquidity_count INTEGER;
ALTER TABLE career_path_plan_stepping_stones ADD COLUMN liquidity_probed_at TEXT;
    -- Live read-only census across configured sources, 90-day window.
    -- Nothing is queued by the probe. Below the configured threshold the
    -- hop is flagged, not dropped — a scarce role can still be right,
    -- and a thin local market undercounts network-filled roles.

ALTER TABLE career_path_plan_stepping_stones ADD COLUMN community_corroborated INTEGER NOT NULL DEFAULT 0;
ALTER TABLE career_path_plan_stepping_stones ADD COLUMN community_mention_count INTEGER;
ALTER TABLE career_path_plan_stepping_stones ADD COLUMN source TEXT NOT NULL DEFAULT 'primary';
    -- primary | community_reported. Mirrors Step 3-extended's tagging.
    -- Corroboration is DISPLAYED next to the score, never folded INTO it.

-- Widened status. The old enum was not_started|in_progress|achieved,
-- enforced in prose rather than by constraint, so no migration is
-- needed — existing values remain valid.
--
--   not_started | in_progress | achieved | matured | skipped |
--   substituted | abandoned
--
-- The achieved -> matured split is the one that stops a plan closing
-- itself early: holding the role is not the same as having got what the
-- role was chosen for.
ALTER TABLE career_path_plan_stepping_stones ADD COLUMN matured_at TEXT;
ALTER TABLE career_path_plan_stepping_stones ADD COLUMN substituted_by_title TEXT;
ALTER TABLE career_path_plan_stepping_stones ADD COLUMN status_reason TEXT;
ALTER TABLE career_path_plan_stepping_stones ADD COLUMN linked_application_id INTEGER REFERENCES applications(id);
    -- The application that actually landed this hop, where one exists.
    -- Ties a plan to real pipeline outcomes rather than self-reported
    -- progress.

CREATE INDEX IF NOT EXISTS idx_stepping_stones_path ON career_path_plan_stepping_stones(path_id, sequence_order);
CREATE INDEX IF NOT EXISTS idx_stepping_stones_status ON career_path_plan_stepping_stones(status);

-- 3. What each hop is actually FOR. Without this table 'achieved' can
-- only ever mean "he took the job".
CREATE TABLE IF NOT EXISTS career_path_plan_hop_gaps (
  id                 INTEGER PRIMARY KEY AUTOINCREMENT,
  stepping_stone_id  INTEGER NOT NULL REFERENCES career_path_plan_stepping_stones(id),
  requirement_text   TEXT NOT NULL,
  gap_class          TEXT NOT NULL,   -- role_gated | credential_gated |
                                      -- tenure_gated | self_closable
                                      -- (see engine doc §1)
  provides_evidence  TEXT,            -- the O*NET task / market_signal on the
                                      -- hop's own record showing it structurally
                                      -- grants this. Evidenced, not assumed.
  evidenced_at       TEXT,            -- NULL until Kene confirms he now has it.
                                      -- All non-null => the hop can mature.
  evidence_ref       TEXT,            -- STAR entry / journal entry / domain-
                                      -- knowledge entry that confirmed it

  FOREIGN KEY (stepping_stone_id) REFERENCES career_path_plan_stepping_stones(id)
);

CREATE INDEX IF NOT EXISTS idx_hop_gaps_stone ON career_path_plan_hop_gaps(stepping_stone_id);

-- 4. Roadmap items become hop-scoped. One table, one query shape — NOT a
-- second roadmap system. hop_id NULL = the item belongs to the final
-- target, which is also the correct value for every pre-existing row.
ALTER TABLE career_path_plan_roadmap_items ADD COLUMN hop_id INTEGER REFERENCES career_path_plan_stepping_stones(id);
ALTER TABLE career_path_plan_roadmap_items ADD COLUMN gap_class TEXT;
    -- Same four classes. A role_gated item on the TARGET with no hop
    -- covering it is the engine's own miss, and is queryable as one.
ALTER TABLE career_path_plan_roadmap_items ADD COLUMN carries_forward INTEGER NOT NULL DEFAULT 0;
    -- Required by both a hop and the target. Highest-leverage items on
    -- the plan; the flag makes the reason legible rather than implicit
    -- in a rank number.

CREATE INDEX IF NOT EXISTS idx_roadmap_items_hop ON career_path_plan_roadmap_items(hop_id, status);

-- 5. Re-evaluation runs record whether they regenerated the path.
ALTER TABLE career_path_plan_reevaluations ADD COLUMN replanned_path INTEGER NOT NULL DEFAULT 0;
ALTER TABLE career_path_plan_reevaluations ADD COLUMN replan_trigger TEXT;
    -- hop_matured | hop_skipped | hop_substituted | career_pulse_cascade |
    -- taxonomy_change | annual_staleness (engine doc §6.2)

INSERT OR IGNORE INTO schema_version (filename, note) VALUES
  ('applications_db_schema_addendum_14.sql', 'stepping-stone engine: candidate paths, two-sided scoring, per-hop gaps and roadmap items, widened hop lifecycle');
