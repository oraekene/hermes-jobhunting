# The stepping-stone engine

The intermediate-role system behind `19-career-path-planner` Step 3.5.

Before this file, stepping stones were one bullet in Step 3 — *"if the
`job_zone` delta is more than one band, propose one or two plausible
stepping-stone titles"* — and four columns in
`career_path_plan_stepping_stones` to hold the answer. There was no
trigger beyond the `job_zone` delta, no method for generating a
candidate, no check that the candidate was reachable or that the hop
was worth taking, no per-hop gap analysis, and no rule for what happens
when a hop is achieved, missed, or overtaken by an unplanned offer.

That is a large omission for the part of a career plan that people
actually act on. Nobody applies to the role they want in five years.
They apply to the next one. This file specifies the next one.

---

## 1. The distinction the old design was missing

Step 2's gap analysis produces requirements Kene doesn't yet evidence.
Step 3 turns each into a roadmap item. The bullet that was missing:
**not every gap can be closed outside a role.**

| Class | Definition | Closed by | Example |
|---|---|---|---|
| `self_closable` | Acquirable through Kene's own effort, on his own time, without anyone's permission | A roadmap item | A certification, a shipped side project, a portfolio piece, a published write-up, a language |
| `role_gated` | Acquirable **only** by holding a role that grants it | A stepping stone | Direct reports, budget/P&L authority, a regulated-sector reference, vendor-negotiation history, on-call ownership of a production system at scale, board or exec exposure |
| `tenure_gated` | Acquirable only by elapsed time in a role at a level | Time, in the current role or a hop | "Five years post-qualification", "two full annual planning cycles" |
| `credential_gated` | Requires a sponsor, employer, or institution to act | Either, depending on who sponsors | Visa sponsorship, security clearance, an employer-funded programme, licensure requiring supervised hours |

**Classify every unresolved Step 2 requirement into one of these four
before generating any candidate.** The classification is the trigger, the
candidate filter, and the success criterion for the whole engine — a
stepping stone exists to close `role_gated` and `credential_gated` gaps,
and a plan whose gaps are all `self_closable` does not need one no matter
how many `job_zone` bands it crosses.

Classification is a judgement call, so it is surfaced, not asserted: each
requirement's class is shown to Kene with its reasoning and is
correctable before candidates are generated. A misclassified
`role_gated` gap produces a plan that quietly cannot work, and Kene will
usually spot it faster than the taxonomy will.

---

## 2. When a stepping stone is proposed at all

Four independent triggers. **Any one fires the engine**; the old
`job_zone` rule is now the first of four rather than the only one.

1. **Seniority distance** — `job_zone` delta ≥ 2. The original trigger,
   kept unchanged.
2. **Role-gated gap present** — at least one Step 2 requirement
   classified `role_gated` or `credential_gated`. **This fires
   independently of `job_zone`, including at a delta of zero.** It is the
   most common real case and the old rule missed all of it: Analyst →
   Analytics Lead is often one `job_zone`, and the gap that actually
   blocks it — has never managed anyone — cannot be closed by a side
   project.
3. **Domain distance** — a mode (c) target where whole-text embedding
   similarity is low even though `transferable_skill_score` is high. The
   skills transfer; the sector credibility does not. A bridge role that
   is *familiar work in the new sector* converts a two-variable jump into
   two one-variable moves.
4. **Gap density** — the count of unresolved Step 2 requirements exceeds
   `stepping_stone.gap_density_threshold` (default 8). Not a proxy for
   difficulty so much as for planning horizon: a roadmap with fifteen
   open items is not a plan Kene can start on Monday, and splitting it at
   a real intermediate role is what makes the first third of it
   actionable.

**Suppression.** If every unresolved requirement is `self_closable` and
the `job_zone` delta is ≤ 1, do not propose a stepping stone even if
trigger 4 fires — say so explicitly. "This is a direct move; the gap list
is long but you can close all of it from where you sit" is a genuinely
useful finding and the engine should be willing to return it. Inventing
an intermediate role to look thorough is the failure mode this paragraph
exists to prevent.

---

## 3. Generating candidates

### 3.1 The pool

Occupations from `title-taxonomy.md`'s database, filtered to those
satisfying **all** of:

- `job_zone` between current and target inclusive — or, for trigger 2 at
  delta zero, equal to both.
- Not the current title's own taxonomy record, and not the target's.
- Has a `market_signals` block (an occupation nobody is currently hiring
  for is not a stepping stone; see §4.3).

### 3.2 Two-sided scoring — the core of the engine

A stepping stone is not "the most similar title in between." It has to be
**reachable from where Kene is** *and* **carry him toward the target**.
Those are different measurements and a candidate strong on only one is
worthless — which is exactly why a single similarity ranking, the thing
the old bullet implied, cannot produce one.

For each candidate `S`, between current `C` and target `T`:

```
reachability(C → S)   = transferable_skill_score(C, S)
                        adjusted by the count of S's own requirements
                        Kene already evidences, from a gap analysis of
                        S run the same way Step 2 runs one for T

bridge_value(S → T)   = |{ role_gated ∪ credential_gated gaps of T
                           that S structurally provides }|
                        ÷ |{ role_gated ∪ credential_gated gaps of T }|

residual_gap(S → T)   = the Step 2 gap count that would remain
                        between S and T, once S's own gaps are assumed
                        closed by holding S
```

Ranked by `reachability × bridge_value`, **a product, not a sum** —
deliberately, because a sum lets a candidate that is trivially reachable
but closes nothing beat one that does real work. Zero on either term
should zero the candidate, and a product is the honest way to say that.

`residual_gap` is not a ranking term. It is reported alongside, because
it answers a different question — *how much is left after this hop* —
and folding it into the rank would double-count `bridge_value`.

**`bridge_value` is the term the old design had no equivalent of, and it
is where most of the value is.** It asks the only question that justifies
a detour: *of the things I cannot get where I am, how many does this role
actually hand me?* A candidate scoring 0 on it is not a stepping stone,
however close it sits to both ends — it is a lateral move with extra
steps, and the engine should say so rather than rank it fifth.

Structural provision is evidenced, not assumed: S provides "manages
people" because S's O*NET tasks/`market_signals` say so, and the
supporting element is carried forward as `evidence_ref` the same way
`content-model-overlap.md` §101–115 requires for mode (c) results.
No bare numbers reach Kene.

### 3.3 Depth

Default maximum two hops (`stepping_stone.max_hops`, default 2). A
three-hop plan is a forecast, not a plan — its third hop rests on a
profile two roles from now that nobody can predict, and the re-plan rule
in §6 will regenerate it anyway.

Generate a second hop only when the first hop's `residual_gap` still
trips a trigger from §2. Chain the same scoring: hop 2's `reachability`
is measured from hop 1, not from Kene's current position.

### 3.4 Community-reported paths

`role-transition-intel.md` already scrubs public accounts of
how people actually reached a target role, and the most common
intermediate title between C and T is one of the more reliable things
those accounts contain — it is a fact about someone's résumé rather than
an opinion about their strategy.

Run that scrub with an explicit intermediate-title extraction and use it
in exactly two ways, both additive:

- **Corroboration** — a generated candidate that also appears in
  community accounts gets a `community_corroborated` flag and its
  frequency. It does not get a score bump; the flag is shown next to the
  score, not folded into it.
- **Surfacing** — a title appearing frequently in community accounts that
  the taxonomy pool *missed* is surfaced as a candidate tagged
  `[COMMUNITY-REPORTED]`, with the same hard rule Step 3-extended already
  carries: it can be added, it can never displace or gate a primary
  candidate, and it lives in its own labelled section.

The second case is worth the extra pass on its own. Real transitions run
through job titles the taxonomy does not model well — hybrid roles,
contract or agency bridges, secondments, internal-transfer titles that
exist only inside one employer. Those show up in people's actual
histories and nowhere in O*NET.

---

## 4. Validating a candidate — four checks, all disqualifying

A generated path is a hypothesis. These are the checks that stop the
engine handing Kene a plausible-reading route that does not work.

### 4.1 Monotonicity — is the hop even worth taking?

If `reachability(C → S) ≤ reachability(C → T)`, the stepping stone is
**harder to reach than the target itself**. Discard it and say why. This
is not a hypothetical failure: seniority-band interpolation reliably
produces intermediate titles requiring specialist credentials neither the
current nor the target role needs — a common one is a
professional-services or consulting title sitting between two in-house
roles, which reads as an obvious midpoint and is in practice a harder
door than either end.

### 4.2 Non-regression — what does the hop cost?

Compare S's `market_signals.salary_band_observed` against Kene's current
`salary_floor` from `shared/dynamic-target-calibration.yaml`.

A stepping stone paying below the current floor is **not disqualified** —
sector switches and management-track entry both routinely cost money for
a year or two, and a system that refuses to show that path is less honest
than one that prices it. But it is never presented silently. It is
surfaced as an explicit cost with a number attached, the plan records
`comp_regression_accepted`, and Kene answers it as its own question
rather than as a detail inside a roadmap.

**Interaction with `seniority_floor` (addendum 13).** That table exists to
stop discovery surfacing roles below a level Kene has already held. A
deliberate stepping stone below the floor is the one legitimate exception
to it, and it is exception-by-record rather than by override: the hop
carries `seniority_floor_exemption = 1`, `01-job-discovery` honours the
exemption only for postings matching that specific hop's title while the
plan is active and `active_search_status = 'searching'`, and the floor
stays fully in force for everything else. Nothing about the exemption
survives the plan being abandoned or the hop being achieved.

### 4.3 Market liquidity — does this role exist where Kene is?

A stepping stone nobody is hiring for is not a plan. Two signals:

- `market_signals.source_count` and `current_title_strings_seen` from the
  taxonomy record — is the title string in current use at all?
- A live probe: run the candidate title through `01-job-discovery`'s
  configured sources as a **read-only count**, scoped to Kene's actual
  location and remote preferences from `target-profile.yaml`. No rows are
  written and nothing enters the queue; this is a census, not a search.

Below `stepping_stone.min_liquidity_postings` (default 5 across the
configured sources in 90 days), mark the hop `low_liquidity` and show the
count. Do not discard automatically — a genuinely scarce role may still
be the right target for a patient plan, and Port Harcourt is a thinner
market than the taxonomy's global signal implies, which cuts both ways:
the global count over-promises and the local count under-counts roles
filled through networks rather than boards. Say which number is which.

Low liquidity should also feed back into `17-cold-prospecting`: a role
that exists but is not advertised is a cold-outreach problem, not a
discovery problem, and that is a more useful conclusion than dropping the
hop.

### 4.4 Dwell time — how long before the hop counts?

A stepping stone held for four months does not evidence what it was
chosen to evidence. Estimate a dwell period from the `role_gated` gaps it
is meant to close — a full annual planning cycle for budget ownership,
two review cycles for people management, one full delivery for
end-to-end ownership — and record it as `estimated_dwell_months` with the
specific gap driving it.

Deliberately qualitative and deliberately **not** turned into a plan
completion date. It exists to answer one question at re-evaluation time:
has this hop been held long enough to have done its job, or is it being
counted too early?

---

## 5. Per-hop gap analysis — the roadmap Kene can actually start

**This is the change with the most day-to-day effect.**

Today Step 2 runs against the final target and Step 3's roadmap is the
target's roadmap. On a two-hop plan that is a list of things needed for a
role two moves away — accurate, leverage-ranked, and not actionable this
quarter. It is the standard way career plans fail: everything on the list
is true and none of it is next.

With hops present:

- **Run Step 2 once per hop**, plus once for the final target. Same
  method, same three-way well-evidenced / partial / no-evidence split,
  different right-hand side each time.
- **`career_path_plan_roadmap_items` rows carry a `hop_id`** (nullable —
  null means the item belongs to the final target). One table, one query
  shape, no second roadmap system.
- **The active roadmap is the current hop's roadmap.** Target-level items
  stay visible and stay tracked, in their own section, clearly marked as
  belonging to a later hop. They are not deleted, hidden, or deferred out
  of the record — they are just not what Kene is being asked to work on
  this month.
- **An item required by both a hop and the target gets flagged
  `carries_forward`.** These are the highest-leverage items on the whole
  plan and Step 3's leverage ranking should already surface them, but the
  flag makes the reason legible rather than implicit in a rank number.

---

## 6. Lifecycle — what happens when reality arrives

The old status enum was `not_started | in_progress | achieved`. It had no
way to record any of the four things that actually happen to a career
plan.

### 6.1 Extended statuses

| Status | Meaning |
|---|---|
| `not_started` | Planned, not being pursued yet |
| `in_progress` | Actively searching for or working toward this hop |
| `achieved` | Hop role held, dwell time not yet met |
| `matured` | Hop held **and** `estimated_dwell_months` elapsed **and** its `role_gated` gaps evidenced — this, not `achieved`, is what closes the hop |
| `skipped` | Kene reached the next hop or the target without this one. Not a failure; record it and re-plan |
| `substituted` | A different role than the planned one served the same bridging purpose — the common real case. Records `substituted_by_title` and re-scores `bridge_value` against what he actually took |
| `abandoned` | Deliberately dropped, with a reason |

The `achieved` → `matured` split is the one that stops a plan closing
itself early. Landing the role is not the same as having got what the
role was for, and a system that conflates them will mark a plan complete
three months into a hop chosen for a two-year credential.

### 6.2 Re-plan triggers

A stepping-stone path is regenerated, not merely re-scored, when:

- A hop reaches `matured` — Kene's profile has genuinely changed, and
  every downstream `reachability` and `bridge_value` was computed against
  a profile that no longer exists.
- A hop is `skipped` or `substituted` — the remaining path assumed a
  different starting point.
- `16-career-pulse`'s career-event cascade confirms a profile change big
  enough to move a classification in §1 (most often: a `role_gated` gap
  is now closed because Kene's current role quietly grew into it — the
  single most common way a stepping stone becomes unnecessary).
- The target's taxonomy record changes materially on a monthly refresh —
  new required credential, a shifted `job_zone`.
- 12 months elapse with no hop status change. Not because anything is
  wrong, but because a year-old market read is stale and a plan that
  hasn't moved deserves one honest re-examination rather than silent
  persistence.

Re-planning writes a new row to `career_path_plan_reevaluations` with
`replanned_path = 1` and preserves the superseded path — the point of the
path table in §8 is that "what did I think the route was last year" stays
an answerable question.

### 6.3 Opportunistic advancement

Kene takes a role that was on no path. Detect it from the
`16-career-pulse` cascade, then score it against every active plan the
same way any candidate is scored, and report one of three findings, plain
and unhedged:

- **On-path** — it functions as a hop, whether or not it was named. Mark
  the nearest planned hop `substituted` and re-plan from here.
- **Off-path but neutral** — closes nothing for this target. Say so,
  without editorialising; plenty of good reasons to take a role have
  nothing to do with an active plan, and this engine is not entitled to
  an opinion on them.
- **Regressive** — moves away from the target on both scoring terms. Say
  that too, once, with the specific gaps it does not close. Then leave it
  alone. Repeating it at every re-evaluation turns a useful observation
  into nagging about a decision already made.

---

## 7. Presenting paths — where the one-three-one rule earns its place

`19-career-path-planner` already adopts `communication/one-three-one-rule`
for path choices (S11). Hops are what make that adoption real rather than
formal: with a single path there was nothing to choose between, and a
"choice" between one option and nothing is a rubber stamp.

Generate and present **three paths**, always including the direct one:

1. **Direct** — no hop. Always shown, always scored, even when triggers
   fired. Sometimes the honest answer is that the hop isn't worth it, and
   the direct path has to be on the table for that answer to be available.
2. **Recommended hop path** — highest `reachability × bridge_value`.
3. **Alternative hop path** — the best candidate that differs from (2) on
   a dimension Kene might weigh differently: faster but higher residual
   gap, or slower with a comp regression but a much stronger
   `bridge_value`. A near-identical second-ranked title is not an
   alternative; if no genuinely different path exists, present two and
   say why there is no third.

Then **one recommendation, with the conditions that would change it** —
per the one-three-one rule as already adopted. Naming a preferred path is
the part that makes the analysis useful; the conditions are what keep it
from being a verdict.

Each path is presented with: hop titles and `job_zone`s, per-hop
`reachability`/`bridge_value`/`residual_gap` with their evidence,
estimated dwell, comp trajectory including any regression, liquidity
counts, and community corroboration where present. Every number carries
its evidence — no bare scores, same rule as mode (c).

**The journal is read before any of this is presented**, per the skill's
existing "Read the journal before advising a move" section. A hop that
requires two more years in a role `16-career-pulse` shows as stalled and
unhappy is a materially different proposition from the same hop offered
to someone content where they are, and the engine should not present the
first as though it were the second. Evidence for Kene's judgement, not an
input to a verdict.

---

## 8. Schema

`shared/applications_db_schema_addendum_14.sql`:

- `career_path_plan_paths` — one row per candidate path considered,
  including the direct path and the rejected alternatives, with scores
  and `chosen`. Makes "why this route" answerable a year later.
- `career_path_plan_stepping_stones` — extended in place with `path_id`,
  the three scores, dwell, comp band, liquidity, exemption flag,
  community corroboration, and the widened status enum.
- `career_path_plan_hop_gaps` — the `role_gated` / `credential_gated`
  gaps each hop is meant to close, with an evidenced-at timestamp. This
  is what `matured` is checked against.
- `career_path_plan_roadmap_items` — gains `hop_id`, `gap_class`, and
  `carries_forward` via `ALTER TABLE`.

## 9. Config

`shared/target-profile.yaml`, under a new `stepping_stone` block:

```yaml
stepping_stone:
  max_hops: 2
  gap_density_threshold: 8
  min_liquidity_postings: 5        # across configured sources, 90 days
  liquidity_probe: true            # false = taxonomy signal only, no live probe
  community_intel: true            # §3.4 — off makes the engine taxonomy-only
  allow_comp_regression: ask       # ask | never | allow
```

`ask` is the default for `allow_comp_regression` deliberately. `never`
silently removes a whole class of legitimate career move — every sector
switch and most management-track entries — and a default that hides
options is worse than one that asks a question.

## 10. What this engine does not do

Stated plainly, because the machinery is elaborate enough to be
over-trusted.

- **It does not predict.** Every score is computed against today's
  taxonomy, today's market signal, and today's profile. A two-hop path is
  a current best route, not a forecast, which is why §6.2 regenerates
  rather than tracks.
- **It does not know Kene's constraints.** Family, location, visa,
  health, financial runway, and how much risk this particular year can
  absorb are all invisible to it and all frequently decisive. It produces
  candidates; the constraints are Kene's, and a path he rejects for
  reasons the engine cannot see is not a path the engine got wrong.
- **It does not write anything.** Rule 5 holds without exception here.
  The engine proposes paths, hops, and gap classifications; every one is
  confirmed by Kene, and `07-context-architect` remains the only writer
  of memory. Nothing reaches `target-profile.yaml`'s `title_variants`
  except through Step 5's explicit question.
- **It does not model internal moves well.** A promotion or transfer
  inside a current employer is often the cheapest real stepping stone and
  the taxonomy has almost nothing to say about it — internal titles are
  not standardised and internal openings are not posted anywhere it can
  read. `17-cold-prospecting`'s warm-network path and Kene's own
  knowledge of his employer are both better sources here, and the engine
  should say so rather than fill the space with a market-derived guess.
