#!/usr/bin/env python3
"""
installer.py — a licence key in, a working install out.

    python3 installer.py --key LIC-abc123 --dest ~/job-hunting
    python3 installer.py --status
    python3 installer.py --release          # free this machine's seat

Replaces `licence_client.py`, which signed with HMAC while the server used
Ed25519. A reference implementation that contradicts the shipping code teaches
the wrong model, and it was teaching the exact model whose weakness the server
test exists to demonstrate. There is now one client, and it verifies the way the
server signs.

WHY THIS FILE EXISTS AT ALL. "Skills are fetched at activation, not shipped in
the installer" was the plan, and until now only the server half was built — so a
customer still received a folder, which is the thing the design was meant to
prevent. This is the half that makes it true.

OFFLINE IS THE NORMAL CASE. The entitlement token is verified locally against a
pinned public key. It works for fourteen days without contact and keeps working
through a thirty-day grace period after that. A licensing system that bricks the
tool when the network drops does not stop piracy; it punishes the customer.
"""
from __future__ import annotations
import argparse, base64, hashlib, io, json, os, platform, sys, tarfile, time, urllib.error, urllib.request
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

API = os.environ.get("JH_API", "https://hermes-licensing.solarsizer.workers.dev")
STATE = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
TOKEN_FILE = STATE / "licence-token"

# Pinned at build time. The PUBLIC half only — it can verify and cannot mint,
# which is the whole reason for Ed25519 over a shared secret. Someone who
# extracts this from the installer gains nothing.
PUBLIC_KEY = os.environ.get("JH_PUBLIC_KEY", "")


# ── token ───────────────────────────────────────────────────────────────────

def _unb64url(s: str) -> bytes:
    p = s.replace("-", "+").replace("_", "/")
    return base64.b64decode(p + "=" * (-len(p) % 4))


def verify_token(token: str, public_key_b64: str) -> dict | None:
    try:
        body, sig = token.split(".")
    except ValueError:
        return None
    try:
        Ed25519PublicKey.from_public_bytes(base64.b64decode(public_key_b64)) \
            .verify(_unb64url(sig), body.encode())
    except (InvalidSignature, ValueError, TypeError):
        return None
    try:
        return json.loads(_unb64url(body))
    except ValueError:
        return None


def token_state(claims: dict | None, now: float | None = None) -> tuple[str, dict | None]:
    """valid -> grace -> expired. Only the third stops anything working, and
    even then applying still works; the extras pause."""
    if claims is None:
        return "unlicensed", None
    now = now or time.time()
    if now <= claims["exp"]:
        return "valid", claims
    if now <= claims["grace"]:
        return "grace", claims
    return "expired", claims


# ── machine identity ────────────────────────────────────────────────────────

def fingerprint() -> str:
    """Salted, so it is not a device identifier that could be correlated across
    customers. Stable across reinstalls of the tool, not across machines."""
    parts = [platform.node(), platform.machine(), platform.system(),
             str(Path.home())]
    return hashlib.sha256(("jh|" + "|".join(parts)).encode()).hexdigest()[:32]


# ── http ────────────────────────────────────────────────────────────────────

def _call(path, body=None, token=None, raw=False):
    req = urllib.request.Request(
        API + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"content-type": "application/json",
                 "user-agent": "hermes-licensing-client/1.0.0",
                 **({"authorization": f"Bearer {token}"} if token else {})},
        method="POST" if body is not None else "GET")
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read() if raw else json.loads(r.read().decode())


# ── stages ──────────────────────────────────────────────────────────────────

def activate(key: str) -> dict:
    try:
        return _call("/v1/activate", {"licence_id": key, "fingerprint": fingerprint()})
    except urllib.error.HTTPError as e:
        detail = json.loads(e.read().decode() or "{}").get("error", "")
        if e.code == 404:
            raise SystemExit("That licence key was not recognised. Check it and try again.")
        if e.code == 409:
            raise SystemExit(
                "This licence is already in use on other machines and has used its\n"
                "self-service moves for the year. Reply to your receipt and I will sort it.")
        raise SystemExit(f"Could not activate: {detail or e.code}")
    except urllib.error.URLError:
        raise SystemExit("Could not reach the licence server. Check your connection "
                         "and try again — nothing has been changed.")


def download(token: str, dest: Path) -> list[str]:
    listing = _call("/v1/bundles", token=token)
    installed = []
    for b in listing.get("bundles", []):
        blob = _call(f"/v1/bundles/{b['bundle_id']}", token=token, raw=True)

        # Integrity before unpacking, never after. An archive that fails its
        # hash is not opened at all.
        got = hashlib.sha256(blob).hexdigest()
        if b.get("sha256") and got != b["sha256"].lower():
            raise SystemExit(f"The {b['scope']} download did not arrive intact. "
                             f"Nothing has been unpacked. Please try again.")

        with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as tf:
            for m in tf.getmembers():
                # A tar member may not escape the destination. This is the
                # oldest archive bug there is and it is worth the four lines.
                target = (dest / m.name).resolve()
                if not str(target).startswith(str(dest.resolve())):
                    raise SystemExit("The download contained an unexpected path. "
                                     "Nothing has been unpacked.")
                if m.issym() or m.islnk():
                    raise SystemExit("The download contained a link. "
                                     "Nothing has been unpacked.")
            tf.extractall(dest)
        installed.append(f"{b['scope']} {b['version']}")
    return installed


def verify_bundle(dest: Path) -> tuple[bool, list[str]]:
    mf, sig = dest / "MANIFEST.json", dest / "MANIFEST.sig"
    if not mf.is_file():
        return False, ["no manifest in the download"]
    doc = json.loads(mf.read_text())
    bad = []
    for rel, want in doc["files"].items():
        p = dest / rel
        if not p.is_file():
            bad.append(f"missing: {rel}")
        elif hashlib.sha256(p.read_bytes()).hexdigest() != want:
            bad.append(f"changed: {rel}")
    return not bad, bad


# ── commands ────────────────────────────────────────────────────────────────

def cmd_install(a):
    if not PUBLIC_KEY:
        raise SystemExit("This installer was built without a verification key. "
                         "Please download it again from the site.")
    dest = Path(a.dest).expanduser()
    print("Activating…")
    res = activate(a.key)
    claims = verify_token(res["token"], PUBLIC_KEY)
    if claims is None:
        # A token that will not verify is worse than no token: it means
        # something between the server and here is not what it claims to be.
        raise SystemExit("The licence response could not be verified. "
                         "Nothing has been installed.")

    STATE.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(res["token"])
    print(f"  activated on this machine")

    print("Downloading…")
    dest.mkdir(parents=True, exist_ok=True)
    got = download(res["token"], dest)
    for g in got:
        print(f"  {g}")

    ok, bad = verify_bundle(dest)
    print("Checking…")
    if not ok:
        for b in bad[:5]:
            print(f"  ! {b}")
        raise SystemExit("The install did not verify. Please run this again.")
    print("  everything verified")

    check = dest / "00-orchestrator" / "scripts" / "install-check.pyc"
    if not check.is_file():
        check = check.with_suffix(".py")
    if check.is_file():
        os.system(f'"{sys.executable}" "{check}" --root "{dest}"')

    print(f"\nInstalled at {dest}")
    print("Open the tool and say hello — it will take you through setup.")


def cmd_status(a):
    if not TOKEN_FILE.is_file():
        print("Not activated on this machine.")
        return
    claims = verify_token(TOKEN_FILE.read_text().strip(), PUBLIC_KEY)
    state, c = token_state(claims)
    if state == "unlicensed":
        print("The stored licence could not be read. Please reactivate.")
        return
    if state == "valid":
        print(f"Active. {len(c['addons'])} extra features on your plan.")
    elif state == "grace":
        days = int((c["grace"] - time.time()) // 86400)
        print(f"I have not been able to check your licence recently. "
              f"Everything works normally for another {days} days.")
    else:
        print("I could not confirm your licence. Applying still works — "
              "the extra features are paused until I can check again.")


def cmd_release(a):
    if not TOKEN_FILE.is_file():
        print("Nothing to release on this machine.")
        return
    try:
        _call("/v1/seats/release", {}, token=TOKEN_FILE.read_text().strip())
        TOKEN_FILE.unlink()
        print("This machine has been released. You can activate on another one.")
    except Exception:
        print("Could not reach the licence server. Try again when you are online.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key"); ap.add_argument("--dest", default="~/job-hunting")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--release", action="store_true")
    a = ap.parse_args()
    if a.status:
        return cmd_status(a)
    if a.release:
        return cmd_release(a)
    if not a.key:
        raise SystemExit("Usage: installer.py --key YOUR-LICENCE-KEY")
    cmd_install(a)


if __name__ == "__main__":
    main()
