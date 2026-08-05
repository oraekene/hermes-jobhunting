#!/usr/bin/env python3
"""
test_installer.py — the installer against a fake licence server.

    python3 test_installer.py

The cases worth having are the refusals: a token signed by another key, an
archive whose hash does not match, and a tar member that tries to escape the
destination. Each must leave nothing unpacked.
"""
import base64, hashlib, importlib.util, io, json, os, shutil, sys, tarfile, tempfile, threading, time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

HERE = Path(__file__).resolve().parent
ROOT = Path(tempfile.mkdtemp())
CASES, FAILED = [], []


def check(n, c, extra=""):
    CASES.append((n, bool(c), extra))
    if not c:
        FAILED.append(n)


# ── keys ────────────────────────────────────────────────────────────────────
SK = Ed25519PrivateKey.generate()
PK_B64 = base64.b64encode(SK.public_key().public_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PublicFormat.Raw)).decode()
OTHER = Ed25519PrivateKey.generate()


def b64url(b):
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def mint(key, addons=("addon-outreach",), exp_delta=3600, grace_delta=7200):
    now = int(time.time())
    body = b64url(json.dumps({
        "lic": "LIC-1", "seat": "seat_1", "node": "n1", "plan": "core",
        "addons": list(addons), "iat": now,
        "exp": now + exp_delta, "grace": now + grace_delta,
    }, sort_keys=True).encode())
    return f"{body}.{b64url(key.sign(body.encode()))}"


# ── fixture bundles ─────────────────────────────────────────────────────────
def make_tar(entries):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for name, data in entries.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
    return buf.getvalue()


GOOD_FILES = {"README.md": b"hello\n", "shared/pipeline-rules.md": b"rules\n"}
MANIFEST = json.dumps({"seat": "seat_1", "files": {
    k: hashlib.sha256(v).hexdigest() for k, v in GOOD_FILES.items()}},
    sort_keys=True, separators=(",", ":"))
GOOD = make_tar({**GOOD_FILES, "MANIFEST.json": MANIFEST.encode(),
                 "MANIFEST.sig": b"x"})
ESCAPE = make_tar({"../../evil.md": b"pwned\n"})

MODE = {"token": "good", "bundle": "good", "hash": "good"}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, obj, raw=False):
        body = obj if raw else json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("content-type",
                         "application/gzip" if raw else "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        n = int(self.headers.get("content-length", 0))
        self.rfile.read(n)
        if self.path == "/v1/activate":
            key = SK if MODE["token"] == "good" else OTHER
            return self._send({"seat_id": "seat_1", "node_id": "n1",
                               "token": mint(key)})
        if self.path == "/v1/seats/release":
            return self._send({"ok": True})
        self._send({"error": "no"})

    def do_GET(self):
        if self.path == "/v1/bundles":
            blob = GOOD if MODE["bundle"] == "good" else ESCAPE
            sha = hashlib.sha256(blob).hexdigest()
            if MODE["hash"] == "bad":
                sha = "0" * 64
            return self._send({"bundles": [{"bundle_id": "b1", "scope": "core",
                                            "version": "1.0.0", "sha256": sha}]})
        if self.path.startswith("/v1/bundles/"):
            return self._send(GOOD if MODE["bundle"] == "good" else ESCAPE, raw=True)
        self._send({"error": "no"})


srv = HTTPServer(("127.0.0.1", 0), Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
API = f"http://127.0.0.1:{srv.server_port}"

os.environ["JH_API"] = API
os.environ["JH_PUBLIC_KEY"] = PK_B64
os.environ["HERMES_HOME"] = str(ROOT / "state")

spec = importlib.util.spec_from_file_location("inst", HERE / "installer.py")
inst = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inst)


def install(dest):
    class A:
        key, dest_ = "LIC-1", str(dest)
    a = A(); a.dest = str(dest)
    inst.cmd_install(a)


def main():
    # --- token verification -------------------------------------------------
    good = mint(SK)
    check("valid token verifies", inst.verify_token(good, PK_B64) is not None)
    check("token signed by another key is rejected",
          inst.verify_token(mint(OTHER), PK_B64) is None,
          "the pinned public key cannot mint — the point of Ed25519 over HMAC")
    body, sig = good.split(".")
    forged = json.loads(base64.urlsafe_b64decode(body + "=="))
    forged["addons"] = ["addon-outreach", "addon-presence", "addon-interview"]
    tampered = b64url(json.dumps(forged, sort_keys=True).encode()) + "." + sig
    check("edited entitlements are rejected", inst.verify_token(tampered, PK_B64) is None)
    check("garbage is rejected", inst.verify_token("not-a-token", PK_B64) is None)

    now = time.time()
    c = inst.verify_token(mint(SK, exp_delta=-10, grace_delta=3600), PK_B64)
    check("expired token enters grace, not failure",
          inst.token_state(c, now)[0] == "grace",
          "offline is the normal case for these users")
    c = inst.verify_token(mint(SK, exp_delta=-100, grace_delta=-10), PK_B64)
    check("past grace it expires", inst.token_state(c, now)[0] == "expired")

    # --- fingerprint --------------------------------------------------------
    fp = inst.fingerprint()
    check("fingerprint is stable", fp == inst.fingerprint())
    check("fingerprint is salted, not a raw device id",
          fp != hashlib.sha256(str(Path.home()).encode()).hexdigest()[:32])

    # --- happy path ---------------------------------------------------------
    dest = ROOT / "install"
    install(dest)
    check("files land", (dest / "README.md").is_file()
          and (dest / "shared" / "pipeline-rules.md").is_file())
    ok, bad = inst.verify_bundle(dest)
    check("bundle verifies against its manifest", ok, "; ".join(bad[:2]))
    check("token stored for offline use", (ROOT / "state" / "licence-token").is_file())

    # --- refusals -----------------------------------------------------------
    MODE["hash"] = "bad"
    d2 = ROOT / "bad-hash"
    try:
        install(d2); refused = False
    except SystemExit as e:
        refused = "did not arrive intact" in str(e)
    check("hash mismatch refuses to unpack", refused)
    check("nothing unpacked after a hash mismatch",
          not (d2 / "README.md").exists())
    MODE["hash"] = "good"

    MODE["bundle"] = "escape"
    d3 = ROOT / "escape"
    try:
        install(d3); refused = False
    except SystemExit as e:
        refused = "unexpected path" in str(e)
    check("tar member escaping the destination is refused", refused,
          "the oldest archive bug there is")
    check("nothing written outside the destination",
          not (ROOT / "evil.md").exists() and not (HERE / "evil.md").exists())
    MODE["bundle"] = "good"

    MODE["token"] = "wrong-key"
    d4 = ROOT / "wrongkey"
    try:
        install(d4); refused = False
    except SystemExit as e:
        refused = "could not be verified" in str(e)
    check("unverifiable token refuses to install", refused)
    check("nothing installed after an unverifiable token",
          not (d4 / "README.md").exists())
    MODE["token"] = "good"

    w = max(len(n) for n, _, _ in CASES)
    for n, ok_, extra in CASES:
        print(f"  {n:<{w}}  {'ok  ' if ok_ else 'FAIL'}{'  ' + extra if extra else ''}")
    print()
    srv.shutdown()
    shutil.rmtree(ROOT, ignore_errors=True)
    if FAILED:
        print(f"{len(FAILED)} failed: {FAILED}")
        sys.exit(1)
    print(f"{len(CASES)} checks pass")


if __name__ == "__main__":
    main()
