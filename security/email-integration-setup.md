# Email Integration Setup — Corrected

Origin: this file previously recommended hunting down a third-party
Gmail MCP server. That was solving the wrong problem — **Hermes ships
its own first-party, maintained email skills**, and its own onboarding
already tells you which one fits which need. This version corrects
that, verified against Hermes's actual bundled `SKILL.md` files and
`himalaya`'s own docs, not just a first-glance search.

## The two things Hermes actually ships

- **`email/himalaya`** (bundled) — a CLI wrapper around IMAP/SMTP,
  built on the well-established open-source `himalaya` project (Rust,
  actively maintained). Setup is a Gmail **App Password**
  (Settings → Security → App Passwords) — no Google Cloud project, no
  OAuth consent screen. Hermes's own `google-workspace` skill
  explicitly tells the agent to route here for email-only needs.
- **`productivity/google-workspace`** (bundled) — Gmail + Calendar +
  Tasks + Sheets + Docs + Drive + Contacts via OAuth2, heavier setup
  (Google Cloud project, consent screen), justified once you need more
  than email.

Hermes's own `google-workspace` skill asks, before doing anything else:
*"What Google services do you need?"* — and if the answer is email
only, its own instructions say to stop and use `himalaya` instead. This
pipeline only needs to **read** an inbox for job alerts and outcome
emails — it never needs Calendar, Drive, or Sheets. So: **use
`himalaya`.** Lighter setup, narrower permission footprint, and it's
what Hermes's own docs point email-only users toward.

**A third option, explicitly not used here**: the optional
`email/agentmail` skill gives the agent its *own* separate inbox — the
wrong shape for this pipeline entirely. Job alerts and outcome emails
land in *Kene's* existing inbox, and application forms need to show
*his* real email address, not an agent-controlled one. `himalaya`
reads the inbox that actually matters; `agentmail` would just be a
second, disconnected mailbox nothing in this pipeline has any reason to
check.

## The one thing neither bundled skill does: Gmail filters

Checked every documented subcommand for both skills — `himalaya`'s
`envelope`/`message`/`flag`/`folder` commands, and
`google-workspace`'s `gmail search/get/send/reply/labels/modify` — and
**neither exposes Gmail's filter (auto-sorting-rule) API.** That's a
Gmail-specific feature (`Settings.filters`), not something IMAP as a
protocol has a concept of, and `google-workspace`'s documented command
set doesn't cover it either.

This turns out not to matter much: **the filter only needs to be
created once.** Creating it isn't a recurring agent task — it's a
2-minute one-time setup, done by hand in Gmail's own web UI
(Settings → Filters and Blocked Addresses → Create a new filter), not
something worth standing up a heavier integration for:

```
Matches: from:(greenhouse.io OR lever.co OR myworkday.com) OR subject:(application OR interview OR offer)
Action: Apply the label "JobHunt"
```

Leave "Skip the Inbox" unchecked — Kene still wants these visible in
the normal inbox, just labeled for the pipeline to find. Everything
*after* that one-time click-through — reading the label, deciding
what's new, marking things processed — is what actually needs to run
repeatedly, and that's exactly what `himalaya` handles.

(If you ever want the agent to manage filters dynamically and
repeatedly — not a one-time setup — that's the case where a
filter-capable third-party Gmail MCP like `@shinzolabs/gmail-mcp`
would actually earn its keep. Not needed for what's being built here;
noting it so the option isn't lost.)

## Setup

```bash
# Gmail: Settings → Security → 2-Step Verification (must be on) →
# App Passwords → generate one for "Mail"

# Pre-built binary (Linux/macOS)
curl -sSL https://raw.githubusercontent.com/pimalaya/himalaya/master/install.sh | PREFIX=~/.local sh
```

`~/.config/himalaya/config.toml`:

```toml
[accounts.gmail]
default = true
email = "kene@gmail.com"
display-name = "Kene"

[accounts.gmail.folder.aliases]
inbox = "INBOX"
jobhunt = "JobHunt"
processed = "JobHunt/Processed"

[accounts.gmail.imap]
host = "imap.gmail.com"
port = 993
login = "kene@gmail.com"
passwd.cmd = "pass show gmail-app-password"   # or any secure secret store

[accounts.gmail.smtp]
host = "smtp.gmail.com"
port = 587
login = "kene@gmail.com"
passwd.cmd = "pass show gmail-app-password"
```

**Use `folder.aliases` (plural, dotted keys) exactly as above.**
Himalaya's docs flag a real footgun here: pre-v1.2.0 examples used a
singular `folder.alias` sub-section, which v1.2.0 silently ignores —
TOML parses fine, the alias just never resolves, and on Gmail this
makes save-to-Sent fail *after* SMTP delivery already succeeded, so a
naive retry-on-failure wrapper would re-send the same email. Not a risk
for a read-only pipeline like this one, but worth getting right before
this skill ever sends anything.

**`passwd.cmd`, upgraded**: `pass show gmail-app-password` above works
with any command that prints the secret to stdout, which is deliberately
generic — but if the optional `security/1password` skill is installed,
point it at the 1Password CLI instead
(`passwd.cmd = "op read op://Private/gmail-app-password/password"`) for
a more auditable, non-plaintext-on-disk credential store than a bare
`pass` entry. Neither is required; either is a real improvement over an
app password sitting in a plaintext config file with no secret manager
at all.

Verify: `himalaya account list`, then `himalaya envelope list --folder INBOX`.

## The one real Gmail-specific gotcha for reading

Gmail exposes labels as top-level IMAP folders (so `--folder JobHunt`
works, and nested labels like `JobHunt/Processed` show up as
subfolders) — but **Gmail's IMAP server doesn't support the `SORT`
capability** that himalaya's `envelope search` query DSL (the
`from:`/`after:`/`subject:` filter syntax) relies on server-side.
Himalaya's own maintainers note Gmail specifically rejects that command
today. Don't build the read step around `envelope search` — use plain
`envelope list --folder JobHunt` (works fine, no SORT needed — it's
just pagination), and do date filtering in the agent's own logic by
comparing each envelope's date against the last run, not in the query.

## Where this plugs into the existing pipeline

- **`01-job-discovery`**'s `email_label` source: `himalaya envelope
  list --folder JobHunt`, then `himalaya message read <id>` per
  result, filtering client-side by date. See that skill's own "Reading
  an `email_label` source" step.
- **`11-analytics-and-learning`**'s email-scan outcome path: same
  `envelope list` + client-side filtering approach, scoped by company
  domain in the from-address rather than a server-side query. See that
  skill's own "Email-scan outcome detection" section.
- Marking something processed without losing its `JobHunt` label:
  `himalaya message copy <id> "JobHunt/Processed"` — Gmail's IMAP
  mapping treats this as adding a second label, not moving the message
  out of the first one (mirrors how Gmail actually handles multi-label
  messages). `himalaya flag add <id> --flag seen` for simple read-state
  tracking.

## Addendum — other providers, checked against current provider docs (2026)

The setup above is Gmail-specific because that's Kene's own mailbox.
For any future reuse of this pipeline on a different address (a
customer's, or Kene's own if he ever switches), the picture is
genuinely different per provider — worth recording accurately rather
than assuming "IMAP is IMAP everywhere":

- **Yahoo (yahoo.com/ymail.com)**: same shape as Gmail — enable IMAP,
  turn on 2-step verification, generate an app password, use it in
  `passwd.cmd` exactly like the Gmail block above. No OAuth needed.
  Simple.
- **Outlook.com / Hotmail / Microsoft 365 (including a custom domain
  hosted on Microsoft 365 / Exchange Online)**: **not simple, and not
  the same as the setup above.** Microsoft fully deprecated Basic
  Authentication — plain password *and* app passwords — for IMAP/SMTP,
  completing the rollout in phases through early-to-mid 2026. A
  `passwd.cmd`-style config like the Gmail block simply won't
  authenticate anymore. Himalaya's `imap.sasl.xoauth2` / `oauth2` config
  can still reach these accounts, but it requires registering an app in
  Azure/Entra ID (client ID, redirect URI, IMAP/SMTP scopes) and
  completing a one-time interactive browser consent to mint the first
  refresh token — which is a real complication for a headless agent
  pipeline like this one, since nothing in the pipeline itself can click
  "Allow" in a browser. Budget for a genuine one-time manual setup step
  here, not a config-file change, if this ever needs to support an
  Outlook/Hotmail/M365 address.
- **Custom domain on a traditional host (cPanel, Zoho Mail, Fastmail,
  self-hosted Postfix/Dovecot, etc.)**: same shape as Gmail/Yahoo —
  plain IMAP/SMTP with a regular or app-specific password, no OAuth.
  Simple, same `passwd.cmd` pattern.
- **Custom domain hosted on Google Workspace**: same as the Gmail block
  above, provided the Workspace admin hasn't disabled app passwords
  org-wide (some admin consoles do, independent of the individual
  user's 2FA settings) — worth a 30-second check before assuming it'll
  work.

The dividing line isn't really "Gmail vs. everyone else" — it's
"providers that still allow app passwords" (Gmail, Yahoo, most
traditional/self-hosted mail) vs. "providers that now require full
OAuth2 with interactive consent" (Microsoft-hosted mail, full stop,
regardless of domain).
