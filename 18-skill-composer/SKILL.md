---
name: job-hunting-skill-composer
description: "Add or modify a skill in this job-hunting pipeline"
metadata:
  hermes:
    tags: [job-hunting, skill-composer]
    category: job-hunting
    related_skills:
      - job-hunting-orchestrator
      - job-hunting-onboarding
---

# Skill Composer

## When this skill applies

Use this skill when Kene describes a new workflow he wants this pipeline to handle, or points at a source (a directory, a URL, a walked-through session) and wants it turned into a working addition to the job-hunting skill package — 'turn this into a skill,' 'I want the pipeline to also do X,' or anything where the natural next step is authoring or modifying a SKILL.md. Wraps Hermes's native /learn command rather than reimplementing skill authoring — this skill's own job is entirely about making /learn's output conform to this package's house style and its safety rules, not about generating text from a workflow description, which /learn already does well on its own. Triggers before any file gets written: determine whether the request fits an existing skill's remit (extend via an ADDENDUM.md, this package's established pattern) or genuinely needs a new numbered skill. Never uses /learn's default full-rewrite behavior on an existing hand-tuned SKILL.md — see 'The overwrite risk' below.

Origin: Kene's request to generalize `/learn` — Hermes's own June 2026
feature for turning a described workflow or pointed-at source into a
SKILL.md — so that any new capability added to *this* package comes out
matching its existing conventions well enough to "integrate and work
seamlessly," rather than landing as generic Hermes-style output that
happens to sit in the same folder.

## What `/learn` already does, and what this skill adds on top

`/learn` (source material → local directory, URL, or a live session it
watched) already handles the actual authoring — it reads source
material with tools it already has and writes a working SKILL.md with
zero hand-writing required. This skill does not re-implement that. What
it adds is entirely **job-hunting-package-specific steering**, applied
before and after the underlying `/learn` call:

1. **Modify-or-create decision, before anything gets drafted.**
2. **House-style conformance** the generic `/learn` output has no reason
   to know about on its own.
3. **A safety check against this package's own rules** — specifically
   whether the new capability touches Rule 1 (the approval boundary) or
   Rule 5 (confirm-before-write), which is the one thing every skill in
   this package has to get right regardless of what it does.
4. **A non-destructive default** — see "The overwrite risk" below,
   which is the actual reason this steering layer exists rather than
   just running `/learn` directly against this package's skill folders.

## Step 1 — Modify or create?

Before invoking `/learn` at all, check the described workflow against
every existing `SKILL.md` frontmatter `description` in this package (the
same triggers-list format every skill here already uses makes this a
direct comparison, not a fuzzy guess):

- **Fits an existing skill's stated remit** → this is a modification.
  Draft it as `{skill-folder}/ADDENDUM.md` first — **never** point
  `/learn` at the base `SKILL.md`, which is the whole point of this
  step (see "The overwrite risk" below).

  **Then fold it in and archive the draft.** There are no live
  `ADDENDUM.md` files in this package any more; every one has been
  written into its host `SKILL.md` *at the point it applies* — not
  appended as a trailing section — with the verbatim draft preserved
  under `.merge-history/addenda*/`. Read a folded example there for the
  shape rather than looking for a live one. A stray `ADDENDUM.md` left
  in a skill folder is a second document a reader has to know to open,
  and nothing makes them open it.

  Both halves matter and for different reasons: drafting separately
  protects a hand-tuned file from a full rewrite; folding afterwards is
  what stops the skill's behaviour living in two files.
- **Doesn't fit anything existing** → this is a new skill. Assign it
  the next unused number in sequence (check every existing `NN-*`
  folder on disk first — currently 00-24, plus the unnumbered
  `onboarding/`. Do not count from any list written down elsewhere,
  including this sentence; `dry-run.py` counts the folders and the
  folders are the answer. Two skills sharing a number is a real failure
  mode here — `23` collided once already, between `portfolio-onepager`
  and `linkedin-profile-optimizer`, and was resolved by renumbering the
  latter to `24`.)
- **Genuinely ambiguous** → ask Kene directly rather than guessing. A
  wrong "modify" decision means a bloated addendum that doesn't belong
  where it landed; a wrong "create" decision means a near-duplicate
  skill competing with an existing one for the same trigger phrases.
  Getting this wrong is more expensive to unwind later than one
  clarifying question now.

## Step 2 — Draft with `/learn`, scoped correctly

- **New skill**: `/learn` the described workflow or pointed-at source
  normally — but before accepting its output, hand it (or check its
  output against) this package's house-style shape:

  ```yaml
  ---
  name: job-hunting-<short-name>          # unique across the package
  description: "<= 60 characters"         # SEE BELOW -- this is a hard cap
  metadata:
    hermes:
      tags: [job-hunting, <topic>]
      category: job-hunting
      related_skills:                     # every entry must be a real `name:`
        - job-hunting-<other>
  ---
  ```

  **The 60-character cap is not a style preference.** The skill index
  truncates descriptions at 57 characters. Go over it and the part
  saying when the skill fires is silently cut off, so the skill stops
  being selected — it is still on disk, it just never triggers, and
  nothing reports it. Eleven skills were in that state before the
  merge. `dry-run.py` enforces the cap; do not work around it.

  **Triggers do not go in the description any more.** They go in a
  `## When this skill applies` section as the first body section —
  which is where the space to name what fires the skill *and what
  explicitly doesn't* actually exists.

  **`metadata.hermes` is required.** Without it the skill is an
  isolated node in the journey graph. `related_skills` forms an edge
  only where both endpoints resolve to a real `name:`; a typo produces
  no edge and no error, so `dry-run.py` checks these too.

  Then, in the body: an `Origin` section, a numbered/phased `Process`
  section, a `Where this plugs into existing rules` section citing
  specific rule numbers from `shared/pipeline-rules.md` and
  `shared/pipeline-rules-addendum.md` (Rules 0-16), and a `Reference
  files` section listing anything split out rather than inlined. `/learn`'s
  own output won't know this shape exists unless it's told — supply it
  as explicit style guidance in the `/learn` invocation, not left
  implicit.
- **Modification (ADDENDUM.md)**: don't run `/learn` against the whole
  target skill folder — scope it to just the new behavior being added,
  then hand-fit the result into the `ADDENDUM.md` shape (a short "why
  this file exists" framing, then the specific extension) rather than
  letting `/learn` decide the file's structure from scratch.

## Step 3 — The safety check every draft goes through

Regardless of modify-or-create, before anything is proposed to Kene for
approval:

- **Does this touch Rule 1** (nothing sends/submits without Kene's
  explicit per-item approval)? If the new capability sends, posts, or
  submits anything anywhere, it must route through the same approval
  discipline `10-approval-and-submit`/`capability:social_listening`
  already use — never invent a second, lighter-weight approval pattern.
- **Does this touch Rule 5** (only `07-context-architect` writes
  confirmed facts to memory)? If the new capability could plausibly
  learn something durable about Kene, it surfaces a proposal to
  `07-context-architect`, the same way `16-career-pulse` does — it does
  not write to `MEMORY.md`/`USER.md`/`target-profile.yaml` itself.
- **Does this need a DB or config change?** Draft whichever apply,
  following the exact conventions the existing ones use — don't invent
  a new config-file convention for something that fits an existing one.

  - **New table** → `shared/applications_db_schema_addendum_N.sql`,
    additive only, `N` = one past the highest on disk. It must end with
    its own `INSERT OR IGNORE INTO schema_version` row (addendum 7's
    rule: a migration that does not record itself is one that will be
    run twice), **and** be added to README install step 4 and to
    `install-check.py`'s `SCHEMA_FILES` range plus a `SENTINEL_TABLES`
    entry. Three places. `dry-run.py` fails if any is missed — that is
    not belt-and-braces, it is because two of those lists had already
    gone stale by four and five migrations respectively.
  - **New cron job** → `cron/cron-jobs.md`, which is the register.
    Number it off the headings actually in that file, not off any count
    written elsewhere. (`cron-jobs-addendum.md` is archived under
    `.merge-history/` and its numbering is *wrong by design now* — its
    jobs 9-14 are live as 10-15. Do not add to it and do not run it.)
  - **New config** → `shared/*.yaml.template`, plus an entry in
    `onboarding/references/settings-catalog.md` tagged SIMPLE or
    ADVANCED, or the setting is invisible at onboarding.

## Step 4 — how the change actually gets written

Drafting and folding decide *what* the change is. This step is *how* it
lands, and it is not this skill's own invention — it is the same path
`11-analytics-and-learning`'s Tier 1 proposals use, and reusing it is
the point (Step 3's rule against inventing a second, lighter-weight
approval pattern applies to this skill too).

**Write through `skill_manage`, with `skills.write_approval` enabled.**
That stages the edit under `~/.hermes/pending/skills/` rather than
landing it, and Kene approves it there. Concretely:

1. The fold is *composed* first — the edit is written into the host
   `SKILL.md` at the point it applies, as a real diff.
2. That diff is what stages, and that diff is what Kene approves. He is
   not approving a description of a change; he is approving the change,
   in position, and can see where it went.
3. Only then does it land. The draft `ADDENDUM.md` is archived under
   `.merge-history/addenda*/` with a status header naming the host.

**Two things this deliberately is not.** It is not Telegram approval —
that channel is Rule 1's, scoped to sending things outward
(`10-approval-and-submit`), and a skill edit sends nothing. And it is
not the curator's adoption path, which buys unattended rewriting at the
cost of archival and consolidation exposure; `skill_manage` +
`write_approval` works on unadopted skills, which is why this package
stays unadopted (see `README.md`'s curator section).

**One gap worth knowing.** `skills.write_approval` is a single global
boolean and it gates *edits*, not *archival* — those run through
separate paths. It does not make an adopted skill safe. See
`security/security-setup.md`.

## The overwrite risk — why this skill defaults to non-destructive

Worth being explicit about, since it's a real, documented weakness in
the underlying mechanism this skill builds on, not hypothetical
caution: Hermes's own skill-learning loop has a known self-evaluation
bias — it tends to rate its own generated output highly even when it
underperforms, and the same mechanism that creates skills can, left
unchecked, **overwrite a manually customized skill file with a worse
version**. This package has a lot of hand-tuned, reasoned-through
`SKILL.md` files in it (this package's own careful design, plus
everything built across this package's several passes) — letting an
automated authoring step silently rewrite one of those on `/learn`'s own
self-assessment of quality would be a real regression, not a
theoretical one.

**This is why Step 1 defaults to `ADDENDUM.md` over rewriting an
existing base file**, and why nothing this skill drafts — new skill or
addendum — gets written into the live skill directory without Kene
reviewing it first, same confirm-before-write posture as everything
else in this package, applied here to the package's own source code.

## What this skill does not do

Doesn't touch `hermes-agent-self-evolution`'s GEPA optimization pipeline
(the ICLR 2026 offline optimizer that generates and multi-objective-
scores skill variants) — that's a separate tool that doesn't run inside
the Hermes runtime by default, and nothing about this skill's design
assumes it's installed. If Kene wants that layered on later, it's a
distinct, larger decision than what this skill covers.
