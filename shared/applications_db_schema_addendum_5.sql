-- Job-hunting pipeline database schema — Addendum 5
-- Run after applications_db_schema_addendum_4.sql. Adds the two new
-- contact-classification columns cold-dm-email-schema.md's contact
-- block now defines (22-contact-enrichment's Part A output), matching
-- the schema doc so the DB doesn't drift from the documented shape —
-- caught missing during this pass rather than left undocumented.

ALTER TABLE social_outreach ADD COLUMN contact_priority TEXT;
    -- hiring_manager | decision_maker | recruiter_track | unclassified
    -- — set by 22-contact-enrichment's Part A classification.
    -- hiring_manager and decision_maker are the primary target
    -- throughout 14-social-discovery-outreach/17-cold-prospecting;
    -- recruiter_track is legitimate but never primary by default.

ALTER TABLE social_outreach ADD COLUMN identification_confidence TEXT;
    -- confident | best_guess — an identified contact is never treated
    -- as certain; see 22-contact-enrichment/SKILL.md Part A.

CREATE INDEX IF NOT EXISTS idx_social_outreach_contact_priority ON social_outreach(contact_priority);
