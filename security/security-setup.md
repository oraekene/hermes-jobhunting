# Security Setup — Job-Hunting Pipeline

Three of Hermes's built-in security layers matter specifically for this
system, beyond generic good practice. Here's exactly where each one
applies.

## 1. DM pairing — controls who can approve/submit an application

This pipeline's whole safety model rests on Kene being the one who taps
"approve" in Telegram (`10-approval-and-submit`). That only means
something if the bot only accepts approval replies from Kene.

- Do not use `GATEWAY_ALLOW_ALL_USERS=true`, ever, on this deployment.
- Set an explicit allowlist for Kene's Telegram account in
  `~/.hermes/.env` / `~/.hermes/config.yaml`.
- If this pipeline is later sold as a package (per the separate resale
  conversation), each customer's deployment needs their **own** paired
  Telegram identity — one pairing code per customer, approved via
  `hermes pairing approve telegram <code>`, so Customer A can never see
  or approve Customer B's staged applications. Audit periodically with
  `hermes pairing list`; remove anyone who shouldn't still have access
  with `hermes pairing revoke`.

## 2. Dangerous-command approval — the technical backstop on Rule 1

Hermes checks commands against a curated dangerous-pattern list before
execution and requires explicit approval on a match. The form-submit
action inside `10-approval-and-submit` (the actual click/POST that sends
an application) should be registered so it always triggers this check,
independent of the skill's own Telegram-approval-message logic. Two
independent gates — the skill's own review step and Hermes's own
command-approval — is the point; one of them failing shouldn't be enough
to send something unreviewed.

**Important interaction to know about**: if the terminal backend is set
to a container/sandbox (Docker, Modal, Daytona — see #4 below), Hermes
treats the container boundary itself as the security boundary and skips
dangerous-command approval *inside that sandbox*. That's fine for
isolating what a compromised or buggy tool call can touch on the host
machine, but it is **not** a substitute for the Telegram approval step —
container isolation stops a bad command from damaging Kene's laptop, it
does nothing to stop an unreviewed application from actually being
submitted to an employer. Keep `10-approval-and-submit`'s own
human-approval logic regardless of which terminal backend is configured.

## 3. Technical enforcement of Rule 1 — the pre_tool_call submit-gate hook

Section 2's dangerous-command list is generic — a curated pattern list
that has to work for every Hermes install, not something written for
this pipeline's submit action specifically. This section adds a third,
narrower layer: a Hermes `pre_tool_call` shell hook
(`security/hooks/verify-submit-approval.py`) that watches for a
submit-shaped browser click and vetoes it outright unless the
applications DB shows `approval_decision = 'approve'` for the exact
application `10-approval-and-submit` says it's working on. See the
script's own docstring for exactly how it matches a call and why it
fails closed on any ambiguity.

**Install it:**

```bash
mkdir -p ~/.hermes/agent-hooks
cp security/hooks/verify-submit-approval.py ~/.hermes/agent-hooks/job-hunting-verify-submit-approval.py
chmod +x ~/.hermes/agent-hooks/job-hunting-verify-submit-approval.py
```

Then add a shell hook entry to `~/.hermes/config.yaml`:

```yaml
hooks:
  pre_tool_call:
    - matcher: "browser_click|browser_press|browser_tap"
      command: "python3 ~/.hermes/agent-hooks/job-hunting-verify-submit-approval.py"
      timeout: 5
```

The `matcher` scopes this to the same tool names the script itself
watches (`WATCHED_TOOLS` in the script) — Hermes only spawns the hook
process for a matching tool call in the first place, so every other tool
call (reading a file, calling a research skill, anything non-browser)
never pays for it.

**Three things that will bite you if you skip them:**

- **A crashed or timed-out hook is not the same as a hook that blocked.**
  Hermes logs a warning and continues the agent loop on malformed JSON, a
  non-zero exit, or a timeout — it does **not** treat those as a block.
  The script's own "fail closed" design (block on any internal
  ambiguity) only holds *if the script actually runs and returns valid
  JSON*; a script that never finishes fails open at the platform level
  regardless of what it intended to do. Test it standalone
  (`echo '{"tool_name": "browser_click", "tool_input": {...}, "session_id": "test"}' | python3 verify-submit-approval.py`)
  before trusting it in production, and keep the `timeout` generous
  enough for a cold-start SQLite connection to actually complete.

- Shell hooks need one-time consent before Hermes will run them — the
  first time Hermes sees this exact `(event, command)` pair it prompts
  for approval, then remembers the decision in
  `~/.hermes/shell-hooks-allowlist.json`. That prompt needs a human at a
  TTY. A non-interactive context (the gateway, a cron-triggered run, CI)
  has no one to prompt, so the hook silently stays un-registered and
  just logs a warning unless you use one of the three escape hatches
  first: `hermes --accept-hooks chat` (CLI flag, one run), the
  `HERMES_ACCEPT_HOOKS=1` environment variable, or `hooks_auto_accept:
  true` in `~/.hermes/cli-config.yaml` (a *separate* file from the
  `hooks:` block above, which lives in `config.yaml`). Do this *before*
  the first unattended run that could reach this hook, or you're back
  down to two layers without any warning that the third one never
  turned on. Also worth knowing: the allowlist keys on the exact command
  string, not a hash of the script — editing the script later doesn't
  re-prompt you (`hermes hooks doctor` flags this drift if you want to
  check).
- This hook depends on `10-approval-and-submit` writing
  `shared/.active_application/<session_id>.json` before it opens a form
  (see that skill's step 2). If the marker is missing, the hook fails
  closed and blocks the submit — that's the intended behavior, not a bug
  to work around by loosening the script.

This layer doesn't replace layers 1–2 above; it's there so a single point
of failure in either of them still isn't enough to send something
unreviewed. `10-approval-and-submit/SKILL.md`'s "Why this is a technical
boundary" section describes all three layers together from the skill
side.

## 3b. The DB write gate — enforcing row ownership

`shared/db-concurrency.md` establishes that a delegated subagent writes
no SQL: it leaves a JSON file in `shared/.outbox/` and the parent ingests
those serially. That rule was instruction only, and the likelier way it
fails is not defiance but omission — a subagent knows only what the
parent pasted into its context, so a prompt that drifts leaves a child
that never heard the rule and writes directly, successfully, and
silently.

`security/hooks/verify-db-ownership.py` makes it enforced. **During an
active sweep, only the registered writer session may write to
`applications.db`.** Reads are always allowed.

**Install it:**

```bash
cp security/hooks/verify-db-ownership.py ~/.hermes/agent-hooks/job-hunting-verify-db-ownership.py
chmod +x ~/.hermes/agent-hooks/job-hunting-verify-db-ownership.py
```

```yaml
hooks:
  pre_tool_call:
    - matcher: "browser_click|browser_press|browser_tap"
      command: "python3 ~/.hermes/agent-hooks/job-hunting-verify-submit-approval.py"
      timeout: 5
    - matcher: "bash|shell|python|run_command|str_replace|create_file"
      command: "python3 ~/.hermes/agent-hooks/job-hunting-verify-db-ownership.py"
      timeout: 5
```

**This one fails OPEN, and that is the opposite of section 3 on purpose.**
The submit hook guards an irreversible external action — an application
reaching an employer — so a false negative is unrecoverable and blocking
on ambiguity is correct. This hook guards an internal consistency
property, and a false positive would block a legitimate write partway
through a build, manufacturing exactly the half-built application that
addendum 15 exists to clean up. An unparseable payload, a missing session
id, a stale marker, or a crash in the script itself all allow the write
and log it. The only thing it blocks is the unambiguous case.

Getting that asymmetry backwards in either direction is the mistake to
avoid: a fail-closed ownership hook would wedge the pipeline on its first
edge case, and a fail-open submit hook would be decorative.

**Three notes:**

- **The `matcher` list is broader than the submit hook's** because a
  database can be reached from a shell, a Python call, or a file write.
  It is still a list, so a tool name your install uses and this doesn't
  know about passes through untouched — same caveat, same fix: add it to
  both the matcher and `WATCHED_TOOLS` in the script.
- **Enforcement is off unless a sweep is running.** The parent writes
  `shared/.db_writer_session.json` at sweep start and removes it at the
  end. No marker, no restriction — ordinary single-session work is
  completely unaffected and should not pay for this. Markers older than
  8 hours are ignored, so a parent that dies mid-sweep cannot leave the
  pipeline permanently unable to write.
- **Read the audit log after the first few sweeps.**
  `shared/.db_write_audit.jsonl` records every block. Blocks appearing
  there are good news about the hook and bad news about the prompt: they
  mean children are still trying to write, so the outbox instruction is
  not reaching them. Fix the delegation template rather than settling for
  the hook catching it — a backstop doing the primary job is a backstop
  you will eventually outgrow.

Section 3's hook-consent warning applies here identically: shell hooks
need one-time approval at a TTY, and an unattended run will silently skip
an unapproved hook. Approve both at the same time.

## 4. Container isolation — where the browser automation runs

Browser automation (filling application forms) is exactly the kind of
tool use that benefits from running inside a container rather than
directly on Kene's Windows laptop — a malformed or hostile page shouldn't
get host-level access.

Recommended config:

```yaml
terminal:
  backend: docker
  docker_image: "nikolaik/python-nodejs:python3.11-nodejs20"
  docker_forward_env: []        # explicit allowlist only — keep credentials out
  container_cpu: 1
  container_memory: 5120
  container_disk: 51200
  container_persistent: true    # keep the applications DB and skill state across runs
```

`docker_forward_env: []` matters here specifically: this container is
filling out job applications on public websites, some of which will run
arbitrary third-party JavaScript. Don't forward any API keys or
credentials it doesn't strictly need.

## Skill self-editing write approval

`11-analytics-and-learning` proposes skill edits based on outcome data
(see its SKILL.md). By default Hermes lets the agent write skills freely;
set `skills.write_approval` so proposed edits stage under
`~/.hermes/pending/skills/` instead of applying immediately:

```
hermes config set skills.write_approval true
```

**`skills.write_approval` is a single global boolean.** There is no
per-skill or per-category scoping. Turning it on for this package also
gates every other skill write on the machine — a `blogwatcher` tweak, a
Docker workflow the agent wanted to remember, anything. That is worth
knowing in advance, because unrelated approval prompts read like a bug
and the natural response is to switch the gate off, which silently
removes it from this package too. `memory.write_approval` is the
identical gate for memory writes. Runtime toggle: `/skills approval
on|off`; review with `/skills pending`, `/skills diff <id>`,
`/skills approve <id>`, `/skills reject <id>`.

**What the gate does not cover: curator archival.** Archiving runs
through a different path (`archive_skill`), not `skill_manage`, so
`write_approval: true` protects against unwanted *edits* while leaving
skills fully exposed to being archived out of the index after 90 days of
inactivity. Those are two separate controls and only one of them is a
gate — see `README.md`'s "Curator, adoption, and what can quietly disappear" section for the other.

**Related but independent: `skills.guard_agent_created`.** A content
scanner for credential-harvesting, prompt-injection and exfil patterns
in agent-written skill content, off by default. Recommended **on** for
this package: it handles personal documents, and the scanner is an
approval prompt rather than a refusal, so a false positive costs one
keystroke. Exposure here is narrow — it fires on `skill_manage` writes
only, never on reads, and `shared/` sits outside every skill directory
so the credential templates there are never scanned. The one file inside
a skill directory that could trip it is
`22-contact-enrichment/references/api-key-setup.md`; keep realistic
key shapes out of it and use obvious placeholders (`<PROXYCURL_KEY>`,
not an `sk-`-prefixed sample).

This is deliberately stricter than Hermes's default — a system that's
learning from real employer interactions should have its self-edits
reviewed before they change how it represents Kene to the next employer.

## Backups

`backup-and-recovery.md` surveys every durable artifact in the package and
sorts it into three tiers by rebuild cost: irreplaceable, expensive, and
derived. The short version is that job 8 covers one Tier 1 artifact and is
marked optional, which is the wrong default for the only durable record
this system has — and that the enrichment caches are worth backing up for
a reason unrelated to sentiment, namely that re-running metered lookups
costs actual money.

Two scripts ship with it: `scripts/backup.sh` (cron job 8, nightly) and
`scripts/verify-restore.sh` (job 8b, quarterly). Set
`BACKUP_GPG_RECIPIENT` before the first run — without it the script still
works and warns on every snapshot that the data is unencrypted.

## Connectors on a headless host (S13)

Both packages assume MCP connectors work. On a VPS — which is where this
pipeline actually wants to run, since cron jobs need a machine that stays
up — they frequently do not, and the failure is at OAuth rather than at
the connector.

The problem is structural: OAuth wants a browser and a callback URL, and
a headless host has neither. `mcp/mcp-oauth-remote-gateway` is the
documented path through that. Set it up **before** the pipeline depends
on a connector, not after a cron job starts failing at 3am with an auth
error that reads like a network problem.

`mcp/mcporter` gives a terminal way to list, authenticate and test
connectors without a chat session. Worth running once after setup to
confirm each connector this package needs actually responds:
`himalaya` for email, Google Calendar for interview scheduling, Telegram
for approvals.

Do this at install time. A connector that fails during a discovery sweep
costs a day of the pipeline's output and looks like a bug in the skill
rather than an expired token.
