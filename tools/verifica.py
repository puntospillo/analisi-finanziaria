#!/usr/bin/env python3
"""Controllo interno dei dati esposti dopo un aggiornamento (regola di Maurizio, 20/11/2026).
Uso: python3 tools/verifica.py  -> stampa OK/ATTENZIONE per ogni controllo; esce con 1 se c'è un errore.
Il confronto con fonti esterne (S&P 500, Nasdaq 100/QQQ, VIX, rendimento 10 anni) si fa a parte con WebSearch."""
import json, re, sys, datetime as dt
R = __file__.rsplit('/tools/', 1)[0]
J = lambda f: json.load(open(f'{R}/{f}'))
d, x, u, v, n = J('ifi_data.json'), J('extra_data.json'), J('update_status.json'), J('valutazione.json'), J('notizie.json')
ix = {k: i for i, k in enumerate(d['cols'])}; row = d['rows'][-1]; g = lambda k, j=-1: d['rows'][j][ix[k]]
err = []; warn = []
def chk(c, ok, msg, fatal=True):
    print(('OK        ' if ok else ('ERRORE    ' if fatal else 'ATTENZIONE ')) + c + (('' if ok else ': ' + msg)))
    if not ok: (err if fatal else warn).append(c)
a = d['as_of']; today = dt.date.today().isoformat()
chk('date coerenti', d['dates'][-1] == a == x['dates'][-1] == u['as_of'], f"ifi {d['dates'][-1]} as_of {a} extra {x['dates'][-1]} status {u['as_of']}")
chk('data non futura', a <= today, f'{a} > {today}')
chk('ritardo dati', (dt.date.fromisoformat(today) - dt.date.fromisoformat(a)).days <= 4, f'dati al {a}, oggi {today}', False)
sp = g('spx'); q = d['quote']
chk('S&P = quotazione', abs(sp - q['regularMarketPrice']) < 0.01, f"{sp} contro {q['regularMarketPrice']}")
chk('variazione giorno', abs((sp / q['prev_close'] - 1) - (sp / g('spx', -2) - 1)) < 0.0005, 'prev_close diverso dalla chiusura precedente')
pk = max(r[ix['spx']] for r in d['rows'][-300:]); chk('distanza dal massimo', abs((sp / pk - 1) - g('dd')) < 0.0005, f"{sp/pk-1:.4f} contro {g('dd')}")
chk('media 200 giorni', abs(g('ma200') - sum(r[ix['spx']] for r in d['rows'][-200:]) / 200) < 1.5, 'ma200 non coincide con la media dei prezzi')
chk('percentili 0-100', all(0 <= g(k) <= 100 for k in ('p_IFI', 'p_FRAG', 'p_STRS')), 'fuori scala')
chk('salto giornaliero S&P', abs(sp / g('spx', -2) - 1) < 0.08, 'oltre 8% in un giorno: dato sospetto')
for k in ('vix', 'hy_oas', 'baa', 'cape', 'move'):
    same = sum(1 for j in (-2, -3) if g(k, j) == g(k))
    chk(f'serie {k} aggiornata', same < 2, 'uguale da 3 giorni (probabile serie ferma)', False)
chk('valutazione allineata', v.get('data_as_of') == a, f"valutazione {v.get('data_as_of')} contro dati {a}", False)
txt = json.dumps(v, ensure_ascii=False)
m = re.search(r'S&P 500 a ([\d.,]+)', ' '.join(v.get('dashboard', [])))
if m: chk('S&P nella valutazione', abs(float(m.group(1).replace('.', '').replace(',', '.')) - sp) < 1, f'{m.group(1)} contro {sp}')
m = re.search(r'VIX (\d+[.,]?\d*)', ' '.join(v.get('dashboard', [])))
if m: chk('VIX nella valutazione', abs(float(m.group(1).replace(',', '.')) - g('vix')) < 0.1, f"{m.group(1)} contro {g('vix')}")
m = re.search(r'Il (\d+)% dei titoli', ' '.join(v.get('dashboard', [])))
if m: chk('titoli sopra media 200', abs(int(m.group(1)) - g('pct200')) < 1, f"{m.group(1)} contro {g('pct200'):.1f}")
fut = [t['titolo'] for t in n['voci'] if (t.get('data') or '') > today]
chk('notizie senza date future', not fut, str(fut[:2]))
chk('notizie aggiornate', n['aggiornato'] == a or n['aggiornato'] >= a, f"notizie al {n['aggiornato']}, dati {a}", False)
print('\nESITO:', 'ERRORI ' + ', '.join(err) if err else 'nessun errore' + (' · da guardare: ' + ', '.join(warn) if warn else ''))
print('Da fare a mano: confronto con fonti esterne (S&P 500, Nasdaq 100, VIX, 10 anni) e controllo di testi/etichette nuove.')
sys.exit(1 if err else 0)
