# Mixture of Agents Cross-Check (optional, human-initiated only)

**Read this before assuming the gate can "just call MoA" for a second
opinion — it can't, mechanically, and the reason matters for how this
feature is actually built below.**

## Why this is human-initiated, not automatic — verified, not assumed

The original idea for this feature (a MoA cross-check the gate reaches
for automatically on a borderline title-match) turned out not to be
buildable that way, for two independent, confirmed reasons:

1. **`/moa <prompt>` is a human-input-layer construct.** Checked
   `hermes-agent`'s own `cli.py` directly: slash commands are parsed
   from text typed into the chat input (`_should_handle_model_command_
   inline`, `_looks_like_slash_command`, and similar — all operating on
   `user_input`/typed text). An agent's own generated response is never
   re-parsed as a slash command. There is no tool-call equivalent of
   `/moa` a skill's instructions can have the model emit mid-turn.
2. **`delegate_task`'s model override is a global `config.yaml` setting,
   not a per-call parameter.** `delegation.model`/`delegation.provider`
   in `~/.hermes/config.yaml` applies to *every* subagent spawned by
   *any* skill — there's no way to say "just this one delegated task
   uses the MoA preset while everything else uses the normal model."
   Setting it globally to a MoA preset would silently apply MoA's extra
   reference-model cost to any other `delegate_task` usage in this
   pipeline too (relevant if the pipeline-sweep parallelism idea is ever
   built — that would multiply MoA cost across every parallel
   per-application build, not just this one evidentiary check).

Given both, the honest design is: **the gate flags a borderline call,
and hands Kene an exact, ready-to-run prompt** — MoA stays exactly what
it actually is, a human choosing a model for a specific hard question,
not something this pipeline pretends to automate around a mechanism
that doesn't support that shape of automation.

## What "borderline" means for the title-match check specifically

`09-risk-tactics-gate`'s own text already flags every title-match PASS
for Kene's eyes ("the single tactic most likely to raise a question in
an interview"). This feature adds one more distinction on top: a PASS is
marked `[BORDERLINE PASS]` instead of a plain `[PASS]` when the
equivalence relies on **inference or interpretation** rather than a
direct, explicit statement already in memory — e.g., the STAR bank
documents responsibilities that *imply* the target title's scope but
never states the equivalent title outright, versus a case where memory
already contains something close to "functioned as Analytics Lead,
Operations" verbatim. The second is a plain `[PASS]`; the first is
`[BORDERLINE PASS]` — still a pass (the evidence does support it), just
not a slam-dunk one, and exactly the kind of close call a second model's
independent read is actually useful for.

## What Kene sees, and what to do with it

`10-approval-and-submit`'s Telegram message surfaces a `[BORDERLINE
PASS]` line with a ready-to-paste prompt, something like:

```
Title match flagged [BORDERLINE PASS] — worth a second opinion before approving:

/moa Is displaying the title "Analytics Lead, Operations" for a role
documented as "<the actual memory text>" a fair equivalence, or does it
overstate scope? Answer PASS or FAIL with one sentence of reasoning.
```

Kene can paste that directly into the same chat. If a MoA preset is
configured (see below), this runs through two reference models plus an
aggregator, entirely at his discretion — or he can just read the
flagged reasoning himself and decide, same as any other borderline call.
Neither path blocks anything; `[BORDERLINE PASS]` is still a pass unless
Kene overrides it.

## Recommended preset (if you want this to be worth doing)

A dedicated preset, not the profile's general-purpose default — this is
specifically an evidentiary-judgment task, not a coding or general
Q&A task, so tune for that:

```yaml
# ~/.hermes/config.yaml
moa:
  presets:
    risk-gate-review:
      reference_models:
        - provider: openrouter
          model: anthropic/claude-opus-4.8
          reasoning_effort: high
        - provider: openrouter
          model: openai/gpt-5.5
          reasoning_effort: high
      aggregator:
        provider: openrouter
        model: anthropic/claude-opus-4.8
        reasoning_effort: high
      reference_max_tokens: 400   # this is a PASS/FAIL + one sentence, not an essay
      fanout: user_turn            # default; this is always a single one-shot prompt anyway
      enabled: true
  privacy_filter: full           # see "What the privacy filter does" below
```

Use it either by switching models for one message (`/model risk-gate-
review --provider moa`, ask again, switch back) or, more conveniently,
by making it the **default** MoA preset (`moa.default_preset: risk-gate-
review`) so the bare `/moa <prompt>` form works directly, since this
pipeline's actual `/moa` use case is narrow enough that a dedicated
default is more convenient than juggling multiple presets.

`reference_max_tokens: 400` matters here specifically — the doc's own
guidance is that advisor latency dominates turn time and this is a
short, bounded judgment call, not open-ended analysis; there's no reason
to let two reference models write paragraphs when the actual ask is
PASS/FAIL plus one sentence.

## What the privacy filter does, and what it doesn't

`moa.privacy_filter` takes `''`, `display`, or `full`. Set it to `full`.

What it covers, read from `agent/moa_loop.py` rather than inferred: it
redacts **advisor output** — the labelled reference blocks rendered in
the UI, the saved MoA trace files, and (in `full` mode only) the guidance
block injected into the aggregator prompt. Secret shapes (API-key
prefixes, JWTs, private keys, DB connection strings, E.164 phone numbers)
are handled by the repo's central redactor; the MoA filter adds emails
and delimited phone numbers on top, with the phone pattern deliberately
requiring separators so it doesn't mangle dates, git SHAs, or IPs.

**What it does not cover: the prompt going out.** The filter runs on text
coming back. Nothing it does prevents whatever Kene pastes from reaching
the reference models. That matters less here than it would elsewhere,
because of the shape this feature deliberately has — see below — but it
is worth being exact about, since `full` sounds more total than it is.

## What goes in the payload — the role envelope

The obvious two payload shapes are both wrong, and their failure modes
are different, so it is worth being explicit about why this one sits
between them.

**Too narrow — the bare STAR snippet.** This is what an earlier version
of this file specified: the title claim plus the one memory line
supporting it. It fails in both directions.

- *False PASS.* "Owned the forecasting and reporting function, built the
  weekly ops dashboard leadership ran on, and set the methodology the
  other analysts followed" reads like a lead. Elsewhere in the record
  that role is titled Analyst II, reports to a Director of Analytics,
  and sits among six peers. Every word of the snippet is true and the
  title claim still overstates scope — but the advisor cannot see the
  reporting line, so it passes.
- *False FAIL.* A terser snippet — "owned forecasting and reporting" —
  reads thin. The adjacent bullet in the same role, not extracted
  because it was not the STAR entry, says "hired and managed three
  analysts." The evidence exists; it just was not in the payload. A
  defensible title gets dropped.

**Too wide — the full resume, redacted.** Sending the whole record
introduces a halo effect: a model reading an impressive career judges a
single title stretch more permissively than one reading the claim in
isolation. This is well documented in human raters and there is no
reason to assume models are exempt, and it biases toward PASS on
precisely the marginal cases the gate flagged. It also stops being a
cross-check: the gate reached its conclusion from specific evidence, and
a second opinion looking at *more* evidence is answering a different
question in the same verdict format.

**The role envelope.** Both narrow failures come from missing the same
thing — the surrounding *role*, not the whole career. So the payload is
the STAR snippet plus a bounded envelope drawn from that one role:

| Field | Why it is in |
|---|---|
| Actual title held | The thing the claimed title is being compared against |
| Dates / tenure | "Led the function" reads differently at 18 months than at 6 years |
| Reporting line | The single strongest scope signal, and the false-PASS fix |
| Team size / direct reports | The false-FAIL fix; management evidence often sits outside the STAR entry |
| Sibling bullets from the same role | Evidence for the claim that the gate did not happen to extract |

Nothing from adjacent roles, nothing from the career arc, no seniority
trajectory. Target roughly 300 words. If the envelope runs long, cut
sibling bullets that bear on other competencies before cutting any of
the four structural fields — those four are what the judgment turns on.

## Redaction

Employer and client names substitute to stable placeholders before the
prompt goes into the Telegram message. Keep the per-application
substitution table alongside the change-log entry so the answer maps
back.

Nothing else is stripped. Responsibilities, scope, seniority signals,
reporting line and headcount all go through intact — a trimmed or
summarised envelope defeats the purpose, since the whole point is that
the second model sees the evidence the judgment rests on.

Names are the one class no Hermes redactor removes. The central redactor
is credential-shaped; the MoA filter adds only emails and delimited
phone numbers. If an employer name should not leave the machine, this
substitution is the only thing that stops it.

```
/moa Is displaying the title "Analytics Lead, Operations" a fair
equivalence, or does it overstate scope?

Actual title held: Analyst II
Tenure in role: Mar 2021 - Aug 2023 (2y 5m)
Reports to: Director of Analytics
Direct reports: 3 analysts (hired 2 of them)

From that role:
- Owned the forecasting and reporting function for [EMPLOYER_1]'s
  operations org; set the methodology the other analysts followed.
- Built the weekly ops dashboard the leadership team ran on.
- Ran the quarterly capacity model used in [CLIENT_1] renewal planning.

Answer PASS or FAIL with one sentence of reasoning.
```

Note what the envelope changes about this specific example: the bare
snippet would likely have drawn a PASS on "set the methodology the other
analysts followed." With the reporting line and headcount visible, the
advisor can weigh a real three-person management scope against a
non-lead formal title — which is the actual question, and one it can now
answer either way on evidence rather than on tone.

## What this does not do

Doesn't touch `05`/`06`/`08`'s content directly, doesn't change how
`10-approval-and-submit`'s approval gate works, doesn't run during
unattended cron sweeps (there's no one there to read the suggestion or
paste the prompt) — a `[BORDERLINE PASS]` flagged during a cron-driven
pipeline sweep just sits in the change-log exactly like any other flag,
surfaced the same way at the next live approval message. This is
additive rigor for the moment a human is actually looking at the
decision, not a new automated gate.
