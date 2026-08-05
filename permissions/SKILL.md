---
name: job-hunting-permissions
description: "Review and change what the tool asks you before doing — permission groups, individual settings, and turning off the asking"
metadata:
  hermes:
    tags: [job-hunting, permissions, settings]
    category: job-hunting
    related_skills:
      - job-hunting-orchestrator
      - job-hunting-onboarding
      - job-hunting-approval-submit
---

## When this skill applies

**Triggers:** "what do you ask me about", "stop asking me before X", "let me
review the permissions", "turn off the confirmations", "why did you ask me
that", "what am I approving", "show me my settings".

**Also fires unprompted, once:** after fifteen approvals with no edits. Someone
who has approved fifteen packages unchanged has demonstrated the friction is
real. Someone still editing every one has not — offering it to them is offering
to remove a check they are visibly still using.

**Does not fire:** during a live approval. If they are mid-decision on an
application, answer the question in front of them. Offer this afterwards.

## The one thing to get right

**This is a conversation, not a form.** There are thirty-eight decision points
and nobody wants to hear about thirty-eight of anything. Find out what is
actually annoying them, fix that, and stop.

The single most common right answer is not switching anything off — it is batch
review. Offer it early.

## Where things live

Everything comes from `shared/gates.yaml` through
`permissions/scripts/permissions.py`. **Never describe a setting from memory and
never edit the policy file directly.** Both go wrong in the same way: the
description drifts from what the code does, and the user's mental model breaks
at the worst possible moment.

```
permissions.py status                      what is on, what is off
permissions.py packs                       the group view
permissions.py list --pack PACK-SENDING    everything in one group
permissions.py list --changed              only what they have altered
permissions.py show GATE-OR-PLAIN-NAME     the panel, both sides
permissions.py set GATE on|off             reversible things
permissions.py arm GATE --phrase "..."     starts the code challenge
permissions.py arm GATE --code 123456      completes it
permissions.py disarm GATE
permissions.py audit                       what has changed, and when
```

`show` accepts plain language, so `show "submitting a job"` works. Use that —
the user says what they mean, not a gate id.

## Process

### 1. Ask what is actually bothering them

Not "would you like to review your permissions". Something like:

> Which part is asking too often?

Then run `status` so you are talking about their real state, and go straight to
the group that covers it. If they genuinely want the tour, run `packs` and let
them pick.

### 2. Offer batch review before anything else

If the friction is about applications specifically:

> I could send five at a time instead of one by one — same review, a fifth of
> the messages. Most people find that fixes it.

**This is the right answer for most people.** It removes nearly all of the
friction and keeps a human on every application. Only move past it if they say
it is not enough.

### 3. Show the setting, both sides, before touching it

Always `show` before `set`. The panel exists so the choice is informed:

> **If I ask you first:** a Product Manager role at Acme is filled in and ready.
> You get the company, the role, a screenshot of the completed form and the
> claims made. Nothing is sent until you reply approve.
>
> **If I stop asking:** the same application is submitted the moment it is
> built. You find out when it appears in your sent list. If a claim was wrong,
> it has already reached the employer.

Then ask. Do not editorialise beyond the panel — it is written to be fair to
both answers, and the decision is theirs.

### 4. Reversible things: just do it

`set GATE off`, confirm in one line, move on. Research fetches, inbox scans,
enrichment lookups, memory writes. No ceremony — ceremony where it is not
needed teaches people to click through the places where it is.

### 5. Irreversible things: the code, and no persuasion

Sending, submitting, publishing, spending. `arm` sends a six-digit code to their
approval channel. They send it back. Then it is off for thirty days.

Say what the extra step is for, once, without lecturing:

> Because this one cannot be undone, I will send a code to your phone rather
> than take my own word for it — that way a stray instruction in a job posting
> can never switch it off.

**Never suggest arming one of these.** Do it when asked; do not sell it. And
never bundle it with something else — its own question, its own answer.

Two things must be said when it succeeds, and the script says both: the daily
limit still applies, and everything done this way is recorded and readable.

### 6. Some things do not move

Two gates cannot be switched off by anyone:

- **who is allowed to approve** — every other setting is meaningless if any
  account can send the approval
- **using sensitive personal information in an outward document** — religion,
  health, disability, political activity. Recording is free; disclosure is
  always a conscious choice, every time.

Say the reason plainly and briefly. Do not apologise for it. Someone asking is
usually satisfied by the reason, and the reason is a good one.

### 7. Leave them a way back

End with the shape of it:

> Any time: *what do you ask me about?* And *what have I changed?* if you want
> just the differences.

## Expiry

Auto-approval on anything irreversible lapses after thirty days and starts
asking again. This is deliberate — *I turned this on in March and forgot* is
where the accidents live.

When it lapses, say so once, plainly, and offer the code again. Do not treat it
as an error, and do not make them feel caught out.

## Reading the audit

`audit` prints what changed and when. Useful when they ask *why did you send
that without asking* — often the answer is that they switched it off three weeks
ago, and the record is kinder than an argument.

## What not to do

- **Do not walk all thirty-eight.** Ever. Find the annoyance, fix it, stop.
- **Do not batch an irreversible gate with anything else.** One question.
- **Do not describe a setting from memory.** Run `show`.
- **Do not persuade.** The panels are written to be fair to both answers.
- **Do not mention gate ids, file names or pack ids to the user.** They see
  labels and plain language. The ids exist for you.
- **Do not offer this during a live approval.** Finish the decision in front of
  you first.

## Reference files

- `references/arming-flow.md` — the code challenge, expiry, and why the extra
  step exists
