#!/usr/bin/env python3
"""Dopo il calcolo: controlla i nuovi dati, li copia nel repository, archivia il report se è cambiato il mese,
scrive update_status.json e stampa il riepilogo. Uso: dopo_dati.py <cartella lavoro> <repo>"""
import json, os, shutil, sys, datetime as dt
W, R = sys.argv[1], sys.argv[2]
new = json.load(open(W + '/dati/ifi_data.json')); old = json.load(open(R + '/ifi_data.json'))
assert new['as_of'] >= old['as_of'], 'dati nuovi più vecchi di quelli pubblicati'
assert len(new['rows']) >= len(old['rows']) and new['cols'] == old['cols'], 'struttura dei dati cambiata'
ex = json.load(open(W + '/extra_data.json')); assert ex.get('as_of') == new['as_of'], 'serie aggiuntive non allineate'
shutil.copy2(W + '/dati/ifi_data.json', R + '/ifi_data.json'); shutil.copy2(W + '/extra_data.json', R + '/extra_data.json')
shutil.copy2(W + '/dati/cache/ampiezza_storico.csv', R + '/cache/ampiezza_storico.csv')
for f in ('aaii_sentiment.xls', 'cape.html'):
    if os.path.exists(W + '/dati/raw/' + f): shutil.copy2(W + '/dati/raw/' + f, R + '/cache/' + f)
if os.path.getsize(W + '/dati/raw/fred.txt') > 1000: shutil.copy2(W + '/dati/raw/fred.txt', R + '/code/fred_cache.txt')
now = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
m = new.get('monthly') or {}; ip = R + '/archivio/indice.json'; idx = json.load(open(ip)); msg = ''
if False and m.get('month_key') and m['month_key'] not in [r['key'] for r in idx['reports']]:
    json.dump({**m, 'archivio': {'ricostruito': False, 'salvato': now}}, open(R + '/archivio/%s.json' % m['month_key'], 'w'), ensure_ascii=False, separators=(',', ':'))
    idx['reports'].append({'key': m['month_key'], 'month': m.get('month'), 'overall': m.get('overall'), 'end': m.get('end'), 'ricostruito': False})
    json.dump(idx, open(ip, 'w'), ensure_ascii=False, separators=(',', ':')); msg = ' · archiviato il report di ' + str(m.get('month'))
json.dump({'at': now, 'state': 'ok', 'as_of': new['as_of']}, open(R + '/update_status.json', 'w'))
print('DATI calcolati al ' + new['as_of'] + msg)
