---
name: job-hunting-contact-enrichment
description: "Find a specific person's verified contact details"
metadata:
  hermes:
    tags: [job-hunting, contact-enrichment]
    category: job-hunting
    related_skills:
      - job-hunting-social-discovery-outreach
      - job-hunting-cold-prospecting
---

# Contact Enrichment

## When this skill applies

Use this skill whenever 14-social-discovery-outreach or 17-cold-prospecting needs a specific person's contact details — a company/role is known, a name and email are not. Two jobs: (1) identify WHO the hiring manager and decision maker actually are, given only a company name and role; (2) enrich that person (and, as a secondary/parallel target, the recruiter/TA contact) with a verified email. Hiring manager and decision maker are the PRIMARY targets throughout — recruiter-track contacts are legitimate and handled, but never take priority over them. Runs a free-first cascade (public sources → self-hosted tools → free API tiers, rotated across providers → paid, budget-capped) rather than defaulting to a single paid tool. Also use this skill when Kene wants to connect his own paid provider API keys (Hunter, Apollo, etc.) — see references/api-key-setup.md. Every identification is a confidence-scored hypothesis, never an assertion — see the target-claim gate this skill inherits from 17-cold-prospecting.

Origin: a direct correction worth restating here, not just in the
conversation that produced it — an earlier example jumped straight from
"company name" to "here's the email," skipping the actually harder step
of figuring out *who* to even look for. This skill is that missing
step, plus the enrichment (email-finding) step that follows it, built
as one skill because they're genuinely sequential and share the same
confidence-and-evidence discipline throughout.

## Definitions, settled once, used everywhere below

- **Hiring manager** — the role's future direct manager: defines
  requirements, runs the job-specific interview, usually holds or
  heavily influences the final call.
- **Decision maker** — broader, always includes the hiring manager.
  Also includes the hiring manager's own manager (senior roles
  especially), and at small companies, the founder(s) directly, who
  are very often *both* roles at once.
- **Recruiter-track — a different, still-legitimate category, never
  the primary target**: titles containing "Recruiter," "Talent
  Acquisition," "People Ops," "HR." Sources and screens; rarely decides.
  Worth remembering practically: a recruiter is often the *more
  expected* first inbound contact, and reaching them isn't a fallback
  or a lesser move — it's just a different one, aimed at a different
  purpose than reaching the actual decision maker.
- **By company stage**, since this changes who to even look for:
  under ~20 people, default to founder/CEO as both hiring manager and
  decision maker. Growth-stage, a department head with a recruiter
  coordinating. Larger orgs formalize into recruiter → hiring manager →
  sometimes a committee or the manager's own manager.

**Throughout this skill and everywhere it feeds — `14-social-
discovery-outreach`, `17-cold-prospecting` — hiring manager and
decision maker are the primary target. Recruiter-track contacts are
identified and handled too, in parallel, never dropped — just never
ahead of the primary target in priority, framing, or outreach
sequencing.**

## Hermes-native tools this skill actually uses — confirmed via a full crawl of the official catalogs

Both the bundled and optional skills catalogs
(`hermes-agent.nousresearch.com/docs/reference/skills-catalog` and
`.../optional-skills-catalog`) were fetched directly for this pass, not
inferred from search snippets. Headline finding: **there is no bundled
or official enrichment/CRM/email-finder skill at all** — confirming
this skill's whole free-first, mostly-self-built design was the right
call, not a workaround for a missing feature. What the catalogs *do*
offer, relevant here:

- **`domain-intel`** (optional, `research/domain-intel`) — passive DNS/
  WHOIS/subdomain reconnaissance, no API key required. This is Part B
  Tier 1's actual MX-check tool, not a hand-rolled equivalent.
- **`research/parallel-cli`** (optional) — the one option confirmed as
  genuinely Hermes-official that does real enrichment (`enrich run`,
  natural-language intent, free tier). Added to Tier 2's rotation.
- **`security/1password`** (optional) — the credential mechanism behind
  `references/api-key-setup.md`, answering the "can users connect their
  own paid API keys" question directly.
- **`osint-investigation`** (optional) — public-records research (SEC
  EDGAR, OpenCorporates, and similar). More relevant to `12-company-
  research`/`17-cold-prospecting`'s target research than to this
  skill's Part B specifically, worth knowing about regardless.
- **`sherlock`** (optional, security category) — username search across
  400+ networks. Useful corroboration for Part A identification (cross-
  checking a name across platforms), not an email finder itself.
- **`scrapling`** (optional) — stealth browser automation, explicitly
  including Cloudflare bypass. **Available, and deliberately not used
  for LinkedIn or similar ToS-restricted targets** — this is exactly
  the class of tool Rule 6 exists to keep this pipeline away from,
  regardless of what it's technically capable of.
- **`duckduckgo-search`/`searxng-search`** (optional) — free, no-API-key
  web search, usable as additional Tier 0 search capacity alongside
  whatever web search is already configured.

## Part A — Identifying the person (given only a company name)

Given only "Company X is hiring for [role]," no name yet:

1. **Check the posting itself first** — free, often skipped. It
   sometimes names the manager directly or states the reporting line
   ("reports to the VP of Product"). `02-jd-parser`'s output already
   has this text; this skill reads it before doing anything else.
2. **LinkedIn people search, filtered by title** matching what the JD
   implies the role reports to. Driven through Kene's own already-
   authenticated session via `computer-use` — see `shared/site-access-
   model.md` for why that's the model here rather than Hermes
   independently holding LinkedIn credentials, and for the same
   occasional/light-touch posture `platform-capability-matrix.md`
   already requires.
3. **Exa.ai people search** — a semantic query like "Head of Product at
   [Company]" returns structured person results without touching
   LinkedIn's UI directly. The better default tool for this specific
   step; see `references/enrichment-tools-pricing.md` for cost.
4. **Company's own Team/Leadership page, Crunchbase** (startups
   especially — often lists the founding/leadership team directly),
   recent press ("Company X hires [Name] as VP Engineering").
5. **`12-company-research`'s cache**, including its sentiment addition
   — Glassdoor/Reddit reviews sometimes name specific managers directly.
6. **Match candidates against the JD's stated reporting line**, and
   **classify each candidate explicitly as hiring-manager-track,
   decision-maker-track, or recruiter-track** — never left ambiguous.
   A generic "Recruiter" or "Talent Acquisition" title is correctly
   filed as recruiter-track, not mistaken for the primary target because
   it was the easiest name to find.
7. **Confidence, not certainty** — every identification carries a
   confidence level and its evidence trail, same "hypothesis, not
   assertion" discipline `17-cold-prospecting`'s target-claim gate
   already established (Rule 8). Cross-reference across 2+ independent
   signals before calling an identification confident rather than
   best-guess — a title match alone isn't enough. Check the person is
   still actually at the company (LinkedIn goes stale) before treating
   an old identification as current.

## Part B — Enriching the identified person (name → verified email)

**Honest status check, since it was asked directly: this was not fully
built before this pass.** The architecture (four tiers, free-first,
verify-before-send) was right; several pieces inside it were named but
never actually specified — no concrete pattern table, no defined
escalation threshold between tiers, no budget cap for Tier 3, no named
default verifier. All fixed below; nothing here is still "described but
not implemented."

### Tier 0 — free public sources
Company site, GitHub (if technical — commit metadata/bio very often
carries a real email), linked personal blog/portfolio, press,
conference bios. Zero cost, zero risk.

### Tier 1 — free, self-hosted, no vendor account needed

**The pattern table** (candidate generation, ranked by real-world
format frequency — this is the table that was previously only promised,
not written):

| Rank | Pattern | Approx. frequency |
|---|---|---|
| 1 | `first.last@domain` | ~38% |
| 2 | `first@domain` | ~17% |
| 3 | `flast@domain` | ~12% |
| 4 | `firstlast@domain` | ~10% |
| 5 | `first_last@domain` | ~6% |
| 6 | `f.last@domain` | ~5% |
| 7 | `firstl@domain` | ~4% |
| 8 | `last.first@domain` / `lastfirst@domain` | ~3% combined |
| — | remainder (initials-only, nickname-based, etc.) | long tail |

**The full step sequence**, in order, each step gating the next:

1. Generate candidates from the table above for the confirmed name +
   confirmed company domain, highest-frequency first.
2. **MX record check** on the domain — confirms it receives mail at
   all before spending a single verification attempt. Use the
   Hermes-native `domain-intel` optional skill for this specifically
   (`hermes skills install official/research/domain-intel`) — passive
   DNS/WHOIS/subdomain reconnaissance via Python stdlib, **no API key
   required**, confirmed in the official optional-skills catalog. Don't
   hand-roll a second DNS lookup when this already exists as an
   installable skill.
3. **Catch-all probe**: attempt an SMTP handshake against a
   deliberately fake, high-entropy local part at the same domain (e.g.
   a random 12-character string that could not plausibly be a real
   person's address). If the server accepts it too, the domain is
   catch-all — SMTP alone can no longer distinguish a real address from
   a guess, and every candidate below drops one full confidence tier
   regardless of its SMTP result.
4. **SMTP handshake verification** (`RCPT TO`, connection closed before
   `DATA` — no message ever actually sent) on the ranked candidates,
   stopping at the first one that returns accepted, unless the domain
   was flagged catch-all in step 3, in which case none of them can be
   called "verified" from this tier alone — proceed to Tier 2 for a
   second opinion rather than acting on an SMTP-only result for a
   catch-all domain.

Also available at this tier: `theHarvester` (open source, 40+ public
sources including PGP keyservers, self-hosted) for broader domain
reconnaissance when a specific name isn't the bottleneck yet.

This whole tier is deterministic, mechanical work — `execute_code`, not
a reasoning turn, per this package's own capability-audit rule of
thumb.

### Escalation thresholds — when Tier 1 hands off to Tier 2

Not left implicit: escalate past Tier 1 when **any** of the following
hold — (a) the domain came back catch-all in step 3 and no independent
corroboration exists, (b) zero candidates returned an SMTP-accepted
result, (c) the identified contact is `contact_priority:
hiring_manager` or `decision_maker` specifically (worth the extra
lookup for the primary target even on a technically-passing Tier 1
result) — recruiter-track contacts with a clean Tier 1 pass do not
automatically escalate, keeping Tier 2 usage weighted toward the
contacts that actually matter most.

### Tier 2 — free tiers of commercial APIs, rotated across providers
Several vendors offer genuinely-free, genuinely-recurring (not one-time
trial) monthly allowances — Hunter, Snov.io, GetProspect, Prospeo,
Skrapp among them. **Don't pick one and exhaust it — rotate across all
of them**, tracked in `shared/enrichment-tier-usage.yaml` (see
`references/free-tier-rotation.md`), to combine several small free
allowances into meaningfully more free monthly capacity than any single
vendor offers alone. The Hermes-official `research/parallel-cli`
optional skill is also usable here — its `enrich run` command accepts a
natural-language intent ("find this person's work email") against a
structured dataset, priced per row rather than per field, with its own
free tier; treat it as one more rotation candidate, not a replacement
for the dedicated finders.

### Tier 3 — paid, budget-capped, last resort

**Budget cap, concretely, not just "capped" as a word**: a monthly
spend ceiling in `shared/enrichment-tier-usage.yaml`
(`tier3_monthly_budget_usd`, default `$0` — Tier 3 is opt-in, not
assumed), decremented as actual paid lookups happen, refusing further
Tier 3 spend once exhausted for the cycle regardless of how promising a
target is, and requiring Kene's confirmation to raise it rather than
auto-increasing. Only reached when Tier 0-2 come back empty or
low-confidence, and only for a target already classified
`hiring_manager`/`decision_maker` — Tier 3 is never spent on a
recruiter-track contact by default.

### Verification, regardless of which tier found the candidate

**Named default, not left open-ended**: ZeroBounce's free tier (100/mo)
is the default verifier for any candidate that didn't already clear
Tier 1's own SMTP check on a non-catch-all domain. A candidate that
fails this final check is never handed to `14`/`17` for a real send —
it goes back into the cascade at the next tier instead of being used
on a best-effort basis.

## Logging spend (D9)

Every provider lookup writes a row to `enrichment_spend`
(`shared/applications_db_schema_addendum_10.sql`) — provider, tier,
credits, estimated cost, whether it succeeded, and the application it was
for.

Three things about that shape are deliberate:

- **Log failures too.** A failed paid lookup still burns a credit at most
  providers. Counting only successes understates real spend, which is the
  direction that flatters the tool.
- **`application_id` is nullable.** Cold prospecting enriches a contact
  before any application exists. Those lookups cost the same money and
  must still be counted.
- **This does not replace `enrichment-tier-usage.yaml`.** That file is a
  rate-limit counter with a billing-cycle reset; this table is an audit
  trail that never resets. Different jobs, and collapsing them would lose
  one of them.

`v_cost_per_application` and `v_cost_per_outcome` are the payoff:
`11-analytics-and-learning` can finally answer what a submitted
application costs and what an interview request costs. Until now the
pricing doc knew provider rates, the tier-usage file knew credit counts,
and the applications table knew outcomes — with nothing joining them, so
the only question that decides whether Tier 3 is worth paying for could
not be asked.

## Where this plugs in

- **`14-social-discovery-outreach`** and **`17-cold-prospecting`** call
  this skill whenever `contact.handle_or_address` (email specifically)
  is missing but a company/role is known. The returned contact record
  populates `contact.role_guess`/`contact.relationship` with the
  hiring-manager/decision-maker/recruiter-track classification from
  Part A directly — both skills' existing drafting logic already reads
  those fields, nothing new to wire there beyond this skill supplying
  better values.
- **Outreach sequencing**: when both a hiring-manager/decision-maker
  contact and a recruiter-track contact are identified for the same
  opportunity, the primary draft targets the former; the latter is
  staged as its own separate, differently-framed outreach, not skipped
  and not merged into one message.
- **Subagent delegation** applies the same way it does everywhere else
  research-shaped in this package — Part A's multi-source lookup and
  Part B's multi-tier cascade both parallelize naturally.

## Reference files

- `references/enrichment-tools-pricing.md` — every tool researched,
  ranked lowest cost (free) to highest, plus the full token-use/
  bot-risk/rate-limit comparison.
- `references/free-tier-rotation.md` — how multiple free tiers get
  combined and tracked instead of picked one-and-exhausted.
- `references/api-key-setup.md` — how Kene connects his own paid
  provider API keys, via the official `security/1password` skill.
- `references/linkedin-methods.md` — every real way to get an email off
  LinkedIn specifically, and which ones this pipeline actually uses.
- `shared/applications_db_schema_addendum_5.sql` — the
  `contact_priority`/`identification_confidence` columns this skill's
  Part A output populates on `social_outreach`.
