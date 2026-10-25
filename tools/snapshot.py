#!/usr/bin/env python3
"""Calcola lo snapshot della dashboard (stesso contenuto inviato dal bottone "Valutazione attuale", impostazioni standard).
Uso: python3 snapshot.py <cartella con index.html statico e ifi_data.json> <rid> > snapshot.json"""
import asyncio, json, subprocess, sys, time, datetime as dt
from playwright.async_api import async_playwright
d, rid = sys.argv[1], sys.argv[2]
async def main():
    srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8779', '--directory', d], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch(); pg = await b.new_page(viewport={'width': 1366, 'height': 900})
            await pg.goto('http://localhost:8779/index.html')
            snap = None
            for _ in range(60):
                snap = await pg.evaluate('window.AF_SNAPSHOT ? window.AF_SNAPSHOT() : null')
                if snap: break
                await pg.wait_for_timeout(500)
            await b.close()
    finally: srv.terminate()
    if not snap: sys.exit('snapshot non disponibile')
    snap = {'rid': rid, **snap}
    print(json.dumps(snap, ensure_ascii=False))
asyncio.run(main())
