#!/usr/bin/env python3
"""Unisce le nuove notizie (per fonte) in notizie.json e tiene 365 giorni.
Uso: python3 tools/notizie.py /tmp/notizie_nuove.json
Ogni voce: {fonte: milanofinanza|scenarieconomici|zerohedge|web, titolo, sintesi (italiano, parafrasi), url, data (YYYY-MM-DD o null), tema, abbonamento (true se a pagamento: senza link), sito (solo per web)}"""
import json, sys, datetime as dt
F = 'notizie.json'; FONTI = {'milanofinanza', 'scenarieconomici', 'zerohedge', 'web'}; oggi = dt.date.today().isoformat()
try: arc = json.load(open(F))
except Exception: arc = {'voci': []}
nuove = json.load(open(sys.argv[1])); noti = {v['url'] + '|' + v['titolo'] for v in arc['voci']}
agg = (max([v['agg'] for v in arc['voci']] or [0]) + 1); n = 0
for v in nuove:
    if v.get('fonte') not in FONTI or not v.get('titolo') or not v.get('sintesi'): continue
    if (v.get('url', '') + '|' + v['titolo']) in noti: continue
    v['agg'] = agg; v['visto'] = oggi; arc['voci'].append(v); n += 1
lim = (dt.date.today() - dt.timedelta(days=365)).isoformat()
arc['voci'] = [v for v in arc['voci'] if v['visto'] >= lim]
arc['aggiornato'] = oggi; arc['ultimo_agg'] = agg if n else max([v['agg'] for v in arc['voci']] or [0])
json.dump(arc, open(F, 'w'), ensure_ascii=False, indent=1); print('aggiunte', n, 'totale', len(arc['voci']))
