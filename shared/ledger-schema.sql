-- ledger-schema.sql — federated self-improvement
--
-- Two halves. The CENTRAL half lives on your server and is the thing a pirated
-- copy cannot have. The LOCAL half is addendum_22 in the existing chain (21 is
-- reserved for the schema_version backfill in PACKAGING.md).
--
-- Design rule running through all of it: the ledger ships PRIORS and DEAD
-- LISTS, never verdicts. A node keeps its own posterior and makes its own
-- decisions. That is what makes a wrong or poisoned ledger entry recoverable
-- instead of executed.

-- ═════════════════════════════════════════════════════════════════════════
-- CENTRAL  (your server)
-- ═════════════════════════════════════════════════════════════════════════

-- Nodes. No name, no email, no resume — a licence and a public key.
CREATE TABLE IF NOT EXISTS nodes (
  node_id           TEXT PRIMARY KEY,      -- random, not derived from anything
  licence_id        TEXT NOT NULL,
  public_key        TEXT NOT NULL,
  first_seen_at     TEXT NOT NULL,
  last_seen_at      TEXT,
  reputation        REAL NOT NULL DEFAULT 1.0,  -- down-weights outliers/sybils
  channel_a_consent INTEGER NOT NULL DEFAULT 1, -- aggregate telemetry, opt-out
  suspended         INTEGER NOT NULL DEFAULT 0
);

-- The context space, deliberately small. Five dimensions, ordered by how
-- strongly each is expected to moderate WHICH TACTIC WINS. Every additional
-- dimension multiplies cells and divides evidence, so the ~55 other logged
-- fields stay diagnostics and stay out of here.
CREATE TABLE IF NOT EXISTS cells (
  cell_key   TEXT PRIMARY KEY,   -- "global" | "ats_platform=greenhouse" | "...|industry=saas"
  depth      INTEGER NOT NULL,   -- 0..4, position in the hierarchy
  parent_key TEXT REFERENCES cells(cell_key)
);

-- An arm is a tactic the pipeline can choose between, versioned.
CREATE TABLE IF NOT EXISTS arms (
  arm_id      TEXT PRIMARY KEY,
  family      TEXT NOT NULL,   -- resume | letter | answers | outreach | timing | style
  version     INTEGER NOT NULL DEFAULT 1,
  description TEXT NOT NULL,
  origin      TEXT NOT NULL,   -- incumbent | tier1_correlation | tier2_gepa | tier3_research
  created_at  TEXT NOT NULL,
  retired_at  TEXT
);

-- Aggregate evidence. Counts only — never a document, never an employer name,
-- never anything a person wrote. Stratified by model tier, because the outcome
-- label is model-independent (an employer decided, not an LLM) while execution
-- fidelity is not.
CREATE TABLE IF NOT EXISTS cell_evidence (
  cell_key    TEXT NOT NULL REFERENCES cells(cell_key),
  arm_id      TEXT NOT NULL REFERENCES arms(arm_id),
  model_tier  TEXT NOT NULL,          -- frontier | mid | small | unknown
  successes   REAL NOT NULL DEFAULT 0,
  trials      REAL NOT NULL DEFAULT 0,
  n_nodes     INTEGER NOT NULL DEFAULT 0,
  updated_at  TEXT NOT NULL,
  PRIMARY KEY (cell_key, arm_id, model_tier)
);

-- What actually gets pushed to nodes. A distribution with a strength cap, not
-- an instruction. strength_cap is THE design dial: it buys decision quality
-- and costs fleet homogeneity, and the two cannot be separated.
CREATE TABLE IF NOT EXISTS priors (
  cell_key      TEXT NOT NULL REFERENCES cells(cell_key),
  arm_id        TEXT NOT NULL REFERENCES arms(arm_id),
  alpha         REAL NOT NULL,
  beta          REAL NOT NULL,
  strength_cap  REAL NOT NULL DEFAULT 150,  -- pseudo-observations; see sweep.py
  tiers_won     INTEGER NOT NULL DEFAULT 0, -- >= 2 required for global promotion
  published_at  TEXT NOT NULL,
  signature     TEXT NOT NULL,              -- every push is signed
  PRIMARY KEY (cell_key, arm_id)
);

-- Negative sharing. Safe to distribute globally, valuable immediately, and it
-- creates no shared signature because it says what NOT to do rather than what
-- to do. Where confidence is low, share only this half.
CREATE TABLE IF NOT EXISTS dead_arms (
  arm_id      TEXT NOT NULL REFERENCES arms(arm_id),
  cell_key    TEXT NOT NULL REFERENCES cells(cell_key),
  reason      TEXT NOT NULL,   -- underperforms | detected | platform_changed | policy
  evidence_n  INTEGER NOT NULL,
  declared_at TEXT NOT NULL,
  signature   TEXT NOT NULL,
  PRIMARY KEY (arm_id, cell_key)
);

-- Adoption vs performance, which is how decay is detected. A negative slope
-- against rising adoption is the signature of a tactic being pattern-matched
-- by the other side, and it is separable from noise precisely because
-- adoption is a variable you control.
CREATE TABLE IF NOT EXISTS adoption_history (
  arm_id       TEXT NOT NULL REFERENCES arms(arm_id),
  cell_key     TEXT NOT NULL REFERENCES cells(cell_key),
  week         TEXT NOT NULL,
  adoption     REAL NOT NULL,   -- share of fleet applications using this arm
  success_rate REAL NOT NULL,
  PRIMARY KEY (arm_id, cell_key, week)
);

-- Candidate arms from research. Tier 3 PROPOSES; it never edits. Research
-- generates hypotheses, data selects among them — without that separation the
-- system rewrites itself based on what was upvoted last week.
CREATE TABLE IF NOT EXISTS arm_candidates (
  candidate_id TEXT PRIMARY KEY,
  family       TEXT NOT NULL,
  proposal     TEXT NOT NULL,
  sources      TEXT NOT NULL,   -- JSON: where the claim came from
  found_at     TEXT NOT NULL,
  reviewed_by  TEXT,            -- a human, always
  status       TEXT NOT NULL DEFAULT 'pending'  -- pending|accepted|rejected
);

CREATE INDEX IF NOT EXISTS idx_evidence_arm ON cell_evidence(arm_id);
CREATE INDEX IF NOT EXISTS idx_adoption_week ON adoption_history(week);

-- ═════════════════════════════════════════════════════════════════════════
-- LOCAL  (addendum_22, on the user's machine)
-- ═════════════════════════════════════════════════════════════════════════

-- Which arm each application actually used, and why. Without the arm and the
-- context recorded at send time, no outcome arriving weeks later can be
-- attributed to anything.
CREATE TABLE IF NOT EXISTS application_arms (
  application_id INTEGER NOT NULL,
  arm_id         TEXT NOT NULL,
  family         TEXT NOT NULL,
  cell_key       TEXT NOT NULL,
  mode           TEXT NOT NULL,   -- explore | exploit
  model_tier     TEXT NOT NULL,
  chosen_at      TEXT NOT NULL,
  PRIMARY KEY (application_id, family)
);

-- The node's own posterior. Survives being cut off from the ledger — with no
-- connection this is simply an uninformative prior, and the node behaves
-- exactly like today's siloed system. That fallback is what makes the whole
-- design safe to ship.
CREATE TABLE IF NOT EXISTS local_posterior (
  cell_key   TEXT NOT NULL,
  arm_id     TEXT NOT NULL,
  successes  REAL NOT NULL DEFAULT 0,
  trials     REAL NOT NULL DEFAULT 0,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (cell_key, arm_id)
);

-- Priors as received, kept separate from local evidence so the two are always
-- distinguishable and a bad push can be dropped without losing your own data.
CREATE TABLE IF NOT EXISTS received_priors (
  cell_key     TEXT NOT NULL,
  arm_id       TEXT NOT NULL,
  alpha        REAL NOT NULL,
  beta         REAL NOT NULL,
  received_at  TEXT NOT NULL,
  signature_ok INTEGER NOT NULL,
  applied      INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (cell_key, arm_id)
);

CREATE TABLE IF NOT EXISTS received_dead_arms (
  arm_id      TEXT NOT NULL,
  cell_key    TEXT NOT NULL,
  reason      TEXT NOT NULL,
  received_at TEXT NOT NULL,
  PRIMARY KEY (arm_id, cell_key)
);

-- Exactly what leaves the machine, staged for inspection before it goes.
-- The user can read this table. That is the point: Channel A is counts and
-- cell keys, and anyone who wants to check can.
CREATE TABLE IF NOT EXISTS outbound_telemetry (
  batch_id   TEXT PRIMARY KEY,
  payload    TEXT NOT NULL,   -- JSON: cell_key, arm_id, model_tier, successes, trials
  created_at TEXT NOT NULL,
  sent_at    TEXT,
  bytes      INTEGER
);

INSERT OR IGNORE INTO schema_version (filename, note) VALUES
  ('applications_db_schema_addendum_22.sql',
   'Federated self-improvement: arm assignment, local posterior, received priors, outbound telemetry.');
