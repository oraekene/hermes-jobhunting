# Getting Emails Off LinkedIn — every real way, and which ones this pipeline actually uses

Direct answer: yes, sometimes directly, more often indirectly.
LinkedIn itself deliberately doesn't surface emails through its own
paid products (Sales Navigator included) — that's not an oversight,
it's LinkedIn protecting its own data moat. Everything below works
around that, with genuinely different risk profiles.

## 1. The profile's own Contact Info section — direct, zero risk

Many users voluntarily list an email in their profile's "Contact info"
panel, visible when viewing their profile (visibility depends on their
own privacy settings — sometimes public, sometimes connections-only).
This is the person choosing to disclose it. Check this first, every
time — it's the highest-confidence, zero-cost source when it's there.

## 2. A post or comment where they share it themselves — direct, zero risk

A hiring post that says "email me at jane@company.com" or a comment
with a contact address. Already covered by `14-social-discovery-
outreach`'s CTA classification (`email_instructions`) when it's
attached to a discovered post; the same applies to a profile bio's
"About" text if someone put an email there directly.

## 3. Third-party finder tools, in **API/database lookup mode** — indirect, low risk

RocketReach, ContactOut, SignalHire, Lusha, and similar maintain their
own pre-built databases (historical scraping + data partnerships,
compiled by the vendor over time) cross-referenced against a LinkedIn
profile URL. Query their API with a profile URL, get back whatever
they've already indexed. **The vendor absorbs the data-collection risk
here, not Kene's account** — this is the mode `22-contact-enrichment`'s
Tier 2 actually uses when one of these providers is in rotation.

## 4. Third-party tools, in **browser-extension mode** — real risk, not used here

The same vendors above often also ship a Chrome extension that runs
*inside Kene's own logged-in LinkedIn session*, reading whatever
profile is currently open and querying the vendor's database live.
This reintroduces exactly the account-risk `platform-capability-
matrix.md` already flags for LinkedIn automation generally — running
inside an authenticated session at any real frequency risks the account
this whole pipeline depends on for legitimate reading elsewhere. **Not
used by this pipeline, on principle (Rule 6), regardless of how
convenient it would be.**

## 5. Pattern generation, once LinkedIn confirms the *name* and *current company* — indirect, zero risk

The actual most common realistic path, worth stating plainly: LinkedIn
is rarely where the email itself comes from. It's where Part A confirms
*who* someone is and where they currently work — the email then comes
from Part B's own cascade (pattern-gen+verify first, paid finders as
fallback), which has nothing to do with LinkedIn once the name and
domain are known. This is the default path `22-contact-enrichment`
already uses; LinkedIn is an identification source feeding into it, not
a separate email-finding channel of its own.

## 6. What doesn't work anymore

LinkedIn had a public API broad enough for this kind of lookup roughly
a decade ago; it's been locked down since. Anything claiming to pull
bulk contact data via LinkedIn's own official API today is either
describing the narrow, permissioned partner APIs (not available for
this use case) or is quietly doing browser automation/scraping under
the hood — worth being skeptical of a tool's own marketing language
("LinkedIn API integration") without checking which of the two it
actually means.

## Where this plugs in

`22-contact-enrichment/SKILL.md`'s Part A already lists LinkedIn people
search as one of its identification sources — this file is the detail
behind that one line, and the reason Part A and Part B stay genuinely
separate steps rather than one skill trying to get everything from
LinkedIn directly.
