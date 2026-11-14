# Schema di `nuova.json` (comando «aggiorna tutto»)
Scrivi SOLO questi campi; il resto (date, numeri della dashboard, elenco fonti, archivio) lo aggiunge `tools/valutazione.py`.
Fatti solo con fonte e data dalle ricerche di oggi; niente numeri a memoria. Italiano semplice, frasi brevi. Mai «compra/vendi»: idee sempre «da approfondire».
Non scrivere quota e azione (le calcola la pagina) né spiegazioni del metodo.

```
{ "livello": "basso|moderato|elevato|alto",            // coerente con l'indice di rischio di NUMERI
  "titolo": "una frase",
  "in_breve": ["Rischio: …", "Cosa fare: indicazione generale del modello …"],
  "esterno": [ {"tema","lettura" (1–2 frasi con numeri),"segno":"più rischio|neutro|meno rischio","fonte","url","data":"AAAA-MM-GG"} ],   // 5–7
  "concordanza": "2–3 frasi: dove dashboard e fonti concordano o no",
  "monitorare": [ {"cosa","perche","soglia","guardare" (1–2 frasi), "notizie":[{"testo","fonte","url","data"}]} ],   // 4–6 voci, 2–4 notizie ciascuna
  "idee": [ {"riusa":"<nome esatto della precedente>"}                                   // tesi ancora valida: costa pochissimo
            | {"categoria":"azione|etf|materia prima|obbligazioni","mercato","nome","ticker","direzione":"interessante|da evitare|opportunità rischiosa",
               "tesi","perche_ora","rischi","orizzonte","prezzo_rif","fonte","url","data"} ],   // 8–24; sostituisci solo quelle superate dai fatti
  "report": { "precedente":[5–6 righe: data e livello della valutazione prima di questa, indice e quota, cosa diceva (cause, quadro), le soglie che si guardavano, cosa è successo da allora], "precedente_titolo":"es. 9 novembre sera", "cambiato":[3–5 fatti nuovi], "situazione":[3–5 paragrafi],
              "temi":[ {"titolo","testo" (2–3 frasi),"segno","grafico"?,"fonte"?,"url"?,"data"?} ],
              "nota": "solo se serve" } }
```
`report.temi`: prima i sei con grafico, in quest'ordine: `spx`, `ndx`, `ampiezza`, `vix`, `credito`, `settori`; poi senza grafico: tassi e banche centrali, utili, petrolio e oro, Italia, valute, calendario.
Facoltativi (se mancano restano quelli precedenti): `idee_premessa`, `limiti`.

Regola: «aggiorna tutto» NON usa il report del mese. Tutto (esteri, materie prime, cambi, tassi, cripto, indici) è calcolato all'ultima seduta da `aggiorna.sh`. `valutazione.py` aggiorna da solo i prezzi di riferimento delle idee (`code/prezzi_idee.py`, simboli in `code/simboli_idee.json`: aggiungi il simbolo Yahoo delle idee nuove).

`titoli_giorno` (obbligatorio, sotto «Da seguire»): esegui `python3 code/titoli_giorno.py /tmp/titoli_cand.json` (lo fa già `contesto.py`): sceglie i 3 titoli con più rilievo tra i primi 30 per peso (peso SPY × variazione dell'ultima seduta, bonus ×2 per volumi alti) e scrive anche la serie dei prezzi. Per i primi 3 cerca la notizia del giorno (1 ricerca ciascuno) e scrivi:
`{"metodo","pesi_al" (dal file), "titoli":[ {"nome","ticker","peso","prezzo","data","g1","vol_rel","contributo","serie" (tutti copiati dal file), "perche" (1–2 frasi), "cosa_fa" (1 riga: che cosa fa la società), "situazione":[3–4 fatti con numeri], "commento" (UN solo paragrafo: cosa è successo, perché conta per l'indice, cosa guardare, limiti), "fonti":[{"nome","url","data"}]} ]}`.
Il colore del riquadro lo calcola la pagina dalla variazione del giorno. Se la causa non si trova scrivilo («non verificata»). Fonti secondarie/automatiche: dichiarale tali. Mai «compra/vendi».
`report.precedente`: 4 righe (livello e indice, quadro, soglie osservate, cosa è successo da allora).

## Notizie per fonte (v2.6)
Pagina Notizie = solo notizie. Colonne da sinistra: Notizie dal web, Milano Finanza, Scenari Economici, ZeroHedge. A ogni «aggiorna tutto»: cercare le novità, scrivere `/tmp/notizie_nuove.json` (un solo Write) e lanciare `python3 tools/notizie.py /tmp/notizie_nuove.json` (deduplica; tiene 365 giorni; stampa le nuove per fonte).
- Voce: `{fonte: web|milanofinanza|scenarieconomici|zerohedge, titolo, sintesi, url, data (AAAA-MM-GG|null), tema, abbonamento (true = a pagamento: lucchetto, niente link), sito (solo web), arretrato (true solo per recuperi: non «nuova»)}`. Temi ammessi (colori fissi): Mercati, Piazza Affari, Tassi, Macro, USA, Tecnologia, Energia, Materie prime, Geopolitica, Banche, Obbligazioni, Valute, Cripto.
- Titolo e sintesi in italiano con parole proprie (citazioni <15 parole); sintesi di 3-6 frasi con cifre e nomi; 4-10 voci per fonte. Una sintesi riporta solo ciò che dice la fonte: nessuna interpretazione aggiunta.
- REGOLA FISSA (14/11): cercare sempre le notizie PIÙ RECENTI (oggi e ieri) per ogni fonte; mai riempire con articoli vecchi. Se una fonte non ha novità, lasciarla senza.
- Come cercare (strumenti): Milano Finanza → WebSearch con allowed_domains ["milanofinanza.it"] (WebFetch non consentito); Scenari Economici → WebFetch di scenarieconomici.it/economia/finanza/ (date solo relative: stimarle dalla data di pubblicazione); ZeroHedge → WebFetch di zerohedge.com (articoli «Premium» = abbonamento:true); Notizie dal web → WebSearch «extended» con data di oggi e di ieri nella query (es. «Wall Street close November 13»), scartare risultati più vecchi di 2 giorni. Se la ricerca con allowed_domains su più siti esteri viene rifiutata dal proxy, rifarla senza filtro.
- Layout (lo fa la pagina): nuove in alto con etichetta «NUOVA» e conteggio nel riquadro colorato; ultimi 7 giorni in linea; «Prosegui» fino a 30 giorni; «Archivio» oltre il mese; articoli a pagamento in fondo con lucchetto.
- Recupero di un periodo passato: stesse voci con `arretrato:true` e `data` reale (non compaiono come nuove).
- Marco Casario: tolto (14/11).
