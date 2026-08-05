-- Job-hunting pipeline database schema
-- Location on disk: ~/.hermes/skills/job-hunting/shared/applications.db (SQLite)
-- Every field here maps to a metric in 11-analytics-and-learning/references/metrics-schema.md
--
-- MIGRATION NOTE for a database that already exists: `CREATE TABLE IF NOT
-- EXISTS` does nothing for a table that's already there, so a column added
-- to an existing table's definition here won't retroactively appear on
-- disk. If you're re-running this file against a DB created before the
-- interview-prep upgrade pass, run this once first:
--   ALTER TABLE applications ADD COLUMN last_interview_prep_at TIMESTAMP;
-- New installs don't need this — the CREATE TABLE below already has it.

CREATE TABLE IF NOT EXISTS applications (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Identity / discovery
    posting_url             TEXT,
    company                 TEXT NOT NULL,
    role_title              TEXT NOT NULL,
    source_board            TEXT,               -- e.g. LinkedIn, company careers page, Indeed
    ats_platform             TEXT,               -- Greenhouse / Workable / Lever / Workday / other
    posted_at               TIMESTAMP,
    posted_at_raw           TEXT,               -- original label/string as shown
                                                 -- by the source (e.g. "2 hours
                                                 -- ago"), kept alongside the
                                                 -- parsed posted_at so a bad
                                                 -- read is auditable, not just
                                                 -- trusted — see sources.yaml
    discovered_at           TIMESTAMP,

    -- Role attributes (for segmentation)
    industry                TEXT,
    seniority               TEXT,
    remote_type              TEXT,               -- remote / hybrid / onsite
    salary_disclosed         INTEGER DEFAULT 0,   -- 0/1
    salary_range             TEXT,

    -- Pipeline status
    status                  TEXT NOT NULL DEFAULT 'discovered',
        -- discovered | building | staged | awaiting_approval | approved_sent |
        -- edited_then_sent | rejected_by_kene
        --
        -- 'building' and 'staged' were both already anticipated by earlier
        -- versions of this comment but never precisely wired up until the
        -- optional parallel-sweep mode (00-orchestrator/references/
        -- parallel-pipeline-sweep.md) needed the distinction to be real:
        --   discovered        -> found, not yet started
        --   building          -> handed to a build pass (serial or a
        --                        delegated child) — set IMMEDIATELY at
        --                        dispatch, before the build actually runs,
        --                        specifically so a later sweep tick's
        --                        `WHERE status='discovered'` query can't
        --                        pick the same posting twice
        --   staged            -> package cleared 09-risk-tactics-gate,
        --                        built, not yet pinged to Kene
        --   awaiting_approval -> 10-approval-and-submit actually sent the
        --                        Telegram ping and is waiting on a reply
        -- A posting stuck at 'building' or 'staged' well past one full
        -- sweep cycle is a signal something silently failed, not a status
        -- to just leave alone — see the reference file above for the
        -- staleness check this enables.

    -- Scoring (stages 3 & 4)
    overall_match_score      REAL,               -- 03-resume-match
    keyword_match_score      REAL,               -- 04-keyword-analysis

    -- Tactics applied (stage 5/6/8, gated by stage 9)
    exact_phrase_count       INTEGER DEFAULT 0,
    title_matched            INTEGER DEFAULT 0,   -- 0/1
    title_original           TEXT,
    title_displayed          TEXT,
    values_alignment_included INTEGER DEFAULT 0,  -- 0/1
    quantified_bullet_count  INTEGER DEFAULT 0,
    cover_letter_word_count  INTEGER,
    recruiter_named           INTEGER DEFAULT 0,   -- 0/1
    structure_mirrored        INTEGER DEFAULT 0,   -- 0/1
    risk_gate_pass_count     INTEGER DEFAULT 0,
    risk_gate_fail_count     INTEGER DEFAULT 0,
    application_channel      TEXT,                -- easy_apply / full_form / referral / email

    -- Approval & send (stage 10 — the only stage allowed to fill these in)
    staged_at                TIMESTAMP,
    approval_sent_at         TIMESTAMP,           -- when Telegram ping was sent
    approval_decision        TEXT,                -- approve / edit / skip
    approval_decided_at      TIMESTAMP,
    sent_at                  TIMESTAMP,

    -- Outcomes (updated as Kene reports them, or — once built — as an
    -- automated email scan detects them; see outcome_source below)
    first_response_at        TIMESTAMP,
    response_type            TEXT,                -- auto_reject / human_reply / screen_request / interview_request
    interview_request_at     TIMESTAMP,
    interview_date            TIMESTAMP,
    second_round_at          TIMESTAMP,
    final_round_at           TIMESTAMP,
    last_interview_prep_at    TIMESTAMP,          -- set by 13-interview-prep after it builds
                                                    -- or refreshes a prep brief for this
                                                    -- application. NULL means never built.
                                                    -- Deliberately NOT a one-shot boolean —
                                                    -- see 13-interview-prep/SKILL.md's trigger
                                                    -- logic: a NEW email_insights interview_detail
                                                    -- row extracted_at AFTER this timestamp means
                                                    -- a later round has fresh info, so the brief
                                                    -- gets rebuilt rather than staying stale.
    offer_at                  TIMESTAMP,
    offer_amount              TEXT,
    outcome                  TEXT DEFAULT 'pending',
        -- pending | rejected_pre_interview | rejected_post_interview | ghosted | offer_accepted | offer_declined
    outcome_updated_at        TIMESTAMP,
    outcome_source            TEXT               -- email_scan | user_reported | inferred
        -- Source-agnostic by design: today every outcome comes from Kene
        -- typing a sentence to Hermes (user_reported). This column exists
        -- so a future email-scanning capability (11-analytics-and-learning)
        -- can log outcomes it classifies from inbox messages without any
        -- schema change, while keeping the classification's provenance
        -- auditable — an automated read of "auto-reject vs. human reply"
        -- is a judgment call that can be wrong, and Rule 4 depends on this
        -- data being trustworthy, not just plentiful.
);

CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_applications_outcome ON applications(outcome);
CREATE INDEX IF NOT EXISTS idx_applications_company ON applications(company, role_title);

-- Weekly rollups, written by 11-analytics-and-learning's cron job
CREATE TABLE IF NOT EXISTS weekly_metrics_snapshots (
    id                        INTEGER PRIMARY KEY AUTOINCREMENT,
    week_start                DATE NOT NULL,
    applications_sent         INTEGER,
    response_rate             REAL,
    interview_rate            REAL,
    offer_rate                 REAL,
    avg_keyword_score          REAL,
    avg_time_to_apply_hours    REAL,
    notes                      TEXT
);

-- Self-improvement audit trail — every proposed skill edit and its approval status
CREATE TABLE IF NOT EXISTS skill_self_edits (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    proposed_at            TIMESTAMP NOT NULL,
    skill_name             TEXT NOT NULL,
    change_summary         TEXT NOT NULL,
    supporting_data        TEXT,               -- e.g. "n=30/27, +14pp response rate"
    approved_by_kene       INTEGER DEFAULT 0,   -- 0 = pending, 1 = approved, 2 = rejected
    decided_at              TIMESTAMP
);

-- De-duplication support for 01-job-discovery
CREATE UNIQUE INDEX IF NOT EXISTS idx_dedupe ON applications(company, role_title, posting_url);

-- Insight extraction from email bodies — see shared/email-insight-extraction.md
-- for the extraction logic. Populated by both 01-job-discovery (reading
-- email_label sources) and 11-analytics-and-learning (reading reply/
-- outcome emails during the daily ghost-check scan). Deliberately
-- separate from the response_type classification on `applications` —
-- an email can carry a useful detail (an interviewer's name, a stated
-- deadline) independent of whether it classified as a confident outcome,
-- and a classification failure shouldn't cost the detail too.
CREATE TABLE IF NOT EXISTS email_insights (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id        INTEGER,               -- FK to applications.id; NULL when the
                                                    -- email predates a specific application
                                                    -- row (e.g. a discovery-side digest note)
    email_message_id       TEXT NOT NULL,          -- himalaya envelope id, so a message is
                                                    -- never scanned into duplicate rows
    email_date              TIMESTAMP,
    source_skill            TEXT NOT NULL,          -- '01-job-discovery' | '11-analytics-and-learning'
    category                TEXT NOT NULL,
        -- interview_detail | feedback | deadline | action_item | sentiment_signal | other
    detail_text             TEXT NOT NULL,          -- one Kene-readable sentence, not a raw quote —
                                                    -- see shared/email-insight-extraction.md's
                                                    -- "paraphrase, don't quote" rule
    confidence               TEXT DEFAULT 'medium',  -- low | medium | high — this is an LLM read
                                                    -- of free text, same "can be wrong" caveat
                                                    -- 11-analytics-and-learning already applies
                                                    -- to response_type classification
    surfaced_in_digest       INTEGER DEFAULT 0,      -- 0/1 — has this reached Kene yet
    extracted_at             TIMESTAMP NOT NULL,
    FOREIGN KEY (application_id) REFERENCES applications(id)
);

CREATE INDEX IF NOT EXISTS idx_email_insights_application ON email_insights(application_id);
CREATE INDEX IF NOT EXISTS idx_email_insights_category ON email_insights(category);
CREATE UNIQUE INDEX IF NOT EXISTS idx_email_insights_dedupe ON email_insights(email_message_id, category, detail_text);

-- Open gaps flagged by 09-risk-tactics-gate — see that skill's own "Fail
-- handling" section for exactly when a row gets written here.
--
-- This table exists specifically so 09-risk-tactics-gate never writes to
-- ~/.hermes/memories/MEMORY.md. Two reasons, not one:
--   1. Rule 5 (shared/pipeline-rules.md) reserves memory writes for
--      07-context-architect alone, after Kene confirms a fact in the
--      interview loop. An unattended gate appending straight to MEMORY.md
--      during a cron run is exactly the write Rule 5 exists to prevent,
--      regardless of good intent.
--   2. MEMORY.md has a hard ~2,200-character cap and does NOT auto-compact
--      — a write past the cap returns an error and expects the SAME TURN
--      to consolidate before retrying. There is no one available to do
--      that during an unattended pipeline sweep (cron/cron-jobs.md job #3),
--      and an unbounded "Open gaps" list will eventually hit that cap.
-- A SQLite table has no such ceiling and is the pattern this whole schema
-- already uses everywhere else.
CREATE TABLE IF NOT EXISTS open_gaps (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id        INTEGER,               -- FK to applications.id; NULL if flagged
                                                    -- outside a specific application's flow
    company                TEXT,
    role_title             TEXT,
    claim_text             TEXT NOT NULL,          -- the specific claim that had no evidence
                                                    -- (e.g. "stakeholder management")
    missing_evidence       TEXT NOT NULL,          -- what's actually missing, in plain language
    fidelity_mode_at_flag  TEXT NOT NULL,          -- strict | balanced | embellish — mode in
                                                    -- effect when this gap was flagged
    flagged_by             TEXT NOT NULL DEFAULT '09-risk-tactics-gate',
    flagged_at             TIMESTAMP NOT NULL,
    resolved               INTEGER DEFAULT 0,      -- 0/1 — set by 07-context-architect once
                                                    -- Kene supplies the missing evidence (or
                                                    -- explicitly confirms none exists) and it's
                                                    -- written into the STAR bank / domain-
                                                    -- knowledge.md
    resolved_at            TIMESTAMP,
    FOREIGN KEY (application_id) REFERENCES applications(id)
);

CREATE INDEX IF NOT EXISTS idx_open_gaps_resolved ON open_gaps(resolved);
CREATE INDEX IF NOT EXISTS idx_open_gaps_application ON open_gaps(application_id);
