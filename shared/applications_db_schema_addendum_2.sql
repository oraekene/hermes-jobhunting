-- Job-hunting pipeline database schema — Addendum 2 (cold prospecting)
-- Run after applications_db_schema_addendum.sql. Extends social_outreach
-- rather than duplicating it — a prospecting pitch and a posting-
-- triggered cold DM are the same record shape with a few extra fields,
-- not a separate pipeline. No new table for the pitch catalog itself:
-- it lives in shared/pitch-catalog.yaml as a confirmed profile fact,
-- same reasoning target-profile.yaml and dynamic-target-calibration.yaml
-- already use — 11-analytics-and-learning correlates catalog_entry_ids
-- here against that file's entries at analysis time, rather than this
-- schema maintaining a second copy of catalog metadata.

ALTER TABLE social_outreach ADD COLUMN pitch_mode TEXT;
    -- role_fit | role_creation | service | null (null = ordinary
    -- posting-triggered outreach from 14-social-discovery-outreach,
    -- not a 17-cold-prospecting pitch)

ALTER TABLE social_outreach ADD COLUMN catalog_entry_ids TEXT;
    -- JSON array of shared/pitch-catalog.yaml entry ids used to build
    -- this draft, e.g. ["example-held-01"]

ALTER TABLE social_outreach ADD COLUMN target_type TEXT;
    -- company | individual | null

ALTER TABLE social_outreach ADD COLUMN target_research_ref TEXT;
    -- company_slug (shared/company_research_cache/{slug}.md) or
    -- handle_slug (shared/individual_research_cache/{slug}.md)

ALTER TABLE social_outreach ADD COLUMN target_claim_gate_pass_count INTEGER DEFAULT 0;
ALTER TABLE social_outreach ADD COLUMN target_claim_gate_fail_count INTEGER DEFAULT 0;
    -- mirrors risk_gate_pass_count/fail_count, but for claims about the
    -- target rather than claims about Kene — see 17-cold-prospecting/
    -- SKILL.md's "target-claim gate" section

CREATE INDEX IF NOT EXISTS idx_social_outreach_pitch_mode ON social_outreach(pitch_mode);
