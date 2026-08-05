# The Worker — one file, eight endpoints, 33 passing tests

`worker/` is the whole server side. It runs on Cloudflare Workers against D1
and R2, and `node test/run.js` exercises every route with an in-memory database
and a fake Bachs — no deployment needed to know it works.

## Endpoints

| Route | What it does |
|---|---|
| `POST /v1/checkout` | creates a Bachs session; **the market is decided here** |
| `POST /v1/webhooks/bachs` | the only thing that creates a licence |
| `POST /v1/activate` | licence + fingerprint → seat + entitlement token |
| `POST /v1/refresh` | fresh token; also where revocation lands |
| `POST /v1/seats/release` | self-service, no support ticket |
| `GET /v1/bundles` | what this seat may download |
| `POST /v1/telemetry` | Channel A counts |
| `POST /v1/ledger/sync` | priors + dead list — **the real licence check** |

Plus a daily cron: trials in and out, commissions off hold.

## Two rules that run through everything

**1. The client never chooses.** Not the product, not the market, not the price,
not its own entitlements. The checkout response contains a URL and nothing else
— no product id, no price, no market. A visitor abroad cannot request the
₦35,000 checkout because it is not something you can ask for; it is something
the server decides to create from `cf-ipcountry`.

That single rule is what protects a 4.3× price gap. There is a test for it:
*"client cannot pass a product id"* returns 400.

**2. Webhooks are the source of truth.** A redirect is a hint; a signed webhook
is a fact. An unsigned webhook creates nothing, and a replayed one is idempotent
— both tested, because Nigerian connectivity means retries and a duplicate
`collection.succeeded` must not mint a second licence.

## Four design decisions worth checking you agree with

**Entitlements are read from the database, not the token.** The token proves
identity; it is not authority over what it may download. So buying an addon
takes effect immediately rather than at the next fortnightly refresh. Tested:
*"new entitlement visible without a new token."*

**Revocation propagates by silence.** A refunded licence cannot refresh, and its
existing token keeps working until it expires. A refund never cuts someone off
mid-session. The worst case is a refunded customer keeping the tool for up to a
fortnight — far better than every network hiccup looking like a revocation.

**Commissions are earned at purchase and payable only after 30 days.** A refund
inside the window sets them to `clawed`; after payout, `reversed`. This is the
₦86,750-on-a-₦35,000-sale problem from `PAYMENTS.md`, handled at the point where
it can actually be prevented.

**Trials are scheduled at purchase, not triggered later.** Written into `trials`
by the webhook, so a scheduler outage delays the trial rather than losing it.
Expiry removes only trial-sourced entitlements — a purchased addon survives.
Tested both ways.

## Telemetry cannot leak what it does not store

`POST /v1/telemetry` accepts cell keys, arm ids, model tier and counts. Rows
missing a cell key or arm id are dropped. Extra fields are ignored — and the
table has no free-text column for them to land in even if the handler were
wrong. There is a test that reads `PRAGMA table_info` and asserts no
`employer`, `company`, `text` or `note` column exists.

That is the only form of the privacy promise anyone should believe: not a
policy, but a schema with nowhere to put the thing you promised not to keep.

## `ledger/sync` is the licence

Not a separate gate — the thing a copied client cannot have. A pirated copy
still runs; it just stops receiving priors and dead-arm lists, so it decays from
the day it was copied while paying seats keep improving.

## Rate limits before the $5 plan, not after

`wrangler.toml` has rate-limit bindings on `activate` and `checkout` — the two
endpoints worth abusing, since one enumerates licence ids and the other creates
sessions. Both cheap to call, expensive to serve.

Turn these on **before** upgrading to Workers Paid. On the free plan a hammered
endpoint returns error 1027 and you find out; on Paid it keeps serving and
charges you.

## Running it

```bash
cd worker
npm test                     # 33 checks, no deployment needed
npx wrangler d1 create hermes
npm run db:init              # schema.sql = licence + affiliate + ledger tables
npx wrangler secret put TOKEN_SECRET
npx wrangler secret put BACHS_KEY
npx wrangler secret put BACHS_WEBHOOK_SECRET
npm run deploy               # runs the tests first, then deploys
```

`schema.sql` is the concatenation of `licence-schema.sql`, `affiliate-schema.sql`
and the three ledger tables the Worker reads. Regenerate it whenever those
change rather than editing it by hand.

## What is deliberately not here

**Bundle watermarking.** It needs hundreds of milliseconds and belongs in the
GitHub Actions build, which writes pre-built per-seat bundles to R2. The Worker
only serves bytes.

**The weekly hierarchical aggregation.** It walks every cell × arm × tier and
wants seconds of CPU. Either a $5 Worker with a raised limit, or the Oracle box.
Not a request handler either way.

**Anything that emails.** Two emails exist in this system — licence delivery and
affiliate payout notices — and both go through Resend from the webhook handler
once you wire it. Everything else rides Telegram.
