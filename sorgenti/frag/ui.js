// ------------------------------------------------------------------ v4.0: consiglio 2.0, segnali precoci, profilo, confronto
const ST2 = {normale: ['Normale', 's-ok', 'green'], allerta: ['Allerta', 's-yel', 'yel'], riduzione: ['Riduzione', 's-risk', 'red'], rientro: ['Rientro graduale', 's-warn', 'amber'], dati: ['Dati insufficienti', 's-warn', 'amber']};
const cap1 = s => s ? s.charAt(0).toUpperCase() + s.slice(1) : s;
const rnd = v => isNaN(v) ? '—' : Math.round(v);
function why2(i) { return cap1(QF.why[i]) + '. Modello di base: ' + AV.why[i]; }
function topFam(i) { let bk = null, bv = -1; for (const k in F2.fam) { const v = F2.fam[k][i]; if (!isNaN(v) && v > bv) { bv = v; bk = k; } } return [bk, bv]; }
// i tre motivi principali della quota di oggi: [etichetta, testo, livello colore, spiegazione da aprire]
function motivi(i) {
  const s = QF.st[i], leg = Math.round(AV.q[i] * 100), q = Math.round(QF.q[i] * 100), P = PROF[PRF.k], out = [];
  out.push(['Segnali precoci', cap1(QF.why[i]) + ' (punteggio ' + rnd(F2.ew[i]) + '/100).', ST2[s][1], 'segnali']);
  out.push(['Modello di base', cap1(REGIT[AV.reg[i]]) + ', punteggio di favore ' + Math.round(AV.comp[i]) + '/100: quota ' + leg + '%.', quotaLv(leg / 100), 'aav']);
  const [fk, fv] = topFam(i);
  if (AV.cap[i] <= AAV.emCap + 1e-9) out.push(['Limite', 'Emergenza: rischio interno o credito molto deboli, massimo 20%.', 's-risk', 'aav']);
  else if (q < leg) out.push(['Limite', 'Tetto del profilo ' + P.lab + ': la quota non supera il ' + QF.cap[i] * 10 + '% finché i segnali non rientrano.', 's-warn', 'profilo']);
  else if (AV.frz[i]) out.push(['Limite', 'Shock di mercato recente: gli aumenti restano sospesi finché lo stress non rientra.', 's-warn', 'shock']);
  else if (AV.cap[i] < 1) out.push(['Limite', 'Fragilità da due settimane: massimo 60%.', 's-warn', 'aav']);
  else if (AV.vm[i] < 0.995) out.push(['Limite', 'Volatilità ' + nf(AV.vol[i] * 100, 0) + '%: quota ridotta in proporzione.', 's-yel', 'aav_vol']);
  else if (fk) out.push(['Da seguire', FAM2[fk] + ': ' + Math.round(fv) + '/100.', lev(fv), 'fam_' + fk]);
  return out;
}
function renderAdvice(i) {
  const box = document.getElementById('advCard'); if (!box) return;
  const a = adviceAt(i), [lab, col] = ADV[a.k], P = PROF[PRF.k], s = QF.st[i];
  const seg = ADV.map((x, k) => [x[1], k]);
  const arc = (f0, f1) => { const R = 70, cx = 90, cy = 86, p = f => [cx - R * Math.cos(Math.PI * f), cy - R * Math.sin(Math.PI * f)]; const [x0, y0] = p(f0), [x1, y1] = p(f1); return `M${x0.toFixed(1)},${y0.toFixed(1)} A${R},${R} 0 0 1 ${x1.toFixed(1)},${y1.toFixed(1)}`; };
  let svg = '<svg viewBox="0 0 180 100" class="advg" aria-hidden="true">';
  seg.forEach(([c, k]) => { svg += `<path d="${arc(k / 5 + 0.012, (k + 1) / 5 - 0.012)}" stroke="var(${c})" stroke-opacity="${k === a.k ? 1 : 0.41}" stroke-width="${k === a.k ? 16 : 12}" fill="none" stroke-linecap="butt"/>`; });
  const f = (a.k + 0.5) / 5, nx = 90 - 52 * Math.cos(Math.PI * f), ny = 86 - 52 * Math.sin(Math.PI * f);
  svg += `<line x1="90" y1="86" x2="${nx.toFixed(1)}" y2="${ny.toFixed(1)}" stroke="var(--ink-2,var(--muted))" stroke-width="3" stroke-linecap="round"/><circle cx="90" cy="86" r="6" fill="var(--ink-2,var(--muted))"/></svg>`;
  const mj = T[a.j], prevLab = 'fine ' + MESI3[mj.getUTCMonth()] + ' ' + mj.getUTCFullYear();
  box.innerHTML = '<div class="adv-top"><span class="eyebrow"><span class="adv-who"></span><button class="hb" type="button" data-help="consiglio" aria-label="Come si legge il consiglio">?</button></span><button class="prof-chip' + (PRF.set ? '' : ' todo') + '" type="button" id="btnProf" title="Apri il pannello della tua propensione al rischio"></button></div>'
    + '<div class="adv-row"><span class="adv-lab"></span><span class="adv-pct"></span><span class="adv-az">azioni</span></div><div class="adv-pf">su un portafoglio 100% azionario</div><div class="adv-g">' + svg + '<div class="adv-ends"><span>Esci</span><span>Mantieni</span><span>Entra</span></div></div><div class="adv-sub"></div>'
    + '<div class="adv-conv"><span class="adv-me">Per il tuo portafoglio<button class="hb" type="button" data-help="myeq" aria-label="Come si calcola la tua quota">?</button></span><div class="adv-real"></div></div>'
    + '<p class="adv-brief"></p><button class="btn adv-how" type="button" data-tech="1">Come ci siamo arrivati</button>';
  const pb = box.querySelector('#btnProf');
  box.querySelector('.adv-who').textContent = 'Consiglio' + (PRF.name ? ' per ' + PRF.name : '');
  if (PRF.set) { pb.append('Profilo: ', el('b', null, P.lab), ' · modifica'); } else pb.textContent = 'Compila il tuo profilo di rischio';
  pb.addEventListener('click', (ev) => { ev.stopPropagation(); openProf(); });
  const lb = box.querySelector('.adv-lab'); lb.textContent = lab; lb.style.color = css(col);
  const qcol = css(LVCOL[quotaLv(a.q / 100)]), pc = box.querySelector('.adv-pct'); pc.textContent = a.q + '%'; pc.style.color = qcol; box.querySelector('.adv-az').style.color = qcol;
  box.querySelector('.adv-sub').textContent = 'Quota precedente (' + prevLab + '): ' + a.q0 + '% → oggi ' + a.q + '%' + (a.d ? ' (' + (a.d > 0 ? '+' : '') + a.d + ' punti)' : '');
  const r = Math.round(MYEQ * a.q / 100 * 10) / 10, real = box.querySelector('.adv-real');
  real.append('Azioni ', el('b', null, String(r).replace('.', ',') + '%'), el('span', null, ' (quota massima ' + MYEQ + '% × ' + a.q + '%)')); real.querySelector('b').style.color = qcol;
  box.querySelector('.adv-brief').textContent = inBreve(i);
  box.style.setProperty('--adv', `var(${col})`);
}
function renderSig(i) {
  const box = document.getElementById('sigCard'); if (!box) return;
  const s = QF.st[i], ew = F2.ew[i]; box.replaceChildren();
  const h = el('div', 'sig-head'), eb = el('span', 'eyebrow', 'Segnali precoci'), hb = el('button', 'hb', '?'); hb.type = 'button'; hb.dataset.help = 'segnali'; hb.setAttribute('aria-label', 'Spiegazione'); eb.append(hb);
  const pill = el('span', 'pill ' + ST2[s][2], ST2[s][0]); h.append(eb, pill);
  const sc = el('div', 'sig-score'), b = el('b', null, rnd(ew)); b.style.color = riskColor(ew);
  sc.append(b, el('small', null, '/ 100'), el('span', null, 'Riduzione se resta da ' + E2.on + ' in su per ' + E2.kOn + ' chiusure su ' + E2.kWin + ', con almeno 2 famiglie in peggioramento.'));
  box.append(h, sc);
  const row = (name, v, colr, help, cls) => { const r = el('button', 'sig-row' + (cls ? ' ' + cls : '')); r.type = 'button'; r.dataset.help = help; r.title = 'Clicca per la spiegazione';
    const bar = el('span', 'sb'), ii = el('i'); ii.style.width = (isNaN(v) ? 0 : v) + '%'; ii.style.background = colr; bar.append(ii); r.append(el('span', null, name), bar, el('em', null, rnd(v))); box.append(r); };
  for (const k in FAM2) row(FAM2[k], F2.fam[k][i], riskColor(F2.fam[k][i]), 'fam_' + k);
  const rs = F2.rs[i]; row('Segnali di rientro (alto = meglio)', rs, isNaN(rs) ? css('--muted') : rs >= 65 ? css('--ok') : rs >= 50 ? css('--yel') : css('--amber'), 'rientro', 're');
  const cov = F2.cov[i]; if (!F2.has || cov < 0.999) box.append(el('div', 'sig-foot', !F2.has ? 'Serie aggiuntive non disponibili: punteggio calcolato solo su ampiezza, titoli medi e credito.' : 'Copertura dei segnali ' + Math.round(cov * 100) + '%: alcune serie non esistevano ancora in questa data.'));
}
// ---- pannello del profilo
const PQ = [
  ['q1', 'Se la parte in azioni perde il 10% in un mese, cosa fai?', ['Riduco subito: non voglio perdere di più', 'Aspetto, ma se continua a scendere riduco', 'Resto investito: per me è un\'oscillazione normale']],
  ['q2', 'Quale perdita sulla parte in azioni accetti prima di cambiare strategia?', ['Fino al 10%', 'Fino al 20%', 'Oltre il 20%']],
  ['q3', 'Tra quanto tempo ti serviranno questi soldi?', ['Entro 3 anni', 'Tra 3 e 10 anni', 'Oltre 10 anni']],
  ['q4', 'Cosa ti pesa di più?', ['Perdere durante un ribasso', 'Tutte e due allo stesso modo', 'Restare fuori durante un rialzo']]];
function profSuggest(ans) { let s = 0, n = 0; for (const [id] of PQ) if (ans[id] != null) { s += +ans[id]; n++; } if (n < PQ.length) return null; return s <= 2 ? 'prudente' : s <= 5 ? 'bilanciato' : 'dinamico'; }
function profBt(q, from) { const a = Math.max(1, d3.bisectLeft(T, new Date(from + 'T00:00:00Z'))), r = btRun(q, a, N - 1); let s = 0; if (q) for (let i = a; i < N; i++) s += q[i]; return {cagr: r.cagr, mdd: r.mdd, avg: q ? s / (N - a) : 1}; }
function profRead() { const f = document.getElementById('profForm'), ans = {}; for (const [id] of PQ) { const c = f.querySelector('input[name="' + id + '"]:checked'); if (c) ans[id] = +c.value; } return {ans, pick: f.querySelector('#profPick').value, max: +f.querySelector('#profMax').value, name: f.querySelector('#profName').value.trim().slice(0, 40)}; }
function profSync() {
  const {ans, pick} = profRead(), sug = profSuggest(ans), k = pick === 'auto' ? (sug || PRF.k) : pick, res = document.getElementById('profRes');
  res.replaceChildren(); res.append(sug ? 'Dalle risposte il profilo suggerito è ' : 'Rispondi alle quattro domande per avere un suggerimento. ', sug ? el('b', null, PROF[sug].lab) : '', sug ? '. ' : '', 'Profilo che verrà usato: ', el('b', null, PROF[k].lab), pick === 'auto' ? '.' : ' (scelto da te).');
  document.querySelectorAll('#profTable tbody tr').forEach(tr => tr.classList.toggle('sel', tr.dataset.k === k));
}
function openProf(welcome) {
  const dlg = document.getElementById('profDlg'), f = document.getElementById('profForm'); f.replaceChildren();
  document.getElementById('profLab').textContent = welcome ? 'Benvenuto' : 'Il tuo profilo';
  document.getElementById('profTitle').textContent = welcome ? 'Prima di iniziare: chi sei e quanta prudenza vuoi' : 'Profilo di investitore' + (PRF.name ? ' di ' + PRF.name : '');
  document.getElementById('profClose').textContent = welcome ? 'Più tardi' : 'Chiudi senza salvare';
  const ln = el('label', 'prof-name', 'Come ti chiami?'), inp = el('input'); inp.type = 'text'; inp.id = 'profName'; inp.maxLength = 40; inp.autocomplete = 'given-name'; inp.placeholder = 'Il tuo nome'; inp.value = PRF.name || ''; ln.append(inp); f.append(ln);
  for (const [id, q, opts] of PQ) { const fs = el('fieldset', 'prof-q'); fs.append(el('legend', null, q)); opts.forEach((o, n) => { const l = el('label'), r = el('input'); r.type = 'radio'; r.name = id; r.value = n; if (PRF.ans && PRF.ans[id] === n) r.checked = true; l.append(r, el('span', null, o)); fs.append(l); }); f.append(fs); }
  const two = el('div', 'prof-two'), l1 = el('label', null, 'Profilo da usare'), s1 = el('select'); s1.id = 'profPick';
  [['auto', 'Quello suggerito dalle risposte'], ['prudente', 'Prudente'], ['bilanciato', 'Bilanciato'], ['dinamico', 'Dinamico']].forEach(([v, t]) => { const o = el('option', null, t); o.value = v; s1.append(o); }); s1.value = PRF.set && PRF.man ? PRF.k : 'auto'; l1.append(s1);
  const l2 = el('label', null, 'Quota massima in azioni del tuo portafoglio'), s2 = el('select'); s2.id = 'profMax'; for (let v = 0; v <= 100; v += 5) { const o = el('option', null, v + '%'); o.value = v; s2.append(o); } s2.value = String(MYEQ); l2.append(s2);
  two.append(l1, l2); f.append(two);
  const tb = document.querySelector('#profTable tbody'); tb.replaceChildren();
  for (const k in PROF) { const P = PROF[k], a = profBt(Q2[k].q, '2000-01-03'), b = profBt(Q2[k].q, '2010-01-04'), tr = el('tr'); tr.dataset.k = k;
    const tq = el('td', 'r mono'), dq = el('span', 'qdot'), qn = Math.round(Q2[k].q[N - 1] * 100); dq.style.background = css(LVCOL[quotaLv(qn / 100)]); tq.append(dq, qn + '%');
    tr.append(el('td', null, P.lab), tq, el('td', 'r mono', P.cap * 10 + '%'), el('td', 'r mono', '+10 punti ogni ' + P.slow + ' sedute'), el('td', null, P.recheck ? 'nessun aumento finché l\'indice di rischio resta da 55 in su (fino a ' + E2.rchk + ' sedute)' : 'regola del modello di base (10–21 sedute)'), el('td', 'r mono', pct(a.cagr) + ' / ' + pct(a.mdd, 0)), el('td', 'r mono', pct(b.cagr) + ' / ' + pct(b.mdd, 0))); tb.append(tr); }
  f.onchange = profSync; profSync();
  if (typeof dlg.showModal === 'function' && !dlg.open) dlg.showModal(); else dlg.setAttribute('open', '');
}
const profSeen = () => { try { localStorage.setItem('af2-benvenuto', '1'); } catch (e) {} };
document.getElementById('profDlg').addEventListener('close', profSeen);
document.getElementById('profClose').addEventListener('click', () => document.getElementById('profDlg').close());
document.getElementById('profDlg').addEventListener('click', (e) => { if (e.target.id === 'profDlg') e.target.close(); });
document.getElementById('profSave').addEventListener('click', () => {
  const {ans, pick, max, name} = profRead(), sug = profSuggest(ans);
  if (pick === 'auto' && !sug) { const res = document.getElementById('profRes'); res.textContent = 'Per usare il profilo suggerito rispondi a tutte e quattro le domande, oppure scegli tu il profilo dal menu.'; return; }
  PRF = {k: pick === 'auto' ? sug : pick, set: true, man: pick !== 'auto', ans, name}; MYEQ = max;
  try { localStorage.setItem('af2-profilo', JSON.stringify(PRF)); localStorage.setItem('af2-max-eq', String(MYEQ)); } catch (e) {}
  QF = Q2[PRF.k]; document.getElementById('profDlg').close(); renderAll(); renderReport();
});
// ---- prove del modello: profili, modello di base, sempre investito
function renderCmp() {
  const tb = document.querySelector('#cmpBt tbody'); if (!tb || !QF) return; tb.replaceChildren();
  const rows = [['Sempre investito', null, null], ['Modello di base (allocazione adattiva)', AV.q, null]]; for (const k in PROF) rows.push(['Modello 2.0 · ' + PROF[k].lab, Q2[k].q, k]);
  const R = {}, qc = (v) => { const td = el('td', 'r mono'), d = el('span', 'qdot'); d.style.background = css(LVCOL[quotaLv(v / 100)]); td.append(d, v + '%'); return td; };
  for (const [name, q, k] of rows) { const a = profBt(q, '2000-01-03'), b = profBt(q, '2010-01-04'), tr = el('tr'); if (k === PRF.k) tr.classList.add('sel'); R[k || name] = {a, b};
    tr.append(el('td', null, name + (k === PRF.k ? ' (il tuo)' : '')), el('td', 'r mono', pct(a.cagr)), el('td', 'r mono', pct(a.mdd, 0)), el('td', 'r mono', pct(b.cagr)), el('td', 'r mono', pct(b.mdd, 0)), el('td', 'r mono', pct(a.avg, 0)), qc(q ? Math.round(q[N - 1] * 100) : 100)); tb.append(tr); }
  document.getElementById('cmpBtNote').textContent = 'Fino al ' + fmtDl(T[N - 1]) + '. Soli prezzi dell\'S&P 500 (senza dividendi), liquidità remunerata, senza costi e tasse. Prove fatte sugli stessi dati usati per progettare le regole: non sono una verifica indipendente. Per cambiare profilo e vedere i risultati ricalcolati clicca su "Profilo" nel riquadro Consiglio.';
  const m = R[PRF.k], b0 = R['Modello di base (allocazione adattiva)'], bh = R['Sempre investito'];
  document.getElementById('cmpVerdict').textContent = 'Con il profilo ' + PROF[PRF.k].lab + ', dal 2000 il modello 2.0 ha reso ' + pct(m.a.cagr) + ' l\'anno con una perdita massima di ' + pct(m.a.mdd, 0) + ', contro ' + pct(b0.a.cagr) + ' e ' + pct(b0.a.mdd, 0) + ' del modello di base e ' + pct(bh.a.cagr) + ' e ' + pct(bh.a.mdd, 0) + ' del sempre investito. Dal 2010: ' + pct(m.b.cagr) + ' e ' + pct(m.b.mdd, 0) + ' contro ' + pct(b0.b.cagr) + ' e ' + pct(b0.b.mdd, 0) + '. In sintesi: i segnali precoci hanno ridotto un po\' la perdita massima nei 26 anni, ma dal 2010 non hanno migliorato il risultato del modello di base; le differenze sono piccole e dipendono da pochi episodi. Il modello 2.0 quindi non ha ancora dimostrato di essere migliore: resta in prova, da osservare nei prossimi mesi prima di sostituire quello online.';
}
// per le verifiche automatiche e per il registro dei segnali
window.AF2 = () => ({N, T, COL, IFI, AV, F2, Q2, QF, PRF, MYEQ, PROF, E2, APP_VERSION, openHelp, dates: DATA.dates});
