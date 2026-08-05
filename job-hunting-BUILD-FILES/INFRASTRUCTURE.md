# Infrastructure — hosting, payments, pricing

Answers to the three decisions, with the numbers behind each. Run
`python3 unit_economics.py` to reproduce the fee and capacity tables.

---

# 1. Hosting on Cloudflare

## What maps cleanly to the free tier

| Component | Product | Free allowance | Your load |
|---|---|---|---|
| Licensing API | Workers | 100k requests/day | ~0.2% at 100 users |
| Ledger sync | Workers + D1 | 5 GB, 5M rows read/day | trivial |
| Telemetry ingest | Workers + D1 | 100k rows written/day | 1% at 100 users |
| Bundle storage | R2 | 10 GB, zero egress | package is sub-megabyte |
| Bachs webhooks | Workers | — | a few per day |
| Scheduled jobs | Cron Triggers | included | 3–4 jobs |
| Marketing site, dashboard | Pages | unlimited static | — |
| Signing keys | Workers Secrets | included | — |

**Request volume is not what breaks first.** At 40,000 users you would still be
inside the daily request cap. The binding constraint is **10 ms CPU per
request** on the free plan, and Cloudflare's own guidance puts a typical Worker
at ~2.2 ms with auth-and-parsing work at 10–20 ms.

## (a) Where the free tier is genuinely insufficient — four places

**1. Per-seat bundle watermarking.** Reading a bundle, injecting markers,
rehashing and signing is hundreds of milliseconds. It cannot run in a 10 ms
budget. *Fix without spending: build watermarked bundles offline and upload
them, so the Worker only serves bytes from R2.*

**2. The weekly hierarchical aggregation.** Walking every cell × arm × model
tier to recompute priors is seconds of CPU, not milliseconds. This is the one
that most clearly needs more room.

**3. Outbound email.** Cloudflare has **no transactional send product** —
Email Routing forwards inbound mail and Email Workers cannot originate arbitrary
outbound. Your trial-reminder newsletters have nowhere to go. **This is the only
gap that money to Cloudflare does not close.**

**4. KV as a write store.** 1,000 writes/day means a per-request write fails at
1,000 users. Not a spending problem — a design one. Use D1 for anything written
per request and treat KV as read-mostly config cache.

## (b) Does $5 Workers Paid close the gaps?

**Three of the four, yes.** It removes the daily request cap, raises CPU from
10 ms to 30 s by default (configurable to 5 minutes), lifts the D1 row
allowances, and includes 10M requests and 30M CPU-ms before per-unit charges
start at $0.30/M requests and $0.02/M CPU-ms.

At a few hundred users you would not approach the included allotment, so the
realistic bill is **$5/month flat**.

**It does not close the email gap.** Nothing Cloudflare sells does.

**One caution about moving to Paid:** it converts a hard stop into a bill. On
Free, a hammered endpoint returns error 1027 and you find out. On Paid it keeps
serving and charges you. **Put rate limiting on every public endpoint before you
upgrade, not after** — this is a documented way people have turned a $5 month
into a $50 one.

## (c) Where Oracle's Always Free VM fits

The 1 GB / 1 vCPU instance is a genuinely good fit for **exactly the work that
does not belong in a Worker**: bundle building and watermarking, the weekly
aggregation, GEPA runs, and anything that wants a persistent process.

Use it as an **async worker behind a queue, never in the request path.** Three
reasons: 1 GB RAM is tight for a build step; it is one machine in one region
with no edge; and Always Free instances are reclaimed when idle, with
well-documented cases of accounts terminated without warning.

**So: yes as a build box, no as your API.** And if it is holding anything you
cannot regenerate, back it up somewhere else.

## (d) Other free tiers worth using

| Need | Service | Free tier | Note |
|---|---|---|---|
| **Transactional email** | Resend | 3,000/mo, 100/day | the gap Cloudflare cannot fill |
| | Brevo | 300/day | higher daily cap, clunkier API |
| **Build and watermark** | GitHub Actions | 2,000 min/mo private | better than Oracle — ephemeral, versioned, no server to lose |
| **Error tracking** | Sentry | 5k errors/mo | you cannot debug a customer's machine; you need this |
| **Uptime checks** | UptimeRobot / Better Stack | 50 monitors | the ledger going down is silent otherwise |
| **Digests** | Telegram Bot API | free | already in the package |
| **DB alternative** | Turso | generous SQLite | only if you outgrow D1 |
| **Object storage alt** | Backblaze B2 | 10 GB | R2's zero egress is better; keep R2 |

**GitHub Actions over Oracle for the build step.** (Measured: 2,000 free
Linux minutes a month against a ~2 minute build. See `BUILD.md`.) Ephemeral, versioned,
nothing to maintain, and no risk of losing a VM you forgot about. Oracle earns
its place only for the recurring aggregation job, and even that fits in a $5
Worker.

## Recommended shape

```
Cloudflare Workers ($5/mo)   licensing API, ledger sync, telemetry,
                             Bachs webhooks, cron
Cloudflare D1                licences, seats, entitlements, cell evidence
Cloudflare R2                pre-built watermarked bundles
Cloudflare Pages             marketing site + your admin dashboard
GitHub Actions               build, strip, compile, watermark, sign, upload
Resend                       trial reminders and receipts
Sentry + UptimeRobot         you cannot see your customers' machines
```

**Total: $5/month.** Everything else free at your scale.

On email specifically, see `PAYMENTS.md` §1 — the requirement turned out to be
**two emails**, licence delivery and affiliate payout notices, not a newsletter
platform. Everything else rides the Telegram channel the tool already owns.

---

# 2. Payments — Bachs

## The finding that changes your pricing plan

Bachs currency options support GHS, KES, UGX, TZS, XAF, XOF, ZMW and RWF. Your
primary currency is **USD *or* NGN**, and — this is the part that matters —
**the primary currency cannot also be a currency option.**

**So you cannot put ₦35,000 and $100 on the same product.** One product has one
primary; the other currency is unreachable on it.

**Fix: two products per SKU.** An NGN-primary product and a USD-primary
product, ten products total for base plus four addons. Route the customer to
the right checkout server-side. It also gives you exact prices in both markets
rather than a live-rate conversion, which is what you want for a price point
like ₦35,000.

## The arbitrage problem

₦35,000 is about **$23**. Against $100, that is a **4.3× gap** — and on the full
stack, ₦135,000 (~$87) against $220. The Nigerian full stack costs less than the
international base alone.

That is correct purchasing-power pricing and I would not change it. But it means
**the NGN checkout must not be reachable by anyone who wants it.** Three
defences, in order of effectiveness:

1. **Never expose the NGN checkout by URL.** Create the session server-side
   after your own market determination. A guessable link is a price list.
2. **Offer the NGN product only through NGN methods** — bank transfer and local
   cards — which require Nigerian bank details to complete.
3. **Watermarking traces resale.** Someone buying at ₦35k to resell abroad is
   traceable to their seat.

Do not use `billing_currency` from anything client-supplied. It is a testing
parameter; treating it as user input hands over the price.

## Fees, and what actually lands

| Sale | Method | Fee | Net |
|---|---|---|---|
| ₦35,000 base | bank transfer | ₦525 (1.5%) | **₦34,475** |
| ₦35,000 base | local card | ₦700 (2.0%) | ₦34,300 |
| ₦25,000 addon | bank transfer | ₦375 (1.5%) | **₦24,625** |
| $100 base | card, non-US | $6.90 (6.9%) | $93.10 |
| $100 base | card, US | $5.40 (5.4%) | $94.60 |
| $100 base | **USDT/USDC** | $1.50 (1.5%) | **$98.50** |
| $30 addon | card, non-US | $2.35 (7.8%) | $27.65 |
| $30 addon | **USDT/USDC** | $0.45 (1.5%) | **$29.55** |

**Nigerian pricing is far more fee-efficient than international.** Bank transfer
costs 1.5% capped at ₦2,000; international cards cost 5% + $0.40, plus 1.5% more
for non-US cards — and most of your international buyers will hold non-US cards.

**Correction — see `PAYMENTS.md`.** An earlier version of this document told you
to push USDT/USDC at international buyers for the 1.5% rate. **Withdrawn.** That
rail expects a customer who already holds stablecoin; it cannot be paid with a
normal Visa or Mastercard, and card-to-crypto onramps add 3–5% plus a KYC step.
Cards stay the default. Keep crypto as a quiet secondary option for the buyers
who prefer it.

For the same reason, 6.9% is not the outlier it looks like: `PAYMENTS.md` prices
it against every alternative available to a Nigerian seller.

Payouts: NGN → bank is ₦215 flat, so **batch weekly, never per sale**. USD
payout is 1%, or hold USD and withdraw as USDT.

## Disputes will hurt more than you expect

A refund costs **$1.00**. A dispute costs **$30.00**.

On a $30 addon that is 1.0× the sale. On a ₦25,000 addon it is **1.9× the sale**
— one chargeback wipes out two of them.

**Refund immediately, in full, without argument.** It is always cheaper than
losing the dispute, and at ₦35k the relationship is worth more than the sale.
Make refunds visible and easy, because a customer who cannot find the refund
button files a chargeback instead.

## Integration notes

- **Webhooks are the source of truth**, never redirects or client events.
  `collection.succeeded` creates the licence; nothing else does.
- **Lifetime means one-time products** — omit `billing_cycle`. Skip subscriptions
  entirely, which also avoids the coming +0.5% billing-volume fee.
- **Use `Idempotency-Key` on every POST.** Nigerian connectivity means retries.
- Sandbox first (`sk_sandbox_`), and going live is a key swap.
- Money is a decimal string with an ISO 4217 currency. Never minor units — note
  this differs from `licence-schema.sql`, which stores minor units internally;
  convert at the boundary.

---

# 3. Pricing

## Your prices

| | Nigeria | International |
|---|---|---|
| Base | ₦35,000 | $100 |
| Each addon | ₦25,000 | $30 |
| Full stack | ₦135,000 (~$87) | $220 |

## The one thing I would reconsider

**Your Nigerian addon is priced at 71% of the base. Internationally it is 30%.**
A Nigerian buyer faces **2.4× the marginal price** for the same addon.

At ₦25,000 an addon costs nearly as much as the whole tool, so the rational
Nigerian buyer buys the base and stops. That is a shame, because the week-3
trial is designed specifically to create addon demand — and it will create
demand that the price then refuses.

**₦12,000–15,000 per addon** would mirror the international ratio. Four addons
at ₦12,000 is ₦48,000 on top of ₦35,000: a full stack of ₦83,000, which is a
plausible purchase. At ₦135,000 it is not, and you will sell base-only to almost
everyone.

You know your market better than I do. But if the trial converts poorly in
Nigeria, this is why, and the fix is the price rather than the reminder emails.

## What lifetime pricing means structurally

Lifetime licences fund a **perpetual** server dependency. Revenue is one-time;
the ledger costs money every month forever.

At $5/month this is not a problem — 300 customers at ₦34,475 net is roughly
₦10.3M against $60/year of hosting. But the shape is worth naming, because
Workers Paid charges scale with users while your revenue does not. Model it
again at 5,000 users, not before.

**A practical consequence:** an entitlement token that never expires still has
to refresh every 14 days. Lifetime is about *entitlement*, not about the token.
Revocation stays available for refunds and chargebacks.

## Trial mechanics against these prices

Week 3 grants all four addons for a week. In Nigeria that is ₦100,000 of value
given away and then withdrawn — a bigger emotional swing than $120 is
internationally, precisely because the addon-to-base ratio is so high.

**Track what they actually used** and make the reminder about that one thing.
"You built 11 outreach drafts — here is what those are doing now" against a
₦25,000 price is a harder sell than it should be, which brings you back to the
ratio question above.

---

## Files

| File | What it is |
|---|---|
| `unit_economics.py` | Fee model, capacity model, gap list — runnable |
| `licence-schema.sql` | Licensing tables; `payment_ref` holds the Bachs charge id |
| `installer.py` | Activation, offline grace, download, verification |
