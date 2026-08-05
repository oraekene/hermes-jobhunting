-- licence-schema.sql — licensing server (your infrastructure, not the user's)
--
-- Separate database from the ledger, on purpose. The ledger holds pseudonymous
-- aggregate counts; this holds names, emails and payment references. Joining
-- them would turn Channel A telemetry into identified personal data and undo
-- the whole privacy design in one foreign key.
--
-- The only link is node_id, which is random and lives here. The ledger never
-- receives it alongside anything identifying.

-- ── who bought what ─────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS customers (
  customer_id   TEXT PRIMARY KEY,
  email         TEXT NOT NULL UNIQUE,
  display_name  TEXT,
  country       TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  -- NDPA 2023: a data subject can demand deletion. Purge must be executable
  -- without breaking the ledger, which is why the ledger holds no PII at all.
  deleted_at    TEXT
);

CREATE TABLE IF NOT EXISTS licences (
  licence_id    TEXT PRIMARY KEY,       -- shown to the customer
  customer_id   TEXT NOT NULL REFERENCES customers(customer_id),
  plan          TEXT NOT NULL,          -- core | core_plus | full
  status        TEXT NOT NULL,          -- active | lapsed | refunded | revoked
  seats         INTEGER NOT NULL DEFAULT 1,
  currency      TEXT NOT NULL DEFAULT 'NGN',
  amount        INTEGER NOT NULL,       -- minor units
  payment_ref   TEXT,                   -- Paystack/Flutterwave reference
  issued_at     TEXT NOT NULL DEFAULT (datetime('now')),
  expires_at    TEXT,                   -- NULL = perpetual core
  revoked_at    TEXT,
  revoke_reason TEXT
);

-- One row per installed machine. Seat binding is deliberately forgiving:
-- people reinstall, replace laptops, and lose phones. A licensing system that
-- treats every rebind as fraud generates more support cost than the piracy it
-- prevents, and at a few hundred customers support cost is what kills you.
CREATE TABLE IF NOT EXISTS seats (
  seat_id       TEXT PRIMARY KEY,
  licence_id    TEXT NOT NULL REFERENCES licences(licence_id),
  node_id       TEXT NOT NULL UNIQUE,   -- the ONLY value shared with the ledger
  fingerprint   TEXT NOT NULL,          -- salted hash of stable machine facts
  public_key    TEXT NOT NULL,
  watermark     TEXT NOT NULL,          -- per-seat salt baked into the build
  activated_at  TEXT NOT NULL DEFAULT (datetime('now')),
  last_seen_at  TEXT,
  released_at   TEXT,                   -- self-service, no support ticket
  rebind_count  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS activations (
  activation_id TEXT PRIMARY KEY,
  licence_id    TEXT NOT NULL,
  seat_id       TEXT,
  outcome       TEXT NOT NULL,   -- granted | seat_limit | revoked | unknown_licence | rate_limited
  ip_country    TEXT,            -- country only; never a full address
  at            TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ── what they can use ───────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS entitlements (
  licence_id  TEXT NOT NULL REFERENCES licences(licence_id),
  addon_id    TEXT NOT NULL,     -- addon-interview | addon-outreach | ...
  source      TEXT NOT NULL,     -- purchase | trial | comp | bundled
  granted_at  TEXT NOT NULL DEFAULT (datetime('now')),
  expires_at  TEXT,              -- NULL = permanent
  PRIMARY KEY (licence_id, addon_id, source)
);

-- The week-3 automatic trial. Scheduled at activation rather than triggered
-- later, so it survives the scheduler being down for a day.
CREATE TABLE IF NOT EXISTS trials (
  licence_id  TEXT PRIMARY KEY REFERENCES licences(licence_id),
  starts_at   TEXT NOT NULL,     -- activation + 14 days
  ends_at     TEXT NOT NULL,     -- starts + 7 days
  state       TEXT NOT NULL DEFAULT 'scheduled',  -- scheduled|running|ended|skipped
  addons      TEXT NOT NULL      -- JSON array
);

-- What they actually USED during the trial. This is the whole point: a
-- reminder listing six addons is ignorable; "you built 11 outreach drafts,
-- here is what those are doing now" is not.
CREATE TABLE IF NOT EXISTS trial_usage (
  licence_id  TEXT NOT NULL REFERENCES licences(licence_id),
  addon_id    TEXT NOT NULL,
  uses        INTEGER NOT NULL DEFAULT 0,
  artefacts   INTEGER NOT NULL DEFAULT 0,   -- things they made and still own
  last_used   TEXT,
  PRIMARY KEY (licence_id, addon_id)
);

-- ── delivery ────────────────────────────────────────────────────────────────

-- Skills are fetched at activation, not shipped in the installer, so there is
-- nothing to forward before a licence exists.
CREATE TABLE IF NOT EXISTS bundles (
  bundle_id   TEXT PRIMARY KEY,
  scope       TEXT NOT NULL,     -- core | addon-outreach | ...
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

-- A leaked copy carries its buyer's watermark. At a few hundred customers this
-- deters sharing better than obfuscation, because the deterrent is social.
CREATE TABLE IF NOT EXISTS watermark_sightings (
  sighting_id TEXT PRIMARY KEY,
  watermark   TEXT NOT NULL,
  seat_id     TEXT,
  found_where TEXT NOT NULL,
  at          TEXT NOT NULL DEFAULT (datetime('now')),
  action      TEXT               -- contacted | revoked | ignored
);

CREATE INDEX IF NOT EXISTS idx_seats_licence   ON seats(licence_id);
CREATE INDEX IF NOT EXISTS idx_ent_licence     ON entitlements(licence_id);
CREATE INDEX IF NOT EXISTS idx_activations_lic ON activations(licence_id, at);

-- Effective entitlements, trials included, expiries respected.
CREATE VIEW IF NOT EXISTS v_effective_entitlements AS
SELECT e.licence_id, e.addon_id,
       MAX(CASE WHEN e.source = 'trial' THEN 0 ELSE 1 END) AS permanent
FROM   entitlements e
JOIN   licences l ON l.licence_id = e.licence_id
WHERE  l.status = 'active'
  AND  (l.expires_at IS NULL OR l.expires_at > datetime('now'))
  AND  (e.expires_at IS NULL OR e.expires_at > datetime('now'))
GROUP BY e.licence_id, e.addon_id;
