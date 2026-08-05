# STAR bank aging — a fixed reading budget instead of a growing file

Solves the scaling problem in `memory/star-story-bank.md` without giving up
the property that makes the current design work.

## The problem, and why the two obvious answers are both wrong

The bank loads whole into context. That is fine at 15 stories and untenable
at 200, and it is a file meant to accumulate across a career.

**Option A — leave it.** Accept the cost. Works until it doesn't, and the
failure is gradual: context fills, other material gets squeezed, and
nothing announces it.

**Option B — index it in qmd and retrieve top-k.** Scales, but gives up the
thing that makes the current design good. With every story present the
model compares all of them and picks the best fit. Top-k returns the most
textually *similar* stories, and the best story for a question is often not
the most similar one — the strongest answer to "tell me about handling
conflict" may be a story that never uses the word.

Both answers trade one property for the other. There is a third shape that
does not.

## The mechanism, adapted from OptMem

`VictorTaelin/OptMem` (MIT) solves the same problem for agent memory
generally. Its core is `_cover`:

> Tile `[0,T)` with aligned power-of-two blocks; keep a block whole iff its
> size is at most `alpha` times its age. Detail decays with age, so recent
> memories stay verbatim and ancient ones collapse. If everything fits,
> nothing is compressed at all.

`cover(T, budget)` binary-searches `alpha` to land on a fixed line budget,
then spends any leftover budget splitting the newest blocks — "spend what
is left on the present, where detail is worth most."

Applied to the STAR bank, the read becomes:

- **Recent stories: verbatim.** Full Situation/Task/Action/Result.
- **Older stories: collapsed into one-line summaries**, in pairs, then
  quads, then eights, the further back they sit.
- **Every story is still represented.** Nothing is invisible — the
  comparison set stays complete, which is exactly what Option B gave up.
- **Fixed token cost** regardless of bank size. OptMem's default of 96
  lines is roughly 8k tokens whether the store holds 100 entries or a
  million.
- **Zoom on demand.** When a summary looks like the right story, expand
  that node to its two halves and keep going down to the raw entry.

So the model still sees the whole bank; it sees the recent part in full and
the distant part in outline, and can pull any outline into full detail when
it matters. That is a better fit for story selection than either loading
everything or retrieving a few.

## Why this suits a career bank specifically

Recency is a genuinely good proxy for relevance here. A STAR story from
last quarter is more likely to be the right answer than one from six years
ago — more current technology, closer to the seniority being applied for,
better recalled in an actual interview. The decay curve is not arbitrary;
it matches how the material is used.

## Implementation notes

- **Storage stays append-only.** OptMem never edits its log; summaries are
  a rebuildable cache. Keep the same split: `star-story-bank.md` remains
  the record, the tiered read is derived and disposable.
- **Summaries are generated once, on merge**, not on every read. A merge
  becomes due when a block's size crosses its age threshold.
- **Rule 5 still applies.** Summarisation is a read-side transformation of
  already-confirmed facts, not a new fact. `07-context-architect` remains
  the only writer of the bank itself.
- **Budget is a reading knob, not a storage knob.** Change it in either
  direction at any time; nothing is recomputed.

## What this does not solve

Stated plainly, because the mechanism is elegant enough to be
over-trusted:

- **Importance is not modelled.** Decay is purely chronological. A
  career-defining story from four years ago collapses on exactly the same
  schedule as a forgettable one from the same week. This is the main
  limitation, and it is why a `pinned` flag matters: any story marked
  pinned should stay verbatim regardless of age. That is a small addition
  and it covers most of the real cases.
- **Urgency is not modelled**, and should not be here. Urgency lives in
  the applications DB with `interview_request_at` and the ghost window.
- **Contradiction is not detected.** That is the Holographic layer's
  `contradict` action, which the package already uses well.

## One adoption caveat if OptMem is used directly

Its integration prompt is explicit that **subagents must never write
memories** — they cannot judge what is already known, so their notes
arrive duplicated and wrong. This package delegates heavily
(`parallel-pipeline-sweep.md`, cold-prospecting research fan-out,
the three-scope intel scrub). Any subagent spawned by this package must
carry that instruction, or a parallel sweep across twelve applications
will write twelve near-identical memories.
