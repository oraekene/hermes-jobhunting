/**
 * worker/src/delivery.js — the pieces between a payment and a working install.
 *
 *   downloadBundle   GET  /v1/bundles/:id     stream from R2 against entitlement
 *   sendLicenceEmail                          the one email that cannot be Telegram
 *   payoutRun        cron                     affiliate commissions -> payouts
 *   adminHandler     GET  /v1/admin/*         read-only view of everything
 */

const json = (o, s = 200) =>
  new Response(JSON.stringify(o), { status: s, headers: { "content-type": "application/json" } });
const err = (m, s = 400) => json({ error: m }, s);

const iso = (t = Date.now()) => new Date(t).toISOString();
const uid = () => crypto.randomUUID().replace(/-/g, "").slice(0, 24);

// ── bundle download ─────────────────────────────────────────────────────────

export async function downloadBundle(req, env, claims, bundleId) {
  const b = await env.DB.prepare(
    `SELECT bundle_id, scope, version, sha256 FROM bundles
      WHERE bundle_id = ? AND yanked_at IS NULL`).bind(bundleId).first();
  if (!b) return err("unknown bundle", 404);

  // Entitlement is re-read from the database, never taken from the token. The
  // token proves who is asking; it is not authority over what they may have.
  if (b.scope !== "core") {
    const ent = await env.DB.prepare(
      `SELECT 1 FROM entitlements
        WHERE licence_id = ? AND addon_id = ?
          AND (expires_at IS NULL OR expires_at > datetime('now'))`
    ).bind(claims.lic, b.scope).first();
    if (!ent) return err("not entitled", 403);
  }

  // Per-seat bundle first — it carries this buyer's watermark. Fall back to the
  // core template only when the seat build has not landed yet.
  const seatKey = `${claims.seat}/${b.scope}-${b.version}.tar.gz`;
  const sharedKey = `core-template/${b.scope}-${b.version}.tar.gz`;
  let obj = await env.BUNDLES.get(seatKey);
  let watermarked = true;
  if (!obj) {
    obj = await env.BUNDLES.get(sharedKey);
    watermarked = false;
  }
  if (!obj) return err("bundle not built yet", 503);

  await env.DB.prepare(
    `INSERT INTO downloads (seat_id, bundle_id, at) VALUES (?,?,?)`
  ).bind(claims.seat, b.bundle_id, iso()).run();

  return new Response(obj.body, {
    headers: {
      "content-type": "application/gzip",
      "content-disposition": `attachment; filename="${b.scope}-${b.version}.tar.gz"`,
      "x-bundle-sha256": b.sha256,
      "x-watermarked": String(watermarked),
      "cache-control": "private, no-store",
    },
  });
}

/** Ask GitHub Actions to build this seat's bundles. Fire and forget. */
export async function requestSeatBuild(env, seatId) {
  if (!env.GITHUB_TOKEN) return;
  try {
    await fetch(
      `https://api.github.com/repos/${env.GITHUB_REPO}/actions/workflows/release.yml/dispatches`,
      {
        method: "POST",
        headers: {
          authorization: `Bearer ${env.GITHUB_TOKEN}`,
          accept: "application/vnd.github+json",
          "user-agent": "hermes-licensing",
          "content-type": "application/json",
        },
        body: JSON.stringify({ ref: "main", inputs: { seat: seatId } }),
      });
  } catch (e) {
    // A failed build request must never fail an activation — the customer can
    // still download the core template while the seat build catches up.
    console.error("seat build dispatch failed", e?.message);
  }
}

// ── email ───────────────────────────────────────────────────────────────────

async function resend(env, { to, subject, text }) {
  if (!env.RESEND_KEY) {
    console.error("RESEND_KEY unset — would have emailed", to, subject);
    return false;
  }
  const r = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { authorization: `Bearer ${env.RESEND_KEY}`,
               "content-type": "application/json" },
    body: JSON.stringify({ from: env.MAIL_FROM, to: [to], subject, text }),
  });
  if (!r.ok) console.error("resend failed", r.status, await r.text());
  return r.ok;
}

/**
 * The one email that cannot ride Telegram: there is no Telegram chat yet at the
 * moment of purchase. Plain text on purpose — it survives every client, it does
 * not look like marketing, and nothing in it can be mistaken for a phishing
 * template.
 */
export async function sendLicenceEmail(env, { to, licenceId }) {
  return resend(env, {
    to,
    subject: "Your licence key",
    text:
`Thanks for buying.

Your licence key:

    ${licenceId}

To set up, run the installer and paste that key when it asks.

    ${env.SITE_URL}/install

Keep this email. The key is how you move to a new machine later — you can do
that yourself up to three times a year, no need to ask me.

If anything goes wrong, reply to this email. It reaches a person.
`,
  });
}

export async function sendPayoutEmail(env, { to, amount, currency, count }) {
  return resend(env, {
    to,
    subject: `Affiliate payout sent — ${currency} ${amount}`,
    text:
`Your affiliate payout has been sent.

    Amount:      ${currency} ${amount}
    Commissions: ${count}

Payouts run monthly for balances over the minimum. Commissions are held for 30
days after each sale so refunds settle first — that is why a recent sale may not
appear on this one.
`,
  });
}

// ── affiliate payouts ───────────────────────────────────────────────────────

const MIN_PAYOUT = { NGN: 10000, USD: 50 };
const PAYOUT_FEE = { NGN: 215, USD: null };   // USD is 1%, computed below

/**
 * Monthly. Pays commissions that have cleared the refund window, netting off
 * anything reversed by a later refund.
 *
 * The threshold is not tidiness: an NGN payout costs a flat 215, so paying one
 * 5,250 commission on its own burns 4.1% of it. A 10,000 minimum brings that
 * under 2.1%.
 */
export async function payoutRun(env, { dryRun = false } = {}) {
  const { results: due } = await env.DB.prepare(
    `SELECT a.affiliate_id, a.email, a.payout_ccy,
            SUM(CASE WHEN c.state = 'payable'  THEN CAST(c.amount AS REAL) ELSE 0 END) AS owed,
            SUM(CASE WHEN c.state = 'reversed' THEN CAST(c.amount AS REAL) ELSE 0 END) AS back,
            COUNT(CASE WHEN c.state = 'payable' THEN 1 END) AS n
       FROM affiliates a
       JOIN commissions c ON c.affiliate_id = a.affiliate_id
      WHERE a.status = 'active' AND c.state IN ('payable','reversed')
      GROUP BY a.affiliate_id`).all();

  const paid = [];
  for (const row of due || []) {
    const gross = (row.owed || 0) - (row.back || 0);
    if (gross <= 0) continue;
    if (gross < (MIN_PAYOUT[row.payout_ccy] ?? Infinity)) continue;

    const fee = row.payout_ccy === "NGN" ? PAYOUT_FEE.NGN : gross * 0.01;
    const net = gross - fee;
    const payoutId = uid();

    if (!dryRun) {
      await env.DB.prepare(
        `INSERT INTO affiliate_payouts (payout_id, affiliate_id, currency,
           gross_amount, reversals, fee, net_amount, state)
         VALUES (?,?,?,?,?,?,?,'pending')`
      ).bind(payoutId, row.affiliate_id, row.payout_ccy, String(row.owed || 0),
             String(row.back || 0), String(fee), net.toFixed(2)).run();

      await env.DB.prepare(
        `UPDATE commissions SET state = 'paid', paid_at = ?, payout_id = ?
          WHERE affiliate_id = ? AND state = 'payable'`
      ).bind(iso(), payoutId, row.affiliate_id).run();

      // Reversals are consumed once netted off, so they cannot be deducted twice.
      await env.DB.prepare(
        `UPDATE commissions SET state = 'settled', payout_id = ?
          WHERE affiliate_id = ? AND state = 'reversed'`
      ).bind(payoutId, row.affiliate_id).run();

      await sendPayoutEmail(env, { to: row.email, amount: net.toFixed(2),
                                   currency: row.payout_ccy, count: row.n });
    }
    paid.push({ affiliate_id: row.affiliate_id, currency: row.payout_ccy,
                gross, fee, net, commissions: row.n, payout_id: payoutId });
  }
  return paid;
}

// ── admin ───────────────────────────────────────────────────────────────────

const Q = {
  summary: `
    SELECT (SELECT COUNT(*) FROM licences WHERE status='active')            AS active_licences,
           (SELECT COUNT(*) FROM licences WHERE status='refunded')          AS refunded,
           (SELECT COUNT(*) FROM seats WHERE released_at IS NULL)           AS active_seats,
           (SELECT COUNT(*) FROM entitlements WHERE source='purchase')      AS addons_bought,
           (SELECT COUNT(*) FROM entitlements WHERE source='trial')         AS addons_on_trial,
           (SELECT COUNT(*) FROM trials WHERE state='running')              AS trials_running,
           (SELECT COUNT(*) FROM commissions WHERE state='held')            AS comm_held,
           (SELECT COUNT(*) FROM commissions WHERE state='payable')         AS comm_payable`,
  sales: `
    SELECT l.licence_id, c.email, l.currency, l.amount/100.0 AS amount,
           l.status, l.issued_at
      FROM licences l JOIN customers c USING (customer_id)
     ORDER BY l.issued_at DESC LIMIT 100`,
  // Trial conversion, split by market — the number that answers whether the
  // Nigerian addon price is too high. It is a question about the price, and
  // only this query can answer it.
  trial_conversion: `
    SELECT c.country AS market,
           COUNT(DISTINCT t.licence_id) AS trials,
           COUNT(DISTINCT CASE WHEN e.source='purchase' AND e.addon_id LIKE 'addon-%'
                               THEN e.licence_id END) AS converted
      FROM trials t
      JOIN licences l USING (licence_id)
      JOIN customers c USING (customer_id)
      LEFT JOIN entitlements e ON e.licence_id = t.licence_id
     WHERE t.state = 'ended'
     GROUP BY c.country`,
  affiliates: `
    SELECT a.code, a.email, a.payout_ccy,
           COUNT(DISTINCT r.referral_id)                                  AS referrals,
           COUNT(DISTINCT r.payment_id)                                   AS conversions,
           SUM(CASE WHEN cm.state='payable' THEN CAST(cm.amount AS REAL) END) AS payable
      FROM affiliates a
      LEFT JOIN referrals   r  ON r.affiliate_id  = a.affiliate_id
      LEFT JOIN commissions cm ON cm.affiliate_id = a.affiliate_id
     GROUP BY a.affiliate_id`,
  ledger: `
    SELECT cell_key, arm_id, model_tier, successes, trials
      FROM cell_evidence ORDER BY trials DESC LIMIT 50`,
};

export async function adminHandler(req, env, path) {
  // Bearer token, not a login. One operator, no session management, no cookie
  // to steal. If this ever grows past you, replace it with Cloudflare Access.
  const auth = (req.headers.get("authorization") || "").replace(/^Bearer /, "");
  if (!env.ADMIN_TOKEN || auth !== env.ADMIN_TOKEN) return err("unauthorised", 401);

  const view = path.replace("/v1/admin/", "") || "summary";
  if (view === "payouts-preview") {
    return json({ would_pay: await payoutRun(env, { dryRun: true }) });
  }
  if (!Q[view]) return err(`unknown view. try: ${Object.keys(Q).join(", ")}`, 404);
  const { results } = await env.DB.prepare(Q[view]).all();
  return json({ view, rows: results || [] });
}
