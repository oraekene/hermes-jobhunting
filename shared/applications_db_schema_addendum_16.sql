-- Addendum 16 — fact aging and supersession
--
-- last_confirmed_at existed in exactly four places before this: written
-- by 07-context-architect at Phase 0 and Phase 0.5, declared null in two
-- templates. NOTHING READ IT. The package had a timestamp on its facts
-- and no behaviour attached to it.
--
-- Meanwhile the memory model is append-only by design (Rule 5: facts are
-- added on confirmation, nothing silently overwrites), which is correct
-- and has one cost — a superseded fact and a current fact sit side by
-- side looking identical. Kene's salary floor from eighteen months ago
-- and from last week are both true statements that were confirmed, and
-- only one is true now.
--
-- Every other piece of memory work in this package sharpened RETRIEVAL:
-- the holographic layer, qmd, the taxonomy vector index, STAR-bank
-- compression. None of it makes stale facts stop being returned. Better
-- retrieval over unaged memory returns the wrong answer faster.
--
-- See 07-context-architect/references/fact-conflict-resolution.md.
--
-- WHY AN OVERLAY. The facts are not in this database. fact_store is a
-- Hermes-native tool with its own storage and no schema we can extend,
-- and the rest of the pipeline's memory is YAML and markdown. There is
-- no facts table to ALTER. Per-entry stamps in the memory files carry
-- most of the load; this table carries the metadata for fact_store
-- entries, where we cannot attach it directly.
--
-- The compromise is real: this can drift from fact_store if a fact is
-- deleted through the tool. Hence the reconcile pass below. The
-- alternative — writing aging metadata into the fact text itself, where
-- fact_store would index it as content — pollutes semantic search and
-- makes every probe noisier. A drift-prone sidecar that keeps retrieval
-- clean is the better trade, and the drift is detectable.
--
-- Apply after applications_db_schema_addendum_15.sql. Fully idempotent
-- (no ALTER TABLE), unlike _14 and _15.

CREATE TABLE IF NOT EXISTS fact_aging_overlay (
  id                 INTEGER PRIMARY KEY AUTOINCREMENT,

  -- Stable reference to the fact wherever it actually lives.
  fact_ref           TEXT NOT NULL UNIQUE,
      -- 'fact_store:<fact_id>' | 'yaml:target-profile.salary_floor' |
      -- 'md:interests-profile#kite-surfing'
  entity             TEXT NOT NULL,   -- 'Kene' | '<Project name>' | '<Company>'
  attribute          TEXT NOT NULL,   -- 'salary_floor' | 'visa_status' |
                                      -- 'current_title'
      -- Conflict detection is (entity, attribute) scoped and applies ONLY
      -- to attributes the schema treats as single-valued. "wants fintech"
      -- and "wants climate tech" are not a conflict — a person can want
      -- both, and treating preferences as single-valued is how a system
      -- talks itself into deleting true things.

  volatility         TEXT NOT NULL DEFAULT 'volatile',
      -- durable    — never reconfirmed unless contradicted (degrees, past
      --              employers, shipped projects, certifications). Most of
      --              the STAR bank. Asking Kene to reconfirm his degree
      --              annually trains him to click through confirmations
      --              without reading them, which costs more than it buys.
      -- volatile   — reconfirmed on the configured interval
      -- contextual — true only relative to one application; not aged

  last_confirmed_at  TEXT NOT NULL,
      -- Moves when KENE confirms, not when the pipeline reads or
      -- re-derives. A fact re-inferred from the same stale source is not
      -- fresher for having been looked at again.
  confirmed_via      TEXT,   -- 'phase_0' | 'reconfirmation_prompt' |
                             -- 'career_pulse' | 'offer_intake'

  superseded_by      INTEGER REFERENCES fact_aging_overlay(id),
  superseded_at      TEXT,
      -- Superseded, NEVER deleted. The row stays and drops out of default
      -- reads. "What did I think my floor was last year" is a real
      -- question, and a wrong supersession has to be recoverable.

  reconfirm_after_months INTEGER,
      -- NULL = use the class default from fact_aging config. Set only for
      -- facts needing a non-standard interval.

  created_at         TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_fact_aging_entity_attr
    ON fact_aging_overlay(entity, attribute, superseded_at);
CREATE INDEX IF NOT EXISTS idx_fact_aging_staleness
    ON fact_aging_overlay(volatility, last_confirmed_at);

-- Every supersession, with enough detail to reverse one.
CREATE TABLE IF NOT EXISTS fact_supersession_log (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  superseded_id     INTEGER NOT NULL REFERENCES fact_aging_overlay(id),
  superseding_id    INTEGER NOT NULL REFERENCES fact_aging_overlay(id),
  entity            TEXT NOT NULL,
  attribute         TEXT NOT NULL,
  old_value_summary TEXT,
  new_value_summary TEXT,
  resolved_by       TEXT NOT NULL,
      -- 'timestamp_rule'  — Rule 1 applied automatically
      -- 'kene_confirmed'  — a tie or near-tie he resolved himself
      -- 'reverted'        — a previous supersession undone
  reverted_at       TEXT,
  occurred_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_supersession_entity
    ON fact_supersession_log(entity, attribute, occurred_at);

-- RECONCILE PASS (run by cron job 14 alongside the plan re-evaluation,
-- or on demand). Not a table — a rule, recorded here because this is
-- where the overlay's one weakness is dealt with:
--
--   1. For every non-superseded row with fact_ref LIKE 'fact_store:%',
--      probe fact_store for that id. No result => the fact was deleted
--      through the tool. Mark the overlay row superseded with
--      resolved_by='reverted' and a reason, rather than leaving a stamp
--      pointing at nothing.
--   2. Report any fact_store entry with no overlay row as unaged. Do not
--      auto-create one — a default timestamp would be a fabrication, and
--      an unaged fact honestly labelled is better than a fact carrying a
--      confirmation date nobody ever gave.
--   3. Never write to fact_store from this pass. It reads only.

INSERT OR IGNORE INTO schema_version (filename, note) VALUES
  ('applications_db_schema_addendum_16.sql', 'fact aging overlay and supersession log — makes last_confirmed_at load-bearing');
