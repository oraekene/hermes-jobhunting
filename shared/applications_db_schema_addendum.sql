-- Job-hunting pipeline database schema — Addendum
-- Same file/location as the base schema: ~/.hermes/skills/job-hunting/
-- shared/applications.db (SQLite). Run this after applications_db_schema.sql;
-- every table here is additive, nothing in the base schema is altered.
--
-- Deliberately NOT adding a new table for employment_status or
-- calibration thresholds — those live in dynamic-target-calibration.yaml
-- as confirmed profile facts, same reasoning target-profile.yaml already
-- uses for everything else Rule 5 governs. Recalibration approvals reuse
-- the existing skill_self_edits table rather than a new one — see
-- shared/dynamic-target-calibration.md.

-- 14-social-discovery-outreach: one row per outreach attempt, mirrors
-- cold-dm-email-schema.md's structure field-for-field.
CREATE TABLE IF NOT EXISTS social_outreach (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Trigger
    trigger_type                TEXT NOT NULL,   -- social_listening_post |
                                                  -- manual_request | application_followup |
                                                  -- referral_ask | interview_thank_you
    source_platform              TEXT,
    source_url                   TEXT,
    source_cta_type              TEXT,            -- apply_link | dm_instructions |
                                                   -- email_instructions | unclear | n/a
    source_cta_context           TEXT,

    -- Contact
    contact_platform              TEXT NOT NULL,
    contact_handle                TEXT,
    contact_display_name          TEXT,
    contact_profile_url           TEXT,
    contact_role_guess            TEXT,
    contact_company                TEXT,
    contact_relationship           TEXT,           -- stranger | inbound_invited |
                                                   -- 1st_degree | warm_intro

    -- Routing (from platform-capability-matrix.md)
    send_tier                     INTEGER,          -- 1 | 2 | 3
    send_method                   TEXT,             -- api_direct_pending_approval | manual_cued
    matrix_checked_at             TIMESTAMP,

    -- Message
    channel                      TEXT NOT NULL,     -- dm | email
    subject                      TEXT,
    body_draft                   TEXT,
    personalization_hooks         TEXT,              -- JSON array, kept as text (SQLite has no native array type)
    char_count                    INTEGER,
    platform_char_limit           INTEGER,
    linked_application_id         INTEGER,

    -- Fidelity (Rule 2)
    risk_gate_pass_count          INTEGER DEFAULT 0,
    risk_gate_fail_count          INTEGER DEFAULT 0,
    fidelity_mode_at_draft         TEXT,

    -- Approval & delivery (Rule 1 / Rule 6)
    status                       TEXT NOT NULL DEFAULT 'drafted',
        -- drafted | awaiting_approval | approved | api_sent |
        -- cued_delivered_by_user | skipped
    approval_sent_at              TIMESTAMP,
    approval_decision             TEXT,              -- approve | edit | skip
    approval_decided_at           TIMESTAMP,
    sent_at                       TIMESTAMP,
    sent_via                      TEXT,              -- api | manual

    -- Outcome (Rule 4)
    replied_at                    TIMESTAMP,
    reply_type                    TEXT,              -- no_reply | auto_reply | human_reply |
                                                     -- led_to_application | led_to_referral
    led_to_application_id          INTEGER,
    outcome_updated_at             TIMESTAMP,

    created_at                    TIMESTAMP NOT NULL,

    FOREIGN KEY (linked_application_id) REFERENCES applications(id),
    FOREIGN KEY (led_to_application_id) REFERENCES applications(id)
);

CREATE INDEX IF NOT EXISTS idx_social_outreach_status ON social_outreach(status);
CREATE INDEX IF NOT EXISTS idx_social_outreach_platform ON social_outreach(contact_platform);

-- 16-career-pulse: raw journal entries, stored before any confirmation —
-- recall material, not curated fact (same status as FTS5 session search
-- relative to MEMORY.md/USER.md; see 16-career-pulse/SKILL.md, section 1).
CREATE TABLE IF NOT EXISTS career_journal (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_at                     TIMESTAMP NOT NULL,
    raw_text                     TEXT NOT NULL,
    candidate_facts_extracted     TEXT,     -- JSON array of {text, category} —
                                            -- what this entry flagged for
                                            -- 07-context-architect to confirm
    surfaced_to_context_architect  INTEGER DEFAULT 0,   -- 0/1
    surfaced_at                   TIMESTAMP
);

-- 16-career-pulse: diffs from explicit-channel monitoring (LinkedIn,
-- GitHub, portfolio, blog) — same "surface, don't write" discipline.
CREATE TABLE IF NOT EXISTS profile_monitor_events (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    channel                      TEXT NOT NULL,    -- linkedin | github | portfolio | blog | other
    checked_at                    TIMESTAMP NOT NULL,
    diff_summary                  TEXT NOT NULL,    -- Kene-readable, e.g. "2 new
                                                     -- merged PRs on repo X"
    surfaced_to_context_architect  INTEGER DEFAULT 0,
    surfaced_at                   TIMESTAMP
);

-- 15-interview-prep: post-interview debrief, distinct from the outcome
-- fields already on applications (those are status/timing; this is
-- Kene's own qualitative read, the exact kind of detail the README's
-- "cross-session recall" section already flags as easy to lose).
CREATE TABLE IF NOT EXISTS interview_debrief (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id               INTEGER NOT NULL,
    interview_at                 TIMESTAMP,
    round                        TEXT,             -- e.g. "first", "second", "final"
    kene_read                    TEXT NOT NULL,     -- free text: how it went, what felt thin,
                                                     -- what surprised him
    thank_you_outreach_id         INTEGER,          -- FK to social_outreach, if a
                                                     -- thank-you note was drafted
    created_at                    TIMESTAMP NOT NULL,

    FOREIGN KEY (application_id) REFERENCES applications(id),
    FOREIGN KEY (thank_you_outreach_id) REFERENCES social_outreach(id)
);

CREATE INDEX IF NOT EXISTS idx_interview_debrief_application ON interview_debrief(application_id);
