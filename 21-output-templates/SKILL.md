---
name: job-hunting-output-templates
description: "Create or edit templates for outward-facing artifacts"
metadata:
  hermes:
    tags: [job-hunting, output-templates]
    category: job-hunting
    related_skills:
      - job-hunting-resume-customizer
      - job-hunting-cover-letter
      - capability:cold_outreach
---

# Output Templates

## When this skill applies

Use this skill when Kene wants to create, edit, or manage a named template for any outward-facing artifact this pipeline produces — cover letters, application answers, resumes, cold emails, cold DMs, social replies, or (once built) social posts. Triggers: 'I want a specific way of writing cover letters for X,' 'save this as a template,' 'use my [name] template for this one.' Three ways to specify a template (a strict structural outline, general natural-language instructions, or submitted writing samples), and two independent modes governing how the result interacts with the built-in default (append — layered on top, preserving the built-in structure's own advantages — or replace — the built-in default isn't consulted at all). A template always guides STRUCTURE, never the actual words used; content stays custom every time. Elicited entirely through natural conversation, the same register 16-career-pulse's journal already uses — never a form. Confirms and saves directly to shared/output-templates.yaml; does not route through 07-context-architect — see Rule 11.

Origin: Kene's request to generalize something that already exists in
narrow form — every artifact this pipeline produces already has exactly
one built-in structural guide (`06-cover-letter/references/
cover-letter-formula.md`, `capability:social_listening/references/
cold-dm-email-schema.md`'s message shape). This turns "one hardcoded
default" into "any number of named, user-authored ones," elicited by
talking rather than filling in a form, plus the targeting parameters
each producing skill already tracks.

## What a template actually is — and isn't

A template governs **structure, never content**: section order, what
each section should accomplish, tone, length. The generated artifact is
still fully custom to the specific JD/contact/context every time.

**An earlier pass of this skill treated "how strictly to follow a
structure" as the only lever. That collapsed two genuinely different
questions into one, and this rebuild separates them:**

- **How the template gets specified** — three ways, below.
- **How it interacts with the built-in default** — two independent
  modes, below, orthogonal to how it was specified.

Every template a Kene creates has a value on *both* axes, chosen
separately.

## The three ways to specify a template

### (a) Strict structural outline

Kene states the structure directly and precisely — "Opener: two
sentences referencing something specific about the company. Body:
exactly three bullets, each starting with a number. Close: one
sentence, no stock phrases." Least inference required from this skill;
the elicitation mostly just captures what's said.

### (b) Natural-language general instructions

Looser, feel-based guidance rather than an explicit spec — "keep it
casual, don't oversell, mention I'm local if it's relevant." This
skill has to infer a structure that honors the instruction rather than
being handed one directly. See the append/replace interaction below —
this is the one input way where the choice of mode genuinely changes
how much work this skill has to do to produce something usable.

### (c) Submitted writing samples

Kene pastes a URL, uploads a past message, or points at something he's
written before. This skill extracts the structural/stylistic pattern
from the concrete example — same source-ingestion tools `/learn` uses
(`read_file`, `web_extract`), applied to a data record rather than a
new skill file (see `18-skill-composer`'s reasoning for why the output
shape differs even though the ingestion mechanism is shared). Always
confirmed conversationally before saving, never accepted as-extracted
verbatim.

## The two application modes — independent of how the template was specified

### Append mode — layered on top, not swapped in

The user's template gets fit into the existing built-in guide
(`cover-letter-formula.md`'s five-paragraph flow, for example) at
whatever points make sense, **without losing that built-in structure's
own established advantages** — its tone rules, its word-limit
discipline, its proven flow. Concretely, per input way:

- **(a) strict outline, append**: specific instructions slot into the
  matching built-in section rather than replacing the whole flow — "add
  a line about my volunteer work" lands in the Story paragraph, not a
  wholesale restructure.
- **(b) general instructions, append**: the built-in structure stays
  exactly as-is; the instruction becomes a tone/style overlay applied
  across it.
- **(c) writing samples, append**: the built-in paragraph structure
  stays; the extracted *voice* (sentence rhythm, word choice) replaces
  the built-in tone within that same structure.

### Replace mode — the built-in default isn't consulted at all

- **(a) strict outline, replace**: the draft follows only Kene's
  specified structure, full stop.
- **(b) general instructions, replace** — **the one combination worth
  flagging as genuinely riskier than the other five**: general
  instructions alone under-specify a structure, and with nothing
  built-in to anchor to, this skill has to derive a full structure from
  loose guidance with the least to work from of any combination. This
  skill shows the derived structure back to Kene for explicit
  confirmation before saving in this specific case, more deliberately
  than the other five combinations warrant — the underdetermination is
  real, not just a theoretical edge case.
- **(c) writing samples, replace**: the draft follows only the
  extracted structure from the samples — the built-in default is fully
  set aside.

`strictness` (`guide`/`strict`, unchanged from before) still applies
*within* whichever structure results from the mode above — it answers
"how rigidly to follow this structure," a third, independent question
from *which* structure applies.

## The data shape

```yaml
# shared/output-templates.yaml — one entry per named template
- template_id: ""
  artifact_type: ""    # cover_letter | application_answer | resume |
                         # cold_email | cold_dm | social_reply |
                         # social_post (stub, per 14's inactive channel)
  name: ""              # Kene's own name for it, e.g. "Startup Casual"
  input_method: ""       # strict_outline | general_instructions |
                          # writing_samples — how this template was specified
  application_mode: ""   # append | replace — how it interacts with the
                          # built-in default; independent of input_method
  structure:             # ordered list — guidance, never wording.
                          # For append mode, section names should match
                          # (or explicitly note "new section, insert
                          # after X") the built-in default's own
                          # sections, so the merge is unambiguous.
    - section: ""
      guidance: ""
  strictness: "guide"    # guide | strict — how rigidly to follow
                          # whichever structure application_mode
                          # produces, independent of input_method/
                          # application_mode
  trigger_conditions: []  # e.g. "company_stage: seed/series-a",
                          # "role_family: engineering", "source_cta_type:
                          # dm_instructions" — reuses each artifact
                          # type's own existing field vocabulary, not a
                          # new one (see references/elicitation-checklists.md)
  recipient_targeting:
    mode: ""              # individual_list | described_category | any
    individuals: []
    category_description: ""  # e.g. "technical recruiters at companies
                                # under 50 people" — matched at
                                # generation time by the same kind of
                                # judgment call target_customer_profile
                                # already uses in shared/pitch-catalog.yaml
  parameters: {}           # artifact-specific — see the checklist file;
                            # never a new parameter surface, always the
                            # existing one for that artifact type
  source_material: ""      # the URL/document reference, if input_method:
                            # writing_samples — kept for Kene's own later
                            # reference, not re-fetched at generation time
  created_at: ""
  last_used_at: null      # null = never used. "" would be a used-at-unknown-time
                          # value, and the package's own rule is that skipped
                          # must stay distinguishable from done.
```

## Elicitation — conversation, not a form

`references/elicitation-checklists.md` holds the complete field list per
artifact type, each one reusing that artifact's *existing* parameter
vocabulary rather than inventing a parallel one — a cold-DM template's
`trigger_conditions` options are the same fields `14-social-discovery-
outreach`'s CTA classification already produces, not a new taxonomy to
maintain twice.

The conversation itself: determine the artifact type first, then which
of the three input ways fits what Kene's actually doing (he'll usually
signal this himself — "here's exactly how I want it structured" is (a),
"just keep it casual" is (b), a pasted link or upload is (c)), then ask
only for whatever the checklist still needs beyond that — if Kene
volunteers three fields in one answer, extract all three, don't re-ask
what's already been said. Then confirm `application_mode` explicitly —
append or replace — since it's never inferred from the input way alone;
even a precise (a) strict outline could be meant as an addition to the
built-in flow or a full swap, and only Kene knows which. Same
voice-friendly setup every other elicitation in this package reuses
(`voice-interview-mode.md`), same reason: describing a structure out
loud is often easier than composing it as a spec.

## Confirmation and ownership

Confirmed directly by this skill, saved straight to `shared/output-
templates.yaml` — **deliberately not routed through
`07-context-architect`**, unlike career-fact memory. See the new Rule
11 in `shared/pipeline-rules-addendum.md`: a template is a pipeline-
behavior preference (closer in kind to `tier-config.yaml` or
`dynamic-target-calibration.yaml`) than a fact about Kene's career, and
giving it its own confirm step rather than folding it into
`07-context-architect`'s remit keeps that skill's job (the one place
that writes career-fact memory) from quietly expanding into "also
manages output formatting preferences," a different kind of thing.

## Selection at generation time

Every producing skill checks `output-templates.yaml` before drafting —
purely additive, so a Kene who never creates a template sees no change
in behavior:

- No saved template matches the current context → the existing
  built-in default runs exactly as before.
- Exactly one template matches (`trigger_conditions`/
  `recipient_targeting`) → `application_mode` decides what happens
  next: `replace` skips the built-in default entirely and drafts from
  the template's own `structure`; `append` drafts from the built-in
  default with the template's `structure` merged in at the matching
  points, per the per-input-way merge behavior above.
- More than one plausible match → a quick confirm ("your Startup
  Casual or Formal Recruiter template could both apply here — which?"),
  never a silent pick between two things Kene explicitly authored.
- Every draft is tagged with which template (and which mode) produced
  it, so Kene can see it at a glance rather than having to infer it.

Each producing skill's own wiring for this is in its `ADDENDUM.md` —
`05-resume-customizer`, `06-cover-letter`, `08-application-qa`, plus
this skill's own note in `capability:social_listening`'s and
`capability:cold_outreach`'s files for cold DM/email/reply.

## Reference files

- `references/elicitation-checklists.md` — the complete per-artifact-type
  field list this skill's conversation works from.
