#!/usr/bin/env python3
"""Contesto compatto per la valutazione: numeri della pagina + sintesi della valutazione precedente.
Uso: python3 tools/contesto.py   (stampa testo breve; salva /tmp/af_contesto.json)"""
import json, os, subprocess, sys, time
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(R + '/ifi_data.json')); c = d['cols']; rows = d['rows']
g = lambda k, i=-1: rows[i][c.index(k)]
N = {'as_of': d['as_of'], 'ifi': round(g('p_IFI')), 'ifi_4sett': round(g('p_IFI', -22)), 'frag': round(g('p_FRAG')), 'stress': round(g('p_STRS')),
     'spx': round(g('spx')), 'spx_vs_ma200_pct': round((g('spx') / g('ma200') - 1) * 100, 1), 'dal_massimo_pct': round(g('dd') * 100, 1),
     'titoli_sopra_ma200_pct': round(g('pct200')), 'vix': round(g('vix'), 1), 'ma200': round(g('ma200'))}
try:
    from playwright.sync_api import sync_playwright
    srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8779', '--directory', R], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
    try:
        with sync_playwright() as p:
            kw = {'executable_path': '/usr/bin/google-chrome'} if os.path.exists('/usr/bin/google-chrome') else {}
            b = p.chromium.launch(args=['--no-sandbox'], **kw); pg = b.new_page(); err = []
            pg.on('pageerror', lambda e: err.append(str(e)))
            pg.goto('http://localhost:8779/index.html'); pg.wait_for_function('window.AF2 && document.getElementById("stateChip")', timeout=30000); pg.wait_for_timeout(800)
            N.update(pg.evaluate("""(() => { const a = AF2(), i = a.N - 1, o = {quote_pct: {}}; for (const k in a.Q2) o.quote_pct[k] = Math.round(a.Q2[k].q[i] * 100);
              o.ifi = Math.round(a.IFI[i]); o.ifi_4sett = Math.round(a.IFI[Math.max(0, i - 21)]); o.quota_base_pct = Math.round(a.AV.q[i] * 100); o.stato = (document.getElementById('stateChip') || {}).textContent; o.versione = a.APP_VERSION; return o; })()"""))
            N['errori_pagina'] = err; b.close()
    finally: srv.terminate()
except Exception as e: N['nota'] = 'pagina non letta: ' + str(e)[:80]
if '--breve' in sys.argv:
    if N.get('nota') or N.get('errori_pagina'): print('ERRORE pagina:', N.get('nota') or N['errori_pagina']); sys.exit(1)
    print('PAGINA ok · dati al %s · indice di rischio %s (%s; 4 settimane fa %s) · fragilità %s, stress %s · S&P 500 %s, %+.1f%% sulla media a 200 giorni · quota in azioni: prudente %s%%, bilanciato %s%%, dinamico %s%%'
          % (N['as_of'], N['ifi'], N['stato'], N['ifi_4sett'], N['frag'], N['stress'], N['spx'], N['spx_vs_ma200_pct'], N['quote_pct'].get('prudente'), N['quote_pct'].get('bilanciato'), N['quote_pct'].get('dinamico')))
    sys.exit(0)
v = json.load(open(R + '/valutazione.json'))
P = {'del': v.get('at'), 'livello': v.get('livello'), 'titolo': v.get('titolo'), 'da_seguire': [m['cosa'] + ' → ' + m['soglia'] for m in v.get('monitorare', [])],
     'temi_senza_grafico': [t['titolo'] for t in v.get('report', {}).get('temi', []) if not t.get('grafico')],
     'idee': ['%s [%s, %s]' % (i.get('nome'), i.get('categoria'), i.get('direzione')) for i in v.get('idee', [])]}
json.dump({'numeri': N, 'precedente': P}, open('/tmp/af_contesto.json', 'w'), ensure_ascii=False)
print('NUMERI', json.dumps(N, ensure_ascii=False)); print('PRECEDENTE', json.dumps(P, ensure_ascii=False))
