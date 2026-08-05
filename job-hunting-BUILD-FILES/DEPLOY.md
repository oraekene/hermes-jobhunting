# Deploy — step by step

Assumes Windows with the package at the project root.
Every command is copy-pasteable. Where something needs a decision rather than a
command, it says so.

**Read `STATUS.md` first.** Steps 1–6 give you a sellable product. Steps 7–8 are
the pieces that are specced but not built.

---

## 0. Prerequisites

```powershell
node --version      # need 18+
python --version    # need 3.10+
npm i -g wrangler
pip install pyyaml
```

Accounts: Cloudflare (free), GitHub (free), Bachs, Resend (free).

---

## 1. Apply the preflight fixes

Copy this bundle's files into your package folder first, then:

```powershell
cd job-hunting-BUILD-FILES
python apply_preflight.py --root .. --dry-run
```

Read the plan. Then:

```powershell
python apply_preflight.py --root . --apply
```

Every edited file is backed up to `<file>.pre21.bak`, and re-running is safe —
it reports "already present" rather than duplicating.

That covers fixes 1, 2 and 4. **Three still need you**, and the script prints
exactly where:

- **Fix 3** — 30 line occurrences across 19 skill relationships. Replace each
  reference to an addon skill with `capability:<name>` and give it a defined
  behaviour when absent. This is the one that gates the addon model.
- **Fix 5** — trace how `daily_staging_cap` is actually enforced. Do this before
  any sending gate ships as toggleable.
- **Fix 6** — replace `00-orchestrator/scripts/install-check.py` with the tested
  one from this bundle.

Verify:

```powershell
python check_gates.py
python check_flows.py
python check_manifest.py
python check_onboarding.py
python check_patterns.py
```

All five must pass. The build refuses to run otherwise, by design.

---

## 2. Repository and secrets

```powershell
cd ..
git init
git remote add origin https://github.com/YOU/hermes-jobhunting.git
```

**Keep it private.** `_merge-history/` and the audit files are excluded from the
build, not from the repo.

Copy `.github/workflows/release.yml` in, then set four repository secrets under
Settings → Secrets and variables → Actions:

`SIGNING_KEY`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_ENDPOINT`.

Generate the signing key once and never lose it — every bundle you have ever
shipped verifies against it:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 3. Cloudflare

```powershell
cd worker
wrangler login
wrangler d1 create hermes
```

Paste the returned `database_id` into `wrangler.toml`. Then:

```powershell
npm test                              # 33 checks — do this before deploying
wrangler d1 execute hermes --remote --file=schema.sql
wrangler r2 bucket create bundles

node scripts/keygen.js                      # prints both halves, once
wrangler secret put TOKEN_PRIVATE_KEY       # signs entitlement tokens
wrangler secret put TOKEN_PUBLIC_KEY        # also pinned in the client
wrangler secret put BACHS_KEY               # sk_sandbox_... for now
wrangler secret put BACHS_WEBHOOK_SECRET
wrangler secret put RESEND_KEY
wrangler secret put ADMIN_TOKEN             # your dashboard
wrangler secret put GITHUB_TOKEN            # dispatches per-seat builds

wrangler deploy
```

You get a URL like `https://hermes-licensing.YOURNAME.workers.dev`. Check it:

```powershell
curl https://hermes-licensing.YOURNAME.workers.dev/v1/activate `
  -X POST -H "content-type: application/json" `
  -d '{\"licence_id\":\"LIC-nope\",\"fingerprint\":\"x\"}'
# expect: 404 {"error":"unknown licence"}   <- the Worker is live
```

**Stay on the free plan for now.** Move to $5 Workers Paid only after the rate
limits in `wrangler.toml` are live: on free a hammered endpoint returns error
1027 and you find out; on paid it keeps serving and charges you.

---

## 4. Bachs — ten products

Sandbox first. Because a Bachs product has one primary currency and NGN cannot
be an option on a USD product, each SKU exists twice.

```bash
# repeat for: base 35000/100, and each addon 25000/30
curl https://sandbox-api.bachs.io/v1/products \
  -H "Authorization: Bearer $BACHS_KEY" -H "Content-Type: application/json" \
  -d '{"name":"Hermes base",
       "price":{"price_type":"fixed","amount":"35000.00","currency":"NGN"},
       "metadata":{"sku":"base","market":"NG"}}'

curl https://sandbox-api.bachs.io/v1/products \
  -H "Authorization: Bearer $BACHS_KEY" -H "Content-Type: application/json" \
  -d '{"name":"Hermes base",
       "price":{"price_type":"fixed","amount":"100.00","currency":"USD"},
       "metadata":{"sku":"base","market":"INT"}}'
```

Put the ten returned ids into `CATALOG` at the top of `worker/src/index.js`, then
redeploy. Register the webhook endpoint in the Bachs dashboard:

```
https://hermes-licensing.YOURNAME.workers.dev/v1/webhooks/bachs
```

Subscribe to `collection.succeeded`, `refund.succeeded`, `dispute.created`. Copy
the signing secret into `BACHS_WEBHOOK_SECRET`.

**Test with a sandbox purchase before touching live keys.** Confirm a licence
row appears, a trial is scheduled, and — if you used a `?ref=` link — a
commission sits in `held`.

---

## 5. Build and serve bundles

Tag a release:

```powershell
git tag v1.0.0
git push origin v1.0.0
```

Actions validates, regenerates the graph and manual, builds, signs, and uploads
to R2. Roughly two minutes against a 2,000-minute monthly allowance.

**Per-seat bundles are built on demand**, triggered by your webhook handler
calling `workflow_dispatch` with the seat id. Until you wire that, build them by
hand:

```powershell
python build.py build --src . --out dist --seat SEAT_ID --key %SIGNING_KEY%
python build.py verify --bundle dist --key %SIGNING_KEY%
```

**Per-seat builds are now automatic.** First activation dispatches the workflow
with the seat id; the build uploads to `R2://bundles/<seat>/`. Until that lands,
`GET /v1/bundles/{id}` serves the shared `core-template` build and sets
`x-watermarked: false`, so a customer is never blocked waiting on CI.

Upload the template builds once so that fallback exists:

```powershell
python build.py build --src . --out dist --seat core-template --key %SIGNING_KEY%
tar -czf core-1.0.0.tar.gz -C dist .
wrangler r2 object put bundles/core-template/core-1.0.0.tar.gz --file core-1.0.0.tar.gz
```

Then register each bundle in D1 so it is listable:

```powershell
wrangler d1 execute hermes --remote --command `
  "INSERT INTO bundles (bundle_id,scope,version,sha256,signature,published_at) `
   VALUES ('b_core','core','1.0.0','<sha>','<sig>',datetime('now'))"
```

---

## 5b. Publish the installer

The installer ships **separately from the bundle** — it is the thing that
fetches the bundle, so it cannot be inside it. That means it needs its own
build step, and forgetting it is a blocker rather than a rough edge: an
unstamped installer refuses to install for every customer.

```powershell
cd worker; node scripts/keygen.js       # if you have not already
cd ..
python build.py stamp-installer --public-key "PASTE_THE_PUBLIC_HALF" --out dist/installer.py
```

It prints a sha256. **Publish that hash beside the download link** so a customer
can check what they ran.

Upload `dist/installer.py` to your Pages site. The whole customer path is then:

```
buy  ->  licence key by email  ->  download installer.py
     ->  python installer.py --key LIC-xxxx
     ->  activated, downloaded, verified, install-checked
```

`installer.py --status` tells them their licence state; `--release` frees the
machine so they can move to another one without contacting you.

## 6. Site and email

```powershell
wrangler pages deploy ./site --project-name hermes
```

Pricing page calls `POST /v1/checkout` and redirects to the returned URL. It must
never send a product id, a price, or a market — the server decides all three
from `cf-ipcountry`. That single rule is what protects the 4.3× price gap.

Resend: verify your domain, create an API key, add it as `RESEND_KEY`. Both
emails are wired already — licence delivery fires from the purchase webhook,
payout notices from the monthly run. Everything else rides Telegram.

**Check your own numbers any time:**

```powershell
curl https://hermes-licensing.YOURNAME.workers.dev/v1/admin/summary `
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
# views: summary, sales, trial_conversion, affiliates, ledger, payouts-preview
```

`trial_conversion` splits by market. That is the query that answers whether the
NGN 25,000 addon price is too high — measured rather than argued.

---

## 7. Go-live checklist

- [ ] Five checkers pass
- [ ] `npm test` — 52 checks
- [ ] `python test_install_check.py` — 13 cases
- [ ] `python test_installer.py` — 17 checks
- [ ] Sandbox purchase creates exactly one licence; a replay creates none
- [ ] A refund claws the commission back and blocks refresh
- [ ] `GATEWAY_ALLOW_ALL_USERS` is **not** set anywhere
- [ ] Rate limits live before moving to Workers Paid
- [ ] Signing key backed up somewhere you will still have in three years
- [ ] `dist/installer.py` is **stamped** — `check_build.py` fails if it is not
- [ ] Installer hash published beside the download link
- [ ] Terms state the user is the applicant of record for anything auto-sent
- [ ] Swap sandbox keys for live keys — last step, not first

---

## 8. Still to build

Per `STATUS.md`: the permission-pack skill, the message catalog, and the
federated loop (client plus weekly aggregation).

**None of them blocks a first sale.** Everything between a payment and a working
install now exists and is tested — buy, key by email, activate, download a
watermarked bundle. Ship that, then add depth with paying customers in front of
you rather than guessing what they need.
