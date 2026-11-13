#!/usr/bin/env python3
"""Completa, controlla e salva la valutazione scritta da Claude. Uso: python3 tools/valutazione.py <nuova.json>
Aggiunge i campi automatici (rid, date, impostazioni, numeri della dashboard, elenco fonti), riusa le idee indicate con
{"riusa": "<nome>"}, controlla lo schema e, solo se tutto è a posto, scrive valutazione.json, valutazione_stato.json e
aggiunge le opportunità rischiose ad archivio/opportunita.json. Se qualcosa non va elenca gli errori e non scrive nulla."""
import json, os, sys, time, datetime as dt
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
n = json.load(open(sys.argv[1])); old = json.load(open(R + '/valutazione.json')); cx = json.load(open('/tmp/af_contesto.json'))['numeri']
E = []; req = lambda ok, m: ok or E.append(m)
for k in ['livello', 'titolo', 'in_breve', 'esterno', 'concordanza', 'monitorare', 'idee', 'report']: req(n.get(k), 'manca ' + k)
if E: print('ERRORI:', *E, sep='\n- '); sys.exit(1)
SEG = ('più rischio', 'neutro', 'meno rischio'); url = lambda u: isinstance(u, str) and u.startswith('http')
req(n['livello'] in ('basso', 'moderato', 'elevato', 'alto'), 'livello: basso | moderato | elevato | alto')
req(2 <= len(n['in_breve']) <= 3, 'in_breve: 2–3 punti')
for e in n['esterno']: req(e.get('tema') and e.get('lettura') and e.get('segno') in SEG and url(e.get('url')) and e.get('fonte') and e.get('data'), 'esterno incompleto: ' + str(e.get('tema')))
req(4 <= len(n['monitorare']) <= 6, 'monitorare: 4–6 voci')
for m in n['monitorare']:
    req(m.get('cosa') and m.get('perche') and m.get('soglia') and m.get('guardare'), 'monitorare incompleto: ' + str(m.get('cosa')))
    req(len(m.get('notizie') or []) >= 2, 'servono almeno 2 notizie per: ' + str(m.get('cosa')))
    for x in m.get('notizie') or []: req(x.get('testo') and (not x.get('fonte') or url(x.get('url'))), 'notizia senza testo o con fonte senza url: ' + str(m.get('cosa')))
prev = {i['nome']: i for i in old.get('idee', [])}; idee = []
for i in n['idee']:
    if 'riusa' in i:
        req(i['riusa'] in prev, 'idea da riusare non trovata: ' + str(i['riusa'])); idee.append({**prev.get(i['riusa'], {}), **{k: v for k, v in i.items() if k != 'riusa'}})
    else:
        for k in ['categoria', 'mercato', 'nome', 'direzione', 'tesi', 'perche_ora', 'rischi', 'orizzonte', 'fonte', 'url', 'data']: req(i.get(k), 'idea "%s": manca %s' % (i.get('nome'), k))
        idee.append(i)
req(8 <= len(idee) <= 24, 'idee: da 8 a 24')
for i in idee:
    req(i.get('direzione') in ('interessante', 'da evitare', 'opportunità rischiosa'), 'direzione non valida: ' + str(i.get('nome')))
    t = json.dumps(i, ensure_ascii=False).lower(); req(not any(w in t for w in ('compra ', 'vendi ', 'comprare', 'vendere subito')), 'idea con linguaggio compra/vendi: ' + str(i.get('nome')))
rp = n['report']
for k, a, b in [('precedente', 1, 4), ('cambiato', 3, 5), ('situazione', 3, 5)]: req(a <= len(rp.get(k) or []) <= b, 'report.%s: %d–%d voci' % (k, a, b))
gr = [t.get('grafico') for t in rp.get('temi', []) if t.get('grafico')]
req(gr == ['spx', 'ndx', 'ampiezza', 'vix', 'credito', 'settori'], 'report.temi: prima i sei temi con grafico, in ordine spx, ndx, ampiezza, vix, credito, settori')
for t in rp.get('temi', []): req(t.get('titolo') and t.get('testo') and t.get('segno') in SEG, 'tema incompleto: ' + str(t.get('titolo')))
if E: print('ERRORI:', *E, sep='\n- '); sys.exit(1)
now = dt.datetime.now(dt.timezone.utc); at = now.strftime('%Y-%m-%dT%H:%M:%SZ')
def b36(x):
    s = ''
    while x: s = '0123456789abcdefghijklmnopqrstuvwxyz'[x % 36] + s; x //= 36
    return s
rid = 'v' + b36(int(time.time() * 1000)); q = cx.get('quote_pct', {})
dash = ['Indice di rischio %s su 100 (%s); quattro settimane fa era %s. Fragilità %s, stress %s.' % (cx['ifi'], cx.get('stato', ''), cx['ifi_4sett'], cx['frag'], cx['stress']),
        'S&P 500 a %s: %+.1f%% rispetto alla media a 200 giorni (%s) e %+.1f%% dal massimo. Il %s%% dei titoli è sopra la propria media a 200 giorni. VIX %s.' % (cx['spx'], cx['spx_vs_ma200_pct'], cx['ma200'], cx['dal_massimo_pct'], cx['titoli_sopra_ma200_pct'], cx['vix']),
        'Quota in azioni indicata dal modello: prudente %s%%, bilanciato %s%%, dinamico %s%%, reattivo %s%% (modello di base del profilo Bilanciato %s%%).' % (q.get('prudente'), q.get('bilanciato'), q.get('dinamico'), q.get('reattivo'), cx.get('quota_base_pct'))]
fonti, seen = [], set()
def addf(nome, u, d):
    if url(u) and u not in seen: seen.add(u); fonti.append({'nome': nome or u, 'url': u, 'data': d or ''})
for e in n['esterno']: addf(e['fonte'], e['url'], e['data'])
for m in n['monitorare']:
    for x in m['notizie']: addf(x.get('fonte'), x.get('url'), x.get('data'))
for t in rp['temi']: addf(t.get('fonte'), t.get('url'), t.get('data'))
for i in idee: addf(i.get('fonte'), i.get('url'), i.get('data'))
out = {'rid': rid, 'state': 'ok', 'at': at, 'app_version': cx.get('versione', '2.0'), 'data_as_of': cx['as_of'], 'settings_key': old.get('settings_key'), 'settings_label': old.get('settings_label'),
       'livello': n['livello'], 'titolo': n['titolo'], 'in_breve': n['in_breve'], 'dashboard': dash, 'esterno': n['esterno'], 'concordanza': n['concordanza'], 'monitorare': n['monitorare'],
       'idee_premessa': n.get('idee_premessa') or old.get('idee_premessa'), 'idee': idee, 'limiti': n.get('limiti') or old.get('limiti'), 'fonti': fonti, 'report': rp, 'titoli_giorno': n.get('titoli_giorno') or old.get('titoli_giorno')}
json.dump(out, open(R + '/valutazione.json', 'w'), ensure_ascii=False, separators=(',', ':'))
json.dump({'rid': rid, 'state': 'ok', 'at': at}, open(R + '/valutazione_stato.json', 'w'))
op = [i for i in idee if i['direzione'] == 'opportunità rischiosa']; ap = R + '/archivio/opportunita.json'; A = json.load(open(ap)); day = at[:10]
A['voci'] = [v for v in A['voci'] if v.get('data') != day] + [{'data': day, 'rid': rid, 'livello': n['livello'], 'titolo': n['titolo'], 'opportunita': op}]
json.dump(A, open(ap, 'w'), ensure_ascii=False, separators=(',', ':'))
print('VALUTAZIONE salvata · %s · %d idee (%d opportunità rischiose) · %d fonti' % (n['livello'], len(idee), len(op), len(fonti)))
# prezzi di riferimento delle idee all'ultima chiusura (Yahoo Finance)
try:
    import subprocess; subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'code', 'prezzi_idee.py')], timeout=120)
except Exception as e: print('WARN prezzi idee non aggiornati:', e)
