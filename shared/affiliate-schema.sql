-- affiliate-schema.sql — 15% affiliate program (licensing server)
--
-- Bachs has no affiliate feature, so attribution lives here. The whole design
-- turns on one number: a chargeback costs USD 30, and a paid-out commission is
-- gone. On a NGN 35,000 sale that combination loses NGN 86,750 — 2.5x the sale.
-- So commissions are EARNED at purchase and PAYABLE only after the refund
-- window closes.

CREATE TABLE IF NOT EXISTS affiliates (
  affiliate_id  TEXT PRIMARY KEY,
  email         TEXT NOT NULL UNIQUE,
  display_name  TEXT,
  code          TEXT NOT NULL UNIQUE,   -- short, human, goes in the URL
  rate          REAL NOT NULL DEFAULT 0.15,
  -- payout destination, per market
  payout_ccy    TEXT NOT NULL,          -- NGN | USD
  payout_detail TEXT,                   -- bank or wallet, encrypted at rest
  status        TEXT NOT NULL DEFAULT 'active',  -- active|paused|banned
  -- an affiliate is usually also a customer; this is how self-referral is caught
  customer_id   TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  banned_reason TEXT
);

-- Attribution. Recorded when the checkout session is created, confirmed when
-- collection.succeeded arrives. Never trust a client-supplied code at
-- confirmation time — read it back from the session you created.
CREATE TABLE IF NOT EXISTS referrals (
  referral_id   TEXT PRIMARY KEY,
  affiliate_id  TEXT NOT NULL REFERENCES affiliates(affiliate_id),
  checkout_id   TEXT NOT NULL UNIQUE,   -- chk_... from Bachs
  landed_at     TEXT NOT NULL,
  ip_country    TEXT,
  converted_at  TEXT,
  payment_id    TEXT                    -- set from the webhook, never the redirect
);

CREATE TABLE IF NOT EXISTS commissions (
  commission_id TEXT PRIMARY KEY,
  affiliate_id  TEXT NOT NULL REFERENCES affiliates(affiliate_id),
  referral_id   TEXT NOT NULL REFERENCES referrals(referral_id),
  licence_id    TEXT NOT NULL,
  sku           TEXT NOT NULL,          -- base | addon-outreach | ...
  gross_amount  TEXT NOT NULL,          -- decimal string, Bachs convention
  currency      TEXT NOT NULL,
  rate          REAL NOT NULL,
  amount        TEXT NOT NULL,          -- gross * rate
  state         TEXT NOT NULL DEFAULT 'held',
  -- held      -> inside the refund window, earned but not payable
  -- payable   -> window closed, waiting for the next payout run
  -- paid      -> sent
  -- clawed    -> refunded or disputed before payout; never paid
  -- reversed  -> refunded AFTER payout; owed back, netted off future earnings
  earned_at     TEXT NOT NULL DEFAULT (datetime('now')),
  payable_at    TEXT NOT NULL,          -- earned_at + refund window
  paid_at       TEXT,
  payout_id     TEXT,
  note          TEXT
);

CREATE TABLE IF NOT EXISTS affiliate_payouts (
  payout_id     TEXT PRIMARY KEY,
  affiliate_id  TEXT NOT NULL REFERENCES affiliates(affiliate_id),
  currency      TEXT NOT NULL,
  gross_amount  TEXT NOT NULL,
  reversals     TEXT NOT NULL DEFAULT '0',   -- netted off prior over-payments
  fee           TEXT NOT NULL,               -- NGN 215 flat, or 1% USD
  net_amount    TEXT NOT NULL,
  state         TEXT NOT NULL DEFAULT 'pending',
  bachs_ref     TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  settled_at    TEXT
);

-- Fraud signals, evaluated before a commission becomes payable. None of these
-- auto-bans; they queue for a human, because a false ban on a genuine
-- affiliate costs more than the commission ever would.
CREATE TABLE IF NOT EXISTS affiliate_flags (
  flag_id      TEXT PRIMARY KEY,
  affiliate_id TEXT NOT NULL REFERENCES affiliates(affiliate_id),
  kind         TEXT NOT NULL,
  -- self_referral        buyer email or fingerprint matches the affiliate
  -- fingerprint_cluster  many referrals from one machine
  -- refund_rate          referred sales refund far above baseline
  -- velocity             implausible conversions in a short window
  detail       TEXT,
  raised_at    TEXT NOT NULL DEFAULT (datetime('now')),
  resolved_at  TEXT,
  resolution   TEXT
);

CREATE INDEX IF NOT EXISTS idx_comm_state ON commissions(state, payable_at);
CREATE INDEX IF NOT EXISTS idx_ref_aff    ON referrals(affiliate_id, converted_at);

-- What is actually owed right now, minimum threshold applied.
-- NGN payout costs a flat NGN 215, so paying a single NGN 5,250 commission
-- burns 4.1% of it. A NGN 10,000 minimum brings that under 2.1%.
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

INSERT OR IGNORE INTO schema_version (filename, note) VALUES
  ('affiliate_schema.sql', '15% affiliate program: codes, attribution, holds, clawbacks, payouts.');
