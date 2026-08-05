---
name: job-hunting-keyword-analysis
description: "ATS keyword extraction and match scoring for one JD"
metadata:
  hermes:
    tags: [job-hunting, keyword-analysis]
    category: job-hunting
    related_skills:
      - job-hunting-jd-parser
      - job-hunting-resume-match
      - job-hunting-resume-customizer
---

# ATS Keyword Analysis

## When this skill applies

Use this skill to run a strict ATS-style keyword extraction and match analysis between a job description and Kene's resume, producing a weighted JSON score. Triggers: 'run keyword analysis', 'ATS score this', or being handed a JD + resume by the orchestrator after 03-resume-match. Do NOT use this for the holistic fit narrative (that's 03-resume-match) or for deciding what to actually change in the resume (that's 05-resume-customizer, which consumes this skill's JSON output).

Origin: Kene's original "Chat 3A," unchanged in method — it was already
built to simulate an ATS closely. What's new is *why* this stage matters
more than it looks: the Splendor thread's central, best-evidenced claim
is that a generic resume typically hits ~30-40% of a posting's keywords
while a tailored one can hit 85%+, and that gap is often the difference
between a human ever seeing the application at all. This skill is what
makes that number real instead of a guess.

## Process

Follow `references/keyword-json-schema.md` exactly — segmentation into
Core Domain / Hard Requirements / Soft-Bonus, the three keyword
categories (A: Hard Skills & KPIs, B: Domain & Market Context, C:
Role-Specific Soft Skills), the negative constraints (no hallucinated
terms, no generic soft-skill junk keywords, no ungrouped unigrams), the
tech-stack explosion rule, and the weighted scoring formula
(3/2/1 points by category, penalty logic for seniority/industry
mismatches). That file is the source of truth for the scoring mechanics
— don't improvise a different formula.

Output strictly the JSON format defined there. `05-resume-customizer` and
`08-application-qa` both parse this JSON programmatically — free-text
deviation breaks them.

## Logging

Write `match_score_percentage` and the full keyword list to the
applications DB. This is the single most useful field for
`11-analytics-and-learning`'s self-improvement loop, since it's the
number the thread's central claim is actually about — track whether
higher keyword-match scores really do correlate with higher response
rates in Kene's own outcome data, not just in the thread's anecdote.
