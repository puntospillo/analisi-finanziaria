#!/usr/bin/env bash
# Commit (autore Claude, noreply@anthropic.com, dal 20/11/2026) e push del repository. Uso: bash tools/pubblica.sh "<messaggio>" ["<righe di attribuzione>"]
set -euo pipefail
R="$(cd "$(dirname "$0")/.." && pwd)"; cd "$R"
git add -A
if git diff --cached --quiet; then echo "Nessuna modifica da pubblicare"; exit 0; fi
git -c user.name="Claude" -c user.email="noreply@anthropic.com" commit -qm "$1" ${2:+-m "$2"}
git fetch -q origin main 2>/dev/null && git rebase -q FETCH_HEAD 2>/dev/null || true
git push -q origin HEAD:main && echo "PUBBLICATO $(git log --oneline -1)"
