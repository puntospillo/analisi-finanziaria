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
- REGOLA FISSA (14/11): cercare sempre le notizie PIÙ RECENTI (oggi e ieri) per ogni fonte; mai riempire con articoli vecchi. Se una fonte non ha novità, lasciarla senza: la pagina scrive «Nessuna novità in questo aggiornamento» con la data dell'ultima voce. Prima di concludere che non c'è nulla, provare il metodo WebSearch+WebFetch sotto; mai saltare una fonte per un rifiuto di WebFetch sulla home.
- Come cercare (strumenti): Milano Finanza → WebSearch con allowed_domains ["milanofinanza.it"] (WebFetch non consentito); Scenari Economici → WebFetch diretto della home è RIFIUTATO (URL_NOT_ON_ALLOWLIST, verificato 17/11): usare WebSearch con allowed_domains ["scenarieconomici.it"] (query con data di oggi/ieri e temi: mercati, inflazione, energia, cripto, geopolitica), poi WebFetch dei link articolo trovati; prendere i più rilevanti per i mercati anche da altre sezioni (cripto, oro, energia, geopolitica), chiedendo nel prompt gli URL (date solo relative: stimarle dalla data di pubblicazione); ZeroHedge → stesso metodo: WebSearch con allowed_domains ["zerohedge.com"], poi WebFetch degli articoli (https; se un URL va in loop di redirect 302 salta quell'URL; articoli «Premium» = abbonamento:true); Notizie dal web → WebSearch «extended» con data di oggi e di ieri nella query (es. «Wall Street close November 13»), scartare risultati più vecchi di 2 giorni. Se la ricerca con allowed_domains su più siti esteri viene rifiutata dal proxy, rifarla senza filtro.
- Layout (lo fa la pagina): nuove in alto con etichetta «NUOVA» e conteggio nel riquadro colorato; ultimi 7 giorni in linea; «Prosegui» fino a 30 giorni; «Archivio» oltre il mese; articoli a pagamento in fondo con lucchetto.
- Recupero di un periodo passato: stesse voci con `arretrato:true` e `data` reale (non compaiono come nuove).
- Marco Casario: tolto (14/11).

## Rotazione delle idee (regola dal 16/11)
Ogni «aggiorna tutto» deve cambiare almeno 4 idee: non basta che la tesi regga. Mai riconfermare tutte (`riusa`) come il 12–16/11.
- Riscrivi con fatti nuovi (con fonte e data) le idee toccate dalla seduta: es. petrolio → energetiche, tassi → banche, IA → semiconduttori e tecnologia.
- Aggiungi o sostituisci almeno 1–2 idee con candidati nuovi, cercati con ricerche dedicate (conti trimestrali recenti, settori che reggono quando il mercato scende). Non inserire un nome senza cifre verificate e data; se manca un dato (es. capitalizzazione ≥1 mld per le opportunità rischiose) non inserirlo.
- Se non trovi 4 cambi con fonti valide, dillo nella `nota` del report e nella risposta, indicando quali idee restano ferme e perché.
- Aggiungi il simbolo Yahoo delle idee nuove in `code/simboli_idee.json`. Vincoli sui minimi per categoria e mercato restano invariati.

## Verifica dei dati esposti (regola fissa di Maurizio, 20/11/2026)
Dopo OGNI aggiornamento («aggiorna» e «aggiorna tutto») controllare tutti i dati esposti prima di darli per buoni e dire nella risposta l'esito (verificato / non verificato / scostamenti).
1. `python3 tools/verifica.py`: coerenza date, S&P e variazione giorno, massimo e media a 200 giorni, serie ferme, valutazione e notizie allineate ai dati (`aggiorna.sh` stampa già le righe non OK).
2. Confronto con fonti esterne (WebSearch): chiusura S&P 500 e variazione (SPY come proxy), Nasdaq 100 (QQQ), VIX, rendimento Treasury a 10 anni; per i titoli del giorno e i numeri di cronaca della valutazione la variazione e la causa. Scostamenti piccoli su dati serali (es. VIX) si dichiarano; fonti discordanti (es. probabilità di rialzo Fed) si dichiarano.
3. Testi ed etichette nuove: letti contro i numeri (es. «allerta rientrata» solo se il punteggio dei segnali precoci è sotto 55).
4. Non scrivere come certo ciò che non è verificato: etichetta [VERIFICATO] / [DEDOTTO] / [NON VERIFICATO].


## Lezioni dell'aggiornamento del 21/11/2026 (errori da non ripetere)
- **Chiusura contro metà seduta:** i comunicati Teleborsa a metà seduta e i commenti «al momento» non sono chiusure. Ogni numero di chiusura va da Reuters, dal riepilogo di chiusura o dalla dashboard; se si usa un dato intraday va scritto «a metà seduta». (Errore del 19/11: Anthropic «chiude a 95» era un dato di metà seduta, la chiusura fu 97,17, +17,1%.)
- **Dati discordanti:** se due fonti divergono (es. petrolio a 91 contro 83, spread 110,74 contro 106,07, oro 3.539 contro 3.515,7) si riporta quello della dashboard o della fonte di chiusura e si dichiara lo scarto in `concordanza`; mai copiare un dato dubbio in una notizia senza marcarlo «non verificato».
- **Probabilità dei future Fed:** variano per fonte (94% Reuters, 96,4% 24/7 Wall St): citare la fonte e l'ora oppure l'intervallo.
- **Indice che scende in una seduta di crollo:** non spiegarlo a parole generiche. L'indice della pagina è (fragilità + stress + 0,5 × «Grandi investitori») / 2,5; il gruppo «Grandi investitori» (CFTC, uscita settimanale del venerdì con circa 3 giorni di ritardo) può calare e togliere punti. Calcolare i contributi da `ifi_data.json` (colonne `p_FRAG`, `p_STRS`, `p_cot_am`, `p_cot_lev`) e scriverli in `concordanza`.
- **Soglie raggiunte:** se una soglia di «da monitorare» è stata superata, la voce successiva ne indica una nuova (nota: S&P 500 sotto 7.000 → ora 6.600).
- **Fonti bloccate:** ZeroHedge (proxy) e Scenari Economici/ZeroHedge non sempre leggibili: dire quali fonti non sono state lette; le notizie con data vecchia si segnano `arretrato`.
- **Etichette:** non usare «in molti casi» o simili senza numeri; citare i settori con il nome esatto della fonte.
