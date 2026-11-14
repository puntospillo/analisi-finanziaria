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
A ogni «aggiorna tutto» cercare le novità di 3 fonti e scrivere `/tmp/notizie_nuove.json` (lista di voci), poi `python3 tools/notizie.py /tmp/notizie_nuove.json` (deduplica, tiene 365 giorni in `notizie.json`; le voci dell'ultimo aggiornamento sono le «nuove», le altre stanno sotto «Precedenti»).
- Voce: `{fonte: casario|zerohedge|scenarieconomici, titolo, sintesi, url, data (YYYY-MM-DD|null), tema}`; titolo e sintesi in italiano, parafrasi con parole proprie (mai testo copiato, citazioni <15 parole), 3–7 voci per fonte.
- Marco Casario: profilo Substack https://substack.com/@marcocasario (≈29.000 iscritti; newsletter marcocasario.substack.com, NON raggiungibile da WebFetch: fuori allowlist); la pagina profilo non elenca i post. Telegram non trovato. Si usano i suoi episodi YouTube/podcast «The 10Min Trader» via ricerca web. Se l'utente indica il link esatto del canale, usarlo.
- ZeroHedge: WebFetch di zerohedge.com (articoli «Premium» solo titolo); Scenari Economici: WebFetch di scenarieconomici.it/economia/finanza/ (date solo relative: stimarle).
- Pubblicare anche `notizie.json` (aggiungerlo a `tools/pubblica.sh` se non è già incluso).
