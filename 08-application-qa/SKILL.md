---
name: job-hunting-application-qa
description: "Draft answers to free-text application questions"
metadata:
  hermes:
    tags: [job-hunting, application-qa]
    category: job-hunting
    related_skills:
      - job-hunting-cover-letter
      - job-hunting-context-architect
      - job-hunting-risk-tactics-gate
---

# Application Question Responder

## When this skill applies

Use this skill to draft answers to free-text application questions (e.g. 'why do you want to work here', 'describe a time you handled conflict') using Kene's STAR story bank and the keyword analysis report. Triggers: 'answer this application question', 'draft a response for this form field', or being handed application questions by the orchestrator alongside 04's keyword report. Do NOT use this for the cover letter itself (06-cover-letter) — this is for the extra free-text fields many application forms add beyond the cover letter.

Origin: Kene's original "Chat 5B," unchanged in method. This is where
the STAR story bank built by `07-context-architect` earns its keep —
every answer should read as a specific, lived story, not a generic
statement that could apply to any candidate.

## Process

0. **Check for a matching output template.** Look in
   `shared/output-templates.yaml` for an `artifact_type:
   application_answer` entry whose `trigger_conditions` — question
   category, word-limit range, `variant_dimensions` applicability —
   match the question at hand. No match, and steps 1 onward run exactly
   as written below. A match can override the **output format** only,
   e.g. dropping the Strategy Brief section and showing Kene the Final
   Response alone. A template governs presentation and nothing else:
   never which STAR story gets picked, never which gated keywords get
   woven in.
1. **Classify the question**: technical/skills, behavioral/situational,
   motivation/career goals, domain expertise, personal qualities, or
   cultural fit. Note any stated word/character limit — it's a hard
   constraint, not a suggestion.
2. **Read the psychology**: what is the recruiter actually worried about
   with this question? Answer that underlying concern, not just the
   literal words.
3. **For motivation/career-goals and cultural-fit questions
   specifically** — "why do you want to work here," "what interests you
   about our mission," "how would you approach [X] here" — read
   `shared/company_research_cache/{company_slug}.md`
   (`12-company-research`) before drafting. Behavioral/technical/domain
   questions don't need this step; the STAR bank answers those the same
   way regardless of employer.
4. **Select the story**: pick the single best-fit STAR story from memory
   for this specific prompt — don't generalize across several. If the
   question bank entry (`shared/question_bank.yaml`) has
   `variant_dimensions` set, use the research cache's stage/size signal
   to pick the matching variant (`07-context-architect/references/
   answer-variants.md`), falling back to the JD text alone only when the
   cache has no reliable signal. If the Holographic memory layer is
   configured (optional — see `07-context-architect/references/
   holographic-memory-layer.md`), `fact_store(action="reason",
   entities=[...])` across the company and the question's topic can
   surface a fact connected to both — a supplementary check, not a
   replacement for picking the story from the bank directly.
5. **Weave in keywords**: for any `found_in_resume: false` term in the
   keyword report that clears `09-risk-tactics-gate`, work the exact term
   in naturally (e.g. "managed the Product Roadmap and SDLC," not
   "managed the project schedule"). This is gated the same way as
   `05-resume-customizer` — a genuine `[PASS]` term is woven in as fact;
   an `[UNVERIFIED]` term (`balanced`/`embellish` mode only) is still
   woven in, but flagged the same way in this skill's own change-log
   contribution, so the answer never reads more certain than the
   evidence behind it.
6. **Write in Kene's voice**: first-principles framing, specific project
   names, genuine reflection — not generic corporate phrasing.
7. **Humanizer pass**: run the drafted answer through Hermes's bundled
   `creative/humanizer` skill before handing off — same reasoning and
   same boundary as `06-cover-letter`'s equivalent step: phrasing only,
   never a change to what the answer actually claims. `06-cover-letter/references/anti-slop-checklist.md`'s banned-opener/self-description
   list applies here too, since these answers have the same "sounds like
   40 other applicants" failure mode a cover letter does.

## Revise to a threshold, don't reject at one (S5)

The draft/QA relationship here is pass/fail: an answer either clears or
it doesn't, and one that doesn't gets rejected rather than improved. A
6.5-out-of-10 answer is not a failure to be discarded, it is a draft one
revision away from being good.

`NousResearch/autonovel` runs the same shape as a loop — modify, evaluate,
keep or discard, repeat until the phase score clears its threshold — and
Hermes's own self-evolution pipeline gates candidates the same way before
promoting them. Adopt that here:

1. Draft the answer.
2. Score it on the rubric below, 1-10 per dimension.
3. Below threshold on any dimension → revise **that dimension
   specifically** and re-score. Not a blind rewrite: a blind rewrite
   loses the parts that were already working.
4. Stop at threshold, or after **3 iterations**, whichever comes first.

| Dimension | Threshold | What a low score means |
|---|---|---|
| Specificity | 7 | Generic enough to fit any company |
| Evidence | 8 | The claim has no STAR entry or resume line behind it |
| Relevance | 7 | Answers a question adjacent to the one asked |
| Voice | 6 | Reads as generated — see `06-cover-letter/references/anti-slop-checklist.md` |
| Length discipline | 8 | Over the stated word limit |

**The iteration cap is not decoration.** Three passes that fail to reach
threshold mean the problem is the underlying evidence, not the wording,
and a fourth rewrite is polishing a claim that isn't supported. Stop and
tell Kene which dimension is stuck — that is a useful finding, and it is
usually a gap in the STAR bank rather than a drafting failure.

**Report the final scores** with the answer. A 7 that took three passes
is different from a 7 that took one, and `11-analytics-and-learning` can
correlate score-at-submission against reply rate — which turns the rubric
from an opinion into something testable.

## Output format

```
[Strategy Brief]
Targeted Story: <story name from the bank>
Keywords Injected: <list>
Alignment Strategy: <one line>

[Final Response]
<the exact text for the form field>

[Word/Character Count]
<X> Words / <Y> Characters
```

Strict adherence to the stated limit — under is fine, over is not.
