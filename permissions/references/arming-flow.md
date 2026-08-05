# Arming an irreversible gate

## Why there is an extra step

A typed phrase defends against a careless human. It does not defend against a
prompt injection.

The phrase is written in the source. Any text that can make the agent run a
command can make it run the command *with the phrase* — and the text can arrive
inside a scraped job posting, which is untrusted input this pipeline handles by
design. A confirmation the agent can supply on its own is not a confirmation.

So arming takes two steps, and the second one leaves the machine.

## The flow

1. **Request.** `arm GATE --phrase "I accept the risk"` mints a six-digit code
   and writes it to `~/.hermes/.arm-outbound` for the notifier to send.
2. **Delivery.** The code goes to the approval channel — the user's own phone.
   **It is never returned to the calling process.** That is the whole mechanism:
   injected text cannot predict a code generated after it was written, and
   cannot read a message sent to a phone.
3. **Redemption.** The user sends it back. `arm GATE --code 123456`.
4. **Effect.** Auto-approval for thirty days, then it lapses.

The message the user receives names the setting and says what to do if they did
not ask for it. Someone who receives an unexpected code has just been told an
attack is in progress, in language they can act on.

## Deliberate hard edges

**One attempt.** A wrong code cancels the whole request rather than allowing a
retry. Six digits with unlimited attempts is not a secret; six digits with one
attempt is. If they mistype, they ask again and get a new code — mildly annoying
and much safer.

**Ten minutes.** Long enough to find your phone, short enough that a code left
in a chat log is worthless by the time anyone finds it.

**Scoped to one gate.** A code for one setting cannot arm another. Same shape as
dcg's allow-once: short, single-use, expiring, and tied to one specific action.

**Thirty days, then it lapses.** Not a nag — the failure mode it prevents is
real. *I turned this on in March and forgot* is where the accidents live, and a
permanent switch is exactly how they happen.

**The cap never lifts.** The daily limit binds whether or not a gate is armed.
With the asking removed, the cap is the only thing between a bug and a full day
of unreviewed output going out under someone's name.

**Everything is recorded.** `audit` shows every change with a timestamp. This is
for the user, not for you — when they ask *why did you send that without
asking*, the record is a kinder answer than an argument.

## The two that never arm

`GATE-DM-PAIRING` and `GATE-SENSITIVE-DISCLOSURE` refuse regardless of any code.
Not a trust judgement — these are the two whose failure lands on someone who
never agreed to use this product. One protects every other approval from being
sent by the wrong account; the other stops the tool outing someone to an
employer.

## What the policy file is, and where

`~/.hermes/job-hunting-policy.yaml`, **outside the working directory**,
checksummed at session start. An edit made anywhere other than through this tool
fails closed: the next check reports the change and asks anyway.

That is the point of the location. A gate that reads a file the agent can write
is not a gate — it is a suggestion with extra steps.
