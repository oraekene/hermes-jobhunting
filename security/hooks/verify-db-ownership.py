#!/usr/bin/env python3
"""
job-hunting DB write gate — a Hermes `pre_tool_call` shell hook.

THE PROBLEM THIS EXISTS FOR
shared/db-concurrency.md establishes that a delegated subagent owns
exactly one applications row and writes nothing else. That rule was
instruction only. A child that ignored it — or never had it pasted into
its context, which is the likelier failure since a subagent knows only
what the parent gave it — would write to another application's row and
succeed. Silently.

This is the ownership equivalent of verify-submit-approval.py, and the
same reasoning applies: a boundary that matters should not rest on an
agent choosing to respect it.

THE PREDICATE, AND WHY IT IS THIS ONE
The obvious design — parse the SQL, extract the target application_id,
compare against the child's owned id — is fragile in exactly the way that
gets a security control quietly disabled. SQL arrives inside bash
pipelines, heredocs, Python one-liners and ORM calls; a parser that
handles 90% of that provides 0% of the guarantee, because the 10% it
misses is where a determined-or-confused agent ends up.

So the predicate is coarser and far more robust:

    During an active sweep, only the registered writer session may write
    to applications.db at all.

Detecting *write intent* in a blob of text is tractable in a way that
detecting *which row* is not. Everything else — children write to an
outbox, the parent ingests it serially — is what makes that coarse rule
workable rather than crippling. See db-concurrency.md "The outbox".

Reads are always allowed. A child that cannot read the DB cannot do its
job, and reads under WAL contend with nothing.

HOW HERMES CALLS THIS
stdin: one JSON object (hook_event_name, tool_name, tool_input,
session_id, cwd, ...). stdout: one JSON object; {"action": "block",
"message": "..."} vetoes, anything else allows.

FAILS OPEN, DELIBERATELY — the opposite of the submit hook.
That asymmetry is intentional and worth stating plainly. The submit hook
guards an irreversible external action (an application going to an
employer), so a false negative is unrecoverable and it fails closed. This
hook guards an internal consistency property. A false positive here would
block a legitimate write mid-build and manufacture exactly the
half-built-application problem addendum 15 exists to clean up — so a bug
in this script, or an unparseable payload, must not take the pipeline
down. Every uncertain case is allowed and logged.

The one exception: when the marker file says a sweep is active and this
session is definitively not the writer, it blocks. That case is not
uncertain.

USAGE
  Registered as a pre_tool_call hook. See security/security-setup.md.
  Standalone check:  echo '<payload>' | python3 verify-db-ownership.py
"""
import json
import os
import re
import sys
import time
from pathlib import Path

SKILL_ROOT = Path(
    os.environ.get(
        "JOB_HUNTING_ROOT",
        Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
        / "skills"
        / "job-hunting",
    )
)
SHARED = SKILL_ROOT / "shared"
DB_NAME = "applications.db"

# Written by the parent at sweep start, removed at sweep end. Its
# presence is what puts this hook into enforcing mode; without it, this
# is ordinary single-session operation and nothing is restricted.
WRITER_MARKER = SHARED / ".db_writer_session.json"

# Stale marker guard. A parent that crashes mid-sweep would otherwise
# leave the pipeline permanently unable to write. Longer than the sweep
# cycle plus margin (~7h, per parallel-pipeline-sweep.md) so it cannot
# expire under a legitimately slow batch.
MARKER_MAX_AGE_S = 8 * 3600

AUDIT_LOG = SHARED / ".db_write_audit.jsonl"

# Tools that can reach a database. An unlisted tool is invisible here and
# passes through — same caveat as the submit hook, and the same fix if
# your install's toolset differs: add it.
WATCHED_TOOLS = {
    "bash", "shell", "run_command", "execute_command",
    "python", "run_python", "code_execution",
    "str_replace", "create_file", "write_file",
}

# Write intent. Deliberately over-broad: a false positive costs a logged
# allow (see FAILS OPEN above — coarse detection only escalates to a
# block when the session is definitively not the writer).
WRITE_SQL = re.compile(
    r"\b(insert\s+into|insert\s+or\s+\w+\s+into|update\s+|delete\s+from|"
    r"replace\s+into|drop\s+table|alter\s+table|create\s+table|"
    r"create\s+index|truncate|vacuum|pragma\s+journal_mode|"
    r"pragma\s+wal_checkpoint|attach\s+database)\b",
    re.IGNORECASE,
)

# Redirections and copies that would clobber the file without any SQL at
# all — the hole a purely SQL-shaped matcher leaves open.
CLOBBER = re.compile(
    r"(>\s*\S*applications\.db|cp\s+\S+\s+\S*applications\.db|"
    r"mv\s+\S+\s+\S*applications\.db|rm\s+\S*applications\.db|"
    r"sqlite3\s+\S*applications\.db\s+[\"'].*?\.(?:restore|import))",
    re.IGNORECASE,
)


def emit(obj):
    print(json.dumps(obj))
    sys.exit(0)


def allow(reason=None, payload=None):
    if reason:
        log(payload, "allow", reason)
    emit({})


def block(message, payload=None, reason=""):
    log(payload, "block", reason)
    emit({"action": "block", "message": message})


def log(payload, decision, reason):
    """Best-effort audit trail. Never raises — a logging failure must not
    become a pipeline failure."""
    try:
        SHARED.mkdir(parents=True, exist_ok=True)
        with AUDIT_LOG.open("a") as fh:
            fh.write(
                json.dumps(
                    {
                        "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                        "decision": decision,
                        "reason": reason,
                        "session": (payload or {}).get("session_id"),
                        "tool": (payload or {}).get("tool_name"),
                    }
                )
                + "\n"
            )
    except Exception:
        pass


def read_marker():
    """The active writer session, or None. Any problem reading it means
    no enforcement — see FAILS OPEN."""
    try:
        if not WRITER_MARKER.exists():
            return None
        if time.time() - WRITER_MARKER.stat().st_mtime > MARKER_MAX_AGE_S:
            # Parent probably died. Enforcing against a ghost would wedge
            # the pipeline for good.
            return None
        data = json.loads(WRITER_MARKER.read_text())
        return data if data.get("writer_session_id") else None
    except Exception:
        return None


def payload_text(payload):
    """Flatten tool_input to searchable text without assuming its shape."""
    ti = payload.get("tool_input")
    if isinstance(ti, str):
        return ti
    try:
        return json.dumps(ti)
    except Exception:
        return str(ti)


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except Exception:
        emit({})  # unparseable: allow, silently. Not our call to make.

    if payload.get("tool_name") not in WATCHED_TOOLS:
        emit({})

    text = payload_text(payload)
    if DB_NAME not in text:
        emit({})

    touches_write = bool(WRITE_SQL.search(text)) or bool(CLOBBER.search(text))
    if not touches_write:
        emit({})  # a read. Always fine.

    marker = read_marker()
    if marker is None:
        # No sweep in progress, or the marker is stale/unreadable. Normal
        # single-session operation — this hook does nothing.
        allow("no_active_sweep", payload)

    session = payload.get("session_id")
    if not session:
        # Cannot identify the caller. Allowing an unidentified writer is
        # the lesser evil versus blocking the parent because Hermes
        # omitted a field.
        allow("no_session_id", payload)

    if session == marker.get("writer_session_id"):
        allow("is_writer", payload)

    # Definitively a non-writer session attempting a write during an
    # active sweep. This is the case the hook exists for.
    owned = marker.get("dispatched_application_ids", [])
    block(
        "BLOCKED by job-hunting DB write gate.\n\n"
        "A sweep is in progress and this session is not the registered "
        "writer, so it may not write to applications.db. This is not a "
        "permissions problem to work around — it is shared/db-concurrency.md's "
        "row-ownership rule, enforced.\n\n"
        "If you are a delegated subagent: write your result to the outbox "
        f"instead — {SHARED}/.outbox/<application_id>.<attempt>.json — and "
        "report what you did in your summary. The parent ingests the outbox "
        "serially and updates the database. Do not retry this write, and do "
        "not attempt to reach the file another way.\n\n"
        f"Active sweep dispatched {len(owned)} application(s). "
        f"Writer session: {marker.get('writer_session_id')}.\n"
        "Reads are unaffected — query freely.",
        payload,
        "non_writer_write_attempt",
    )


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        # A crash in this hook must never wedge the pipeline. See the
        # asymmetry note in the module docstring.
        #
        # The fallback emit() can itself fail — a closed stdout raises
        # BrokenPipeError, which would turn a harmless internal error into
        # a non-zero exit and, depending on how the caller reads that, a
        # blocked tool call. Swallow it: if stdout is gone, nothing is
        # reading the verdict anyway, and silence is the fail-open answer.
        try:
            emit({})
        except SystemExit:
            raise
        except Exception:
            os._exit(0)
