#!/usr/bin/env bash
# BK6 — quarterly restore verification.
#
# A backup nobody has restored is a hypothesis. This restores the newest
# snapshot into a scratch directory, asserts it is a working database
# with plausible contents, and deletes it. Loud on failure.
set -euo pipefail

DEST="${BACKUP_DIR:-$HOME/.hermes/backups/job-hunting}"
LIVE="${SKILL_DIR:-$HOME/.hermes/skills/job-hunting}/shared/applications.db"
SCRATCH="$(mktemp -d)"
trap 'rm -rf "$SCRATCH"' EXIT

NEWEST="$(ls -1dt "$DEST"/daily/* 2>/dev/null | head -1 || true)"
[ -n "$NEWEST" ] || { echo "NO SNAPSHOTS FOUND in $DEST/daily" >&2; exit 1; }

if [[ "$NEWEST" == *.gpg ]]; then
  gpg --batch --yes --decrypt "$NEWEST" | tar -xzf - -C "$SCRATCH"
else
  cp -a "$NEWEST"/. "$SCRATCH"/
fi

DB="$SCRATCH/applications.db"
[ -f "$DB" ] || { echo "RESTORE FAILED: no applications.db in $NEWEST" >&2; exit 1; }

[ "$(sqlite3 "$DB" 'PRAGMA integrity_check;' | head -1)" = "ok" ] \
  || { echo "RESTORE FAILED: restored database is corrupt" >&2; exit 1; }

N="$(sqlite3 "$DB" 'SELECT COUNT(*) FROM applications;')"
[ "$N" -gt 0 ] || { echo "RESTORE FAILED: restored database has no applications" >&2; exit 1; }

# Compare against live. A snapshot with far fewer rows than the live DB
# means backups silently stopped working at some point; a snapshot with
# MORE rows means the live database lost data. Both are worth an alarm.
if [ -f "$LIVE" ]; then
  L="$(sqlite3 "$LIVE" 'SELECT COUNT(*) FROM applications;')"
  if [ "$N" -lt $(( L * 9 / 10 )) ]; then
    echo "RESTORE WARNING: snapshot has $N applications, live has $L" >&2; exit 1
  fi
  if [ "$N" -gt "$L" ]; then
    echo "RESTORE WARNING: snapshot has MORE rows ($N) than live ($L) — live may have lost data" >&2; exit 1
  fi
fi

echo "[SILENT] restore verified: $NEWEST, $N applications, integrity ok"
