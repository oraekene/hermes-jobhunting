# Message catalog — obscuring made enforceable

`shared/messages.yaml` (41 messages), `shared/scripts/msg.py`, and a test suite.
This is item 9 from your original list — rewriting everything a user sees to
hide how the system works — turned into something a build can check.

## Three audiences, one of which this file serves

| Audience | What they get | Where it lives |
|---|---|---|
| User, ordinary | plain language, no machinery | **here** |
| User, safety-critical | specific about *what happened and what it means for them*, still no machinery | **here** |
| You, support | full detail: file paths, gate ids, stack traces | local log, with a short code the user can quote |

That third row is the reconciliation of your point 4. You wanted everything the
user sees obscured; I said safety messages must stay specific. Both hold, because
**specificity is about consequence, not mechanism**:

> I stopped before sending this. It has not been approved yet, and I do not send
> applications you have not seen.

Completely specific about what happened and why it matters. Mentions no hook, no
table, no rule number. The detail a user needs and the detail you need are
different detail, not different amounts of the same detail.

## The check that makes it real

`msg.py check` fails the build if any user-visible string contains a skill
directory name, gate id, flow id, pack id, file path, rule number, config key or
environment variable. It uses the same detector as the documentation build, so
the two cannot disagree.

Careful writing has no failure mode — it just drifts. This one has 41 messages
and a build step.

The test suite asserts the detector actually fires, which matters more than the
catalog passing: a leak check that never triggers reports "clean" forever.

```
Blocked by Rule 1                caught
see gates.yaml                   caught
GATE-SEND-DM refused             caught
set fidelity_mode                caught
GATEWAY_ALLOW_ALL_USERS          caught
I stopped before sending this.   allowed
```

## Rules the catalog holds itself to

- **Every refusal explains itself.** A message under eight words that says no
  and nothing else fails the check. "Blocked" is not a message.
- **No user-visible string uses the word "error".** Describe the situation.
- **Problem messages carry a quotable code** — `[E01]` — so the user has
  something to give you without ever seeing a path.
- **A missing key never prints the key.** It degrades to a plain apology, so a
  bug in your code cannot become a leak in front of a customer.
- **A missing variable leaves no braces.** Nobody should read `{days}`.

## What the scan found in your package

`msg.py scan` reports **49 candidate strings across 9 skill files** — mostly
sample replies written as block quotes, concentrated in the memory interview
(20) and interview prep (14).

**It reports and changes nothing, deliberately.** Guessing which quoted line is
an emitted message and which is an example for the model would eventually
rewrite an instruction, and that failure is silent — a skill that still reads
convincingly and does something else. Same reasoning as the rationale strip.

The realistic path: move messages into the catalog as you touch those files
anyway, and let the scan tell you where the concentration is. The 41 already in
the catalog cover the pipeline's main emissions, every refusal, the whole
permissions conversation, setup, outcomes, and licensing.

## Two things you get for free

**Translation.** One pass over one file, not a rewrite of 137. Add
`text_ha:`, `text_yo:` beside `text:` and the renderer picks by locale.

**Tone consistency.** Thirty-eight gates and nine skills written over months
drift apart. A catalog does not — and reading all 41 messages together, which
takes two minutes, is the only way to notice that three of them apologise and
one of them nags.

## Usage

```bash
python3 shared/scripts/msg.py get blocked.not_approved
python3 shared/scripts/msg.py get permissions.armed \
        --var label="submitting applications" --var days=30 --var until=2026-09-03
python3 shared/scripts/msg.py check
python3 shared/scripts/msg.py scan .
python3 shared/scripts/msg.py keys --prefix blocked.
```

Wire `check` into the release workflow beside the other five.
