#!/usr/bin/env python3
"""Sceglie i titoli di maggior rilievo dell'ultima seduta tra i primi 30 per peso dell'S&P 500.
Metodo (fisso, ripetibile): contributo = peso ufficiale SPY × variazione dell'ultima seduta (Yahoo Finance).
Punteggio = |contributo| × (1 + min(max(volume/media 20 sedute − 1, 0), 1)): conta chi ha spostato di più l'indice,
con un bonus fino a ×2 se è stato scambiato molto più del solito (segno che c'è una notizia).
Uso: titoli_giorno.py <out.json>   (legge ifi_data.json → holdings.top)"""
import json, os, sys, urllib.request, urllib.parse, datetime as dt, concurrent.futures as cf
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); UA = {'User-Agent': 'Mozilla/5.0'}
H = json.load(open(R + '/ifi_data.json'))['holdings']
top = H['top'][:30]
def get(t):
    s = t['ticker'].replace('.', '-')
    try:
        j = json.load(urllib.request.urlopen(urllib.request.Request('https://query1.finance.yahoo.com/v8/finance/chart/%s?range=1y&interval=1d' % urllib.parse.quote(s), headers=UA), timeout=25))['chart']['result'][0]
        q = j['indicators']['quote'][0]; D = {}
        for ts, c, v in zip(j['timestamp'], q['close'], q['volume']):
            if c is not None: D[dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime('%Y-%m-%d')] = (c, v or 0)
        ks = sorted(D)
        if len(ks) < 22: return None
        c1, c0 = D[ks[-1]][0], D[ks[-2]][0]; mx = max(D[k][0] for k in ks); r21 = (c1 / D[ks[-22]][0] - 1) * 100; vm = sum(D[k][1] for k in ks[-21:-1]) / 20
        g1 = (c1 / c0 - 1) * 100; vr = D[ks[-1]][1] / vm if vm else 1
        contr = t['weight'] * g1 / 100; score = abs(contr) * (1 + min(max(vr - 1, 0), 1))
        return {'nome': t['name'], 'ticker': t['ticker'], 'peso': round(t['weight'], 2), 'prezzo': round(c1, 2), 'data': ks[-1], 'g1': round(g1, 2),
                'vol_rel': round(vr, 2), 'contributo': round(contr, 3), 'punteggio': round(score, 4), 'da_massimo_1a': round((c1 / mx - 1) * 100, 1), 'r21': round(r21, 1), 'serie': [[k, round(D[k][0], 2)] for k in ks[-252:]]}
    except Exception: return None
with cf.ThreadPoolExecutor(8) as ex: res = [r for r in ex.map(get, top) if r]
res.sort(key=lambda r: -r['punteggio'])
out = {'metodo': "Tra i 30 titoli più pesanti dell'S&P 500 conta chi ha spostato di più l'indice nell'ultima seduta (peso × variazione del giorno), con un bonus se è stato scambiato molto più del solito: di solito c'è una notizia.",
       'pesi_al': H.get('asof'), 'candidati': res[:8]}
json.dump(out, open(sys.argv[1] if len(sys.argv) > 1 else '/tmp/titoli_cand.json', 'w'), ensure_ascii=False, indent=1)
for r in res[:8]: print(r['ticker'], r['peso'], r['g1'], r['vol_rel'], r['contributo'], r['punteggio'])
