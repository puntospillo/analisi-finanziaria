#!/usr/bin/env python3
"""Trasforma la pagina dell'artifact claude.ai nella versione statica per GitHub Pages.
Uso: python3 make_github.py <cartella_file_artifact> <cartella_repo>
Copia i file pubblicati e riscrive index.html: documento completo, bottoni che lanciano i compiti
di Claude nascosti, riga con date di aggiornamento e valutazione."""
import json, os, shutil, sys
src, dst = sys.argv[1], sys.argv[2]
FILES = ['logo-spillo.png', 'ifi_data.json', 'update_status.json', 'valutazione.json', 'valutazione_stato.json']
for f in FILES:
    if os.path.exists(os.path.join(src, f)): shutil.copy2(os.path.join(src, f), os.path.join(dst, f))
for d in ['archivio', 'code', 'cache']:
    if os.path.isdir(os.path.join(src, d)):
        os.makedirs(os.path.join(dst, d), exist_ok=True)
        for f in os.listdir(os.path.join(src, d)): shutil.copy2(os.path.join(src, d, f), os.path.join(dst, d, f))
html = open(os.path.join(src, 'index.html'), encoding='utf-8').read()
# l'artifact letto può contenere lo scheletro aggiunto da claude.ai: lo tolgo
if html.startswith('<!doctype html><html><head><meta charset=utf8>'):
    html = html[html.index('<body>') + 6:]
    if html.rstrip().endswith('</body></html>'): html = html.rstrip()[:-len('</body></html>')]
STATIC = """<style id="gh-static">
:root{box-sizing:border-box}html{scroll-padding-top:env(safe-area-inset-top,0px)}body{margin:0;padding:0}img{max-width:100%}
[hidden]:not([hidden=until-found i]){display:none!important}
.evprog{display:none!important}
#btnUpdate,#evRun,.ev-run,.ev-actions #evRun{display:none!important}
.gh-note{font-size:.76rem;color:var(--muted);margin:2px 0 0}
</style>
<script>window.GH_STATIC=true;</script>"""
NOTE = """<script>
(function(){function go(){var h=document.querySelector('.hdr');if(!h||document.getElementById('ghNote'))return;
var p=document.createElement('p');p.id='ghNote';p.className='gh-note';
p.textContent='Versione pubblica su GitHub: dati e valutazione si aggiornano su richiesta, elaborati con Claude e pubblicati qui. Il report PDF si crea nel browser.';
h.appendChild(p);var b=document.getElementById('btnEval');if(b){var l=b.querySelector('.blab');if(l)l.textContent='Valutazione';b.title='Mostra l\\'ultima valutazione salvata';}}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',go);else go();setTimeout(go,1500);})();
</script>"""
head = ('<!doctype html>\n<html lang="it">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
        '<link rel="icon" href="logo-spillo.png">\n' + STATIC + '\n</head>\n<body>\n')
open(os.path.join(dst, 'index.html'), 'w', encoding='utf-8').write(head + html + '\n' + NOTE + '\n</body>\n</html>\n')
open(os.path.join(dst, '.nojekyll'), 'w').close()
st = {}
try: st = json.load(open(os.path.join(src, 'update_status.json')))
except Exception: pass
print('ok', st)
