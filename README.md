# Analisi Finanziaria

Dashboard sul rischio del mercato azionario americano (S&P 500): indice di rischio 0–100, quota in azioni consigliata per profilo (modello 2.0: allocazione adattiva + segnali precoci + rientro a tranche), valutazione di mercato con fonti, idee da approfondire, mercati esteri e materie prime, indicatori di sentiment e macro, prova sul passato.

**Sito:** https://puntospillo.github.io/analisi-finanziaria/ · versione in fondo alla pagina (v2.5.3).

## Come si aggiorna (solo su richiesta, con Claude)
- **«aggiorna»** → `bash tools/aggiorna.sh`: scarica i dati di borsa, ricalcola, controlla che la pagina si apra e pubblica (circa 1 minuto e mezzo). Se qualcosa fallisce i file pubblicati restano invariati.
- **«aggiorna tutto»** → `bash tools/aggiorna.sh --no-push`, `python3 tools/contesto.py`, ricerca delle notizie, `nuova.json` secondo `tools/VALUTAZIONE.md`, `python3 tools/valutazione.py nuova.json`, `bash tools/pubblica.sh "<messaggio>"`.

## File
`index.html` pagina · `lib/` librerie (d3, jsPDF, html-to-image) · `ifi_data.json` dati e indice · `extra_data.json` serie per i segnali precoci e S&P 500 con dividendi (`SPXTR`), agganciate per data · `valutazione.json` ultima valutazione · `update_status.json`, `valutazione_stato.json` stato · `archivio/` report mensili e opportunità · `cache/` dati riusati tra un aggiornamento e l'altro · `code/` calcolo · `tools/` comandi · `sorgenti/` sorgenti della pagina.

## Modello 2.3 (13/11/2026)
Blocco degli aumenti dopo uno shock forte (almeno 2 condizioni su 3): massimo 10 sedute dal primo shock, sblocco anticipato da 3 sedute con indice di rischio sotto 60 e S&P sopra la media a 20 giorni. Salita +20 punti a settimana, tendenza come quarto voto di ripresa, volatilità che non taglia oltre il 65%. Nel Consiglio: azione rispetto alla seduta precedente, indicazione Proteggi / Neutro / Rientro, ultime 15 sedute e dettaglio da inizio mese. Prove sul passato con i dividendi reinvestiti. Dati FRED scaricati serie per serie (FRED non risponde all'intestazione `Mozilla/5.0`).

## Novità 2.5 (14/11/2026)
Quattro profili con blocco dopo shock diverso: Prudente e Bilanciato 15 sedute, Dinamico 10, Reattivo 5 (nuovo: tetto 70%, rientro ogni 3 sedute, +20 con conferme, aumenti anche a metà settimana). Il modello di base si calcola per profilo (`computeAAVAll` → `AVP`). Questionario a 6 domande (4 rischio, 2 operatività).

## Novità 2.4 (13/11/2026)
Riquadro Italia (ETF EWI) negli «Altri mercati azionari», con approfondimento al clic: FTSE MIB in euro, confronto con le altre borse, settori, principali titoli e spread BTP-Bund (OECD via FRED). Dati in `indici.json` → `italia`.

## Avvertenza
Indicazioni generali basate su dati di mercato e su regole studiate sul passato; il modello 2.0 non è validato. Non è consulenza finanziaria personalizzata. Le idee sono spunti da approfondire.
