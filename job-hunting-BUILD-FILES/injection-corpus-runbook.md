# Injection Corpus Runbook — the weekly 60–90 minutes

You asked whether you personally have to research and curate all of this. Yes —
the collection is automated, the judgement is not, and it should stay that way.
An LLM deciding on its own what counts as a security pattern and shipping it to
every install is the single riskiest automation available in this whole plan.

Budget 60–90 minutes a week. Below is the actual sitting-down process.

## Step 0 — Automated collection (runs before you sit down)

A server cron fills a review queue overnight. Nothing here needs you.

**Your own fleet telemetry.** Every pattern-fired event, plus — and this is the
best source you have — a *suspicious but unmatched* bucket: inputs that tripped
generic heuristics (imperative verbs addressed to an assistant, long encoded
blobs, unusual unicode, instruction-shaped text inside a job description)
without matching any known pattern. These are attacks in your actual domain that
nobody else has seen, and no public feed will ever carry them.

**Public feeds.** GitHub Security Advisories tagged AI/LLM; the OWASP LLM Top 10
repository; `promptfoo` and `garak` pattern updates; Simon Willison's
prompt-injection tag; arXiv cs.CR new submissions filtered for "prompt
injection" and "indirect injection".

**Platform changelogs.** Greenhouse, Lever, Workday, Ashby status pages and
release notes, watched for anything about content sanitisation.

> **Good output:** 5–30 queued items.
> **Bad output:** zero items two weeks running. Your collectors broke — check
> the feeds before concluding the internet went quiet.

## Step 1 — Triage (15 min)

Discard anything that cannot reach one of the four boundaries: `posting_text`,
`email_body`, `dm_reply`, `fetched_page`. Most published injection research
targets chat interfaces or RAG systems and is structurally unable to reach this
pipeline.

> **Failure mode to watch:** adding patterns for attacks that are impossible
> against your architecture. Every one is pure false-positive risk with zero
> benefit, and they accumulate silently because they never fire.

## Step 2 — Reproduce (30 min)

For each survivor, write the attack into a fixture — a fake posting or email
body — and run it through a throwaway install. `promptfoo` is a reasonable
harness.

> **Good output:** it either succeeds (real, patternable) or fails (already
> covered — record *why*, don't add a pattern).
>
> **Never add a pattern for something you have not reproduced.** Unreproduced
> patterns are exactly how corpora rot: they never fire, nobody dares remove
> them, and eventually the file is 400 lines of folklore.

`check_patterns.py` enforces this — a missing `reproduced` date fails the build.

## Step 3 — Write the pattern (20 min)

One entry in `patterns.yaml`: id, matcher, severity, boundaries, a one-line
plain-language user message, and — mandatory — one positive fixture proving it
fires plus **at least two negative fixtures** proving it does not fire on
legitimate text.

An LLM can draft the regex. You read every one.

> **Bad output to catch here:** a pattern that matches ordinary posting
> language. Real postings say "ignore prior experience requirements" and
> "disregard the earlier salary range" constantly.

**The checker caught three defects in the seed corpus, which is the point:**

| Pattern | Defect | Fix |
|---|---|---|
| `INJ-005` | positive fixture was a placeholder, not a payload | real encoded blob |
| `INJ-006` | fired on *"update your permissions with the security team"* | narrowed the object to automation-specific terms only |
| `INJ-007` | fired on *"send your resume to careers@company.example"* — which **is** the normal flow | demoted to `composite`: the regex is stage 1, an off-domain destination check is stage 2, and the regex may never be used alone |

`INJ-007` is the instructive one. A pattern that cannot work standalone should
be *declared* as needing runtime context, not shipped as a regex and hoped
about. The checker now fails any composite pattern with no stage-2 rule.

## Step 4 — Regression run (automated, 5 min)

New corpus against every fixture plus a large sample of real benign postings.

**The build fails if the benign false-positive rate rises at all.** Not "stays
low" — the budget is zero. A corpus that cries wolf gets switched off by the
user, and then it protects nothing.

```
python3 check_patterns.py
```

## Step 5 — Sign and canary

Sign the corpus. Publish to a canary group — your own install plus a handful of
opted-in users — for 48 hours before the fleet.

> **Bad output:** canary false-positive reports. Pull it. Do not push through.

## Step 6 — Retire (quarterly)

Drop any pattern with zero fleet-wide fires in 90 days and no active
exploitation evidence. Corpora that only grow eventually become unusable, and
the retirement pass is what keeps step 4 achievable.

## The entry that matters most

`INJ-006` — text instructing the tool to change its own approval settings.

This is the attack your permission design is directly exposed to: a posting
persuades the agent to write `auto_approve` into the policy file, and the submit
hook then reads that same file and waves everything through. Detection is the
*second* line of defence. The first is architectural, and it is in the gate
registry already: the policy file lives outside the agent's writable directory,
it is checksummed at session start, and a mid-session change fails closed.

Defence in depth means both. Neither alone is enough.

## What this deliberately does not do

- **Never auto-applies.** Patterns install as signed data; nothing changes a
  code path.
- **Never lets an LLM be the sole gate** on shipping a security change.
- **Never sends matched content home.** Telemetry is pattern id plus
  fired/not-fired. The matched text is third-party writing and often personal
  data — it stays on the user's machine.

## Files

| File | What it is |
|---|---|
| `patterns.yaml` | The corpus: 7 seed patterns, schema, fixtures |
| `check_patterns.py` | Step 4 — the regression gate |
