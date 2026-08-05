/**
 * worker/src/crypto.js — Ed25519 token signing.
 *
 * Replaces the HMAC placeholder. The difference that matters: with HMAC the
 * verifying key IS the signing key, so a client able to verify a token is also
 * able to mint one. Anyone who pulled the secret out of a client binary could
 * grant themselves every addon forever. With Ed25519 the client holds only the
 * public key, and a pinned public key cannot forge anything.
 *
 * Keys are stored as base64: raw 32 bytes public, pkcs8 48 bytes private.
 * Generate once with `node scripts/keygen.js` and never lose the private half —
 * every token you have ever issued verifies against its public pair.
 */

const enc = new TextEncoder();
const ALG = { name: "Ed25519" };

export const b64url = (buf) =>
  btoa(String.fromCharCode(...new Uint8Array(buf)))
    .replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");

export const unb64url = (s) => {
  const p = s.replace(/-/g, "+").replace(/_/g, "/");
  const bin = atob(p + "=".repeat((4 - (p.length % 4)) % 4));
  return Uint8Array.from(bin, (c) => c.charCodeAt(0));
};

const b64 = (buf) => btoa(String.fromCharCode(...new Uint8Array(buf)));
const unb64 = (s) => Uint8Array.from(atob(s), (c) => c.charCodeAt(0));

// Cached BY KEY MATERIAL, not globally. Caching on first use alone would mean
// a rotated or staging key silently kept signing with the old one — invisible,
// and only discovered when tokens stopped verifying in production.
const _keys = new Map();

async function importOnce(material, fmt, usage) {
  if (!_keys.has(material)) {
    _keys.set(material, await crypto.subtle.importKey(
      fmt, unb64(material), ALG, false, usage));
  }
  return _keys.get(material);
}

const privateKey = (env) => importOnce(env.TOKEN_PRIVATE_KEY, "pkcs8", ["sign"]);
const publicKey  = (env) => importOnce(env.TOKEN_PUBLIC_KEY,  "raw",   ["verify"]);

export async function signToken(payload, env) {
  const body = b64url(enc.encode(JSON.stringify(payload)));
  const sig = await crypto.subtle.sign(ALG, await privateKey(env), enc.encode(body));
  return `${body}.${b64url(sig)}`;
}

export async function verifyToken(token, env) {
  const [body, sig] = String(token || "").split(".");
  if (!body || !sig) return null;
  let ok;
  try {
    ok = await crypto.subtle.verify(ALG, await publicKey(env),
                                    unb64url(sig), enc.encode(body));
  } catch {
    return null;                       // malformed signature bytes
  }
  if (!ok) return null;
  try {
    return JSON.parse(new TextDecoder().decode(unb64url(body)));
  } catch {
    return null;
  }
}

/** Webhook signatures stay HMAC — that is what Bachs sends. */
export async function verifyWebhook(raw, header, secret) {
  const key = await crypto.subtle.importKey(
    "raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const expect = b64url(await crypto.subtle.sign("HMAC", key, enc.encode(raw)));
  if (!header || header.length !== expect.length) return false;
  let diff = 0;
  for (let i = 0; i < header.length; i++) diff |= header.charCodeAt(i) ^ expect.charCodeAt(i);
  return diff === 0;
}

export async function generateKeypair() {
  const kp = await crypto.subtle.generateKey(ALG, true, ["sign", "verify"]);
  return {
    publicKey: b64(await crypto.subtle.exportKey("raw", kp.publicKey)),
    privateKey: b64(await crypto.subtle.exportKey("pkcs8", kp.privateKey)),
  };
}
