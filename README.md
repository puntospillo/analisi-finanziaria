# Analisi Finanziaria

Dashboard sul rischio del mercato azionario americano (S&P 500): indice di rischio 0–100, quota in azioni consigliata per profilo (modello 2.0: allocazione adattiva + segnali precoci + rientro a tranche), valutazione di mercato con fonti, idee da approfondire, mercati esteri e materie prime, indicatori di sentiment e macro, prova sul passato.

**Sito:** https://puntospillo.github.io/analisi-finanziaria/ · versione in fondo alla pagina (v2.0).

## Come si aggiorna (solo su richiesta, con Claude)
- **«aggiorna»** → `bash tools/aggiorna.sh`: scarica i dati di borsa, ricalcola, controlla che la pagina si apra e pubblica (circa 1 minuto e mezzo). Se qualcosa fallisce i file pubblicati restano invariati.
- **«aggiorna tutto»** → `bash tools/aggiorna.sh --no-push`, `python3 tools/contesto.py`, ricerca delle notizie, `nuova.json` secondo `tools/VALUTAZIONE.md`, `python3 tools/valutazione.py nuova.json`, `bash tools/pubblica.sh "<messaggio>"`.

## File
`index.html` pagina · `lib/` librerie (d3, jsPDF, html-to-image) · `ifi_data.json` dati e indice · `extra_data.json` serie per i segnali precoci · `valutazione.json` ultima valutazione · `update_status.json`, `valutazione_stato.json` stato · `archivio/` report mensili e opportunità · `cache/` dati riusati tra un aggiornamento e l'altro · `code/` calcolo · `tools/` comandi · `sorgenti/` sorgenti della pagina.

## Avvertenza
Indicazioni generali basate su dati di mercato e su regole studiate sul passato; il modello 2.0 non è validato. Non è consulenza finanziaria personalizzata. Le idee sono spunti da approfondire.
