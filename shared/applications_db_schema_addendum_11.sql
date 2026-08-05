-- Addendum 11 — postings that disappear mid-pipeline (D10)
--
-- Postings get pulled: the role is filled, the req is frozen, the board
-- listing expires. The ghost-check job handles no RESPONSE; nothing
-- handled the posting itself vanishing between discovery and submission.
--
-- Without this, three things go wrong quietly. A staged application sits
-- in the approval queue for a role that no longer exists, so Kene spends
-- attention approving it. The submit attempt then fails in a browser
-- session with no clean way to record why. And 11-analytics counts it as
-- an application that got no reply, which is false — it never arrived,
-- and treating it as a rejection poisons the correlation data the
-- self-improvement loop learns from.
--
-- Apply after applications_db_schema_addendum_10.sql.

ALTER TABLE applications ADD COLUMN posting_last_verified_at TEXT;
ALTER TABLE applications ADD COLUMN posting_gone_at TEXT;
ALTER TABLE applications ADD COLUMN posting_gone_signal TEXT;
-- 'http_404' | 'http_410' | 'listing_removed' | 'marked_filled' | 'redirect_to_index'
-- A redirect to a job-board index page is the common real case and is
-- NOT a 404 — the fetch succeeds, so only the content tells you.

CREATE INDEX IF NOT EXISTS idx_applications_posting_gone
  ON applications(posting_gone_at);

-- Excludes vanished postings from outcome statistics. A posting that was
-- never submittable is not a non-reply, and counting it as one understates
-- every reply rate this package measures.
CREATE VIEW IF NOT EXISTS v_outcome_eligible AS
SELECT * FROM applications
WHERE posting_gone_at IS NULL
   OR status = 'submitted';   -- pulled AFTER submitting is a real outcome

INSERT OR IGNORE INTO schema_version (filename, note) VALUES
  ('applications_db_schema_addendum_11.sql', 'posting disappearance handling');
