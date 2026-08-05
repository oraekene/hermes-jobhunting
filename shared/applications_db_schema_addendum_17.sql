-- Addendum 17 — fact influence, the second ranking dimension
--
-- Holographic gives every fact a trust score (0.0-1.0, default 0.5,
-- moved by fact_feedback). It is the only ranking dimension the provider
-- has, and it measures RELIABILITY — is this fact correct.
--
-- Nothing measured IMPORTANCE. "Kene's daughter is called Ada" can be
-- perfectly trustworthy and irrelevant to a job application; "Kene will
-- not relocate" is decisive. Both sat at 0.5, and wiring fact_feedback
-- on does not fix that — it makes trust scores move along the
-- reliability axis and only ever along that axis.
--
-- See 07-context-architect/references/fact-influence-scoring.md.
--
-- WHY EVENTS AND NOT A COUNTER. Influence is recomputed from events
-- every run rather than incremented in place. A running total drifts,
-- and it cannot implement the 180-day trailing window without a second
-- decay pass to undo itself. The events are the truth.
--
-- WHY NOT RETRIEVAL COUNTS. Those are trivially available and
-- completely misleading — the most-retrieved fact in any career memory
-- bank is something like a current job title, retrieved constantly and
-- deciding almost nothing. Only events where a fact CHANGED an output
-- are recorded here.
--
-- Apply after applications_db_schema_addendum_16.sql. Fully idempotent.

CREATE TABLE IF NOT EXISTS fact_influence_events (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  fact_ref        TEXT NOT NULL,
      -- Same addressing as fact_aging_overlay.fact_ref:
      -- 'fact_store:<id>' | 'yaml:...' | 'md:...' | 'star:<entry>'
  application_id  INTEGER REFERENCES applications(id),

  event_type      TEXT NOT NULL,
      -- gate_outcome     (weight 3) — supplied the evidence that passed a
      --                              claim through 09-risk-tactics-gate,
      --                              or was the reason one failed
      -- document_content (weight 2) — appeared in substance in a resume
      --                              bullet or cover-letter paragraph that
      --                              survived to 'staged'
      -- story_selected   (weight 2) — drove which STAR story was chosen
      --                              over an alternative
      -- posting_filtered (weight 1) — caused a posting to be dropped or
      --                              ranked down at Gate 1 or 2
      --
      -- Weights are ordinal, not measured. They encode one judgement —
      -- a changed GATE DECISION outranks appearing in prose, which
      -- outranks nudging a rank — and nothing finer. The ranking is
      -- insensitive to their exact values; treating them as calibrated
      -- would be false precision.

  weight          INTEGER NOT NULL,
  evidence_ref    TEXT,
      -- The tactics_log row, change-log line or selection record this was
      -- derived from. Without it the score is unfalsifiable.
  occurred_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_influence_events_fact
    ON fact_influence_events(fact_ref, occurred_at);
CREATE INDEX IF NOT EXISTS idx_influence_events_app
    ON fact_influence_events(application_id);

-- Recomputed each weekly pass. A cache of the aggregation, never the
-- source of truth.
CREATE TABLE IF NOT EXISTS fact_influence (
  fact_ref          TEXT PRIMARY KEY,
  influence_raw     INTEGER NOT NULL DEFAULT 0,   -- Σ weight, trailing 180d
  influence_score   REAL NOT NULL DEFAULT 0.0,    -- raw / (raw + 6)
      -- Saturating, not linear. A linear count lets one heavily-reused
      -- fact dominate a ranking permanently, and the useful signal is
      -- categorical — does this fact do work — not how much.
      -- ~0.14 at one event, 0.5 at six, 0.77 at twenty, never 1.
  event_count       INTEGER NOT NULL DEFAULT 0,
  last_event_at     TEXT,
  trust_score_seen  REAL,
      -- Trust as read from fact_store at computation time. Cached here
      -- ONLY so the low-trust/high-influence report can be a single
      -- query. The two dimensions are never averaged, and nothing writes
      -- back to trust from here — letting influence nudge trust would
      -- reintroduce the exact conflation this addendum exists to undo.
  computed_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_fact_influence_score
    ON fact_influence(influence_score DESC);

-- The report that neither dimension can produce alone: facts that are
-- deciding gates AND keep getting edited out. Wrong, and load-bearing.
-- Empty most weeks; when it isn't, it is the most important line in the
-- digest.
CREATE VIEW IF NOT EXISTS v_low_trust_high_influence AS
SELECT fact_ref, influence_score, trust_score_seen, event_count, last_event_at
  FROM fact_influence
 WHERE influence_score >= 0.5
   AND trust_score_seen IS NOT NULL
   AND trust_score_seen < 0.45
 ORDER BY influence_score DESC;

-- Which facts are actually carrying the search.
CREATE VIEW IF NOT EXISTS v_top_influence AS
SELECT fact_ref, influence_score, trust_score_seen, event_count
  FROM fact_influence
 WHERE influence_score > 0
 ORDER BY influence_score DESC
 LIMIT 20;

-- NOT PROVIDED, DELIBERATELY: any view of zero-influence facts shaped as
-- a deletion candidate list. Zero influence means "not yet needed", not
-- "dead weight" — a career memory bank exists precisely to hold things
-- until the day they matter, and the interest nobody asked about for
-- three years is the one that lands the conversation. The weekly digest
-- reports a COUNT of stale-zero facts and never a list, so there is
-- nothing shaped like a prune prompt to click through.

INSERT OR IGNORE INTO schema_version (filename, note) VALUES
  ('applications_db_schema_addendum_17.sql', 'fact influence scoring — importance as a dimension separate from trust');
