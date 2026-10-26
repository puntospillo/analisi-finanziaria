#!/usr/bin/env python3
"""Trasforma la pagina dell'artifact claude.ai nella versione statica per GitHub Pages.
Uso: python3 make_github.py <cartella_file_artifact> <cartella_repo>
Copia i file pubblicati e riscrive index.html: documento completo, bottoni che lanciano i compiti
di Claude nascosti, riga con date di aggiornamento e valutazione."""
import json, os, shutil, sys
src, dst = sys.argv[1], sys.argv[2]
FILES = ['apple-touch-icon.png', 'logo-spillo.png', 'ifi_data.json', 'update_status.json', 'valutazione.json', 'valutazione_stato.json']
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
.hdr .upd{flex-wrap:nowrap}
.gh-note{font-size:.76rem;color:var(--muted);margin:2px 0 0}\n.hdr .upd{display:grid!important;grid-template-columns:minmax(0,2fr) minmax(0,1fr)!important;gap:8px;align-items:stretch;flex:1 1 560px!important;max-width:680px!important}
.hdr .upd .btn.gh-ev{box-sizing:border-box;display:grid;gap:1px;justify-content:stretch;align-content:center;text-align:left;line-height:1.25;padding:8px 12px;border-radius:10px;min-width:0;width:100%;white-space:nowrap;font-weight:500;grid-column:auto}
.gh-ev .k{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:.66rem;text-transform:uppercase;letter-spacing:.06em;font-weight:700;opacity:.9}
.gh-ev .l{font:700 .86rem var(--font-display);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;display:block;max-width:100%}
.gh-ev .s{font-size:.74rem;font-weight:600;text-decoration:underline;opacity:.95}
.hdr .upd #btnReport{width:100%;height:100%;justify-content:center;box-sizing:border-box}
@media (max-width:900px){.hdr .upd{max-width:none!important;flex-basis:100%!important}}
.ev-close-top{position:sticky;top:0;z-index:3;justify-self:end;margin:0;font-weight:700;background:var(--panel);box-shadow:0 2px 8px rgba(0,0,0,.12)}
</style>
<script>window.GH_STATIC=true;</script>"""
NOTE = """<script>
(function(){
var MESI=['gen','feb','mar','apr','mag','giu','lug','ago','set','ott','nov','dic'];
function dt(x){if(!x)return '—';var d=new Date(x);if(isNaN(d))return '—';return d.getDate()+' '+MESI[d.getMonth()]+' '+d.getFullYear()+', '+String(d.getHours()).padStart(2,'0')+':'+String(d.getMinutes()).padStart(2,'0');}
function sd(x){var d=new Date(x);if(isNaN(d))return '';return String(d.getDate()).padStart(2,'0')+'/'+String(d.getMonth()+1).padStart(2,'0')+' '+String(d.getHours()).padStart(2,'0')+':'+String(d.getMinutes()).padStart(2,'0');}
function dd(x){if(!x)return '—';var p=String(x).slice(0,10).split('-');return +p[2]+' '+MESI[+p[1]-1]+' '+p[0];}
function j(u){return fetch(u+'?t='+Date.now(),{cache:'no-store'}).then(function(r){return r.ok?r.json():null}).catch(function(){return null});}
function go(){var h=document.querySelector('.hdr');if(!h||document.getElementById('ghNote'))return;
var p=document.createElement('p');p.id='ghNote';p.className='gh-note';
p.textContent='Versione pubblica su GitHub: dati e valutazione si aggiornano su richiesta (comandi \u201caggiorna ora\u201d e \u201cValutazione attuale\u201d dati a Claude) e vengono pubblicati qui. Il report PDF si crea nel browser.';
h.appendChild(p);
var ev=document.getElementById('btnEval'),rp=document.getElementById('btnReport');
if(ev&&rp&&ev.nextSibling!==rp)ev.parentNode.insertBefore(ev,rp);
if(ev){ev.classList.add('gh-ev');ev.title='Apri l’ultima valutazione salvata';ev.innerHTML='<span class="k" id="ghEvK">Valutazione attuale</span><span class="l" id="ghEvL">…</span><span class="s">clicca qui</span>';}
var dlg=document.getElementById('evalDlg');if(dlg&&!document.getElementById('evCloseTop')){var c=document.createElement('button');c.type='button';c.className='btn ev-close-top';c.id='evCloseTop';c.textContent='Chiudi ✕';c.onclick=function(){dlg.close()};var hi=dlg.querySelector('.help-in');hi.insertBefore(c,hi.firstChild);}
j('valutazione.json').then(function(v){if(!v)return;document.getElementById('ghEvK').textContent='Valutazione attuale · '+sd(v.at);var t=(v.titolo||'').trim();document.getElementById('ghEvL').textContent=t||('Rischio '+(v.livello||'—'));document.getElementById('ghEvL').title=t;});
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',go);else go();setTimeout(go,1500);})();
</script>"""
head = ('<!doctype html>\n<html lang="it">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
        '<link rel="icon" href="logo-spillo.png">\n<link rel="apple-touch-icon" href="apple-touch-icon.png">\n<meta name="apple-mobile-web-app-title" content="Analisi Finanziaria">\n' + STATIC + '\n</head>\n<body>\n')
open(os.path.join(dst, 'index.html'), 'w', encoding='utf-8').write(head + html + '\n' + NOTE + '\n</body>\n</html>\n')
open(os.path.join(dst, '.nojekyll'), 'w').close()
st = {}
try: st = json.load(open(os.path.join(src, 'update_status.json')))
except Exception: pass
print('ok', st)
