#!/usr/bin/env node
/**
 * worker/scripts/keygen.js — generate Ed25519 keypair for token signing.
 *
 *     node scripts/keygen.js
 *
 * Outputs two base64 strings: TOKEN_PRIVATE_KEY (pkcs8) and TOKEN_PUBLIC_KEY (raw).
 * Paste them into `wrangler secret put` — never commit them.
 */

const ALG = { name: "Ed25519" };
const b64 = (buf) => btoa(String.fromCharCode(...new Uint8Array(buf)));

const kp = await crypto.subtle.generateKey(ALG, true, ["sign", "verify"]);
const publicKey  = b64(await crypto.subtle.exportKey("raw", kp.publicKey));
const privateKey = b64(await crypto.subtle.exportKey("pkcs8", kp.privateKey));

console.log("\n=== Ed25519 Keypair ===\n");
console.log("TOKEN_PRIVATE_KEY (paste into `wrangler secret put TOKEN_PRIVATE_KEY`):");
console.log(privateKey);
console.log("\nTOKEN_PUBLIC_KEY (paste into `wrangler secret put TOKEN_PUBLIC_KEY`):");
console.log(publicKey);
console.log("\nSave these somewhere safe. Every future token verifies against the public key.");
