# Payments — corrections, comparison, and the affiliate program

Four of your questions changed my answer. Taking them in order.

---

## 1. What email do *you* actually need to send?

You are right that user-facing email — cold outreach, applications — goes out
from their own agent, on their own account. That is not your gap.

**The gap is the ~30 seconds between payment and a working install**, plus
anything you need to tell a customer who is not currently in a Telegram chat
with the tool.

| Email | Can Telegram replace it? |
|---|---|
| **Licence key + install link after purchase** | **No** — this is the irreducible one |
| Receipt | Bachs sends this |
| Trial start / trial ending / trial ended | Yes, once installed |
| "Here is what you built with X" reminder | Yes |
| Update available | Yes |
| Security advisory | Yes, but email is a safer second channel |
| Refund confirmation | Bachs sends this |
| Affiliate payout notice | **No** — affiliates never install the tool |

**So the real requirement is two emails, not a newsletter platform:** licence
delivery, and affiliate payout notices. Everything else can ride the Telegram
channel the tool already owns — which is *better* than email anyway, because
open rates are higher and you are already paying nothing for it.

At two emails per sale, Resend's free tier (3,000/month) covers roughly 1,500
sales a month. You will not outgrow it.

**One caution.** Do not make Telegram the *only* channel for security notices.
If someone uninstalls, changes phone, or blocks the bot, you have no way to
reach them — and a security advisory that cannot be delivered is not an
advisory. Keep the email address on file and use it for that one case.

---

## 2. Crypto — I was wrong for your users

**No. USDT/USDC cannot be paid with a normal Visa or Mastercard** through
Bachs's 1.5% crypto rail. That rail expects a customer who already holds
stablecoin in a wallet and sends it on-chain. Card-to-crypto onramps exist, but
they add 3–5% of their own plus a KYC step, which erases the saving and adds
friction exactly where you cannot afford it.

I optimised for margin and ignored who your buyer is. **Withdraw the
recommendation.** Cards should be the default and the prominent option.

Keep crypto as a quiet secondary option — some international buyers genuinely
prefer it, and every one who uses it saves you five points — but never as the
path you steer people down.

---

## 3. Is 6.9% high? No. It is the market rate.

I gave you the number without context, which made it look worse than it is.

**What $100 actually costs, by provider (non-US card — the common case):**

| Provider | Effective | Fee | Net | Note |
|---|---|---|---|---|
| Creem | 3.9% | $4.30 | $95.70 | cheapest MoR; verify NGN payout |
| Dodo Payments | 4.0% | $4.40 | $95.60 | built for non-US founders |
| *Stripe* | *4.4%* | *$4.70* | *$95.30* | **not available to you** |
| Paddle | 5.0% | $5.50 | $94.50 | **+2–3% FX in its own MSA** → really ~7–8% |
| **Bachs** | **6.5%** | **$6.90** | **$93.10** | MoR, NGN + USD payout, no US bank |
| Lemon Squeezy | 6.5% | $7.00 | $93.00 | +1.5% intl; Stripe-owned since 2024 |
| Polar (2026 Starter) | 6.5% | $7.00 | $93.00 | pays via Stripe Connect — **not Nigeria** |
| Gumroad | 12.9% | $13.70 | $86.30 | 10% + 50¢ **plus** 2.9% + 30¢ |

**Bachs is not an outlier.** It matches Lemon Squeezy and Polar once their
international surcharges are counted, beats Paddle once Paddle's own currency
conversion is added, and is half of Gumroad. The headline rates you see quoted
elsewhere — "Paddle is 5%" — are not all-in, and the honest all-in figure for a
non-US founder selling internationally is 7–8% at Paddle.

**What you are buying for the 6.5%** is merchant-of-record coverage: VAT in the
EU, GST in Australia, sales tax across 40+ US states, all collected and remitted
by someone else. Doing that yourself is not a 2% problem, it is a compliance
department.

**Also worth seeing clearly:** your Nigerian sales cost **1.5%, capped at
₦2,000**. If most of your volume is Nigerian, your blended rate is closer to 2%
than 6.5%, and the international rate barely matters.

### Alternatives genuinely worth a look

**Creem (3.9% + 40¢) and Dodo Payments (4% + 40¢)** are the only two that would
save you real money — about 2.5 points, or $2.50 per base sale. Both position
themselves for non-US founders. **Before switching, confirm one thing: can they
pay out to a Nigerian bank account, and in what currency?** That is where most
MoRs fail Nigerian sellers, and it is why Polar is unusable for you regardless
of price — it settles through Stripe Connect.

**Korapay for NGN only** is workable but I would not bother. Bachs already
charges 1.5% capped on NGN transfers, which is at or below what Korapay would
charge, and running two providers means two integrations, two webhook handlers,
two reconciliation processes and two failure modes — for a saving of roughly
nothing on your largest volume segment.

**My recommendation: stay on Bachs.** The saving from Creem or Dodo is $2.50 a
sale on your smaller segment, against the cost of re-integrating, and against a
platform that is explicitly built for the payout problem you actually have. If
you want to revisit, revisit when international is over half your revenue.

---

## 4. "Two products per SKU" — illustrated

Bachs lets a product have **one** primary currency, USD **or** NGN. The
`currency_options` list — which is how you set an exact price in a second
currency — **cannot contain the primary currency**, and only covers GHS, KES,
UGX, TZS, XAF, XOF, ZMW, RWF. Neither USD nor NGN can be an option on the other.

So this does not exist:

```json
{ "name": "Hermes base",
  "price": { "amount": "100.00", "currency": "USD",
             "currency_options": [ { "currency": "NGN", "amount": "35000.00" } ] } }
```

`NGN` is a primary currency, not an option. It will be rejected.

**Instead, create the same thing twice** — once with each primary:

```bash
# NGN product — sold to Nigerian buyers
curl https://sandbox-api.bachs.io/v1/products \
  -H "Authorization: Bearer $BACHS_API_KEY" -H "Content-Type: application/json" \
  -d '{ "name": "Hermes base",
        "price": { "price_type": "fixed", "amount": "35000.00", "currency": "NGN" },
        "metadata": { "sku": "base", "market": "NG" } }'
# -> prod_ng_base

# USD product — same thing, sold to everyone else
curl https://sandbox-api.bachs.io/v1/products \
  -H "Authorization: Bearer $BACHS_API_KEY" -H "Content-Type: application/json" \
  -d '{ "name": "Hermes base",
        "price": { "price_type": "fixed", "amount": "100.00", "currency": "USD" },
        "metadata": { "sku": "base", "market": "INT" } }'
# -> prod_int_base
```

Ten products in total:

| SKU | NGN product | USD product |
|---|---|---|
| base | ₦35,000 | $100 |
| addon-interview | ₦25,000 | $30 |
| addon-outreach | ₦25,000 | $30 |
| addon-direction | ₦25,000 | $30 |
| addon-presence | ₦25,000 | $30 |

Your own code holds the mapping and picks:

```js
const CATALOG = {
  base:            { NG: "prod_ng_base",     INT: "prod_int_base" },
  "addon-outreach":{ NG: "prod_ng_outreach", INT: "prod_int_outreach" },
  // ...
};

// market is decided SERVER-SIDE from request geography, never from the client
const market = cf.country === "NG" ? "NG" : "INT";

await fetch("https://api.bachs.io/v1/checkout-sessions", {
  method: "POST",
  headers: { Authorization: `Bearer ${env.BACHS_KEY}`,
             "Content-Type": "application/json",
             "Idempotency-Key": crypto.randomUUID() },
  body: JSON.stringify({
    product_cart: skus.map(s => ({ product_id: CATALOG[s][market], quantity: 1 })),
    customer: { email },
    return_url: "https://yoursite.com/thanks",
    cancel_url: "https://yoursite.com/pricing",
  }),
});
```

**The important part is what is *not* there.** No product id from the client, no
`billing_currency` from the client, no market parameter in the URL. The customer
never sees a product id, so the ₦35,000 checkout is not something a visitor
abroad can request — it is something your server decides to create.

That single rule is what protects a 4.3× price gap. `metadata.sku` is what your
`collection.succeeded` handler reads to decide which entitlement to grant, so
the same handler serves both markets.

---

## 5. GitHub Actions — free, with a real allowance

**Public repositories: unlimited and unmetered.** Yours will be private, so:

| Plan | Included Linux minutes/month | Artifact storage |
|---|---|---|
| **Free** | **2,000** | 500 MB |
| Team ($4/user/mo) | 3,000 | 2 GB |

Beyond that, Linux 2-core is **$0.006/min** after the January 2026 repricing
(down up to 39%). Windows drains the quota at 2× and macOS at 10× — stay on
Linux. Minutes do not roll over.

**Your build is a few minutes: strip rationale, compile scripts, watermark,
sign, upload.** Say 5 minutes a run. 2,000 free minutes is **400 builds a
month**. You will not come close, and if you did, the overage on 100 extra
builds is $3.

One note: the $0.002/min self-hosted-runner charge announced for March 2026 was
postponed after backlash and never took effect. Some comparison sites still list
it as live. Irrelevant to you — you will use GitHub-hosted runners.

**Watch the artifact storage,** not the minutes. 500 MB is shared with GitHub
Packages, and per-seat watermarked bundles accumulate fast if you upload them as
artifacts. Push them straight to R2 instead and keep artifacts for build logs
only.

---

## 6. Pricing — retained as you specified

₦35,000 / ₦25,000 and $100 / $30, unchanged. Noted and built into everything
below.

One thing worth instrumenting rather than arguing: **track the Nigerian addon
attach rate after the week-3 trial separately from the international one.** If
the Nigerian rate comes in below half the international rate, that is the price
ratio talking, and you will have real numbers rather than my guess. Cheap to
measure, and you can change the price later — you cannot un-charge someone.

---

## 7. The 15% affiliate program

Bachs has no affiliate feature, so attribution lives in your licensing server.
`affiliate-schema.sql` — 5 tables and a view.

### What you keep

| Sale | Gross | Processing | Affiliate | Net | Kept |
|---|---|---|---|---|---|
| Nigeria base | ₦35,000 | ₦525 | ₦5,250 | **₦29,225** | 84% |
| Nigeria addon | ₦25,000 | ₦375 | ₦3,750 | ₦20,875 | 84% |
| Intl base (card) | $100.00 | $6.90 | $15.00 | **$78.10** | 78% |
| Intl addon (card) | $30.00 | $2.35 | $4.50 | $23.15 | 77% |

Affordable. 15% is a normal rate and these margins hold.

### The one number that shapes the whole design

**A chargeback costs $30, and a commission already paid is gone.** Together, on
a ₦35,000 sale: ₦35,000 reversed, ₦46,500 dispute fee, ₦5,250 commission — a
**₦86,750 loss on a ₦35,000 sale, 2.5×**.

So commissions are **earned at purchase and payable only after the refund
window closes.** Five states: `held` → `payable` → `paid`, with `clawed` if the
refund lands before payout and `reversed` if it lands after. Thirty days is the
right window.

### Payout thresholds are not optional

An NGN payout costs a flat ₦215. Paying a single ₦5,250 commission burns **4.1%
of it**. A ₦10,000 minimum, paid monthly, brings that under 2.1%. USD payouts
are 1%, so a $50 minimum is enough there.

### Attribution rules

- **Read the code from the checkout session you created**, never from the
  webhook payload or a client-supplied field. Same discipline as the product
  ids above.
- **Lifetime products make this simple:** one purchase, one commission, no
  recurring attribution and no cookie-window arguments.
- **Addons count.** Someone who refers a customer who later buys three addons
  earned that; paying only on the base teaches affiliates to stop promoting.
- **Last-touch, 30-day window**, recorded at session creation.

### Fraud, handled without banning honest people

Four signals, all queued for a human rather than auto-enforced — a false ban on
a genuine affiliate costs you far more than any commission:

- **self-referral** — buyer email or machine fingerprint matches the affiliate
- **fingerprint cluster** — many referrals from one machine
- **refund rate** — referred sales refunding well above baseline
- **velocity** — implausible conversions in a short window

Self-referral is the common one and it is mostly not malice: people genuinely
think using their own code is a discount. Say so plainly in the terms, then
decline it quietly rather than banning.

### One thing to decide now

**Are affiliates paid in their own currency or yours?** A Nigerian affiliate
referring an international sale earns $15 — pay in USD and they need a domiciliary
account; convert to NGN and you carry the FX. I would pay each affiliate in
**one** currency chosen at signup and convert at your side, because one
conversion at your volume is cheaper than many at theirs.

---

## Files

| File | What it is |
|---|---|
| `unit_economics.py` | Fees, provider comparison, affiliate math, capacity — runnable |
| `affiliate-schema.sql` | Affiliate tables, holds, clawbacks, payouts |
| `licence-schema.sql` | Licences and entitlements; `payment_ref` holds the Bachs charge id |
