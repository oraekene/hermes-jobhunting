---
name: job-hunting-portfolio-onepager
description: "Build and publish a one-page portfolio for a target role"
metadata:
  hermes:
    tags: [job-hunting, portfolio, outward-facing]
    category: job-hunting
    related_skills:
      - job-hunting-context-architect
      - job-hunting-resume-customizer
      - job-hunting-output-templates
      - job-hunting-cold-prospecting
      - job-hunting-risk-tactics-gate
---

# Portfolio One-Pager

## When this skill applies

Use when Kene wants a single public page representing his work — for a
link in an application, a cold-outreach signature, a social profile, or
because a role explicitly asks for a portfolio. Triggers: "I need a
portfolio page," "what do I link to when they ask for work samples,"
"build me a one-pager for the [role] search."

## The decision this skill records (A26/A27)

This sat undecided across several review passes, and it is the only
addition to this package that produces a **new user-facing deliverable**
rather than improving an existing one. That is exactly why it kept
getting deferred, and it deserves a stated answer rather than another
deferral.

**The answer is: build it, narrowly.**

The case for: everything a one-pager needs is already in the package and
already confirmed under Rule 5. The STAR bank has the stories, the
quantification gate has the numbers, `09-risk-tactics-gate` has the
claim-verification pass, `21-output-templates` has the structure system,
and `17-cold-prospecting` already wants something to link to. Not
building it means Kene assembles by hand, from a corpus this pipeline
maintains, the one artifact that is *most* reusable across applications.

The case against, and why it shapes the scope: a portfolio is a design
problem as much as a content problem, and this pipeline has no business
being a site builder. A "portfolio system" with themes, galleries,
analytics and a CMS would be a second product living inside a job-hunting
pipeline.

So the scope is deliberately narrow: **one page, generated from confirmed
memory, published as static HTML, versioned per target role.** No CMS, no
multi-page site, no theme system, no visitor analytics. If Kene wants a
real personal site, this produces a good starting file and he takes it
elsewhere — and this skill should say so plainly rather than growing
toward it.

## Portfolio versus customised CV — what each is actually for

The most common way to get this wrong is to build a portfolio that is a
prettier CV. They do different jobs, and the difference is not
presentation.

| | **Customised CV** (`05-resume-customizer`) | **Portfolio one-pager** |
|---|---|---|
| **How it reaches the reader** | Pushed. Sent to one employer for one opening. | Pulled. The reader clicks a link and arrives. |
| **What the reader already knows** | They have the JD in front of them. They know what they're matching against. | Often nothing. Could be a recruiter browsing, a hiring manager who got a cold email, someone from a conference, a person who just read a reply of his on X. |
| **Whether a role exists** | Always. | Frequently not — which is the whole basis of cold prospecting. |
| **Lifespan** | Frozen at send. A snapshot. | Live. Mutable, and permanently public. |
| **Evidence** | **Asserts.** "Cut deploy time from 40 minutes to 6." | **Shows.** Here is the repo, the running thing, the notebook, the writeup. |
| **Format constraints** | ATS parsing, one page, conventional layout, no clever formatting. | No parser. Screenshots, diagrams, longer narrative, links. |
| **Failure mode** | Missed keywords; not matching the JD. | Dead links, stale content, or leaking something that shouldn't be public. |

**The row that matters is "evidence".** Everything else is a consequence
of it. A CV can only make claims — the format has no room for proof and
the reader has no way to verify in the ninety seconds they spend on it. A
portfolio is the artifact layer: the place where "cut deploy time from 40
minutes to 6" becomes a repo with the before-and-after CI config in the
history.

That is the reason to build one at all. If a portfolio page carries no
links to real artifacts, it is a CV with worse ATS compatibility and
should not be published — `09-risk-tactics-gate`'s pre-publish pass
enforces this (see "Artifact links" below).

**When each is needed:**

- **CV, always.** Every application. Non-optional, and this skill does
  not reduce that.
- **Portfolio, when the reader arrives without context.** Cold outreach
  (`17-cold-prospecting`), a link in a social bio, a role that explicitly
  asks for work samples, a referral where someone is passing his name on,
  or any conversation where "what have you built" comes before "here's
  the job spec."
- **Both, linked.** The CV carries the portfolio URL; the portfolio does
  not reproduce the CV. Redundancy between them is wasted space on the
  page and a second thing to keep in sync.

**The current-employer consideration.** A CV goes to one recipient. A
portfolio is findable by anyone, including a current employer, and
publishing one is a mildly visible act. `16-career-pulse`'s
discretion-mode handling applies: if Kene is searching quietly, that is a
real input to whether this gets published at all, and the skill raises it
once at first publish rather than assuming either way.

## Artifact links — the primary content, not a footer

A portfolio without links is a CV. Links are what it is *for*, so they
get first-class treatment rather than a "selected work" list at the
bottom.

**Each work item can carry one or more artifacts:**

| Type | Notes |
|---|---|
| `deployed` | The running thing. Highest-value link there is — a reader can use it in ten seconds. |
| `repo` | GitHub/GitLab. Link to the **repo root** unless a specific file is the point; a deep link into one file reads as cherry-picking. |
| `notebook` | Colab, Jupyter, Kaggle. See the readability note below. |
| `writeup` | A blog post, a design doc, a postmortem. Often the strongest artifact for work whose code isn't shareable. |
| `demo` | A screen recording where the thing can't be deployed publicly. Two minutes, no narration required. |
| `package` | npm, PyPI, crates.io — a published, installable thing. |
| `paper` | arXiv or a published venue. |

**Notebooks need a readability check that repos don't.** An `.ipynb`
with cleared outputs is a wall of code that proves nothing to someone
skimming. Link the rendered form — a Colab link that runs, or nbviewer /
GitHub's own render with **outputs committed** — and make sure the top
cell says what the notebook is for. A notebook whose first visible thing
is `import pandas as pd` is a link the reader closes.

**A repo needs a README that survives thirty seconds.** If the repo's
README doesn't say what the thing is and why it exists, linking it is
worse than not linking it. This skill flags that; it does not fix it,
because fixing it is real work Kene has to do.

**Link rot is checked, because the failure is silent and total.** A
portfolio with dead links is worse than one with no links: it looks
careless in exactly the dimension the page exists to demonstrate. Every
artifact URL is checked at publish and re-checked on the quarterly
refresh (`shared/applications_db_schema_addendum_18.sql`,
`portfolio_artifacts`). A 404, a repo gone private, or a Colab that
now requires permission are all reported by URL — never silently dropped
from the page, because a silently removed artifact means the page quietly
gets weaker and nobody notices.

**What is safe to link — the hard boundary.** Only artifacts Kene owns or
that are already public with permission. Employer-owned code, internal
documents, anything under NDA, and anything containing a third party's
data do not go on a public page. This is checked at add time and again at
publish, and it is the one check in this skill that does not have a
"Kene can override" path — the failure mode is publishing something he
didn't own, and that ends careers rather than jobs.

Where the underlying work can't be shown, the `writeup` and `demo` types
exist precisely for that: describing a system he built, at a level of
abstraction that gives away nothing, is legitimate and often more
readable than the code would have been.

Six blocks, in order. Every one is drawn from existing confirmed memory;
this skill originates no facts (Rule 5).

1. **Positioning line** — one sentence, what he does and for whom.
   Derived from `target-profile.yaml`'s current target title and
   `content-model-overlap.md`'s framing, confirmed by Kene before it
   ships. This is the hardest line on the page and the one worth the most
   iteration.
2. **Three to five work items** — from the STAR bank, selected for the
   target role the same way `05-resume-customizer` selects. Each is
   situation → what he did → the number. **Every number carries the same
   quantification bar as a resume bullet.** A portfolio is not a lower-
   evidence surface because it is self-published; if anything a claim
   sitting permanently on a public page deserves more care than one in a
   document sent once.
3. **Capability summary** — grouped skills with the evidence attached,
   from `domain-knowledge.md`. Grouped, not a wall of tags.
4. **Artifact links per work item** — attached to item 2, not listed
   separately at the bottom. A link sitting next to the claim it evidences
   is doing work; the same link in a "selected work" appendix is a list
   the reader skips. See "Artifact links" above.
5. **Contact** — whatever Kene has already chosen to make public.
   Defaults to nothing until he says otherwise.
6. **Last updated** — a real date. A portfolio with a stale date reads
   worse than one with no date, which is an argument for the refresh
   prompt below rather than against showing it.

## Variants — two axes, not one

The first version of this skill said "one variant per target-title
cluster." That is right for applications and wrong for cold outreach,
which is a different situation with a different reader.

**Axis 1 — target-title cluster (application-facing).** Same underlying
material, different selection and ordering per role family. The same
principle as a tailored resume. `19-career-path-planner`'s current hop is
the default on a multi-hop plan: the page should present him for the role
he is applying to now, not the one two moves away.

**Axis 2 — pitch mode (outreach-facing).** `17-cold-prospecting` has
three modes and they need genuinely different pages, because the reader's
question differs:

| Pitch mode | Reader's question | What the page leads with |
|---|---|---|
| **Role-fit** | "Could he do the job we already have?" | Same shape as the application variant. Often the *same* variant. |
| **Role-creation** | "Is this function worth creating here?" | The problem the function solves, evidenced by work where he solved it. The role is the argument, not the CV. |
| **Service** | "Would I hire this person for a defined piece of work?" | Scope, deliverable, and comparable past work. Closest to a consultancy page — and the one a role-shaped portfolio actively misreads. |

**Role-fit outreach usually needs no separate variant** — it reuses the
matching target-title one. Only role-creation and service pitches
generally justify their own, and only if Kene pitches that way often
enough to be worth maintaining.

**Per-outreach relevance without per-outreach variants.** Rather than a
page per prospect, the published page carries a stable anchor per work
item (`#credit-scoring-pipeline`), and `17-cold-prospecting` deep-links
to the relevant one. One variant serves many outreaches, each landing the
reader on the item that motivated the email. This is the real reason not
to proliferate variants: the tailoring that matters is *which item they
see first*, and an anchor does that for free.

**Cap it.** Four or five variants across both axes is a lot. Each is a
page that can go stale independently, and a portfolio's worst failure is
being out of date. If a sixth is requested, the better question is
usually whether two existing ones have converged.

Variants live in `shared/portfolio/{variant_slug}/`, each recording what
it was built for, what it selected, and when.

## Choosing what goes on the page — Kene picks

This skill proposes and he adjusts. Same propose-confirm-save shape as
everything else here, not a page he discovers after the fact.

**`shared/portfolio-manifest.yaml`** holds three things:

1. **The eligible pool** — every STAR entry, capability and artifact
   already confirmed in memory, each with a one-line summary and an id.
   Built by scanning; Kene never types it. This is the menu, and it is
   the answer to "what *could* go on a page."
2. **Global rules** — `always_include` for the one or two flagship items
   that belong on every variant regardless of target, and
   `never_include` for anything he doesn't want public at all. `never`
   wins over everything including a per-variant selection, and it is the
   right home for work that is technically shareable but that he'd rather
   not lead with.
3. **Per-variant selection** — an ordered list of ids. **Order is
   meaningful** and the page renders it as given, because on a one-pager
   the first item is most of the impression.

**How the conversation goes.** On a new variant, this skill proposes a
selection from the pool with a reason per item, ranked for that target.
Kene adds, drops and reorders in plain language — "drop the second one,
move the payments work to the top, add the thing I did for the co-op."
Confirmed once, written to the manifest.

**A rebuild never silently re-selects.** The existing selection is the
starting point every time. A page Kene curated should not quietly
rearrange itself because a new STAR entry landed.

**New material is offered, never inserted.** When something enters the
bank that would rank highly for an existing variant, the quarterly
refresh raises it once — "this would be a strong fit for the fintech
variant, add it?" A question, not a diff applied on his behalf.

## Publishing

Static HTML, one file plus assets, no build step and no framework. The
output is readable and editable by hand, because Kene will want to edit
it by hand and a generated file he cannot touch is worse than no file.

### Where hosting is asked, and what happens if he doesn't care

**At first publish, once.** Not at generate — generating is free and
reversible, and asking about hosting before there is a page to host is a
question with no context. Never again after that: the choice is recorded
per variant and reused.

The question is a real one with a default attached, not an open-ended
"where would you like to host this":

> Ready to publish. I can set this up on **Cloudflare Pages free tier**,
> which is the default — no cost, no card, custom domain if you want one
> later. Or: Netlify (you have the connector), GitHub Pages (if the repo
> is already public), or I can hand you the folder for anywhere else.

**Default: Cloudflare Pages, free tier.** Chosen because the free tier is
genuinely free with no card, bandwidth is unmetered, and Direct Upload
means no build step and no repo requirement — which matters, since not
every variant belongs in a public repo.

`references/hosting-and-publish.md` carries the setup for each, including
the headless path for the Oracle Cloud instance where there is no browser
to complete a login in.

**One boundary I am keeping, and it is worth explaining rather than just
asserting.** This skill will run the whole setup for him — install the
CLI, create the project, deploy, report the URL, wire the custom domain —
but it **never stores his credentials itself.** Not in
`target-profile.yaml`, not in a config file, not anywhere in this
package.

That is not caution for its own sake. A Cloudflare API token scoped to
Pages can create and delete projects across the account; a Netlify token
similarly. Putting one in a file inside a folder that syncs between
machines — which is exactly this package's situation, per
`shared/db-concurrency.md` — is how a credential ends up somewhere nobody
intended. The tools already solve this properly: `wrangler login` puts an
OAuth token in Wrangler's own config under `~/.config/`, and the headless
path uses `CLOUDFLARE_API_TOKEN` from the environment. Either way the
credential lives where that tool manages it, this skill reads nothing,
and revoking access is one click in a dashboard rather than a hunt
through files.

So: **he can hand off the whole setup and never think about it again.**
The only thing he does himself is the one-time login, in whichever form
suits the machine.

**Nothing is published without an explicit confirmation.** Rule 1's logic
applies by analogy even though this is not an application submission:
generating the file is free and reversible, putting it at a public URL is
neither. The generate step and the publish step are separate, and the
publish step asks.

**Run `09-risk-tactics-gate` over the page before publishing.** Every
claim on it faces the same verification a resume bullet faces. This is
the one place where the gate runs on an artifact that is not an
application, and it should: a public page is read by every employer at
once and outlives any single application.

## Refresh

A portfolio decays quietly. The page does not change, the work does, and
the gap only becomes visible at the worst moment.

`16-career-pulse`'s quarterly check-in asks once whether anything on the
page has changed — new work worth adding, a number now outdated, a
capability no longer current. Batched into that conversation, not a
standalone chore. If `19-career-path-planner` records a hop as `matured`,
that is also a refresh trigger, because the positioning line is probably
now wrong.

## What this skill does not do

- **It does not originate facts.** Rule 5 holds. Every claim comes from
  confirmed memory; if something belongs on the page that isn't in the
  bank, that routes to `07-context-architect` first.
- **It does not host anything, or hold credentials.** It writes files and
  prints deploy commands. No provider API, no tokens, no account.
- **It does not publish work product.** Links to already-public artifacts
  only. Employer-owned code, internal documents, and anything under NDA
  do not go on a public page, and this skill will not help route around
  that — the failure mode is a candidate who publishes something they
  did not own, and it ends careers rather than jobs.
- **It does not become a website.** One page. If the answer to a request
  is "add a blog", "add a projects section with sub-pages", or "add a
  theme picker", the answer is that Kene should take the generated file
  to a real site builder.
- **It does not track visitors.** No analytics, no pixels, no
  link-shortener telemetry. Knowing that someone looked would be mildly
  interesting and is not worth putting a tracker on a page that exists to
  represent him.

## Reference

- `references/hosting-and-publish.md` — Cloudflare Pages (the default),
  Netlify, GitHub Pages, the headless path for the Oracle Cloud
  instance, the credential boundary, the pre-publish checklist, and
  unpublishing.
- `references/page-design.md` — the template's design tokens and the two
  rules to preserve when editing the HTML by hand.
- `assets/portfolio-template.html` — the page itself. Plain HTML, no
  build step, no JS, editable by hand.
- `shared/portfolio-manifest.yaml` — the eligible pool, the global
  include/exclude rules, and Kene's ordered selection per variant.
- `shared/applications_db_schema_addendum_18.sql` — artifact registry,
  link-health checks, publish history.
- `07-context-architect` — the STAR bank, `domain-knowledge.md`, and the
  quantification gate every number here passes.
- `05-resume-customizer` — the selection logic reused for ranking work
  items per variant, and the artifact this page deliberately does not
  duplicate.
- `17-cold-prospecting` — the main consumer of the published URL, via
  per-item deep links.
- `21-output-templates` — `input_method` and `application_mode` apply
  here as to any outward artifact.
- `09-risk-tactics-gate` — the pre-publish verification pass.
