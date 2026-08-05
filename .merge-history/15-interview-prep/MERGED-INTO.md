# Merged into `13-interview-prep`

This directory previously declared `name: job-hunting-interview-prep`,
the same name as `13-interview-prep` in the main package. Two directories
declaring one skill name means Hermes resolves only one of them, and
which one wins depends on directory scan order.

Resolved by merge, not by choosing:

- `13-interview-prep/SKILL.md` is the spine. It carries the full
  implementation — the three-part brief/flashcard/study-session
  structure, the `memento-flashcards` integration, and the working
  cron blueprint.
- Everything unique to this directory has been folded into it: the
  role/industry/company interview-intelligence scrub, the
  `12-company-research` sentiment inheritance, the three-source
  cross-referenced question list, the reported-format signal, and the
  post-interview debrief and thank-you-note stage (now Part 4).
- `13-interview-prep/references/interview-intel-research.md` has been copied to
  `13-interview-prep/references/`.
- The interviewer-research boundary, where the two documents disagreed,
  is reconciled explicitly in the merged skill's closing section rather
  than silently resolved in one direction.

The original text is preserved here as `SUPERSEDED-SKILL.md` (frontmatter
intact, but no longer loaded as a skill because the file is not named
`SKILL.md`). Nothing was discarded.
