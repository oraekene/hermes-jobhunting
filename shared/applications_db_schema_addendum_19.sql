-- Addendum 19 — outreach send path (was ADDENDUM-27's addendum_6.sql)
--
-- RENUMBERED ON MERGE. This file and the main package's addendum_6.sql
-- ('overqualification gate outcome') were two entirely different
-- migrations sharing one filename and one chain slot. Installing from
-- either shared/ silently dropped the other. Same failure class as the
-- cron job-9 collision, in the schema chain, where the symptom is a
-- missing table rather than a duplicated job.
--
-- Moved to the end of the chain rather than inserted, so every DB
-- already built from the main package's chain can apply this forward
-- with no renumbering of anything that already ran.
--
-- Job-hunting pipeline database schema — Addendum 6
-- Run after applications_db_schema_addendum_5.sql. Adds the columns
-- 14-social-discovery-outreach/references/cold-dm-email-schema.md's
-- new connection/inmail/x_follow_state/ig_fb_window blocks now define
-- (this pass's platform-gate tracking work), matching the schema doc
-- so the DB doesn't drift from the documented shape — same discipline
-- addendum_5.sql already established for contact_priority/
-- identification_confidence.

-- --- routing block additions ---
ALTER TABLE social_outreach ADD COLUMN send_method_detail TEXT;
    -- api_direct_pending_approval | manual_cued | computer_use_approved
    -- — supersedes any earlier plain send_method value in intent, kept
    -- under a new column name rather than overwriting in place so a
    -- migration script can backfill deliberately instead of silently
    -- reinterpreting old rows

ALTER TABLE social_outreach ADD COLUMN inmail_used INTEGER DEFAULT 0;
    -- boolean (0/1) — see 14-social-discovery-outreach/references/inmail-credits.md

-- --- connection block (LinkedIn connect-first gate) ---
ALTER TABLE social_outreach ADD COLUMN connection_required INTEGER DEFAULT 0;
ALTER TABLE social_outreach ADD COLUMN connection_status TEXT;
    -- not_connected | note_drafted | note_awaiting_approval |
    -- request_sent_pending_acceptance | accepted | declined | expired |
    -- withdrawn
ALTER TABLE social_outreach ADD COLUMN connection_note_draft TEXT;
ALTER TABLE social_outreach ADD COLUMN connection_note_char_count INTEGER;
ALTER TABLE social_outreach ADD COLUMN connection_approval_sent_at TEXT;
ALTER TABLE social_outreach ADD COLUMN connection_approval_decided_at TEXT;
ALTER TABLE social_outreach ADD COLUMN connection_send_method TEXT;
    -- computer_use_approved | manual_cued
ALTER TABLE social_outreach ADD COLUMN connection_sent_at TEXT;
ALTER TABLE social_outreach ADD COLUMN connection_check_method TEXT;
    -- kene_confirmed | computer_use_check
ALTER TABLE social_outreach ADD COLUMN connection_last_checked_at TEXT;
ALTER TABLE social_outreach ADD COLUMN connection_accepted_at TEXT;
ALTER TABLE social_outreach ADD COLUMN connection_expires_at TEXT;
ALTER TABLE social_outreach ADD COLUMN connection_free_tier_note_quota_used INTEGER;

-- --- inmail block ---
ALTER TABLE social_outreach ADD COLUMN inmail_sent_at TEXT;
ALTER TABLE social_outreach ADD COLUMN inmail_reply_deadline TEXT;
    -- sent_at + 90d, computed at write time
ALTER TABLE social_outreach ADD COLUMN inmail_credit_refunded INTEGER DEFAULT 0;
ALTER TABLE social_outreach ADD COLUMN inmail_open_profile_send INTEGER DEFAULT 0;

-- --- x_follow_state block ---
ALTER TABLE social_outreach ADD COLUMN x_follow_checked_at TEXT;
ALTER TABLE social_outreach ADD COLUMN x_follow_target_follows_kene INTEGER;
    -- nullable boolean: null = not yet checked
ALTER TABLE social_outreach ADD COLUMN x_follow_target_dm_setting TEXT;
    -- everyone | followers_and_verified | unknown
ALTER TABLE social_outreach ADD COLUMN x_follow_kene_tier_gate_applies INTEGER;
ALTER TABLE social_outreach ADD COLUMN x_follow_back_achieved_at TEXT;

-- engagement_attempts stays a normalized child table, not a JSON blob —
-- same reasoning applications_db_schema_addendum_4.sql gave for
-- splitting career_path_plan roadmap items into real rows: a list that
-- analytics will eventually want to query by type/date shouldn't be
-- buried in one column.
CREATE TABLE IF NOT EXISTS x_follow_engagement_attempts (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    social_outreach_id INTEGER NOT NULL REFERENCES social_outreach(id),
    attempt_type      TEXT NOT NULL,   -- reply | like | quote
    url               TEXT,
    posted_at         TEXT NOT NULL
);

-- --- ig_fb_window block ---
ALTER TABLE social_outreach ADD COLUMN ig_fb_window_opened_at TEXT;
ALTER TABLE social_outreach ADD COLUMN ig_fb_window_expires_at TEXT;
ALTER TABLE social_outreach ADD COLUMN ig_fb_message_tag_used TEXT;
ALTER TABLE social_outreach ADD COLUMN ig_fb_messages_sent_in_window INTEGER DEFAULT 0;
ALTER TABLE social_outreach ADD COLUMN ig_fb_window_closed_unused INTEGER DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_social_outreach_connection_status ON social_outreach(connection_status);
CREATE INDEX IF NOT EXISTS idx_social_outreach_x_follow ON social_outreach(x_follow_target_follows_kene);
CREATE INDEX IF NOT EXISTS idx_social_outreach_ig_fb_window ON social_outreach(ig_fb_window_expires_at);

INSERT OR IGNORE INTO schema_version (filename, note) VALUES
  ('applications_db_schema_addendum_19.sql', 'outreach send path: connection/inmail/x-follow/ig-fb gates');
