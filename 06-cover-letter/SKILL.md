---
name: job-hunting-cover-letter
description: "Write a tailored cover letter for one application"
metadata:
  hermes:
    tags: [job-hunting, cover-letter]
    category: job-hunting
    related_skills:
      - job-hunting-resume-customizer
      - job-hunting-application-qa
      - job-hunting-risk-tactics-gate
      - job-hunting-output-templates
---

# Cover Letter Generator

## When this skill applies

Use this skill to write a tailored cover letter for a specific application, using the JD analysis, match analysis, keyword report, and tailored resume. Triggers: 'write a cover letter for this', 'draft the cover letter', or being handed the pipeline outputs by the orchestrator after 05-resume-customizer. Always run this even if the application form marks the cover letter field optional — see references/cover-letter-formula.md for why.

Origin: Kene's original "Chat 4," restructured around the Splendor
thread's five-paragraph formula, and switched to plain-text/simple HTML
output rather than a heavily styled template, for the same ATS-parsing
reasons as `05-resume-customizer`.

## Always write one, even when marked optional

The Splendor thread's read on this: "optional" is a filter, not a
suggestion — it separates candidates willing to do the extra work from
everyone else. This skill runs on every application this pipeline stages,
full stop, regardless of whether the form marks the field required.

## Process

**First, check for a saved template.** Look in
`shared/output-templates.yaml` for an `artifact_type: cover_letter`
entry whose `trigger_conditions` / `recipient_targeting` match this
company and role. No match → the base default below runs unchanged. One
match → use it, and note which template in the draft. More than one →
ask Kene which, per `21-output-templates`'s own selection rule.

**Narrative shape when `profile_stage: first_time`.** This skill's
default opener leans on years-of-experience framing — "in my N years
doing X". That framing does not fit a first-time applicant and should
not be forced. The narrative shifts to what is actually true and still
genuine: what the person has built, learned, and cares about, and why it
points at this specific role. The same widened evidence sources
`09-risk-tactics-gate` and `05-resume-customizer` use at this stage —
school projects, volunteer work, `memory/interests-profile.md` entries —
are legitimate hook material here, not a fallback for when nothing
better exists. The fidelity discipline is unchanged throughout: a
genuine interest works as a "why this role" hook only when it is
actually true, exactly like any other claim this skill drafts.

Follow `references/cover-letter-formula.md` for structure. Key constraints
carried over from the thread:

- Under 400 words total.
- Sound like a person, not a form letter — contractions are fine, "I am
  writing to express my interest in..." is banned, it's the single most
  forgettable opening line in the genre.
- Paragraph 2 ("Technical Match") is where keyword density from
  `04-keyword-analysis` belongs — natural, not stuffed.
- Paragraph 3 ("The Story") needs one concrete, numbered example — pull
  from the STAR bank (`07-context-architect`), never invent one. If the
  Holographic memory layer is configured (optional — see
  `07-context-architect/references/holographic-memory-layer.md`),
  `fact_store(action="probe")` on the target company/project can
  surface a relevant atomic fact the headline story doesn't mention —
  worth a quick check, never a blocking one; proceed on the STAR bank
  alone if it's not configured or turns up nothing.
- Address the recruiter by name if `02-jd-parser` found one; otherwise
  use a role-appropriate generic greeting, never a fabricated name.
- Explain any real gap the match analysis (`03-resume-match`) flagged,
  briefly and professionally, rather than hoping it goes unnoticed.
- **Before moving to Output**: run the draft through Hermes's bundled
  `creative/humanizer` skill and check it against
  `references/anti-slop-checklist.md` (job-application-specific clichés
  humanizer's general pass won't all catch — banned openers/closers,
  self-description words used in place of the concrete example that's
  already in the STAR bank). The "sound like a person, not a form
  letter" rule above is exactly what these two passes exist to enforce
  systematically rather than trusting the model to self-police the same
  rule fresh on every single application. Phrasing only, same boundary as
  `05-resume-customizer`'s Phase 7: if a suggested change would alter
  what a sentence actually claims, don't take it — that's
  `09-risk-tactics-gate`'s job, not this pass's.

## Output

Plain text or minimally-styled HTML (single font, no floats/columns) —
whatever the application form's cover-letter field actually accepts.
No citation numbers or footnote markers in the final text.
