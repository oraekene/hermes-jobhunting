#!/usr/bin/env python3
"""
permissions.py — the policy engine behind the permissions conversation.

The skill talks; this decides. Every invariant from gates.yaml is enforced here
rather than in prose, because prose in a skill file is a suggestion to a model
and this needs to be a rule.

    permissions.py status                     what is on, what is off, what expires
    permissions.py packs                      the pack view
    permissions.py list [--pack P] [--changed] the flat expert view
    permissions.py show GATE                  the info panel, both sides
    permissions.py set GATE on|off            reversible gates only
    permissions.py arm GATE --phrase "..."    irreversible gates
    permissions.py disarm GATE
    permissions.py check GATE                 what a hook asks: may this proceed?
    permissions.py sweep                      expire lapsed arming (cron)
    permissions.py audit [--limit N]

THE POLICY FILE LIVES OUTSIDE THE AGENT'S WORKING DIRECTORY, at
~/.hermes/job-hunting-policy.yaml, and its checksum is pinned at session start.

That is not tidiness. The attack it defends against: text inside a scraped job
posting persuades the agent to write auto_approve into the policy file, and the
submit hook — reading that same file — then waves everything through. A gate
that reads a file the agent can write is not a gate.
"""
from __future__ import annotations
import argparse, hashlib, json, os, sys, time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
POLICY = Path(os.environ.get("JH_POLICY", HOME / "job-hunting-policy.yaml"))
DIGEST = HOME / ".session-policy-digest"
AUDIT = HOME / "job-hunting-policy-audit.jsonl"
GATES = Path(os.environ.get("JH_GATES", "shared/gates.yaml"))

ARM_PHRASE = "I accept the risk"
CHALLENGE = HOME / ".arm-challenge.json"
CHALLENGE_TTL = 600          # seconds

# WHY A CODE AND NOT JUST A PHRASE.
# A typed phrase defends against a careless human. It does not defend against a
# prompt injection, because the phrase is written in this file and any text that
# can make the agent run a command can make it run the command WITH the phrase.
#
# So arming an irreversible gate takes two steps and the second one leaves the
# machine: a short code is delivered to the approval channel — the user's own
# phone — and must come back. Injected text cannot predict a code that is
# generated after it was written, and cannot read a message sent to a phone.
#
# This is the same shape as dcg's allow-once: short, single-use, expiring, and
# scoped to one specific action.
now = lambda: datetime.now(timezone.utc)
iso = lambda d: d.replace(microsecond=0).isoformat()


# ── registry ────────────────────────────────────────────────────────────────

def registry():
    doc = yaml.safe_load(GATES.read_text(encoding="utf-8"))
    return doc, {g["id"]: g for g in doc["gates"]}, {p["id"]: p for p in doc["packs"]}


def load_policy():
    if not POLICY.is_file():
        return {"version": 1, "gates": {}}
    return yaml.safe_load(POLICY.read_text(encoding="utf-8")) or {"version": 1, "gates": {}}


def save_policy(pol, action, detail):
    HOME.mkdir(parents=True, exist_ok=True)
    POLICY.write_text(yaml.safe_dump(pol, sort_keys=False), encoding="utf-8")
    # Re-pin immediately: a change made through this tool is legitimate and must
    # not look like tampering on the next session check.
    DIGEST.write_text(hashlib.sha256(POLICY.read_bytes()).hexdigest())
    with AUDIT.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"at": iso(now()), "action": action, **detail}) + "\n")


def session_pin():
    """Called once at session start. Returns True if the file is unchanged."""
    if not POLICY.is_file():
        return True
    d = hashlib.sha256(POLICY.read_bytes()).hexdigest()
    if DIGEST.is_file() and DIGEST.read_text().strip() not in ("", d):
        return False
    DIGEST.parent.mkdir(parents=True, exist_ok=True)
    DIGEST.write_text(d)
    return True


# ── state ───────────────────────────────────────────────────────────────────

def state_of(gate, pol):
    """(enabled, why) — enabled means the gate ASKS. Disabled means auto-approve."""
    gid = gate["id"]
    entry = (pol.get("gates") or {}).get(gid)
    if not gate.get("toggleable"):
        return True, "cannot be switched off"
    if not entry or entry.get("enabled", True):
        return True, "asking"
    exp = entry.get("expires_at")
    if exp and datetime.fromisoformat(exp) <= now():
        return True, "auto-approval expired, asking again"
    if exp:
        days = (datetime.fromisoformat(exp) - now()).days
        return False, f"auto-approving, {days} days left"
    return False, "auto-approving"


def sweep(pol, gates):
    """Expire lapsed arming. Auto-approval on an irreversible action is never
    permanent — 'I turned this on in March and forgot' is where the disasters
    live."""
    expired = []
    for gid, entry in (pol.get("gates") or {}).items():
        exp = entry.get("expires_at")
        if entry.get("enabled") is False and exp and datetime.fromisoformat(exp) <= now():
            entry["enabled"] = True
            entry.pop("expires_at", None)
            entry["expired_at"] = iso(now())
            expired.append(gid)
    return expired


# ── mutation ────────────────────────────────────────────────────────────────

def set_gate(gid, on, gates, phrase=None):
    g = gates.get(gid)
    if not g:
        return f"No such setting: {gid}"
    if on:
        pol = load_policy()
        pol.setdefault("gates", {}).setdefault(gid, {})["enabled"] = True
        pol["gates"][gid].pop("expires_at", None)
        save_policy(pol, "enable", {"gate": gid})
        return f"{g['label']} — I will ask you again."

    if not g.get("toggleable"):
        note = g.get("note", "").strip().split(".")[0]
        return (f"{g['label']} cannot be switched off.\n  {note}.")

    if g.get("arm_required"):
        if phrase and phrase.isdigit() and len(phrase) == 6:
            return _redeem(gid, phrase, g)
        if phrase != ARM_PHRASE:
            return (f"{g['label']} is one of the ones that cannot be undone.\n\n"
                    f"  {str(g['panel']['when_off']).strip()}\n\n"
                    f"To switch it off, type exactly:  {ARM_PHRASE}")
        return _challenge(gid, g)

    pol = load_policy()
    pol.setdefault("gates", {})[gid] = {"enabled": False, "changed_at": iso(now())}
    save_policy(pol, "disable", {"gate": gid})
    return f"{g['label']} — I will stop asking."


def _challenge(gid, g):
    """Step one: mint a code and hand it to the notifier, never to stdout."""
    import secrets
    code = f"{secrets.randbelow(1_000_000):06d}"
    HOME.mkdir(parents=True, exist_ok=True)
    CHALLENGE.write_text(json.dumps({
        "gate": gid, "code_sha": hashlib.sha256(code.encode()).hexdigest(),
        "expires": time.time() + CHALLENGE_TTL,
    }))
    # The notifier reads this and sends it to the approval channel. It is
    # deliberately not returned to the caller: the whole point is that the code
    # travels to the user's phone and not through this process's output.
    (HOME / ".arm-outbound").write_text(json.dumps({
        "channel": "approval",
        "text": (f"Code {code} — to stop being asked before "
                 f"{g['label'].lower()}. Expires in 10 minutes. "
                 f"If you did not ask for this, ignore it and tell me."),
    }))
    out = (f"{g['label']} cannot be switched off from here alone.\n"
           f"  I have sent a 6-digit code to your approval channel.\n"
           f"  Send it back to confirm. It expires in 10 minutes.")
    if os.environ.get("JH_TEST") == "1":
        out += f"\n  TEST-CODE {code}"
    return out


def _redeem(gid, code, g):
    """Step two: the code comes back from the user's own channel."""
    if not CHALLENGE.is_file():
        return "Nothing is waiting for a code right now."
    ch = json.loads(CHALLENGE.read_text())
    if ch["gate"] != gid:
        return "That code was for a different setting."
    if time.time() > ch["expires"]:
        CHALLENGE.unlink(missing_ok=True)
        return "That code has expired. Ask me again and I will send a new one."
    if hashlib.sha256(code.encode()).hexdigest() != ch["code_sha"]:
        CHALLENGE.unlink(missing_ok=True)      # single attempt, then start over
        return "That code does not match. I have cancelled the request."
    CHALLENGE.unlink(missing_ok=True)
    (HOME / ".arm-outbound").unlink(missing_ok=True)

    days = g.get("expires_days") or 30
    pol = load_policy()
    pol.setdefault("gates", {})[gid] = {
        "enabled": False,
        "armed_at": iso(now()),
        "expires_at": iso(now() + timedelta(days=days)),
    }
    save_policy(pol, "arm", {"gate": gid, "days": days})
    return (f"{g['label']} — I will stop asking, for {days} days.\n"
            f"  Your daily limit still applies.\n"
            f"  Everything I do this way is recorded and you can read it back.\n"
            f"  On {iso(now() + timedelta(days=days))[:10]} I start asking again.")


# ── rendering ───────────────────────────────────────────────────────────────

def wrap(text, width=72, indent="  "):
    words, line, out = str(text).split(), "", []
    for w in words:
        if len(line) + len(w) + 1 > width:
            out.append(indent + line); line = w
        else:
            line = f"{line} {w}".strip()
    if line:
        out.append(indent + line)
    return "\n".join(out)


def panel(g):
    lines = [g["label"], ""]
    lines.append("  If I ask you first:")
    lines.append(wrap(g["panel"]["when_on"], indent="    "))
    off = str(g["panel"]["when_off"])
    lines.append("")
    if "not available" in off.lower():
        lines.append("  This one cannot be switched off.")
        if g.get("note"):
            lines.append(wrap(g["note"].strip(), indent="    "))
    else:
        lines.append("  If I stop asking:")
        lines.append(wrap(off, indent="    "))
    return "\n".join(lines)


CLASS_LABEL = {
    "irreversible_external": "cannot be undone",
    "reversible_external": "reaches outside, undoable",
    "reversible_internal": "changes your own setup",
    "structural": "always on",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["status", "packs", "list", "show", "set", "arm",
                                    "disarm", "check", "sweep", "audit", "pin"])
    ap.add_argument("gate", nargs="?")
    ap.add_argument("value", nargs="?")
    ap.add_argument("--pack"); ap.add_argument("--phrase"); ap.add_argument("--code")
    ap.add_argument("--changed", action="store_true")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    doc, gates, packs = registry()
    pol = load_policy()

    if a.cmd == "pin":
        ok = session_pin()
        print("ok" if ok else "POLICY CHANGED MID-SESSION")
        sys.exit(0 if ok else 2)

    if a.cmd == "sweep":
        expired = sweep(pol, gates)
        if expired:
            save_policy(pol, "expire", {"gates": expired})
            for gid in expired:
                print(f"{gates[gid]['label']} — auto-approval has expired. "
                      f"I will ask you again.")
        else:
            print("nothing expired")
        return

    if a.cmd == "status":
        off = [(gid, g) for gid, g in gates.items() if not state_of(g, pol)[0]]
        print(f"{len(gates)} decision points. "
              f"{len(gates) - len(off)} ask you first, {len(off)} do not.\n")
        if not off:
            print("  Nothing is set to run without asking you.")
        for gid, g in off:
            _, why = state_of(g, pol)
            mark = "  !" if g["class"] == "irreversible_external" else "  ."
            print(f"{mark} {g['label']}  ({why})")
        return

    if a.cmd == "packs":
        for pid, p in packs.items():
            members = [g for g in gates.values() if g.get("pack") == pid]
            if not members:
                continue
            asking = sum(1 for g in members if state_of(g, pol)[0])
            print(f"\n{p['label']}  —  {asking}/{len(members)} ask you first")
            print(wrap(p["blurb"]))
        print("\nSay the name of any group to go through it one at a time.")
        return

    if a.cmd == "list":
        rows = [g for g in gates.values()
                if (not a.pack or g.get("pack") == a.pack)
                and (not a.changed or not state_of(g, pol)[0])]
        for g in sorted(rows, key=lambda g: (g["class"], g["label"])):
            on, why = state_of(g, pol)
            print(f"  [{'ask' if on else 'auto'}]  {g['label']:<44} "
                  f"{CLASS_LABEL[g['class']]}")
        if not rows:
            print("  nothing matches")
        return

    if a.cmd == "show":
        g = gates.get(a.gate)
        if not g:
            hits = [x for x in gates.values() if a.gate.lower() in x["label"].lower()]
            if len(hits) != 1:
                print(f"No single match for {a.gate!r}."
                      + (f" Did you mean: {', '.join(h['label'] for h in hits[:4])}?"
                         if hits else ""))
                return
            g = hits[0]
        print(panel(g))
        on, why = state_of(g, pol)
        print(f"\n  Right now: {'I ask you first' if on else 'I do not ask'} ({why})")
        return

    if a.cmd in ("set", "arm", "disarm"):
        gid = a.gate
        if gid not in gates:
            hits = [x for x in gates.values() if str(a.gate).lower() in x["label"].lower()]
            if len(hits) == 1:
                gid = hits[0]["id"]
        if a.cmd == "arm":
            print(set_gate(gid, False, gates, a.code or a.phrase))
        elif a.cmd == "disarm":
            print(set_gate(gid, True, gates))
        else:
            print(set_gate(gid, (a.value or "on").lower() == "on", gates, a.phrase))
        return

    if a.cmd == "check":
        g = gates.get(a.gate)
        if not g:
            print(json.dumps({"gate": a.gate, "known": False, "ask": True}))
            sys.exit(1)
        if not session_pin():
            print(json.dumps({"gate": a.gate, "ask": True,
                              "reason": "policy changed mid-session"}))
            sys.exit(2)
        expired = sweep(pol, gates)
        if expired:
            save_policy(pol, "expire", {"gates": expired})
        on, why = state_of(g, pol)
        print(json.dumps({"gate": g["id"], "ask": on, "reason": why,
                          "cap_applies": g.get("cap_applies", True)}))
        sys.exit(0 if not on else 1)

    if a.cmd == "audit":
        if not AUDIT.is_file():
            print("nothing recorded yet")
            return
        for ln in AUDIT.read_text(encoding="utf-8").splitlines()[-a.limit:]:
            e = json.loads(ln)
            g = gates.get(e.get("gate"), {})
            print(f"  {e['at'][:16].replace('T',' ')}  {e['action']:<8} "
                  f"{g.get('label', e.get('gate',''))}")


if __name__ == "__main__":
    main()
