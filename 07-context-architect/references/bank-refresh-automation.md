# Keeping the Bank Fresh — Automated, Sparse, Staged

Origin: Kene's question — can the crawler run "very sparsely, very
infrequently, but repeatedly," so the bank drifts along with how
employers actually change their screening questions over time, without
re-running the full manual three-batch process every time.

**Yes, and I think it's worth building** — the underlying calls are
free and rate-limited by design (the 1-second delay in the script is
being polite, not compensating for a paid quota), so infrequent
automated runs cost nothing and don't risk anyone's rate limits or
goodwill. The one thing worth being careful about is **never letting a
cron job overwrite the live bank unattended** — that's not a hypothetical
risk, it's the same trust boundary `11-analytics-and-learning` already
draws around its own self-editing behavior (`security/security-setup.md`'s
`skills.write_approval`). This design borrows that exact pattern for a
different kind of self-modifying artifact.

## Two different cadences for two different jobs

**Monthly, automated, cheap — the "trickle"**: a small incremental crawl
(20–30 companies, not the full 100+100+100), rotating in whichever
seed-list slugs haven't been hit recently, re-clustered against the
*entire* accumulated raw history (cheap — clustering doesn't need new
network calls), producing a candidate bank. This is what actually
catches "employers are asking more AI-usage questions now than six
months ago" — a new question cluster showing up that didn't exist in
the current live bank is exactly the trend signal you're after.

**Quarterly, semi-manual — the deliberate reseed**: still worth doing by
hand, on purpose, because *discovering new companies to add to
underrepresented tag cells* is a judgment call, not something worth
automating. This is the same three-batch process in `HOW-TO-RUN.md`,
just repeated periodically rather than only once.

## Why staged, not automatic

A cron job silently swapping the live question bank changes what
`07-context-architect` asks about and what `08-application-qa` treats
as a "real" question pattern — that's close enough to
`11-analytics-and-learning`'s self-editing behavior that it deserves the
same discipline: **propose, don't apply**. Concretely:

1. Cron job crawls a small batch, appends to the existing raw jsonl
   (this step is safe to run unattended — it's pure accumulation,
   nothing live changes).
2. `curate` runs against the full accumulated raw history, writing to a
   *candidate* file, never directly to `shared/question_bank.yaml`.
3. `diff --live shared/question_bank.yaml --candidate <candidate file>`
   produces a plain-English summary: what's new, what dropped out of
   the top 100.
4. If the diff is non-trivial (a handful of new questions, at least —
   don't ping Kene over a diff with zero real change), deliver it as a
   Telegram digest, same pattern as the weekly analytics digest.
5. Kene reviews and replies "approve" (or edits the candidate file
   directly, same as the Step 3 human pass in `HOW-TO-RUN.md`).
6. Only then: `promote --candidate <candidate file> --live
   shared/question_bank.yaml` — which also backs up the previous live
   file automatically, so a bad promote is a one-command revert.

## Cron wiring

Add as job #6 in `cron/cron-jobs.md`, monthly, low-traffic hour:

```
hermes cron create "0 5 1 * *" \
  "Run an incremental question-bank refresh: python 07-context-architect/references/question_bank_crawler.py crawl --seed 07-context-architect/templates/seed_companies.yaml --limit 30 --out 07-context-architect/references/question_bank_raw.jsonl --skip-crawled, then curate the full accumulated raw file to a candidate bank, then diff --live shared/question_bank.yaml --candidate <that file>. If the diff shows any new or dropped questions, deliver it as a Telegram digest and wait for approval before running promote. Use [SILENT] if the diff is empty." \
  --skill job-hunting-context-architect
```

## Should you actually do this, or skip it?

My honest read: build it, but don't over-invest in it yet. The
mechanism above is genuinely cheap to run (a few Python subprocess
calls, no new dependencies beyond what `HOW-TO-RUN.md` already needs)
and low-risk (staged, never auto-applied, one-command revert). Where I'd
push back if you wanted to go further: don't add anything fancier than
this — no need for weekly runs, no need for an LLM-based "is this
question genuinely novel" classifier on top of the clustering, no need
to auto-expand the seed list itself. The value here is specifically in
"notice drift early, cheaply" — the deliberate quarterly reseed is still
where the real diversity work happens, and that one benefits from
staying manual.
