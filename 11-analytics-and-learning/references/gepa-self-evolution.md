# GEPA-Based Self-Evolution — Tier 2 (optional, manual, not cron-automated)

**Read this before running anything.** Everything below was verified by
reading the actual `hermes-agent-self-evolution` source
(`evolution/core/*.py`, `evolution/skills/*.py`) directly — not by
trusting its own `PLAN.md`/`README.md`, which describe a more automated,
more rigorously-scored system than what's actually wired up in the code.
Several gaps between the documentation and the implementation matter a
lot for how much to trust this tool, and they're called out explicitly
below rather than smoothed over.

## What this is, relative to what `11-analytics-and-learning` already does

`11-analytics-and-learning`'s weekly review (**Tier 1**) is fast, cheap,
explainable: correlate a tactic against real response rates, propose a
targeted edit via `skill_manage` + `write_approval`, done in-band, no
extra tooling. Nothing here replaces that.

**Tier 2** is `hermes-agent-self-evolution` — a separate repo
(`NousResearch/hermes-agent-self-evolution`, MIT-licensed), a
DSPy+GEPA-based tool that treats a skill's body text as an optimizable
parameter and evolves it against an evaluation dataset. It's slower,
costs real API money per run (many LLM calls per optimization pass, not
one), requires manual setup, and its output is **never applied
automatically** — every run just produces two local files to read and
compare, same as Tier 1's proposals, gated the same way. Run this
quarterly, or when Tier 1's simple correlation nudges feel like they've
plateaued — not on a schedule, and there is deliberately no cron job or
blueprint for this anywhere in this package.

## Scope: three skills, not four

The original recommendation for this feature named `05`, `06`, `08`,
and `09` as candidates. **This build deliberately excludes
`09-risk-tactics-gate`.** Reason, not just caution: reading
`evolution/core/constraints.py` in full (below) showed the tool's
safety-gate system checks size, growth percentage, non-emptiness, and
frontmatter structure — **nothing about content**. There is no
mechanism, as shipped, that would notice or object to an evolved skill
becoming *more permissive*. `09-risk-tactics-gate` is the one skill in
this whole pipeline whose entire value is being conservative and
rule-following — optimizing it against an outcome metric (even a
carefully-built one) is exactly the wrong place to first try a tool with
this gap in its safety net. `05-resume-customizer`, `06-cover-letter`,
and `08-application-qa` are lower-risk: their job is persuasive-writing
*quality* inside constraints `09-risk-tactics-gate` still separately
enforces at runtime regardless of what these three look like. Revisit
including `09` later, if ever, only alongside a much more rigorous
custom safety gate than what's described below.

## Three things the tool's own docs oversell — verified by reading the code, not assumed

### 1. The fitness metric is keyword overlap, not "LLM-as-judge"

`PLAN.md` describes scoring as "LLM-as-judge with rubrics" across three
dimensions. The actual metric passed to `dspy.GEPA(metric=...)` in
`evolve_skill.py` — confirmed by grep, not inference — is
`skill_fitness_metric`, and its real implementation is:

```python
# evolution/core/fitness.py — this is the ACTUAL scoring during optimization
expected_words = set(expected.lower().split())
output_words = set(output_lower.split())
overlap = len(expected_words & output_words) / len(expected_words)
score = 0.3 + (0.7 * overlap)
```

A word-overlap ratio between your `expected_behavior` text and the
agent's output. The more sophisticated `LLMJudge` class (three-dimension
rubric scoring, the thing `PLAN.md` actually describes) **exists in the
same file but is imported and never called** anywhere in
`evolve_skill.py`. This isn't a bug to route around so much as a fact to
design the dataset for: **write `expected_behavior` so its own wording
contains the actual words a good output would use**, not just a
description of the desired quality in the abstract. `build_gepa_golden_
set.py` (below) does this deliberately — e.g. "mirror exact JD phrasing"
rather than just "should be well-tailored."

### 2. The constraint gate has no content-safety check at all

Covered above (scope decision) — worth restating precisely:
`ConstraintValidator.validate_all()` runs exactly four checks (size
limit, growth-vs-baseline limit, non-empty, has-frontmatter-with-name-
and-description), and nothing else. `run_test_suite()` exists as a
method but **is never called from `evolve_skill.py`'s actual flow** —
the `--run-tests` CLI flag threads a `run_tests` value into
`EvolutionConfig(run_pytest=...)` but nothing downstream reads that
field to decide whether to actually run pytest. Don't assume `--run-
tests` is doing anything until you've confirmed otherwise against
whatever version you've cloned.

**Mandatory before running this on any of the three in-scope skills**:
add a safety-anchor check to your local clone's
`evolution/core/constraints.py`. This is not optional hardening, it's
the minimum bar for using this tool on this pipeline at all. Add this
method to `ConstraintValidator`:

```python
def _check_safety_anchors(self, evolved_text: str, baseline_text: str) -> ConstraintResult:
    """Reject any evolved skill that dropped a safety-critical anchor
    present in the baseline. Frequency-floor, not exact-phrase match —
    robust to legitimate rewording, not to deletion."""
    anchors = ["09-risk-tactics-gate", "invent", "fabricat"]
    dropped = []
    for anchor in anchors:
        baseline_count = baseline_text.lower().count(anchor)
        evolved_count = evolved_text.lower().count(anchor)
        if baseline_count > 0 and evolved_count < baseline_count:
            dropped.append(f"{anchor!r} ({baseline_count} -> {evolved_count})")
    if dropped:
        return ConstraintResult(
            passed=False,
            constraint_name="safety_anchors",
            message=f"Evolved skill reduced safety-anchor mentions: {', '.join(dropped)}",
        )
    return ConstraintResult(
        passed=True,
        constraint_name="safety_anchors",
        message="Safety anchor frequency held or increased",
    )
```

Then add one line to `validate_all()`, right after the existing `if
baseline_text:` block that calls `_check_growth`:

```python
        if baseline_text:
            results.append(self._check_growth(artifact_text, baseline_text, artifact_type))
            results.append(self._check_safety_anchors(artifact_text, baseline_text))  # ADD THIS LINE
```

This is a frequency floor on three stable anchors (the literal
cross-reference to `09-risk-tactics-gate`, and the `invent`/`fabricat`
word stems that anchor this pipeline's fabrication-prevention language
in all three in-scope skills — verified present in the actual current
text of `05`, `06`, and `08` before writing this, not assumed). It will
not catch every possible regression — no mechanical check will — but it
turns "nothing checks content at all" into "a specific, known, checkable
floor," which is the minimum this pipeline should require before trusting
this tool's PASS/FAIL output on anything.

### 3. There is no auto-generated PR — the real output is two local files

`PLAN.md`'s architecture diagram shows "Git Branch + PR (with diff,
metrics, before/after comparison) → Human Review & Merge." The actual
`evolve()` function writes `output/<skill>/<timestamp>/evolved_skill.md`,
`baseline_skill.md`, and `metrics.json`, then prints a suggested `diff`
command. `pr_builder.py` is listed in `PLAN.md`'s file tree but never
imported by `evolve_skill.py`. `create_pr: bool = True` exists in
`EvolutionConfig` but nothing reads it. In practice: you run the diff
yourself, read both files yourself, and — if it looks genuinely
better — hand-apply the change the same way a Tier-1 proposal gets
applied: through `skill_manage` with `write_approval`, never by copying
`evolved_skill.md` over the real file directly. This keeps every
skill-edit path in this pipeline, Tier 1 or Tier 2, going through the
same staged-approval mechanism.

## Setup

### The path problem, and the workaround

`find_skill()` (`evolution/skills/skill_module.py`) looks for
`{hermes_agent_path}/skills/<name>/SKILL.md` — it requires whatever
path you point it at to contain a `skills/` subdirectory, recursively
searched. This pipeline's skills live at
`~/.hermes/skills/job-hunting/05-resume-customizer/SKILL.md` — not
nested under a `skills/` folder the way `find_skill` expects. Rather
than needing to patch this too, the simplest fix is a small scratch
directory with symlinks:

```bash
mkdir -p ~/.hermes/evolution-workspace/skills
ln -s ~/.hermes/skills/job-hunting/05-resume-customizer ~/.hermes/evolution-workspace/skills/05-resume-customizer
ln -s ~/.hermes/skills/job-hunting/06-cover-letter ~/.hermes/evolution-workspace/skills/06-cover-letter
ln -s ~/.hermes/skills/job-hunting/08-application-qa ~/.hermes/evolution-workspace/skills/08-application-qa
export HERMES_AGENT_REPO=~/.hermes/evolution-workspace
```

`find_skill` matches on the containing directory's name first (`05-
resume-customizer`, matching what's used everywhere else in this
package), falling back to a fuzzy match against the frontmatter `name:`
field (`job-hunting-resume-customizer`) if the directory-name match
fails — either works as the `--skill` argument.

**One thing this workaround gets right for free**: `reassemble_skill()`
only ever replaces the markdown *body* — it explicitly preserves the
original frontmatter verbatim. The `metadata.hermes.blueprint` block on
skills that carry one (not on these three, but worth knowing generally)
is never touched by anything GEPA does here.

### Install the tool itself

```bash
git clone https://github.com/NousResearch/hermes-agent-self-evolution.git
cd hermes-agent-self-evolution
pip install -e ".[dev]"
```

Real dependency, real cost: this needs `dspy`+`gepa` and a working LLM
API key (`optimizer_model`/`eval_model` default to `openai/gpt-4.1`/
`openai/gpt-4.1-mini` — override via `--optimizer-model`/`--eval-model`
if you're using a different provider). A GEPA run makes many LLM calls
across its iterations, not one — budget for that before running this
across three skills.

**Apply the safety-anchor patch above to this clone now**, before
building the dataset or running anything.

### Build the golden dataset from real outcomes

```bash
cd ~/.hermes/skills/job-hunting/11-analytics-and-learning/scripts
python3 build_gepa_golden_set.py --output-dir ~/.hermes/evolution-workspace/datasets
```

Reads only structured columns already in `applications.db` (company,
role, industry, seniority, tactic counts, `response_type`) — never a
raw job-description or resume/cover-letter text, since neither is
persisted anywhere in this schema, and this script isn't the place to
start storing third-party posting text verbatim. `task_input` is a
realistic prompt synthesized from the structured fields; `expected_
behavior` is built from the *same real application's* own tactic counts
for applications with a confirmed `interview_request`/`screen_request`
response — the actual outcome-grounding this feature exists for. Refuses
to write anything with fewer than 12 qualifying applications (configurable
via `--min-sample-size`) — a golden set built from a handful of outcomes
is fitting noise, not a pattern. Tested against synthetic data during
development, including the too-few-samples refusal path and a full
round-trip through the real `EvalExample`/`GoldenDatasetLoader` schema.

### Run it

```bash
cd hermes-agent-self-evolution
python -m evolution.skills.evolve_skill \
  --skill 05-resume-customizer \
  --iterations 10 \
  --eval-source golden \
  --dataset-path ~/.hermes/evolution-workspace/datasets/05-resume-customizer \
  --hermes-repo ~/.hermes/evolution-workspace
```

Repeat for `06-cover-letter` and `08-application-qa`. Read the printed
per-holdout-example score honestly: it's a keyword-overlap number (see
above), not a semantic quality judgment — a higher score means the
output shares more words with your `expected_behavior` text, which is a
reasonable proxy given how the dataset was built, but not the same
claim `PLAN.md`'s "LLM-as-judge" framing would imply.

### Deploy — manually, gated, never automatic

1. `diff output/<skill>/<timestamp>/baseline_skill.md
   output/<skill>/<timestamp>/evolved_skill.md` and actually read it.
2. If it looks genuinely better — not just a higher keyword-overlap
   score — load Hermes's bundled `software-development/hermes-agent-skill-authoring`
   skill before drafting this edit, then apply it through `skill_manage`
   with `write_approval`, the same staged-approval path Tier 1's proposals
   already use. Never copy the evolved file over the real one directly.
3. If `_check_safety_anchors` (or the mechanical constraints) failed,
   don't relax the check to make the run pass — that check exists for a
   more important reason than a clean run.
