// v2.5: il modello di base si calcola per profilo nella pagina (computeAAVAll -> AVP[profilo]); runIFI2 usa AVP[pk]
// ================================================================== motore 2.0 (segnali precoci + rientro + profilo)
// Ricerca non validata. Parametri fissati prima delle prove sul passato (dalla specifica IFI-2.0), uguali per tutti:
// il profilo dell'utente NON cambia la misura del rischio, cambia solo quanto si riduce e quanto in fretta si rientra.
const E2 = {win: 1260, minObs: 252, on: 65, off: 55, kOn: 3, kWin: 5, fam: 65, step: 1, minFam: 4,
  w: {br: 0.30, dv: 0.20, cr: 0.20, bt: 0.15, df: 0.15},
  rw: {rb: 0.30, rc: 0.25, rv: 0.20, rm: 0.15, re: 0.10}, rOn: 65, rImp: 60, rConf: 2, rGap: 5, noShock: 3, rchk: 42, rchkShock: 2};
// v2.5: ogni profilo ha il suo blocco degli aumenti dopo uno shock forte (base: shMin, shCap, shIfi) e il suo rientro (cap, slow, stepC)
const PROF = {
  prudente: {lab: 'Prudente', cap: 4, slow: 15, stepC: 1, recheck: true, base: {shMin: 5, shCap: 15, shIfi: 58}},
  bilanciato: {lab: 'Bilanciato', cap: 5, slow: 10, stepC: 1, recheck: false, base: {shMin: 5, shCap: 15, shIfi: 58}},
  dinamico: {lab: 'Dinamico', cap: 6, slow: 5, stepC: 1, recheck: false, base: {shMin: 3, shCap: 10, shIfi: 60}},
  reattivo: {lab: 'Reattivo', cap: 7, slow: 3, stepC: 2, recheck: false, base: {shMin: 2, shCap: 5, shIfi: 62, upDaily: true, up: 0.1}}
};
const FAM2 = {br: 'Ampiezza in peggioramento', dv: 'Indice che regge, titoli medi no', cr: 'Credito', bt: 'Grandi titoli tecnologici', df: 'Rotazione verso i difensivi'};
const REC2 = {rb: 'Ampiezza in ripresa', rc: 'Credito in ripresa', rv: 'Volatilità in calo', rm: 'Prezzi sopra la media a 20 sedute', re: 'Titoli medi in recupero'};
let X2 = null, F2 = null, Q2 = {};
// percentile mobile su 5 anni (solo dati fino al giorno stesso): 100 = valore più alto della finestra
function pr2(x) {
  const out = new Float64Array(N).fill(NaN);
  for (let i = 0; i < N; i++) { const v = x[i]; if (isNaN(v)) continue; let n = 0, b = 0, e = 0;
    for (let k = Math.max(0, i - E2.win + 1); k <= i; k++) { const u = x[k]; if (isNaN(u)) continue; n++; if (u < v) b++; else if (u === v) e++; }
    if (n >= E2.minObs) out[i] = 100 * (b + 0.5 * e) / n; }
  return out;
}
// v2.3: le serie aggiuntive si agganciano per data; senza date si accettano solo se lunghezza e ultima seduta coincidono
let X2ERR = '';
function loadExtra(x) {
  X2 = {}; F2 = null; X2ERR = '';
  if (!x || !x.rows || !x.cols) { X2ERR = 'file delle serie aggiuntive non disponibile'; return false; }
  let map = null;
  if (x.dates) { const pos = new Map(x.dates.map((d, k) => [d, k])); map = DATA.dates.map(d => pos.has(d) ? pos.get(d) : -1); const miss = map.filter(k => k < 0).length; if (miss > 5 || map[N - 1] < 0) { X2ERR = 'serie aggiuntive non allineate alle date dei dati (' + miss + ' sedute mancanti)'; X2 = {}; return false; } }
  else if (x.rows.length !== N || x.as_of !== DATA.as_of) { X2ERR = 'serie aggiuntive di un altro aggiornamento (' + (x.as_of || 'data sconosciuta') + ')'; return false; }
  x.cols.forEach((c, j) => { const a = new Float64Array(N); for (let i = 0; i < N; i++) { const k = map ? map[i] : i, v = k < 0 ? null : x.rows[k][j]; a[i] = v == null ? NaN : v; } X2[c] = a; });
  return true;
}
function computeFeat2() {
  const A = n => new Float64Array(n).fill(NaN), spx = COL.spx, has = !!(X2 && X2.QQQ);
  const dif = (x, k) => { const o = A(N); for (let i = k; i < N; i++) o[i] = x[i] - x[i - k]; return o; };
  const ret = (x, k) => { const o = A(N); for (let i = k; i < N; i++) o[i] = x[i] / x[i - k] - 1; return o; };
  const neg = x => x.map(v => -v);
  const sma = (x, k) => { const o = A(N); let s = 0, n = 0; for (let i = 0; i < N; i++) { if (!isNaN(x[i])) { s += x[i]; n++; } if (i >= k) { if (!isNaN(x[i - k])) { s -= x[i - k]; n--; } } if (n === k) o[i] = s / k; } return o; };
  const mean = (arrs) => { const o = A(N); for (let i = 0; i < N; i++) { let s = 0, n = 0; for (const a of arrs) if (a && !isNaN(a[i])) { s += a[i]; n++; } if (n) o[i] = s / n; } return o; };
  // --- famiglie di rischio (0-100, alto = peggio)
  const d200 = dif(COL.pct200, 20), d50 = dif(COL.pct50, 20);
  const nlh = A(N); for (let i = 0; i < N; i++) nlh[i] = COL.nl10[i] - COL.nh10[i];
  const br = mean([pr2(neg(d200)), pr2(neg(d50)), pr2(nlh)]);
  const dv = mean([COL.p_ewcap63, pr2(neg(dif(COL.ewcap63, 20)))]);
  let cr, bt = A(N), df = A(N), ratio = null, q = null;
  if (has) {
    ratio = A(N); for (let i = 0; i < N; i++) ratio[i] = X2.HYG[i] / X2.IEF[i];
    cr = mean([COL.p_hy63, pr2(neg(ret(ratio, 20))), pr2(neg(ret(ratio, 60)))]);
    q = X2.QQQ; const m50 = sma(q, 50), m200 = sma(q, 200), dd = A(N), g50 = A(N), g200 = A(N);
    for (let i = 0; i < N; i++) { let hi = -Infinity; for (let k = Math.max(0, i - 251); k <= i; k++) if (!isNaN(q[k])) hi = Math.max(hi, q[k]); dd[i] = hi > 0 ? 1 - q[i] / hi : NaN; g50[i] = -(q[i] / m50[i] - 1); g200[i] = -(q[i] / m200[i] - 1); }
    bt = mean([pr2(neg(ret(q, 20))), pr2(g50), pr2(g200), pr2(dd)]);
    const bas = (ids, k) => { const o = A(N); for (let i = k; i < N; i++) { let s = 0, n = 0; for (const id of ids) { const v = X2[id][i] / X2[id][i - k] - 1; if (!isNaN(v)) { s += v; n++; } } if (n === ids.length) o[i] = s / n; } return o; };
    const rel = k => { const d = bas(['XLU', 'XLP', 'XLV'], k), c = bas(['XLY', 'XLI', 'XLF', 'XLK'], k), o = A(N); for (let i = 0; i < N; i++) o[i] = d[i] - c[i]; return o; };
    df = mean([pr2(rel(20)), pr2(rel(60))]);
  } else cr = COL.p_hy63;
  const fam = {br, dv, cr, bt, df}, ew = A(N), cov = new Float64Array(N), nfam = new Uint8Array(N), nok = new Uint8Array(N), brAbs = new Uint8Array(N);
  for (let i = 0; i < N; i++) { let s = 0, w = 0, n = 0;
    brAbs[i] = (d200[i] <= -10 || d50[i] <= -15) ? 1 : 0;
    for (const k in E2.w) { const v = fam[k][i]; if (!isNaN(v)) { s += E2.w[k] * v; w += E2.w[k]; nok[i]++; if (v >= E2.fam || (k === 'br' && brAbs[i])) n++; } }
    cov[i] = w; ew[i] = w > 0 ? s / w : NaN; nfam[i] = n; }
  // --- componenti del rientro (0-100, alto = meglio)
  const rb = mean([pr2(dif(COL.pct50, 5)), pr2(dif(COL.pct50, 10))]);
  const rc = has ? mean([pr2(ret(ratio, 5)), pr2(ret(ratio, 10)), pr2(neg(dif(COL.p_hy63, 10)))]) : pr2(neg(dif(COL.p_hy63, 10)));
  const rv = mean([pr2(neg(dif(COL.vix, 10))), pr2(neg(dif(COL.move, 10)))]);
  const m20 = sma(spx, 20), qm20 = has ? sma(q, 20) : null, rm = A(N);
  for (let i = 0; i < N; i++) { if (isNaN(m20[i])) continue; const a = spx[i] >= m20[i] ? 1 : 0; if (has && !isNaN(qm20[i])) rm[i] = 50 * (a + (q[i] >= qm20[i] ? 1 : 0)); else rm[i] = 100 * a; }
  const re = pr2(dif(COL.ewcap63, 10));
  const rec = {rb, rc, rv, rm, re}, rs = A(N), nimp = new Uint8Array(N);
  for (let i = 0; i < N; i++) { let s = 0, w = 0, n = 0; for (const k in E2.rw) { const v = rec[k][i]; if (!isNaN(v)) { s += E2.rw[k] * v; w += E2.rw[k]; if (v >= E2.rImp) n++; } } rs[i] = w >= 0.7 ? s / w : NaN; nimp[i] = n; }
  F2 = {fam, ew, cov, nfam, nok, brAbs, rec, rs, nimp, d200, d50, has, hyg: has ? X2.HYG.map(v => !isNaN(v)) : null};
}
// quota 2.0 per un profilo: parte dalla quota dell'allocazione adattiva (invariata) e le mette un tetto quando i segnali
// precoci sono confermati (tetto del profilo, raggiunto a 10 punti per seduta); il tetto risale a tranche di 10 punti.
// Il tetto agisce solo quando la quota di base è ancora alta: non somma una seconda riduzione a quella già fatta dal modello di base.
function runIFI2(pk) {
  const P = PROF[pk], A = AVP[pk], q = new Float64Array(N), stt = new Array(N), capA = new Uint8Array(N), actA = new Uint8Array(N), why = new Array(N);
  let cap = 10, act = false, sinceOff = 0, lastTr = -1e9, lastShock = -1e9, shk0 = -1e9, prev = null;
  for (let i = 0; i < N; i++) {
    const leg = Math.round(A.q[i] * 10), s = F2.ew[i], ok = F2.nok[i] >= (F2.has ? E2.minFam : 3) && !isNaN(s);   // v2.3: almeno 4 famiglie su 5 (3 solo se le serie aggiuntive mancano del tutto: avviso nel riquadro)
    const shn = shockAt(i).n; if (shn >= 1) lastShock = i;
    // v2.3: il ricontrollo del Prudente parte dal primo shock forte e dura al massimo rchk sedute: nuovi shock non lo allungano
    if (shn >= E2.rchkShock && i - shk0 > E2.rchk) shk0 = i;
    const hard = A.cap[i] <= AAV.emCap + 1e-9;
    let t, state, w = '';
    if (!ok) { t = prev == null ? leg : Math.min(prev, leg); state = 'dati'; w = 'dati insufficienti per i segnali precoci: nessun aumento'; }
    else {
      let hiC = 0, loC = 0; for (let k = Math.max(0, i - E2.kWin + 1); k <= i; k++) { if (F2.ew[k] >= E2.on) hiC++; if (F2.ew[k] < E2.off) loC++; }
      if (!act && hiC >= E2.kOn && F2.nfam[i] >= 2) { act = true; if (cap >= 10) cap = Math.max(P.cap, prev == null ? leg : prev); }
      else if (act && loC >= E2.kOn) { act = false; sinceOff = 0; }
      let rsok = i >= E2.rConf - 1; for (let k = 0; rsok && k < E2.rConf; k++) rsok = F2.rs[i - k] >= E2.rOn;   // v2.3: usa il parametro rConf (prima 2 era scritto nel codice)
      const rconf = rsok && F2.nimp[i] >= 3 && (i - lastShock) > E2.noShock && !hard;
      if (act) { cap = Math.max(P.cap, cap - E2.step); state = 'riduzione'; w = 'segnali precoci confermati: ' + hiC + ' chiusure su 5 sopra ' + E2.on + ', ' + F2.nfam[i] + ' famiglie in peggioramento; tetto ' + cap * 10 + '%'; }
      else if (cap < 10) { sinceOff++;
        if (rconf && i - lastTr >= E2.rGap) { cap = Math.min(10, cap + E2.step * P.stepC); lastTr = i; w = 'rientro confermato: tetto alzato a ' + cap * 10 + '%'; }
        else if (sinceOff >= P.slow && i - lastTr >= P.slow && s < E2.off && (i - lastShock) > E2.noShock && !hard) { cap += E2.step; lastTr = i; w = 'allerta rientrata da ' + sinceOff + ' sedute: tetto alzato a ' + cap * 10 + '%'; }
        else w = 'allerta rientrata, tetto ' + cap * 10 + '% in attesa di conferme';
        state = 'rientro'; }
      else { state = s >= E2.off ? 'allerta' : 'normale'; w = state === 'allerta' ? 'segnali precoci in aumento, non ancora confermati' : 'nessun segnale precoce'; }
      t = Math.min(leg, cap);
      if (prev != null && t > prev) {
        // v2.3: durante la riduzione vale solo il tetto del profilo (come da specifica): prima la quota restava ferma al livello più basso anche se il tetto era più alto
        if (P.recheck && (i - shk0) <= E2.rchk && IFI[i] >= 55) { t = prev; w += '; ricontrollo dopo lo shock: indice ancora da 55 in su, nessun aumento'; }
      }
    }
    q[i] = t / 10; stt[i] = state; capA[i] = cap; actA[i] = act ? 1 : 0; why[i] = w; prev = t;
  }
  return {q, st: stt, cap: capA, act: actA, why};
}
function computeIFI2() { computeFeat2(); Q2 = {}; for (const k in PROF) Q2[k] = runIFI2(k); }
