-- Addendum 18 — portfolio artifacts, link health, and publish history
--
-- 23-portfolio-onepager's content selection lives in
-- shared/portfolio-manifest.yaml, which is right: it is configuration
-- Kene edits and reads. What does NOT belong in a YAML file is the
-- time-series — every link check, every publish, every variant's history
-- — because that grows without bound and nobody wants it in a file they
-- open to change an ordering.
--
-- THE POINT OF THE ARTIFACT TABLE. A portfolio without links is a CV
-- with worse ATS compatibility. Links are the reason the page exists, so
-- their health is load-bearing rather than housekeeping: a page with dead
-- links looks careless in exactly the dimension it was built to
-- demonstrate.
--
-- And the failure is silent. Nothing tells you a repo went private, a
-- Colab now needs permission, or a demo host shut down. Only a check
-- does.
--
-- Apply after applications_db_schema_addendum_17.sql. Fully idempotent.

CREATE TABLE IF NOT EXISTS portfolio_artifacts (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  artifact_id       TEXT NOT NULL UNIQUE,   -- matches manifest pool.artifacts[].id
  artifact_type     TEXT NOT NULL,
      -- deployed | repo | notebook | writeup | demo | package | paper
      -- 'deployed' is the highest-value link there is: a reader can use
      -- the thing in ten seconds.
  url               TEXT NOT NULL,
  label             TEXT,

  ownership         TEXT NOT NULL DEFAULT 'own',
      -- own | public_with_permission
      -- Nothing employer-owned, NDA-covered, or carrying third-party data
      -- reaches a public page. Checked at add time and again at publish,
      -- and it is the one check in this skill with NO override path — the
      -- failure mode is publishing something he did not own, and that
      -- ends careers rather than jobs.

  readable_checked_at TEXT,
  readable            INTEGER,
      -- A link can resolve and still prove nothing. A repo whose README
      -- does not say what the thing is, or a notebook with cleared
      -- outputs that opens as a wall of code, is a link the reader
      -- closes. Flagged, never auto-fixed — fixing it is real work Kene
      -- has to do.

  added_at          TEXT NOT NULL DEFAULT (datetime('now')),
  retired_at        TEXT
      -- Soft retire. An artifact pulled from the pool keeps its check
      -- history, because "when did this break" stays answerable.
);

CREATE INDEX IF NOT EXISTS idx_portfolio_artifacts_active
    ON portfolio_artifacts(retired_at, artifact_type);

-- One row per check. History, not just current state: an intermittent
-- failure and a permanent one look identical in a single status column
-- and call for different responses.
CREATE TABLE IF NOT EXISTS portfolio_link_checks (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  artifact_id   TEXT NOT NULL REFERENCES portfolio_artifacts(artifact_id),
  checked_at    TEXT NOT NULL DEFAULT (datetime('now')),
  http_status   INTEGER,
  outcome       TEXT NOT NULL,
      -- ok | not_found | forbidden | timeout | redirected | tls_error
      -- 'forbidden' is the interesting one and the reason this is not
      -- just a 404 check: a repo flipped to private and a Colab that now
      -- requires access both return 403 while the URL stays perfectly
      -- valid. That is the most common real failure here.
  redirect_to   TEXT,
      -- A redirect is not automatically a failure — repos get renamed.
      -- But a redirect to an org index or a login page is a dead link
      -- wearing a 200, so the destination is recorded for a human read.
  note          TEXT
);

CREATE INDEX IF NOT EXISTS idx_link_checks_artifact
    ON portfolio_link_checks(artifact_id, checked_at DESC);

-- Current health, for the publish gate and the quarterly refresh.
CREATE VIEW IF NOT EXISTS v_portfolio_link_health AS
SELECT a.artifact_id, a.artifact_type, a.url, a.label,
       c.outcome AS last_outcome, c.http_status, c.checked_at AS last_checked_at,
       a.readable
  FROM portfolio_artifacts a
  LEFT JOIN portfolio_link_checks c
         ON c.id = (SELECT id FROM portfolio_link_checks
                     WHERE artifact_id = a.artifact_id
                     ORDER BY checked_at DESC LIMIT 1)
 WHERE a.retired_at IS NULL;

-- Publish history per variant. Answers "what was live in March" without
-- keeping a copy of every page.
CREATE TABLE IF NOT EXISTS portfolio_publishes (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  variant_slug      TEXT NOT NULL,
  published_at      TEXT NOT NULL DEFAULT (datetime('now')),
  provider          TEXT,      -- cloudflare_pages | netlify | github_pages | manual
  url               TEXT,
  item_ids          TEXT,      -- JSON array, the ordered selection as published
  gate_passed_at    TEXT,      -- 09-risk-tactics-gate over the page content
  dead_links_at_publish INTEGER NOT NULL DEFAULT 0,
      -- Should be 0. A failing link blocks the publish until Kene decides,
      -- so a non-zero value here means he decided to ship anyway — which is
      -- his call, and worth having on the record.
  unpublished_at    TEXT,
  unpublish_reason  TEXT
      -- Usually 'accepted an offer'. Worth capturing: taking a page down
      -- is a real event and the reason predicts whether it goes back up.
);

CREATE INDEX IF NOT EXISTS idx_portfolio_publishes_variant
    ON portfolio_publishes(variant_slug, published_at DESC);

INSERT OR IGNORE INTO schema_version (filename, note) VALUES
  ('applications_db_schema_addendum_18.sql', 'portfolio artifacts, link-rot checks and publish history');
