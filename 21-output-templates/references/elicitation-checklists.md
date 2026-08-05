# Elicitation Checklists — per artifact type

Every list below reuses the vocabulary the producing skill already has
— checked against each skill's actual current file before writing this,
not assumed. This skill's conversation only needs to ask for what's
still missing after Kene's said something, against whichever list
applies.

## `cover_letter` (produced by `06-cover-letter`)

The base default is `06-cover-letter/references/cover-letter-formula.md`'s
five-paragraph structure (Hook → Technical Match → Story → Why This
Role → Close) with its own tone rules (contractions fine, cut stock
phrases, under 400 words). A custom template's checklist:

- Which of the five sections to keep, reorder, merge, or replace —
  default assumption is "same five, Kene's own emphasis" unless he says
  otherwise.
- Tone beyond the base rules — more formal, more casual, shorter than
  400 words, etc.
- `trigger_conditions` — company stage/size, role family, industry, or
  any other condition drawn from what `12-company-research`'s cache
  already tracks.
- `recipient_targeting` — individual company names, or a described
  category ("Series A/B startups," "big tech").

## `application_answer` (produced by `08-application-qa`)

Base default: classify by question type (technical/skills, behavioral/
situational, motivation/career-goals, domain expertise, personal
qualities, cultural fit) → select one best-fit STAR story → weave
gated keywords → output as Strategy Brief + Final Response + word/char
count. A custom template's checklist:

- Which question types this template applies to — a template rarely
  covers all six categories equally, usually one or two (e.g. a
  "cultural fit answers" template).
- Whether to change the output format itself (the Strategy Brief
  section is internal scaffolding — some users might want it omitted
  from what they see, keeping only the Final Response).
- `trigger_conditions` — question category, word-limit range, whether
  `variant_dimensions` apply (per `07-context-architect/references/
  answer-variants.md`).
- `recipient_targeting` — same company-stage/category options as
  cover letters, since motivation/cultural-fit answers read the same
  research cache.

## `resume` (produced by `05-resume-customizer`)

Base default: reverse-chronological for `profile_stage: experienced`/
`returning_after_gap`/`career_pivot`, skills/projects-led for
`first_time` (per `05-resume-customizer/ADDENDUM.md`). A custom
template's checklist:

- Section order and inclusion (an Interests/Activities section,
  otherwise standard only for `first_time`, can be explicitly added for
  any `profile_stage` via a template).
- Format family — chronological, functional, combination — overriding
  the `profile_stage` default where Kene wants a specific format
  regardless of stage.
- `trigger_conditions` — role family, seniority band, whether a
  portfolio link is expected.
- `recipient_targeting` — same options as above.

## `cold_email` / `cold_dm` (produced by `14-social-discovery-outreach`, `17-cold-prospecting`)

Base default: `14-social-discovery-outreach/references/cold-dm-content-
formula.md` — hook → value-prop → ask → sign-off, with its own
banned-opener register rules and per-channel length table. A saved
template here now behaves like `cover_letter`'s: `append` layers onto
that formula, `replace` opts out of it entirely. Checklist, using the
schema's own field vocabulary directly:

- `message.channel` this applies to (dm/email/reply).
- Structure — opener/hook approach, how personalization_hooks get
  used, ask/CTA phrasing style, sign-off convention.
- `trigger.type`/`trigger.source_cta_type` this applies to (e.g. a
  template specifically for `dm_instructions`-triggered outreach vs.
  `manual_request` cold prospecting).
- `contact.relationship`/`contact.role_guess` as `recipient_targeting`
  category options (e.g. "recruiters" vs. "hiring managers" vs.
  "individual creators," for `17-cold-prospecting` targets).
- For `17-cold-prospecting` specifically: which `pitch_mode`
  (`role_fit`/`role_creation`/`service`) and which
  `shared/pitch-catalog.yaml` entries this template pairs with.

## `social_reply` (produced by `14-social-discovery-outreach` Part C)

Checklist:

- Which platforms this applies to (reply tier varies by platform per
  the capability matrix — a template shouldn't assume a tier it can't
  actually get).
- Structure — how directly to reference the original post, whether to
  include a link/portfolio reference as the post's CTA specified.
- `trigger_conditions` — `source_cta_type: reply_instructions`
  specifically, or broader.

## `social_post` (stub only — `14-social-discovery-outreach`'s inactive `quote`/`post` channels)

Not elicited yet — no producing process exists for this artifact type
to guide. This skill will accept a template *definition* for it (no
reason to block someone from describing what they want in advance) but
flags it clearly as inert until the personal-branding feature it
depends on actually gets built.
