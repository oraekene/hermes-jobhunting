# Enrichment Tools — every option researched, ranked lowest cost to highest

Researched fresh, not assumed — several numbers below (Apollo's free
tier especially) are genuinely contested across sources or have changed
recently; noted explicitly rather than picked confidently where that's
the honest state of things. Re-verify anything time-sensitive before
relying on it; this table is a snapshot, not a live feed.

**Status note**: this file originally covered cost only — the token-
use/bot-restriction/rate-limit comparison promised when this research
started got dropped somewhere along the way. Restored below as its own
section, finished now rather than left as a gap.

## The full comparison, across every criterion originally asked for

| Method/tool | Token/agent cost | Bot-restriction risk | Rate limits | Coverage/accuracy | Notes |
|---|---|---|---|---|---|
| **Tier 0 — public pages, GitHub, press** | Very low (a few fetches) | None — normal page reads | None beyond normal fetch etiquette | Low-moderate, inconsistent | Best first move for small/technical companies |
| **Tier 1 — pattern-gen + MX/catch-all/SMTP** | Very low — `execute_code`, deterministic | None — standard DNS/SMTP protocol, not scraping any platform | Only the target mail server's own limits | High for standardized-pattern companies, poor for personal-domain/small-company addresses | The workhorse tier — most volume should land here |
| **theHarvester** | Low — one process invocation | None (public sources only) | Source-dependent, generally generous | Good for broad domain recon, not name-specific lookups | Genuinely free forever, self-hosted |
| **domain-intel (Hermes optional skill)** | Very low | None — passive DNS/WHOIS, no API key | None stated | N/A — infrastructure, not a finder itself | The actual tool behind Tier 1's MX check |
| **Hunter.io** | Low (one API call) | None (official API, own database) | 50/mo free; 2,000/mo at $34 | ~32.5% domain-search find rate (one benchmark) | Well-documented, most established brand |
| **Apollo.io** | Low | None | Free tier exists, contested size (~100-900/mo, shrinking) | ~70-80% estimated | Confirmed free entry point exists; not the generous one it used to be |
| **Prospeo** | Low | None | 75/mo free, ongoing | Claims ~98% (vendor figure) | Best-value free tier found |
| **Snov.io** | Low | None | 50/mo free | Mid-tier | Also has a database-search-by-role mode |
| **Exa.ai people search** | Low-moderate (semantic search, sometimes multi-step) | None — searches its own index, doesn't scrape LinkedIn's UI | 8,000 credits/$49 (Core), no free tier found | Good for identification, not bulk finding | Has an MCP server — a real Hermes tool connection, not just a raw API |
| **Parallel CLI (Hermes-official optional skill)** | Low-moderate — CLI call, JSON output, agent-native by design | None — its own web-intelligence stack, not platform scraping | Free tier confirmed to exist (no card required); exact monthly figure not independently confirmed | `enrich run` supports natural-language intent extraction (e.g. "find this person's work email"), priced per row | Confirmed in the **official** Hermes optional-skills catalog (`research/parallel-cli`) — install via `hermes skills install official/research/parallel-cli` |
| **RocketReach/SignalHire/ContactOut/Lusha, API mode** | Low | None — vendor's own database via API | Credit-based, $49-799/mo ranges | Good when target has a complete LinkedIn profile | See `linkedin-methods.md` for the API-vs-extension distinction |
| **RocketReach/SignalHire/ContactOut/Lusha, browser-extension mode** | N/A | **Real** — runs inside your own LinkedIn session | N/A | N/A | **Not used by this pipeline (Rule 6)** — listed for completeness, not as an option |
| **Clay.com** | Moderate — adds its own orchestration layer | None | Its own credits on top of providers it calls | Best-in-class via waterfall (80-95% claimed) | Right pattern, unnecessary third paid layer given we implement the same cascade natively |
| **ZeroBounce/Kickbox (verification)** | Low | None | 100/mo free each | High accuracy for the one thing they do | ZeroBounce is this skill's named default final check |

**One correction to a tool mentioned in an earlier pass**: "Explorium"
was described then as a Hermes-native GTM skill; a fresh crawl of the
*official* bundled and optional skills catalogs (both fetched directly,
not inferred) does not list it. Parallel CLI is the one confirmed via
the official catalog — treat any earlier mention of Explorium as
third-party/unconfirmed rather than Hermes-packaged.

## Genuinely free — open source, self-hosted, no account or credit system at all

| Tool | What it does | Cost |
|---|---|---|
| **Pattern generation + MX/catch-all/SMTP verify** | The core technique behind Part B Tier 1 — not a product, a method. Open-source prior art exists (e.g. `email-sleuth` on GitHub) doing exactly this: pattern generation, DNS/MX lookup, catch-all probing, SMTP handshake verification, concurrent processing. | **$0 — your own compute** |
| **theHarvester** (`github.com/laramies/theHarvester`) | 15,800+ GitHub stars, GPL. Passive OSINT recon — harvests emails, subdomains, names from 40+ public sources including search engines, certificate transparency, and PGP keyservers (which surfaces addresses that never appeared in a normal web crawl). Some optional premium sources need their own API key; the 40+ free sources need nothing. | **$0** |
| **holehe** (GPL-3.0, 5.6k+ stars) | Checks which of 120+ platforms a given email is registered on — useful as a corroboration/existence signal on a candidate address, not a finder itself. | **$0** |

## Free tiers — genuinely recurring monthly allowance, no card required

Ranked by most generous free monthly volume first. **The design in
`free-tier-rotation.md` stacks several of these together
rather than picking one.**

| Provider | Free allowance | Notes |
|---|---|---|
| **Prospeo** | 75 verified emails/mo + 100 Chrome-extension credits, ongoing, no expiration | Claims 98% accuracy, 7-day data refresh (most-cited "best free tier" across the comparisons checked — though several of those comparisons are themselves published by Prospeo, so treat the *ranking* with appropriate skepticism even though the credit numbers check out independently) |
| **Skrapp.io** | 100 credits/mo, **with rollover** | One of few with rollover on the free tier |
| **GetProspect** | 50 valid emails + 100 separate verifications/mo, **with rollover** (up to 1 month) | Enforces one free account per person |
| **Hunter.io** | 50 credits/mo (finding + verification share one pool) | Well-documented API, most established brand |
| **Snov.io** | 50 credits/mo | Also includes a database-search mode (browse by company/role before you have a name) |
| **Apollo.io** | Free tier exists ($0/mo) — **contested exact number**: sources report anywhere from ~100 to ~900 credits/mo as of mid-2026, down sharply from a former 10,000/mo after a late-2025 restructuring. One source specifically flags that **an account without a corporate email domain is capped at just 100/mo** — worth checking directly given your own setup, since a personal/freelancer email address may land you at the lower end regardless of the headline number. Confirms your instinct that Apollo has a genuine free entry point; it's a much smaller one than it used to be. |
| **ZeroBounce** (verification only) | 100/mo, ongoing, no expiration | |
| **Kickbox** (verification only) | 100/mo | |
| **AbstractAPI** (verification only) | 100/mo | |
| **EXPERTE.com** | No stated limit, no signup | Accuracy unverified — fine for a one-off spot check, not a primary source |

## One-time trial credits — not recurring, don't count toward monthly capacity

Anymail Finder (100, expire in 7 days), FindyMail (10, one-time),
Voila Norbert (50, one-time), RocketReach (5 lookups total),
Kaspr (15 B2B emails), Explorium's Hermes-native GTM skill (~50
enriched contacts trial). Useful for one-off evaluation, not for
ongoing rotation the way the recurring free tiers above are.

## Paid — ranked lowest starting cost to highest

| Tool | Entry cost | Notes |
|---|---|---|
| **NeverBounce** (verification only) | $0.008/verification, pay-as-you-go, no minimum | **No free tier as of 2026** — several older articles still list one; confirmed that's outdated |
| **Prospeo** (beyond free tier) | ~$0.01/email | Cheapest true per-lookup paid rate found |
| **theHarvester, cloud-hosted** (Apify) | $0.003/record | Only relevant if self-hosting the free version isn't wanted; the underlying tool is free either way |
| **Anymail Finder** | $9/mo (annual) | Pay-only-for-valid-results model |
| **Snov.io** | ~$29-39/mo | International-lead coverage is a stated strength |
| **Lusha** | ~$29.90/user/mo → 250 credits | Better known for phone numbers than email |
| **Hunter.io** | $34/mo (annual) → 2,000 credits | |
| **GetProspect** | $34-49/mo | |
| **SignalHire** | $49/mo → 100 credits | Single credit = full contact reveal (email+phone+socials together) |
| **ContactOut** | ~$49/mo (email plan) | LinkedIn-first positioning |
| **Apollo.io** | $49/user/mo (Basic, annual) — unlimited email credits under fair-use policy | Per-seat pricing; steep for solo use relative to per-lookup tools |
| **Exa.ai People Search / Websets** | $49/mo (Core) → 8,000 credits, 10 credits/resolved result | Has an MCP server — connectable to Hermes as a proper tool, not just a raw API call. Best fit for *identification* (Part A) more than bulk email-finding specifically. |
| **RocketReach** | Broad mid-tier range | Broadest raw profile coverage of the LinkedIn-centric tools |
| **Apollo Professional/Organization** | $79-119/user/mo | Adds intent data, AI writing, dialer |
| **Explorium** (Hermes-native GTM skill, beyond trial) | 8 credits per fully-enriched contact (email+phone) | The one option that's literally packaged *as a Hermes skill* rather than a generic MCP wrapper |
| **Clay.com** | $149+/mo | The waterfall-orchestration pattern worth copying (see `22-contact-enrichment/SKILL.md`'s Tier 2/3 design) — but a third paid layer on top of tools already reachable directly |
| **ZoomInfo** | Custom, typically five figures/year | Enterprise-only; not a realistic option here |

## The honest bottom line, for the "pick all the free options" ask

Stack, in order: pattern-gen+verify (Tier 1, truly $0) → theHarvester
for broader recon when needed (also $0) → rotate Hunter (50) + Snov.io
(50) + GetProspect (50) + Prospeo (75) + Skrapp (100) = **325+
free-tier lookups/month before any of them run out**, tracked per
`free-tier-rotation.md` → Apollo's free entry point as one
more rotation slot, sized to whatever your account's actual allowance
turns out to be → free verifiers (ZeroBounce/Kickbox/AbstractAPI, 100
each) for the final check. Paid tiers only enter the picture once that
combined free capacity is genuinely exhausted for a given month, or for
a specific target confident enough to be worth it.
