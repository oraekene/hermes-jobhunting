<!-- STATUS: ABSORBED. This file is preserved as a record, not as instructions.
Content lives in 05-resume-customizer/SKILL.md (first_time format branch + template precedence).
Do not follow it as a procedure; the host file named above is authoritative. -->

# 05-resume-customizer — Addendum: a format branch for `profile_stage: first_time`

Reverse-chronological work history is this skill's implicit default
shape — the wrong one for someone who doesn't have a work history to
organize chronologically. For `profile_stage: first_time`:

- Default to a **skills/projects-led format** (functional or
  combination) rather than reverse-chronological — organized around
  what the person can do and has built, not a timeline of employers
  that may have one or zero entries.
- An **Interests/Activities section becomes standard**, not the
  niche addition `20-interests-profile/SKILL.md` scoped it as for the
  general case — pulling from `memory/interests-profile.md`, same
  sensitive-category discretion rule (Rule 10) applying regardless of
  `profile_stage`.
- Content sources widen the same way `09-risk-tactics-gate/ADDENDUM.md`
  already does — school projects, coursework, volunteer work,
  interests-profile entries are legitimate resume content here, not a
  weaker substitute for "real" experience.

`profile_stage: experienced`/`returning_after_gap`/`career_pivot` all
keep this skill's existing default format unchanged.

## Wiring: `21-output-templates`

Same check as `06-cover-letter/ADDENDUM.md`: before applying the
`profile_stage`-driven default format above, check `shared/output-
templates.yaml` for an `artifact_type: resume` match — a matched
template's format/section choices override the `profile_stage` default
for that specific application, the `profile_stage` logic only ever
applies when nothing more specific was saved.
