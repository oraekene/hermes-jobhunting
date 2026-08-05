# 08-application-qa — Addendum: `21-output-templates` wiring

Before running the base classify → select-story → weave-keywords →
output process, check `shared/output-templates.yaml` for an
`artifact_type: application_answer` entry whose `trigger_conditions`
(question category, word-limit range, `variant_dimensions` applicability)
match the question at hand. No match → base process runs exactly as
`08-application-qa/SKILL.md` already specifies. A match can override
the output format specifically (e.g. omitting the Strategy Brief
section from what Kene sees, keeping only the Final Response) without
changing anything about the underlying story-selection or
keyword-weaving logic — a template governs presentation, never which
STAR story gets picked or which gated keywords get woven in.
