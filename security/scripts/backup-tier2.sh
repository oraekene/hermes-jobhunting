#!/usr/bin/env bash
# BK4 — weekly Tier 2 backup. See security/backup-and-recovery.md
#
# Tier 2 is regenerable, which is why this is weekly rather than nightly.
# But "regenerable" is not "free": individual_research_cache is built from
# METERED enrichment providers, so losing it means paying again for
# lookups already paid for. addendum_10's v_cost_per_outcome now measures
# exactly that, which turns this from a hunch into a number.
#
# Deliberately separate from backup.sh rather than a flag on it. Tier 1
# runs nightly and must never be skipped; Tier 2 is weekly and may be.
# One script with a mode flag invites running the cheap mode by habit.

set -euo pipefail

SKILL_DIR="${SKILL_DIR:-$HOME/.hermes/skills/job-hunting}"
DEST="${BACKUP_DIR:-$HOME/.hermes/backups/job-hunting}/tier2"
STAMP="$(date +%Y-%m-%d)"
SNAP="$DEST/$STAMP"
mkdir -p "$SNAP"

cd "$SKILL_DIR"

# Research caches — hours of crawling, and real money in the people cache.
for d in shared/company_research_cache \
         shared/individual_research_cache \
         shared/interview_intel_cache \
         shared/role_transition_intel_cache \
         shared/career_path_plans; do
  [ -d "$d" ] && cp -a "$d" "$SNAP/" || true
done

# Config seeded through conversations, not hand-filled. Small files,
# disproportionate rebuild cost.
mkdir -p "$SNAP/config"
for f in shared/*.yaml; do
  [ -f "$f" ] && cp -a "$f" "$SNAP/config/" || true
done

# Question bank and taxonomy index — deterministic but slow and
# dependency-heavy to rebuild.
[ -f shared/question_bank.yaml ] && cp -a shared/question_bank.yaml "$SNAP/" || true
for f in shared/*taxonomy*.db 07-context-architect/references/*.db; do
  [ -f "$f" ] && cp -a "$f" "$SNAP/" || true
done

# Staged, unapproved skill edits. Small window, but losing them loses
# proposals that were mid-judgement.
[ -d "$HOME/.hermes/pending/skills" ] && \
  cp -a "$HOME/.hermes/pending/skills" "$SNAP/pending-skills" || true

# NOT backed up, on purpose (BK8): the qmd index and shared/journal_export
# are derived. Backing them up costs the same storage and attention as a
# real backup while offering false reassurance — and journal_export is
# actively misleading, since it follows the database down rather than
# surviving it.

if [ -n "${BACKUP_GPG_RECIPIENT:-}" ]; then
  tar -czf - -C "$SNAP" . | gpg --batch --yes --encrypt \
      -r "$BACKUP_GPG_RECIPIENT" -o "$SNAP.tar.gz.gpg"
  rm -rf "$SNAP"; SNAP="$SNAP.tar.gz.gpg"
else
  echo "WARNING: BACKUP_GPG_RECIPIENT unset — Tier 2 snapshot is unencrypted" >&2
fi

# 8 weekly snapshots. Tier 2 loss is bounded and measurable, so the
# window is shorter than Tier 1's.
ls -1dt "$DEST"/* 2>/dev/null | tail -n +9 | xargs -r rm -rf

echo "[SILENT] tier2 backup ok: $SNAP"
