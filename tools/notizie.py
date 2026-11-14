#!/usr/bin/env python3
"""Unisce le nuove notizie (per fonte) in notizie.json e tiene 365 giorni.
Uso: python3 tools/notizie.py /tmp/notizie_nuove.json
Ogni voce: {fonte: milanofinanza|scenarieconomici|zerohedge|web, titolo, sintesi (italiano, parafrasi), url, data (YYYY-MM-DD o null), tema, abbonamento (true se a pagamento: senza link), sito (solo per web), arretrato (true = notizia già vecchia: non «nuova», visto = data)}
Le voci senza «arretrato» sono le «nuove» dell'aggiornamento (agg = max+1)."""
import json, sys, datetime as dt
F = 'notizie.json'; FONTI = {'milanofinanza', 'scenarieconomici', 'zerohedge', 'web'}; oggi = dt.date.today().isoformat()
try: arc = json.load(open(F))
except Exception: arc = {'voci': []}
nuove = json.load(open(sys.argv[1])); noti = {v['url'] + '|' + v['titolo'] for v in arc['voci']}
agg = (max([v['agg'] for v in arc['voci']] or [0]) + 1); n = 0; k = 0
for v in nuove:
    if v.get('fonte') not in FONTI or not v.get('titolo') or not v.get('sintesi'): continue
    if (v.get('url', '') + '|' + v['titolo']) in noti: continue
    if v.pop('arretrato', False): v['agg'] = 0; v['visto'] = v.get('data') or oggi; k += 1
    else: v['agg'] = agg; v['visto'] = oggi; n += 1
    arc['voci'].append(v); noti.add(v.get('url', '') + '|' + v['titolo'])
lim = (dt.date.today() - dt.timedelta(days=365)).isoformat()
arc['voci'] = [v for v in arc['voci'] if v['visto'] >= lim]
arc['aggiornato'] = oggi; arc['ultimo_agg'] = agg if n else max([v['agg'] for v in arc['voci']] or [0])
json.dump(arc, open(F, 'w'), ensure_ascii=False, indent=1); from collections import Counter; c = Counter(v['fonte'] for v in arc['voci'] if v['agg'] == arc['ultimo_agg'])
print('nuove', n, 'arretrate', k, 'totale', len(arc['voci']), '| nuove per fonte:', dict(c))
