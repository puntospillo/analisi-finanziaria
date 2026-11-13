# Simulazione di un portafoglio con i segnali della dashboard (2010 → oggi)

Dashboard Analisi Finanziaria **v2.5** (14/11/2026) · modello di base (allocazione adattiva, calcolato per profilo) + segnali precoci · segnali calcolati con i dati al 13/11/2026 e i pesi predefiniti (consigliati + Grandi investitori istituzionali 0,50).

Novità rispetto al 13/11/2026: quattro profili (nuovo **Reattivo**) e blocco degli aumenti dopo uno shock diverso per profilo (15 sedute Prudente e Bilanciato, 10 Dinamico, 5 Reattivo). I valori **non coincidono con i file precedenti**.

## File allegati

| File | Contenuto |
|---|---|
| `segnali_giornalieri_2010_oggi.csv` | Una riga per seduta (01/12/2009 → 13/11/2026, 4.265 righe). File principale. Separatore `;`, decimali con la virgola. Si scarica da https://puntospillo.github.io/analisi-finanziaria/simulazione/segnali_giornalieri_2010_oggi.csv (troppo grande per i documenti del progetto). |
| `segnali_mensili_2010_oggi.csv` | Una riga per mese: quote a fine mese (novembre 2026 = 13/11). Separatore `;`. |

### Colonne (file giornaliero)
- `quota_prudente`, `quota_bilanciato`, `quota_dinamico`, `quota_reattivo`: quota in azioni consigliata (0–100, passi del 10%) alla chiusura USA della seduta, per profilo. È la quota del riquadro Consiglio.
- `quota_<profilo>_da_applicare`: le stesse spostate di una seduta. **Sono quelle da usare nelle simulazioni** (il segnale di oggi si esegue domani).
- `quota_base_bilanciato` e `aumenti_sospesi`: quota del modello di base e blocco dopo shock (1 = aumenti sospesi) del profilo Bilanciato.
- `indice_rischio` (0–100), `volatilita_20g` (% annua a 20 sedute), `sp500` (solo prezzo), `sp500_con_dividendi` (indice con dividendi reinvestiti, `^SP500TR`), `media200`.
- `liquidita_rend_giorno`: rendimento giornaliero della liquidità in dollari (T-bill a 3 mesi / 252).

### Come nasce la quota (per capirla, non serve ricalcolarla)
Modello di base: sei pilastri 0–100 (tendenza 20%, momento 20%, ampiezza 20%, rischio interno 20%, credito 15%, macro 5%) → regime (rialzo confermato 80–100, fragile 50–70, stress 20–40, ripresa 40–70) → × 12% / volatilità a 20 sedute (tra 0,35 e 1) → tetti 20% (emergenza) e 60% (fragilità) → esecuzione graduale (tagli fino a 20 punti al giorno, aumenti di 20 punti a fine settimana, 25 al giorno in ripresa; Reattivo 10 punti in ogni seduta).
Blocco dopo uno shock forte (almeno 2 condizioni su 3): aumenti sospesi al massimo 15 sedute (Prudente, Bilanciato), 10 (Dinamico), 5 (Reattivo) dal primo shock, con sblocco anticipato se l'indice di rischio scende e l'S&P torna sopra la media a 20 giorni.
Segnali precoci: se confermati mettono un tetto (Prudente 40%, Bilanciato 50%, Dinamico 60%, Reattivo 70%), che poi risale a tranche di 10 punti (Reattivo 20 con conferme).

### Riferimento (S&P 500 con dividendi reinvestiti, senza costi, liquidità al T-bill, quota `_da_applicare`)
| Dal 2010 | Rendimento annuo | Perdita massima | Quota media |
|---|---|---|---|
| Prudente | 7,2% | −11,2% | 60% |
| Bilanciato | 7,7% | −11,4% | 65% |
| Dinamico | 8,0% | −11,3% | 67% |
| Reattivo | 8,7% | −12,0% | 70% |
| Sempre investito | 14,0% | −34% | 100% |

Dal 2000: Bilanciato 6,5% / −12%, Reattivo 7,2% / −13%, sempre investito 8,3% / −55%. Il Reattivo cambia quota circa 35 volte l'anno (Bilanciato 26): con costi dello 0,1% per operazione perde circa mezzo punto l'anno, tasse escluse. Il vantaggio dei modelli è sulla perdita massima, non sul rendimento; si concentra in poche crisi ed è in-sample.

## Cosa portare nell'altra chat
1. Questo documento e i due CSV (il mensile è nei documenti del progetto Finanza, il giornaliero si scarica dal link qui sopra).
2. Il portafoglio di esempio, per ogni strumento: nome, ticker e/o ISIN, peso % (o importo), se è **azionario** o no (obbligazioni, oro, liquidità…), valuta.
3. Il profilo da usare (se non lo indichi: Bilanciato) e le scelte della simulazione (se non le indichi si usano quelle tra parentesi):
   - capitale iniziale (100.000 €) e data di inizio (primo giorno di borsa del 2010);
   - dove va la parte tolta alle azioni (liquidità in euro a rendimento €STR/Euribor 3 mesi; in alternativa un ETF monetario o obbligazionario breve);
   - ribilanciamento (quando la quota cambia, e una volta al mese se i pesi si scostano di oltre 5 punti);
   - costi per operazione (0,10% sul controvalore scambiato) e tasse (escluse; eventualmente 26% sulle plusvalenze realizzate);
   - valuta di calcolo (euro; strumenti in dollari convertiti al cambio del giorno).

## Regola di applicazione al portafoglio
- La quota (es. 70%) indica quanta parte **della componente azionaria del portafoglio** tenere: con 60% azioni e quota 70%, le azioni scendono a 60 × 0,70 = 42% e il 18% liberato va nella destinazione scelta. Le parti non azionarie restano.
- Le azioni si riducono in proporzione tra tutti i titoli/ETF azionari (nessun cambio di composizione).
- Quota 100% = portafoglio originale.
- Confronto obbligatorio con il portafoglio originale sempre investito (stesso ribilanciamento). Facoltativo: la stessa regola con quota fissa 65% (circa la quota media del Bilanciato), per separare l'effetto dei segnali da quello della sola esposizione ridotta.

## Risultati da chiedere
Valore finale, rendimento annuo, volatilità, perdita massima e date, peggior anno, tempo per recuperare le perdite, quota media in azioni, numero di operazioni e costi; grafico del valore nel tempo con le fasce di difesa; tabella anno per anno; i 5 momenti in cui la quota ha aiutato di più e i 5 in cui ha danneggiato di più.

## Limiti da tenere presenti
- Segnali calcolati sul **mercato americano** (S&P 500): applicarli a titoli europei o italiani è un'ipotesi.
- Soglie, pesi e regole sono stati scelti guardando gli stessi anni: test non fuori campione. Bias di sopravvivenza prima del 2010 (universo S&P 500 ricostruito).
- Servono prezzi storici giornalieri o mensili di ogni strumento dal 2010 (prezzi adjusted). Se uno strumento è nato dopo il 2010 va sostituito (indice/ETF simile) o fatto entrare dalla sua data.
- Le quote storiche usano le regole e i pesi di oggi: se cambiano, i segnali cambiano.
- Non è una consulenza: tasse, costi reali e situazione personale cambiano il risultato.

## Testo da incollare nell'altra chat
> Allego `simulazione-portafoglio.md`, `segnali_mensili_2010_oggi.csv`, `segnali_giornalieri_2010_oggi.csv` e il mio portafoglio di esempio. Fai una simulazione storica dal primo giorno di borsa del 2010 a oggi applicando ogni giorno la colonna `quota_bilanciato_da_applicare` (o quella del profilo che indico) del file giornaliero alla sola parte azionaria del portafoglio, come descritto nel documento (destinazione della parte tolta, ribilanciamento, costi, valuta: usa le scelte indicate tra parentesi se non specifico diversamente). I file usano `;` come separatore e la virgola per i decimali. Scarica i prezzi storici adjusted degli strumenti; se mancano dati dimmelo prima di sostituire. Confronta con il portafoglio sempre investito e con una quota fissa 65%. Dammi i risultati elencati in "Risultati da chiedere" in una pagina interattiva in cui posso cambiare capitale, profilo, destinazione della liquidità, costi e soglia di ribilanciamento. Distingui dati verificati, deduzioni e dati mancanti.
