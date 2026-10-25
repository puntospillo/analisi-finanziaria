#!/usr/bin/env python3
"""
IFI — scarico diretto dei dati grezzi (senza browser).
Scrive in <progetto>/dati/raw:
  sp500_pit.csv         composizione storica S&P 500 (github fja05680)
  yahoo_prices.csv.gz   prezzi giornalieri dal 1996 (Yahoo Finance, aggiustati)
  cftc_tff.pack         CFTC Traders in Financial Futures (zip annuali)
  aaii_sentiment.xls    sondaggio AAII
  cape.html             CAPE di Shiller mensile (multpl.com)
  quote.json            ultima quotazione S&P 500 (anche a mercato aperto)
  fred.txt              serie FRED (solo se il sito risponde; altrimenti resta il file precedente)
Uso: python3 fetch_data.py <cartella progetto>
Aggiornamento incrementale: se in dati/raw c'è fattori_storico.csv (lo storico dell'ampiezza di mercato già calcolato,
salvato nell'artifact in cache/ampiezza_storico.csv), per i titoli scarica solo gli ultimi ~19 mesi (quanto basta per
ricalcolare medie a 200 giorni e massimi/minimi annuali) dei titoli presenti nell'indice in quel periodo; gli indici e
gli ETF di riferimento (pochi) si scaricano interi. Senza storico salvato scarica tutto dal 1996.
Solo libreria standard.
"""
import sys, os, io, json, gzip, time, datetime as dt, urllib.request, urllib.error, concurrent.futures as cf

ROOT = sys.argv[1] if len(sys.argv) > 1 else '.'
RAW = os.path.join(ROOT, 'dati', 'raw'); os.makedirs(RAW, exist_ok=True)
UA = {'User-Agent': 'Mozilla/5.0', 'Accept': '*/*'}   # Yahoo risponde 429 a user-agent "curl" o browser completi senza cookie
EXTRA = ['^GSPC', '^VIX', '^VIX3M', '^VIX9D', '^VVIX', 'RSP', 'SPY', '^SPXEW', 'HYG', 'LQD', 'IEF', 'TLT', 'SHY', 'JNK',
         '^TNX', '^IRX', '^FVX', '^TYX', '^MOVE', 'HG=F', 'GC=F', 'CL=F', '^DSPX', '^SKEW', 'QQQ', 'IWM', '^RUT', '^NDX',
         'XLU', 'XLP', 'XLY', 'XLK', 'XLF', 'XLI', 'XLV', 'KRE', '^NYA', '^DJI', '^IXIC', '^OEX', 'VWEHX', 'VFITX', 'VUSTX',
         'EURUSD=X', 'DX-Y.NYB', 'SI=F', 'BTC-USD', 'VGK', 'FXI', 'EWJ', 'EEM', 'ACWI', 'ACWX']
log = []
def say(*a):
    s = ' '.join(str(x) for x in a); print(s, flush=True); log.append(s)

def get(url, timeout=40, tries=3):
    last = None
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                return r.read()
        except Exception as e:
            last = e; time.sleep(1.5 * (k + 1))
    raise last

def atomic_write(name, data):
    p = os.path.join(RAW, name); tmp = p + '.tmp'
    with open(tmp, 'wb') as fh: fh.write(data)
    os.replace(tmp, p)

def fetch_pit():
    url = 'https://raw.githubusercontent.com/fja05680/sp500/master/S%26P%20500%20Historical%20Components%20%26%20Changes(Updated).csv'
    urls = [url.replace('Changes(Updated)', 'Changes%20(Updated)'), url]
    for u in urls:
        try:
            b = get(u)
            if b[:4] == b'date': atomic_write('sp500_pit.csv', b); say('OK  composizione storica', len(b), 'byte'); return b.decode()
        except Exception as e: pass
    say('ERR composizione storica: uso la copia precedente')
    return open(os.path.join(RAW, 'sp500_pit.csv')).read()

def fetch_yahoo(pit_text):
    tick = set()
    for line in pit_text.splitlines()[1:]:
        i = line.find(',')
        if i > 0 and line[:i] >= '1996-01-01':
            for t in line[i + 1:].replace('"', '').split(','):
                if t.strip(): tick.add(t.strip())
    try:
        cur = get('https://raw.githubusercontent.com/fja05680/sp500/master/sp500.csv').decode()
        for l in cur.splitlines()[1:]:
            t = l.split(',')[0].strip()
            if t: tick.add(t)
    except Exception: pass
    lst = list(dict.fromkeys(EXTRA + sorted(tick)))
    win = incremental_start()
    if win:
        # titoli nell'indice da win in poi (più quelli attuali): solo la finestra recente
        recent = set()
        for line in pit_text.splitlines()[1:]:
            i = line.find(',')
            if i > 0 and line[:i] >= win.strftime('%Y-%m-%d'):
                recent |= {t.strip() for t in line[i + 1:].replace('"', '').split(',') if t.strip()}
        recent |= current_members(pit_text)
        lst = list(dict.fromkeys(EXTRA + sorted(recent)))
        p1 = dt.datetime(win.year, win.month, win.day, tzinfo=dt.timezone.utc).timestamp()
        say(f'Aggiornamento incrementale: {len(recent)} titoli dal {win} (storico dell\'ampiezza già salvato), {len(EXTRA)} indicatori interi')
    else:
        p1 = None
    def one(t, p1=820454400):
        y = t.replace('.', '-')
        u = ('https://query1.finance.yahoo.com/v8/finance/chart/' + urllib.request.quote(y) +
             f'?period1={int(p1)}&period2=4102444800&interval=1d&events=split%2Cdiv')
        q = None
        for k in range(3):
            try:
                q = json.loads(get(u, timeout=30, tries=1))['chart']['result'][0]; break
            except urllib.error.HTTPError as e:
                if e.code == 404: return t, None
                time.sleep(3 * (k + 1))
            except Exception:
                time.sleep(2 * (k + 1))
        if q is None: return t, None
        ts = q.get('timestamp')
        if not ts: return t, None
        if t == '^GSPC':
            m = q.get('meta', {})
            atomic_write('quote.json', json.dumps({k: m.get(k) for k in ['regularMarketPrice', 'regularMarketTime', 'chartPreviousClose', 'previousClose', 'regularMarketDayHigh', 'regularMarketDayLow', 'currentTradingPeriod', 'exchangeTimezoneName']} | {'fetched_at': int(time.time())}).encode())
        qq = q['indicators']['quote'][0]; adj = (q['indicators'].get('adjclose') or [{}])[0].get('adjclose')
        out = []
        for k, s in enumerate(ts):
            d = dt.datetime.fromtimestamp(s, dt.timezone.utc).strftime('%Y%m%d')
            cl = qq['close'][k]; a = adj[k] if adj else cl
            f = (a / cl) if (cl and a) else 1.0
            h = qq['high'][k]; l = qq['low'][k]; v = qq['volume'][k] if t.startswith('^') else None   # volumi solo per gli indici
            g = lambda x: '' if x is None else ('%.6g' % x)
            out.append(f"{t},{d},{g(a)},{g(None if h is None else h * f)},{g(None if l is None else l * f)},{'' if v is None else v}\n")
        return t, ''.join(out)
    ok = 0; buf = io.StringIO(); buf.write('t,d,c,h,l,v\n'); missing = []
    with cf.ThreadPoolExecutor(6) as ex:
        for t, txt in ex.map(lambda t: one(t) if (p1 is None or t in EXTRA) else one(t, p1), lst):
            if txt: buf.write(txt); ok += 1
            else: missing.append(t)
    if '^GSPC' in missing: raise RuntimeError('S&P 500 non scaricato da Yahoo')
    atomic_write('yahoo_prices.csv.gz', gzip.compress(buf.getvalue().encode(), 6))
    say(f'OK  prezzi Yahoo: {ok}/{len(lst)} titoli (gli altri sono società uscite dalla borsa)')

def read_pack(path):
    b = open(path, 'rb').read(); nl = b.index(b'\n', 8); hdr = json.loads(b[8:nl]); pos = nl + 1; out = {}
    for name, size in hdr: out[name] = b[pos:pos + size]; pos += size
    return out

def fetch_cftc():
    y = dt.date.today().year
    urls = ['https://www.cftc.gov/files/dea/history/fin_fut_txt_2006_2016.zip'] + \
           [f'https://www.cftc.gov/files/dea/history/fut_fin_txt_{k}.zip' for k in range(2017, y + 1)]
    old = {}
    p = os.path.join(RAW, 'cftc_tff.pack')
    if os.path.exists(p):
        try: old = read_pack(p)
        except Exception: old = {}
    keep_upto = y - 1 if dt.date.today().month > 1 else y - 2      # gli anni chiusi non cambiano più
    hdr, blobs = [], []
    for u in urls:
        name = u.rsplit('/', 1)[1]; yr = int(name.rsplit('_', 1)[1][:4]) if name.startswith('fut_fin') else 2016
        if name in old and yr <= keep_upto:
            hdr.append([name, len(old[name])]); blobs.append(old[name]); continue
        try:
            b = get(u, timeout=60); hdr.append([u.rsplit('/', 1)[1], len(b)]); blobs.append(b)
        except Exception as e:
            say('WARN CFTC', u.rsplit('/', 1)[1], e)
    if not blobs: say('ERR CFTC: uso la copia precedente'); return
    atomic_write('cftc_tff.pack', b'IFIPACK\n' + json.dumps(hdr).encode() + b'\n' + b''.join(blobs))
    say('OK  CFTC', len(blobs), 'file')

def fetch_aaii():
    try:
        b = get('https://www.aaii.com/files/surveys/sentiment.xls', timeout=40)
        if b[:4] == b'\xd0\xcf\x11\xe0': atomic_write('aaii_sentiment.xls', b); say('OK  AAII'); return
        say('WARN AAII risposta non valida: uso la copia precedente')
    except Exception as e:
        say('WARN AAII non raggiungibile: uso la copia precedente', type(e).__name__)

def fetch_cape():
    try:
        b = get('https://www.multpl.com/shiller-pe/table/by-month', timeout=40)
        if b'datatable' in b: atomic_write('cape.html', b); say('OK  CAPE (multpl)'); return
        say('WARN CAPE risposta non valida')
    except Exception as e:
        say('WARN CAPE non raggiungibile', type(e).__name__)

def fetch_holdings():
    # composizione e pesi ufficiali dell'ETF SPY (State Street), aggiornati ogni giorno lavorativo
    try:
        b = get('https://www.ssga.com/us/en/intermediary/library-content/products/fund-data/etfs/us/holdings-daily-us-en-spy.xlsx', timeout=40)
        if b[:2] == b'PK': atomic_write('spy_holdings.xlsx', b); say('OK  pesi S&P 500 (SPY)'); return
        say('WARN pesi SPY risposta non valida')
    except Exception as e:
        say('WARN pesi SPY non raggiungibili', type(e).__name__)

def fetch_fred():
    ids = ['BAA10Y', 'AAA10Y', 'T10Y3M', 'T10Y2Y', 'NFCI', 'ANFCI', 'STLFSI4', 'BAMLH0A0HYM2', 'BAMLC0A0CM', 'DGS10', 'DTB3', 'VIXCLS']
    parts = []
    for i in ids:
        try:
            t = get('https://fred.stlouisfed.org/graph/fredgraph.csv?id=' + i, timeout=15, tries=1).decode()
            parts.append('#' + i + '\n' + t + '\n')
        except Exception as e:
            say('WARN FRED non raggiungibile da qui: resta la copia precedente (solo pannello di confronto)'); return
    atomic_write('fred.txt', ''.join(parts).encode()); say('OK  FRED')

def incremental_start():
    """data d'inizio della finestra recente, se esiste lo storico dell'ampiezza già calcolato"""
    p = os.path.join(RAW, 'fattori_storico.csv')
    if not os.path.exists(p): return None
    try:
        last = open(p).read().strip().splitlines()[-1].split(',')[0]
        return dt.date.fromisoformat(last[:10]) - dt.timedelta(days=560)
    except Exception:
        return None

def current_members(pit_text):
    last = pit_text.strip().splitlines()[-1]; i = last.find(',')
    out = {t.strip() for t in last[i + 1:].replace('"', '').split(',') if t.strip()}
    try:
        cur = get('https://raw.githubusercontent.com/fja05680/sp500/master/sp500.csv').decode()
        out |= {l.split(',')[0].strip() for l in cur.splitlines()[1:] if l.strip()}
    except Exception: pass
    return out

if __name__ == '__main__':
    t0 = time.time()
    pit = fetch_pit()
    fetch_yahoo(pit)
    fetch_cftc()
    fetch_aaii()
    fetch_cape()
    fetch_holdings()
    fetch_fred()
    say(f'Fine scarico in {time.time() - t0:.0f} s')
    open(os.path.join(ROOT, 'dati', 'ultimo_scarico.txt'), 'w').write(dt.datetime.now().isoformat() + '\n' + '\n'.join(log))
