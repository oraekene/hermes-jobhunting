#!/usr/bin/env python3
"""
unit_economics.py — what actually lands in your account, and when free stops.

Two models:
  1. Bachs fees per sale, by market and payment method.
  2. Cloudflare free-tier headroom against user count.

    python3 unit_economics.py
"""
from dataclasses import dataclass

NGN_PER_USD = 1550.0          # adjust; every naira figure below moves with it

# ── prices ──────────────────────────────────────────────────────────────────
PRICES = {
    "NG": {"base": 35_000, "addon": 25_000, "ccy": "NGN"},
    "INT": {"base": 100.0, "addon": 30.0,   "ccy": "USD"},
}

# ── Bachs fee schedule (docs.bachs.io/for-you/fees) ─────────────────────────

def fee_ngn_transfer(amount):        # 1.5% capped at NGN 2000
    return min(amount * 0.015, 2000)

def fee_ngn_card(amount):            # 2% local cards (beta)
    return amount * 0.02

def fee_usd_card(amount, us_issued=False):
    rate = 0.05 if us_issued else 0.065        # +1.5% for non-US cards
    return amount * rate + 0.40

def fee_usd_crypto(amount):          # USDT / USDC
    return amount * 0.015

def fee_mobile_money(amount):
    return amount * 0.035

PAYOUT_NGN = 215.0                   # NGN 200 + NGN 15 VAT, per payout not per sale
PAYOUT_USD_RATE = 0.01
REFUND_FEE_USD = 1.00
DISPUTE_FEE_USD = 30.00


def line(label, gross, fee, ccy, note=""):
    net = gross - fee
    pct = fee / gross * 100
    g = f"{gross:,.0f}" if ccy == "NGN" else f"{gross:,.2f}"
    f_ = f"{fee:,.0f}" if ccy == "NGN" else f"{fee:,.2f}"
    n = f"{net:,.0f}" if ccy == "NGN" else f"{net:,.2f}"
    print(f"  {label:<34}{ccy} {g:>9}   {ccy} {f_:>8} ({pct:4.1f}%)   {ccy} {n:>9}   {note}")


def sales():
    print("BACHS FEES PER SALE")
    print(f"  {'':<34}{'gross':>13}{'fee':>22}{'net':>17}")
    ng = PRICES["NG"]
    for name, amt in [("base", ng["base"]), ("addon", ng["addon"])]:
        line(f"Nigeria {name} — bank transfer", amt, fee_ngn_transfer(amt), "NGN")
        line(f"Nigeria {name} — local card", amt, fee_ngn_card(amt), "NGN")
    it = PRICES["INT"]
    for name, amt in [("base", it["base"]), ("addon", it["addon"])]:
        line(f"Intl {name} — card (non-US)", amt, fee_usd_card(amt), "USD")
        line(f"Intl {name} — card (US)", amt, fee_usd_card(amt, True), "USD")
        line(f"Intl {name} — USDT/USDC", amt, fee_usd_crypto(amt), "USD", "<- cheapest by far")

    print("\nFULL STACK (base + 4 addons)")
    ng_total = ng["base"] + 4 * ng["addon"]
    it_total = it["base"] + 4 * it["addon"]
    print(f"  Nigeria        NGN {ng_total:>10,.0f}   (~USD {ng_total/NGN_PER_USD:,.0f})")
    print(f"  International  USD {it_total:>10,.2f}   (~NGN {it_total*NGN_PER_USD:,.0f})")
    print(f"  Ratio          international costs {it_total/(ng_total/NGN_PER_USD):.1f}x the Nigerian price")

    print("\nADDON PRICE AS A SHARE OF BASE")
    print(f"  Nigeria        {ng['addon']/ng['base']:.0%}")
    print(f"  International  {it['addon']/it['base']:.0%}")
    print(f"  A Nigerian buyer faces {(ng['addon']/ng['base'])/(it['addon']/it['base']):.1f}x the "
          f"marginal price for\n  the same addon. Expect a much lower attach rate.")

    print("\nWHAT A DISPUTE COSTS")
    for mkt, amt, ccy in [("Nigeria addon", ng["addon"], "NGN"),
                          ("Intl addon", it["addon"], "USD")]:
        cost = DISPUTE_FEE_USD * (NGN_PER_USD if ccy == "NGN" else 1)
        print(f"  {mkt:<16}{ccy} {cost:>10,.0f} fee against a {ccy} {amt:,.0f} sale "
              f"= {cost/amt:.1f}x the sale")
    print("  A refund costs USD 1.00. A dispute costs USD 30.00. Refund fast and")
    print("  without argument — it is always cheaper than losing the dispute.")


# ── Cloudflare capacity ─────────────────────────────────────────────────────

@dataclass
class Load:
    users: int
    ledger_syncs_per_user_per_day: float = 1.0
    telemetry_per_user_per_day: float = 1.0
    token_refresh_per_user_per_day: float = 1 / 14
    rows_written_per_user_per_day: float = 6.0


FREE = {"requests_day": 100_000, "d1_rows_written_day": 100_000,
        "d1_rows_read_day": 5_000_000, "kv_writes_day": 1_000,
        "r2_class_a_month": 1_000_000, "queue_ops_day": 10_000,
        "cpu_ms_per_request": 10}


def capacity():
    print("\n\nCLOUDFLARE FREE-TIER HEADROOM")
    print(f"  {'users':>8}{'req/day':>12}{'% of cap':>11}{'rows written':>15}{'% of cap':>11}")
    for n in (100, 500, 2_000, 10_000, 40_000):
        l = Load(n)
        req = n * (l.ledger_syncs_per_user_per_day + l.telemetry_per_user_per_day +
                   l.token_refresh_per_user_per_day)
        rows = n * l.rows_written_per_user_per_day
        print(f"  {n:>8,}{req:>12,.0f}{req/FREE['requests_day']*100:>10.0f}%"
              f"{rows:>15,.0f}{rows/FREE['d1_rows_written_day']*100:>10.0f}%")
    print("\n  Request volume is not what breaks first. At 40,000 users you are still")
    print("  inside the daily request cap. The binding limit is CPU: 10 ms per")
    print("  request on Free, and two jobs blow straight through it.")


def gaps():
    print("\n\nWHERE FREE IS NOT ENOUGH")
    rows = [
        ("Per-seat bundle watermarking",
         "read a bundle, inject markers, rehash, sign — hundreds of ms",
         "$5 Workers Paid, or build offline"),
        ("Weekly hierarchical aggregation",
         "walks every cell x arm x tier; seconds, not milliseconds",
         "$5 Workers Paid (30s default, 5 min max)"),
        ("Outbound email",
         "Cloudflare has no transactional send product at all",
         "NOT fixed by $5 — needs a third party"),
        ("KV as a write store",
         "1,000 writes/day; a per-request write dies at 1,000 users",
         "use D1 instead — a design fix, not a spend"),
    ]
    for what, why, fix in rows:
        print(f"  {what}\n      {why}\n      -> {fix}")


# ── provider comparison ─────────────────────────────────────────────────────

PROVIDERS = [
    # name,                 pct,   fixed, intl_extra, chargeback, note
    ("Bachs (non-US card)",  0.050, 0.40, 0.015, 30.00, "MoR, NGN + USD payout, no US bank needed"),
    ("Creem",                0.039, 0.40, 0.000, 25.00, "cheapest MoR; verify NGN payout"),
    ("Dodo Payments",        0.040, 0.40, 0.000, 25.00, "built for non-US founders"),
    ("Polar (Starter 2026)", 0.050, 0.50, 0.015, 15.00, "pays via Stripe Connect - not NG"),
    ("Paddle",               0.050, 0.50, 0.000, 0.00,  "+2-3% FX in its own MSA"),
    ("Lemon Squeezy",        0.050, 0.50, 0.015, 0.00,  "Stripe-owned since 2024"),
    ("Gumroad (direct card)", 0.129, 0.80, 0.000, 0.00, "10% + 50c PLUS 2.9% + 30c"),
    ("Stripe (unavailable)", 0.029, 0.30, 0.015, 15.00, "not available to Nigerian entities"),
]


def providers(amount=100.0):
    print("\n\nWHAT $100 COSTS, BY PROVIDER (non-US card, the common case)")
    print(f"  {'provider':<24}{'effective':>11}{'fee':>9}{'net':>9}   note")
    rows = []
    for name, pct, fixed, intl, cb, note in PROVIDERS:
        fee = amount * (pct + intl) + fixed
        rows.append((fee, name, pct + intl, fee, amount - fee, note))
    for fee, name, eff, f_, net, note in sorted(rows):
        print(f"  {name:<24}{eff*100:>9.1f}%{f_:>9.2f}{net:>9.2f}   {note}")
    print("\n  Bachs at 6.5% + $0.40 is NOT an outlier. It sits with Polar and")
    print("  Lemon Squeezy once their international surcharges are counted, beats")
    print("  Paddle once Paddle's own 2-3% FX is added, and is half of Gumroad.")


# ── affiliate ───────────────────────────────────────────────────────────────

AFFILIATE_RATE = 0.15
PAYOUT_MIN_NGN = 10_000
PAYOUT_MIN_USD = 50.0


def affiliate():
    print("\n\n15% AFFILIATE — WHAT YOU KEEP")
    print(f"  {'sale':<22}{'gross':>11}{'processing':>12}{'affiliate':>11}{'net':>11}{'kept':>7}")
    cases = [
        ("Nigeria base", 35_000, "NGN", fee_ngn_transfer(35_000)),
        ("Nigeria addon", 25_000, "NGN", fee_ngn_transfer(25_000)),
        ("Intl base (card)", 100.0, "USD", fee_usd_card(100.0)),
        ("Intl addon (card)", 30.0, "USD", fee_usd_card(30.0)),
    ]
    for label, gross, ccy, proc in cases:
        comm = gross * AFFILIATE_RATE
        net = gross - proc - comm
        fmt = ",.0f" if ccy == "NGN" else ",.2f"
        print(f"  {label:<22}{gross:>11{fmt}}{proc:>12{fmt}}{comm:>11{fmt}}"
              f"{net:>11{fmt}}{net/gross*100:>6.0f}%")

    print("\n  PAYOUT COST TO THE AFFILIATE")
    print(f"  NGN payout is a flat NGN {PAYOUT_NGN:,.0f}. Paying one NGN "
          f"{35_000*AFFILIATE_RATE:,.0f} commission")
    print(f"  individually burns {PAYOUT_NGN/(35_000*AFFILIATE_RATE)*100:.1f}% of it. "
          f"Set a NGN {PAYOUT_MIN_NGN:,} minimum")
    print(f"  and pay monthly: the fee then falls under "
          f"{PAYOUT_NGN/PAYOUT_MIN_NGN*100:.1f}%.")

    print("\n  WORST CASE: AFFILIATE PAID, THEN CHARGEBACK")
    for label, gross, ccy, proc in cases[:1] + cases[2:3]:
        comm = gross * AFFILIATE_RATE
        cb = DISPUTE_FEE_USD * (NGN_PER_USD if ccy == "NGN" else 1)
        loss = gross + cb + comm - 0  # revenue reversed, fee charged, commission gone
        fmt = ",.0f" if ccy == "NGN" else ",.2f"
        print(f"  {label:<22}{ccy} {loss:>10{fmt}} lost on a {ccy} {gross:{fmt}} sale "
              f"= {loss/gross:.1f}x")
    print("  This is why commissions are held until the refund window closes.")


if __name__ == "__main__":
    sales()
    providers()
    affiliate()
    capacity()
    gaps()
