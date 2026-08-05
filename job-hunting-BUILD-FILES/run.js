/**
 * worker/test/run.js — exercise every route without Cloudflare.
 *
 *     node test/run.js
 *
 * Stubs D1 with node:sqlite and fetch with a fake Bachs. The point is to catch
 * the failures that matter before a customer does: a client choosing its own
 * market, a forged token, a replayed webhook, a refund that leaves a commission
 * payable, an entitlement taken from the token instead of the database.
 */
import { DatabaseSync } from "node:sqlite";
import { readFileSync } from "node:fs";
import worker, { scheduled } from "../src/index.js";
import { generateKeypair } from "../src/crypto.js";
import { payoutRun } from "../src/delivery.js";

// ── D1 stub ─────────────────────────────────────────────────────────────────
function makeDB(sql) {
  const db = new DatabaseSync(":memory:");
  db.exec(sql);
  return {
    prepare(q) {
      let args = [];
      const api = {
        bind(...a) { args = a; return api; },
        async first() { return db.prepare(q).get(...args) ?? null; },
        async all() { return { results: db.prepare(q).all(...args) }; },
        async run() { return db.prepare(q).run(...args); },
      };
      return api;
    },
    _raw: db,
  };
}

const SCHEMA = `
CREATE TABLE schema_version (filename TEXT PRIMARY KEY, note TEXT);
${readFileSync(new URL("../schema.sql", import.meta.url), "utf8")}
`;

// ── fake Bachs ──────────────────────────────────────────────────────────────
let lastCheckout = null;
globalThis.fetch = async (url, init) => {
  if (String(url).includes("api.resend.com")) {
    sent.push(JSON.parse(init.body));
    return new Response("{}", { status: 200 });
  }
  if (String(url).includes("api.github.com")) {
    dispatched.push(JSON.parse(init.body));
    return new Response("{}", { status: 204 });
  }
  if (String(url).includes("/checkout-sessions")) {
    lastCheckout = JSON.parse(init.body);
    return new Response(JSON.stringify({
      id: "chk_test_1", url: "https://checkout.bachs.io/chk_test_1",
    }), { status: 200, headers: { "content-type": "application/json" } });
  }
  return new Response("{}", { status: 200 });
};

const kp = await generateKeypair();
const sent = [];        // emails
const dispatched = [];  // seat build requests
const R2 = new Map();

const env = {
  DB: null,
  BUNDLES: {
    async get(k) { return R2.has(k) ? { body: R2.get(k) } : null; },
  },
  TOKEN_PRIVATE_KEY: kp.privateKey,
  TOKEN_PUBLIC_KEY: kp.publicKey,
  RESEND_KEY: "re_test",
  MAIL_FROM: "you@example.com",
  ADMIN_TOKEN: "admin-secret",
  GITHUB_TOKEN: "ghp_test",
  GITHUB_REPO: "you/repo",
  BACHS_KEY: "sk_test",
  BACHS_API: "https://sandbox-api.bachs.io",
  BACHS_WEBHOOK_SECRET: "wh-secret",
  SITE_URL: "https://example.com",
};

const enc = new TextEncoder();
const b64url = (b) => btoa(String.fromCharCode(...new Uint8Array(b)))
  .replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
async function sigFor(raw) {
  const k = await crypto.subtle.importKey("raw", enc.encode(env.BACHS_WEBHOOK_SECRET),
    { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return b64url(await crypto.subtle.sign("HMAC", k, enc.encode(raw)));
}

const call = (method, path, { body, token, country, query } = {}) =>
  worker.fetch(new Request(`https://api.example.com${path}${query || ""}`, {
    method,
    headers: {
      ...(token ? { authorization: `Bearer ${token}` } : {}),
      ...(country ? { "cf-ipcountry": country } : {}),
      "content-type": "application/json",
    },
    ...(body ? { body: JSON.stringify(body) } : {}),
  }), env);

async function hook(evt) {
  const raw = JSON.stringify(evt);
  return worker.fetch(new Request("https://api.example.com/v1/webhooks/bachs", {
    method: "POST",
    headers: { "bachs-signature": await sigFor(raw), "content-type": "application/json" },
    body: raw,
  }), env);
}

// ── harness ─────────────────────────────────────────────────────────────────
const results = [];
const check = (name, cond, extra = "") => results.push([name, !!cond, extra]);

const PAY = (over = {}) => ({
  type: "collection.succeeded",
  data: {
    id: "pay_1", checkout_id: "chk_test_1", amount: "35000.00", currency: "NGN",
    customer: { email: "buyer@example.com" },
    metadata: { skus: "base", market: "NG" },
    ...over,
  },
});

async function main() {
  env.DB = makeDB(SCHEMA);
  await env.DB.prepare(
    `INSERT INTO affiliates (affiliate_id, email, code, payout_ccy)
     VALUES ('aff1','a@x.com','KENE','NGN')`).bind().run();
  await env.DB.prepare(
    `INSERT INTO bundles (bundle_id, scope, version, sha256, signature, published_at)
     VALUES ('b_core','core','1.0.0','x','y',datetime('now')),
            ('b_out','addon-outreach','1.0.0','x','y',datetime('now'))`).bind().run();

  // --- market is decided server-side ---------------------------------------
  let r = await call("POST", "/v1/checkout",
    { body: { email: "buyer@example.com", skus: ["base"] }, country: "NG", query: "?ref=KENE" });
  let j = await r.json();
  check("checkout returns a url only", r.status === 200 && j.checkout_url && !j.product_id);
  check("NG buyer routed to the NGN product",
    lastCheckout.product_cart[0].product_id === "prod_ng_base");

  await call("POST", "/v1/checkout",
    { body: { email: "x@y.com", skus: ["base"] }, country: "GB" });
  check("GB buyer routed to the USD product",
    lastCheckout.product_cart[0].product_id === "prod_int_base");

  r = await call("POST", "/v1/checkout",
    { body: { email: "x@y.com", skus: ["prod_int_base"] }, country: "NG" });
  check("client cannot pass a product id", r.status === 400);

  check("affiliate referral recorded",
    (await env.DB.prepare(`SELECT COUNT(*) c FROM referrals`).bind().first()).c === 1);

  // --- webhook is the only thing that creates a licence ---------------------
  r = await worker.fetch(new Request("https://api.example.com/v1/webhooks/bachs", {
    method: "POST", headers: { "bachs-signature": "wrong" }, body: JSON.stringify(PAY()),
  }), env);
  check("unsigned webhook rejected", r.status === 401);
  check("no licence created by a bad webhook",
    (await env.DB.prepare(`SELECT COUNT(*) c FROM licences`).bind().first()).c === 0);

  r = await hook(PAY());
  j = await r.json();
  const LIC = j.licence_id;
  check("signed webhook creates a licence", r.status === 200 && LIC);

  const replay = await (await hook(PAY())).json();
  check("replayed webhook is idempotent", replay.replayed === true && replay.licence_id === LIC);
  check("only one licence exists",
    (await env.DB.prepare(`SELECT COUNT(*) c FROM licences`).bind().first()).c === 1);

  check("commission held, not payable",
    (await env.DB.prepare(`SELECT state FROM commissions`).bind().first()).state === "held");
  check("trial scheduled for all four addons",
    JSON.parse((await env.DB.prepare(`SELECT addons FROM trials`).bind().first()).addons).length === 4);

  // --- activation ----------------------------------------------------------
  r = await call("POST", "/v1/activate", { body: { licence_id: LIC, fingerprint: "fp-1" } });
  const act = await r.json();
  check("activation issues a token", r.status === 200 && act.token);
  check("node id is not the licence id", act.node_id !== LIC);

  const again = await (await call("POST", "/v1/activate",
    { body: { licence_id: LIC, fingerprint: "fp-1" } })).json();
  check("same machine reuses its seat", again.seat_id === act.seat_id);

  const rebind = await call("POST", "/v1/activate",
    { body: { licence_id: LIC, fingerprint: "fp-2" } });
  check("new machine rebinds", rebind.status === 200);

  r = await call("POST", "/v1/activate", { body: { licence_id: "LIC-nope", fingerprint: "f" } });
  check("unknown licence refused", r.status === 404);

  // --- tokens --------------------------------------------------------------
  r = await call("GET", "/v1/bundles", { token: act.token });
  let bundles = (await r.json()).bundles;
  check("core bundle offered", bundles.some((b) => b.scope === "core"));
  check("unpurchased addon NOT offered", !bundles.some((b) => b.scope === "addon-outreach"));

  const forged = act.token.split(".")[0] + ".AAAA";
  r = await call("GET", "/v1/bundles", { token: forged });
  check("forged token rejected", r.status === 401);
  r = await call("GET", "/v1/bundles", {});
  check("missing token rejected", r.status === 401);

  // entitlements come from the DB, not the token
  await env.DB.prepare(
    `INSERT INTO entitlements (licence_id, addon_id, source) VALUES (?,?,'purchase')`
  ).bind(LIC, "addon-outreach").run();
  bundles = (await (await call("GET", "/v1/bundles", { token: act.token })).json()).bundles;
  check("new entitlement visible without a new token",
    bundles.some((b) => b.scope === "addon-outreach"),
    "entitlements are read from the database, not the token");

  // --- telemetry and ledger ------------------------------------------------
  await call("POST", "/v1/telemetry", {
    token: act.token,
    body: { rows: [
      { cell_key: "ats_platform=greenhouse", arm_id: "variant", model_tier: "mid",
        successes: 2, trials: 10 },
      { arm_id: "no_cell" },                                   // dropped
      { cell_key: "c", arm_id: "a", employer: "Acme Corp", successes: 1, trials: 1 },
    ] },
  });
  const ev = await env.DB.prepare(`SELECT COUNT(*) c FROM cell_evidence`).bind().first();
  check("malformed telemetry row dropped", ev.c === 2);
  const cols = env.DB._raw.prepare(`PRAGMA table_info(cell_evidence)`).all().map((c) => c.name);
  check("no free-text column exists to leak into",
    !cols.some((c) => ["employer", "company", "text", "note"].includes(c)));

  r = await call("POST", "/v1/ledger/sync", { token: act.token });
  check("ledger sync requires a valid token", r.status === 200);
  check("ledger sync refuses without one",
    (await call("POST", "/v1/ledger/sync", {})).status === 401);

  // --- scheduled work ------------------------------------------------------
  env.DB._raw.exec(`UPDATE trials SET starts_at = datetime('now','-1 day'),
                                      ends_at   = datetime('now','+1 day')`);
  await scheduled(env);
  check("trial grants all four addons",
    (await env.DB.prepare(
      `SELECT COUNT(*) c FROM entitlements WHERE licence_id = ? AND source='trial'`
    ).bind(LIC).first()).c === 4);

  env.DB._raw.exec(`UPDATE trials SET ends_at = datetime('now','-1 hour')`);
  env.DB._raw.exec(`UPDATE entitlements SET expires_at = datetime('now','-1 hour')
                     WHERE source='trial'`);
  await scheduled(env);
  check("trial expiry removes only trial addons",
    (await env.DB.prepare(
      `SELECT COUNT(*) c FROM entitlements WHERE licence_id = ?`).bind(LIC).first()).c === 1,
    "the purchased addon survives");

  env.DB._raw.exec(`UPDATE commissions SET payable_at = datetime('now','-1 day')`);
  await scheduled(env);
  check("commission becomes payable after the window",
    (await env.DB.prepare(`SELECT state FROM commissions`).bind().first()).state === "payable");

  // --- refund --------------------------------------------------------------
  await hook({ type: "refund.succeeded", data: { payment_id: "pay_1" } });
  check("refund marks the licence refunded",
    (await env.DB.prepare(`SELECT status FROM licences WHERE licence_id=?`)
      .bind(LIC).first()).status === "refunded");
  check("refund claws back the commission",
    (await env.DB.prepare(`SELECT state FROM commissions`).bind().first()).state === "clawed");
  check("refunded licence cannot refresh",
    (await call("POST", "/v1/refresh", { token: act.token })).status === 403);
  check("existing token still works until it expires",
    (await call("GET", "/v1/bundles", { token: act.token })).status === 200,
    "revocation propagates by silence, never mid-session");

  // --- delivery: email, seat build, bundle download -----------------------
  check("licence email sent on purchase",
    sent.some((m) => m.to[0] === "buyer@example.com" && /licence key/i.test(m.subject)));
  check("licence key appears in the email body",
    sent.some((m) => m.text.includes(LIC)));
  check("seat build requested on first activation",
    dispatched.some((d) => d.inputs.seat === act.seat_id));

  R2.set(`${act.seat_id}/core-1.0.0.tar.gz`, "SEAT-BYTES");
  R2.set("core-template/addon-outreach-1.0.0.tar.gz", "SHARED-BYTES");

  r = await call("GET", "/v1/bundles/b_core", { token: act.token });
  check("core bundle downloads", r.status === 200);
  check("per-seat build served when it exists",
    r.headers.get("x-watermarked") === "true");

  r = await call("GET", "/v1/bundles/b_out", { token: act.token });
  check("entitled addon downloads", r.status === 200);
  check("falls back to the template when the seat build is missing",
    r.headers.get("x-watermarked") === "false");

  await env.DB.prepare(
    `DELETE FROM entitlements WHERE licence_id = ? AND addon_id = 'addon-outreach'`
  ).bind(LIC).run();
  r = await call("GET", "/v1/bundles/b_out", { token: act.token });
  check("unentitled addon refused", r.status === 403);
  await env.DB.prepare(
    `INSERT INTO entitlements (licence_id, addon_id, source) VALUES (?,?,'purchase')`
  ).bind(LIC, "addon-outreach").run();

  r = await call("GET", "/v1/bundles/b_core", {});
  check("download requires a token", r.status === 401);

  // --- Ed25519: verifying key cannot mint --------------------------------
  const other = await generateKeypair();
  const wrongEnv = { ...env, TOKEN_PRIVATE_KEY: other.privateKey };
  const { signToken } = await import("../src/crypto.js");
  const foreign = await signToken({ lic: LIC, seat: act.seat_id, addons: ["addon-presence"],
    exp: Math.floor(Date.now()/1000)+999, grace: Math.floor(Date.now()/1000)+999 }, wrongEnv);
  check("token signed by another key is rejected",
    (await call("GET", "/v1/bundles", { token: foreign })).status === 401,
    "public key cannot forge — the whole point of Ed25519 over HMAC");

  // --- admin --------------------------------------------------------------
  check("admin refuses without a token",
    (await call("GET", "/v1/admin/summary")).status === 401);
  r = await worker.fetch(new Request("https://api.example.com/v1/admin/summary",
    { headers: { authorization: "Bearer admin-secret" } }), env);
  const sum = (await r.json()).rows[0];
  check("admin summary reports live counts",
    r.status === 200 && sum.refunded === 1 && sum.active_seats >= 1,
    "the licence was refunded earlier in this run, so active is 0");
  r = await worker.fetch(new Request("https://api.example.com/v1/admin/trial_conversion",
    { headers: { authorization: "Bearer admin-secret" } }), env);
  check("trial conversion view works", r.status === 200);

  // --- affiliate payouts --------------------------------------------------
  env.DB._raw.exec(`UPDATE commissions SET state='payable', amount='5250.00'`);
  let preview = await payoutRun(env, { dryRun: true });
  check("below-threshold balance is not paid", preview.length === 0,
    "NGN 5,250 < the NGN 10,000 minimum; a flat NGN 215 fee would be 4.1%");

  env.DB._raw.exec(`INSERT INTO commissions
    (commission_id, affiliate_id, referral_id, licence_id, sku, gross_amount,
     currency, rate, amount, state, payable_at)
    SELECT 'c2', affiliate_id, referral_id, licence_id, 'addon-outreach',
           '25000.00','NGN',0.15,'5250.00','payable', datetime('now','-1 day')
      FROM commissions LIMIT 1`);
  preview = await payoutRun(env, { dryRun: true });
  check("above-threshold balance is paid", preview.length === 1 && preview[0].gross === 10500);
  check("flat NGN payout fee applied", preview[0].fee === 215);

  const done = await payoutRun(env);
  check("payout marks commissions paid",
    (await env.DB.prepare(
      `SELECT COUNT(*) c FROM commissions WHERE state='paid'`).bind().first()).c === 2);
  check("payout emails the affiliate",
    sent.some((m) => m.to[0] === "a@x.com" && /payout/i.test(m.subject)));
  check("second run does not pay twice",
    (await payoutRun(env, { dryRun: true })).length === 0);

  // --- report --------------------------------------------------------------
  const w = Math.max(...results.map(([n]) => n.length));
  for (const [n, ok, extra] of results) {
    console.log(`  ${n.padEnd(w)}  ${ok ? "ok  " : "FAIL"}${extra ? "  " + extra : ""}`);
  }
  const bad = results.filter(([, ok]) => !ok);
  console.log();
  if (bad.length) {
    console.log(`${bad.length} of ${results.length} failed`);
    process.exit(1);
  }
  console.log(`${results.length} checks pass`);
}

main();
