#!/usr/bin/env bash
# Tier 1 backup — see security/backup-and-recovery.md
#
# Deliberately NOT `cp applications.db backup-$(date).db`. Four reasons,
# each one a way that loses data:
#   1. cp on a live SQLite file can capture a mid-write state.
#   2. Copying an already-corrupt DB over the last good snapshot destroys
#      the only working copy. Integrity is checked BEFORE anything moves.
#   3. A single overwritten slot is not a backup. The realistic failure
#      is a bad write found a week later, so snapshots are versioned.
#   4. Tier 1 is not just the database — the memory files, the skill tree
#      (job 5 has been editing it since install) and the sent-artifact
#      archive are equally irreplaceable.
#
# Exit non-zero on any failure so the cron delivery is a real alert.

set -euo pipefail

SKILL_DIR="${SKILL_DIR:-$HOME/.hermes/skills/job-hunting}"
DEST="${BACKUP_DIR:-$HOME/.hermes/backups/job-hunting}"
HERMES_MEM="${HERMES_MEMORY_DIR:-$HOME/.hermes/memory}"
STAMP="$(date +%Y-%m-%dT%H%M)"
SNAP="$DEST/daily/$STAMP"

mkdir -p "$SNAP"

DB="$SKILL_DIR/shared/applications.db"
if [ -f "$DB" ]; then
  # (2) integrity first — refuse to snapshot a corrupt database
  RESULT="$(sqlite3 "$DB" 'PRAGMA integrity_check;' | head -1)"
  if [ "$RESULT" != "ok" ]; then
    echo "INTEGRITY CHECK FAILED: $RESULT" >&2
    echo "Last good snapshot left untouched. Investigate before re-running." >&2
    exit 1
  fi
  # (1) consistent snapshot of a possibly-live file
  sqlite3 "$DB" "VACUUM INTO '$SNAP/applications.db';"
  echo "db ok ($(sqlite3 "$SNAP/applications.db" 'SELECT COUNT(*) FROM applications;') applications)"
fi

# (4) the rest of Tier 1
for d in memory templates shared/sent_artifacts; do
  [ -d "$SKILL_DIR/$d" ] && cp -a "$SKILL_DIR/$d" "$SNAP/" || true
done

# the skill tree, minus anything derived
tar -czf "$SNAP/skills.tar.gz" -C "$SKILL_DIR" \
  --exclude='shared/applications.db*' \
  --exclude='shared/journal_export' \
  --exclude='shared/*_cache' \
  . 2>/dev/null || true

# BK3 — the Holographic fact store lives OUTSIDE the skill tree, which is
# exactly why it gets forgotten. Trust scores and contradiction history
# are not reconstructable.
[ -d "$HERMES_MEM" ] && tar -czf "$SNAP/hermes-memory.tar.gz" -C "$(dirname "$HERMES_MEM")" "$(basename "$HERMES_MEM")" || true

# BK7 — encrypt at rest. This holds a full resume, contact details,
# salary expectations and third-party enrichment data.
if [ -n "${BACKUP_GPG_RECIPIENT:-}" ]; then
  tar -czf - -C "$SNAP" . | gpg --batch --yes --encrypt \
      -r "$BACKUP_GPG_RECIPIENT" -o "$SNAP.tar.gz.gpg"
  rm -rf "$SNAP"
  SNAP="$SNAP.tar.gz.gpg"
else
  echo "WARNING: BACKUP_GPG_RECIPIENT unset — snapshot is unencrypted" >&2
fi

# BK5 — retention: 7 daily, 13 weekly, 12 monthly. Prune so backups don't
# become the thing that fills the disk.
ls -1dt "$DEST"/daily/* 2>/dev/null | tail -n +8 | xargs -r rm -rf
[ "$(date +%u)" = "7" ] && cp -a "$SNAP" "$DEST/weekly/" 2>/dev/null || true
ls -1dt "$DEST"/weekly/* 2>/dev/null | tail -n +14 | xargs -r rm -rf
[ "$(date +%d)" = "01" ] && cp -a "$SNAP" "$DEST/monthly/" 2>/dev/null || true
ls -1dt "$DEST"/monthly/* 2>/dev/null | tail -n +13 | xargs -r rm -rf

echo "[SILENT] backup ok: $SNAP"
