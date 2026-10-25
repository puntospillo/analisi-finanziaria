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
#btnUpdate,#evRun,.ev-run{display:none!important}
.gh-note{font-size:.76rem;color:var(--muted);margin:2px 0 0}\n.gh-upd,.btn.gh-ev{box-sizing:border-box;display:inline-grid;gap:0;text-align:left;line-height:1.25;padding:6px 12px;border-radius:10px;font-size:.78rem}\n.gh-upd{background:var(--navy);color:#fff}\n.gh-upd .k,.gh-ev .k{font-size:.66rem;text-transform:uppercase;letter-spacing:.06em;font-weight:700;opacity:.9}\n.gh-upd b,.gh-ev b{font:700 .9rem var(--font-display)}\n.gh-upd .s,.gh-ev .s{font-size:.7rem;opacity:.85;font-weight:500}\n@media (max-width:560px){.hdr .upd{display:grid!important;grid-template-columns:1fr;gap:6px}.hdr .upd .btn,.hdr .gh-upd{width:100%}}
</style>
<script>window.GH_STATIC=true;</script>"""
NOTE = """<script>
(function(){
var MESI=['gen','feb','mar','apr','mag','giu','lug','ago','set','ott','nov','dic'];
function dt(x){if(!x)return '—';var d=new Date(x);if(isNaN(d))return '—';return d.getDate()+' '+MESI[d.getMonth()]+' '+d.getFullYear()+', '+String(d.getHours()).padStart(2,'0')+':'+String(d.getMinutes()).padStart(2,'0');}
function dd(x){if(!x)return '—';var p=String(x).slice(0,10).split('-');return +p[2]+' '+MESI[+p[1]-1]+' '+p[0];}
function j(u){return fetch(u+'?t='+Date.now(),{cache:'no-store'}).then(function(r){return r.ok?r.json():null}).catch(function(){return null});}
function go(){var h=document.querySelector('.hdr');if(!h||document.getElementById('ghNote'))return;
var p=document.createElement('p');p.id='ghNote';p.className='gh-note';
p.textContent='Versione pubblica su GitHub: dati e valutazione si aggiornano su richiesta (comandi \u201caggiorna ora\u201d e \u201cValutazione attuale\u201d dati a Claude) e vengono pubblicati qui. Il report PDF si crea nel browser.';
h.appendChild(p);
var up=document.getElementById('btnUpdate'),ev=document.getElementById('btnEval');
var bu=document.createElement('div');bu.className='gh-upd';bu.title='Ultimo aggiornamento dei dati di mercato (comando \u201caggiorna ora\u201d)';
bu.innerHTML='<span class="k">Aggiorna ora</span><b id="ghUpdAt">\u2026</b><span class="s" id="ghUpdSub"></span>';
if(up&&up.parentNode)up.parentNode.insertBefore(bu,up);
if(ev){ev.classList.add('gh-ev');ev.title='Apri l’ultima valutazione salvata (comando \u201cValutazione attuale\u201d)';ev.innerHTML='<span class="k">Valutazione attuale</span><b id="ghEvAt">\u2026</b><span class="s" id="ghEvSub">clicca per aprirla</span>';}
j('update_status.json').then(function(u){document.getElementById('ghUpdAt').textContent=u&&u.at?dt(u.at):'\u2014';document.getElementById('ghUpdSub').textContent=u&&u.as_of?'dati di mercato \u00b7 seduta del '+dd(u.as_of):'dati di mercato';});
Promise.all([j('valutazione_stato.json'),j('valutazione.json')]).then(function(r){var v=r[1],s=r[0];document.getElementById('ghEvAt').textContent=v&&v.at?dt(v.at):(s&&s.at?dt(s.at):'\u2014');if(v&&v.livello)document.getElementById('ghEvSub').textContent='ricerca su fonti esterne \u00b7 rischio '+v.livello+' \u00b7 clicca per aprirla';});
}
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
