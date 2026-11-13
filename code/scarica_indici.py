#!/usr/bin/env python3
"""Scarica da Yahoo Finance gli indici mondiali, materie prime, cambi, tassi e cripto: ultimo prezzo, variazioni e serie 1 anno.
Uso: scarica_indici.py <file_uscita.json>. Non blocca l'aggiornamento: se un simbolo manca, resta fuori."""
import sys, json, urllib.request, urllib.parse, concurrent.futures as cf, datetime as dt
UA = {'User-Agent': 'Mozilla/5.0'}
G = [('Stati Uniti', [('^GSPC', 'S&P 500'), ('^IXIC', 'Nasdaq Composite'), ('^NDX', 'Nasdaq 100'), ('^DJI', 'Dow Jones'), ('^RUT', 'Russell 2000'), ('^VIX', 'VIX (paura)')]),
     ('Europa', [('FTSEMIB.MI', 'FTSE MIB (Italia)'), ('^GDAXI', 'DAX (Germania)'), ('^FCHI', 'CAC 40 (Francia)'), ('^FTSE', 'FTSE 100 (Regno Unito)'), ('^STOXX50E', 'Euro Stoxx 50'), ('^IBEX', 'IBEX 35 (Spagna)'), ('^SSMI', 'SMI (Svizzera)')]),
     ('Asia e resto del mondo', [('^N225', 'Nikkei 225 (Giappone)'), ('^HSI', 'Hang Seng (Hong Kong)'), ('000001.SS', 'Shanghai (Cina)'), ('^KS11', 'Kospi (Corea)'), ('^BSESN', 'Sensex (India)'), ('^AXJO', 'ASX 200 (Australia)'), ('^BVSP', 'Bovespa (Brasile)')]),
     ('Materie prime', [('BZ=F', 'Petrolio Brent'), ('CL=F', 'Petrolio WTI'), ('NG=F', 'Gas naturale USA'), ('GC=F', 'Oro'), ('SI=F', 'Argento'), ('HG=F', 'Rame'), ('PL=F', 'Platino')]),
     ('Cambi', [('EURUSD=X', 'Euro / Dollaro'), ('EURGBP=X', 'Euro / Sterlina'), ('EURCHF=X', 'Euro / Franco svizzero'), ('USDJPY=X', 'Dollaro / Yen'), ('DX-Y.NYB', 'Indice del dollaro')]),
     ('Tassi (rendimento %)', [('^IRX', 'Treasury 3 mesi'), ('^FVX', 'Treasury 5 anni'), ('^TNX', 'Treasury 10 anni'), ('^TYX', 'Treasury 30 anni')]),
     ('Cripto', [('BTC-USD', 'Bitcoin'), ('ETH-USD', 'Ethereum'), ('SOL-USD', 'Solana'), ('XRP-USD', 'XRP')])]
def one(s):
    for host in ('query1', 'query2'):
        try:
            u = 'https://%s.finance.yahoo.com/v8/finance/chart/%s?range=1y&interval=1d' % (host, urllib.parse.quote(s))
            j = json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=25))['chart']['result'][0]
            ts = j['timestamp']; cl = j['indicators']['quote'][0]['close']
            P = [(t, c) for t, c in zip(ts, cl) if c is not None]
            m = j['meta']; last = m.get('regularMarketPrice') or P[-1][1]
            if P and abs(P[-1][1] - last) > 1e-9 and m.get('regularMarketTime', 0) > P[-1][0]: P.append((m['regularMarketTime'], last))
            D = {}
            for t, c in P: D[dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime('%Y-%m-%d')] = (t, c)   # una sola barra per giorno
            P = [D[k] for k in sorted(D)]
            return s, P
        except Exception: continue
    return s, None
def chg(P, days):
    t0 = P[-1][0] - days * 86400; b = [c for t, c in P if t <= t0]
    return None if not b or not b[-1] else (P[-1][1] / b[-1] - 1) * 100
syms = [s for _, L in G for s, _ in L]
with cf.ThreadPoolExecutor(8) as ex: R = dict(ex.map(one, syms))
out = {'generated_at': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'gruppi': []}
def build_rows(g, L, R):
    rows = []
    for s, n in L:
        P = R.get(s)
        if not P or len(P) < 5: continue
        yr = dt.datetime.fromtimestamp(P[-1][0], dt.timezone.utc).year; y0 = [c for t, c in P if dt.datetime.fromtimestamp(t, dt.timezone.utc).year < yr]
        rate = g.startswith('Tassi')
        d = lambda a, b: None if a is None or b is None else round(a - b, 2)
        hi = max(c for _, c in P)
        rows.append({'s': s, 'n': n, 'p': round(P[-1][1], 4), 'data': dt.datetime.fromtimestamp(P[-1][0], dt.timezone.utc).strftime('%Y-%m-%d'),
                     'g1': None if len(P) < 2 else round(P[-1][1] - P[-2][1], 3) if rate else round((P[-1][1] / P[-2][1] - 1) * 100, 2),
                     'm1': None if chg(P, 30) is None else (round(P[-1][1] - [c for t, c in P if t <= P[-1][0] - 30 * 86400][-1], 3) if rate else round(chg(P, 30), 1)),
                     'y0': None if not y0 else (round(P[-1][1] - y0[-1], 3) if rate else round((P[-1][1] / y0[-1] - 1) * 100, 1)),
                     'a1': None if chg(P, 364) is None else (round(P[-1][1] - [c for t, c in P if t <= P[-1][0] - 364 * 86400][-1], 3) if rate else round(chg(P, 364), 1)),
                     'dmax': round((P[-1][1] / hi - 1) * 100, 1), 'sd': [dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime('%Y-%m-%d') for t, c in P][::-2][::-1], 'sp': [round(c, 3) for t, c in P][::-2][::-1]})
    return rows
for g, L in G: out['gruppi'].append({'g': g, 'righe': build_rows(g, L, R)})
# v2.4: approfondimento Italia - principali titoli del FTSE MIB (settore) e spread BTP-Bund a 10 anni (OECD via FRED, mensile)
IT = [('ISP.MI', 'Intesa Sanpaolo', 'Banche'), ('UCG.MI', 'UniCredit', 'Banche'), ('BAMI.MI', 'Banco BPM', 'Banche'), ('BMPS.MI', 'Monte dei Paschi', 'Banche'), ('BPE.MI', 'BPER Banca', 'Banche'), ('FBK.MI', 'FinecoBank', 'Banche'),
      ('G.MI', 'Generali', 'Assicurazioni'), ('PST.MI', 'Poste Italiane', 'Servizi finanziari'), ('ENEL.MI', 'Enel', 'Energia elettrica'), ('ENI.MI', 'Eni', 'Petrolio e gas'), ('TRN.MI', 'Terna', 'Reti elettriche'), ('SRG.MI', 'Snam', 'Reti gas'),
      ('RACE.MI', 'Ferrari', 'Auto e lusso'), ('MONC.MI', 'Moncler', 'Lusso'), ('STLAM.MI', 'Stellantis', 'Auto'), ('LDO.MI', 'Leonardo', 'Difesa'), ('PRY.MI', 'Prysmian', 'Industria'), ('STMMI.MI', 'STMicroelectronics', 'Semiconduttori'), ('TIT.MI', 'Telecom Italia', 'Telecomunicazioni')]
with cf.ThreadPoolExecutor(8) as ex: RI = dict(ex.map(one, [x[0] for x in IT]))
it_rows = build_rows('Italia', [(a, b) for a, b, _ in IT], RI); SET = {a: c for a, _, c in IT}
for r in it_rows: r['set'] = SET[r['s']]; r.pop('sd', None); r.pop('sp', None)
def fred(sid):
    try:
        t = urllib.request.urlopen('https://fred.stlouisfed.org/graph/fredgraph.csv?id=' + sid, timeout=20).read().decode().strip().splitlines()[1:]
        return {a: float(b) for a, b in (l.split(',') for l in t) if b not in ('', '.')}
    except Exception: return {}
yi, yd = fred('IRLTLT01ITM156N'), fred('IRLTLT01DEM156N'); ds = sorted(set(yi) & set(yd))[-36:]
out['italia'] = {'titoli': it_rows, 'spread': {'d': ds, 'it': [yi[d] for d in ds], 'de': [yd[d] for d in ds], 'v': [round((yi[d] - yd[d]) * 100) for d in ds], 'fonte': 'OECD via FRED (IRLTLT01ITM156N, IRLTLT01DEM156N), media mensile'} if ds else None}
# v2.5.2: spread BTP-Bund giornaliero recente (Teleborsa su Borsa Italiana: "Spread Btp/Bund chiude a +N punti" e "BTP, rendimento X%"). L'OECD e' mensile e in ritardo di 2-3 mesi.
import re, os, html as _h
BI = 'https://www.borsaitaliana.it'
def _get(u):
    try: return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=25).read().decode('utf8', 'ignore')
    except Exception: return ''
def spread_recente():
    prec = {}
    try:
        old = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'indici.json')))['italia'].get('recente') or {}
        for d, v, b, u in zip(old.get('d', []), old.get('v', []), old.get('btp', []), old.get('url', [])): prec[d] = [v, b, u]
    except Exception: pass
    nuovi = {}
    for pg in range(1, 7):
        s = _get(BI + '/borsa/notizie/archivi/teleborsa.html?lang=it&page=%d' % pg)
        for u in re.findall(r'href="([^"]+_TLB[^"]*)"', s):
            m = re.search(r'/spread-btpbund-chiude[^/]*_(\d{4}-\d\d-\d\d)_TLB', u)
            if m and m.group(1) not in nuovi:
                t = _h.unescape(re.sub(r'<[^>]+>', ' ', _get(u if u.startswith('http') else BI + u)))
                k = re.search(r'Spread Btp/Bund chiude a \+?(-?\d+(?:[.,]\d+)?) punti', t)
                if k: nuovi[m.group(1)] = [float(k.group(1).replace(',', '.')), None, u.split('?')[0]]
            m2 = re.search(r'/btp-rendimento-(\d+)-alle-1800[^/]*_(\d{4}-\d\d-\d\d)_TLB', u)
            if m2: nuovi.setdefault(m2.group(2) + '#btp', float(m2.group(1)) / 100)
    for d in [k for k in nuovi if k.endswith('#btp')]:
        b = nuovi.pop(d); dd = d[:10]
        if dd in nuovi: nuovi[dd][1] = b
    prec.update({d: [v[0], v[1] if v[1] is not None else (prec.get(d) or [0, None])[1], v[2]] for d, v in nuovi.items()})
    ds = sorted(prec)[-60:]
    return {'d': ds, 'v': [prec[d][0] for d in ds], 'btp': [prec[d][1] for d in ds], 'url': [prec[d][2] for d in ds], 'fonte': 'Teleborsa su Borsa Italiana, chiusura giornaliera'} if ds else None
out['italia']['recente'] = spread_recente()
json.dump(out, open(sys.argv[1], 'w'), ensure_ascii=False, separators=(',', ':'))
print('INDICI: %d simboli su %d · Italia: %d titoli, spread %s' % (sum(len(x['righe']) for x in out['gruppi']), len(syms), len(it_rows), out['italia']['spread']['d'][-1] if out['italia']['spread'] else 'non disponibile'))
