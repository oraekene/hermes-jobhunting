-- schema.sql — D1 schema for hermes-licensing worker
-- Derived from shared/licence-schema.sql

CREATE TABLE IF NOT EXISTS customers (
  customer_id   TEXT PRIMARY KEY,
  email         TEXT NOT NULL UNIQUE,
  display_name  TEXT,
  country       TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  deleted_at    TEXT
);

CREATE TABLE IF NOT EXISTS licences (
  licence_id    TEXT PRIMARY KEY,
  customer_id   TEXT NOT NULL REFERENCES customers(customer_id),
  plan          TEXT NOT NULL,
  status        TEXT NOT NULL,
  seats         INTEGER NOT NULL DEFAULT 1,
  currency      TEXT NOT NULL DEFAULT 'NGN',
  amount        INTEGER NOT NULL,
  payment_ref   TEXT,
  issued_at     TEXT NOT NULL DEFAULT (datetime('now')),
  expires_at    TEXT,
  revoked_at    TEXT,
  revoke_reason TEXT
);

CREATE TABLE IF NOT EXISTS seats (
  seat_id       TEXT PRIMARY KEY,
  licence_id    TEXT NOT NULL REFERENCES licences(licence_id),
  node_id       TEXT NOT NULL UNIQUE,
  fingerprint   TEXT NOT NULL,
  public_key    TEXT NOT NULL,
  watermark     TEXT NOT NULL,
  activated_at  TEXT NOT NULL DEFAULT (datetime('now')),
  last_seen_at  TEXT,
  released_at   TEXT,
  rebind_count  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS activations (
  activation_id TEXT PRIMARY KEY,
  licence_id    TEXT NOT NULL,
  seat_id       TEXT,
  outcome       TEXT NOT NULL,
  ip_country    TEXT,
  at            TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS entitlements (
  licence_id  TEXT NOT NULL REFERENCES licences(licence_id),
  addon_id    TEXT NOT NULL,
  source      TEXT NOT NULL,
  granted_at  TEXT NOT NULL DEFAULT (datetime('now')),
  expires_at  TEXT,
  PRIMARY KEY (licence_id, addon_id, source)
);

CREATE TABLE IF NOT EXISTS trials (
  licence_id  TEXT PRIMARY KEY REFERENCES licences(licence_id),
  starts_at   TEXT NOT NULL,
  ends_at     TEXT NOT NULL,
  state       TEXT NOT NULL DEFAULT 'scheduled',
  addons      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS trial_usage (
  licence_id  TEXT NOT NULL REFERENCES licences(licence_id),
  addon_id    TEXT NOT NULL,
  uses        INTEGER NOT NULL DEFAULT 0,
  artefacts   INTEGER NOT NULL DEFAULT 0,
  last_used   TEXT,
  PRIMARY KEY (licence_id, addon_id)
);

CREATE TABLE IF NOT EXISTS bundles (
  bundle_id   TEXT PRIMARY KEY,
  scope       TEXT NOT NULL,
  version     TEXT NOT NULL,
  sha256      TEXT NOT NULL,
  signature   TEXT NOT NULL,
  min_core    TEXT,
  published_at TEXT NOT NULL DEFAULT (datetime('now')),
  yanked_at   TEXT
);

CREATE TABLE IF NOT EXISTS downloads (
  seat_id    TEXT NOT NULL REFERENCES seats(seat_id),
  bundle_id  TEXT NOT NULL REFERENCES bundles(bundle_id),
  at         TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (seat_id, bundle_id, at)
);

CREATE TABLE IF NOT EXISTS watermark_sightings (
  sighting_id TEXT PRIMARY KEY,
  watermark   TEXT NOT NULL,
  seat_id     TEXT,
  found_where TEXT NOT NULL,
  at          TEXT NOT NULL DEFAULT (datetime('now')),
  action      TEXT
);

CREATE INDEX IF NOT EXISTS idx_seats_licence   ON seats(licence_id);
CREATE INDEX IF NOT EXISTS idx_ent_licence     ON entitlements(licence_id);
CREATE INDEX IF NOT EXISTS idx_activations_lic ON activations(licence_id, at);

CREATE VIEW IF NOT EXISTS v_effective_entitlements AS
SELECT e.licence_id, e.addon_id,
       MAX(CASE WHEN e.source = 'trial' THEN 0 ELSE 1 END) AS permanent
FROM   entitlements e
JOIN   licences l ON l.licence_id = e.licence_id
WHERE  l.status = 'active'
  AND  (l.expires_at IS NULL OR l.expires_at > datetime('now'))
  AND  (e.expires_at IS NULL OR e.expires_at > datetime('now'))
GROUP BY e.licence_id, e.addon_id;

-- ── federated learning ──────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS nodes (
  node_id           TEXT PRIMARY KEY,
  licence_id        TEXT NOT NULL,
  public_key        TEXT NOT NULL,
  first_seen_at     TEXT NOT NULL,
  last_seen_at      TEXT,
  reputation        REAL NOT NULL DEFAULT 1.0,
  channel_a_consent INTEGER NOT NULL DEFAULT 1,
  suspended         INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS cells (
  cell_key   TEXT PRIMARY KEY,
  depth      INTEGER NOT NULL,
  parent_key TEXT REFERENCES cells(cell_key)
);

CREATE TABLE IF NOT EXISTS arms (
  arm_id      TEXT PRIMARY KEY,
  family      TEXT NOT NULL,
  version     INTEGER NOT NULL DEFAULT 1,
  description TEXT NOT NULL,
  origin      TEXT NOT NULL,
  created_at  TEXT NOT NULL,
  retired_at  TEXT
);

CREATE TABLE IF NOT EXISTS cell_evidence (
  cell_key    TEXT NOT NULL REFERENCES cells(cell_key),
  arm_id      TEXT NOT NULL REFERENCES arms(arm_id),
  model_tier  TEXT NOT NULL,
  successes   REAL NOT NULL DEFAULT 0,
  trials      REAL NOT NULL DEFAULT 0,
  n_nodes     INTEGER NOT NULL DEFAULT 0,
  updated_at  TEXT NOT NULL,
  PRIMARY KEY (cell_key, arm_id, model_tier)
);

CREATE TABLE IF NOT EXISTS priors (
  cell_key      TEXT NOT NULL REFERENCES cells(cell_key),
  arm_id        TEXT NOT NULL REFERENCES arms(arm_id),
  alpha         REAL NOT NULL,
  beta          REAL NOT NULL,
  strength_cap  REAL NOT NULL DEFAULT 150,
  tiers_won     INTEGER NOT NULL DEFAULT 0,
  published_at  TEXT NOT NULL,
  signature     TEXT NOT NULL,
  PRIMARY KEY (cell_key, arm_id)
);

CREATE TABLE IF NOT EXISTS dead_arms (
  arm_id      TEXT NOT NULL REFERENCES arms(arm_id),
  cell_key    TEXT NOT NULL REFERENCES cells(cell_key),
  reason      TEXT NOT NULL,
  evidence_n  INTEGER NOT NULL,
  declared_at TEXT NOT NULL,
  signature   TEXT NOT NULL,
  PRIMARY KEY (arm_id, cell_key)
);

CREATE TABLE IF NOT EXISTS adoption_history (
  arm_id       TEXT NOT NULL REFERENCES arms(arm_id),
  cell_key     TEXT NOT NULL REFERENCES cells(cell_key),
  week         TEXT NOT NULL,
  adoption     REAL NOT NULL,
  success_rate REAL NOT NULL,
  PRIMARY KEY (arm_id, cell_key, week)
);

CREATE TABLE IF NOT EXISTS arm_candidates (
  candidate_id TEXT PRIMARY KEY,
  family       TEXT NOT NULL,
  proposal     TEXT NOT NULL,
  sources      TEXT NOT NULL,
  found_at     TEXT NOT NULL,
  reviewed_by  TEXT,
  status       TEXT NOT NULL DEFAULT 'pending'
);

CREATE INDEX IF NOT EXISTS idx_evidence_arm ON cell_evidence(arm_id);
CREATE INDEX IF NOT EXISTS idx_adoption_week ON adoption_history(week);

-- ── affiliate program ───────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS affiliates (
  affiliate_id  TEXT PRIMARY KEY,
  email         TEXT NOT NULL UNIQUE,
  display_name  TEXT,
  code          TEXT NOT NULL UNIQUE,
  rate          REAL NOT NULL DEFAULT 0.15,
  payout_ccy    TEXT NOT NULL,
  payout_detail TEXT,
  status        TEXT NOT NULL DEFAULT 'active',
  customer_id   TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  banned_reason TEXT
);

CREATE TABLE IF NOT EXISTS referrals (
  referral_id   TEXT PRIMARY KEY,
  affiliate_id  TEXT NOT NULL REFERENCES affiliates(affiliate_id),
  checkout_id   TEXT NOT NULL UNIQUE,
  landed_at     TEXT NOT NULL,
  ip_country    TEXT,
  converted_at  TEXT,
  payment_id    TEXT
);

CREATE TABLE IF NOT EXISTS commissions (
  commission_id TEXT PRIMARY KEY,
  affiliate_id  TEXT NOT NULL REFERENCES affiliates(affiliate_id),
  referral_id   TEXT NOT NULL REFERENCES referrals(referral_id),
  licence_id    TEXT NOT NULL,
  sku           TEXT NOT NULL,
  gross_amount  TEXT NOT NULL,
  currency      TEXT NOT NULL,
  rate          REAL NOT NULL,
  amount        TEXT NOT NULL,
  state         TEXT NOT NULL DEFAULT 'held',
  earned_at     TEXT NOT NULL DEFAULT (datetime('now')),
  payable_at    TEXT NOT NULL,
  paid_at       TEXT,
  payout_id     TEXT,
  note          TEXT
);

CREATE TABLE IF NOT EXISTS affiliate_payouts (
  payout_id     TEXT PRIMARY KEY,
  affiliate_id  TEXT NOT NULL REFERENCES affiliates(affiliate_id),
  currency      TEXT NOT NULL,
  gross_amount  TEXT NOT NULL,
  reversals     TEXT NOT NULL DEFAULT '0',
  fee           TEXT NOT NULL,
  net_amount    TEXT NOT NULL,
  state         TEXT NOT NULL DEFAULT 'pending',
  bachs_ref     TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  settled_at    TEXT
);

CREATE TABLE IF NOT EXISTS affiliate_flags (
  flag_id      TEXT PRIMARY KEY,
  affiliate_id TEXT NOT NULL REFERENCES affiliates(affiliate_id),
  kind         TEXT NOT NULL,
  detail       TEXT,
  raised_at    TEXT NOT NULL DEFAULT (datetime('now')),
  resolved_at  TEXT,
  resolution   TEXT
);

CREATE INDEX IF NOT EXISTS idx_comm_state ON commissions(state, payable_at);
CREATE INDEX IF NOT EXISTS idx_ref_aff    ON referrals(affiliate_id, converted_at);

CREATE VIEW IF NOT EXISTS v_payable AS
SELECT a.affiliate_id, a.email, a.payout_ccy,
       COUNT(*)                            AS commissions,
       SUM(CAST(c.amount AS REAL))         AS total
FROM   commissions c
JOIN   affiliates  a ON a.affiliate_id = c.affiliate_id
WHERE  c.state = 'payable'
  AND  a.status = 'active'
GROUP BY a.affiliate_id
HAVING (a.payout_ccy = 'NGN' AND total >= 10000)
    OR (a.payout_ccy = 'USD' AND total >= 50);
