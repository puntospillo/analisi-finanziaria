#!/usr/bin/env python3
"""Analisi Finanziaria 2.0 (locale) - serie giornaliere aggiuntive per i segnali precoci.
Scarica da Yahoo Finance le chiusure rettificate (dividendi e frazionamenti) di pochi ETF
e le allinea alle date di ifi_data.json. Solo libreria standard. Nessun dato futuro: ogni
valore è la chiusura di quel giorno.
Uso: python3 scarica_extra.py <ifi_data.json> <extra_data.json>
"""
import json, sys, time, urllib.request, urllib.parse, datetime as dt
TICKERS = ['XLU', 'XLP', 'XLV', 'XLY', 'XLI', 'XLF', 'XLK', 'QQQ', 'HYG', 'IEF', '^SP500TR']
NAMES = {'^SP500TR': 'SPXTR'}   # S&P 500 con i dividendi reinvestiti (per le prove sul passato)
UA = {'User-Agent': 'Mozilla/5.0'}

def one(t):
    url = ('https://query1.finance.yahoo.com/v8/finance/chart/%s?period1=0&period2=%d&interval=1d&events=div%%2Csplit'
           % (urllib.parse.quote(t), int(time.time()) + 86400))
    for k in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                j = json.load(r)['chart']['result'][0]
            break
        except Exception as e:
            if k == 3: raise
            time.sleep(2 + 2 * k)
    ts = j['timestamp']; adj = j['indicators']['adjclose'][0]['adjclose']
    off = j['meta'].get('gmtoffset', -18000)
    out = {}
    for s, v in zip(ts, adj):
        if v is None: continue
        d = dt.datetime.utcfromtimestamp(s + off).strftime('%Y-%m-%d')
        out[d] = v
    return out

def main(src, dst):
    base = json.load(open(src))
    dates = base['dates']
    series, first = {}, {}
    for t in TICKERS:
        s = one(t); series[t] = s; first[t] = min(s) if s else None
        print('%-8s %5d sedute dal %s al %s' % (t, len(s), first[t], max(s)), flush=True)
    rows = []
    for d in dates:
        rows.append([None if series[t].get(d) is None else float('%.5g' % series[t][d]) for t in TICKERS])
    last = rows[-1]
    cols = [NAMES.get(t, t) for t in TICKERS]
    # le date servono alla pagina per agganciare le serie per data e non per posizione di riga
    out = {'generated_at': dt.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'), 'as_of': dates[-1],
           'source': 'Yahoo Finance, chiusure rettificate', 'cols': cols, 'first': {NAMES.get(t, t): v for t, v in first.items()},
           'missing_last': [c for c, v in zip(cols, last) if v is None], 'dates': dates, 'rows': rows}
    json.dump(out, open(dst, 'w'), separators=(',', ':'))
    print('scritto', dst, 'ultima seduta', dates[-1], 'mancanti ultima seduta:', out['missing_last'])

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
