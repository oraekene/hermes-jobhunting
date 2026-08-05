---
name: job-hunting-resume-customizer
description: "Produce a tailored ATS-formatted resume for one posting"
metadata:
  hermes:
    tags: [job-hunting, resume-customizer]
    category: job-hunting
    related_skills:
      - job-hunting-keyword-analysis
      - job-hunting-cover-letter
      - job-hunting-risk-tactics-gate
      - job-hunting-output-templates
---

# Resume Customizer

## When this skill applies

Use this skill to produce a fully tailored, ATS-formatted resume for a specific job posting, using the keyword analysis JSON, the JD analysis, and the match analysis. Triggers: 'customize my resume for this job', 'tailor my CV', or being handed the outputs of 02-04 by the orchestrator. Do NOT use this to write the cover letter (06-cover-letter) or to decide whether a risky tactic is evidence-backed (that already happened one step earlier, in 09-risk-tactics-gate — this skill only applies tactics that already passed the gate).

Origin: Kene's original "Chat 3B," restructured around the Splendor
thread's tactics, and **the output format is changed on purpose** — see
"Format change" below, it's the most important edit in this file.

## Format change: docx, not styled HTML

The original prompt output a styled HTML/CSS template (floated date
ranges, custom borders, two-column-adjacent spacing). The Splendor thread
is explicit and specific about why that's a liability: many ATS parsers
mis-read tables, columns, text boxes, and graphics, and can silently
mangle or drop content — .docx in a single column, standard fonts
(Calibri/Arial/Times New Roman), standard bullets, and clear section
headers (PROFESSIONAL EXPERIENCE, EDUCATION, SKILLS) parse far more
reliably. **This skill now uses the `docx` skill (`/mnt/skills/public/docx/`
or Hermes's own docx-capable tool) to output a real single-column `.docx`
file** — no tables, no text boxes, no headers/footers, no images/logos.
Only fall back to a styled format if the specific posting explicitly asks
for a PDF/portfolio-style submission.

## Format branch — `profile_stage: first_time`

Reverse-chronological work history is this skill's implicit default
shape, and it is the wrong one for someone with no work history to
organise chronologically. When `target-profile.yaml`'s `profile_stage`
is `first_time`:

- Default to a **skills/projects-led format** — functional or
  combination — organised around what the person can do and has built,
  not a timeline of employers with one or zero entries in it.
- An **Interests/Activities section becomes standard**, not the niche
  addition `capability:interests_profile` scopes it as in the general case.
  Pull from `memory/interests-profile.md`, with Rule 10's
  sensitive-category discretion applying at every `profile_stage`.
- Content sources widen exactly as they do in `09-risk-tactics-gate`:
  school projects, coursework, and volunteer work are legitimate resume
  content here, not a weaker substitute for "real" experience.

`experienced`, `returning_after_gap` and `career_pivot` keep this
skill's existing default format unchanged.

**Template precedence.** Before applying the `profile_stage` default
above, check `shared/output-templates.yaml` for an `artifact_type:
resume` match. A matched template's format and section choices override
the `profile_stage` default for that application — the `profile_stage`
logic only applies when nothing more specific was saved.

## Phase 1 — Keyword integration (from 04-keyword-analysis JSON)

For every `found_in_resume: false` entry that **cleared `09-risk-tactics-gate`**
— either a genuine `[PASS]` (evidence match in memory/portfolio), or an
`[UNVERIFIED]` tag under `balanced`/`embellish` fidelity mode (see that
skill's "Fidelity mode" section) — apply it, tagged accordingly in this
skill's own change-log contribution. Never apply anything the gate left
stripped under `strict` mode; that means don't use it, full stop:
- **Terminology swaps**: resume says "GitHub," JD wants "Git" → use the
  JD's exact term.
- **Exact-phrase mirroring (Splendor thread)**: where the gate confirms
  Kene genuinely has the skill, use the JD's exact wording rather than a
  paraphrase — e.g. if the posting says "Strong SQL skills, with the
  ability to query, join, and manipulate large and complex datasets,"
  and Kene's evidence supports it, that phrase (or the operative clause
  of it) goes in verbatim. Do not get creative with synonyms here — ATS
  matching is literal, and paraphrasing loses the match.
- **Priority 3 (Hard Skills)**: explicitly add to Skills section or
  Professional Summary if evidence supports it.
- **Priority 2 (Domain Concepts)**: weave into Summary or the most
  relevant Experience/Project bullet.
- **Explode tech stacks**: list every specific tool the JSON lists, not
  a category label.
- Keyword density: high-priority terms appear in the top third of the
  document (Summary + Skills).

## Phase 2 — Structural mirroring (Splendor thread)

If the JD analysis (`02-jd-parser`) captured named section headers
(e.g. "Data Governance & Quality"), and Kene has genuinely relevant
experience for that category, create a matching section using that exact
header instead of a generic chronological layout. This does two things:
satisfies ATS structural keyword matching, and makes the human reviewer's
scan trivially easy — the resume is already organized around what they
asked for.

## Phase 3 — Role title alignment (Splendor thread, gated)

If `09-risk-tactics-gate` has cleared the title change — either a genuine
`[PASS]` because Kene's actual responsibilities in his current/most
relevant role genuinely match the target title, or an `[UNVERIFIED]` tag
under `balanced`/`embellish` mode — the resume's job title line may be
adjusted toward the posting's title (e.g. "Data Governance Specialist" if
that's what he applied for and, for a `[PASS]`, what he actually did).
**This skill never makes that call itself** — it only applies a title
change the gate already cleared, tagged the way the gate returned it, and
it always keeps a `title_original` / `title_displayed` pair in the
application record so the difference is visible to Kene at approval time,
not buried.

## Phase 4 — Values alignment section (Splendor thread)

If `02-jd-parser` captured stated company values, add a short "Values
Alignment" section: one line per value, connecting it to something Kene
has actually done (pull from the STAR bank / memory, don't invent). Skip
this section entirely if the posting states no values — don't manufacture
one.

## Phase 5 — Quantification (Splendor thread + original)

Every major bullet should carry a number where the evidence supports one
— percentage, dollar amount, time saved, records processed, team size,
scope. If memory has an estimate rather than an exact figure, say so
plainly to Kene rather than presenting an estimate as measured fact.
This is what `07-context-architect`'s Quantification gate exists to make
possible — if a STAR bank entry lacks a number, that's a memory-side gap
to fix there, not something this skill should paper over at write time.
If the Holographic memory layer is configured (optional — see
`07-context-architect/references/holographic-memory-layer.md`), a quick
`fact_store(action="probe")` on the project name can double-check that
the number about to go on the resume matches what's on record elsewhere
— not a blocking step, just a cheap second look on the numbers doing the
most work.
Log the resulting `quantified_bullet_count` to the applications DB
(`shared/applications_db_schema.sql`) so `11-analytics-and-learning` can
correlate it against response rates over time.

## Phase 6 — Standard best practices (original)

Action-verb + hard-skill + result bullet structure. Keep essential
non-matching qualifications unless space is critical — don't delete
impressive experience just because this JD didn't ask for it. Mirror the
JD's tone (innovation-forward postings get creative-solution framing;
compliance-forward postings get reliability framing) without changing
what actually happened.

## Phase 7 — Anti-slop, then humanizer, then anti-slop again

Bullets are drafted **against**
`06-cover-letter/references/anti-slop-checklist.md` from the start —
including its structural bans, which are the ones that survive a
find-and-replace. Generating clean is cheaper than cleaning up, and a
humanizer pass over text built on rhetorical scaffolding produces fluent
scaffolding.

Then the humanizer. Then check the output against the checklist once
more: `humanizer` is a general skill and does not know these bans, so it
can reintroduce one while fixing something else. That third step is the
one most likely to be skipped and the reason output drifts back toward
generic over time.

### The humanizer pass itself

Run the finished bullet text through the bundled `humanizer` skill
before handing off to `09-risk-tactics-gate`. This is a phrasing pass
only — it strips generic LLM-tell constructions ("leveraged synergies
to drive," stock transition phrases, the kind of sentence that reads
fine once and generic the fifth time an ATS reviewer sees it this week)
and tightens toward how Kene actually talks, without touching any
number, claim, or fact this skill's earlier phases already set. If a
humanizer suggestion would change what a bullet actually claims (not
just how it's phrased), don't apply it — that's out of scope for this
pass and back in `09-risk-tactics-gate`'s territory, not this one's.

## Output

A `.docx` file per `references/ats-formatting-rules.md`, plus a short
change-log (what keywords were added, what title/phrase decisions were
applied and why) that `10-approval-and-submit` shows Kene alongside the
file at review time.

## Fixing a typo without regenerating (S7)

When `08-application-qa` catches a typo in an already-generated PDF, use
`productivity/nano-pdf` to edit the text in place rather than
regenerating the document.

The reason is not speed. Regeneration re-rolls wording Kene already read
and approved — a bullet he signed off on comes back phrased differently,
and now he has to re-review the whole document to find out what else
moved. A one-word fix should change one word.

Regenerate, not patch, when the change is structural: a section reordered,
a bullet added, keywords re-integrated. Patching those in a PDF produces
layout damage that is harder to spot than the original problem.
