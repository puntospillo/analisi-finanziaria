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

`titoli_giorno` (obbligatorio, sotto «Da seguire»): esegui `python3 code/titoli_giorno.py /tmp/titoli_cand.json` (dopo `aggiorna.sh`): sceglie i 3 titoli con più rilievo tra i primi 30 per peso (peso SPY × variazione dell'ultima seduta, bonus ×2 per volumi alti). Per ognuno dei primi 3 cerca la notizia del giorno (1 ricerca ciascuno) e scrivi:
`{"metodo": <dal file>, "pesi_al": <dal file>, "titoli":[ {"nome","ticker","peso","prezzo","data","g1","vol_rel","contributo" (copiati dal file), "perche" (1–2 frasi), "situazione":[3–4 fatti con numeri], "analisi":[5 punti: cosa è successo · perché conta per l'indice · valutazione · cosa guardare · rischi], "fonti":[{"nome","url","data"}]} ]}`.
Se la causa del movimento non si trova, scrivilo («non verificata»). Fonti secondarie/automatiche: dichiarale tali. Mai «compra/vendi».
