-- Job-hunting pipeline database schema — Addendum 4
-- SUPERSEDES the single career_path_plan_progress table from
-- applications_db_schema_addendum_3.sql. That table stored roadmap
-- items as one JSON blob overwritten in place on every re-evaluation —
-- workable, but genuinely "lightweight": no per-item history, no link
-- to what evidence actually resolved an item, no record of what
-- changed across re-evaluation runs, no connection to the real
-- applications a plan eventually produced. Kene asked directly for
-- full tracking instead of that. This is the replacement: five
-- normalized tables instead of one, each answering a question the old
-- single table genuinely could not.
--
-- Migration: run this after addendum_3.sql. It drops and replaces
-- career_path_plan_progress; if any real plan data already exists in
-- that table, migrate it into career_path_plans/career_path_plan_
-- roadmap_items before running the DROP, since this file does not
-- attempt an automatic data migration (the schema shapes are too
-- different for a safe automatic copy — roadmap_items alone goes from
-- one JSON column to a normalized table with fields the JSON version
-- never captured, like category and resolved_by_evidence_ref).

DROP TABLE IF EXISTS career_path_plan_progress;

-- 1. The plan itself — one row per plan, header/metadata only.
CREATE TABLE IF NOT EXISTS career_path_plans (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id                     TEXT NOT NULL UNIQUE,  -- matches
                                                        -- shared/career_path_plans/
                                                        -- {plan_id}.md
    target_title                TEXT NOT NULL,
    target_job_zone             INTEGER,
    current_title                TEXT,                 -- null for mode e
                                                         -- with no held title
    current_job_zone_at_creation INTEGER,               -- may be
                                                         -- education/life-stage-
                                                         -- derived, not held-title-derived
    selection_mode               TEXT NOT NULL,          -- higher_seniority | adjacent |
                                                          -- different | manual | interest_led
    rationale                    TEXT,                   -- why this target — taxonomy/
                                                          -- transferable-skill match,
                                                          -- "manually specified", or the
                                                          -- interests-profile entries behind
                                                          -- an interest_led pick
    interest_fit_score_at_creation      REAL,
    transferable_skill_score_at_creation REAL,           -- null unless mode: different

    status                       TEXT NOT NULL DEFAULT 'active',
                                                          -- active | achieved | abandoned |
                                                          -- superseded
    created_at                   TIMESTAMP NOT NULL,
    achieved_at                  TIMESTAMP,
    abandoned_at                 TIMESTAMP,
    abandoned_reason             TEXT,
    superseded_by_plan_id        TEXT,                   -- FK to another
                                                          -- career_path_plans.plan_id

    -- Step 5 — closing the loop, tracked explicitly rather than only
    -- reflected as a side effect on target-profile.yaml
    active_search_status         TEXT NOT NULL DEFAULT 'not_searching',
                                                          -- not_searching | searching
    active_search_confirmed_at   TIMESTAMP,

    last_reevaluated_at          TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_career_path_plans_status ON career_path_plans(status);

-- 2. Stepping stones — one row per hop, each independently tracked.
-- Empty for a direct single-hop plan (no rows, not a null/empty JSON
-- field on the parent).
CREATE TABLE IF NOT EXISTS career_path_plan_stepping_stones (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id                     TEXT NOT NULL,
    sequence_order               INTEGER NOT NULL,       -- 1, 2, ... —
                                                          -- order along the path
    stepping_stone_title          TEXT NOT NULL,
    stepping_stone_job_zone       INTEGER,
    status                       TEXT NOT NULL DEFAULT 'not_started',
                                                          -- not_started | in_progress | achieved
    achieved_at                  TIMESTAMP,

    FOREIGN KEY (plan_id) REFERENCES career_path_plans(plan_id)
);

CREATE INDEX IF NOT EXISTS idx_stepping_stones_plan ON career_path_plan_stepping_stones(plan_id);

-- 3. Roadmap items — one row per item, not a JSON blob. This is the
-- core of "full tracking": every item is its own addressable record.
CREATE TABLE IF NOT EXISTS career_path_plan_roadmap_items (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id                     TEXT NOT NULL,
    item_text                    TEXT NOT NULL,
    category                     TEXT,                   -- certification | project |
                                                          -- experience | scope_change |
                                                          -- time_in_role | other
    closes_gap                   TEXT,                   -- which requirement(s) this
                                                          -- addresses
    leverage_rank                 INTEGER,                -- lower = higher leverage
    source                       TEXT NOT NULL DEFAULT 'primary',
                                                          -- primary | community_reported —
                                                          -- mirrors Step 3's
                                                          -- [COMMUNITY-REPORTED] tagging

    status                       TEXT NOT NULL DEFAULT 'open',
                                                          -- open | in_progress | resolved
    resolved_by_evidence_ref      TEXT,                   -- pointer to the specific
                                                          -- STAR-bank / domain-knowledge /
                                                          -- interests-profile / journal
                                                          -- entry that resolved this —
                                                          -- null until resolved

    created_at                   TIMESTAMP NOT NULL,
    last_status_change_at         TIMESTAMP,
    resolved_at                   TIMESTAMP,

    FOREIGN KEY (plan_id) REFERENCES career_path_plans(plan_id)
);

CREATE INDEX IF NOT EXISTS idx_roadmap_items_plan ON career_path_plan_roadmap_items(plan_id);
CREATE INDEX IF NOT EXISTS idx_roadmap_items_status ON career_path_plan_roadmap_items(status);

-- 4. Roadmap item history — the actual audit trail. Every status
-- transition gets its own row here; career_path_plan_roadmap_items
-- above only ever shows the *current* state.
CREATE TABLE IF NOT EXISTS career_path_plan_roadmap_item_history (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    roadmap_item_id              INTEGER NOT NULL,
    changed_at                   TIMESTAMP NOT NULL,
    old_status                   TEXT,
    new_status                   TEXT NOT NULL,
    trigger                      TEXT,                   -- career_pulse_cascade |
                                                          -- cron_reevaluation | manual |
                                                          -- journal_surfaced
    note                          TEXT,

    FOREIGN KEY (roadmap_item_id) REFERENCES career_path_plan_roadmap_items(id)
);

CREATE INDEX IF NOT EXISTS idx_roadmap_item_history_item ON career_path_plan_roadmap_item_history(roadmap_item_id);

-- 5. Re-evaluation log — one row per re-evaluation run (cron job 14 or
-- manual), not just a single last_reevaluated_at timestamp overwritten
-- each time. This is what makes "how has this plan evolved" an
-- actually answerable question.
CREATE TABLE IF NOT EXISTS career_path_plan_reevaluations (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id                     TEXT NOT NULL,
    evaluated_at                 TIMESTAMP NOT NULL,
    trigger                      TEXT,                   -- cron_job_13 |
                                                          -- career_pulse_cascade | manual
    items_resolved_this_run       INTEGER DEFAULT 0,
    items_still_open              INTEGER,
    interest_fit_score_at_time     REAL,
    transferable_skill_score_at_time REAL,
    gap_summary_snapshot          TEXT,                   -- short human-readable summary
                                                          -- of what changed this run

    FOREIGN KEY (plan_id) REFERENCES career_path_plans(plan_id)
);

CREATE INDEX IF NOT EXISTS idx_reevaluations_plan ON career_path_plan_reevaluations(plan_id);

-- 6. Application links — once Step 5 promotes a plan to an active
-- search, real applications start happening against that target. This
-- table is what lets a plan's progress roll up real outcomes
-- (interview requests, offers), not just roadmap-item completion.
CREATE TABLE IF NOT EXISTS career_path_plan_application_links (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id                     TEXT NOT NULL,
    application_id                INTEGER NOT NULL,
    linked_at                    TIMESTAMP NOT NULL,

    FOREIGN KEY (plan_id) REFERENCES career_path_plans(plan_id),
    FOREIGN KEY (application_id) REFERENCES applications(id)
);

CREATE INDEX IF NOT EXISTS idx_application_links_plan ON career_path_plan_application_links(plan_id);
