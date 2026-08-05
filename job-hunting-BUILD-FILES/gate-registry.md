# Gate Registry — every human-decision point in the package

38 gates, extracted from the 16 pipeline rules, the three Rule 1 enforcement layers, and every confirm-point across the 25 skills. `gates.yaml` is the machine-readable source of truth; this file is the same data for reading. `check_gates.py` enforces the invariants below on every change.

## The four classes

| Class | Count | Definition | Toggleable |
|---|---|---|---|
| `irreversible_external` | 11 | A real thing happens to a third party and cannot be undone. | Yes — but arm-required, expiring, capped |
| `reversible_external` | 7 | Touches the outside world but is undoable or low-stakes. | Yes, freely |
| `reversible_internal` | 16 | Writes to your own files, memory, config or database. | Mostly yes |
| `structural` | 4 | A mechanical prerequisite, not a permission. | Never |

## The two that can never be switched off

Not a trust judgement. These are the two whose failure lands on someone who never agreed to use this product.

- **`GATE-DM-PAIRING`** — who is allowed to approve. Every other gate in this registry means nothing if any account can send the approval. `GATEWAY_ALLOW_ALL_USERS` must never be true on a deployment of this package, and each customer needs their own paired identity.
- **`GATE-SENSITIVE-DISCLOSURE`** — religion, health, disability, political and organising activity appearing in an outward document. Recording is free and unrestricted; disclosure is always a conscious per-use choice. Automating it would mean the tool outing someone to an employer.

## Switching off an irreversible gate

Five conditions, all enforced by `check_gates.py`:

1. Typed confirmation phrase
2. Own screen, never bundled in a pack toggle
3. Expiry and re-arm
4. Daily cap still enforced
5. Entry written to the audit log

Plus one engineering requirement that is not a policy but a defence. The submit hook reads the policy file. If the agent can write that file, a prompt injection inside a scraped job posting can open every gate at once. So the policy lives outside the agent's working directory, is checksummed at session start, and a mid-session change fails closed.

## Packs

| Pack | Gates | What it covers |
|---|---|---|
| **Sending and submitting** | 5 | Anything that reaches an employer, a recruiter or a stranger. |
| **Publishing under your name** | 5 | Public pages, profile edits, comments and posts. |
| **Spending money and credits** | 2 | Paid lookups and metered platform credits. |
| **Writing to your memory** | 6 | Facts about your career, before they are stored. |
| **Changing how the tool works** | 6 | Targets, templates, volume caps, schedules. |
| **The tool changing itself** | 3 | Skill edits proposed by the learning loop. |
| **Reading the outside world** | 6 | Fetching pages, scanning your inbox, looking up contacts. |
| **System safety** | 3 | Command guards, backups, install integrity. |

## Every gate

### Class A — irreversible, external

| ID | Gate | Owner | Rule | Default | Toggle | Layers |
|---|---|---|---|---|---|---|
| `GATE-SUBMIT-APPLICATION` | Submitting a job application | `10-approval-and-submit/SKILL.md` | Rule 1 | on | **arm** | 3 |
| `GATE-SEND-DM` | Sending a direct message | `14-social-discovery-outreach/SKILL.md` | Rule 6, Rule 12 | on | **arm** | 2 |
| `GATE-SEND-EMAIL` | Sending a cold email | `17-cold-prospecting/SKILL.md` | Rule 1, Rule 8 | on | **arm** | 2 |
| `GATE-SEND-INMAIL` | Spending an InMail credit | `14-social-discovery-outreach/references/inmail-credits.md` | Rule 14 | on | **arm** | 2 |
| `GATE-LINKEDIN-CONNECT` | Sending a connection request | `14-social-discovery-outreach/references/linkedin-connection-flow.md` | Rule 13, Rule 14 | on | **arm** | 2 |
| `GATE-PUBLIC-REPLY` | Commenting publicly under your name | `14-social-discovery-outreach/SKILL.md` | Rule 1 | on | **arm** | 1 |
| `GATE-PROFILE-EDIT` | Editing your live LinkedIn profile | `24-linkedin-profile-optimizer/SKILL.md` | Rule 1 | on | **arm** | 1 |
| `GATE-PORTFOLIO-PUBLISH` | Publishing your portfolio page | `23-portfolio-onepager/references/hosting-and-publish.md` | Rule 1 | on | **arm** | 1 |
| `GATE-TESTIMONIAL-POST` | Posting your results publicly | `(new — outcome-sharing feature)` | Rule 1 | on | — | 2 |
| `GATE-SENSITIVE-DISCLOSURE` | Using sensitive personal information in an outward document | `20-interests-profile/SKILL.md` | Rule 10 | on | — | 1 |
| `GATE-PAID-SPEND` | Spending real money on contact lookups | `22-contact-enrichment/SKILL.md` | — | on | **arm** | 1 |

### Class B — reversible, external

| ID | Gate | Owner | Rule | Default | Toggle | Layers |
|---|---|---|---|---|---|---|
| `GATE-SITE-SESSION` | Driving your logged-in browser session | `shared/site-access-model.md` | — | on | yes | 1 |
| `GATE-INBOX-SCAN` | Reading your email for application outcomes | `11-analytics-and-learning/SKILL.md` | — | off | yes | 1 |
| `GATE-CALENDAR-CREATE` | Creating calendar events | `13-interview-prep/SKILL.md` | — | on | yes | 1 |
| `GATE-RESEARCH-FETCH` | Fetching company and person research | `12-company-research/SKILL.md` | — | off | yes | 1 |
| `GATE-ENRICHMENT-LOOKUP` | Free-tier contact lookups | `22-contact-enrichment/SKILL.md` | — | off | yes | 1 |
| `GATE-SOCIAL-POLL` | Polling social platforms for opportunities | `14-social-discovery-outreach/references/platform-capability-matrix.md` | Rule 6 | off | yes | 1 |
| `GATE-API-KEY-CONNECT` | Connecting a provider API key | `22-contact-enrichment/references/api-key-setup.md` | — | on | — | 1 |

### Class C — reversible, internal

| ID | Gate | Owner | Rule | Default | Toggle | Layers |
|---|---|---|---|---|---|---|
| `GATE-MEMORY-WRITE` | Storing a new fact about your career | `07-context-architect/SKILL.md` | Rule 5 | on | yes | 1 |
| `GATE-STAR-WRITE` | Adding a story to your example bank | `07-context-architect/SKILL.md` | Rule 5 | on | yes | 1 |
| `GATE-VOICE-NUMBER-ECHO` | Confirming numbers from voice notes | `07-context-architect/references/voice-interview-mode.md` | Rule 5 | on | yes | 1 |
| `GATE-FACT-CONFLICT` | Resolving contradictory facts | `07-context-architect/references/fact-conflict-resolution.md` | Rule 5 | on | yes | 1 |
| `GATE-TARGET-PROFILE-WRITE` | Changing your target role and constraints | `07-context-architect/SKILL.md` | Rule 5 | on | yes | 1 |
| `GATE-FIDELITY-MODE` | Changing how strictly claims must be evidenced | `09-risk-tactics-gate/SKILL.md` | Rule 2 | on | — | 1 |
| `GATE-OUTPUT-TEMPLATE-WRITE` | Saving a named output format | `21-output-templates/SKILL.md` | Rule 11 | on | yes | 1 |
| `GATE-PITCH-CONFIRM` | Confirming a service you can deliver | `shared/pitch-catalog.md` | — | on | yes | 1 |
| `GATE-PITCH-WILDCARD` | Confirming a stretch offer | `shared/pitch-catalog.md` | Rule 9 | on | — | 1 |
| `GATE-CALIBRATION-CHANGE` | Changing match-score thresholds | `shared/dynamic-target-calibration.md` | — | off | yes | 1 |
| `GATE-TIER-CONFIG-CHANGE` | Changing your daily volume cap | `shared/tier-config.yaml` | Rule 3 | on | — | 1 |
| `GATE-PIPELINE-PAUSE` | Pausing and resuming the pipeline | `00-orchestrator/SKILL.md` | Rule 15 | on | — | 1 |
| `GATE-SKILL-EDIT` | Applying a change the tool proposes to itself | `11-analytics-and-learning/SKILL.md` | — | on | **arm** | 1 |
| `GATE-GEPA-DEPLOY` | Applying an optimiser-evolved skill | `11-analytics-and-learning/references/gepa-self-evolution.md` | — | on | — | 1 |
| `GATE-SKILL-COMPOSER-WRITE` | Adding a new capability to the tool | `18-skill-composer/SKILL.md` | — | on | — | 1 |
| `GATE-BACKUP-RESTORE` | Restoring from a backup | `security/backup-and-recovery.md` | — | on | — | 1 |

### Class D — structural (not permissions)

| ID | Gate | Owner | Rule | Default | Toggle | Layers |
|---|---|---|---|---|---|---|
| `GATE-DM-PAIRING` | Who is allowed to approve | `security/security-setup.md` | Rule 1 | on | — | 1 |
| `GATE-DANGEROUS-COMMAND` | Destructive command guard | `security/security-setup.md` | — | on | — | 1 |
| `GATE-INSTALL-INTEGRITY` | Install completeness check | `00-orchestrator/scripts/install-check.py` | Rule 0 | on | — | 1 |
| `GATE-PLATFORM-PREREQ` | Platform prerequisites before a send is even possible | `shared/pipeline-rules-addendum.md` | Rule 13 | on | — | 1 |

## Info-panel copy

Every non-structural gate ships both sides of the comparison. This is the content that renders in the settings panel, and it is written once here rather than three times across UI, docs and onboarding.

**Submitting a job application** &nbsp;`GATE-SUBMIT-APPLICATION`

- *On* — A Product Manager role at Acme is filled in and ready. You get a message with the company, the role, a screenshot of the completed form and the list of claims made. Nothing is sent until you reply approve. If you say nothing, it waits.
- *Off* — The same application is submitted the moment it is built — typically within a minute of the posting being found. You find out it went out when it appears in your sent list. If a claim was wrong, it has already reached the employer.

**Sending a direct message** &nbsp;`GATE-SEND-DM`

- *On* — A hiring manager posts that they are hiring. A message is drafted using your pitch catalog and shown to you with the post it responds to. You approve or edit it.
- *Off* — The message sends itself. On a platform where automated sending is against the rules, the account carrying that risk is yours, not the tool's.

**Sending a cold email** &nbsp;`GATE-SEND-EMAIL`

- *On* — A pitch to a company you have researched is drafted, with every claim about their situation traced to a line in the research record. You read it before it sends.
- *Off* — It sends on the research pass's own schedule. A wrong guess about a company's problems is now something you asserted to them in writing.

**Spending an InMail credit** &nbsp;`GATE-SEND-INMAIL`

- *On* — You are told which of your monthly credits this would use and how many remain, before it goes. One InMail per recipient — there is no follow-up without a reply.
- *Off* — Credits are spent as targets are found. A month's allowance can be gone in a day, on recipients you never saw.

**Sending a connection request** &nbsp;`GATE-LINKEDIN-CONNECT`

- *On* — Each request is shown with the note attached, then sent at human pace on your own logged-in session.
- *Off* — Requests go out in batches. LinkedIn's pattern detection is looking for exactly this shape, and the account it acts against is yours.

**Commenting publicly under your name** &nbsp;`GATE-PUBLIC-REPLY`

- *On* — A reply to a public thread is drafted and marked as going up publicly, visible to everyone in that thread, before you approve it.
- *Off* — Comments post themselves under your name where colleagues and future employers can read them.

**Editing your live LinkedIn profile** &nbsp;`GATE-PROFILE-EDIT`

- *On* — Each headline, summary or role change is proposed one at a time with the current text beside the new one.
- *Off* — Your public profile is rewritten. Your network sees the edit activity, and so does your current employer.

**Publishing your portfolio page** &nbsp;`GATE-PORTFOLIO-PUBLISH`

- *On* — The page is built locally and you open it before deciding whether it goes to a public address.
- *Off* — It publishes on build. Anything drawn from memory that you would not have put on a public page is now on one.

**Posting your results publicly** &nbsp;`GATE-TESTIMONIAL-POST`

- *On* — After your sixth interview invite, a short post is drafted in your own writing style with the underlying numbers shown beside it. You edit or discard it.
- *Off* — not available — this gate cannot be switched off

**Using sensitive personal information in an outward document** &nbsp;`GATE-SENSITIVE-DISCLOSURE`

- *On* — A cover letter would mention volunteer work with a religious organisation because it matches the employer's stated values. You are asked, for this one letter, whether to include it.
- *Off* — not available — this gate cannot be switched off

**Spending real money on contact lookups** &nbsp;`GATE-PAID-SPEND`

- *On* — The free cascade runs first — public sources, self-hosted tools, then rotated free tiers, over 325 lookups a month before anything costs money. Only past that are you asked, with the price.
- *Off* — Paid lookups run automatically up to your monthly budget. Set the budget before switching this off; the default is zero, which means nothing spends.

**Driving your logged-in browser session** &nbsp;`GATE-SITE-SESSION`

- *On* — You are told each time the tool needs to act inside a site you are logged into.
- *Off* — It uses your session when it needs to, without saying so each time.

**Reading your email for application outcomes** &nbsp;`GATE-INBOX-SCAN`

- *On* — You confirm each scan. Slower, and outcomes get logged later than they happened.
- *Off* — Rejections and interview invites are detected and logged automatically, so the daily nudge only asks about applications with no email trace at all.

**Creating calendar events** &nbsp;`GATE-CALENDAR-CREATE`

- *On* — An interview is confirmed for Thursday; you are asked before a prep block goes on your calendar.
- *Off* — Prep blocks appear automatically. Anyone who can see your calendar can see them.

**Fetching company and person research** &nbsp;`GATE-RESEARCH-FETCH`

- *On* — You approve each research pass. Applications wait on you.
- *Off* — Research runs and caches per company, feeding the resume, letter and interview prep.

**Free-tier contact lookups** &nbsp;`GATE-ENRICHMENT-LOOKUP`

- *On* — You approve each lookup.
- *Off* — The free cascade runs automatically. No money moves — that is a separate gate.

**Polling social platforms for opportunities** &nbsp;`GATE-SOCIAL-POLL`

- *On* — Listening runs only when you ask.
- *Off* — Scheduled low-frequency scans surface posts worth replying to.

**Connecting a provider API key** &nbsp;`GATE-API-KEY-CONNECT`

- *On* — You connect a key deliberately, once, and it is read from your vault at the point of use.
- *Off* — not available

**Storing a new fact about your career** &nbsp;`GATE-MEMORY-WRITE`

- *On* — A story you tell in passing is read back to you before it is stored, so a detail you misremembered does not become the version used in every future application.
- *Off* — Facts are inferred and stored silently. A wrong figure propagates into resumes and interview answers until you notice it.

**Adding a story to your example bank** &nbsp;`GATE-STAR-WRITE`

- *On* — A story with an unresolved number is either given the number or explicitly marked as having none, before it is saved.
- *Off* — Stories are written as told, gaps included. An interview answer later relies on a figure nobody checked.

**Confirming numbers from voice notes** &nbsp;`GATE-VOICE-NUMBER-ECHO`

- *On* — You say "25% growth over six months" and it is read back as text before anything is written.
- *Off* — A transcription of "25" heard as "225" is stored as a fact and appears on your resume.

**Resolving contradictory facts** &nbsp;`GATE-FACT-CONFLICT`

- *On* — Two different team sizes for the same project are shown side by side and you say which is right.
- *Off* — The newer one wins silently. Both versions may already have gone out to different employers.

**Changing your target role and constraints** &nbsp;`GATE-TARGET-PROFILE-WRITE`

- *On* — A suggestion to widen your search to adjacent titles is proposed and you accept or decline it.
- *Off* — The search target drifts on its own. You start seeing roles you would not have chosen.

**Changing how strictly claims must be evidenced** &nbsp;`GATE-FIDELITY-MODE`

- *On* — strict — every claim cites a specific line in your resume, portfolio or story bank. Where no evidence exists the tactic is dropped and the gap is flagged to you.
- *Off* — embellish — claims may be extended past what the evidence states. What goes out is something you may have to defend in an interview without anything on file behind it.

**Saving a named output format** &nbsp;`GATE-OUTPUT-TEMPLATE-WRITE`

- *On* — A structure you asked for once is confirmed before it becomes the default for that output type.
- *Off* — Formats are saved as inferred. Later outputs follow a shape you never chose.

**Confirming a service you can deliver** &nbsp;`GATE-PITCH-CONFIRM`

- *On* — Each catalog entry is confirmed with its evidence before it can appear in a pitch.
- *Off* — Entries are inferred from your history. A pitch offers something you would rather not have promised.

**Confirming a stretch offer** &nbsp;`GATE-PITCH-WILDCARD`

- *On* — A stretch capability is confirmed separately, in its own conversation, and tagged wherever it is used.
- *Off* — not available

**Changing match-score thresholds** &nbsp;`GATE-CALIBRATION-CHANGE`

- *On* — You approve each threshold change.
- *Off* — Thresholds adjust to what is actually landing responses. Ships at 70 minimum, 50 stretch — 55/35 if you are starting out.

**Changing your daily volume cap** &nbsp;`GATE-TIER-CONFIG-CHANGE`

- *On* — A change to how many applications get built per day is your decision.
- *Off* — not available

**Pausing and resuming the pipeline** &nbsp;`GATE-PIPELINE-PAUSE`

- *On* — Pausing and resuming are always your call, and a pause has a visible expiry.
- *Off* — not available

**Applying a change the tool proposes to itself** &nbsp;`GATE-SKILL-EDIT`

- *On* — "Values-alignment section shows no response-rate difference over 40 applications — recommend making it optional." You read the proposed edit and the numbers behind it before it takes effect.
- *Off* — The tool rewrites its own instructions weekly on its own evidence. When output quality changes you will not know which edit did it.

**Applying an optimiser-evolved skill** &nbsp;`GATE-GEPA-DEPLOY`

- *On* — An evolved version is produced as a file to diff and read. You apply it by hand or not at all.
- *Off* — not available

**Adding a new capability to the tool** &nbsp;`GATE-SKILL-COMPOSER-WRITE`

- *On* — A new capability is drafted and shown to you before it is installed.
- *Off* — not available

**Restoring from a backup** &nbsp;`GATE-BACKUP-RESTORE`

- *On* — A restore states what will be overwritten and from which date before it runs.
- *Off* — not available

## What this unlocks

- **Permission-pack UI** — packs, the flat expert list, and the arm-required flow all render from `gates.yaml`.
- **Docs** — the demonstration-led documentation uses `panel.when_on` / `panel.when_off` directly as its worked examples.
- **Manifest** — `PACK-*` ids become the permission surface an addon declares against.
- **Telemetry** — Channel A counts gate decisions by `id`, which is why ids are stable and never reused.

## Findings while building this

**One invariant violation caught and fixed.** `GATE-PORTFOLIO-PUBLISH` was toggleable with no arm requirement and no expiry, while publishing a page built from personal memory to a public URL is plainly irreversible. Now arm-required with a 30-day expiry.

**Rule 2's `fidelity_mode` is a gate, not just a setting.** It governs what your documents are allowed to claim happened, and no skill may change it on its own. It is the only three-value gate in the registry (`strict` / `balanced` / `embellish`, ships `strict`).

**`skills.write_approval` is global and does not cover archival.** It gates every `skill_manage` write behind approval, but archival runs through a separate path — so an adopted skill stays exposed to being archived out of the index after 90 days of inactivity. Two controls, only one of which is a gate.

**A container terminal backend silently disables one Rule 1 layer.** Hermes treats the container boundary as the security boundary and skips dangerous-command approval inside it. That protects the host machine and does nothing to stop an unreviewed application reaching an employer. Worth surfacing in the install check.

**Four gates default to off, deliberately** — inbox scan, research fetch, enrichment lookup, social polling. All are reversible-external, all make the pipeline meaningfully better, and none touches a third party irreversibly. That is the right default shape: friction where it protects someone, absent where it only slows you down.
