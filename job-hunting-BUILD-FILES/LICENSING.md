# Licensing — API surface and activation flow

The piece the whole IP strategy rests on, so it is worth being clear about what
it can and cannot do.

**It cannot stop a determined attacker.** Nothing client-side can. What it does
is make casual sharing pointless and keep the one genuinely non-copyable asset —
the ledger — behind a check that runs on your infrastructure.

## The constraint that shapes everything

**It must work offline.** Your customers are on connections that drop. A
licensing system that bricks the tool when the network is unavailable does not
stop piracy; it punishes the paying customer and generates the refund request.
Losing a week's work to a dropped connection is a worse outcome for your
business than a pirated copy.

So the server issues a **short-lived signed entitlement token**. The client
verifies it locally against a pinned public key, works offline until it expires,
and keeps working through a long grace period after that.

| | |
|---|---|
| Token life | 14 days |
| Grace after expiry | 30 days |
| Effective offline tolerance | 44 days |
| Rebinds per year, self-service | 3 |

**Nothing in the client is a boolean anyone can flip.** The client only ever
checks a signature. A forged token fails verification and grants nothing —
tested, and it grants strictly less than no token at all.

## Endpoints

```
POST /v1/activate          licence_id + machine fingerprint -> seat + token
POST /v1/refresh           seat + current token             -> fresh token
GET  /v1/bundles           token                            -> what this seat may download
GET  /v1/bundles/{id}      token                            -> signed, watermarked bundle
POST /v1/seats/release     token                            -> free the seat, no ticket
POST /v1/telemetry         token + Channel A counts         -> ack
POST /v1/ledger/sync       token                            -> priors + dead list
```

`/v1/ledger/sync` is the one that matters. **It is the licence check** — not a
separate gate, but the thing a copied client cannot get and cannot fake. A
pirated copy still runs; it just decays from the day it was copied while paying
customers get a tool that improves. That is the only protection here a
determined copier cannot defeat, and it is why the architecture decision and the
business-model decision are the same decision.

## Activation

1. Customer pays. Paystack or Flutterwave webhook creates the licence.
2. Installer asks for the licence id.
3. Client computes a **fingerprint** — a salted hash of stable machine facts.
   Salted, so it is not a device identifier you could correlate across
   customers.
4. `POST /v1/activate` returns a seat, a random `node_id`, a per-seat
   **watermark**, and the first token.
5. Client fetches its bundles. **Skills are fetched at activation, never shipped
   in the installer**, so there is nothing to forward before a licence exists.
6. Bundles are built with that seat's watermark baked in.

`node_id` is random and never derived from the licence. It is the only value
shared with the ledger, which is what keeps aggregate telemetry from becoming
identified personal data.

## Seat binding is deliberately forgiving

People reinstall, replace laptops, and lose phones. **A licensing system that
treats every rebind as fraud generates more support cost than the piracy it
prevents** — and at a few hundred customers, support cost is what kills you, not
piracy.

So: same fingerprint reactivating never consumes a second seat. A new machine
rebinds automatically, releasing the oldest seat, up to three times a year.
Past that a human is involved. Users can release a seat themselves without
contacting you.

## Revocation propagates by silence

A revoked licence cannot refresh, and its existing token stays valid until it
expires. That is the correct trade: a legitimate refund does not cut someone off
mid-session, and the worst case is a refunded customer keeping the tool for up
to a fortnight. Cutting off instantly would mean every network hiccup looked
identical to a revocation.

## Trials (item 6)

Scheduled at activation rather than triggered later, so it survives the
scheduler being down for a day.

- **Day 0–14** — the plan they bought.
- **Day 14–21** — every addon, automatically.
- **Day 21 on** — back to their plan, under the degradation contracts in
  `PACKAGING.md`. Data retained, readable, restored on purchase.

`trial_usage` records **what they actually used**. That is the whole point: a
reminder listing six addons is ignorable; *"you built 11 outreach drafts during
your trial — here is what those are doing now"* is not.

One thing to get right: an expired addon's spending and sending gates go
**dormant, not permissive**. An expired addon leaving a send path open is the
worst bug available in this system.

## Watermarking

Each seat's bundles carry unique invisible markers — whitespace patterns, benign
comment ids, a per-seat salt in a config value. A leaked copy is traceable to
the buyer.

At your scale this deters sharing better than obfuscation, because **the
deterrent is social rather than technical.** Someone who knows their copy is
traceable does not send it to fifteen friends. `watermark_sightings` records
what you find and what you did about it — and *contacted* should usually beat
*revoked*. A customer who shared a copy is still a customer.

## Two databases, never joined

The licensing database holds names, emails and payment references. The ledger
holds pseudonymous counts. **Joining them would turn Channel A telemetry into
identified personal data and undo the whole privacy design in one foreign key.**

The only shared value is `node_id`, which is random and lives here. NDPA 2023
gives a data subject the right to demand deletion — which is executable without
breaking the ledger precisely because the ledger holds no personal data at all.

## What is verified where

| Check | Where | Why |
|---|---|---|
| Signature on the token | Client | Works offline |
| Entitlements | Client, from signed claims | Cannot be forged |
| Seat limits | **Server** | The client cannot be trusted to count |
| Revocation | **Server**, at refresh | Client-side would be patched out |
| Bundle access | **Server** | The only true gate on delivery |
| Ledger access | **Server** | The asset a copy cannot have |

Anything a client could lie about is checked on the server. Anything the client
needs offline is signed.

## Files

| File | What it is |
|---|---|
| `licence-schema.sql` | Server tables — 10 tables, 1 view |
| `licence_client.py` | Reference activation, verification, offline grace, trials |

`python3 licence_client.py --selftest` — 21 checks, covering activation,
reactivation, bounded rebinds, offline grace, expiry, forged tokens,
revocation, and the trial lifecycle.

## What I would not build

**A phone-home on every launch.** It adds a failure mode on every start for
protection the fortnightly refresh already provides.

**Hardware-locked licences.** The support burden is real and immediate; the
piracy prevented is speculative.

**Aggressive anti-tamper.** Effort better spent on `strip_rationale` in the
build, which removes more intellectual value from a leaked copy than any
runtime defence, and costs nothing.
