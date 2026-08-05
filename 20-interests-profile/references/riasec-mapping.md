# RIASEC Mapping — deriving a matchable interest signal without flattening the profile

Companion to `20-interests-profile/SKILL.md`, same relationship
`content-model-overlap.md` has to `19-career-path-planner`: rich,
specific, evidence-cited content stays the primary representation;
a standardized structure gets derived underneath it only for the one
job standardization is genuinely good at — comparing against every
O*NET occupation on the same terms.

## What gets pulled, additively, alongside the Content Model addition

O*NET already publishes a sixth Content Model domain most of this
package hasn't touched yet: **Occupational Interests** — every
occupation rated against Holland's six RIASEC types (Realistic,
Investigative, Artistic, Social, Enterprising, Conventional), the same
domain O*NET's own Interest Profiler links its 3-letter codes back to.
Same additive pattern as `content-model-overlap.md`'s change to
`title_taxonomy_builder.py` — one more field on the same existing
record, not a new database:

```yaml
# further addition to the record schema title-taxonomy.md defines,
# alongside the content_model field content-model-overlap.md added
riasec:
  realistic:      2.8   # 1-7 scale, O*NET's own rating convention
  investigative:  4.1
  artistic:       1.9
  social:         3.0
  enterprising:   2.2
  conventional:   2.5
```

## Mapping Kene's side — derived from the narrative entries, not a survey

**Deliberately not** administering O*NET's own 30/60-item survey to
Kene and scoring it — that would just be rebuilding the tool this skill
was explicitly built to be a different shape than. Instead, each
confirmed `interests-profile.md` entry gets mapped to whichever RIASEC
type(s) it most plausibly expresses — a judgment call
(`delegate_task`-scale, not `execute_code`), proposed by Hermes and
confirmed in the same batched pass `content-model-overlap.md` uses for
skill mappings, not a second interview:

- A sustained side project building something technical → weighted
  toward Investigative/Realistic.
- Volunteer work organizing people → Social/Enterprising.
- A childhood interest in drawing, still present as an adult hobby →
  Artistic.
- "Things people noticed and complimented" often carries useful signal
  precisely *because* it's other people's read, not Kene's own — worth
  weighting those mappings' confidence differently (an outside
  observation and a self-reported hobby aren't the same strength of
  evidence, even though both are genuine).

Kene's own six-value RIASEC vector is the weighted aggregate across all
confirmed entries, recomputed whenever `interests-profile.md` changes —
same career-event cascade trigger `content-model-overlap.md` and Phase
1.5 already share, one more consumer of the same re-fire point.

## The score

`interest_fit_score` between Kene and a candidate occupation: distance
between his six-value RIASEC vector and the occupation's own —
`execute_code` arithmetic once both vectors exist, same reasoning
`content-model-overlap.md` already applied to its own overlap
computation. Kept as its own independent score, never blended into
`transferable_skill_score` or the whole-text embedding similarity —
three genuinely different questions ("would you enjoy this," "could you
actually do this," "does your overall profile read similar to this")
that happen to often correlate, but conflating them into one number
would hide exactly the cases worth seeing separately — a role Kene
would love but isn't yet equipped for reads completely differently from
one he's equipped for but wouldn't enjoy, and both are useful things to
know on their own terms.

## Where this plugs in

`19-career-path-planner`'s Step 1.5 and mode (e) — see that skill's own
file for how `interest_fit_score` gets used once it exists.
