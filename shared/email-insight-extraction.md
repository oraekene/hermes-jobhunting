# Email Insight Extraction

Origin: Kene's request that reading an email not stop at labeling it and
updating the tracker — the body itself often carries something worth
noting (an interviewer's name, a stated format for the call, a deadline,
a specific piece of feedback) that should reach him and, later, feed
interview prep, rather than being read once by the classifier and then
discarded.

**Where this runs**: as an additional pass over a message body **already
being read** by an existing step — never a new, separate email-reading
pass of its own. Both call sites already fetch the full body for their
own reason (discovery needs it to extract postings; the outcome scan
needs it to classify `response_type`), so this rides along at zero extra
`himalaya message read` cost:

- `01-job-discovery`, step 2.3 (reading an `email_label` source) — lower
  value here, since job-alert digests are mostly auto-generated listings,
  but occasionally carry a genuine aside (a recruiter's personal note
  above the auto-listing, a "closes in 48h" flag).
- `11-analytics-and-learning`'s Email-scan outcome detection, step 3 —
  the higher-value call site, since this is where recruiter replies,
  interview scheduling, and feedback actually arrive.

## What counts as an insight

Five categories, each written as its own row in `email_insights`
(`shared/applications_db_schema.sql`) — a single email can produce zero,
one, or several rows:

- **`interview_detail`** — interviewer name(s), stated format (phone
  screen / panel / technical / take-home), stated topics or focus areas,
  round number, platform (Zoom/Meet/phone). The category the future
  interview-prep stage cares about most (see "Where this feeds forward"
  below).
- **`feedback`** — anything evaluative a human actually wrote, not
  auto-generated boilerplate: "the team felt your systems experience was
  strong but wanted more startup-pace examples."
- **`deadline`** — a stated date/window Kene needs to act within
  (respond by, complete a task by, availability requested by).
- **`action_item`** — something Kene needs to actually do (reply with
  availability, complete an assessment, send a reference).
- **`sentiment_signal`** — a read on how warm/cold a reply is, when it's
  not a clean `response_type` classification on its own but is still
  informative (e.g. an enthusiastic personal note attached to a generic
  auto-ack). Lowest-confidence category by nature — flag as `confidence:
  low` unless the wording is genuinely unambiguous.
- **`other`** — anything else that's clearly notable but doesn't fit
  above. Used sparingly; if `other` starts showing up often, that's a
  sign this category list needs a new named entry, not that `other`
  should become a catch-all.

## What does *not* get logged

Auto-generated acknowledgments ("Thanks for applying, we'll be in
touch"), template boilerplate, and anything with no information content
beyond what the `response_type` classification already captures. This
mirrors `11-analytics-and-learning`'s own existing discipline for
outcome classification — silence (no row written) is the default,
not a low-confidence row for everything. A quiet inbox pass that finds
nothing notable should produce zero new rows, not a summary padded out to
look thorough.

## Extraction rule: paraphrase, don't quote

Write `detail_text` as one plain, Kene-readable sentence in your own
words — "Interviewer is Sarah from the platform team; panel round,
focused on system design" — not a copied block of the original email
text. Two reasons, not one: it keeps the digest/tracker readable instead
of pasting raw email fragments back at Kene, and it avoids the DB
accumulating verbatim third-party correspondence (a recruiter's own
written words) beyond what's actually useful to retain.

## Where this surfaces

- **Immediately, in the digest**: any `interview_detail`, `deadline`, or
  `action_item` row gets included in the next Telegram digest/tracker
  notification (the cron digest already described in
  `01-job-discovery`'s step 7 and `11-analytics-and-learning`'s weekly
  digest) — these are the categories where Kene missing it has a real
  cost. `feedback` and `sentiment_signal` rows surface too, but batched
  rather than urgent.
- **On demand**: "what's the latest on the Acme application" should pull
  every `email_insights` row for that `application_id`, not just the
  `applications` table's own status fields.
- **Marked `surfaced_in_digest`** once shown, so the same row doesn't
  repeat in every subsequent digest indefinitely.

## Where this feeds forward: interview prep

`12-company-research`'s own SKILL.md already names this seam: it
explicitly doesn't do interviewer research or anything post-application,
and flags that "if Kene later adds an interview-prep stage, this is the
stage where research pays off hardest." `email_insights` is the other
half of that same seam — a future interview-prep stage's natural inputs
are exactly `12-company-research`'s cached company research plus every
`interview_detail`/`feedback` row logged here for that application. See
`13-interview-prep/SKILL.md` (stub — not yet wired into
`00-orchestrator`) for where this plugs in once built.

## Confidence and the "can be wrong" caveat

Same discipline `11-analytics-and-learning` already applies to
`response_type` classification: this is an LLM read of free text, and
can misread tone or miss context a human catches instantly. `confidence`
exists so a `low`-confidence `sentiment_signal` row doesn't get presented
with the same weight as a `high`-confidence `interview_detail` row that
just states a name and a date. When genuinely unsure whether something
rises to "notable," the default is the same as elsewhere in this
pipeline: don't write the row rather than guess.
