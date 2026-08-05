# Cost model — model spend

What running this pipeline costs, and what stops it running away.

## The gap

`enrichment-tools-pricing.md` and `free-tier-rotation.md` cover
enrichment API spend well — per-lookup costs, tier ladders, a monthly
allowance, spend joined to outcomes in `enrichment_spend`. That is a
genuine cost model for one input.

**There was no equivalent for model spend, which is the larger number.**
No budget, no per-job estimate, no circuit breaker, nothing that could
answer "what does a month of this cost."

And the exposure kept growing while nobody was counting: **18 cron jobs**
(1–16 plus 8b and 8c), parallel subagent fan-out on every sweep, MoA
advisor calls, a weekly review pass, employer research per posting, and —
newest and hungriest — the stepping-stone engine's per-candidate research
fan-out.

Two wake-gates exist and do real work, and they are not this. A wake gate
is per-job cost *avoidance*: it stops one job doing expensive work when
there is nothing to do. Neither knows what anything costs, neither knows
what the others are spending, and neither can stop a run.

### How the four mechanisms compose (R4)

They stack rather than compete, and each catches a case the others
cannot. Tuning one without knowing the other three exist is how you end
up solving a problem twice:

| Mechanism | Question it answers | Scope |
|---|---|---|
| **Wake gates** (`discovery-wake-gate.py`, `interview-prep-wake-gate.py`) | *Is there anything to do right now?* | One job, per tick |
| **Blueprint `no_agent`** | *Does this need a model at all?* | One job, always |
| **`iteration_budget`** + `execute_code` refunds | *Has this run looped too long?* | One run, mid-flight |
| **This cost model** | *What has the whole pipeline spent this month?* | All jobs, cumulative |

The order matters, because each is cheaper than the one after it. A wake
gate that returns "nothing new" costs a script invocation and zero
tokens — the cheapest possible outcome, and the reason wake gates are
worth writing for high-frequency jobs even though discovery is
individually trivial. `no_agent` is cheaper still where it applies, since
a job that never needed reasoning should not be paying for a model at
all; it is under-used here and worth a look whenever you add a cron job
that only moves data. `iteration_budget` catches the opposite case — work
that legitimately started and then ran away — and its refund behaviour
for `execute_code` means a job doing real deterministic work is not
penalised for the loops that work takes.

**Only this file sees the aggregate.** The other three are all local: a
wake gate that fires correctly a hundred times a day is doing its job
perfectly while the pipeline runs 3× over budget, and nothing in it could
know. That is the specific gap the budget and breaker below fill, and it
is why they do not replace the other three.

**Tune the cheap ones first.** If spend is high, the fix is almost always
a wake gate on a frequent job or `no_agent` on a mechanical one — not a
lower budget, which just stops work later and more disruptively.

## Where the money actually goes

Not evenly. Roughly, per unit of work:

| Work | Relative cost | Why |
|---|---|---|
| Parallel application build | **Highest** | 8 stages × N concurrent children. The one that scales with volume. |
| Stepping-stone candidate research | **High, bursty** | A gap analysis + liquidity probe per candidate, fanned out. Rare, expensive when it fires. |
| Employer research (skill 12) | High | Multi-source, per posting, with a video-transcript pass. |
| Interview prep + question bank | Medium | Bounded by real interviews, so self-limiting. |
| MoA advisor calls | Medium | Multiple models per call by design. |
| Discovery ticks | Low each | 6×/day, 6 days/week — **volume makes this material.** |
| Career pulse, journal, monitors | Low | Short prompts, wake-gated. |

The two ends are what matter. Application builds dominate on any active
week. Discovery is individually trivial and runs 36 times a week, which
is the classic shape of a cost nobody notices.

## Budget

`shared/cost-model.yaml`:

```yaml
model_spend:
  monthly_budget_usd: 40           # null = unlimited, and say so out loud
  currency_note: "USD. Convert for NGN reporting at the month's rate."

  soft_ceilings:
    application_build_usd: 0.60    # one posting, all 8 stages
    employer_research_usd: 0.25
    stepping_stone_replan_usd: 1.50
    discovery_tick_usd: 0.03

  thresholds:
    warn_at_pct: 70                # notify once
    throttle_at_pct: 85            # low-priority jobs stop
    halt_at_pct: 100               # only Kene-initiated work runs

  priority:
    always: [approval-and-submit, interview-prep, offer-comparison]
    throttled: [discovery, company-research, social-discovery, cold-prospecting]
    deferred: [career-path-replan, analytics, weekly-review, monitors]
```

The tiering is the important part and it is not arbitrary: **the things
that never stop are the ones with a deadline attached.** An interview is
on Thursday whether or not the budget is tight. A discovery tick can wait
until the first of the month at essentially no cost — the postings will
still be there, and a search that pauses for three days is a mild
inconvenience where a missed interview prep is a lost opportunity.

## Estimation, not metering

There is no token meter this package can read. So spend is **estimated**,
and the estimate is labelled as one everywhere it appears.

Each job records an estimate against its soft ceiling in `model_spend_log`
after it runs. The estimate is coarse — stage count, delegated child
count, whether a research pass fired — and it will be wrong in either
direction on any single run.

**It does not need to be accurate to be useful.** It needs to catch the
shape of a problem: a week where builds ran 4× the usual count, a
re-plan that fanned out to thirty candidates, a monitor that started
firing hourly. Those show up clearly in a coarse estimate. Precision
would be nice and is not what the absence of this file was costing.

Calibrate quarterly against the real provider bill and adjust the
per-unit constants. One number, four times a year, and the estimates stay
roughly honest.

## The circuit breaker

At each threshold, in order:

1. **70%** — notify once, with the breakdown by job. Once. A budget
   warning repeated daily is a budget warning nobody reads.
2. **85%** — `throttled` jobs stop. Discovery drops to once daily instead
   of six times. `deferred` jobs stop entirely. `always` jobs untouched.
   Kene is told what stopped and what it would take to resume.
3. **100%** — only Kene-initiated work runs. No cron job fires. The
   pipeline still responds normally to anything he asks for directly.

**A single run is never killed mid-flight.** A build halted at stage 5
leaves exactly the half-built application that addendum 15 exists to
clean up, and spending the remaining three stages is cheaper than
producing a mess. The breaker stops *new* work; in-flight work finishes.

**Nothing here can stop `10-approval-and-submit`.** An application Kene
has approved gets submitted regardless of budget state. A cost control
that could silently block a submission would be a worse bug than any
overspend it prevented.

## Reporting

`11-analytics-and-learning`'s weekly review gains a spend section:
estimated month-to-date against budget, the three most expensive job
categories, and cost-per-application-sent — which is the number that
actually means something, since 40 dollars is cheap for twelve
applications and expensive for two.

Where `enrichment_spend` already joins enrichment cost to outcomes, this
joins model cost to the same outcomes, so the combined per-application
figure is answerable rather than split across two systems that don't talk.

## What this does not do

- **It does not meter.** Every number is an estimate from a coarse model.
  Treating the running total as a bill is the main way to misuse this.
- **It does not cover the Hermes host, storage, or enrichment APIs.**
  Enrichment has its own model, and conflating them would hide which one
  is growing.
- **It does not optimise anything.** No prompt shortening, no model
  downgrading under pressure, no automatic switch to a cheaper model.
  Quietly degrading output quality to stay under budget is a decision
  Kene should make deliberately, if at all — a pipeline that gets worse
  without saying so is worse than one that stops and explains why.
