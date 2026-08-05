# Job-Application Metrics — Full Schema

Every metric this pipeline tracks, grouped by purpose. All of these map
to columns in `shared/applications_db_schema.sql`. Nothing here is
optional to log — a metric that's sometimes missing breaks every
correlation calculation downstream.

## A. Funnel / volume

- Postings discovered (per day/week)
- Postings passing the cheap filter (stage 1)
- Postings queued into the full pipeline
- Applications staged (cleared 09-risk-tactics-gate)
- Applications awaiting approval
- Applications approved & sent
- Applications skipped/rejected by Kene at the approval step
- Applications edited by Kene before sending
- Daily cap utilization — staged ÷ configured daily limit

## B. Timing

- Posting live → discovered (source lag)
- Discovered → staged (pipeline processing time)
- Staged → approval decision (Kene's review latency)
- **Posting live → sent** — the thread's core "speed" claim, tracked directly
- Sent → first response
- Sent → rejection
- Sent → interview request
- Interview request → interview date
- Interview → next round
- Interview → offer
- Posting live → offer (total cycle time)
- Ghosted flag: no response after a configurable window (default 21 days)

## C. Content & tactic flags (per application — this is what makes the tactics testable instead of assumed)

- Exact-phrase mirroring used, and count of phrases
- Title matched to posting (Y/N) + original/displayed pair
- Values-alignment section included (Y/N)
- Count of quantified bullets
- Overall match score (stage 3, %)
- Keyword match score (stage 4, %)
- Structure-mirroring used (Y/N)
- Cover letter word count
- Recruiter addressed by name (Y/N)
- Risk-gate pass count vs fail count (how many tactics had evidence vs got honestly declined)
- Application channel (easy-apply / full form / referral / direct email)
- Source job board
- Company size band, industry, seniority level, remote/hybrid/onsite
- Salary disclosed (Y/N) and range if yes

## D. Outcome rates (all as sent-denominator unless noted)

- Response rate (any reply, including auto-reject)
- Human response rate (excludes auto-generated rejections)
- Screening-call rate
- Interview rate
- Second-round rate (÷ interviews, not ÷ sent)
- Final-round rate
- Offer rate
- Offer-to-acceptance rate
- Rejection rate (pre-interview)
- Rejection rate (post-interview)
- Ghost rate

## E. Correlation checks (what the self-improvement loop actually runs weekly)

- Keyword-match-score bucket vs response rate
- Title-matched vs not — response rate delta
- Exact-phrase count vs response rate
- Time-to-apply (hours since posting) vs response rate
- Values-alignment included vs not — response rate delta
- Company size / industry / seniority vs response rate
- Source board vs response rate
- Overall-match-score vs actual outcome (checks whether stage 3's scoring is well-calibrated)

### Proposal release — staggered, not filtered

All eight checks run **every week**. All eight results are logged every
week. Detection does not change, no metric is dropped, and no dimension
of possible change is removed — this section governs only *when a
proposal reaches Kene*, not whether it is produced.

The problem being solved is approval fatigue, not proposal volume. A
weekly review that surfaces eight diffs at once trains the reader to
type `/skills approve all`, which is functionally the same as having no
approval gate. A review that surfaces two gets read.

So any check clearing its sample-size and effect-size thresholds writes
a row to the proposal queue, and the queue **releases on a four-week
rotation**:

| Week | Released group | Checks |
|---|---|---|
| 1 | Content signal | Keyword-match-score bucket; exact-phrase count |
| 2 | Match calibration | Title-matched vs not; overall-match-score vs outcome |
| 3 | Timing and sourcing | Time-to-apply; source board |
| 4 | Targeting and positioning | Values-alignment included vs not; company size / industry / seniority |

Rules that make this a stagger rather than a filter:

- **Nothing is discarded.** A proposal whose group is not this week's
  waits in the queue. It surfaces on its week, with its original
  detection date recorded so the delay is visible rather than silent.
- **Dedup by proposal identity**, not by run. If the same finding
  re-clears thresholds in a later week, it updates the queued row's
  supporting numbers instead of enqueuing behind itself.
- **Strength escalation.** A queued proposal whose effect size grows
  materially between detection and release is promoted to the next
  release regardless of group — a signal getting stronger is exactly
  the one not to sit on for three weeks.
- **Queue depth is a health metric.** Track it in Section F. A queue
  that keeps growing means proposals are being generated faster than
  they are being decided, which is worth knowing on its own.
- **The rotation is delivery-side only.** Correlation results, sample
  sizes and effect sizes land in the metrics tables the week they are
  computed, whatever the release schedule says. Anything querying the
  data directly sees everything, immediately.

## F. System health (is the pipeline itself working, separate from job-market outcomes)

- Skill self-edit count and what changed
- Cost per submitted application and cost per interview request, from
  `v_cost_per_outcome`. Track the trend, not the absolute: a rising cost
  per interview request with flat spend means targeting is drifting, and
  that is visible long before the monthly bill says anything.
- Spend split by tier. If Tier 3's share of spend is not matched by a
  better reply rate on the applications it touched, that is the tier
  question answered with data instead of intuition.
- Proposal queue depth, and median age of a queued proposal at release — rising depth means findings are outpacing decisions; rising age means a release group is consistently being skipped
- Kene's approval rate — staged packages actually approved vs skipped (a proxy for draft quality; a low rate means the drafts need work, not the job market)
- Approval latency — median time from Telegram ping to Kene's decision
- Risk-gate false-positive rate — cases where Kene manually confirms a FAIL was actually fine, used to recalibrate the gate's evidence threshold
- Open gaps outstanding — `SELECT COUNT(*) FROM open_gaps WHERE resolved = 0`, unresolved flags from `09-risk-tactics-gate` still blocking tactics elsewhere in the pipeline until `07-context-architect` resolves them
