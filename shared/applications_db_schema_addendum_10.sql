-- Addendum 10 — enrichment spend, joined to outcomes (D9)
--
-- enrichment-tools-pricing.md knows what providers cost.
-- enrichment-tier-usage.yaml knows how many credits were consumed.
-- The applications table knows which applications got replies.
-- Nothing joins them, so the only question that actually decides whether
-- Tier 3 enrichment is worth paying for -- "what does an interview
-- request cost me?" -- cannot be asked.
--
-- Per-provider tier usage stays where it is: it is a rate-limit counter
-- with a billing-cycle reset, which is a different job from an audit
-- trail. This table is the audit trail.
--
-- Apply after applications_db_schema_addendum_9.sql.

CREATE TABLE IF NOT EXISTS enrichment_spend (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  application_id  INTEGER REFERENCES applications(id) ON DELETE SET NULL,
  -- NULL is legitimate: cold prospecting enriches a contact before any
  -- application exists. Those lookups still cost money and must still be
  -- counted, so this is nullable by design rather than by oversight.
  contact_handle  TEXT,
  provider        TEXT NOT NULL,
  tier            INTEGER NOT NULL,         -- 1 free / 2 freemium / 3 paid
  credits_used    INTEGER NOT NULL DEFAULT 1,
  est_cost_usd    REAL,                     -- NULL for tier 1
  was_successful  INTEGER NOT NULL DEFAULT 0,
  -- A failed paid lookup still costs a credit at most providers. Counting
  -- only successes would understate real spend, which is the direction
  -- that flatters the tool.
  occurred_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_enrichment_spend_app ON enrichment_spend(application_id);
CREATE INDEX IF NOT EXISTS idx_enrichment_spend_when ON enrichment_spend(occurred_at);

-- Cost per application. Applications with no enrichment show 0.0, not
-- NULL, so an average over this view is not silently distorted by the
-- rows that cost nothing.
CREATE VIEW IF NOT EXISTS v_cost_per_application AS
SELECT a.id                                AS application_id,
       a.company,
       a.role_title,
       a.status,
       COALESCE(SUM(s.est_cost_usd), 0.0)  AS cost_usd,
       COALESCE(SUM(s.credits_used), 0)    AS credits
FROM applications a
LEFT JOIN enrichment_spend s ON s.application_id = a.id
GROUP BY a.id;

-- The number that actually decides the tier question. Unattributed spend
-- (cold prospecting, no application yet) is folded in, because excluding
-- it would understate what a reply really costs.
CREATE VIEW IF NOT EXISTS v_cost_per_outcome AS
SELECT
  (SELECT COALESCE(SUM(est_cost_usd), 0.0) FROM enrichment_spend)          AS total_spend_usd,
  (SELECT COUNT(*) FROM applications WHERE status = 'submitted')           AS submitted,
  (SELECT COUNT(*) FROM applications WHERE interview_request_at IS NOT NULL) AS interview_requests,
  ROUND((SELECT COALESCE(SUM(est_cost_usd), 0.0) FROM enrichment_spend) /
        NULLIF((SELECT COUNT(*) FROM applications WHERE status = 'submitted'), 0), 2)
                                                                          AS cost_per_submitted,
  ROUND((SELECT COALESCE(SUM(est_cost_usd), 0.0) FROM enrichment_spend) /
        NULLIF((SELECT COUNT(*) FROM applications WHERE interview_request_at IS NOT NULL), 0), 2)
                                                                          AS cost_per_interview_request;

INSERT OR IGNORE INTO schema_version (filename, note) VALUES
  ('applications_db_schema_addendum_10.sql', 'enrichment spend joined to outcomes');
