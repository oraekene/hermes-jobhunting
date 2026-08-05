/**
 * worker/src/index.js — the whole server side, in one Worker.
 *
 * Endpoints
 *   POST /v1/checkout          create a Bachs session; market decided HERE
 *   POST /v1/webhooks/bachs    the only thing that creates a licence
 *   POST /v1/activate          licence + fingerprint -> seat + entitlement token
 *   POST /v1/refresh           seat -> fresh token (also where revocation lands)
 *   POST /v1/seats/release     self-service, no support ticket
 *   GET  /v1/bundles           what this seat may download
 *   POST /v1/telemetry         Channel A counts
 *   POST /v1/ledger/sync       priors + dead list — the real licence check
 *
 * Two rules run through everything:
 *   1. The client never chooses. Not the product, not the market, not the
 *      price, not its own entitlements. Anything a client could lie about is
 *      decided or verified here.
 *   2. Webhooks are the source of truth. A redirect is a hint; a signed
 *      webhook is a fact.
 */

import { signToken, verifyToken, verifyWebhook, b64url } from "./crypto.js";
import { downloadBundle, requestSeatBuild, sendLicenceEmail,
         payoutRun, adminHandler } from "./delivery.js";

const json = (o, status = 200) =>
  new Response(JSON.stringify(o), {
    status,
    headers: { "content-type": "application/json" },
  });

const err = (msg, status = 400) => json({ error: msg }, status);

// ── catalogue ───────────────────────────────────────────────────────────────
// Bachs allows one primary currency per product and NGN cannot be a currency
// option on a USD product. So each SKU exists twice and we pick.
const CATALOG = {
  base: { NG: "prod_9bca8de5a3604d1fa813", INT: "prod_92bc1cb4ff014db49966" },
  "addon-interview": { NG: "prod_256c8a2e733345f9bfea", INT: "prod_2930ed2d84384e24b1f7" },
  "addon-outreach": { NG: "prod_fd50f2e4bb374c6ebae7", INT: "prod_871143d64fe84d8e89bc" },
  "addon-direction": { NG: "prod_b751edee9a634cb08d0e", INT: "prod_b690e5a893374e18b54c" },
  "addon-presence": { NG: "prod_a61c2887b68d47b7baf6", INT: "prod_e94d9bbfc02d4b468876" },
};
const ADDONS = Object.keys(CATALOG).filter((k) => k !== "base");

const TOKEN_TTL = 14 * 86400;
const GRACE = 30 * 86400;
const REBIND_ALLOWANCE = 3;
const REFUND_WINDOW_DAYS = 30;
const AFFILIATE_RATE = 0.15;
const TRIAL_OFFSET_DAYS = 14;
const TRIAL_LENGTH_DAYS = 7;

// ── small helpers ───────────────────────────────────────────────────────────

const uid = () => crypto.randomUUID().replace(/-/g, "").slice(0, 24);
const now = () => Math.floor(Date.now() / 1000);
const iso = (t = Date.now()) => new Date(t).toISOString();

// ── auth ────────────────────────────────────────────────────────────────────

async function seatFromRequest(req, env) {
  const auth = req.headers.get("authorization") || "";
  const claims = await verifyToken(auth.replace(/^Bearer /, ""), env);
  if (!claims) return null;
  if (now() > claims.grace) return null;          // past grace, refuse
  return claims;
}

// ── entitlements ────────────────────────────────────────────────────────────

async function entitlementsFor(env, licenceId) {
  const { results } = await env.DB.prepare(
    `SELECT addon_id FROM entitlements
      WHERE licence_id = ?
        AND (expires_at IS NULL OR expires_at > datetime('now'))`
  ).bind(licenceId).all();
  return (results || []).map((r) => r.addon_id).sort();
}

async function mintToken(env, licence, seat) {
  const addons = await entitlementsFor(env, licence.licence_id);
  const t = now();
  return signToken({
    lic: licence.licence_id, seat: seat.seat_id, node: seat.node_id,
    plan: licence.plan, addons, iat: t, exp: t + TOKEN_TTL,
    grace: t + TOKEN_TTL + GRACE,
  }, env);
}

// ── routes ──────────────────────────────────────────────────────────────────

async function createCheckout(req, env) {
  const { email, skus } = await req.json();
  if (!email || !Array.isArray(skus) || !skus.length) return err("email and skus required");
  for (const s of skus) if (!CATALOG[s]) return err(`unknown sku ${s}`);

  // Market is decided HERE, from request geography. Never from the client —
  // that is what protects a 4.3x price gap between NGN and USD.
  const market = req.headers.get("cf-ipcountry") === "NG" ? "NG" : "INT";

  // Affiliate code is read from our own cookie/param and recorded now, so the
  // webhook never has to trust anything the buyer's browser sends.
  const url = new URL(req.url);
  const ref = url.searchParams.get("ref");
  let affiliateId = null;
  if (ref) {
    const a = await env.DB.prepare(
      `SELECT affiliate_id FROM affiliates WHERE code = ? AND status = 'active'`
    ).bind(ref).first();
    affiliateId = a ? a.affiliate_id : null;
  }

  const body = {
    product_cart: skus.map((s) => ({ product_id: CATALOG[s][market], quantity: 1 })),
    customer: { email },
    return_url: `${env.SITE_URL}/thanks`,
    cancel_url: `${env.SITE_URL}/pricing`,
    metadata: { skus: skus.join(","), market },
  };

  const res = await fetch(`${env.BACHS_API}/v1/checkout-sessions`, {
    method: "POST",
    headers: {
      authorization: `Bearer ${env.BACHS_KEY}`,
      "content-type": "application/json",
      "idempotency-key": crypto.randomUUID(),
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) return err("checkout failed", 502);
  const session = await res.json();

  if (affiliateId) {
    await env.DB.prepare(
      `INSERT INTO referrals (referral_id, affiliate_id, checkout_id, landed_at, ip_country)
       VALUES (?,?,?,?,?)`
    ).bind(uid(), affiliateId, session.checkout_id, iso(), req.headers.get("cf-ipcountry")).run();
  }
  // The client gets a URL. Never a product id, never a price, never a market.
  return json({ checkout_url: session.checkout_url });
}

async function bachsWebhook(req, env) {
  const raw = await req.text();
  const ok = await verifyWebhook(raw, req.headers.get("bachs-signature"), env.BACHS_WEBHOOK_SECRET);
  if (!ok) return err("bad signature", 401);

  const evt = JSON.parse(raw);
  const d = evt.data || {};

  if (evt.type === "collection.succeeded") {
    // Idempotency: the same event may arrive more than once.
    const seen = await env.DB.prepare(
      `SELECT licence_id FROM licences WHERE payment_ref = ?`).bind(d.id).first();
    if (seen) return json({ ok: true, licence_id: seen.licence_id, replayed: true });

    const email = d.customer?.email;
    const skus = (d.metadata?.skus || "base").split(",");
    let cust = await env.DB.prepare(
      `SELECT customer_id FROM customers WHERE email = ?`).bind(email).first();
    if (!cust) {
      cust = { customer_id: uid() };
      await env.DB.prepare(
        `INSERT INTO customers (customer_id, email, country) VALUES (?,?,?)`
      ).bind(cust.customer_id, email, d.metadata?.market || null).run();
    }

    const licenceId = "LIC-" + uid().slice(0, 12);
    await env.DB.prepare(
      `INSERT INTO licences (licence_id, customer_id, plan, status, seats,
                             currency, amount, payment_ref)
       VALUES (?,?,?,'active',1,?,?,?)`
    ).bind(licenceId, cust.customer_id, "core", d.currency,
           Math.round(parseFloat(d.amount || "0") * 100), d.id).run();

    for (const sku of skus) {
      if (sku === "base") continue;
      await env.DB.prepare(
        `INSERT OR IGNORE INTO entitlements (licence_id, addon_id, source)
         VALUES (?,?,'purchase')`).bind(licenceId, sku).run();
    }

    // Trial scheduled at purchase, not triggered later, so it survives the
    // scheduler being down for a day.
    const start = Date.now() + TRIAL_OFFSET_DAYS * 86400_000;
    await env.DB.prepare(
      `INSERT OR IGNORE INTO trials (licence_id, starts_at, ends_at, addons)
       VALUES (?,?,?,?)`
    ).bind(licenceId, iso(start), iso(start + TRIAL_LENGTH_DAYS * 86400_000),
           JSON.stringify(ADDONS.filter((a) => !skus.includes(a)))).run();

    // Commission is EARNED now and PAYABLE only after the refund window. A
    // chargeback costs $30 and a paid commission is gone; together they lose
    // 2.5x the sale.
    const ref = await env.DB.prepare(
      `SELECT referral_id, affiliate_id FROM referrals WHERE checkout_id = ?`
    ).bind(d.checkout_id || d.id).first();
    if (ref) {
      await env.DB.prepare(
        `UPDATE referrals SET converted_at = ?, payment_id = ? WHERE referral_id = ?`
      ).bind(iso(), d.id, ref.referral_id).run();
      const payable = iso(Date.now() + REFUND_WINDOW_DAYS * 86400_000);
      for (const sku of skus) {
        await env.DB.prepare(
          `INSERT INTO commissions (commission_id, affiliate_id, referral_id,
             licence_id, sku, gross_amount, currency, rate, amount, state, payable_at)
           VALUES (?,?,?,?,?,?,?,?,?,'held',?)`
        ).bind(uid(), ref.affiliate_id, ref.referral_id, licenceId, sku,
               d.amount, d.currency, AFFILIATE_RATE,
               (parseFloat(d.amount) * AFFILIATE_RATE).toFixed(2), payable).run();
      }
    }
    await sendLicenceEmail(env, { to: email, licenceId });
    return json({ ok: true, licence_id: licenceId });
  }

  if (evt.type === "refund.succeeded" || evt.type === "dispute.created") {
    const lic = await env.DB.prepare(
      `SELECT licence_id FROM licences WHERE payment_ref = ?`).bind(d.payment_id || d.id).first();
    if (lic) {
      await env.DB.prepare(
        `UPDATE licences SET status = 'refunded', revoked_at = ?, revoke_reason = ?
          WHERE licence_id = ?`).bind(iso(), evt.type, lic.licence_id).run();
      // held -> clawed (never paid). paid -> reversed (netted off future earnings).
      await env.DB.prepare(
        `UPDATE commissions SET state = CASE WHEN state = 'paid' THEN 'reversed'
                                             ELSE 'clawed' END
          WHERE licence_id = ?`).bind(lic.licence_id).run();
    }
    return json({ ok: true });
  }

  return json({ ok: true, ignored: evt.type });
}

async function activate(req, env) {
  const { licence_id, fingerprint } = await req.json();
  if (!licence_id || !fingerprint) return err("licence_id and fingerprint required");

  const lic = await env.DB.prepare(
    `SELECT * FROM licences WHERE licence_id = ?`).bind(licence_id).first();
  await env.DB.prepare(
    `INSERT INTO activations (activation_id, licence_id, outcome, ip_country)
     VALUES (?,?,?,?)`
  ).bind(uid(), licence_id, lic ? lic.status : "unknown_licence",
         req.headers.get("cf-ipcountry")).run();

  if (!lic) return err("unknown licence", 404);
  if (lic.status !== "active") return err(`licence ${lic.status}`, 403);

  // Same machine reactivating never consumes a second seat.
  let fresh = false;
  let seat = await env.DB.prepare(
    `SELECT * FROM seats WHERE licence_id = ? AND fingerprint = ? AND released_at IS NULL`
  ).bind(licence_id, fingerprint).first();

  if (!seat) {
    const { results } = await env.DB.prepare(
      `SELECT * FROM seats WHERE licence_id = ? AND released_at IS NULL
        ORDER BY activated_at`).bind(licence_id).all();
    if ((results || []).length >= lic.seats) {
      // Rebinding is normal life, not fraud: people reinstall and replace
      // laptops. Bounded, self-service, then a human.
      const used = results[0]?.rebind_count || 0;
      if (used >= REBIND_ALLOWANCE) return err("seat limit reached", 409);
      await env.DB.prepare(
        `UPDATE seats SET released_at = ?, rebind_count = rebind_count + 1
          WHERE seat_id = ?`).bind(iso(), results[0].seat_id).run();
    }
    fresh = true;
    seat = {
      seat_id: uid().slice(0, 12),
      node_id: uid(),                    // random; the ONLY value the ledger sees
      watermark: uid().slice(0, 16),
    };
    await env.DB.prepare(
      `INSERT INTO seats (seat_id, licence_id, node_id, fingerprint, public_key, watermark)
       VALUES (?,?,?,?,?,?)`
    ).bind(seat.seat_id, licence_id, seat.node_id, fingerprint, "", seat.watermark).run();
  }

  if (fresh) await requestSeatBuild(env, seat.seat_id);
  return json({ seat_id: seat.seat_id, node_id: seat.node_id,
                token: await mintToken(env, lic, seat) });
}

async function refresh(req, env) {
  const claims = await seatFromRequest(req, env);
  if (!claims) return err("invalid token", 401);
  const lic = await env.DB.prepare(
    `SELECT * FROM licences WHERE licence_id = ?`).bind(claims.lic).first();
  // Revocation propagates by silence: an existing token stays valid until it
  // expires, so a refund never cuts someone off mid-session.
  if (!lic || lic.status !== "active") return err("licence not active", 403);
  const seat = await env.DB.prepare(
    `SELECT * FROM seats WHERE seat_id = ? AND released_at IS NULL`).bind(claims.seat).first();
  if (!seat) return err("seat released", 403);
  await env.DB.prepare(`UPDATE seats SET last_seen_at = ? WHERE seat_id = ?`)
    .bind(iso(), seat.seat_id).run();
  return json({ token: await mintToken(env, lic, seat) });
}

async function releaseSeat(req, env) {
  const claims = await seatFromRequest(req, env);
  if (!claims) return err("invalid token", 401);
  await env.DB.prepare(`UPDATE seats SET released_at = ? WHERE seat_id = ?`)
    .bind(iso(), claims.seat).run();
  return json({ ok: true });
}

async function listBundles(req, env) {
  const claims = await seatFromRequest(req, env);
  if (!claims) return err("invalid token", 401);
  // Entitlements are re-read from the database, not taken from the token. The
  // token is proof of identity; it is not authority over what it may download.
  const addons = await entitlementsFor(env, claims.lic);
  const scopes = ["core", ...addons];
  const { results } = await env.DB.prepare(
    `SELECT bundle_id, scope, version, sha256 FROM bundles
      WHERE yanked_at IS NULL AND scope IN (${scopes.map(() => "?").join(",")})`
  ).bind(...scopes).all();
  return json({ bundles: results || [] });
}

async function telemetry(req, env) {
  const claims = await seatFromRequest(req, env);
  if (!claims) return err("invalid token", 401);
  const body = await req.json();
  // Channel A only: counts and cell keys. Anything else is dropped here rather
  // than stored and regretted.
  for (const row of (body.rows || []).slice(0, 500)) {
    if (!row.cell_key || !row.arm_id) continue;
    try {
      await env.DB.prepare(
        `INSERT INTO cell_evidence (cell_key, arm_id, model_tier, successes, trials,
                                    n_nodes, updated_at)
         VALUES (?,?,?,?,?,1,?)
         ON CONFLICT(cell_key, arm_id, model_tier) DO UPDATE SET
           successes = successes + excluded.successes,
           trials    = trials    + excluded.trials,
           updated_at = excluded.updated_at`
      ).bind(row.cell_key, row.arm_id, row.model_tier || "unknown",
             Number(row.successes) || 0, Number(row.trials) || 0, iso()).run();
    } catch (e) {
      // Drop malformed or foreign-key-violating rows silently.
    }
  }
  return json({ ok: true });
}

async function ledgerSync(req, env) {
  const claims = await seatFromRequest(req, env);
  if (!claims) return err("invalid token", 401);
  // THIS is the licence check. A copied client still runs — it just decays
  // from the day it was copied while paying seats keep improving.
  const priors = await env.DB.prepare(
    `SELECT cell_key, arm_id, alpha, beta, strength_cap FROM priors`).all();
  const dead = await env.DB.prepare(
    `SELECT arm_id, cell_key, reason FROM dead_arms`).all();
  return json({ priors: priors.results || [], dead_arms: dead.results || [],
                as_of: iso() });
}

// ── scheduled ───────────────────────────────────────────────────────────────

async function scheduled(env) {
  // 1. trials start and end
  await env.DB.prepare(
    `UPDATE trials SET state = 'running'
      WHERE state = 'scheduled' AND starts_at <= datetime('now')`).run();
  const starting = await env.DB.prepare(
    `SELECT licence_id, addons FROM trials
      WHERE state = 'running' AND ends_at > datetime('now')`).all();
  for (const t of starting.results || []) {
    for (const a of JSON.parse(t.addons)) {
      await env.DB.prepare(
        `INSERT OR IGNORE INTO entitlements (licence_id, addon_id, source, expires_at)
         SELECT ?,?,'trial',ends_at FROM trials WHERE licence_id = ?`
      ).bind(t.licence_id, a, t.licence_id).run();
    }
  }
  await env.DB.prepare(
    `UPDATE trials SET state = 'ended'
      WHERE state = 'running' AND ends_at <= datetime('now')`).run();
  await env.DB.prepare(
    `DELETE FROM entitlements
      WHERE source = 'trial' AND expires_at <= datetime('now')`).run();

  // 2. commissions come out of hold once the refund window closes
  await env.DB.prepare(
    `UPDATE commissions SET state = 'payable'
      WHERE state = 'held' AND payable_at <= datetime('now')`).run();

  // 3. affiliate payouts, on the 1st. Monthly rather than per sale because an
  //    NGN payout costs a flat 215 whatever the amount.
  if (new Date().getUTCDate() === 1) {
    const paid = await payoutRun(env);
    if (paid.length) console.log("payouts", JSON.stringify(paid));
  }
}

// ── router ──────────────────────────────────────────────────────────────────

const ROUTES = {
  "POST /v1/checkout": createCheckout,
  "POST /v1/webhooks/bachs": bachsWebhook,
  "POST /v1/activate": activate,
  "POST /v1/refresh": refresh,
  "POST /v1/seats/release": releaseSeat,
  "GET /v1/bundles": listBundles,
  "POST /v1/telemetry": telemetry,
  "POST /v1/ledger/sync": ledgerSync,
};

export default {
  async fetch(req, env) {
    const url = new URL(req.url);

    if (req.method === "GET" && url.pathname.startsWith("/v1/bundles/")) {
      const claims = await seatFromRequest(req, env);
      if (!claims) return err("invalid token", 401);
      try {
        return await downloadBundle(req, env, claims,
                                    url.pathname.slice("/v1/bundles/".length));
      } catch (e) {
        console.error(e?.stack || String(e));
        return err("internal error", 500);
      }
    }
    if (url.pathname.startsWith("/v1/admin/")) {
      try {
        return await adminHandler(req, env, url.pathname);
      } catch (e) {
        console.error(e?.stack || String(e));
        return err("internal error", 500);
      }
    }

    const handler = ROUTES[`${req.method} ${url.pathname}`];
    if (!handler) return err("not found", 404);
    try {
      return await handler(req, env);
    } catch (e) {
      // Never leak internals to a caller. The detail goes to the log.
      console.error(e?.stack || String(e));
      return err("internal error", 500);
    }
  },
  async scheduled(_event, env) {
    await scheduled(env);
  },
};

export { scheduled, CATALOG, ADDONS };
