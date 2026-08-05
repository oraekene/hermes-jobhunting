---
name: job-hunting-approval-submit
description: "Fill the application form and get approval to submit"
metadata:
  hermes:
    tags: [job-hunting, approval-submit]
    category: job-hunting
    related_skills:
      - job-hunting-risk-tactics-gate
      - job-hunting-analytics
      - job-hunting-orchestrator
---

# Approval & Submit

## When this skill applies

Use this skill for the final stage of every application: filling the actual web form with the approved package, then stopping to get Kene's explicit one-tap approval over Telegram before the submit button is ever pressed. Triggers: a package that has cleared 09-risk-tactics-gate and is ready to go out. Do NOT use this skill to send anything without a logged approval reply tied to that specific application — see shared/pipeline-rules.md Rule 1, which this skill exists to enforce.

This is the one skill in the pipeline that touches a real employer, and
the only one that's allowed to. Everything upstream of this produces a
staged, reviewable package. This skill's whole job is to make the last
step a genuine human decision, not a formality.

## Process

1. Take the approved-and-gated package: `.docx` resume, cover letter,
   application Q&A answers, and the risk-tactics change-log.

   **Re-verify the posting still exists (D10).** Fetch the canonical URL
   before building the approval message. Postings get pulled — filled,
   frozen, or expired — and a staged application for a role that no
   longer exists costs Kene attention on a decision that cannot matter.

   Three signals, and the third is the one that catches most real cases:
   an HTTP 404/410; a listing page that now says filled or closed; and a
   **redirect to the board's index page**, where the fetch *succeeds* and
   only the content tells you the posting is gone. A status-code check
   alone misses that one.

   On a positive signal, set `posting_gone_at` and `posting_gone_signal`,
   drop the application out of the approval queue, and tell Kene in the
   digest rather than in a per-application ping — a pulled posting is
   information, not a decision.

   This matters beyond wasted attention: `v_outcome_eligible` exists
   because a posting that was never submittable is **not** a non-reply.
   Counting it as one understates every reply rate this package measures
   and feeds false correlations to job 5's learning loop.

   **Preflight the submit gate before opening anything.** Confirm that
   the tool names you are about to drive the form with appear in
   `security/hooks/verify-submit-approval.py`'s `WATCHED_TOOLS`. That
   hook fails *closed* on every branch it can see — but it fails *open*
   on any tool name it was never told about, and it does so silently. So
   an install whose toolset uses an unlisted name has no Rule 1 gate and
   no indication that it has none.

   If the tool you would use is not listed: **do not open the form.**
   Report which tool name is missing and stop. Adding a name to that set
   is a thirty-second edit; discovering afterwards that an application
   went out unreviewed is not recoverable. This is the one preflight in
   the package that must never be skipped for convenience.

   The form-fill below operates under `shared/site-access-model.md`'s
   **model 3** — Kene's own authenticated session and browser state,
   driven rather than independently established by Hermes. This was
   always implicitly true, since submitting a real application as Kene
   requires being inside whatever account context the submission expects
   (an ATS login, an email-linked flow). Stating it changes no behaviour
   here and nothing about Rule 1; several skills in this package were
   quietly assuming an access model without any of them saying so, and
   this is that correction.
2. Before opening the posting's form, write
   `shared/.active_application/<session_id>.json` —
   `{"application_id": <id>, "company": "...", "role_title": "...",
   "opened_at": "<timestamp>"}` (`<session_id>` is the current Hermes
   session id). This is what the `pre_tool_call` submit-gate hook (see
   "Why this is a technical boundary" below and
   `security/security-setup.md`) reads to know which application a click
   belongs to — without it, the hook has no application to check approval
   for and blocks by design rather than guessing. Then open the posting's
   actual application form (via the browser tool) and fill every field —
   name/contact from memory, resume upload, cover letter field, free-text
   answers, the works.
3. **Stop before the submit click.** Take a screenshot of the fully
   filled form. Mention its absolute path in the response with the
   literal `[[as_document]]` directive somewhere in the same message
   (Hermes's gateway strips the directive and delivers every media path
   in that response as a downloadable file attachment instead of an
   inline image bubble). **This is not optional formatting** — without
   it, Telegram's `sendPhoto` recompresses the image to roughly 200 KB at
   1280px, and small form-field text becomes exactly hard enough to
   misread at the one moment this system's entire safety model depends
   on Kene actually being able to verify it. The `.docx` resume needs no
   such directive — it already uploads as a native file attachment
   regardless (documents don't go through the lossy image path).
4. Send Kene a Telegram message: company, role, the screenshot (as a
   document, per step 3), the risk-tactics change-log, and one clear
   question — approve, edit, or skip. If `12-company-research`'s cache
   for this company has a flagged Domain signal (see that skill's step
   2.5 — only present when `research/domain-intel` is installed and
   found something worth a second look), lead with that note, before the
   rest of the message — Kene should see it before deciding, not have to
   go dig for it. Say nothing extra when the signal is unremarkable or
   the section is absent; a flag on every application trains Kene to
   ignore all of them. If the change-log has a `[BORDERLINE PASS]` entry
   (see `09-risk-tactics-gate/references/moa-cross-check.md`), include
   the ready-to-paste `/moa <question>` prompt right below that line in
   the message, not just the tag by itself — the whole point is Kene can
   act on it in one copy-paste if he wants a second opinion, not have to
   go compose the question himself. Once the message has actually sent,
   write `status='awaiting_approval'` for this application — this is
   what distinguishes "built" (`status='staged'`, set by
   `09-risk-tactics-gate`) from "Kene has actually been asked."
5. Only on an explicit "approve" reply tied to this specific message
   (not a generic "yes" earlier in the conversation) does this skill
   write `approval_decision = 'approve'` to this application's row in the
   applications DB, **then** press submit. Any other reply — silence,
   "edit," "skip," anything ambiguous — leaves the application in
   `awaiting_approval`, leaves `approval_decision` unset or non-approve,
   and does nothing further. The DB write has to land before the submit
   click, not after — see "Why this is a technical boundary" below for
   why that ordering specifically matters now.
6. Log the outcome (`sent`, `edited_then_sent`, `skipped`) to the
   applications DB immediately — this feeds `11-analytics-and-learning`.

## Why this is a technical boundary, not just a polite pause

Three independent layers have to agree before anything goes out — not
two:

1. **This skill's own approval-message step** (above) — the first line
   of defense, and the only one that's actually reading the reply for
   intent, not just checking a flag.
2. **Hermes's built-in dangerous-command approval** (see
   `security/security-setup.md`) — the submit action is registered as a
   dangerous command, so it requires explicit approval at the platform
   level even if this skill's own logic were ever bypassed or
   mis-triggered by a bad prompt injection from a scraped job posting.
3. **A `pre_tool_call` hook, purpose-built for this specific action** (see
   `security/security-setup.md`'s "Technical enforcement of Rule 1" —
   this is new, added specifically because layer 2 is a generic
   pattern-matched list, not something written for this pipeline's submit
   action in particular). The hook checks the applications DB for
   `approval_decision = 'approve'` on this exact application row before
   letting the browser's submit/click tool call proceed at all, and
   vetoes it outright if that row isn't set — independent of whatever
   this skill's own logic thinks it already confirmed. This is why step 5
   above writes the DB flag *before* attempting the submit click: the
   hook has nothing to check otherwise.

Layer 3 doesn't replace layers 1–2; it's there so a single point of
failure in either of them still isn't enough to send something
unreviewed.

## Rate limits live here, not at the mailbox

The daily volume cap from `README.md` governs how many packages reach
this skill's queue per day — it is not a cap on how fast this skill
sends, because this skill never sends anything on its own. A "200/day"
tier means 200 fully-prepared, reviewed-and-approved-by-a-human packages
can be staged in a day if Kene (or a customer) actually reviews and taps
approve on that many — not 200 unattended submissions.

## What this skill must never do

- Never infer approval from silence, from a prior day's approval, or
  from Kene being "usually fine with these."
- Never batch-approve — each application gets its own message and its
  own explicit reply.
- Never retry a submit after a platform error without re-surfacing the
  form to Kene; a failed submit is not a reason to try a workaround
  automatically.

## The offer stage — comparison and decision (S8, S11)

Rule 1's approval boundary is about *sending*. An offer is the other end
of the pipeline and the higher-stakes decision, and the package handled
it as prose.

**Build the comparison as a workbook** (`finance/excel-author`). Total
compensation across base, bonus, equity grant, vesting schedule,
pension/benefits, and cost-of-living adjustment is a spreadsheet problem
— it has cells, formulas, and a four-year time axis. Prose comparisons of
two offers reliably lose the vesting cliff and the COL difference,
because both are arithmetic rather than narrative.

The workbook is a decision aid, not an answer. It should make the
trade-offs legible — what the equity is worth under three assumptions
rather than one, what the COL-adjusted base actually is — and stop there.
A single "score" per offer would hide exactly the judgement Kene needs to
make himself.

Pull `salary_floor` and any confirmed comp from `target-profile.yaml`
rather than asking again, and pull the company's stage and financial
signal from `company_research_cache` — for a public company, equity is
worth something checkable; for a seed-stage company it is a lottery
ticket with a strike price, and the workbook should say which it is
modelling.

**Frame the decision as one-three-one** (`communication/one-three-one-rule`).
One issue, three options, one recommendation. Career-decision stages
currently produce analysis without a forcing structure, and analysis
without a recommendation quietly hands the hardest part back.

The three options are genuinely three, not one plus two strawmen:
accepting, countering with a specific number and rationale, and declining
or holding for the pipeline's other live applications. The recommendation
names which and says why, in one paragraph — and says what would change
it, because a recommendation whose conditions are unstated cannot be
argued with.

Same shape applies in `capability:career_planning`, where "which path" is the
same class of decision.

