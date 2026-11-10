import re, sys
SRC='/home/claude/af2/src/index.html'; DST='/home/claude/af2/v2/index.html'; FR='/home/claude/af2/work/frag/'
s=open(SRC,encoding='utf8').read()
def rd(n): return open(FR+n,encoding='utf8').read()
def rep(old,new,cnt=1):
    global s
    n=s.count(old)
    assert n==cnt, ('attese %d, trovate %d: %r' % (cnt,n,old[:90]))
    s=s.replace(old,new)
# ---------- testata
rep('<title>Analisi Finanziaria</title>','<title>Analisi Finanziaria 2.0 (locale)</title>')
rep('<h1>Analisi Finanziaria<button class="ver"','<h1>Analisi Finanziaria 2.0<button class="ver"')
rep('<p class="muted">S&amp;P 500 · Valori calcolati su dati reali di mercato</p>','<p class="muted">S&amp;P 500 · Valori calcolati su dati reali di mercato</p>')
rep('<a href="#stato">Situazione</a><a href="#grafico">Grafico</a><a href="#fattori">Pesi e fattori</a><a href="#conferma">Indicatori esterni</a><a href="#report">Report del mese</a><a href="#backtest">Prova sul passato</a><a href="#calibrazione">Affidabilità</a><a href="#metodo">Metodo</a>',
    '<a href="#stato">Situazione</a><a href="#mercato">Valutazione di mercato</a><button type="button" class="navbtn tech-btn" data-tech="t" aria-pressed="true">Come ci siamo arrivati</button><a href="#esteri">Esteri e materie prime</a><a class="tl" href="#grafico">Grafico</a><a class="tl" href="#fattori">Fattori</a><a class="tl" href="#conferma">Indicatori esterni</a><a href="#calibrazione">Affidabilità</a><a href="#metodo">Metodo</a><a href="#confronto">Prove del modello</a><a href="#backtest">Prova sul passato</a>')
rep('<button type="button" class="navbtn" id="btnOpenAll">Apri tutto</button><button type="button" class="navbtn" id="btnCloseAll">Chiudi tutto</button>','<button type="button" class="navbtn tl" id="btnOpenAll">Apri tutto</button><button type="button" class="navbtn tl" id="btnCloseAll">Chiudi tutto</button>')
# ---------- stile, librerie locali, caricamento locale
rep('</style>\n','\n'+rd('style.css')+'</style>\n',1) if s.count('</style>\n')==1 else None
if rd('style.css')[:30] not in s:
    k=s.rindex('</style>', 0, s.index('<div class="wrap">')); s=s[:k]+rd('style.css')+s[k:]
rep('<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script>','<script>\n'+rd('shim.js')+'</script>\n<script src="lib/d3.min.js"></script>')
rep("const LIBS = ['https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js', 'https://cdnjs.cloudflare.com/ajax/libs/html-to-image/1.11.11/html-to-image.min.js'];","const LIBS = ['lib/jspdf.umd.min.js', 'lib/html-to-image.min.js'];")
# ---------- finestra del profilo
rep('<dialog class="help" id="helpDlg"', rd('html_dialog.txt')+'<dialog class="help" id="helpDlg"')
# ---------- prima schermata
rep(rd('html_hero_old.txt'), rd('html_hero_new.txt'))
rep('  <section class="hero" id="stato" aria-label="Situazione">\n','  <section class="hero" id="stato" aria-label="Situazione">\n    <div class="card adv-card clickable" id="advCard" data-help="consiglio" tabindex="0"></div>\n')
# ---------- sezioni: riordino e nuova sezione confronto
L=s.split('\n')
a=next(i for i,l in enumerate(L) if l.startswith('  <section class="card" id="grafico">'))
b=next(i for i,l in enumerate(L) if l.startswith('  <p class="foot" id="footNote">'))
blocks={}; cur=None; order=[]
for l in L[a:b]:
    m=re.match(r'  <section class="[^"]*" id="(\w+)"',l)
    if m: cur=m.group(1); blocks[cur]=[]; order.append(cur)
    blocks[cur].append(l)
assert order==['grafico','oggi','fattori','calibrazione','conferma','report','backtest','spaccatura','metodo'], order
fat='\n'.join(blocks['fattori'])
assert '<div class="wlive" id="wLive" aria-live="polite"></div>' in fat
fat=fat.replace('<div class="wlive" id="wLive" aria-live="polite"></div>','<div class="wlive" id="wLive" aria-live="polite"></div>\n    <div class="nowbox wide" id="factNow" style="margin-bottom:10px"></div>')
fat=fat.replace('<h2>Fattori e pesi<button','<h2>Fattori dell\'indice di rischio<button')
blocks['fattori']=fat.split('\n')
fat=fat.replace('<button class="btn" type="button" id="btnTop50">Primi 50 titoli per peso</button></div>','<div style="display:flex;gap:6px;flex-wrap:wrap"><button class="btn" type="button" data-help="pesidist">Come sono distribuiti i pesi</button><button class="btn" type="button" id="btnTop50">Primi 50 titoli per peso</button></div></div>')
assert 'data-help="pesidist"' in fat
blocks['fattori']=fat.split('\n')
new=rd('html_mercato.txt').split('\n')+rd('html_tech.txt').rstrip('\n').split('\n')
for k in ['grafico','fattori','conferma']: new+=blocks[k]
new+=['  </div>','  <div class="tech" id="deep">']
for k in ['calibrazione','spaccatura','metodo']: new+=blocks[k]
new+=rd('html_confronto.txt').split('\n')
new+=blocks['backtest']
new+=['  </div>','  <div id="oldRep" hidden>']+blocks['report']+['  </div>']
L[a:b]=new; s='\n'.join(L)
# ---------- versione
rep("const APP_VERSION = '3.8.1';","const APP_VERSION = '2.0';")
rep("const CHANGELOG = [\n","const CHANGELOG = [\n  ['2.0', '10/11/2026', ['Nuova versione 2.0: sostituisce la 3.8.1 con un modello semplificato e un pannello pensato per chi investe.', 'Pulsanti in alto: Notizie (la valutazione di mercato con fonti), Idee da approfondire, Peso S&P 500 e Report. Cliccando una voce di «Da seguire» si aprono le notizie approfondite su quel punto.', 'Cliccando il grafico dell\\'indice di rischio si vede l\\'andamento a 12 mesi con i numeri colorati e la data al passaggio del mouse.', 'Ogni indicatore di sentiment, grandi investitori, valutazione e macro ha la sua scheda con grafici, indicazioni e storico.', 'Nuovo modello di quota: al modello di base (allocazione adattiva, invariato) si aggiungono i segnali precoci (ampiezza, titoli medi contro indice, credito, grandi titoli tecnologici, rotazione verso i difensivi) e una regola di rientro a tranche.', 'Pannello della propensione al rischio: quattro domande, tre profili fissi (Prudente, Bilanciato, Dinamico) e quota massima in azioni.', 'Pesi e soglie fissi: tolti i cursori dei pesi e i comandi della regola.', 'Esposizione semplificata: in alto solo il Consiglio con una frase che spiega il motivo, l\\'indice di rischio e la quota mese per mese. Metodo e numeri sono dietro al bottone «Come ci siamo arrivati».', 'La valutazione di mercato è nel corpo della pagina al posto del report del mese, con la data di aggiornamento in evidenza e i temi del momento con i loro grafici.', 'Fattori dell\\'indice in forma compatta; i pesi si vedono dal bottone «Come sono distribuiti i pesi».', 'Nuova sezione Prove del modello: risultati sul passato per profilo.', 'Alla prima apertura chiede il nome e il profilo di investitore; restano memorizzati e si possono cambiare quando si vuole.', 'Funziona con un doppio clic, senza internet: dati e librerie sono nella cartella.']],\n")
# ---------- pesi congelati e memoria separata dalla versione online
rep("const LSW = 'rm-weights-v3';","const LSW = 'af2-ui-v1';")
rep("const LSF = 'rm-folds-v1';","const LSF = 'af2-folds-v2';")
s=s.replace("'rm-my-eq'","'af2-max-eq'")
rep("""  for (const k of Object.keys(st.w)) if (typeof v.w[k] === 'number') st.w[k] = v.w[k];
  for (const k of Object.keys(st.wc)) if (v.wc && typeof v.wc[k] === 'number') st.wc[k] = v.wc[k];
  for (const k of ['gF', 'gS', 'gI', 'gSe', 'gM']) if (typeof v[k] === 'number') st[k] = v[k];
  st.preset = v.preset || null; applyUi(v.ui); return true;""","""  /* v4.0: pesi e gruppi fissi, si ripristinano solo le scelte di visualizzazione */
  st.preset = null; applyUi(v.ui); return true;""")
rep("""  if (typeof u.th === 'number' && u.th >= 50 && u.th <= 90) st.th = u.th;
  if (typeof u.hold === 'number' && u.hold >= 1 && u.hold <= 250) st.hold = Math.round(u.hold);
  if (typeof u.lvl === 'number' && u.lvl >= 0 && u.lvl <= 0.5) st.lvl = u.lvl;
  if (typeof u.trend === 'boolean') st.trend = u.trend;
""","")
rep("if (typeof u.myeq === 'number' && u.myeq >= 0 && u.myeq <= 100 && u.myeq % 5 === 0) { MYEQ = u.myeq; try { localStorage.setItem('af2-max-eq', String(MYEQ)); } catch (e) {} }","")
rep("if (restored) { const ws = document.getElementById('wSaved'); if (ws) ws.textContent = 'Pesi ripristinati dalla tua ultima visita.';","if (restored) {")
# ---------- motore 2.0
eng=open('/home/claude/af2/work/engine2.js',encoding='utf8').read()
eng=eng.replace("function computeIFI2() { computeFeat2(); Q2 = {}; for (const k in PROF) Q2[k] = runIFI2(k); }",
"""let PRF = {k: 'bilanciato', set: false, man: false, ans: {}, name: ''};
try { const v = JSON.parse(localStorage.getItem('af2-profilo') || 'null'); if (v && PROF[v.k]) PRF = {k: v.k, set: !!v.set, man: !!v.man, ans: v.ans || {}, name: typeof v.name === 'string' ? v.name.slice(0, 40) : ''}; } catch (e) {}
let QF = null;
function computeIFI2() { if (!F2) computeFeat2(); Q2 = {}; for (const k in PROF) Q2[k] = runIFI2(k); QF = Q2[PRF.k]; }""")
assert 'let QF = null' in eng
eng=eng.replace("function loadExtra(x) {\n  X2 = {};","function loadExtra(x) {\n  X2 = {}; F2 = null;")
assert 'F2 = null;' in eng
rep("function back(i, k) { const j = i - k; return j >= 0 ? j : 0; }\n","function back(i, k) { const j = i - k; return j >= 0 ? j : 0; }\n\n"+eng+"\n")
rep("  computeAAV();\n}\n\nfunction stateAt(i) {","  computeAAV(); computeIFI2();\n}\n\nfunction stateAt(i) {")
rep("  st.sel = N - 1; STD_IFI = computeStd(); syncUi();\n","  loadExtra(await fetchJson('extra_data.json'));\n  st.sel = N - 1; STD_IFI = computeStd(); syncUi(); setTech(true, false);\n")
rep("  if (late) DBP.then(","  if (!PRF.set && !lsGet2('af2-benvenuto')) setTimeout(() => openProf(true), 500);\n  if (late) DBP.then(")
# ---------- quota mostrata = quota 2.0 del profilo
rep("const ms = ruleMonths(i), q = Math.round(AV.q[i] * 100) / 100,","const ms = ruleMonths(i), q = Math.round(QF.q[i] * 100) / 100,")
rep("const x = Math.round(AV.q[o.i] * 100) / 100, c = document.createElement('div')","const x = Math.round(QF.q[o.i] * 100) / 100, c = document.createElement('div')")
rep("+ '% in azioni. ' + AV.why[o.i] + '.';","+ '% in azioni. ' + why2(o.i) + '.';")
rep("l.innerHTML = 'Quota in azioni · allocazione adattiva<button class=\"hb\" type=\"button\" data-help=\"aav\" aria-label=\"Come funziona\">?</button> · mese per mese <b>· su un portafoglio 100% azionario · ultimi 2 anni</b>';",
    "l.innerHTML = 'Quota in azioni consigliata · profilo ' + PROF[PRF.k].lab + ' · mese per mese · ultimi 2 anni';")
rep("why.textContent = 'Perché ' + Math.round(q * 100) + '%: ' + AV.why[i] + '.';\n  box.append(aavChips(i), why);","why.textContent = 'I motivi della quota di oggi sono nel riquadro Consiglio; passa sopra una barra per il motivo di quel mese.'; why.style.fontWeight = 400; why.style.color = css('--muted');\n  box.append(why); const ab = document.getElementById('aavBox'); if (ab) ab.replaceChildren(aavChips(i));")
rep("const j = prevMonthEnd(i), q = Math.round(AV.q[i] * 100), q0 = Math.round(AV.q[j] * 100), d = q - q0;","const j = prevMonthEnd(i), q = Math.round(QF.q[i] * 100), q0 = Math.round(QF.q[j] * 100), d = q - q0;")
rep("const qa = Math.round(AV.q[ie] * 100), qp = Math.round(AV.q[ip] * 100),","const qa = Math.round(QF.q[ie] * 100), qp = Math.round(QF.q[ip] * 100),")
rep("document.createTextNode('allocazione adattiva ' + qa + '% (' + act","document.createTextNode('modello 2.0, profilo ' + PROF[PRF.k].lab + ', ' + qa + '% (' + act")
rep("  renderRule(i);\n  renderAdvice(i);\n}","  renderRule(i);\n  renderAdvice(i);\n  renderSig(i);\n  renderMot(i);\n}")
# renderAdvice: sostituzione completa
a=s.index("function renderAdvice(i) {"); b=s.index("let FROWS")
s=s[:a]+rd('ui.js')+rd('ui2.js')+s[b:]
rep("renderBacktest(); drawCal(); document.getElementById('thLab').textContent = st.th; }","renderBacktest(); renderCmp(); renderMkt(); drawCal(); document.getElementById('thLab').textContent = st.th; }")
# ---------- prova sul passato
rep("r: btRun(AV.q, a, b), c: css('--amber')},\n","r: btRun(AV.q, a, b), c: css('--amber')},\n    {id: 'ifi2', k: 'Quota consigliata 2.0 · profilo ' + PROF[PRF.k].lab, d: 'modello di base + segnali precoci + rientro', r: btRun(QF.q, a, b), c: css('--navy'), main: true},\n")
rep("{id: 'rule', k: 'Regola della dashboard', d: 'indice' + (st.trend ? ' + media 200 giorni' : ''), r: btRun(EXPO, a, b), c: css('--risk'), main: true},","{id: 'rule', k: 'Freno d\\'emergenza da solo', d: 'indice' + (st.trend ? ' + media 200 giorni' : ''), r: btRun(EXPO, a, b), c: css('--risk')},")
rep("{id: 'aav', k: 'Allocazione adattiva (grafico a barre)',","{id: 'aav', k: 'Modello di base (allocazione adattiva)',")
rep("for (const row of rows.filter(r => r.id === 'bh' || r.id === 'rule')) {","for (const row of rows.filter(r => r.id === 'bh' || r.id === 'ifi2')) {")
rep("(row.id === 'rule' ? ' · fuori dalla borsa il ' + pct(row.r.def, 0) + ' del tempo' : '');","(row.id === 'ifi2' ? ' · quota sotto il 100% il ' + pct(row.r.def, 0) + ' del tempo' : '');")
rep("ru = rows.find(r => r.id === 'rule').r;","ru = rows.find(r => r.id === 'ifi2').r;")
rep("'In ' + nf(yrs, 0) + ' anni la regola '","'In ' + nf(yrs, 0) + ' anni la quota consigliata (profilo ' + PROF[PRF.k].lab + ') '")
# ---------- cartelle chiuse alla prima apertura
rep("  const saved = lsGet2(LSF) || {};\n  const cards = ","  const saved0 = lsGet2(LSF), first = !saved0, saved = saved0 || {};\n  const cards = ")
rep("    if (saved[key]) c.classList.add('collapsed'); sync();\n  });","    if (saved[key] || (first && /^(calibrazione|spaccatura|metodo|confronto|backtest)/.test(key))) { c.classList.add('collapsed'); saved[key] = 1; } sync();\n  });\n  if (first) lsSet2(LSF, saved);")
# ---------- spiegazioni
rep("function helpContent(k) {", rd('help.js')+rd('help2.js')+"function helpContent(k) {")
rep("if (EX[k]) out.push(exBox(EX[k]));","if (EX[k]) out.push(exBox(typeof EX[k] === 'function' ? EX[k]() : EX[k]));")
rep("""    const q = AV.q[i]; lv = quotaLv(q);
    title = 'Quota in azioni (allocazione adattiva): ' + Math.round(q * 100) + '%';
    text = 'Perché: ' + AV.why[i] + '.';""","""    const q = QF.q[i]; lv = quotaLv(q);
    title = 'Quota in azioni consigliata (profilo ' + PROF[PRF.k].lab + '): ' + Math.round(q * 100) + '%';
    text = 'Perché: ' + why2(i) + '.';""")
rep("""    title = 'Consiglio: ' + ADV[a.k][0] + ' · azioni ' + a.q + '% (allocazione adattiva)';
    text = 'Quota di fine mese precedente ' + a.q0 + '%, oggi ' + a.q + '%. Motivo: ' + AV.why[i] + '.';
  } else if (k === 'shock') {""","""    title = 'Consiglio: ' + ADV[a.k][0] + ' · azioni ' + a.q + '% (profilo ' + PROF[PRF.k].lab + ')';
    text = 'Quota di fine mese precedente ' + a.q0 + '%, oggi ' + a.q + '%. Motivo: ' + why2(i) + '.';
  } else if (k === 'segnali') {
    const v = F2.ew[i]; lv = QF.st[i] === 'riduzione' ? 's-risk' : lev(v);
    title = 'Segnali precoci: ' + rnd(v) + '/100 · stato: ' + ST2[QF.st[i]][0].toLowerCase();
    text = Object.keys(FAM2).map(f => FAM2[f] + ' ' + rnd(F2.fam[f][i])).join(' · ') + '. ' + cap1(QF.why[i]) + '.';
  } else if (k === 'rientro') {
    const v = F2.rs[i]; lv = isNaN(v) ? null : v >= 65 ? 's-ok' : v >= 50 ? 's-yel' : 's-warn';
    title = 'Segnali di rientro: ' + rnd(v) + '/100 · ' + F2.nimp[i] + ' componenti su 5 in miglioramento';
    text = Object.keys(REC2).map(f => REC2[f] + ' ' + rnd(F2.rec[f][i])).join(' · ') + '.';
  } else if (k === 'shock') {""")
# ---------- istantanea e PDF
rep("quota_azioni_consigliata_pct: Math.round(AV.q[i] * 100), allocazione_adattiva:","quota_azioni_consigliata_pct: Math.round(QF.q[i] * 100), modello_2_0: {profilo: PRF.k, stato: QF.st[i], punteggio_segnali_precoci: r1(F2.ew[i]), motivo: QF.why[i]}, allocazione_adattiva:")
rep("basato_su: 'allocazione adattiva'","basato_su: 'modello 2.0 (in prova)'")
rep("doc.text('Allocazione adattiva', x + w - 4, Y0 + 7, {align: 'right'});","doc.text('Profilo ' + PROF[PRF.k].lab, x + w - 4, Y0 + 7, {align: 'right'});")
rep("doc.text('QUOTA IN AZIONI · ALLOCAZIONE ADATTIVA · MESE PER MESE', M + 4, y2 + 6.5);","doc.text('QUOTA IN AZIONI CONSIGLIATA · PROFILO ' + PROF[PRF.k].lab.toUpperCase() + ' · MESE PER MESE', M + 4, y2 + 6.5);")
rep("ms.forEach((o, k) => { const q = Math.round(AV.q[o.i] * 100), c = LV[qI(q / 100)],","ms.forEach((o, k) => { const q = Math.round(QF.q[o.i] * 100), c = LV[qI(q / 100)],")
rep("doc.text(split('Perché ' + qa + '%: ' + AV.why[i] + '.', CW - 8, 7.6)","doc.text(split('Perché ' + qa + '%: ' + why2(i) + '.', CW - 8, 7.6)")
# ---------- avvisi versione locale
rep("'Dashboard v' + APP_VERSION + ' · Modello '","'Dashboard v' + APP_VERSION + ' · Modello 2.0 su base '")
rep("Se il download non parte, apri la dashboard in Claude.'","Lo trovi nella cartella dei download del browser.'")
rep('</b> (modificabile nel backtest)</span>','</b> (fissa)</span>')
rep("evBtnLabel(); if (evDlg.open) renderEval(); }","evBtnLabel(); if (evDlg.open) renderEval(); renderMkt(); }")
rep("btnEval.addEventListener('click', () => { if (!DATA) return; renderEval();","btnEval.addEventListener('click', () => { const mk = document.getElementById('mercato'); if (mk) { if (mk.classList.contains('collapsed')) { setFold(mk, false); mk._syncFold && mk._syncFold(); } mk.scrollIntoView({behavior: 'smooth', block: 'start'}); return; } if (!DATA) return; renderEval();")
rep("  ['report', 'Report del mese (Stati Uniti)', 2, 16], ['estero', 'Mercati esteri', 1, 6], ['conferma', 'Indicatori esterni', 1, 4],","  ['conferma', 'Indicatori esterni', 1, 4],")
rep("['fattori', 'Fattori e pesi', 1, 5],","['fattori', 'Fattori dell\\'indice', 1, 5],")
rep("PDF_SECS.filter(x => MONTHLY.includes(x[0]))]];","PDF_SECS.filter(x => MONTHLY.includes(x[0]))]].filter(g => g[3].length);")
rep("document.body.classList.add('pdfmode'); wrap.style.width = '1040px';","document.body.classList.add('pdfmode'); document.getElementById('tech').hidden = false; wrap.style.width = '1040px';")
rep("pdfRestore = () => { pdfRestore = null; stage.remove(); document.body.classList.remove('pdfmode');","pdfRestore = () => { pdfRestore = null; stage.remove(); document.body.classList.remove('pdfmode'); document.getElementById('tech').hidden = !document.body.classList.contains('tech-on');")
rep("    if (!list.length) continue;\n    if (x && !sepDone)","    if (!list.length || (x && !(st[gk] > 0))) continue;\n    if (x && !sepDone)")
rep("td.textContent = 'Gruppi sperimentali · di base solo i grandi investitori (0,50), gli altri esclusi (0)';","td.textContent = 'Gruppo aggiuntivo · conta la metà degli altri due';")
rep("if (EX[k]) out.push(exBox(","if (k === 'pesidist') out.push(pesiTable());\n  if (EX[k]) out.push(exBox(")
rep("'. Percentile alto = più rischio rispetto agli ultimi 5 anni. Clicca un fattore per la spiegazione, sposta il cursore per cambiarne il peso.'","'. Livello alto = più rischio rispetto agli ultimi 5 anni. Clicca un fattore per la spiegazione.'")
rep('<th>Percentile rischio <span class="muted">(vs ultimi 5 anni)</span></th><th class="r">Δ percentile <span class="muted">4 sett.</span></th>','<th>Livello di rischio 0–100 <span class="muted">(rispetto agli ultimi 5 anni)</span></th><th class="r">Variazione <span class="muted">4 sett.</span></th>')
# ---------- v2.1: testata compatta, niente "Situazione attuale" nelle finestre
rep("  out.push(sitBox(SBMAP[k] || k));\n","")
rep("""  const sb = document.createElement('div'); sb.className = 'sitbox ' + cl;
  sb.innerHTML = '<div class="lab"><span class="dot4"></span><span></span></div><div class="t"></div><div></div>';
  sb.querySelector('.dot4').style.background = css(QV[c.status]); sb.querySelector('.lab span:last-child').textContent = 'Situazione a fine mese · ' + QN[c.status] + ' · ' + QL[c.status] + (c.prev_status == null ? '' : c.prev_status === c.status ? ' · invariato rispetto al mese prima' : ' · il mese prima era ' + QN[c.prev_status]);
  sb.children[1].textContent = c.value; sb.children[2].textContent = c.text; body.append(sb);""","""  const sb = document.createElement('div'); sb.className = 'sitbox ' + cl;
  sb.innerHTML = '<div class="t"></div><div></div>';
  sb.children[0].textContent = c.value; sb.children[1].textContent = c.text + (c.prev_status == null ? '' : c.prev_status === c.status ? ' Colore invariato rispetto al mese prima.' : ' Il mese prima il colore era ' + QN[c.prev_status] + '.'); body.append(sb);""")
rep("  chip('Calcolato il', genTxt);\n","")
rep("    chip('S&P 500', f); chip('quotazione delle', tq);","    chip('S&P 500', f);")
rep("function renderHero() {\n","function renderHero() {\n  { const gc = document.getElementById('gaugeCard'), sbx = document.getElementById('shockBar'); if (gc && sbx && sbx.parentNode !== gc) gc.append(sbx); }\n")
# ---------- v2.2: pulsanti in testata (Idee da approfondire, Peso S&P 500)
import re as _re
_new='<button class="btn btn-eval" id="btnEval" type="button" hidden><span class="spark"></span><span class="blab"></span></button><button class="btn btn-eval" id="btnNotizie" type="button" title="Le notizie del momento: dashboard, fonti esterne, cosa seguire"><span class="spark" aria-hidden="true">◔</span><span class="blab">Notizie</span></button><button class="btn btn-eval" id="btnIdee" type="button" title="Idee di approfondimento: società e temi da studiare, con le fonti"><span class="spark" aria-hidden="true">✦</span><span class="blab">Idee da approfondire</span></button><button class="btn btn-peso" id="btnPeso" type="button" title="I primi 50 titoli dell\'S&P 500 per peso nell\'indice"><span class="ic" aria-hidden="true">▦</span><span class="blab">Peso S&amp;P 500</span></button>'
s,_n=_re.subn(r'<button class="btn btn-eval" id="btnEval".*?</button>',lambda m:_new,s,count=1,flags=_re.S); assert _n==1
# ---------- v2.4: spiegazione "perché adesso" dentro ogni casella
rep("  tiles.append(lg);\n  renderRule(i);","""  tiles.append(lg);
  { const FN = {ewcap63: 'ritardo dei titoli piccoli dell\\'indice', pct200: 'titoli sotto la media a 200 giorni', nl10: 'nuovi minimi annuali', near_hi: 'titoli lontani dai massimi', rut63: 'ritardo delle small cap', rv21: 'volatilità reale', vix: 'VIX', ts: 'curva del VIX', move: 'volatilità dei Treasury', hy63: 'debolezza del credito high yield'};
    const fct = g => DATA.factors.filter(x => x.group === g).map(x => ({n: FN[x.id] || x.name, p: COL['p_' + x.id][i]})).filter(x => !isNaN(x.p)).sort((a, b2) => b2.p - a.p);
    const lst = a => a.map(x => x.n + ' (' + Math.round(x.p) + ')').join(' e ');
    const RS = {};
    for (const g of ['FRAG', 'STRS']) { const a = fct(g); RS[g] = a.length > 2 ? 'Spingono: ' + lst(a.slice(0, 2)) + ', punteggi 0–100. Più calmo: ' + lst(a.slice(-1)) + '.' : ''; }
    const bw = spx >= ma;
    RS.spx = (dd > -0.0005 ? 'Sul massimo storico' : 'A ' + nf(-dd * 100, 1) + '% sotto il massimo') + (isNaN(ma) ? '' : ', ' + nf(Math.abs(spx / ma - 1) * 100, 1) + '% ' + (bw ? 'sopra' : 'sotto') + ' la media a 200 giorni') + (td ? ': tendenza negativa.' : ': la tendenza resta positiva.');
    RS.coverage = 'Ci sono i prezzi di oggi per il ' + nf(cov, 0) + '% dei titoli dell\\'indice' + (cov >= 97 ? ': dati completi, indice affidabile.' : ': qualche dato manca, indice meno preciso.');
    RS.regola = ex < 1 ? 'Attivo perché ' + (SIG[i] ? 'l\\'indice (' + Math.round(v) + ') supera la soglia di ' + st.th : 'l\\'S&P è sotto la media a 200 giorni') + ': la quota è ridotta.' : 'L\\'indice è a ' + Math.round(v) + ', sotto la soglia di ' + st.th + ', e l\\'S&P è ' + (td ? 'sotto' : 'sopra') + ' la media a 200 giorni: nessun taglio d\\'emergenza.';
    for (const [k, txt] of Object.entries(RS)) { const t = tiles.querySelector('[data-help="' + k + '"]'); if (t && txt) { const d = document.createElement('div'); d.className = 'rs'; d.textContent = txt; const bar = t.querySelector('.bar'); bar ? t.insertBefore(d, bar) : t.append(d); } }
  }
  renderRule(i);""")
# ---------- v2.5: mini grafico accanto all'indice
rep("  document.getElementById('scaleMk').style.left","  if (typeof drawIfiSpark === 'function') drawIfiSpark(i);\n  document.getElementById('scaleMk').style.left")
rep("if (k === 'pesidist') out.push(pesiTable());","if (/^seg\\d+$/.test(k)) out.push(segBox(k));\n  if (k === 'pesidist') out.push(pesiTable());")
rep('Puoi includerli nel riquadro "Pesi del modello" (gruppo sperimentale). Clicca un riquadro per la spiegazione.','Qui sono solo da leggere: nel modello 2.0 i pesi sono fissi. Clicca un riquadro per la spiegazione.')
rep("box.className = 'sm clickable'; box.dataset.help = c.id; box.tabIndex = 0;","box.className = 'sm clickable'; box.tabIndex = 0; box.title = 'Clicca per grafico e indicazioni'; box.addEventListener('click', () => openConfCard(c.id)); box.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openConfCard(c.id); } });")
rep('<button class="ver" type="button" id="btnVer" title="Versione della dashboard: clicca per le novità">v—</button>','')
rep('</template>','</template>\n<p class="foot verfoot">Versione <button class="ver" type="button" id="btnVer" title="Versione della dashboard: clicca per le novità">v—</button> · clicca per le novità</p>')
rep('<title>Analisi Finanziaria 2.0 (locale)</title>','<title>Analisi Finanziaria</title>')
rep('<h1>Analisi Finanziaria 2.0','<h1>Analisi Finanziaria')
assert 'AV.q[' in s
left=[m.start() for m in re.finditer(r'AV\.q\[', s)]
print('AV.q residui:', len(left)); 
for p in left: print('   ', s[max(0,p-60):p+40].replace('\n',' '))
open(DST,'w',encoding='utf8').write(s); print('scritto', DST, len(s))

# ---------- variante online (CDN al posto di librerie locali e senza caricatore locale)
import os, json as _json
_o=s
_a=_o.index('<script>\n/* Versione locale'); _b=_o.index('</script>',_a)+len('</script>\n')
_o=_o[:_a]+_o[_b:]
os.makedirs('/home/claude/af2/online',exist_ok=True)
open('/home/claude/af2/online/index.html','w',encoding='utf8').write(_o); print('online', len(_o))
