# Discovery Query Design

How `social_listening` actually decides what to search for. Kene's own
framing is the right one to start from: social posts don't use job-board
language, the phrasing space indicating "I need someone" is close to
unbounded, and a fixed keyword list will systematically miss the
oblique/informal cases — "anyone know someone who can just handle X,"
"drowning in Y, send help," a reply buried three levels into an unrelated
thread. Query generation has to be genuinely creative, not just broad.

## Three sources, always coexisting

### 1. Manual (Kene-set)

Exact queries, hashtags, subreddits, or accounts to watch — entered
directly, full control, no generation involved. Always available
regardless of how good the other two get; this is a floor, not a
fallback that gets deprecated once auto-generation works.

### 2. Hermes-generated

Drafted from Kene's full profile (`target-profile.yaml`'s titles/
variants, `domain-knowledge.md`, the STAR bank) — not literal keyword
matching against his title, deliberately expansive: role synonyms,
task-phrased variants ("need someone who can build X" for a skill Kene
has, not just "hiring for X"), industry-specific phrasing, and informal/
oblique phrasings a recruiter would never use but an individual founder
or small-team lead might. Generation should explicitly optimize for
recall over precision at this stage — a query that's a little too broad
gets filtered by the CTA-classification step downstream anyway; a query
that's too narrow just never surfaces the post at all, which is the
worse failure mode here.

### 3. Example-guided

Kene pastes real posts he's seen — leads, near-misses, or even posts he
wishes had been caught earlier. Hermes generates queries by
**generalizing the pattern**, not by re-searching the example's literal
words: if the example is "ugh I really need someone who can just take
this off my plate, anyone free?", the useful generalization is the
*shape* (informal, first-person overwhelm framing, no job-posting
vocabulary at all) applied across Kene's own skill areas, not a query
for that exact sentence. This is the source most directly responsive to
"the model has to be broadly creative" — real examples are the best
grounding for what "broad" should actually mean for this specific
person's target space, better than either pure manual or pure
Hermes-generated alone.

## Self-improvement loop — recommended, tying into what already exists

Kene's own instinct here is right, and it's not a new mechanism to
build — it's the same propose-and-approve loop `11-analytics-and-
learning` already runs for tactics, applied to queries instead. Track,
per query: posts returned, how many cleared CTA classification as
`apply_link`/`dm_instructions`/`email_instructions`/`reply_instructions`
vs. `unclear`/irrelevant, and how many of those led anywhere
(`social_outreach.reply_type`/`applications.outcome` — the two tables
name the same concept differently, and `social_outreach` has no `outcome`
column). Low-yield queries get
proposed for retirement or rewording; high-yield ones get proposed as
templates for generating *more* queries in the same shape — same
`skill_self_edits` staging, same "propose, don't silently change,"
regardless of source (auto-generated queries get tuned automatically;
Kene's own manual queries get the same performance visibility but are
never auto-edited without him choosing to accept a suggestion — his
queries are his queries).

## Schema

Ships as `shared/discovery_queries.yaml.template` (copy to
`discovery_queries.yaml` before first use — caught missing in a later
audit pass and actually created then, not just described here):

```yaml
- id: ""
  source: ""              # manual | hermes_generated | example_guided
  platform: ""
  query_text: ""
  origin_example: ""       # the pasted post that prompted this, if
                             # source: example_guided
  status: "active"         # active | paused | retired
  performance:
    posts_returned: 0
    classified_relevant: 0   # apply_link + dm/email/reply_instructions
    led_to_outcome: 0         # fed into a real application or outreach
                                # record that got a reply/progressed
    last_evaluated_at: null
  created_at: ""
```

Correlation logic lives in `11-analytics-and-learning`, reading this
file against `social_outreach` and `applications` outcomes — no new
table needed beyond this YAML file itself, same "config lives in YAML,
attempts/outcomes live in SQLite" split the rest of this pipeline
already uses.
