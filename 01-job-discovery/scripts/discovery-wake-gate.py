#!/usr/bin/env python3
"""
job-hunting discovery wake-gate — a Hermes cron `script=` pre-run gate.

Purpose (see 01-job-discovery/SKILL.md, "Cost control: the wake-gate
script", and cron/cron-jobs.md job #1): 01-job-discovery's discovery-scan
cron job currently pays for a full LLM agent turn on every tick — up to
6x/day, every day, forever — whether or not anything new actually exists
to look at. This script runs as that job's `script=` pre-run step and
does the cheap part first: check the sources this script knows how to
check cheaply, and tell Hermes's cron system to skip waking the agent
entirely (zero token cost) when nothing survived the cheap filter.

Contract (user-guide/features/cron.md, "Skipping the agent entirely:
wakeAgent"): print a single JSON object to stdout as the LAST line;
{"wakeAgent": false} skips the agent turn for this tick, anything else
(including no wakeAgent key, or this script erroring out) wakes it
normally.

FAILS OPEN, deliberately — the opposite direction from the submit-gate
hook in security/hooks/verify-submit-approval.py, and for a specific
reason: the cost of an unnecessary wake is one LLM turn; the cost of a
wrongly-skipped wake is a real posting sitting unseen until the next
tick, which is exactly the "speed matters" finding 01-job-discovery's
own SKILL.md already leads with. So: any source type this script can't
cheaply check, any error reading a source, any error in this script
itself — every one of those wakes the agent rather than skips it. This
script only ever recommends a skip when it positively confirmed nothing
changed across every source it was ABLE to check, and defers to the
agent for everything else.

Scope, honestly stated: this script cheap-checks `rss` and `email_label`
sources only (the two cheapest and most common source types in this
pipeline). `aggregator_api`, `open_web_search`, `google_dork`,
`linkedin_search_url`, `indeed_search_url`, `scrape_and_filter`, and
`export_file` sources always cause a wake — there's no cost saving for
those yet. If most of your sources.yaml entries are one of those types,
this gate will rarely fire and that's expected, not a bug.
"""
import json
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

SKILL_ROOT = Path.home() / ".hermes" / "skills" / "job-hunting"
SOURCES_PATH = SKILL_ROOT / "shared" / "sources.yaml"
STATE_PATH = SKILL_ROOT / "shared" / ".discovery_gate_state.json"

CHEAP_CHECKABLE_TYPES = {"rss", "email_label"}


def wake(reason: str) -> None:
    """Emit a payload with no wakeAgent key (or true) — cron wakes the agent.
    reason is for the job's own log, not parsed by Hermes."""
    print(json.dumps({"wakeAgent": True, "reason": reason}))
    sys.exit(0)


def skip(reason: str) -> None:
    print(json.dumps({"wakeAgent": False, "reason": reason}))
    sys.exit(0)


def load_sources() -> list:
    # Minimal YAML reading without a hard PyYAML dependency: this file's
    # shape is simple enough (flat list of mappings under `sources:`) that
    # a real parser is preferable if available, so try it first.
    try:
        import yaml  # type: ignore

        with open(SOURCES_PATH) as f:
            data = yaml.safe_load(f) or {}
        return data.get("sources", [])
    except ImportError:
        wake("PyYAML not available in this environment — can't parse sources.yaml, waking to be safe")
        return []  # unreachable, wake() exits


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save_state(state: dict) -> None:
    try:
        STATE_PATH.write_text(json.dumps(state, indent=2))
    except OSError:
        pass  # non-fatal — worst case, next tick re-checks the same window


def check_rss(source: dict, state: dict) -> bool:
    """Return True if this feed has an item not seen in a prior check."""
    url = source.get("url")
    if not url:
        return True  # malformed entry — let the agent sort it out
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            body = resp.read()
        root = ET.fromstring(body)
        guids = [
            (el.text or "").strip()
            for el in root.iter()
            if el.tag.lower() in ("guid", "id") and (el.text or "").strip()
        ]
        if not guids:
            return "error", "feed fetched but no guid/id elements found — can't determine new vs seen"
    except Exception as exc:
        return "error", f"feed fetch/parse failed ({exc})"

    last_seen = set(state.get(source["id"], {}).get("seen_guids", []))
    new_guids = [g for g in guids if g not in last_seen]

    # Keep the state file bounded — only the most recent window of guids
    # per feed, not an ever-growing list.
    state.setdefault(source["id"], {})["seen_guids"] = guids[:200]
    if new_guids:
        return "new", f"{len(new_guids)} new item(s) since last check"
    return "unchanged", "no new items"


def check_email_label(source: dict, state: dict) -> tuple:
    """Return (status, detail) — status in {"new", "unchanged", "error"}."""
    handle = source.get("handle")
    if not handle:
        return "error", "source has no 'handle' configured"
    try:
        result = subprocess.run(
            ["himalaya", "envelope", "list", "--folder", handle, "--output", "json"],
            capture_output=True,
            text=True,
            timeout=20,
        )
        if result.returncode != 0:
            return "error", f"himalaya exited {result.returncode} — not configured, or folder missing"
        envelopes = json.loads(result.stdout or "[]")
    except Exception as exc:
        return "error", f"himalaya call failed ({exc})"

    ids = [str(e.get("id")) for e in envelopes if e.get("id") is not None]
    last_seen = set(state.get(source["id"], {}).get("seen_ids", []))
    new_ids = [i for i in ids if i not in last_seen]

    state.setdefault(source["id"], {})["seen_ids"] = ids[:200]
    if new_ids:
        return "new", f"{len(new_ids)} new envelope(s) since last check"
    return "unchanged", "no new envelopes"


def main() -> None:
    if not SOURCES_PATH.exists():
        wake("sources.yaml not found — waking so the agent can report the setup gap")
        return

    sources = load_sources()
    if not sources:
        wake("sources.yaml has no declared sources yet — waking so the agent can say so")
        return

    state = load_state()
    new_details = []       # sources that positively confirmed new content
    error_details = []     # sources this gate couldn't reliably check this tick
    uncheckable_types = set()  # source types this gate doesn't know how to cheap-check at all

    for source in sources:
        stype = source.get("type")
        if stype not in CHEAP_CHECKABLE_TYPES:
            uncheckable_types.add(stype)
            continue

        try:
            if stype == "rss":
                status, detail = check_rss(source, state)
            else:  # email_label
                status, detail = check_email_label(source, state)
        except Exception as exc:
            status, detail = "error", f"unhandled exception ({exc})"

        label = source.get("id", "<unnamed source>")
        if status == "new":
            new_details.append(f"{label}: {detail}")
        elif status == "error":
            error_details.append(f"{label}: {detail}")
        # "unchanged" sources contribute nothing to either list — that's the
        # whole point, they're the ones this gate can actually vouch for.

    save_state(state)

    if new_details:
        wake("new content confirmed — " + "; ".join(new_details))
        return

    if error_details:
        wake("could not reliably check " + str(len(error_details)) + " source(s) this tick — " + "; ".join(error_details))
        return

    if uncheckable_types:
        wake(
            "every rss/email_label source confirmed unchanged, but sources.yaml also "
            f"has type(s) this gate can't cheap-check yet ({', '.join(sorted(uncheckable_types))}) "
            "— deferring to the agent rather than guessing about those"
        )
        return

    skip("every source in sources.yaml is a cheap-checkable type and every one confirmed no new items")


if __name__ == "__main__":
    main()
