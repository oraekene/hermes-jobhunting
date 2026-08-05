#!/usr/bin/env python3
"""
job-hunting submit-gate — a Hermes `pre_tool_call` shell hook.

Purpose (see 10-approval-and-submit/SKILL.md "Why this is a technical
boundary" and security/security-setup.md "Technical enforcement of
Rule 1"): veto a job-application submit click unless the applications DB
shows `approval_decision = 'approve'` for the exact application
10-approval-and-submit is currently working on. This is layer 3 of three
independent layers — it exists specifically because layer 2 (Hermes's
built-in dangerous-command approval) is a generic pattern-matched list,
not something written for this pipeline's submit action in particular.

How Hermes calls this: stdin gets one JSON object per invocation
(hook_event_name, tool_name, tool_input, session_id, cwd, ...). Stdout
must be a single JSON object; `{"action": "block", "message": "..."}`
vetoes the call, anything else (including `{}`) allows it. See
user-guide/features/hooks.md, "pre_tool_call" and "Shell hooks".

Design notes, read before you install this:

- This is a HEURISTIC, not a semantic understanding of the page. It
  watches a small set of tool names and does a keyword match against the
  call's own arguments (selector text / accessible name / button label —
  whatever the tool call includes). Tune WATCHED_TOOLS and
  SUBMIT_KEYWORDS against whatever ATS platforms you actually apply
  through if you see false positives (blocking a legitimate non-submit
  click that happens to say "submit" somewhere) or false negatives (an
  ATS whose submit button says something this list doesn't catch).
- It FAILS CLOSED. Any error — can't parse the hook payload, no active-
  application marker, can't read the DB, no matching row — blocks the
  call rather than letting it through on a guess. A false positive here
  costs you a re-click after checking why; a false negative costs an
  unreviewed application going out. That tradeoff is deliberate.
- It depends on 10-approval-and-submit writing
  shared/.active_application/<session_id>.json BEFORE it opens the form
  (see that skill's step 2). If you're seeing this hook block every
  submit attempt, check that marker is actually being written first —
  don't loosen this script to "just allow it" as the fix.
"""
import json
import sqlite3
import sys
from pathlib import Path

# Tool names this hook inspects. If your Hermes install's browser toolset
# uses different tool names, add them here — an unlisted tool name is
# invisible to this hook and passes through untouched.
WATCHED_TOOLS = {
    # Browser toolset
    "browser_click", "browser_press", "browser_tap",
    # computer-use toolset. shared/site-access-model.md's model 3 — the
    # model this pipeline actually submits under — drives Kene's own
    # authenticated session via computer-use, NOT the browser toolset.
    # Watching only browser_* left the real submit path invisible to this
    # hook, which fails OPEN for unlisted tools. That is the one failure
    # mode here that costs an unreviewed application.
    "computer", "computer_use", "computer-use",
}

# Tool names whose calls this hook has verified it can see. 10-approval-
# and-submit checks this at session start (see that skill's step 2) and
# refuses to open a form if the toolset it is about to drive is not in
# WATCHED_TOOLS. Without that check, an install whose browser toolset uses
# a name not listed above gets NO gate and no warning that it has none —
# the hook simply never fires. A silent absent gate is worse than a noisy
# one, so the skill fails closed on Kene's behalf rather than relying on
# this list being exhaustive.

# Case-insensitive substring match against the tool call's own arguments.
# Curated, not exhaustive — same style as Hermes's own dangerous-command
# approval list, just scoped to this pipeline's specific action.
SUBMIT_KEYWORDS = (
    "submit application",
    "submit my application",
    "apply now",
    "send application",
    "review and submit",
    "submit",
)

SKILL_ROOT = Path.home() / ".hermes" / "skills" / "job-hunting"
DB_PATH = SKILL_ROOT / "shared" / "applications.db"
ACTIVE_APP_DIR = SKILL_ROOT / "shared" / ".active_application"


def _respond(action: dict) -> None:
    print(json.dumps(action))
    sys.exit(0)


def _block(reason: str) -> None:
    _respond({"action": "block", "message": reason})


def _allow() -> None:
    _respond({})


def main() -> None:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw or "{}")
    except json.JSONDecodeError:
        _block("job-hunting submit-gate: could not parse hook payload — failing closed")
        return

    tool_name = payload.get("tool_name") or ""
    if tool_name not in WATCHED_TOOLS:
        _allow()
        return

    tool_input = payload.get("tool_input") or {}
    haystack = json.dumps(tool_input).lower()
    if not any(kw in haystack for kw in SUBMIT_KEYWORDS):
        _allow()
        return

    # From here on: this looks like a submit click. Every remaining branch
    # blocks unless we can positively confirm approval — no branch below
    # is allowed to fall through to _allow() on missing information.
    session_id = payload.get("session_id") or ""
    if not session_id:
        _block("job-hunting submit-gate: hook payload has no session_id — failing closed")
        return

    marker_path = ACTIVE_APP_DIR / f"{session_id}.json"
    if not marker_path.exists():
        _block(
            "job-hunting submit-gate: this looks like a submit click but no "
            f"active-application marker exists at {marker_path} — "
            "10-approval-and-submit must write that file before opening a "
            "form (see that skill's step 2). Refusing to guess which "
            "application this belongs to."
        )
        return

    try:
        marker = json.loads(marker_path.read_text())
        application_id = marker["application_id"]
    except Exception as exc:
        _block(f"job-hunting submit-gate: unreadable active-application marker ({exc})")
        return

    if not DB_PATH.exists():
        _block(f"job-hunting submit-gate: applications.db not found at {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(str(DB_PATH))
        row = conn.execute(
            "SELECT approval_decision FROM applications WHERE id = ?",
            (application_id,),
        ).fetchone()
        conn.close()
    except Exception as exc:
        _block(f"job-hunting submit-gate: DB read failed ({exc})")
        return

    decision = ((row[0] if row else None) or "").strip().lower()
    if decision != "approve":
        _block(
            f"job-hunting submit-gate: application id={application_id} has "
            f"approval_decision={decision or '(unset)'!r}, not 'approve' — "
            "submit blocked. 'Looked approved in the conversation' and 'is "
            "actually approve in the DB' are two different things, "
            "especially during an unattended run — this gate only trusts "
            "the second one."
        )
        return

    _allow()


if __name__ == "__main__":
    main()
