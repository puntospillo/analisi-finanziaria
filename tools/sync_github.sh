#!/usr/bin/env bash
# Pubblica su GitHub i file dell'artifact già letti in una cartella.
# Uso: bash tools/sync_github.sh <cartella_file_artifact> <repo> "<messaggio commit>"
set -euo pipefail
SRC="$1"; REPO="$2"; MSG="$3"
python3 "$REPO/tools/make_github.py" "$SRC" "$REPO"
cd "$REPO"
git add -A
if git diff --cached --quiet; then echo "Nessuna modifica da pubblicare"; exit 0; fi
git -c user.name="puntospillo" -c user.email="pippo.pagani@gmail.com" commit -qm "$MSG"
git fetch -q origin main 2>/dev/null && git rebase -q origin/main 2>/dev/null || true
git push -q origin HEAD:main
git log --oneline -1
