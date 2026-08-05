#!/usr/bin/env python3
"""
test_permissions.py — exercise the policy engine, including the attacks.

    python3 test_permissions.py

The cases that matter are not "does the toggle toggle". They are:
  * can a non-negotiable gate be switched off by anyone      (no)
  * can an irreversible gate be armed without the code       (no)
  * can a wrong or expired code arm anything                 (no)
  * does auto-approval lapse on its own                      (yes)
  * does an edit made outside this tool fail closed          (yes)
"""
import json, os, re, shutil, subprocess, sys, tempfile, time
from pathlib import Path

ROOT = Path(tempfile.mkdtemp())
HOME = ROOT / ".hermes"
SCRIPT = Path(__file__).resolve().parent / "permissions.py"
GATES = Path(__file__).resolve().parents[2] / "gates.yaml"

ENV = {**os.environ, "HERMES_HOME": str(HOME), "JH_TEST": "1",
       "JH_GATES": str(GATES)}

FAILED, CASES = [], []


def run(*args):
    r = subprocess.run([sys.executable, str(SCRIPT), *args],
                       capture_output=True, text=True, env=ENV, cwd=ROOT)
    return r.returncode, r.stdout.strip()


def check(name, cond, extra=""):
    CASES.append((name, bool(cond), extra))
    if not cond:
        FAILED.append(name)


def code_from(out):
    m = re.search(r"TEST-CODE (\d{6})", out)
    return m.group(1) if m else None


def main():
    _, out = run("status")
    check("everything asks by default", "38 decision points" in out and "38 ask" in out)

    _, out = run("packs")
    check("packs render", "Sending and submitting" in out)

    _, out = run("show", "GATE-SUBMIT-APPLICATION")
    check("info panel shows both sides",
          "If I ask you first:" in out and "If I stop asking:" in out)

    _, out = run("show", "submitting a job")
    check("gate findable by plain name", "Submitting a job application" in out,
          "the user says what they mean, not a gate id")

    # --- non-negotiables ----------------------------------------------------
    _, out = run("set", "GATE-SENSITIVE-DISCLOSURE", "off")
    check("non-negotiable cannot be switched off", "cannot be switched off" in out)
    _, out = run("arm", "GATE-SENSITIVE-DISCLOSURE", "--phrase", "I accept the risk")
    check("non-negotiable cannot be armed either", "cannot be switched off" in out)
    _, out = run("set", "GATE-DM-PAIRING", "off")
    check("approval-channel gate cannot be switched off", "cannot be switched off" in out)

    # --- reversible gates are easy, as intended -----------------------------
    _, out = run("set", "GATE-RESEARCH-FETCH", "off")
    check("reversible gate switches off in one step", "stop asking" in out)
    rc, out = run("check", "GATE-RESEARCH-FETCH")
    check("hook sees it off", rc == 0 and json.loads(out)["ask"] is False)

    # --- irreversible needs the out-of-band code ----------------------------
    _, out = run("arm", "GATE-SUBMIT-APPLICATION", "--phrase", "I accept the risk")
    check("phrase alone only starts a challenge", "sent a 6-digit code" in out)
    rc, chk = run("check", "GATE-SUBMIT-APPLICATION")
    check("still asking while the challenge is open", json.loads(chk)["ask"] is True,
          "an injection that runs the arm command achieves nothing")

    sent = json.loads((HOME / ".arm-outbound").read_text())["text"]
    check("code travels to the approval channel", re.search(r"Code \d{6}", sent),
          "to the user's phone, not to this process's output")

    _, bad = run("arm", "GATE-SUBMIT-APPLICATION", "--code", "000000")
    check("wrong code refused", "does not match" in bad)
    rc, chk = run("check", "GATE-SUBMIT-APPLICATION")
    check("wrong code leaves the gate on", json.loads(chk)["ask"] is True)
    _, out2 = run("arm", "GATE-SUBMIT-APPLICATION", "--code",
                  code_from(out) or "111111")
    check("one wrong attempt cancels the whole request", "Nothing is waiting" in out2,
          "no brute force: a single miss and you start over")

    # --- the real path ------------------------------------------------------
    _, out = run("arm", "GATE-SUBMIT-APPLICATION", "--phrase", "I accept the risk")
    _, done = run("arm", "GATE-SUBMIT-APPLICATION", "--code", code_from(out))
    check("correct code arms the gate", "I will stop asking, for 30 days" in done)
    check("arming states the cap still applies", "daily limit still applies" in done)
    check("arming states it is recorded", "recorded" in done)
    rc, chk = run("check", "GATE-SUBMIT-APPLICATION")
    j = json.loads(chk)
    check("hook now auto-approves", j["ask"] is False)
    check("cap still applies in the hook's answer", j["cap_applies"] is True)

    _, out = run("status")
    check("status flags it as not asking", "auto-approving" in out and "29 days" in out)

    # --- a code cannot be reused -------------------------------------------
    _, out = run("disarm", "GATE-SUBMIT-APPLICATION")
    check("disarm is one step, no ceremony", "ask you again" in out)

    # --- expiry -------------------------------------------------------------
    _, out = run("arm", "GATE-SEND-DM", "--phrase", "I accept the risk")
    run("arm", "GATE-SEND-DM", "--code", code_from(out))
    pol = (HOME / "job-hunting-policy.yaml").read_text()
    (HOME / "job-hunting-policy.yaml").write_text(
        pol.replace(re.search(r"expires_at: '?(\S+?)'?\n", pol).group(1),
                    "2020-01-01T00:00:00+00:00"))
    (HOME / ".session-policy-digest").unlink(missing_ok=True)   # re-pin: our edit
    run("check", "GATE-SEND-DM")
    _, out = run("status")
    check("lapsed auto-approval reverts to asking", "Send" not in out or "38 ask" in out,
          "'I turned this on in March and forgot' is where the disasters live")

    # --- tampering ----------------------------------------------------------
    _, out = run("set", "GATE-RESEARCH-FETCH", "on")
    run("check", "GATE-RESEARCH-FETCH")                # pins the digest
    p = HOME / "job-hunting-policy.yaml"
    p.write_text(p.read_text() + "\n# injected\n")     # edited outside the tool
    rc, out = run("check", "GATE-SUBMIT-APPLICATION")
    check("edit outside the tool fails closed",
          rc == 2 and json.loads(out)["ask"] is True,
          "a gate that reads a file the agent can write is not a gate")

    # --- audit --------------------------------------------------------------
    _, out = run("audit")
    check("every change is recorded", "arm" in out and "disable" in out)

    w = max(len(n) for n, _, _ in CASES)
    for n, ok, extra in CASES:
        print(f"  {n:<{w}}  {'ok  ' if ok else 'FAIL'}{'  ' + extra if extra else ''}")
    print()
    shutil.rmtree(ROOT, ignore_errors=True)
    if FAILED:
        print(f"{len(FAILED)} failed: {FAILED}")
        sys.exit(1)
    print(f"{len(CASES)} checks pass")


if __name__ == "__main__":
    main()
