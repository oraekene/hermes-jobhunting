# Hosting and publishing

Setup for each supported target, and the credential boundary that shapes
all of them.

## The credential rule

**This skill runs the setup. It never holds the credential.**

Not in `target-profile.yaml`, not in a config file, not anywhere in this
package. The reasoning is specific rather than reflexive: a Cloudflare
API token scoped to Pages can create and delete projects across the whole
account, and this package's own folder is a **synced** folder on Kene's
setup (see `shared/db-concurrency.md`). A token written into a file here
is a token replicated to every machine that folder reaches, sitting in
plaintext, outliving any memory of having put it there.

Every tool below already solves this correctly, so there is nothing to
invent:

| Machine | Mechanism | Where the token lives |
|---|---|---|
| Laptop, browser available | `wrangler login` (OAuth) | `~/.config/.wrangler/` — Wrangler's own store |
| VPS / Oracle Cloud, headless | `CLOUDFLARE_API_TOKEN` env var | The shell environment, or a systemd unit file |
| Netlify | The already-connected MCP connector | Managed by the connector |
| GitHub Pages | Existing `gh` auth or SSH key | Wherever git already keeps it |

Revocation is a click in a dashboard rather than a hunt through files,
which is the practical test of whether the boundary is worth keeping.

**Kene does exactly one thing himself: the one-time login.** Everything
after that — project creation, deploy, URL, custom domain, redeploys on
refresh — this skill does.

## Default: Cloudflare Pages, free tier

Chosen as the default because the free tier is genuinely free with no
card required, bandwidth is unmetered, and **Direct Upload needs no repo
and no build step**. That last point matters more than it looks: a
role-creation or service variant is not something Kene necessarily wants
sitting in a public GitHub repo, and a hosting default that requires one
quietly forces a disclosure decision.

**Laptop, first time:**

```bash
npm install -g wrangler          # once
wrangler login                   # opens a browser, one time, token goes to ~/.config
wrangler pages project create <project-name> --production-branch main
wrangler pages deploy shared/portfolio/<variant>/ --project-name <project-name>
```

**Oracle Cloud / any headless host:** `wrangler login` needs a browser it
does not have. Create a scoped API token in the Cloudflare dashboard
instead — **Account → Cloudflare Pages → Edit**, and nothing else, since a
Pages-only token cannot touch DNS or zones — then:

```bash
export CLOUDFLARE_API_TOKEN="..."     # shell profile or systemd Environment=
export CLOUDFLARE_ACCOUNT_ID="..."
wrangler pages deploy shared/portfolio/<variant>/ --project-name <project-name>
```

Note this is the same headless-OAuth problem `security/security-setup.md`
§`mcp-oauth-remote-gateway` describes for connectors, and it has the same
shape of answer. Worth solving once, in the same sitting.

**Redeploys are the deploy command again.** Pages keeps every deployment,
so a bad publish is rolled back from the dashboard rather than repaired
under time pressure — which is a real argument for this default over a
plain file host.

**Custom domain**, only if Kene asks: `wrangler pages deployment
domain add`, then one CNAME. Not proposed unprompted — a `.pages.dev`
subdomain is fine on a CV and buying a domain is a decision with a
recurring cost attached.

## Netlify

Kene has the Netlify connector already, which makes this the
lowest-friction option when it is available — no CLI install, no token
handling at all, since the connector owns the auth.

Use the connector to create the site and deploy the variant directory.
Fall back to `netlify deploy --prod --dir=...` if the connector is not
reachable. Same rule as Cloudflare: this skill does not read or store a
Netlify token.

## GitHub Pages

Reasonable **only if the variant's content is already public anyway** —
Pages serves from a repo, so the source is exposed by construction. That
is fine for a portfolio whose whole point is public artifacts and wrong
for anything else.

```bash
gh repo create <name> --public --source=. --push
# Settings → Pages → Deploy from branch → main → / (root)
```

Slower to propagate than the other two (minutes, not seconds) and there
is no deployment history to roll back to.

## Anywhere else

The variant directory is plain static files with no build step, no
framework and no server requirement. `shared/portfolio/<variant>/` copies
to any web root and works. This skill prints the path and stops.

## Publish is a separate, asked step

Generating is free and reversible. Publishing puts a page at a URL that
anyone can find, including Kene's current employer, and that is neither.
So they are two steps and the second one asks — Rule 1's logic by
analogy, even though no application is being submitted.

**Before every publish, in order:**

1. **`09-risk-tactics-gate` over the page content.** Every claim faces
   the same verification a resume bullet does. The one place that gate
   runs on a non-application artifact, and it should: a public page is
   read by every employer at once and outlives any single application.
2. **Artifact link check** — every URL fetched, results recorded to
   `portfolio_artifacts`. Dead links are reported by URL and block the
   publish until Kene decides; they are never silently dropped, because
   a silently removed artifact means the page quietly gets weaker and
   nobody notices.
3. **Ownership check** — nothing employer-owned, NDA-covered, or
   containing third-party data. No override path on this one.
4. **Discretion check, first publish only.** If `16-career-pulse` shows
   Kene searching quietly, publishing a portfolio is a mildly visible
   act and he should hear that once before it happens. Raised, then
   dropped — not repeated at every subsequent publish.

## Unpublishing

Worth documenting because it is needed at the worst possible moment —
usually right after accepting an offer, or when something on the page
turns out to be a problem.

```bash
wrangler pages project delete <project-name>       # Cloudflare
```

The generated directory stays on disk. Taking the page down does not
destroy the work, and republishing later is one deploy command.

Search engines will hold a cached copy for a while regardless of the
host, and there is nothing this skill can do about that. Worth knowing
before publishing rather than discovering after unpublishing.
