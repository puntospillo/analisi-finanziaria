#!/usr/bin/env python3
"""Aggiorna il prezzo di riferimento delle idee in valutazione.json con l'ultima chiusura di Yahoo Finance.
Uso: prezzi_idee.py  (legge code/simboli_idee.json: nome idea -> simbolo Yahoo; le idee senza simbolo restano invariate)"""
import json, os, sys, urllib.request, urllib.parse, datetime as dt, concurrent.futures as cf
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); UA = {'User-Agent': 'Mozilla/5.0'}
S = json.load(open(R + '/code/simboli_idee.json')); v = json.load(open(R + '/valutazione.json'))
def px(s):
    try:
        j = json.load(urllib.request.urlopen(urllib.request.Request('https://query1.finance.yahoo.com/v8/finance/chart/%s?range=5d&interval=1d' % urllib.parse.quote(s), headers=UA), timeout=25))['chart']['result'][0]
        m = j['meta']; return s, m['regularMarketPrice'], m.get('currency', ''), dt.datetime.fromtimestamp(m['regularMarketTime'], dt.timezone.utc).strftime('%d/%m/%Y')
    except Exception: return s, None, None, None
with cf.ThreadPoolExecutor(8) as ex: P = {r[0]: r for r in ex.map(px, set(S.values()))}
n = 0
for i in v['idee']:
    s = S.get(i['nome']); r = P.get(s)
    if not r or r[1] is None: continue
    sym = {'EUR': '€', 'USD': '$', 'CHF': 'CHF'}.get(r[2], r[2])
    i['prezzo_rif'] = '%s %s (Yahoo Finance, %s)' % (('%.2f' % r[1]).replace('.', ','), sym, r[3]); n += 1
json.dump(v, open(R + '/valutazione.json', 'w'), ensure_ascii=False, indent=1); print('PREZZI idee aggiornati: %d su %d' % (n, len(v['idee'])))
