// ---- v4.0: frase semplice del Consiglio, motivi (parte tecnica), valutazione di mercato nel corpo della pagina
function inBreve(i) {
  const s = QF.st[i], R = AV.reg[i];
  const base = {BULL_CONFIRMED: 'La tendenza del mercato è positiva', FRAGILE: 'La tendenza è positiva ma poggia su pochi titoli', BEAR_STRESS: 'Il mercato è in una fase negativa', EARLY_RECOVERY: 'Il mercato prova a ripartire dopo un ribasso'}[R];
  const sig = {normale: 'e non ci sono segnali di allarme', allerta: 'ma compaiono i primi segnali di debolezza, non ancora confermati', riduzione: 'ma i segnali di debolezza sono confermati: meglio tenere meno azioni', rientro: 'e l\'allerta dei giorni scorsi è rientrata: si risale per gradi', dati: 'ma mancano alcuni dati: per prudenza la quota non aumenta'}[s];
  let lim = '';
  if (AV.cap[i] <= AAV.emCap + 1e-9) lim = ' È attiva l\'emergenza: quota al minimo.';
  else if (AV.frz[i]) lim = ' Dopo lo scossone recente la quota non aumenta finché non torna la calma.';
  else if (AV.vm[i] < 0.9) lim = ' Le oscillazioni sono forti, quindi la quota è più bassa del normale.';
  else if (AV.cap[i] < 1) lim = ' Il mercato è fragile da due settimane: quota limitata.';
  return base + ', ' + sig + '.' + lim;
}
function renderMot(i) {
  const box = document.getElementById('motCard'); if (!box) return; const s = QF.st[i]; box.replaceChildren();
  const h = el('div', 'sig-head'), eb = el('span', 'eyebrow', 'Perché questa quota'), hb = el('button', 'hb', '?'); hb.type = 'button'; hb.dataset.help = 'stato2'; hb.setAttribute('aria-label', 'Cosa significa lo stato'); eb.append(hb);
  h.append(eb, el('span', 'pill ' + ST2[s][2], ST2[s][0]));
  const ul = el('ul', 'adv-mot');
  for (const [k, t, lv, hk] of motivi(i)) { const li = el('li'); li.dataset.help = hk; li.title = 'Clicca per la spiegazione'; const dot = el('i'); dot.style.background = css(LVCOL[lv] || '--muted'); const sp = el('span'); sp.append(el('b', null, k + ': '), t); li.append(dot, sp); ul.append(li); }
  box.append(h, ul);
}
function setTech(on, scroll) {
  const t = document.getElementById('tech'); if (!t) return; t.hidden = !on; document.body.classList.toggle('tech-on', on);
  document.querySelectorAll('.tech-btn').forEach(b => b.setAttribute('aria-pressed', on ? 'true' : 'false'));
  if (on) requestAnimationFrame(() => { drawMain(); drawEq(); drawCal(); if (scroll !== false) document.getElementById('come').scrollIntoView({behavior: 'smooth', block: 'start'}); });
  else if (scroll !== false) document.getElementById('stato').scrollIntoView({behavior: 'smooth', block: 'start'});
}
document.addEventListener('click', (ev) => { const b = ev.target.closest('[data-tech]'); if (!b) return; ev.preventDefault(); ev.stopPropagation(); const v = b.dataset.tech; setTech(v === 't' ? document.getElementById('tech').hidden : v === '1'); }, true);
// ---- grafici piccoli della valutazione (sempre dai dati della pagina)
let MK = null;
function mkSeries() {
  if (MK) return MK; const A = () => new Float64Array(N).fill(NaN);
  const sma = (x, k) => { const o = A(); let s = 0, n = 0; for (let i = 0; i < N; i++) { if (!isNaN(x[i])) { s += x[i]; n++; } if (i >= k && !isNaN(x[i - k])) { s -= x[i - k]; n--; } if (n === k) o[i] = s / k; } return o; };
  MK = {spx: {y: COL.spx, ma: COL.ma200, yrs: 2, cap: 'S&P 500 e media a 200 giorni (tratteggiata) · ultimi 2 anni'},
    ampiezza: {y: COL.pct200, yrs: 2, ref: 50, suf: '%', cap: 'Titoli dell\'S&P 500 sopra la propria media a 200 giorni · ultimi 2 anni'},
    vix: {y: COL.vix, yrs: 2, ref: 20, cap: 'VIX, l\'indice della paura · ultimi 2 anni'}};
  if (X2 && X2.QQQ) {
    MK.ndx = {y: X2.QQQ, ma: sma(X2.QQQ, 200), yrs: 4, cap: 'Nasdaq 100 (fondo QQQ) e media a 200 giorni (tratteggiata) · ultimi 4 anni'};
    const cr = A(); for (let i = 0; i < N; i++) cr[i] = X2.HYG[i] / X2.IEF[i];
    MK.credito = {y: cr, yrs: 2, base: 100, cap: 'Obbligazioni rischiose contro titoli di Stato (inizio = 100; se scende, il credito peggiora) · ultimi 2 anni'};
    const st0 = A(); let v = 100; const dd = ['XLU', 'XLP', 'XLV'], cc = ['XLY', 'XLI', 'XLF', 'XLK'];
    for (let i = 1; i < N; i++) { let a = 0, b = 0, ok = true; for (const k of dd) { const r = X2[k][i] / X2[k][i - 1] - 1; if (isNaN(r)) ok = false; a += r / 3; } for (const k of cc) { const r = X2[k][i] / X2[k][i - 1] - 1; if (isNaN(r)) ok = false; b += r / 4; } if (ok) { v *= (1 + a) / (1 + b); st0[i] = v; } }
    MK.settori = {y: st0, yrs: 2, base: 100, cap: 'Settori difensivi contro ciclici (inizio = 100; se sale, vincono i difensivi) · ultimi 2 anni'};
  }
  return MK;
}
function miniChart(box, key) {
  const W = Math.max(260, box.clientWidth || 320), H = 118, m = {l: 6, r: 46, t: 6, b: 16};
  let xs = [], ys = [], ms = [], step = false, ref = null, suf = '';
  if (key === 'quota') { const t0 = T[N - 1].getTime() - 365.25 * 864e5; for (let i = 0; i < N; i++) if (T[i].getTime() >= t0) { xs.push(T[i]); ys.push(QF.q[i] * 100); } step = true; suf = '%'; }
  else { const S = mkSeries()[key]; if (!S) return false; const t0 = T[N - 1].getTime() - S.yrs * 365.25 * 864e5; let b0 = null;
    for (let i = 0; i < N; i++) if (T[i].getTime() >= t0 && !isNaN(S.y[i])) { if (S.base && b0 == null) b0 = S.y[i] / S.base; xs.push(T[i]); ys.push(S.base ? S.y[i] / b0 : S.y[i]); ms.push(S.ma ? S.ma[i] : NaN); }
    ref = S.ref != null ? S.ref : (S.base || null); suf = S.suf || ''; }
  if (xs.length < 20) return false;
  const x = d3.scaleUtc().domain([xs[0], xs[xs.length - 1]]).range([m.l, W - m.r]);
  const all = ys.concat(ms.filter(v => !isNaN(v))), lo = step ? 0 : d3.min(all), hi = step ? 100 : d3.max(all), pad = (hi - lo) * 0.06 || 1;
  const y = d3.scaleLinear().domain([step ? 0 : lo - pad, step ? 100 : hi + pad]).range([H - m.b, m.t]);
  const svg = d3.create('svg').attr('viewBox', `0 0 ${W} ${H}`).attr('role', 'img');
  const fmtM = itLocale.utcFormat('%b %y');
  x.ticks(4).forEach(t => { svg.append('text').attr('x', x(t)).attr('y', H - 3).attr('text-anchor', 'middle').attr('font-size', 9).attr('fill', css('--muted')).text(fmtM(t)); svg.append('line').attr('x1', x(t)).attr('x2', x(t)).attr('y1', m.t).attr('y2', H - m.b).attr('stroke', css('--line')).attr('stroke-width', 0.5); });
  if (ref != null && ref > y.domain()[0] && ref < y.domain()[1]) svg.append('line').attr('x1', m.l).attr('x2', W - m.r).attr('y1', y(ref)).attr('y2', y(ref)).attr('stroke', css('--muted')).attr('stroke-dasharray', '2 3').attr('stroke-width', 0.8);
  const line = d3.line().x((d, i) => x(xs[i])).y(d => y(d)).defined(d => !isNaN(d)); if (step) line.curve(d3.curveStepAfter);
  if (ms.some(v => !isNaN(v))) svg.append('path').attr('d', line(ms)).attr('fill', 'none').attr('stroke', css('--muted')).attr('stroke-width', 1).attr('stroke-dasharray', '4 3');
  if (step) svg.append('path').attr('d', d3.area().x((d, i) => x(xs[i])).y0(y(0)).y1(d => y(d)).curve(d3.curveStepAfter)(ys)).attr('fill', css('--navy')).attr('fill-opacity', 0.12);
  svg.append('path').attr('d', line(ys)).attr('fill', 'none').attr('stroke', css('--navy')).attr('stroke-width', 1.6);
  const lv = ys[ys.length - 1]; svg.append('circle').attr('cx', x(xs[xs.length - 1])).attr('cy', y(lv)).attr('r', 3).attr('fill', css('--navy'));
  svg.append('text').attr('x', W - m.r + 6).attr('y', y(lv) + 3.5).attr('font-size', 11).attr('font-weight', 700).attr('fill', css('--navy')).text((Math.abs(lv) >= 1000 ? Math.round(lv).toLocaleString('it-IT') : nf(lv, Math.abs(lv) < 100 && !step ? 1 : 0)) + suf);
  box.replaceChildren(svg.node()); return true;
}
const SEGCL = {'più rischio': 'c-risk', 'meno rischio': 'c-ok', 'neutro': 'c-yel'};
const SEGNO = {'più rischio': '--risk', 'meno rischio': '--ok', 'neutro': '--yel'};
function daysAgoRome(iso) { const f = d => new Date(d).toLocaleDateString('sv-SE', {timeZone: 'Europe/Rome'}); return Math.round((Date.parse(f(Date.now()) + 'T00:00:00Z') - Date.parse(f(iso) + 'T00:00:00Z')) / 864e5); }
function openIdee(mode) { mode = mode === 'notizie' ? 'notizie' : 'idee'; renderEval(); evDlg.dataset.mode = mode; const dt = evDlg.querySelector('.evdet'); if (dt) dt.open = (mode === 'notizie'); if (evDlg.showModal && !evDlg.open) evDlg.showModal(); else evDlg.setAttribute('open', ''); }
function renderMkt() {
  const up = document.getElementById('mktUpd'), body = document.getElementById('mktBody'); if (!up || !body || !QF) return;
  up.replaceChildren(); body.replaceChildren(); up.classList.remove('c-ok', 'c-yel', 'c-warn', 'c-risk');
  if (!EVAL || EVAL.state !== 'ok') { up.classList.add('c-warn'); up.append(el('b', null, 'Nessuna valutazione di mercato salvata.'), el('span', 'sub', 'Per farne una scrivi a Claude: «valutazione attuale».')); return; }
  const d = daysAgoRome(EVAL.at), when = new Date(EVAL.at), i = N - 1;
  const txt = when.toLocaleDateString('it-IT', {timeZone: 'Europe/Rome', weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'}) + ' alle ' + when.toLocaleTimeString('it-IT', {timeZone: 'Europe/Rome', hour: '2-digit', minute: '2-digit'});
  const cls = d <= 1 ? ['c-ok', 'green'] : d <= 3 ? ['c-yel', 'yel'] : d <= 7 ? ['c-warn', 'amber'] : ['c-risk', 'red'];
  up.classList.add(cls[0]); up.append('Aggiornata ', el('b', null, txt), el('span', 'pill ' + cls[1], d === 0 ? 'oggi' : d === 1 ? 'ieri' : d + ' giorni fa'));
  const same = EVAL.data_as_of === DATA.as_of;
  up.append(el('span', 'sub', (d > 3 ? 'Non è recente: per aggiornarla chiedi a Claude una nuova valutazione. ' : '') + 'Fatta sui dati di mercato del ' + fmtDl(new Date(EVAL.data_as_of + 'T00:00:00Z')).trim() + (same ? ', gli stessi di questa pagina.' : '; i numeri della pagina sono del ' + fmtDl(T[i]).trim() + '.')));
  const R = EVAL.report || {};
  body.append(el('p', 'mkt-title', EVAL.titolo || ''));
  const two = el('div', 'mkt-two'), boxUl = (title, arr, help) => { if (!arr || !arr.length) return; const b = el('div', 'mkt-box'); b.dataset.help = help; b.append(el('h3', null, title)); const ul = el('ul'); arr.forEach(t => ul.append(el('li', null, t))); b.append(ul); two.append(b); };
  boxUl('Dalla valutazione precedente', R.precedente, 'mk_prec'); boxUl('Cosa è cambiato', R.cambiato, 'mk_cambiato'); if (two.children.length) body.append(two);
  const sec = el('div', 'mkt-sec'); sec.append(el('h3', null, 'La situazione')); (R.situazione && R.situazione.length ? R.situazione : (EVAL.in_breve || [])).forEach(t => sec.append(el('p', null, t))); body.append(sec);
  const a = adviceAt(i), ind = el('div', 'mkt-ind'); ind.dataset.help = 'consiglio'; ind.style.borderLeftColor = css(LVCOL[quotaLv(a.q / 100)]);
  const ib = el('b', null, ADV[a.k][0] + ' · ' + a.q + '% in azioni'); ib.style.color = css(LVCOL[quotaLv(a.q / 100)]);
  ind.append(el('span', null, 'Indicazione del modello' + (PRF.name ? ' per ' + PRF.name : '') + ':'), ib, el('span', 'muted', 'profilo ' + PROF[PRF.k].lab + ' · per il tuo portafoglio ' + String(Math.round(MYEQ * a.q / 10) / 10).replace('.', ',') + '% · calcolata sui dati del ' + fmtDl(T[i]).trim())); body.append(ind);
  const temi = R.temi && R.temi.length ? R.temi : (EVAL.esterno || []).map(e => ({titolo: e.tema, testo: e.lettura, segno: e.segno, fonte: e.fonte, url: e.url, data: e.data}));
  if (temi.length) { const g = el('div', 'mkt-temi');
    for (const t of temi) { const c = el('div', 'mkt-tema ' + (SEGCL[String(t.segno || '').toLowerCase()] || '')); c.dataset.help = t.grafico && HELP['mk_' + t.grafico] ? 'mk_' + t.grafico : 'mk_tema'; c.title = 'Clicca per la spiegazione';
      const h = el('h4'), dot = el('i'); dot.style.background = css(SEGNO[String(t.segno || '').toLowerCase()] || '--muted'); h.append(dot, t.titolo || ''); c.append(h, el('p', null, t.testo || ''));
      if (t.grafico) { const cb = el('div', 'mkt-chart'); c.append(cb); g.append(c); if (miniChart(cb, t.grafico)) { const S = mkSeries()[t.grafico]; c.append(el('div', 'cap', t.grafico === 'quota' ? 'Quota in azioni consigliata · ultimo anno' : S.cap)); } else cb.remove(); } else g.append(c);
      if (t.fonte) { const s = el('div', 'src'); s.append('Fonte: '); const u = safeUrl(t.url); if (u) { const an = el('a', null, t.fonte); an.href = u; an.target = '_blank'; an.rel = 'noopener noreferrer'; s.append(an); } else s.append(t.fonte); if (t.data) s.append(' · ' + t.data.split('-').reverse().join('/')); c.append(s); } }
    const ws = el('div', 'mkt-sec'); ws.append(el('h3', null, 'I temi del momento'), g); body.append(ws); }
  if (EVAL.monitorare && EVAL.monitorare.length) { const ws = el('div', 'mkt-sec'), ul = el('ul', 'mkt-seg'); ws.append(el('h3', null, 'Da seguire')); EVAL.monitorare.forEach((mm, idx) => { const li = el('li'); li.dataset.help = 'seg' + idx; HELP['seg' + idx] = [(mm.cosa || '') + ': le notizie', 'Quello che sta succedendo adesso su questo punto, con le fonti. Sotto trovi perché conta e la soglia che cambierebbe il quadro.']; li.title = 'Clicca per le notizie approfondite'; li.append(el('b', null, mm.cosa || ''), el('span', 'sg', mm.soglia || ''), el('em', 'more', 'Notizie approfondite ›')); ul.append(li); }); ws.append(ul); body.append(ws); }
  renderEsteri();
  { const e = document.getElementById('esteri'), c = document.getElementById('conferma'); if (e && c && e.nextElementSibling !== c) e.after(c); }
}
window.addEventListener('resize', debounce(() => renderMkt(), 250));
// ---- distribuzione dei pesi (solo lettura)
function pesiTable() {
  const tb = el('table', 'pd-tab'), hd = el('tr'); hd.append(el('th', null, 'Gruppo e fattore'), el('th', 'r', 'Peso'), el('th', 'r', 'Quanto conta nell\'indice')); tb.append(hd);
  const gs = [['Fragilità interna', DATA.factors.filter(f => f.group === 'FRAG').map(f => [f.name, st.w[f.id]]), st.gF], ['Stress di mercato', DATA.factors.filter(f => f.group === 'STRS').map(f => [f.name, st.w[f.id]]), st.gS]];
  for (const [g, name, ids, gk] of XGROUPS) if (st[gk] > 0) gs.push([name, ids.filter(id => st.wc[id] != null).map(id => [(DATA.confirm.find(c => c.id === id) || {name: id}).name, st.wc[id]]), st[gk]]);
  const tot = gs.reduce((s, g) => s + g[2], 0);
  for (const [name, fs, gw] of gs) { const tr = el('tr', 'g'); tr.append(el('td', null, name), el('td', 'r', nf(gw, 2)), el('td', 'r', nf(gw / tot * 100, 0) + '%')); tb.append(tr);
    const sw = fs.reduce((s, f) => s + f[1], 0); for (const [fn, w] of fs) { const r = el('tr'); r.append(el('td', null, fn), el('td', 'r', nf(w, 2)), el('td', 'r', nf(gw / tot * w / sw * 100, 1) + '%')); tb.append(r); } }
  return tb;
}

// ---- mercati esteri, materie prime, cambio, tassi (dati di fine mese del modello mensile)
function estChart(box, c) {
  const ch = c.chart; if (!ch || !ch.dates || !ch.series || !ch.series.length) return false;
  const W = Math.max(240, box.clientWidth || 300), H = 112, multi = ch.series.some(s => s.role === 'second'), m = {l: 6, r: multi ? 74 : 46, t: 6, b: 16};
  const n = ch.dates.length, tEnd = Date.parse(ch.dates[n - 1] + 'T00:00:00Z') - 2 * 365.25 * 864e5; let i0 = ch.dates.findIndex(d => Date.parse(d + 'T00:00:00Z') >= tEnd); if (i0 < 0) i0 = 0; const D = ch.dates.slice(i0).map(d => new Date(d + 'T00:00:00Z'));
  const S = ch.series.map(s => ({name: s.name, role: s.role, v: s.values.slice(i0)}));
  const all = []; S.forEach(s => s.v.forEach(v => { if (v != null && !isNaN(v)) all.push(v); }));
  if (all.length < 10) return false;
  const lo = d3.min(all), hi = d3.max(all), pad = (hi - lo) * 0.08 || 1;
  const x = d3.scaleUtc().domain([D[0], D[D.length - 1]]).range([m.l, W - m.r]), y = d3.scaleLinear().domain([lo - pad, hi + pad]).range([H - m.b, m.t]);
  const svg = d3.create('svg').attr('viewBox', `0 0 ${W} ${H}`).attr('role', 'img'), fmtM = itLocale.utcFormat('%b %y');
  x.ticks(4).forEach(tk => { svg.append('text').attr('x', x(tk)).attr('y', H - 3).attr('text-anchor', 'middle').attr('font-size', 9).attr('fill', css('--muted')).text(fmtM(tk)); });
  (ch.ref || []).forEach(r => { if (r.y > y.domain()[0] && r.y < y.domain()[1]) svg.append('line').attr('x1', m.l).attr('x2', W - m.r).attr('y1', y(r.y)).attr('y2', y(r.y)).attr('stroke', css('--muted')).attr('stroke-dasharray', '2 3').attr('stroke-width', 0.8); });
  const COLS = {main: css('--navy'), ma: css('--muted'), second: css('--amber'), third: css('--sky') || css('--muted')};
  const line = d3.line().x((d, i) => x(D[i])).y(d => y(d)).defined(d => d != null && !isNaN(d));
  S.slice().sort((p, q) => (p.role === 'ma') - (q.role === 'ma')).forEach(s => {
    const col = COLS[s.role] || css('--navy'), p = svg.append('path').attr('d', line(s.v)).attr('fill', 'none').attr('stroke', col).attr('stroke-width', s.role === 'ma' ? 1 : 1.6);
    if (s.role === 'ma') p.attr('stroke-dasharray', '4 3');
    const lv = s.v[s.v.length - 1]; if (lv != null && s.role !== 'ma') { let ly = y(lv); if (multi) { const o = S.filter(q => q.role !== 'ma').map(q => y(q.v[q.v.length - 1])).sort((p1, q1) => p1 - q1); const rk = o.indexOf(ly); ly = o[0] + rk * 12 + (o.length > 1 ? 0 : 0); if (rk > 0) ly = Math.max(ly, o[rk - 1] + 12); }
      svg.append('circle').attr('cx', x(D[D.length - 1])).attr('cy', y(lv)).attr('r', 2.8).attr('fill', col); svg.append('text').attr('x', W - m.r + 5).attr('y', ly + 3.5).attr('font-size', 10).attr('font-weight', 700).attr('fill', col).text((multi ? s.name.split(' ')[0] + ' ' : '') + nf(lv, Math.abs(lv) < 100 ? (Math.abs(lv) < 10 ? 2 : 1) : 0)); }
  });
  (ch.marks || []).forEach(mk => { const d = new Date(mk.d + 'T00:00:00Z'); if (d < D[0]) return; const j = d3.bisector(q => q).left(D, d), v = S[0].v[Math.min(j, D.length - 1)]; if (v == null) return;
    const up = mk.t === 'buy', yy = y(v) + (up ? 7 : -7), xx = x(D[Math.min(j, D.length - 1)]);
    svg.append('path').attr('d', up ? `M${xx - 4},${yy + 3} L${xx + 4},${yy + 3} L${xx},${yy - 4} Z` : `M${xx - 4},${yy - 3} L${xx + 4},${yy - 3} L${xx},${yy + 4} Z`).attr('fill', css(up ? '--ok' : '--risk')); });
  box.replaceChildren(svg.node()); return true;
}
function renderEsteri() {
  const box = document.getElementById('estBody'); if (!box) return; box.textContent = '';
  const R = DATA.monthly; if (!R || !R.cards) { box.append(el('p', 'muted', 'Dati non disponibili.')); return; }
  const CL = ['c-ok', 'c-yel', 'c-warn', 'c-risk'], first = s => String(s || '').split(/(?<=[.!?])\s/)[0];
  const mk = (pick) => { const g = el('div', 'est-grid'); R.cards.forEach((c, k) => { if (!pick(c)) return;
    const b = el('div', 'est-card clickable ' + CL[c.status]); b.tabIndex = 0; b.title = 'Clicca per la spiegazione completa';
    const hd = el('div', 'eh'); hd.append(el('span', 'dot4'), el('b', null, c.title)); hd.firstChild.style.background = css(QV[c.status]);
    const v = el('div', 'ev', c.value); v.style.color = css(QV[c.status]);
    b.append(hd, v, el('div', 'et', c.text));
    const cb = el('div', 'est-chart'); b.append(cb);
    if (c.chart) b.append(el('div', 'cap', 'Ultimi due anni' + (c.chart.marks && c.chart.marks.length ? ' · triangoli verdi = segnale Buy, rossi = Sell; linea tratteggiata = media a 10 mesi' : (c.chart.series.some(s => s.role === 'ma') ? ' · linea tratteggiata = media' : '')) + ' · dati di fine mese'));
    if (c.impl) { const i = el('div', 'ei'); i.append(el('b', null, 'Cosa significa: '), c.impl); b.append(i); }
    const op = () => openRepCard(k); b.addEventListener('click', op); b.addEventListener('keydown', e => { if (e.key === 'Enter') op(); });
    g.append(b); requestAnimationFrame(() => estChart(cb, c)); }); return g; };
  const OTH = ['materie', 'cambio', 'tassi', 'cripto'];
  const E = R.cards.filter(c => c.area === 'estero'), O = R.cards.filter(c => OTH.includes(c.id));
  const up = document.getElementById('estUpd'); if (up) up.textContent = 'Dati di fine ' + (R.month_label || R.month || 'mese') + ' · le tendenze si basano sul prezzo mensile rispetto alla media di 10 mesi · clicca un riquadro per la spiegazione';
  const g1 = mk(c => c.area === 'estero'), g2 = mk(c => OTH.includes(c.id));
  if (g1.children.length) {
    box.append(el('h3', 'est-h', 'Mercati azionari esteri'));
    const buy = E.filter(c => /^Buy/.test(c.value) && c.id !== 'm_rot').map(c => c.title), sell = E.filter(c => /^Sell/.test(c.value)).map(c => c.title), rot = E.find(c => c.id === 'm_rot');
    const e = el('div', 'rep-est'); e.append(el('b', null, 'In sintesi: '), (R.estero || '') + ' ');
    if (buy.length || sell.length) e.append((buy.length ? 'Segnale Buy (tendenza positiva): ' + buy.join(', ') + '. ' : '') + (sell.length ? 'Segnale Sell (tendenza negativa): ' + sell.join(', ') + '. ' : ''));
    if (rot) e.append(first(rot.text) + ' ');
    box.append(e, g1);
  }
  if (g2.children.length) {
    box.append(el('h3', 'est-h', 'Materie prime, cambio, tassi e cripto'));
    const e = el('div', 'rep-est'); e.append(el('b', null, 'In sintesi: ')); e.append(O.map(c => first(c.impl || c.text)).join(' '));
    box.append(e, g2);
  }
}
document.body.classList.add('tech-on');

document.getElementById('btnIdee')?.addEventListener('click', () => { if (DATA) openIdee('idee'); });
document.getElementById('btnNotizie')?.addEventListener('click', () => { if (DATA) openIdee('notizie'); });
document.getElementById('btnPeso')?.addEventListener('click', () => { const b = document.getElementById('btnTop50'); if (b) b.click(); });

function drawIfiSpark(i) {
  const big = document.getElementById('ifiBig'); if (!big) return;
  let row = document.getElementById('ifiRow');
  if (!row) { row = document.createElement('div'); row.id = 'ifiRow'; row.className = 'ifi-row'; big.parentNode.insertBefore(row, big); row.append(big); const sp = document.createElement('div'); sp.id = 'ifiSpark'; sp.className = 'ifi-spark'; sp.title = 'Clicca per il grafico dettagliato. Andamento dell\'indice di rischio nelle ultime 12 settimane'; row.append(sp); }
  const sp = document.getElementById('ifiSpark'), n = 60, a = Math.max(0, i - n + 1), V = [];
  for (let k = a; k <= i; k++) V.push(IFI[k]);
  const ok = V.filter(x => !isNaN(x)); if (ok.length < 5) { sp.textContent = ''; return; }
  const W = 170, H = 62, m = {l: 2, r: 6, t: 6, b: 14}, lo = Math.min(0, d3.min(ok) - 5) , hi = Math.max(100, d3.max(ok) + 5);
  const lo2 = Math.max(0, d3.min(ok) - 8), hi2 = Math.min(100, d3.max(ok) + 8);
  const x = d3.scaleLinear().domain([0, V.length - 1]).range([m.l, W - m.r]), y = d3.scaleLinear().domain([lo2, hi2]).range([H - m.b, m.t]);
  const colr = getComputedStyle(document.getElementById('stateChip')).color || css('--navy');
  const svg = d3.create('svg').attr('viewBox', `0 0 ${W} ${H}`).attr('role', 'img').attr('aria-label', 'Andamento dell\'indice di rischio nelle ultime 12 settimane');
  if (st.th > lo2 && st.th < hi2) svg.append('line').attr('x1', m.l).attr('x2', W - m.r).attr('y1', y(st.th)).attr('y2', y(st.th)).attr('stroke', css('--risk')).attr('stroke-dasharray', '3 3').attr('stroke-width', 0.8).attr('opacity', .7);
  const ln = d3.line().defined(d => !isNaN(d)).x((d, k) => x(k)).y(d => y(d)), ar = d3.area().defined(d => !isNaN(d)).x((d, k) => x(k)).y0(H - m.b).y1(d => y(d));
  svg.append('path').attr('d', ar(V)).attr('fill', colr).attr('opacity', .14);
  svg.append('path').attr('d', ln(V)).attr('fill', 'none').attr('stroke', colr).attr('stroke-width', 1.8).attr('stroke-linejoin', 'round');
  const lastK = V.length - 1; svg.append('circle').attr('cx', x(lastK)).attr('cy', y(V[lastK])).attr('r', 3).attr('fill', colr);
  const first = ok[0], d = V[lastK] - first;
  svg.append('text').attr('x', m.l).attr('y', H - 2).attr('font-size', 9).attr('fill', css('--muted')).text('12 sett. fa ' + Math.round(first));
  svg.append('text').attr('x', W - m.r).attr('y', H - 2).attr('text-anchor', 'end').attr('font-size', 9).attr('font-weight', 700).attr('fill', d > 1 ? css('--risk') : d < -1 ? css('--ok') : css('--muted')).text((d > 0 ? '+' : '') + Math.round(d));
  sp.replaceChildren(svg.node());
}
// ---- grafico dettagliato dell'indice di rischio (12 mesi) ----
function openIfiChart() {
  const i = st.sel, t1 = T[i], t0 = new Date(Date.UTC(t1.getUTCFullYear() - 1, t1.getUTCMonth(), t1.getUTCDate()));
  let a = 0; while (a < i && T[a] < t0) a++;
  const P = []; for (let k = a; k <= i; k++) if (!isNaN(IFI[k])) P.push({k, t: T[k], v: IFI[k]});
  if (P.length < 5) return;
  const LC = {'s-ok': '--ok', 's-yel': '--yel', 's-warn': '--amber', 's-risk': '--risk'}, col = v => css(LC[lev(v)]);
  const W = 640, H = 340, m = {l: 34, r: 28, t: 16, b: 30};
  const x = d3.scaleTime().domain([P[0].t, P[P.length - 1].t]).range([m.l, W - m.r]), y = d3.scaleLinear().domain([0, 100]).range([H - m.b, m.t]);
  const svg = d3.create('svg').attr('viewBox', `0 0 ${W} ${H}`).attr('role', 'img').attr('aria-label', 'Indice di rischio negli ultimi 12 mesi').style('width', '100%').style('height', 'auto');
  [[0, 40, '--ok'], [40, 55, '--yel'], [55, 70, '--amber'], [70, 100, '--risk']].forEach(b => svg.append('rect').attr('x', m.l).attr('width', W - m.l - m.r).attr('y', y(b[1])).attr('height', y(b[0]) - y(b[1])).attr('fill', css(b[2])).attr('opacity', .09));
  [0, 40, 55, 70, 100].forEach(g => { svg.append('line').attr('x1', m.l).attr('x2', W - m.r).attr('y1', y(g)).attr('y2', y(g)).attr('stroke', css('--line')).attr('stroke-width', .7); svg.append('text').attr('x', m.l - 6).attr('y', y(g) + 3).attr('text-anchor', 'end').attr('font-size', 10).attr('fill', css('--muted')).text(g); });
  d3.timeMonths(P[0].t, new Date(+P[P.length - 1].t + 864e5)).forEach(d => { svg.append('text').attr('x', x(d)).attr('y', H - 10).attr('text-anchor', 'middle').attr('font-size', 10).attr('fill', css('--muted')).text(d.toLocaleDateString('it-IT', {month: 'short', timeZone: 'UTC'}) + (d.getUTCMonth() === 0 ? ' ' + String(d.getUTCFullYear()).slice(2) : '')); });
  for (let q = 1; q < P.length; q++) svg.append('line').attr('x1', x(P[q - 1].t)).attr('y1', y(P[q - 1].v)).attr('x2', x(P[q].t)).attr('y2', y(P[q].v)).attr('stroke', col(P[q].v)).attr('stroke-width', 2.4).attr('stroke-linecap', 'round');
  // etichette: un punto circa ogni mese, più massimo, minimo e oggi
  const lab = new Map(); const step = Math.max(1, Math.round(P.length / 9));
  for (let q = P.length - 1; q >= 0; q -= step) lab.set(q, 1);
  let imax = 0, imin = 0; P.forEach((p, q) => { if (p.v > P[imax].v) imax = q; if (p.v < P[imin].v) imin = q; }); lab.set(imax, 1); lab.set(imin, 1);
  const keys = [...lab.keys()].sort((p, q) => p - q), shown = [];
  keys.forEach(q => { const last = q === P.length - 1; if (!last && shown.length && x(P[q].t) - x(P[shown[shown.length - 1]].t) < 38) { if (q !== imax && q !== imin) return; } if (last && shown.length && x(P[q].t) - x(P[shown[shown.length - 1]].t) < 38) shown.pop(); shown.push(q); });
  shown.forEach(q => { const p = P[q], c = col(p.v), up = q !== imin;
    svg.append('circle').attr('cx', x(p.t)).attr('cy', y(p.v)).attr('r', q === P.length - 1 ? 4.5 : 3).attr('fill', c).attr('stroke', css('--panel')).attr('stroke-width', 1.2);
    const tx = svg.append('text').attr('x', Math.min(W - m.r - 8, Math.max(m.l + 8, x(p.t)))).attr('y', y(p.v) + (up ? -9 : 17)).attr('text-anchor', 'middle').attr('font-size', 11.5).attr('font-weight', 800).attr('fill', c).text(Math.round(p.v));
    tx.append('title').text(fmtDl(p.t).trim() + ': ' + Math.round(p.v) + '/100'); });
  const fo = svg.append('g').style('pointer-events', 'none').attr('opacity', 0), fl = fo.append('line').attr('y1', m.t).attr('y2', H - m.b).attr('stroke', css('--muted')).attr('stroke-dasharray', '3 3'), fc = fo.append('circle').attr('r', 5).attr('stroke', css('--panel')).attr('stroke-width', 1.5), fb = fo.append('rect').attr('rx', 6).attr('height', 38).attr('fill', css('--navy')), ft1 = fo.append('text').attr('font-size', 11).attr('fill', '#fff'), ft2 = fo.append('text').attr('font-size', 14).attr('font-weight', 800);
  const bis = d3.bisector(d => d.t).center;
  svg.append('rect').attr('x', m.l).attr('y', m.t).attr('width', W - m.l - m.r).attr('height', H - m.t - m.b).attr('fill', 'transparent').style('cursor', 'crosshair')
    .on('mousemove touchmove', function (ev) { const pt = d3.pointer(ev.touches ? ev.touches[0] : ev, svg.node()), q = Math.max(0, Math.min(P.length - 1, bis(P, x.invert(pt[0])))), p = P[q], c = col(p.v), cx = x(p.t), cy = y(p.v), w = 150, bx = Math.min(W - m.r - w, Math.max(m.l, cx - w / 2)), by = cy < m.t + 60 ? cy + 14 : m.t + 6;
      fo.attr('opacity', 1); fl.attr('x1', cx).attr('x2', cx); fc.attr('cx', cx).attr('cy', cy).attr('fill', c); fb.attr('x', bx).attr('y', by).attr('width', w);
      ft1.attr('x', bx + 8).attr('y', by + 15).text(p.t.toLocaleDateString('it-IT', {day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC'})); ft2.attr('x', bx + 8).attr('y', by + 32).attr('fill', '#fff').text(Math.round(p.v) + ' / 100 · ' + ({'s-ok': 'basso', 's-yel': 'medio', 's-warn': 'attenzione', 's-risk': 'alto'}[lev(p.v)])).attr('font-size', 12); })
    .on('mouseleave touchend', () => fo.attr('opacity', 0));
  const dlg = document.getElementById('helpDlg'), body = document.getElementById('helpBody');
  dlg.classList.add('wide'); if (!dlg._wd) { dlg._wd = 1; dlg.addEventListener('close', () => dlg.classList.remove('wide')); }
  document.getElementById('helpTitle').textContent = 'Indice di rischio: ultimi 12 mesi';
  const wrap = document.createElement('div'); wrap.append(svg.node());
  const leg = document.createElement('div'); leg.className = 'ev-meta'; leg.style.cssText = 'display:flex;gap:12px;flex-wrap:wrap;margin-top:4px';
  [['--ok', 'sotto 40'], ['--yel', '40–54'], ['--amber', '55–69'], ['--risk', '70 o più']].forEach(l => { const s = document.createElement('span'); const d = document.createElement('i'); d.style.cssText = 'display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px;background:' + css(l[0]); s.append(d, l[1]); leg.append(s); });
  const f = P[0].v, l2 = P[P.length - 1].v, p = document.createElement('p');
  p.textContent = 'Oggi ' + Math.round(l2) + '/100; un anno fa ' + Math.round(f) + '. Massimo ' + Math.round(P[imax].v) + ' (' + fmtDl(P[imax].t).trim() + '), minimo ' + Math.round(P[imin].v) + ' (' + fmtDl(P[imin].t).trim() + '). Il colore della linea segue il livello di rischio di quel giorno.';
  body.replaceChildren(wrap, leg, p);
  if (typeof dlg.showModal === 'function' && !dlg.open) dlg.showModal(); else dlg.setAttribute('open', '');
}
document.addEventListener('click', e => { if (e.target.closest && e.target.closest('#ifiSpark') && DATA) { e.stopPropagation(); e.preventDefault(); openIfiChart(); } }, true);
// ---- indicatori Sentiment / grandi investitori / valutazione / macro: scheda dettagliata ----
function confLineChart(box, P, o) {
  const W = Math.max(300, box.clientWidth || 640), H = o.h || 230, m = {l: 40, r: 44, t: 14, b: 24};
  const ext = d3.extent(P, p => p.v), pad = (ext[1] - ext[0]) * .08 || 1, y0 = o.min != null ? o.min : ext[0] - pad, y1 = o.max != null ? o.max : ext[1] + pad;
  const x = d3.scaleUtc([P[0].t, P[P.length - 1].t], [m.l, W - m.r]), y = d3.scaleLinear([y0, y1], [H - m.b, m.t]);
  const svg = d3.create('svg').attr('viewBox', `0 0 ${W} ${H}`).style('width', '100%').style('height', 'auto').attr('role', 'img').attr('aria-label', o.label);
  (o.bands || []).forEach(b => svg.append('rect').attr('x', m.l).attr('width', W - m.l - m.r).attr('y', y(b[1])).attr('height', y(b[0]) - y(b[1])).attr('fill', css(b[2])).attr('opacity', .09));
  y.ticks(5).forEach(t => { svg.append('line').attr('x1', m.l).attr('x2', W - m.r).attr('y1', y(t)).attr('y2', y(t)).attr('stroke', css('--line')).attr('stroke-width', t === 0 ? 1.2 : .6); svg.append('text').attr('x', m.l - 5).attr('y', y(t) + 3).attr('text-anchor', 'end').attr('font-size', 10).attr('fill', css('--muted')).text(o.fmtY ? o.fmtY(t) : t); });
  const fm = itLocale.utcFormat('%b %y'); x.ticks(Math.min(8, Math.floor(W / 90))).forEach(t => svg.append('text').attr('x', x(t)).attr('y', H - 7).attr('text-anchor', 'middle').attr('font-size', 10).attr('fill', css('--muted')).text(fm(t)));
  if (o.color) { for (let q = 1; q < P.length; q++) svg.append('line').attr('x1', x(P[q - 1].t)).attr('y1', y(P[q - 1].v)).attr('x2', x(P[q].t)).attr('y2', y(P[q].v)).attr('stroke', o.color(P[q].v)).attr('stroke-width', 2).attr('stroke-linecap', 'round'); }
  else svg.append('path').attr('d', d3.line().x(p => x(p.t)).y(p => y(p.v))(P)).attr('fill', 'none').attr('stroke', css('--navy-2')).attr('stroke-width', 1.8).attr('stroke-linejoin', 'round');
  const L = P[P.length - 1], iM = d3.maxIndex(P, p => p.v), im = d3.minIndex(P, p => p.v), cl = o.color ? o.color(L.v) : css('--navy');
  [[iM, -8], [im, 15]].forEach(([q, dy]) => { const p = P[q]; svg.append('circle').attr('cx', x(p.t)).attr('cy', y(p.v)).attr('r', 3).attr('fill', css('--muted')); svg.append('text').attr('x', Math.min(W - m.r - 10, Math.max(m.l + 10, x(p.t)))).attr('y', y(p.v) + dy).attr('text-anchor', 'middle').attr('font-size', 10.5).attr('font-weight', 700).attr('fill', css('--muted')).text((q === iM ? 'max ' : 'min ') + o.fmt(p.v)); });
  svg.append('circle').attr('cx', x(L.t)).attr('cy', y(L.v)).attr('r', 4.5).attr('fill', cl).attr('stroke', css('--panel')).attr('stroke-width', 1.5);
  svg.append('text').attr('x', x(L.t) + 7).attr('y', y(L.v) + 4).attr('font-size', 11.5).attr('font-weight', 800).attr('fill', cl).text(o.fmt(L.v));
  const fo = svg.append('g').style('pointer-events', 'none').attr('opacity', 0), fl = fo.append('line').attr('y1', m.t).attr('y2', H - m.b).attr('stroke', css('--muted')).attr('stroke-dasharray', '3 3'), fc = fo.append('circle').attr('r', 4.5).attr('stroke', css('--panel')).attr('stroke-width', 1.5), fb = fo.append('rect').attr('rx', 6).attr('height', 36).attr('width', 150).attr('fill', css('--navy')), t1 = fo.append('text').attr('font-size', 11).attr('fill', '#fff'), t2 = fo.append('text').attr('font-size', 12.5).attr('font-weight', 800).attr('fill', '#fff');
  const bis = d3.bisector(p => p.t).center;
  svg.append('rect').attr('x', m.l).attr('y', m.t).attr('width', W - m.l - m.r).attr('height', H - m.t - m.b).attr('fill', 'transparent').style('cursor', 'crosshair')
    .on('mousemove touchmove', ev => { const pt = d3.pointer(ev.touches ? ev.touches[0] : ev, svg.node()), p = P[Math.max(0, Math.min(P.length - 1, bis(P, x.invert(pt[0]))))], cx = x(p.t), bx = Math.min(W - m.r - 150, Math.max(m.l, cx - 75));
      fo.attr('opacity', 1); fl.attr('x1', cx).attr('x2', cx); fc.attr('cx', cx).attr('cy', y(p.v)).attr('fill', o.color ? o.color(p.v) : css('--navy')); fb.attr('x', bx).attr('y', m.t + 4);
      t1.attr('x', bx + 8).attr('y', m.t + 18).text(p.t.toLocaleDateString('it-IT', {day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC'})); t2.attr('x', bx + 8).attr('y', m.t + 32).text(o.fmt(p.v)); })
    .on('mouseleave touchend', () => fo.attr('opacity', 0));
  box.replaceChildren(svg.node());
}
function openConfCard(id) {
  const c = DATA.confirm.find(x => x.id === id), a = COL[id], pa = COL['p_' + id]; if (!c || !a) return;
  const dlg = document.getElementById('repDlg'), body = document.getElementById('repDlgBody'); body.replaceChildren();
  let last = N - 1; while (last > 0 && isNaN(a[last])) last--;
  const fmt = v => isNaN(v) ? '—' : (FMT[id] ? FMT[id](v) : nf(v, 2)), pc = pa ? pa[last] : NaN, idx = isNaN(pc) ? null : pc >= 70 ? 3 : pc >= 55 ? 2 : pc >= 40 ? 1 : 0, cl = idx == null ? '' : 'c-' + ['ok', 'yel', 'warn', 'risk'][idx];
  const grp = XGROUPS.find(g => g[2].includes(id)), gk = grp ? grp[3] : null, t = FHL[id] || {};
  const sec = (title, cls) => { const d = document.createElement('div'); d.className = 'rsec' + (cls ? ' ' + cls : ''); const h = document.createElement('h4'); h.textContent = title; d.append(h); body.append(d); return d; };
  const para = (b, tx) => { const p = document.createElement('p'); p.textContent = tx; b.append(p); return p; };
  document.getElementById('repDlgLab').textContent = (grp ? grp[1] : 'Indicatore') + ' · dato al ' + fmtDl(T[last]).trim();
  document.getElementById('repDlgTitle').textContent = c.name;
  // 1) situazione
  const j4 = back(last, 21), j13 = back(last, 63), j52 = back(last, 252), pcs = k => pa ? pa[k] : NaN;
  const sb = document.createElement('div'); sb.className = 'sitbox ' + cl; sb.innerHTML = '<div class="t"></div><div></div>';
  sb.children[0].textContent = 'Ultimo: ' + fmt(a[last]) + (idx == null ? '' : ' · percentile di rischio ' + Math.round(pc) + '/100 (' + QN[idx] + ': ' + QL[idx] + ')');
  const verso = idx == null ? 'Dato non disponibile.' : idx === 3 ? t.hi : idx === 2 ? 'Verso il lato rischioso: ' + (t.hs || t.hi) : idx === 1 ? 'Nella media degli ultimi 5 anni: nessun segnale particolare.' : t.lo;
  const dv = (k, lab) => isNaN(pcs(k)) ? '' : lab + ' ' + fmt(a[k]) + ' (percentile ' + Math.round(pcs(k)) + ')';
  sb.children[1].textContent = (verso || '') + ' Quattro settimane fa: ' + dv(j4, '').trim() + (pcs(last) - pcs(j4) >= 5 ? ' — sta peggiorando.' : pcs(j4) - pcs(last) >= 5 ? ' — sta migliorando.' : ' — stabile.');
  body.append(sb);
  // 2) cosa conviene fare
  const pv = sec('Cosa conviene fare', 'rparere ' + cl);
  const AZ = ['Quadro tranquillo: questo indicatore non chiede cautela in più. Resta valido il consiglio generale della pagina.', 'Nella media: nessuna indicazione particolare. Si tiene d\'occhio insieme agli altri, senza cambiare nulla.', 'Attenzione: è sul lato rischioso. Da solo non cambia l\'indicazione, ma è un motivo per non aumentare l\'esposizione in fretta.', 'Segnale di cautela: è tra i valori più rischiosi degli ultimi 5 anni. Da solo non basta a cambiare il consiglio, ma rafforza la prudenza e giustifica di aspettare conferme prima di aumentare.'];
  para(pv, idx == null ? 'Dato non disponibile.' : AZ[idx]);
  para(pv, 'Ruolo nel modello: ' + (gk && st[gk] > 0 ? 'concorre al calcolo dell\'indice con il gruppo "' + grp[1] + '".' : 'oggi non entra nel calcolo dell\'indice di rischio (nei test non migliora la previsione o cambia segno nel tempo): serve come controllo e conferma.')).className = 'rnote';
  // 3) grafici
  const sc = sec('Valore negli ultimi 5 anni'); const b1 = document.createElement('div'); b1.className = 'chart-box'; sc.append(b1);
  const i0 = Math.max(0, last - 1260), V = [], PP = []; for (let k = i0; k <= last; k++) { if (!isNaN(a[k])) V.push({t: T[k], v: a[k]}); if (pa && !isNaN(pa[k])) PP.push({t: T[k], v: pa[k]}); }
  const sp = sec('Livello di rischio nel tempo (percentile 0–100)'); const b2 = document.createElement('div'); b2.className = 'chart-box'; sp.append(b2);
  const lg = document.createElement('div'); lg.className = 'legend4'; lg.innerHTML = LEGEND4; sp.append(lg);
  para(sp, 'Il percentile dice quanto il valore di oggi è alto rispetto agli ultimi 5 anni: 78 vuol dire che solo il 22% dei giorni ha avuto un valore più rischioso. Il colore della linea segue il livello di rischio del giorno.');
  // 4) cosa significa
  const hp = HELP[id]; if (hp || c.desc) { const cm = sec('Cosa misura e cosa significa per il mercato'); para(cm, c.desc + '.'); if (hp) hp.slice(1).forEach(x => para(cm, x)); if (EX[id]) body.append(exBox(typeof EX[id] === 'function' ? EX[id]() : EX[id])); }
  // 5) storico
  const an = DATA.stats.auc_near[id], aa = DATA.stats.auc[id];
  const sh = sec('Quanto è stato utile in passato');
  para(sh, 'La capacità di previsione (AUC) va da 0,5 (come lanciare una moneta) a 1 (perfetta). Questo indicatore ha ' + (aa == null ? '—' : nf(aa, 2)) + ' sull\'intero periodo e ' + (an == null ? '—' : nf(an, 2)) + ' nei momenti vicini ai massimi, quando conta di più.' + ((an != null && an < 0.52) ? ' Valori intorno o sotto 0,5 significano che da solo non ha anticipato i ribassi: per questo è solo un controllo.' : an != null && an >= 0.6 ? ' È un valore discreto: l\'indicatore ha anticipato abbastanza bene i ribassi, ma resta un segnale di probabilità, non una previsione.' : ''));
  const rg = [['Oggi', last], ['4 settimane fa', j4], ['3 mesi fa', j13], ['1 anno fa', j52]].filter(r => !isNaN(a[r[1]]));
  const tw = document.createElement('div'); tw.className = 'tbl-wrap'; const tb = document.createElement('table'); tb.className = 'htab'; tb.innerHTML = '<thead><tr><th>Quando</th><th class="r">Valore</th><th class="r">Percentile di rischio</th></tr></thead><tbody></tbody>';
  rg.forEach(([lab, k]) => { const tr = document.createElement('tr'); if (k === last) tr.className = 'now'; const p = pcs(k); const q = isNaN(p) ? null : p >= 70 ? 3 : p >= 55 ? 2 : p >= 40 ? 1 : 0; [lab, fmt(a[k]), isNaN(p) ? '—' : Math.round(p)].forEach((v, j) => { const td = document.createElement('td'); td.textContent = v; if (j) td.className = 'r mono'; if (j === 2 && q != null) { td.style.color = css(QV[q]); td.style.fontWeight = 700; } tr.append(td); }); tb.querySelector('tbody').append(tr); });
  tw.append(tb); sh.append(tw);
  const nt = para(body, 'Indicazione generale basata sui dati di questo indicatore: va letta insieme agli altri riquadri e al proprio profilo di rischio. Non è una consulenza personalizzata.'); nt.className = 'rnote';
  if (typeof dlg.showModal === 'function' && !dlg.open) dlg.showModal(); else dlg.setAttribute('open', '');
  dlg.querySelector('.help-in').scrollTop = 0;
  requestAnimationFrame(() => {
    if (V.length > 5) confLineChart(b1, V, {fmt, label: c.name + ', ultimi 5 anni'});
    if (PP.length > 5) confLineChart(b2, PP, {fmt: v => Math.round(v), min: 0, max: 100, bands: [[0, 40, '--ok'], [40, 55, '--yel'], [55, 70, '--amber'], [70, 100, '--risk']], color: v => css(QV[v >= 70 ? 3 : v >= 55 ? 2 : v >= 40 ? 1 : 0]), label: c.name + ', livello di rischio', h: 200});
  });
}
