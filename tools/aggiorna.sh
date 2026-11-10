#!/usr/bin/env bash
# Aggiorna i dati di borsa e pubblica. Uso: bash tools/aggiorna.sh [--no-push]
# Scarica (Yahoo, CFTC, AAII, CAPE, SPY), ricalcola l'indice, aggiorna extra_data.json, archivio mensile e update_status.json.
# Se qualcosa fallisce non tocca i file pubblicati. Stampa poche righe di riepilogo.
set -uo pipefail
R="$(cd "$(dirname "$0")/.." && pwd)"; W="$(mktemp -d)"; L="$W/log.txt"
python3 -c "import pandas, numpy, xlrd, openpyxl" 2>/dev/null || pip install -q --break-system-packages pandas numpy xlrd openpyxl >/dev/null 2>&1
git -C "$R" pull -q --rebase origin main 2>/dev/null || true
mkdir -p "$W/dati/raw" "$W/dati/cache"
cp "$R/cache/ampiezza_storico.csv" "$W/dati/raw/fattori_storico.csv"; cp "$R/code/fred_cache.txt" "$W/dati/raw/fred.txt"; cp "$R/cache/aaii_sentiment.xls" "$R/cache/cape.html" "$W/dati/raw/" 2>/dev/null
fail() { echo "ERRORE: $1"; tail -5 "$L"; echo "Dati pubblicati invariati."; exit 1; }
python3 "$R/code/fetch_data.py" "$W" >"$L" 2>&1 || fail "scarico dati"
python3 "$R/code/ifi_pipeline.py" "$W" >>"$L" 2>&1 || fail "calcolo indice"
python3 -W ignore "$R/code/scarica_extra.py" "$W/dati/ifi_data.json" "$W/extra_data.json" >>"$L" 2>&1 || fail "serie aggiuntive"
python3 -W ignore "$R/code/scarica_indici.py" "$W/indici.json" >>"$L" 2>&1 && cp "$W/indici.json" "$R/indici.json" || echo "WARN indici non aggiornati"
python3 "$R/tools/dopo_dati.py" "$W" "$R" >>"$L" 2>&1 || fail "controllo finale"; grep -h "^DATI" "$L"
python3 "$R/tools/contesto.py" --breve || { git -C "$R" checkout -q -- . ; fail "la pagina non si apre con i nuovi dati"; }
grep -h "^WARN" "$L" | head -3
[ "${1:-}" = "--no-push" ] && exit 0
bash "$R/tools/pubblica.sh" "Aggiorna: dati al $(python3 -c "import json;print(json.load(open('$R/update_status.json'))['as_of'])")"
