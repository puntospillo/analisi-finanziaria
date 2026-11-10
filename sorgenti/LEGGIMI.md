Sorgenti della pagina (v2.0). `build.py` applica le modifiche in `frag/` e `engine2.js` a `base_3.8.1.html` e scrive la pagina.
I percorsi in testa a `build.py` (SRC, DST, FR, engine2.js) sono assoluti: adattarli prima di lanciarlo. La pagina pubblicata è `../index.html`
(stesso risultato, con intestazione HTML completa; librerie in `../lib/`, dati JSON nella radice). Per piccole modifiche si può correggere direttamente `../index.html` e riportare la modifica in `frag/`.
