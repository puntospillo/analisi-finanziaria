#!/usr/bin/env python3
"""
IFI Market Risk Lab — pipeline di calcolo.

Legge i file grezzi scaricati dal browser (cartella dati/raw), calcola i fattori
point-in-time, gli score (percentili su finestra mobile di 5 anni, solo dati passati),
le statistiche di backtest e scrive:
  dati/ifi_data.json   -> dati per la dashboard
  dati/ifi_serie.csv   -> serie giornaliera completa
  dati/ifi_report.txt  -> riepilogo testuale

Uso:  python3 ifi_pipeline.py <cartella_progetto>
Compatibile con pandas 2.x e 3.x. Nessuna dipendenza oltre numpy/pandas (+xlrd per AAII).
"""
import sys, os, io, json, zipfile, datetime as dt
import numpy as np, pandas as pd

ROOT = sys.argv[1] if len(sys.argv) > 1 else '.'
PARTIAL = None
C_ALL = None
RAW = os.path.join(ROOT, 'dati', 'raw')
OUT = os.path.join(ROOT, 'dati')
MODEL_VERSION = 'ifi-1.2 (2026-10-24)'

# ----------------------------------------------------------------------------- utils
def read_pack(path):
    """Formato IFIPACK: 'IFIPACK\\n' + json [[nome,size],...] + '\\n' + byte concatenati."""
    b = open(path, 'rb').read()
    assert b.startswith(b'IFIPACK\n'), path
    nl = b.index(b'\n', 8); hdr = json.loads(b[8:nl]); pos = nl + 1; out = {}
    for name, size in hdr:
        out[name] = b[pos:pos + size]; pos += size
    return out

def ppct(s, minp=756, win=1260):
    """Percentile point-in-time del valore di oggi rispetto agli ultimi `win` giorni (>= minp)."""
    a = s.to_numpy(dtype=float); out = np.full(len(a), np.nan)
    for i in range(len(a)):
        if np.isnan(a[i]): continue
        h = a[max(0, i - win):i + 1]; h = h[~np.isnan(h)]
        if len(h) < minp: continue
        out[i] = (h < a[i]).mean() * 100 + (h == a[i]).mean() * 50
    return pd.Series(out, index=s.index)

def auc(x, y):
    m = x.notna() & y.notna(); x = x[m]; y = y[m]
    n1 = y.sum(); n0 = len(y) - n1
    if n1 == 0 or n0 == 0: return np.nan
    r = x.rank()
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))

# ----------------------------------------------------------------------------- load
def load_prices():
    p = os.path.join(RAW, 'yahoo_prices.csv.gz')
    if not os.path.exists(p):  # nome della prima estrazione
        p = os.path.join(RAW, 'ifi_prices_1996_2026.csv.gz')
    d = pd.read_csv(p, dtype={'t': str})
    d['d'] = pd.to_datetime(d['d'].astype(str), format='%Y%m%d')
    return d

def load_membership():
    pit = pd.read_csv(os.path.join(RAW, 'sp500_pit.csv'))
    pit['date'] = pd.to_datetime(pit['date']); pit = pit.sort_values('date')
    iv = {}; prev = set()
    for d, t in zip(pit['date'], pit['tickers']):
        s = set(str(t).split(','))
        for x in s - prev: iv.setdefault(x, []).append([d, None])
        for x in prev - s: iv[x][-1][1] = d
        prev = s
    expected = pit.set_index('date')['tickers'].str.count(',') + 1
    return iv, expected

def load_fred():
    p = os.path.join(RAW, 'fred.txt')
    if not os.path.exists(p): p = os.path.join(RAW, 'ifi_fred.txt')
    if not os.path.exists(p): return {}
    txt = open(p).read()
    out = {}
    for block in txt.split('#')[1:]:
        name, body = block.split('\n', 1)
        df = pd.read_csv(io.StringIO(body))
        if df.shape[1] < 2: continue
        s = pd.to_numeric(df.iloc[:, 1], errors='coerce'); s.index = pd.to_datetime(df.iloc[:, 0])
        out[name.strip()] = s.dropna()
    return out

def load_cftc():
    p = os.path.join(RAW, 'cftc_tff.pack')
    if not os.path.exists(p): return None
    frames = []
    for name, blob in read_pack(p).items():
        z = zipfile.ZipFile(io.BytesIO(blob))
        for n in z.namelist():
            frames.append(pd.read_csv(z.open(n), low_memory=False))
    d = pd.concat(frames, ignore_index=True)
    d = d[d['CFTC_Contract_Market_Code'].astype(str).str.strip() == '13874A'].copy()   # E-mini S&P 500
    d['date'] = pd.to_datetime(d['Report_Date_as_YYYY-MM-DD'].astype(str).str.strip(), format='mixed')
    d = d.drop_duplicates('date').sort_values('date').set_index('date')
    oi = d['Open_Interest_All'].astype(float)
    am = (d['Asset_Mgr_Positions_Long_All'] - d['Asset_Mgr_Positions_Short_All']) / oi * 100
    lev = (d['Lev_Money_Positions_Long_All'] - d['Lev_Money_Positions_Short_All']) / oi * 100
    deal = (d['Dealer_Positions_Long_All'] - d['Dealer_Positions_Short_All']) / oi * 100
    out = pd.DataFrame({'cot_am': am, 'cot_lev': lev, 'cot_dealer': deal})
    out.index = out.index + pd.Timedelta(days=3)       # posizioni del martedì, pubblicate il venerdì
    return out

def load_cape():
    """Shiller CAPE mensile da multpl.com (cape.html). Valore del mese M usato dal primo giorno del mese M+1;
    la riga del mese in corso (data di oggi) vale dal giorno stesso."""
    p = os.path.join(RAW, 'cape.html')
    if not os.path.exists(p): return None
    import re
    h = open(p, encoding='utf-8', errors='ignore').read()
    rows = re.findall(r'<td>([A-Z][a-z]{2} \d{1,2}, \d{4})</td>\s*<td>\s*(?:&#x2002;)?\s*([\d.]+)', h)
    if not rows: return None
    s = pd.Series({pd.to_datetime(a, format='%b %d, %Y'): float(b) for a, b in rows}).sort_index()
    idx = [d + pd.offsets.MonthBegin(1) if d.day == 1 else d for d in s.index]
    s.index = pd.DatetimeIndex(idx); s = s[~s.index.duplicated(keep='last')].sort_index()
    return s.rename('cape')

def load_aaii():
    p = os.path.join(RAW, 'aaii_sentiment.xls')
    if not os.path.exists(p): return None
    try:
        x = pd.read_excel(p, header=None)
    except Exception:
        return None
    x = x.iloc[5:, [0, 1, 3]]; x.columns = ['d', 'bull', 'bear']
    x['d'] = pd.to_datetime(x['d'], errors='coerce'); x = x.dropna()
    x = x.set_index('d').astype(float)
    s = (x['bull'] - x['bear']) * 100
    s.index = s.index + pd.Timedelta(days=1)            # pubblicato giovedì, usato dal giorno dopo
    return s.rename('aaii_spread')

# ----------------------------------------------------------------------------- factors
def build():
    d = load_prices()
    iv, expected = load_membership()
    spx_raw = d[d['t'] == '^GSPC'].set_index('d')['c']
    # seduta in corso: la si tiene (dato provvisorio) e la si segnala; usa quote.json scritto dal downloader
    global PARTIAL
    PARTIAL = None
    last = spx_raw.index.max()
    qp = os.path.join(RAW, 'quote.json')
    if os.path.exists(qp):
        try:
            q = json.load(open(qp))
            rmt = q.get('regularMarketTime'); end = (q.get('currentTradingPeriod') or {}).get('regular', {}).get('end')
            fetched = q.get('fetched_at')
            if rmt and end and fetched and fetched < end and dt.datetime.fromtimestamp(rmt, dt.timezone.utc).date() == last.date():
                PARTIAL = {'date': last.strftime('%Y-%m-%d'), 'quote_time': dt.datetime.fromtimestamp(rmt, dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}
        except Exception:
            PARTIAL = None
    else:
        vol_last = d[(d['t'] == '^GSPC') & (d['d'] == last)]['v']
        if len(vol_last) and float(vol_last.iloc[0]) < 0.6 * float(d[(d['t'] == '^GSPC')]['v'].tail(20).median()):
            d = d[d['d'] < last]
    dates = pd.DatetimeIndex(sorted(d.loc[d['t'] == '^GSPC', 'd'].unique()))
    wide = lambda col: d.pivot_table(index='d', columns='t', values=col, aggfunc='last').reindex(dates)
    C, H, L, V = wide('c'), wide('h'), wide('l'), wide('v')
    H, L, V = H.reindex(columns=C.columns), L.reindex(columns=C.columns), V.reindex(columns=C.columns)   # i volumi sono salvati solo per gli indici
    global C_ALL
    C_ALL = C

    stocks = [t for t in C.columns if t in iv]
    extras = [t for t in C.columns if t not in iv]
    X = C[extras].copy()
    C, H, L, V = C[stocks], H[stocks], L[stocks], V[stocks]
    mem = pd.DataFrame(False, index=dates, columns=stocks)
    first = C.apply(lambda s: s.first_valid_index())
    # finestra recente (aggiornamento incrementale): i prezzi dei titoli partono da wstart invece che dal 1996
    wstart = first.dropna().min() if first.notna().any() else dates[0]
    for t in stocks:
        for s, e in iv[t]:
            # simboli riutilizzati: accetta il dato solo se lo storico Yahoo copre l'inizio dell'appartenenza
            if first[t] is None or pd.isna(first[t]) or first[t] > max(s, wstart) + pd.Timedelta(days=30): continue
            m = (dates >= s) & ((dates < e) if e is not None else True)
            mem.loc[m, t] = True
    valid = mem & C.notna()
    R = C.pct_change(fill_method=None); R = R.where(R.abs() < 0.9)
    nh = C.notna().rolling(252, min_periods=1).sum()
    h252 = H.shift(1).rolling(251, min_periods=240).max(); l252 = L.shift(1).rolling(251, min_periods=240).min()
    ok = valid & (nh >= 250)
    N = ok.sum(axis=1)
    F = pd.DataFrame(index=dates)
    F['N'] = valid.sum(axis=1)
    F['coverage'] = (F['N'] / expected.reindex(dates, method='ffill') * 100).clip(upper=100)
    F['nh'] = ((H >= h252) & ok).sum(axis=1) / N * 100
    F['nl'] = ((L <= l252) & ok).sum(axis=1) / N * 100
    ma200 = C.rolling(200, min_periods=190).mean(); v200 = valid & ma200.notna()
    ma50 = C.rolling(50, min_periods=45).mean(); v50 = valid & ma50.notna()
    F['pct200'] = ((C > ma200) & v200).sum(axis=1) / v200.sum(axis=1) * 100
    F['pct50'] = ((C > ma50) & v50).sum(axis=1) / v50.sum(axis=1) * 100
    Rm = R.where(valid & R.notna())
    F['ew_ret'] = Rm.mean(axis=1)
    hh = C.rolling(252, min_periods=200).max(); vh = valid & hh.notna()
    F['near_hi'] = ((C >= 0.9 * hh) & vh).sum(axis=1) / vh.sum(axis=1) * 100
    vr = valid & R.notna()
    F['adv'] = ((R > 0) & vr).sum(axis=1) / vr.sum(axis=1) * 100
    var_i = Rm.rolling(63, min_periods=50).var().where(valid)
    sd = np.sqrt(var_i); n = sd.notna().sum(axis=1)
    F['corr63'] = (F['ew_ret'].rolling(63).var() * n ** 2 - var_i.sum(axis=1)) / (sd.sum(axis=1) ** 2 - var_i.sum(axis=1))
    F['disp21'] = C.pct_change(21, fill_method=None).where(valid).std(axis=1) * 100
    # --- storico dell'ampiezza: se i titoli coprono solo la finestra recente, prima del punto di giunzione
    #     si usano i valori già calcolati e salvati (cache/ampiezza_storico.csv)
    BCOLS = ['N', 'coverage', 'nh', 'nl', 'pct200', 'pct50', 'ew_ret', 'near_hi', 'adv', 'corr63', 'disp21']
    cpath = os.path.join(RAW, 'fattori_storico.csv')
    if wstart > dates[0] + pd.Timedelta(days=400):
        if not os.path.exists(cpath): raise RuntimeError('prezzi solo recenti ma manca lo storico dell\'ampiezza')
        Fc = pd.read_csv(cpath, index_col=0, parse_dates=True)
        k0 = dates.searchsorted(wstart) + 300                     # 300 sedute di rodaggio per medie e massimi annuali
        splice = dates[min(k0, len(dates) - 1)]
        if Fc.index.max() < splice: raise RuntimeError('storico dell\'ampiezza troppo vecchio rispetto alla finestra scaricata')
        old = dates < splice
        for c in BCOLS: F.loc[old, c] = Fc[c].reindex(dates[old]).values
        print(f'Ampiezza: storico salvato fino al {splice.date()}, ricalcolata dopo (finestra dal {wstart.date()})')
    os.makedirs(os.path.join(ROOT, 'dati', 'cache'), exist_ok=True)
    F[BCOLS].to_csv(os.path.join(ROOT, 'dati', 'cache', 'ampiezza_storico.csv'), float_format='%.6g', date_format='%Y-%m-%d')
    for k, t in {'spx': '^GSPC', 'vix': '^VIX', 'vix3m': '^VIX3M', 'move': '^MOVE', 'rut': '^RUT',
                 'tnx': '^TNX', 'irx': '^IRX', 'hyg': 'HYG', 'ief': 'IEF', 'rsp': 'RSP', 'dspx': '^DSPX',
                 'vwehx': 'VWEHX', 'vfitx': 'VFITX'}.items():
        F[k] = X[t] if t in X.columns else np.nan
    F['ew_idx'] = (1 + F['ew_ret'].fillna(0)).cumprod()

    f = pd.DataFrame(index=dates)
    spx = F['spx']
    f['spx'] = spx
    f['coverage'] = F['coverage']
    f['dd'] = spx / spx.cummax() - 1
    # --- fragilità (struttura interna)
    f['ewcap63'] = (F['ew_idx'].pct_change(63) - spx.pct_change(63)) * 100
    f['pct200'] = F['pct200']
    f['nl10'] = F['nl'].rolling(10).mean()
    f['nh10'] = F['nh'].rolling(10).mean()
    f['near_hi'] = F['near_hi']
    f['rut63'] = (F['rut'].pct_change(63) - spx.pct_change(63)) * 100
    f['pct50'] = F['pct50']
    f['adv21'] = F['adv'].rolling(21).mean()
    f['corr63'] = F['corr63']; f['disp21'] = F['disp21']
    # --- stress
    f['rv21'] = np.log(spx).diff().rolling(21).std() * np.sqrt(252) * 100
    f['vix'] = F['vix']
    f['ts'] = F['vix'] / F['vix3m']
    f['move'] = F['move']
    f['tnx63'] = F['tnx'].diff(63)
    fred = load_fred()
    def fr(k, lag=0):
        if k not in fred: return pd.Series(np.nan, index=dates)
        s = fred[k].copy(); s.index = s.index + pd.Timedelta(days=lag)
        return s.reindex(dates.union(s.index)).ffill().reindex(dates)
    baa = fr('BAA10Y')
    f['baa'] = baa
    f['baa63'] = baa.diff(63)
    # credito da Yahoo (sempre disponibile): fondo high yield Vanguard VWEHX vs Treasury intermedi VFITX, dal 1996
    # i fondi comunicano il NAV dopo la chiusura: durante la seduta si usa l'ultimo disponibile
    f['hy63'] = ((np.log(F['vwehx'] / F['vfitx']).diff(63)) * 100).ffill(limit=3)
    # curva da Yahoo: rendimento 10 anni meno T-bill 3 mesi
    f['curve'] = F['tnx'] - F['irx']
    f['nfci'] = fr('NFCI', lag=5)        # settimana chiusa venerdì, pubblicato mercoledì
    f['hy_oas'] = fr('BAMLH0A0HYM2')     # solo ultimi 3 anni su FRED: solo visualizzazione
    f['cred63'] = np.log(F['hyg'] / F['ief']).diff(63) * 100
    # --- pannello conferma (non nell'indice)
    cot = load_cftc()
    if cot is not None:
        for c in cot.columns:
            f[c] = cot[c].reindex(dates.union(cot.index)).ffill().reindex(dates)
    cp = load_cape()
    if cp is not None:
        f['cape'] = cp.reindex(dates.union(cp.index)).ffill().reindex(dates)
    aa = load_aaii()
    if aa is not None:
        f['aaii'] = aa.reindex(dates.union(aa.index)).ffill().reindex(dates)
        f['aaii8'] = aa.rolling(8).mean().reindex(dates.union(aa.index)).ffill().reindex(dates)
    # --- segnale "spaccatura": indice entro 5% dal massimo,
    #     nuovi minimi > 2x nuovi massimi e >= 4% dei titoli, almeno 2 giorni in 21 sedute
    nlc = F['nl']; nhc = F['nh']
    raw = (f['dd'] >= -0.05) & (nlc > 2 * nhc) & (nlc >= 4)
    f['split_raw'] = raw.astype(float)
    f['split'] = (raw.astype(float).rolling(21).sum() >= 2).astype(float)
    f['nl'] = nlc; f['nh'] = nhc
    f['ma200'] = spx.rolling(200).mean()
    f['trend_down'] = (spx < f['ma200']).astype(float)
    # --- target (solo per statistiche storiche)
    fwd60 = pd.concat([spx.shift(-k) for k in range(1, 61)], axis=1).min(axis=1)
    f['fdd60'] = fwd60 / spx - 1
    f['y10_60'] = (f['fdd60'] <= -0.10).astype(float)
    f.loc[spx.shift(-60).isna(), ['y10_60', 'fdd60']] = np.nan
    f['cash'] = (F['irx'] / 100 / 252).ffill().fillna(0)
    return f

# definizione dei fattori nel modello: (colonna, direzione, gruppo, nome, descrizione)
FACTORS = [
    ('ewcap63', -1, 'FRAG', 'Peso uguale vs indice (63 sedute)', 'Rendimento medio dei titoli S&P 500 meno rendimento dell\'indice: negativo = rialzo trainato da pochi grandi titoli'),
    ('pct200', -1, 'FRAG', '% titoli sopra media 200 giorni', 'Quota dei componenti in trend rialzista di lungo periodo'),
    ('nl10', 1, 'FRAG', 'Nuovi minimi 52 settimane (media 10g)', '% dei componenti che toccano il minimo dell\'ultimo anno'),
    ('near_hi', -1, 'FRAG', '% titoli entro il 10% dal massimo', 'Quanti titoli partecipano davvero ai massimi'),
    ('rut63', -1, 'FRAG', 'Small cap vs S&P 500 (63 sedute)', 'Russell 2000 meno S&P 500: negativo = rischio concentrato sulle large cap'),
    ('rv21', 1, 'STRS', 'Volatilità realizzata 21g', 'Deviazione standard annualizzata dei rendimenti giornalieri S&P 500'),
    ('vix', 1, 'STRS', 'VIX', 'Volatilità implicita a 30 giorni sulle opzioni S&P 500'),
    ('ts', 1, 'STRS', 'Struttura a termine VIX/VIX3M', 'Sopra 1 = paura a breve superiore a quella a 3 mesi'),
    ('move', 1, 'STRS', 'MOVE (volatilità Treasury)', 'Volatilità implicita del mercato obbligazionario USA'),
    ('hy63', -1, 'STRS', 'Credito high yield vs Treasury (63g)', 'Fondo obbligazionario high yield (Vanguard VWEHX) contro Treasury intermedi (VFITX): negativo = il credito rischioso perde terreno'),
]
CONFIRM = [
    ('cot_am', 1, 'Asset manager: posizione netta E-mini (% OI)', 'CFTC Traders in Financial Futures; alto = istituzionali molto lunghi'),
    ('cot_lev', -1, 'Leveraged funds: posizione netta E-mini (% OI)', 'CFTC; hedge fund / CTA'),
    ('aaii', 1, 'AAII rialzisti − ribassisti', 'Sondaggio settimanale investitori privati (sentiment)'),
    ('nfci', 1, 'Chicago Fed NFCI', 'Condizioni finanziarie (positivo = più restrittive della media)'),
    ('curve', -1, 'Curva 10 anni − 3 mesi', 'Negativa = curva invertita'),
    ('baa63', 1, 'Spread corporate BAA: variazione 63g', 'FRED (Moody\'s BAA − Treasury 10 anni); più predittivo ma FRED non è sempre raggiungibile, quindi fuori dall\'indice'),
    ('cape', 1, 'Valutazione: CAPE di Shiller', 'Prezzo dell\'S&P 500 diviso la media degli utili reali degli ultimi 10 anni (multpl.com); alto = mercato caro'),
    ('tnx63', 1, 'Rendimento 10 anni: variazione 63g', 'Rialzo rapido dei tassi; segno instabile nel tempo, escluso dall\'indice'),
]

# Pesi di default (ifi-1.2): 1,25 ai tre fattori che hanno funzionato in tutti i periodi di prova
# (1999-2008, 2009-2016, 2017-2026): quota titoli sopra la media 200g, quota vicino ai massimi, MOVE.
# Gli altri a 1. Pesi stimati liberamente non hanno migliorato la previsione fuori campione.
WEIGHTS = {'ewcap63': 1.0, 'pct200': 1.25, 'nl10': 1.0, 'near_hi': 1.25, 'rut63': 1.0,
           'rv21': 1.0, 'vix': 1.0, 'ts': 1.0, 'move': 1.25, 'hy63': 1.0}

def _wmean(P, cols):
    W = pd.DataFrame({c: np.where(P[c].notna(), WEIGHTS.get(c, 1.0), 0.0) for c in cols}, index=P.index)
    return (P[cols].fillna(0) * W).sum(axis=1) / W.sum(axis=1).replace(0, np.nan)

def scores(f):
    P = pd.DataFrame(index=f.index)
    for col, sgn, *_ in FACTORS + [(c[0], c[1]) for c in CONFIRM]:
        if col not in f or f[col].notna().sum() < 800: continue
        p = ppct(f[col]); P[col] = p if sgn > 0 else 100 - p
    fr = [c for c, s, g, *_ in FACTORS if g == 'FRAG' and c in P]
    st = [c for c, s, g, *_ in FACTORS if g == 'STRS' and c in P]
    P['FRAG'] = _wmean(P, fr)
    P['STRS'] = _wmean(P, st)
    P.loc[P[fr].notna().sum(axis=1) < 3, 'FRAG'] = np.nan
    P.loc[P[st].notna().sum(axis=1) < 3, 'STRS'] = np.nan
    P['IFI'] = 0.5 * P['FRAG'] + 0.5 * P['STRS']
    return P

# ----------------------------------------------------------------------------- stats
def hold(sig, n=21):
    out = np.zeros(len(sig)); k = 0
    for i, s in enumerate(sig.fillna(False).values):
        if s: k = n
        out[i] = 1 if k > 0 else 0; k = max(0, k - 1)
    return pd.Series(out, index=sig.index)

def backtest(f, expo, start, end=None):
    r = f['spx'].pct_change().loc[start:end].fillna(0); c = f['cash'].loc[start:end]
    e = expo.shift(1).loc[start:end].fillna(1)
    ret = e * r + (1 - e) * c; eq = (1 + ret).cumprod(); yrs = len(eq) / 252
    return dict(cagr=round((eq.iloc[-1] ** (1 / yrs) - 1) * 100, 2), maxdd=round((eq / eq.cummax() - 1).min() * 100, 1),
                vol=round(ret.std() * np.sqrt(252) * 100, 1), defensive=round((e < 1).mean() * 100, 0))

def episodes(f, sig, gap=40):
    idx = sig[sig.fillna(False)].index; eps = []
    for d in idx:
        if not eps or f.index.get_loc(d) - f.index.get_loc(eps[-1][1]) > gap: eps.append([d, d])
        else: eps[-1][1] = d
    out = []
    spx = f['spx']
    for s, e in eps:
        i = f.index.get_loc(s)
        m60 = spx.iloc[i + 1:i + 61].min() / spx.iloc[i] - 1 if i + 1 < len(spx) else np.nan
        m126 = spx.iloc[i + 1:i + 127].min() / spx.iloc[i] - 1 if i + 1 < len(spx) else np.nan
        out.append(dict(start=s.strftime('%Y-%m-%d'), end=e.strftime('%Y-%m-%d'), days=int(sig.loc[s:e].sum()),
                        min60=None if np.isnan(m60) else round(m60 * 100, 1),
                        min126=None if np.isnan(m126) else round(m126 * 100, 1),
                        complete=bool(i + 60 < len(spx))))
    return out

def load_holdings(C_all):
    """Primi 50 titoli dell'S&P 500 per peso (ETF SPY), con andamento dai prezzi Yahoo."""
    hp = os.path.join(RAW, 'spy_holdings.xlsx')
    if not os.path.exists(hp): return None
    try:
        x = pd.read_excel(hp, header=None)
    except Exception:
        return None
    asof = None
    for v in x.iloc[:5, 1]:
        v = str(v)
        if 'As of' in v: asof = v.replace('As of', '').strip()
    hdr = [k for k, v in zip(x.index, x.iloc[:, 0]) if str(v).strip() == 'Name']
    if not len(hdr): return None
    h = x.iloc[hdr[0] + 1:, :6].copy(); h.columns = ['name', 'ticker', 'id', 'sedol', 'weight', 'sector']
    h = h[pd.to_numeric(h['weight'], errors='coerce').notna()]
    h['weight'] = h['weight'].astype(float)
    h = h[[bool(__import__('re').match(r'^[A-Z.]+$', str(t))) for t in h['ticker']]].sort_values('weight', ascending=False)
    rows = []
    for _, r in h.head(50).iterrows():
        t = str(r['ticker']).strip()
        s = C_all[t].dropna() if t in C_all.columns else (C_all[t.replace('.', '-')].dropna() if t.replace('.', '-') in C_all.columns else pd.Series(dtype=float))
        def ret(k):
            return round((s.iloc[-1] / s.iloc[-1 - k] - 1) * 100, 2) if len(s) > k else None
        ma = s.rolling(200).mean()
        rows.append(dict(name=str(r['name']).title(), ticker=t, weight=round(float(r['weight']), 3),
                         r1=ret(1), r21=ret(21), r63=ret(63), r252=ret(252),
                         above200=(bool(s.iloc[-1] > ma.iloc[-1]) if len(s) > 200 else None),
                         from_hi=(round((s.iloc[-1] / s.iloc[-252:].max() - 1) * 100, 1) if len(s) > 20 else None)))
    return dict(asof=asof, top=rows, top10=round(float(h['weight'].head(10).sum()), 2),
                top50=round(float(h['weight'].head(50).sum()), 2), n=int(len(h)))

def bootstrap_auc(score, y, n=400, seed=7):
    """Intervallo al 90% dell'AUC ricampionando anni interi (i giorni vicini non sono indipendenti)."""
    m = score.notna() & y.notna(); sc = score[m]; yy = y[m]
    years = sorted(set(sc.index.year)); rng = np.random.default_rng(seed); out = []
    by = {yr: (sc[sc.index.year == yr], yy[yy.index.year == yr]) for yr in years}
    for _ in range(n):
        pick = rng.choice(years, len(years), replace=True)
        a = pd.concat([by[k][0] for k in pick], ignore_index=True); b = pd.concat([by[k][1] for k in pick], ignore_index=True)
        v = auc(a, b)
        if not np.isnan(v): out.append(v)
    return [round(float(np.percentile(out, 5)), 3), round(float(np.percentile(out, 95)), 3)] if out else None

# ===================== REPORT MENSILE (mese precedente, 4 colori) =====================


MESI = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre']
STATO = ['verde', 'giallo', 'arancione', 'rosso']


def _f(v, d=1, suf=''):
    if v is None or (isinstance(v, float) and np.isnan(v)): return 'n.d.'
    s = f"{v:,.{d}f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    return s + suf


def _sg(v, d=1, suf=''):
    if v is None or (isinstance(v, float) and np.isnan(v)): return 'n.d.'
    return ('+' if v > 0 else '') + _f(v, d, suf)


def _at(s, d):
    s = s.dropna(); s = s[s.index <= d]
    return float(s.iloc[-1]) if len(s) else np.nan


def _chg(s, d, k):
    s = s.dropna(); s = s[s.index <= d]
    return float(s.iloc[-1] / s.iloc[-1 - k] - 1) * 100 if len(s) > k else np.nan


def _diff(s, d, k):
    s = s.dropna(); s = s[s.index <= d]
    return float(s.iloc[-1] - s.iloc[-1 - k]) if len(s) > k else np.nan


def _dd(s, d, win=252):
    s = s.dropna(); s = s[s.index <= d]
    if len(s) < 20: return np.nan
    return float(s.iloc[-1] / s.iloc[-win:].max() - 1) * 100


def _series(chart_end, series, years=5, step=2, kind='line', **kw):
    """serie per il grafico del riquadro (5 anni, un punto ogni 2 sedute)"""
    start = chart_end - pd.DateOffset(years=years)
    idx = None; out = []
    for name, s, role in series:
        s = s.dropna(); s = s[(s.index >= start) & (s.index <= chart_end)]
        if idx is None:
            idx = s.index[::step]
            if len(s) and s.index[-1] not in idx: idx = idx.append(pd.DatetimeIndex([s.index[-1]]))
        v = s.reindex(idx).ffill()
        out.append({'name': name, 'role': role, 'values': [None if np.isnan(x) else round(float(x), 4) for x in v]})
    return dict(type=kind, dates=[d.strftime('%Y-%m-%d') for d in idx], series=out, **kw)


def _state_trend(above, rising):
    return 0 if above and rising else 1 if above else 2 if rising else 3




# Indicazione generale (non personalizzata) per ogni riquadro e stato
PARERE = {
    'rischio': ['Mantenere l\'esposizione azionaria prevista dal proprio piano; è una fase in cui uscire dal mercato di solito costa più di quanto protegga.',
                'Mantenere l\'esposizione, senza aumentare il rischio. Controllare l\'indice ogni settimana.',
                'Non aumentare l\'esposizione e rimandare nuovi acquisti importanti; chi è sopra il proprio livello di rischio può riportarsi al livello previsto.',
                'Ridurre il rischio secondo il proprio piano: la regola della dashboard passa in difesa. Prima di vendere, valutare costi e tasse.'],
    'flussi': ['Nessuna azione: la preferenza per le azioni conferma il quadro positivo.',
               'Nessuna azione, ma seguire il rapporto: se scende sotto la media diventa un segnale di prudenza.',
               'Prudenza sui nuovi acquisti azionari finché il rapporto non torna sopra la media.',
               'Segnale di difesa: valutare di alleggerire le azioni più rischiose a favore di liquidità o titoli di Stato brevi.'],
    'ampiezza': ['Nessuna azione: il rialzo è sano e diffuso.',
                 'Nessuna azione; preferire indici diversificati (o a peso uguale) ai pochi titoli più grandi.',
                 'Evitare di concentrarsi sui pochi titoli che trainano l\'indice; diversificare (per esempio con l\'S&P a peso uguale) e non aumentare l\'esposizione.',
                 'Prudenza: non aumentare le azioni, ridurre la concentrazione sui grandi titoli tecnologici e tenere pronta una quota di liquidità. Un calo del 10% è storicamente frequente dopo questo segnale.'],
    'ciclo': ['Contesto favorevole ai settori ciclici (industria, materiali, finanza).',
              'Bilanciare: affiancare ai ciclici una quota di settori difensivi.',
              'Fase spesso favorevole per accumulare gradualmente, se il proprio orizzonte è lungo.',
              'Preferire settori difensivi e qualità (aziende con poco debito e utili stabili).'],
    'speculazione': ['Il pessimismo diffuso storicamente è stato un\'occasione: nessuna fretta di vendere.',
                     'Nessuna azione.',
                     'Evitare acquisti impulsivi sull\'onda dell\'entusiasmo; rispettare il proprio piano.',
                     'Euforia: non inseguire i rialzi, prendere in considerazione di consolidare parte dei guadagni.'],
    'riskonoff': ['Contesto favorevole al rischio: mantenere l\'esposizione prevista.',
                  'Mantenere, monitorando il segnale negativo.',
                  'Segnali misti: evitare di aumentare il rischio.',
                  'Prevale la difesa: ridurre le posizioni più speculative.'],
    'trend': ['Trend pienamente positivo: mantenere.',
              'Mantenere; un cedimento di breve non cambia il trend di fondo.',
              'Trend incerto: non aumentare l\'esposizione finché non torna positivo.',
              'Trend negativo: chi segue una disciplina di trend riduce le azioni.'],
    'settori': ['Favorire i settori ciclici e di crescita.',
                'Mantenere un portafoglio bilanciato tra ciclici e difensivi.',
                'Fase di transizione: bilanciare con una quota difensiva.',
                'Aumentare il peso dei settori difensivi (utility, beni di prima necessità, sanità).'],
    'credito': ['Nessuna azione: il credito conferma la stabilità.',
                'Seguire il dato nelle prossime settimane.',
                'Ridurre le obbligazioni ad alto rendimento e non aumentare le azioni: il credito spesso anticipa la borsa.',
                'Segnale di allarme: ridurre rischio azionario e obbligazioni high yield, privilegiare liquidità e titoli di Stato brevi.'],
    'allocazione': ['La regola dei 10 mesi resta investita al 100%.',
                    'Resta investita, ma vicino alla soglia: un mese debole cambierebbe il segnale.',
                    'La regola indicherebbe di uscire dalle azioni (liquidità) fino a una chiusura mensile sopra la media.',
                    'La regola è fuori dalle azioni: si rientra solo con una chiusura mensile sopra la media.'],
    'tassi': ['Contesto favorevole alle obbligazioni a media e lunga scadenza.',
              'Mantenere le obbligazioni, senza allungare la durata.',
              'Preferire obbligazioni a breve scadenza (meno sensibili ai tassi) e limitare le azioni più care.',
              'Evitare le obbligazioni a lunga scadenza; preferire liquidità e titoli brevi finché i tassi non si stabilizzano.'],
    'cambio': ['Nessuna azione sul cambio.',
               'Nessuna azione; da seguire se il rialzo dell\'euro continua.',
               'Valutare strumenti con copertura del cambio (classi "EUR hedged") per la parte in dollari.',
               'Il rischio di cambio pesa: considerare la copertura valutaria sulla parte americana del portafoglio.'],
    'materie': ['Nessuna azione.',
                'Nessuna azione.',
                'Attenzione all\'inflazione: limitare obbligazioni lunghe; materie prime ed energia possono fare da protezione parziale.',
                'Shock energetico: proteggersi dall\'inflazione (energia, materie prime, titoli indicizzati) e limitare la durata delle obbligazioni.'],
    'cripto': ['Propensione al rischio alta: nessuna indicazione per le azioni.',
               'Entusiasmo in calo: nessuna azione sulle azioni.',
               'Ritiro degli speculatori: segnale da affiancare agli altri, non decisivo da solo.',
               'Forte calo della speculazione: prudenza sugli asset più rischiosi.'],
    'stagionalita': ['Statistica favorevole, ma da sola non giustifica decisioni.',
                     'Nessuna indicazione.',
                     'Statistica sfavorevole: non decidere solo su questa, ma evitare di aggiungere rischio in fretta.',
                     'Statistica molto sfavorevole: prudenza nell\'aggiungere nuovo rischio.'],
}
# Spiegazione approfondita di come funziona ogni indicatore
DETAIL = {
    'rischio': 'L\'indice mette insieme due famiglie di misure. La fragilità guarda dentro l\'S&P 500 titolo per titolo: quanti sono in tendenza positiva, quanti toccano minimi annuali, se le società medie tengono il passo dei giganti, se le piccole società seguono. Lo stress guarda la tensione già visibile: volatilità realizzata, VIX e sua struttura a termine, volatilità dei titoli di Stato (MOVE), credito ad alto rendimento. Ogni misura è confrontata con gli ultimi 5 anni, quindi 70 significa "più rischioso del 70% dei giorni recenti".',
    'flussi': 'Il rapporto tra l\'ETF sull\'S&P 500 e quello sui Treasury a lunga scadenza sale quando le azioni rendono più delle obbligazioni. Non misura i flussi in senso stretto, ma dove si sta spostando il denaro: in fase di fiducia verso le azioni, in fase di paura verso i titoli di Stato. La media a 200 giorni separa la tendenza di fondo dal rumore.',
    'ampiezza': 'Si contano le società dell\'S&P 500 sopra la propria media a 200 giorni (tendenza di lungo periodo positiva) e quelle entro il 10% dal proprio massimo annuale. Quando l\'indice sale ma queste quote scendono, il rialzo è sostenuto da pochi titoli molto grandi: è la "spaccatura interna", che storicamente ha reso il mercato più vulnerabile.',
    'ciclo': 'Il rame è usato in edilizia, elettronica, auto: la domanda cresce con l\'economia. L\'oro è un bene rifugio. Quando il rame sale più dell\'oro, il mercato si aspetta più crescita; quando scende, si aspetta rallentamento. È un indicatore di mercato, aggiornato ogni giorno, che anticipa spesso le statistiche ufficiali ma può dare falsi segnali (per esempio per shock dell\'offerta di rame).',
    'speculazione': 'Ogni settimana l\'associazione americana dei risparmiatori (AAII) chiede se nei prossimi 6 mesi la borsa salirà o scenderà. Il saldo ottimisti meno pessimisti, mediato su 8 settimane, misura l\'umore. Si legge "al contrario": l\'euforia estrema accompagna spesso i massimi, il pessimismo estremo i minimi. Il VIX basso conferma un clima di compiacenza.',
    'riskonoff': 'Quattro segnali indipendenti di propensione al rischio: i consumi discrezionali battono i beni di prima necessità (le famiglie spendono), il credito ad alto rendimento batte i Treasury (gli investitori accettano rischio), l\'S&P è sopra la media a 200 giorni (tendenza positiva), il VIX è sotto 20 (poca paura). Più segnali sono positivi, più il contesto è favorevole alle azioni.',
    'trend': 'I fondi che seguono le tendenze (CTA) gestiscono centinaia di miliardi e comprano o vendono in base a regole simili: prezzo sopra o sotto le medie mobili, rendimento positivo o negativo su vari orizzonti. Qui si contano 6 segnali (medie a 50, 100 e 200 giorni; rendimento a 3, 6 e 12 mesi). Quando i segnali si spengono, questi fondi vendono e possono amplificare i cali.',
    'settori': 'Si confronta un paniere di settori ciclici (tecnologia, finanza, industria, consumi discrezionali) con uno di settori difensivi (utility, beni di prima necessità, sanità), tutti a peso uguale. I ciclici guadagnano di più quando l\'economia accelera; i difensivi tengono meglio nelle fasi difficili. Il rapporto mostra cosa preferiscono i grandi investitori.',
    'credito': 'Le obbligazioni ad alto rendimento (aziende indebitate) sono il primo posto dove si vede la tensione finanziaria: se le aziende fanno più fatica a rifinanziarsi, questi titoli scendono prima delle azioni. Il rapporto con i Treasury a 7–10 anni elimina l\'effetto dei tassi e isola il rischio di credito.',
    'allocazione': 'È una delle regole più studiate (Faber, 2007): a fine mese si confronta l\'S&P con la media delle ultime 10 chiusure mensili. Sopra si è investiti, sotto si passa in liquidità. Guarda solo i prezzi di fine mese, quindi ignora le oscillazioni giornaliere. Nella storia ha evitato gran parte dei grandi mercati ribassisti, al costo di qualche falso segnale.',
    'tassi': 'Il rendimento del Treasury a 10 anni è il riferimento per mutui, credito alle aziende e valutazione delle azioni. Quando sale in fretta, i titoli di Stato già in portafoglio perdono valore e le azioni con utili lontani nel tempo (tecnologia) valgono meno. La variazione in 3 mesi conta più del livello.',
    'cambio': 'Le azioni americane sono in dollari: per un investitore italiano il rendimento finale dipende anche dal cambio. Se l\'euro passa da 1,10 a 1,20 dollari, un investimento americano fermo in dollari perde circa l\'8% in euro. La variazione in 3 mesi misura quanto questo effetto sta pesando.',
    'materie': 'Il petrolio entra nei costi di trasporto, produzione e nei prezzi al consumo: un rialzo forte alza l\'inflazione e spinge le banche centrali a tenere i tassi alti. Oro e argento sono beni rifugio; un calo oltre il 20% dai massimi segna un mercato ribassista per questi metalli. Il grafico è in base 100 per confrontarli.',
    'cripto': 'Il bitcoin è scambiato 24 ore su 24 soprattutto da investitori privati e speculativi: per questo è un termometro della voglia di rischio. Sopra la media a 200 giorni è in tendenza positiva; un calo oltre il 35% dai massimi indica un mercato ribassista. Da solo non dice molto sulle azioni, ma conferma o smentisce il clima.',
    'stagionalita': 'Media dei rendimenti mensili dell\'S&P 500 per mese dell\'anno, calcolata sui dati disponibili dal 1996. Alcuni mesi sono stati storicamente più deboli (spesso settembre), altri più forti (novembre, dicembre). È una tendenza statistica con molte eccezioni: va usata solo come contesto.',
}

# Risvolti sul mercato per ogni riquadro e stato (0 verde, 1 giallo, 2 arancione, 3 rosso)
IMPL = {
    'rischio': ['Rischio interno e stress bassi: storicamente in queste fasi i cali del 10% sono rari e i rialzi tendono a proseguire. È il contesto in cui restare investiti costa meno.',
                'Situazione nella media: nessun allarme, ma il margine di sicurezza si riduce. Conviene seguire l\'evoluzione settimana per settimana.',
                'Rischio sopra la media: in passato, con l\'indice in questa fascia, i cali del 10% entro 3 mesi sono stati più frequenti del normale. Non è un segnale di uscita, ma un invito a non aumentare il rischio.',
                'Rischio alto: la regola della dashboard va in difesa. Storicamente è la fascia in cui si sono concentrati i cali più profondi; la priorità è proteggere il capitale.'],
    'flussi': ['I soldi preferiscono le azioni: è la condizione tipica dei mercati rialzisti, con le obbligazioni che non fanno concorrenza.',
               'Le azioni restano preferite ma il vantaggio si riduce: spesso succede quando i tassi scendono o quando il rialzo azionario rallenta.',
               'Le obbligazioni hanno battuto le azioni negli ultimi mesi: segnale di prudenza, ma la ripresa in corso dice che non è ancora fuga dal rischio.',
               'Gli investitori stanno passando dalle azioni alle obbligazioni: è il comportamento tipico prima o durante le correzioni.'],
    'ampiezza': ['Il rialzo è condiviso dalla maggior parte delle società: un mercato "largo" è più solido e regge meglio le notizie negative.',
                 'Partecipazione discreta ma non piena: alcuni settori restano indietro. Da seguire se la quota continua a scendere.',
                 'Meno della metà delle società è in tendenza positiva: l\'indice regge grazie a pochi titoli grandi, quindi è più vulnerabile se questi si fermano.',
                 'Spaccatura interna: l\'indice è vicino ai massimi ma molte società sono già in calo. Storicamente questa combinazione ha preceduto spesso correzioni del 10% o più.'],
    'ciclo': ['Il mercato sconta un\'economia in accelerazione: favorevole agli utili delle aziende cicliche e alle azioni in generale.',
              'Crescita ancora positiva ma in rallentamento: tipica fase avanzata del ciclo, in cui i settori difensivi iniziano a recuperare.',
              'Economia debole ma in recupero: fase spesso favorevole ai mercati, che anticipano la ripresa.',
              'Il mercato sconta un rallentamento economico: pesa sugli utili attesi e di solito sui settori ciclici.'],
    'speculazione': ['Prevale la prudenza: storicamente il pessimismo dei risparmiatori è stato più spesso un\'occasione che un pericolo.',
                     'Clima equilibrato: il sentiment non dà segnali particolari.',
                     'Ottimismo elevato: quando quasi tutti sono già investiti resta meno denaro nuovo per spingere i prezzi.',
                     'Euforia con volatilità bassa: è la combinazione che ha accompagnato molti massimi di mercato. Aumenta il rischio di delusioni.'],
    'riskonoff': ['Tutti i segnali indicano propensione al rischio: contesto favorevole alle azioni.',
                  'Prevale il risk-on con un segnale contrario: quadro positivo ma non pieno.',
                  'Segnali divisi: il mercato è indeciso, possibili oscillazioni ampie.',
                  'Prevale la fuga dal rischio: contesto storicamente sfavorevole alle azioni.'],
    'trend': ['Trend pienamente positivo: i fondi che seguono le tendenze (CTA) sono compratori, il che sostiene i prezzi.',
              'Trend positivo con qualche cedimento di breve: i CTA riducono un po\' le posizioni.',
              'Trend incerto: i CTA sono in gran parte usciti, il mercato perde un sostegno.',
              'Trend negativo: i CTA vendono o sono ribassisti, e le loro vendite possono accentuare i cali.'],
    'settori': ['I settori legati alla crescita guidano: gli investitori si aspettano un\'economia solida.',
                'I ciclici restano davanti ma rallentano: situazione neutrale, nessun segnale forte.',
                'I difensivi hanno preso il comando ma i ciclici stanno recuperando: fase di transizione.',
                'Utility, beni di prima necessità e sanità battono i ciclici: il mercato si mette sulla difensiva.'],
    'credito': ['Il credito rischioso tiene: nessun segnale di stress dal mondo delle obbligazioni, che di solito anticipa la borsa.',
                'Piccolo cedimento del credito rischioso: da monitorare, spesso rientra.',
                'Il credito rischioso perde terreno: è un campanello d\'allarme che in passato ha anticipato debolezza delle azioni.',
                'Fuga dal credito rischioso: nelle crisi passate è stato uno dei primi segnali, prima del calo delle azioni.'],
    'allocazione': ['Prezzo ben sopra la media di 10 mesi: la regola resta investita con margine.',
                    'Prezzo sopra la media ma vicino: la regola resta investita, ma un mese debole potrebbe farla uscire.',
                    'Prezzo appena sotto la media: la regola sarebbe uscita dalle azioni; spesso succede nelle correzioni.',
                    'Prezzo nettamente sotto la media: la regola è fuori dalle azioni, tipico dei mercati ribassisti.'],
    'tassi': ['Tassi stabili o in calo: sollievo per le obbligazioni già in portafoglio e per le azioni care (tecnologia).',
              'Lieve rialzo dei tassi: impatto limitato.',
              'Rialzo dei tassi deciso: le obbligazioni a lunga scadenza perdono valore e le azioni con valutazioni alte soffrono.',
              'Rialzo dei tassi molto rapido: pressione forte su obbligazioni e azioni care; aumenta il rischio di incidenti finanziari.'],
    'cambio': ['Euro stabile o in calo sul dollaro: chi investe dall\'Italia in azioni americane non perde sul cambio (o ci guadagna).',
               'Euro in lieve rafforzamento: piccola perdita di cambio sugli investimenti in dollari.',
               'Euro in netto rafforzamento: parte del rendimento delle azioni americane viene annullata dal cambio.',
               'Forte rialzo dell\'euro: il cambio erode in modo pesante i rendimenti in dollari; valutare la copertura valutaria.'],
    'materie': ['Energia in calo: frena l\'inflazione e lascia spazio a tassi più bassi.',
                'Petrolio in moderato rialzo: effetto limitato sull\'inflazione.',
                'Petrolio in forte rialzo: spinge l\'inflazione e rende più probabili tassi alti più a lungo.',
                'Shock petrolifero: rischio di inflazione e di rialzo dei tassi, pesa su consumi e margini delle aziende.'],
    'cripto': ['Bitcoin in tendenza positiva: la propensione al rischio degli investitori privati è alta.',
               'Bitcoin sopra la media ma lontano dai massimi: entusiasmo in calo.',
               'Bitcoin sotto la media: gli investitori più speculativi si ritirano.',
               'Bitcoin in mercato ribassista: forte calo della propensione al rischio speculativa.'],
    'stagionalita': ['Storicamente il mese che inizia è stato favorevole: è una tendenza statistica, non una garanzia.',
                     'Storicamente il mese che inizia è stato in media positivo, ma senza una prevalenza netta.',
                     'Storicamente il mese che inizia è stato debole: prudenza nell\'aggiungere nuovo rischio.',
                     'Storicamente il mese che inizia è tra i peggiori dell\'anno: prudenza nell\'aggiungere nuovo rischio.'],
}


WHAT_MK = {
    'm_eu': 'Borse dell\'Europa sviluppata (Regno Unito, Francia, Svizzera, Germania, Paesi Bassi, Italia…) attraverso l\'ETF Vanguard FTSE Europe (VGK), quotato in dollari.',
    'm_cn': 'Grandi società cinesi quotate a Hong Kong attraverso l\'ETF iShares China Large-Cap (FXI), quotato in dollari.',
    'm_jp': 'Borsa giapponese attraverso l\'ETF iShares MSCI Japan (EWJ), quotato in dollari.',
    'm_em': 'Borse dei paesi emergenti (Cina, India, Taiwan, Corea, Brasile, Arabia Saudita…) attraverso l\'ETF iShares MSCI Emerging Markets (EEM), quotato in dollari.',
}
HOW_MK = ('Quattro controlli: segnale automatico Buy/Sell (prezzo di fine mese sopra o sotto la media degli ultimi 10 mesi), rendimento a 6 mesi positivo, '
          'forza relativa a 6 mesi contro la borsa mondiale (ACWI), prezzo sopra la media a 200 giorni. Verde: 4 su 4. Giallo: 3. Arancione: 2. Rosso: 1 o nessuno. '
          'Almeno arancione se il calo dal massimo di 12 mesi supera il 20%; un gradino meglio se il prezzo rompe al rialzo i massimi degli ultimi 5 anni con segnale Buy.')
_MK_DET = ('Il segnale automatico è la regola della media a 10 mesi, usata da molti gestori per decidere quanto pesare ogni area: si guarda solo il prezzo di fine mese. '
           'Sopra la media = Buy (si tiene o si costruisce la posizione), sotto = Sell (si riduce o si copre). Cambia poche volte l\'anno e serve a evitare le fasi ribassiste lunghe, '
           'non a prendere i minimi. La forza relativa dice se l\'area fa meglio o peggio della borsa mondiale: un mercato che sale ma meno del mondo non merita un sovrappeso. '
           'Gli ETF sono in dollari: per chi investe in euro conta anche il cambio (vedi il riquadro Euro/Dollaro).')
for _k, _x in {'m_eu': ' Per l\'Europa il cambio pesa di meno se si usa un ETF in euro: l\'andamento in valuta locale può essere diverso da quello in dollari.',
               'm_cn': ' La Cina ha movimenti molto ampi e dipende dalle decisioni di Pechino (stimoli, regole su tecnologia e immobiliare) e dai rapporti commerciali con gli Stati Uniti: i segnali possono invertirsi in fretta.',
               'm_jp': ' Per il Giappone lo yen conta molto: un ETF in dollari unisce l\'andamento della borsa a quello della valuta. La borsa giapponese beneficia di uno yen debole, il possessore estero no.',
               'm_em': ' Gli emergenti dipendono dal dollaro (un dollaro debole li aiuta), dalle materie prime e dalla Cina, che ne pesa circa un quarto. Una rottura dei massimi di molti anni è un segnale di tendenza importante.'}.items():
    DETAIL[_k] = _MK_DET + _x
DETAIL['m_rot'] = ('Il rapporto tra Stati Uniti e resto del mondo descrive dove si sta spostando la leadership. Dopo oltre un decennio di predominio americano, '
                   'una rotazione verso Europa, Asia ed emergenti cambia il modo di diversificare: chi ha un portafoglio concentrato sull\'S&P 500 è più esposto se la rotazione prosegue. '
                   'La media a 200 giorni separa la tendenza di fondo dalle oscillazioni.')
_MK_PAR = ['Tendenza positiva confermata da tutti i segnali: chi ha già una quota in quest\'area la mantiene; chi non l\'ha può costruirla con ingressi graduali, entro la quota prevista per l\'estero.',
           'Tendenza positiva ma non piena: mantenere la quota senza aumentarla finché i segnali non tornano tutti concordi.',
           'Segnali in prevalenza negativi: non aumentare la quota; chi è sovrappesato può riportarsi al peso neutrale.',
           'Tendenza negativa: il segnale automatico è di vendita o il mercato è debole su tutti i fronti. Ridurre la quota secondo il proprio piano e attendere un nuovo segnale Buy.']
_MK_IMP = ['Il mercato sale, fa meglio della borsa mondiale e sta sopra le sue medie: è la combinazione con i rendimenti futuri storicamente migliori e i cali più rari.',
           'La tendenza resta positiva ma un segnale non conferma (spesso la forza relativa): il mercato sale, ma non è tra i migliori.',
           'Metà dei segnali è negativa: fase di transizione, in cui i movimenti diventano più incerti e i cali più frequenti.',
           'Il mercato è in tendenza negativa: storicamente in queste fasi i ribassi sono stati più profondi e le risalite meno durature.']
for _k in WHAT_MK: PARERE[_k] = _MK_PAR; IMPL[_k] = _MK_IMP
PARERE['m_rot'] = ['Leadership americana solida: nessun motivo di tendenza per ridurre il peso degli Stati Uniti.',
                   'Gli Stati Uniti restano davanti ma rallentano: per chi è molto concentrato sull\'America è un buon momento per diversificare gradualmente.',
                   'Il resto del mondo è davanti: chi ha solo azioni americane può valutare una quota estera nelle aree con segnale Buy.',
                   'Rotazione fuori dagli Stati Uniti in corso: diversificare verso le aree estere con segnale Buy, con ingressi graduali.']
IMPL['m_rot'] = ['Gli Stati Uniti battono il resto del mondo e il vantaggio cresce.', 'Gli Stati Uniti sono ancora davanti, ma il resto del mondo recupera.',
                 'Il resto del mondo è davanti, ma gli Stati Uniti stanno recuperando.', 'Il resto del mondo batte gli Stati Uniti e il divario cresce: rotazione della leadership.']

def build_report(f, P, C, today=None):
    today = today or dt.datetime.now(dt.timezone(dt.timedelta(hours=1))).date()
    first = pd.Timestamp(today.year, today.month, 1)
    dates = f.index
    me_c = dates[dates < first]
    if not len(me_c): return None
    me = me_c[-1]                                   # ultima seduta del mese del report
    m0 = pd.Timestamp(me.year, me.month, 1)
    pe_c = dates[dates < m0]
    pe = pe_c[-1] if len(pe_c) else None            # ultima seduta del mese prima
    month_name = MESI[me.month - 1] + ' ' + str(me.year)
    px = lambda t: C[t].ffill() if t in C else pd.Series(dtype=float)
    spx = f['spx']
    ma = lambda s, n: s.rolling(n, min_periods=int(n * .8)).mean()
    cards = []

    mends = spx.dropna().resample('ME').last().index
    mends = [dates[dates <= x][-1] for x in mends if (dates <= x).any() and x >= dates[0] + pd.DateOffset(years=2) and x < me]
    spxd = spx.dropna()
    def history(fn, tgt=None):
        # per ogni fine mese passato: stato dell'indicatore e cosa ha fatto l'S&P (o il mercato tgt) nei 3 mesi successivi
        rows = []; spxd = spx.dropna() if tgt is None else tgt.dropna()
        t0 = spxd.index[0] + pd.DateOffset(years=1)
        for d in mends:
            if d < t0: continue
            try: st = int(fn(d)[0])
            except Exception: continue
            k = spxd.index.searchsorted(d)
            if k + 63 >= len(spxd): continue
            seg = spxd.iloc[k:k + 64]
            rows.append((st, (seg.iloc[-1] / seg.iloc[0] - 1) * 100, (seg.min() / seg.iloc[0] - 1) * 100))
        out = []
        for st in range(4):
            r = [x for x in rows if x[0] == st]
            out.append(None if not r else dict(n=len(r), ret=round(float(np.mean([x[1] for x in r])), 1), pos=round(100 * np.mean([x[1] > 0 for x in r])), dd10=round(100 * np.mean([x[2] <= -10 for x in r]))))
        return out
    def card(id, sec, title, fn, chart, what, how, tgt=None, tgt_name=None, area='usa', extra=None):
        st, val, txt = fn(me)
        pst = fn(pe)[0] if pe is not None else None
        if chart.get('type') == 'line': chart['band'] = [m0.strftime('%Y-%m-%d'), me.strftime('%Y-%m-%d')]
        cards.append(dict(id=id, sec=sec, title=title, status=int(st), prev_status=None if pst is None else int(pst),
                          value=val, text=txt, what=what, how=how, impl=IMPL.get(id, ['', '', '', ''])[int(st)], chart=chart,
                          parere=PARERE.get(id, ['', '', '', ''])[int(st)], detail=DETAIL.get(id, ''), hist=None if id == 'stagionalita' else history(fn, tgt),
                          hist_target=tgt_name or 'l\'S&P 500', area=area, **(extra or {})))

    # 1 modello di rischio della dashboard
    ifi = P['IFI']
    def f_risk(d):
        v = _at(ifi, d); mm = ifi[(ifi.index >= pd.Timestamp(d.year, d.month, 1)) & (ifi.index <= d)].mean()
        st = 0 if v < 40 else 1 if v < 55 else 2 if v < 70 else 3
        exp = 0 if (v >= 70 or _at(f['trend_down'], d) == 1) else 100
        return st, _f(v, 0) + '/100', f'Indice di rischio a fine mese {_f(v, 0)} (media del mese {_f(mm, 0)}). La regola della dashboard indicava un\'esposizione azionaria del {exp}%.'
    card('rischio', 'Azioni', 'Modello di rischio della dashboard', f_risk,
         _series(me, [('Indice di rischio', ifi, 'main')], ref=[{'y': 70, 'label': 'soglia 70'}, {'y': 55, 'label': '55'}], ymin=0, ymax=100),
         'È l\'indice di questa dashboard: fragilità interna del mercato più stress (volatilità, credito, tassi), da 0 a 100.',
         'Verde sotto 40, giallo 40–54, arancione 55–69, rosso da 70 (la soglia oltre cui la regola va in difesa).')

    # 2 azioni contro obbligazioni
    r_eb = px('SPY') / px('TLT')
    def f_eb(d):
        v = _at(r_eb, d); m2 = _at(ma(r_eb, 200), d); c3 = _chg(r_eb, d, 63)
        st = _state_trend(v > m2, c3 > 0)
        return st, _sg(c3, 1, '% in 3 mesi'), ('Le azioni battono le obbligazioni a lungo termine: ' if v > m2 else 'Le obbligazioni hanno ripreso terreno sulle azioni: ') + f'rapporto azioni/Treasury 20 anni {"sopra" if v > m2 else "sotto"} la sua media a 200 giorni, {_sg(c3, 1, "%")} negli ultimi 3 mesi.'
    card('flussi', 'Azioni', 'Azioni contro obbligazioni', f_eb,
         _series(me, [('SPY / TLT', r_eb, 'main'), ('media 200 giorni', ma(r_eb, 200), 'ma')]),
         'Rapporto tra l\'ETF sull\'S&P 500 (SPY) e quello sui Treasury a 20+ anni (TLT): dice dove preferiscono andare i soldi.',
         'Verde: sopra la media e in salita (preferenza netta per le azioni). Giallo: sopra ma in calo. Arancione: sotto ma in recupero. Rosso: sotto e in calo (fuga verso le obbligazioni).')

    # 3 ampiezza
    def f_br(d):
        v = _at(f['pct200'], d); nh = _at(f['near_hi'], d); sp = _at(f['split'], d) == 1
        st = 0 if v >= 65 else 1 if v >= 50 else 2 if v >= 35 else 3
        if sp: st = min(3, st + 1)
        return st, _f(v, 0, '% sopra media 200g'), f'{_f(v, 0)}% dei titoli S&P 500 sopra la media a 200 giorni, {_f(nh, 0)}% entro il 10% dal proprio massimo.' + (' Segnale di spaccatura acceso: l\'indice è vicino ai massimi ma molti titoli sono ai minimi annuali.' if sp else '')
    card('ampiezza', 'Azioni', 'Ampiezza del mercato', f_br,
         _series(me, [('% titoli sopra media 200g', f['pct200'], 'main'), ('% titoli vicino al massimo', f['near_hi'], 'second')], ref=[{'y': 50, 'label': '50%'}], ymin=0, ymax=100),
         'Quante società partecipano al rialzo: un mercato sano sale "tutto insieme", un mercato fragile sale con pochi titoli.',
         'Verde oltre 65% dei titoli sopra la media a 200 giorni, giallo 50–65%, arancione 35–50%, rosso sotto 35%. Un gradino in più se è acceso il segnale di spaccatura.')

    # 4 ciclo economico (proxy rame/oro)
    r_cg = px('HG=F') / px('GC=F')
    def f_cy(d):
        v = _at(r_cg, d); m = _at(ma(r_cg, 252), d); c3 = _chg(r_cg, d, 63)
        st = _state_trend(v > m, c3 > 0)
        return st, _sg(c3, 1, '% in 3 mesi'), f'Rapporto rame/oro {"sopra" if v > m else "sotto"} la media di 12 mesi e {"in salita" if c3 > 0 else "in discesa"} ({_sg(c3, 1, "%")} in 3 mesi): ' + ('il mercato sconta un\'economia in accelerazione.' if st == 0 else 'crescita ancora sostenuta ma in rallentamento.' if st == 1 else 'segnali di ripresa da livelli deboli.' if st == 2 else 'il mercato sconta un rallentamento economico.')
    card('ciclo', 'Economia', 'Ciclo economico (rame contro oro)', f_cy,
         _series(me, [('Rame / oro', r_cg, 'main'), ('media 12 mesi', ma(r_cg, 252), 'ma')]),
         'Il rame si usa nell\'industria e sale con l\'economia; l\'oro è un bene rifugio. Il loro rapporto è un indicatore di mercato del ciclo economico, aggiornato ogni giorno (non sostituisce i dati ufficiali OCSE).',
         'Verde: sopra la media di 12 mesi e in salita. Giallo: sopra ma in calo. Arancione: sotto ma in recupero. Rosso: sotto e in calo.')

    # 5 speculazione / sentiment
    def f_sp(d):
        p = _at(P['aaii'], d) if 'aaii' in P else np.nan; a8 = _at(f['aaii8'], d) if 'aaii8' in f else np.nan; vx = _at(f['vix'], d)
        st = 3 if (p >= 85 and vx < 15) else 0 if p < 40 else 1 if p < 70 else 2
        return st, f'AAII {_sg(a8, 0, " pt")}', f'Sondaggio AAII (media 8 settimane): ottimisti meno pessimisti {_sg(a8, 0, " punti")}, percentile {_f(p, 0)} sugli ultimi 5 anni; VIX {_f(vx, 1)}. ' + ('Euforia: ottimismo estremo con volatilità bassa, la combinazione dei massimi di mercato.' if st == 3 else 'Ottimismo elevato ma non estremo.' if st == 2 else 'Clima equilibrato.' if st == 1 else 'Prevale la prudenza: nessun eccesso speculativo.')
    card('speculazione', 'Azioni', 'Speculazione e sentiment', f_sp,
         _series(me, [('AAII ottimisti − pessimisti (8 sett.)', f['aaii8'] if 'aaii8' in f else f['spx'] * np.nan, 'main')], ref=[{'y': 0, 'label': '0'}]),
         'Misura l\'umore dei risparmiatori americani: quando sono tutti euforici, chi poteva comprare l\'ha già fatto.',
         'Percentile del sentiment sugli ultimi 5 anni: verde sotto 40, giallo 40–69, arancione da 70, rosso se oltre 85 con VIX sotto 15 (euforia).')

    # 6 risk on / off
    r_yp = px('XLY') / px('XLP'); r_hi = px('HYG') / px('IEF')
    comp = pd.DataFrame({'a': r_yp > ma(r_yp, 200), 'b': r_hi > ma(r_hi, 200), 'c': spx > f['ma200'], 'd': f['vix'] < 20}).astype(float)
    score = comp.sum(axis=1).where(comp.notna().all(axis=1) | True)
    def f_ro(d):
        row = comp[comp.index <= d].iloc[-1]; n = int(row.sum())
        st = 0 if n == 4 else 1 if n == 3 else 2 if n == 2 else 3
        lab = ['consumi discrezionali > beni di prima necessità', 'credito rischioso > Treasury', 'S&P sopra media 200g', 'VIX sotto 20']
        ok = [l for l, x in zip(lab, row) if x == 1]; ko = [l for l, x in zip(lab, row) if x != 1]
        return st, f'{n} su 4', ('Risk-on: ' if n >= 3 else 'Risk-off: ' if n <= 1 else 'Misto: ') + (f'positivi {", ".join(ok)}' if ok else 'nessun segnale positivo') + (f'; negativi {", ".join(ko)}.' if ko else '.')
    card('riskonoff', 'Azioni', 'Modello Risk-on / Risk-off', f_ro,
         _series(me, [('Segnali positivi (0–4)', score, 'main')], ref=[{'y': 2, 'label': '2'}], ymin=0, ymax=4, step_line=True),
         'Quattro segnali di propensione al rischio: consumi discrezionali contro beni di prima necessità, credito ad alto rendimento contro Treasury, S&P sopra la media a 200 giorni, VIX sotto 20.',
         'Verde 4 su 4, giallo 3, arancione 2, rosso 0–1.')

    # 7 trend (stile CTA)
    def f_tr(d):
        s = spx[spx.index <= d].dropna(); v = s.iloc[-1]
        bits = [v > s.rolling(50).mean().iloc[-1], v > s.rolling(100).mean().iloc[-1], v > s.rolling(200).mean().iloc[-1],
                v > s.iloc[-64], v > s.iloc[-127], v > s.iloc[-253]]
        n = int(sum(bits)); ext = (v / s.rolling(200).mean().iloc[-1] - 1) * 100
        st = 0 if n == 6 else 1 if n >= 4 else 2 if n >= 2 else 3
        return st, f'{n} su 6', f'S&P sopra {sum(bits[:3])} medie mobili su 3 (50, 100, 200 giorni) e in rialzo su {sum(bits[3:])} orizzonti su 3 (3, 6, 12 mesi). Distanza dalla media a 200 giorni {_sg(ext, 1, "%")}' + (': trend molto esteso, da seguire ma con attenzione.' if ext > 12 else '.')
    card('trend', 'Azioni', 'Trend dell\'S&P 500 (stile CTA)', f_tr,
         _series(me, [('S&P 500', spx, 'main'), ('media 200 giorni', f['ma200'], 'ma')], log=True),
         'I fondi che seguono i trend (CTA) comprano quando i prezzi sono sopra le medie e il momento è positivo. Qui si contano 6 segnali di trend.',
         'Verde 6 su 6, giallo 4–5, arancione 2–3, rosso 0–1.')

    # 8 ciclici contro difensivi
    def eqidx(ts):
        ss = [px(t) for t in ts if t in C]; ss = [s / s.dropna().iloc[0] for s in ss if s.notna().sum() > 300]
        return pd.concat(ss, axis=1).mean(axis=1) if ss else pd.Series(dtype=float)
    r_cd = eqidx(['XLY', 'XLK', 'XLF', 'XLI']) / eqidx(['XLU', 'XLP', 'XLV'])
    def f_cd(d):
        v = _at(r_cd, d); m2 = _at(ma(r_cd, 200), d); c3 = _chg(r_cd, d, 63)
        st = _state_trend(v > m2, c3 > 0)
        return st, _sg(c3, 1, '% in 3 mesi'), ['I settori ciclici guidano: fiducia nella crescita.', 'Ciclici ancora avanti ma in rallentamento: situazione neutrale.', 'Difensivi avanti, ciclici in recupero.', 'I difensivi battono i ciclici: gli investitori si proteggono.'][st] + f' Rapporto {_sg(c3, 1, "%")} in 3 mesi.'
    card('settori', 'Azioni', 'Settori ciclici contro difensivi', f_cd,
         _series(me, [('Ciclici / difensivi', r_cd, 'main'), ('media 200 giorni', ma(r_cd, 200), 'ma')]),
         'Ciclici: tecnologia, finanza, industria, consumi discrezionali. Difensivi: utility, beni di prima necessità, sanità. Quando comandano i difensivi, il mercato si prepara a tempi peggiori.',
         'Verde: ciclici sopra la media e in salita. Giallo: sopra ma in calo. Arancione: sotto ma in recupero. Rosso: sotto e in calo.')

    # 9 credito (canarino)
    def f_cr(d):
        ddv = _dd(r_hi, d); p = _at(P['hy63'], d) if 'hy63' in P else np.nan
        st = 0 if ddv > -1 else 1 if ddv > -2.5 else 2 if ddv > -5 else 3
        return st, _f(ddv, 1, '% dal massimo'), f'Obbligazioni high yield contro Treasury a {_f(ddv, 1, "%")} dal massimo dell\'ultimo anno (percentile di rischio del credito {_f(p, 0)}). ' + ['Nessun allarme: il credito rischioso tiene.', 'Piccolo cedimento, da monitorare.', 'Il credito rischioso perde terreno: allerta.', 'Fuga dal credito rischioso: storicamente anticipa i cali di borsa.'][st]
    card('credito', 'Obbligazioni', 'Credito: il "canarino nella miniera"', f_cr,
         _series(me, [('High yield / Treasury (HYG/IEF)', r_hi, 'main'), ('media 200 giorni', ma(r_hi, 200), 'ma')]),
         'Le obbligazioni delle aziende più indebitate sono le prime a soffrire quando l\'economia o la liquidità peggiorano: per questo le si chiama il canarino nella miniera.',
         'Distanza del rapporto HYG/IEF dal massimo di 12 mesi: verde oltre −1%, giallo fino a −2,5%, arancione fino a −5%, rosso oltre −5%.')

    # 10 asset allocation mensile (10 mesi)
    mon = spx.dropna().resample('ME').last(); mon = mon[mon.index <= me + pd.offsets.MonthEnd(0)]
    sma10 = mon.rolling(10).mean()
    def f_aa(d):
        mm = mon[mon.index <= d + pd.offsets.MonthEnd(0)]; sm = sma10.reindex(mm.index)
        dist = (mm.iloc[-1] / sm.iloc[-1] - 1) * 100; above = (mm > sm)
        k = 0
        for x in above[::-1]:
            if x == above.iloc[-1]: k += 1
            else: break
        st = 0 if dist > 5 else 1 if dist > 0 else 2 if dist > -3 else 3
        return st, ('100% azioni' if dist > 0 else '0% azioni'), f'Chiusura mensile {_f(dist, 1, "%")} rispetto alla media degli ultimi 10 mesi: esposizione {"100%" if dist > 0 else "0%"} in azioni, {k}° mese consecutivo {"sopra" if dist > 0 else "sotto"} la media.'
    mc = mon[mon.index >= me - pd.DateOffset(years=6)]
    card('allocazione', 'Azioni', 'Asset allocation mensile (regola dei 10 mesi)', f_aa,
         dict(type='line', dates=[x.strftime('%Y-%m-%d') for x in mc.index], series=[{'name': 'S&P 500 fine mese', 'role': 'main', 'values': [round(float(x), 2) for x in mc]}, {'name': 'media 10 mesi', 'role': 'ma', 'values': [None if np.isnan(x) else round(float(x), 2) for x in sma10.reindex(mc.index)]}], log=True),
         'Regola "cieca" che guarda solo i prezzi di fine mese: investiti al 100% se l\'S&P chiude sopra la media degli ultimi 10 mesi, liquidità se chiude sotto.',
         'Verde oltre +5% sopra la media, giallo tra 0 e +5%, arancione fino a −3% sotto, rosso oltre −3% sotto.')

    # 11 tassi e obbligazioni
    tnx = px('^TNX')
    def f_rt(d):
        v = _at(tnx, d); c3 = _diff(tnx, d, 63); c1 = _diff(tnx, d, 21); ddt = _dd(px('TLT'), d, 252 * 5)
        st = 0 if c3 <= 0 else 1 if c3 <= .25 else 2 if c3 <= .5 else 3
        return st, _f(v, 2, '%'), f'Rendimento del Treasury 10 anni {_f(v, 2, "%")}: {_sg(c1, 2, " punti")} nel mese, {_sg(c3, 2, " punti")} in 3 mesi. Treasury a lungo termine (TLT) a {_f(ddt, 0, "%")} dal massimo degli ultimi 5 anni. ' + ['Tassi stabili o in calo: nessuna pressione.', 'Lieve rialzo dei tassi.', 'Rialzo dei tassi deciso: pesa sulle obbligazioni e sulle azioni care.', 'Rialzo dei tassi molto rapido: forte pressione.'][st]
    card('tassi', 'Obbligazioni', 'Tassi e obbligazioni governative', f_rt,
         _series(me, [('Rendimento Treasury 10 anni (%)', tnx, 'main')]),
         'Il rendimento dei titoli di Stato americani a 10 anni è il "prezzo del denaro" di riferimento: se sale in fretta, le obbligazioni già in portafoglio perdono valore e le azioni care soffrono.',
         'Variazione in 3 mesi: verde se in calo, giallo fino a +0,25 punti, arancione fino a +0,5, rosso oltre +0,5.')

    # 12 cambio euro/dollaro
    eur = px('EURUSD=X')
    def f_fx(d):
        v = _at(eur, d); c3 = _chg(eur, d, 63); c1 = _chg(eur, d, 21); m2 = _at(ma(eur, 200), d)
        st = 0 if c3 <= 0 else 1 if c3 <= 3 else 2 if c3 <= 6 else 3
        return st, _f(v, 4), f'Euro/dollaro {_f(v, 4)}: {_sg(c1, 1, "%")} nel mese, {_sg(c3, 1, "%")} in 3 mesi, {"sopra" if v > m2 else "sotto"} la media a 200 giorni. ' + ['Euro stabile o in calo: nessuna perdita di cambio su azioni americane.', 'Euro in lieve rafforzamento: piccolo costo di cambio.', 'Euro in netto rafforzamento: chi investe in dollari perde sul cambio.', 'Forte rialzo dell\'euro: il cambio erode in modo pesante i rendimenti in dollari.'][st]
    card('cambio', 'Valute', 'Euro / Dollaro', f_fx,
         _series(me, [('EUR/USD', eur, 'main'), ('media 200 giorni', ma(eur, 200), 'ma')]),
         'Per chi investe dall\'Italia in azioni americane conta anche il cambio: se l\'euro si rafforza, i guadagni in dollari valgono meno euro.',
         'Variazione dell\'euro in 3 mesi: verde se stabile o in calo, giallo fino a +3%, arancione fino a +6%, rosso oltre +6%.')

    # 13 materie prime
    oil = px('CL=F'); gold = px('GC=F'); silv = px('SI=F')
    def f_cm(d):
        o3 = _chg(oil, d, 63); gd = _dd(gold, d); sd = _dd(silv, d)
        st = 0 if o3 <= 0 else 1 if o3 <= 10 else 2 if o3 <= 25 else 3
        bear = [n for n, x in (('oro', gd), ('argento', sd)) if x <= -20]
        return st, f'Petrolio {_sg(o3, 0, "%")}', f'Petrolio {_sg(o3, 1, "%")} in 3 mesi; oro a {_f(gd, 1, "%")} e argento a {_f(sd, 1, "%")} dai massimi di 12 mesi' + (f' ({" e ".join(bear)} in bear market, oltre −20%).' if bear else '.') + ' ' + ['Energia in calo: nessuna spinta all\'inflazione.', 'Petrolio in moderato rialzo.', 'Petrolio in forte rialzo: rischio inflazione e tassi più alti.', 'Shock petrolifero: forte rischio di inflazione.'][st]
    norm = lambda s: s / s.dropna()[s.dropna().index >= me - pd.DateOffset(years=3)].iloc[0] * 100
    card('materie', 'Materie prime', 'Materie prime: petrolio, oro, argento', f_cm,
         _series(me, [('Petrolio', norm(oil), 'main'), ('Oro', norm(gold), 'second'), ('Argento', norm(silv), 'third')], ref=[{'y': 100, 'label': 'base 100'}]),
         'Il petrolio guida l\'inflazione e quindi i tassi; oro e argento sono beni rifugio. Grafico in base 100 di 3 anni fa.',
         'Variazione del petrolio in 3 mesi: verde se in calo, giallo fino a +10%, arancione fino a +25%, rosso oltre +25%.')

    # 14 cripto
    btc = px('BTC-USD')
    def f_bt(d):
        v = _at(btc, d); m2 = _at(ma(btc, 200), d); ddv = _dd(btc, d)
        st = (0 if ddv > -15 else 1) if v > m2 else (2 if ddv > -35 else 3)
        return st, _f(v, 0, ' $'), f'Bitcoin {_f(v, 0)} dollari, {"sopra" if v > m2 else "sotto"} la media a 200 giorni, {_f(ddv, 0, "%")} dal massimo di 12 mesi. ' + ['Trend positivo.', 'Trend positivo ma lontano dai massimi.', 'Sotto la media: debolezza.', 'Mercato ribassista: oltre −35% dai massimi.'][st]
    card('cripto', 'Cripto', 'Criptovalute (Bitcoin)', f_bt,
         _series(me, [('Bitcoin ($)', btc, 'main'), ('media 200 giorni', ma(btc, 200), 'ma')], log=True),
         'Il bitcoin è l\'attivo più speculativo: spesso anticipa la propensione al rischio degli investitori privati.',
         'Verde: sopra la media a 200 giorni e a meno del 15% dal massimo. Giallo: sopra la media ma più lontano. Arancione: sotto la media. Rosso: oltre −35% dai massimi.')

    # 15 stagionalità del mese che inizia
    mr = spx.dropna().resample('ME').last().pct_change() * 100
    mr = mr[(mr.index.year < me.year) | ((mr.index.year == me.year) & (mr.index <= me + pd.offsets.MonthEnd(0)))]
    nxt = (me.month % 12) + 1
    by = mr.groupby(mr.index.month)
    avg = by.mean(); pos = by.apply(lambda s: (s > 0).mean() * 100); cnt = by.count()
    def f_se(d):
        a = avg.get(nxt, np.nan); p = pos.get(nxt, np.nan)
        st = 0 if (a > 1 and p >= 65) else 1 if a > 0 else 2 if a > -1 else 3
        return st, _sg(a, 1, '% medio'), f'{MESI[nxt - 1].capitalize()} dal {mr.index[1].year}: rendimento medio dell\'S&P {_sg(a, 1, "%")}, positivo nel {_f(p, 0)}% degli anni ({int(cnt.get(nxt, 0))} casi). Mese del report ({MESI[me.month - 1]}): media storica {_sg(avg.get(me.month), 1, "%")}.'
    card('stagionalita', 'Azioni', f'Stagionalità: {MESI[nxt - 1]}', f_se,
         dict(type='bar', labels=[m[:3] for m in MESI], series=[{'name': 'Rendimento medio mensile S&P 500 (%)', 'role': 'main', 'values': [round(float(avg.get(k, np.nan)), 2) for k in range(1, 13)]}], highlight=nxt - 1, ref=[{'y': 0, 'label': '0'}]),
         'Media storica dei rendimenti dell\'S&P 500 per mese dell\'anno, calcolata sui dati disponibili. È una tendenza statistica, non una previsione.',
         'Verde: media oltre +1% e positivo in almeno 65% degli anni. Giallo: media positiva. Arancione: media tra 0 e −1%. Rosso: sotto −1%.')

    # ---------------------------------------------------------------- mercati azionari esteri
    n_us = len(cards)
    acwi = px('ACWI')
    def mk_market(id, tick, name):
        s = px(tick).dropna()
        if len(s) < 600: return
        mcl = s.resample('ME').last(); sma10 = mcl.rolling(10, min_periods=10).mean(); sig = (mcl > sma10).where(sma10.notna())
        sma_d = sma10.reindex(s.index, method='ffill')
        def last_sig(d):
            g = sig[sig.index <= d + pd.offsets.MonthEnd(0)].dropna()
            if not len(g): return None, None
            cur = bool(g.iloc[-1]); ch = g[g != cur]
            since = g.index[0] if not len(ch) else g[g.index > ch.index[-1]].index[0]
            return cur, since
        def f_mk(d):
            v = _at(s, d); buy, since = last_sig(d); m6 = _chg(s, d, 126); r6 = m6 - _chg(acwi, d, 126)
            a200 = v > _at(ma(s, 200), d); ddv = _dd(s, d)
            prior = s[(s.index <= d - pd.DateOffset(months=3)) & (s.index >= d - pd.DateOffset(years=5))]
            brk = len(prior) > 500 and v > prior.max()
            pts = int(bool(buy)) + int(m6 > 0) + int(r6 > 0) + int(a200)
            st = 0 if pts == 4 else 1 if pts == 3 else 2 if pts == 2 else 3
            if ddv <= -20: st = max(st, 2)
            if brk and st > 0 and buy: st -= 1
            sig_t = ('segnale automatico ' + ('Buy' if buy else 'Sell') + ' da ' + MESI[since.month - 1] + ' ' + str(since.year)) if since is not None else 'segnale non disponibile'
            txt = (f'{name} ({tick}, in dollari): {sig_t} (prezzo mensile {"sopra" if buy else "sotto"} la media di 10 mesi). '
                   f'Rendimento 6 mesi {_sg(m6, 1, "%")}, {_sg(r6, 1, " punti")} rispetto alla borsa mondiale (ACWI). '
                   f'{"Sopra" if a200 else "Sotto"} la media a 200 giorni, {_f(ddv, 1, "%")} dal massimo di 12 mesi.'
                   + (' Rottura al rialzo: prezzo sopra i massimi degli ultimi 5 anni.' if brk else ''))
            return st, ('Buy' if buy else 'Sell') + ' · 6m ' + _sg(m6, 0, '%'), txt
        # segnali Buy/Sell degli ultimi 5 anni per il grafico
        g = sig.dropna(); chg = g[g != g.shift(1)].iloc[1:]
        marks = [dict(d=s[s.index <= x].index[-1].strftime('%Y-%m-%d'), t='buy' if b else 'sell') for x, b in chg.items() if x >= me - pd.DateOffset(years=5) and x <= me + pd.offsets.MonthEnd(0) and (s.index <= x).any()]
        ch = _series(me, [(name + ' (' + tick + ', $)', s, 'main'), ('media 10 mesi', sma_d, 'ma')], marks=marks)
        card(id, 'Mercati esteri', name, f_mk, ch, WHAT_MK[id], HOW_MK, tgt=s, tgt_name=name + ' (' + tick + ')', area='estero')
    mk_market('m_eu', 'VGK', 'Europa')
    mk_market('m_cn', 'FXI', 'Cina')
    mk_market('m_jp', 'EWJ', 'Giappone')
    mk_market('m_em', 'EEM', 'Mercati emergenti')
    # rotazione Stati Uniti / resto del mondo
    r_us = px('SPY') / px('ACWX')
    def f_us(d):
        v = _at(r_us, d); m2 = _at(ma(r_us, 200), d); c6 = _chg(r_us, d, 126)
        st = _state_trend(v > m2, c6 > 0)
        return st, _sg(c6, 1, '% in 6 mesi'), (f'Rapporto Stati Uniti / resto del mondo (SPY/ACWX) {"sopra" if v > m2 else "sotto"} la media a 200 giorni, {_sg(c6, 1, "%")} in 6 mesi: '
                + ['la borsa americana guida ancora.', 'gli Stati Uniti restano davanti ma il vantaggio si riduce.', 'il resto del mondo ha preso la guida, ma gli Stati Uniti stanno recuperando.', 'il resto del mondo batte gli Stati Uniti: rotazione in corso fuori dall\'America.'][st])
    card('m_rot', 'Mercati esteri', 'Stati Uniti contro resto del mondo', f_us,
         _series(me, [('SPY / ACWX', r_us, 'main'), ('media 200 giorni', ma(r_us, 200), 'ma')]),
         'Rapporto tra l\'ETF sull\'S&P 500 (SPY) e quello sulle borse mondiali senza Stati Uniti (ACWX): se sale, l\'America fa meglio del resto del mondo.',
         'Verde: sopra la media e in salita (leadership americana). Giallo: sopra ma in calo. Arancione: sotto ma in recupero. Rosso: sotto e in calo (il resto del mondo guida).',
         area='estero')
    xc = cards[n_us:]; cards_us = cards[:n_us]

    # riepilogo del mese
    s_m = spx[(spx.index >= m0) & (spx.index <= me)]
    ret_m = (s_m.iloc[-1] / _at(spx, pe) - 1) * 100 if pe is not None else np.nan
    ytd0 = spx[spx.index < pd.Timestamp(me.year, 1, 1)].dropna()
    ret_y = (s_m.iloc[-1] / ytd0.iloc[-1] - 1) * 100 if len(ytd0) else np.nan
    ath = spx[spx.index <= me].max(); dd_m = (s_m.iloc[-1] / ath - 1) * 100
    sts = [c['status'] for c in cards_us]
    cnts = [sts.count(k) for k in range(4)]
    avg_st = float(np.mean(sts))
    overall = 0 if avg_st < .75 else 1 if avg_st < 1.4 else 2 if avg_st < 2.1 else 3
    worse = [c['title'] for c in cards_us if c['prev_status'] is not None and c['status'] > c['prev_status']]
    better = [c['title'] for c in cards_us if c['prev_status'] is not None and c['status'] < c['prev_status']]
    sev = sorted(cards_us, key=lambda c: -c['status'])
    recap = [c['title'] + ': ' + c['text'] for c in sev if c['status'] >= 2][:5]
    good = [c['title'] for c in cards_us if c['status'] == 0]
    head = (f'S&P 500 {_sg(ret_m, 1, "%")} a {MESI[me.month - 1]} ({_sg(ret_y, 1, "%")} da inizio anno), chiusura a {_f(s_m.iloc[-1], 0)} punti, '
            + ('sul massimo storico. ' if dd_m > -0.5 else f'{_f(dd_m, 1, "%")} dal massimo storico. ')
            + f'Su {len(cards_us)} indicatori del mercato americano: {cnts[0]} verdi, {cnts[1]} gialli, {cnts[2]} arancioni, {cnts[3]} rossi.')
    reds = [c['title'] for c in cards_us if c['status'] == 3]
    parere = ['Quadro favorevole: mantenere l\'esposizione prevista dal proprio piano, senza bisogno di interventi.',
              'Quadro nella norma con alcuni punti da seguire: mantenere l\'esposizione, senza aumentare il rischio; ricontrollare a metà mese.',
              'Quadro di attenzione: non aumentare l\'esposizione azionaria, rimandare nuovi acquisti importanti e ridurre le posizioni più rischiose se si è sopra il proprio livello di rischio.',
              'Quadro di rischio: ridurre il rischio secondo il proprio piano e aumentare la liquidità.'][overall]
    if reds: parere += ' Punti più delicati: ' + ', '.join(reds) + '.'
    mk = [c for c in xc if c['id'] != 'm_rot']
    pos_m = [c['title'] for c in mk if c['status'] <= 1]; neg_m = [c['title'] for c in mk if c['status'] >= 2]
    rot = next((c for c in xc if c['id'] == 'm_rot'), None)
    estero = None
    if mk:
        estero = ((('In tendenza positiva ' + ', '.join(pos_m)) if pos_m else 'Nessun mercato estero in tendenza positiva')
                  + ('; deboli ' + ', '.join(neg_m) if neg_m else '') + '. '
                  + ('' if rot is None else ['La borsa americana resta la più forte: nessun motivo di tendenza per spostarsi.', 'Gli Stati Uniti restano davanti ma il vantaggio si riduce: diversificare fuori dall\'America ha senso per chi è molto concentrato.', 'Il resto del mondo è davanti: chi ha solo azioni americane può valutare una quota estera nelle aree con segnale Buy.', 'Rotazione in corso fuori dagli Stati Uniti: le aree con segnale Buy sono candidate per una quota di diversificazione, con ingressi graduali.'][rot['status']]))
    return dict(parere=parere, month=month_name, month_key=me.strftime('%Y-%m'), end=me.strftime('%Y-%m-%d'), prev_end=None if pe is None else pe.strftime('%Y-%m-%d'),
                generated_for=str(today), overall=overall, counts=cnts, headline=head,
                spx=dict(close=round(float(s_m.iloc[-1]), 2), ret_m=None if np.isnan(ret_m) else round(ret_m, 2), ret_ytd=None if np.isnan(ret_y) else round(ret_y, 2), from_ath=round(dd_m, 2),
                         hi=round(float(s_m.max()), 2), lo=round(float(s_m.min()), 2)),
                recap=recap, good=good, worse=worse, better=better, cards=cards, estero=estero, xcounts=[[c['status'] for c in xc].count(k) for k in range(4)])


def safe(fn, *a):
    try:
        return fn(*a)
    except Exception as e:
        print('WARN', fn.__name__, e); return None

def load_quote(f):
    qp = os.path.join(RAW, 'quote.json')
    if not os.path.exists(qp): return None
    try:
        q = json.load(open(qp))
    except Exception:
        return None
    s = f['spx'].dropna()
    # chiusura precedente: penultima se la seduta di oggi è in corso, altrimenti l'ultima prima di oggi
    q['prev_close'] = float(s.iloc[-2]) if len(s) > 1 else None
    return q

def main():
    f = build(); P = scores(f)
    start = P['IFI'].first_valid_index()
    rep = []
    y = f['y10_60']; near = f['dd'] >= -0.05
    stats = {'auc': {}, 'auc_near': {}}
    for col, *_ in FACTORS + [(c[0],) for c in CONFIRM]:
        if col in P:
            stats['auc'][col] = round(auc(P[col], y), 3); stats['auc_near'][col] = round(auc(P[col][near], y[near]), 3)
    for c in ['FRAG', 'STRS', 'IFI']:
        stats['auc'][c] = round(auc(P[c], y), 3); stats['auc_near'][c] = round(auc(P[c][near], y[near]), 3)
    periods = [(str(start.date()), '2008-12-31'), ('2009-01-01', '2016-12-31'), ('2017-01-01', None)]
    stats['auc_periods'] = [dict(start=a, end=b or 'oggi', IFI=round(auc(P['IFI'].loc[a:b], y.loc[a:b]), 3),
                                 FRAG=round(auc(P['FRAG'].loc[a:b], y.loc[a:b]), 3), STRS=round(auc(P['STRS'].loc[a:b], y.loc[a:b]), 3))
                            for a, b in periods]
    bh = pd.Series(1.0, index=f.index)
    strat = {}
    for a, b in periods + [(str(start.date()), None)]:
        k = f"{a}..{b or 'oggi'}"
        strat[k] = {'buy_hold': backtest(f, bh, a, b),
                    'IFI>=70 -> 0%': backtest(f, 1 - hold(P['IFI'] >= 70), a, b),
                    'IFI>=70 o SPX<MA200 -> 0%': backtest(f, 1 - np.maximum(hold(P['IFI'] >= 70), f['trend_down']), a, b),
                    'SPX<MA200 -> 0%': backtest(f, 1 - f['trend_down'], a, b)}
    stats['strategies'] = strat
    stats['episodes_frag'] = episodes(f, (P['FRAG'] >= 75) & (f['dd'] >= -0.05))
    stats['episodes_ifi'] = episodes(f, P['IFI'] >= 70)
    stats['episodes_split'] = episodes(f, f['split'] >= 1, gap=63)
    stats['auc_ci'] = bootstrap_auc(P['IFI'], y)
    stats['auc_ci_near'] = bootstrap_auc(P['IFI'][near], y[near])
    # serie per dashboard
    keep_f = ['spx', 'dd', 'coverage', 'fdd60', 'cash'] + [c for c, *_ in FACTORS] + [c[0] for c in CONFIRM if c[0] in f] + ['hy_oas', 'baa', 'nh10', 'pct50', 'corr63', 'disp21', 'nl', 'nh', 'split', 'ma200', 'trend_down']
    S = f[keep_f].join(P.add_prefix('p_')).loc[start:]
    S.to_csv(os.path.join(OUT, 'ifi_serie.csv'), float_format='%.4f')
    cols = list(S.columns)
    # precisione per colonna: percentili a 1 decimale, prezzi a 2, il resto a 4 (file più leggero, nessuna perdita utile)
    DEC = [1 if c.startswith('p_') or c in ('coverage', 'pct200', 'near_hi', 'pct50') else 2 if c in ('spx', 'ma200', 'vix', 'move') else 0 if c in ('split', 'trend_down') else 4 for c in cols]
    def enc(v, k=4):
        if v is None or (isinstance(v, float) and np.isnan(v)): return None
        r = round(float(v), k); return int(r) if k == 0 else r
    data = {
        'version': MODEL_VERSION,
        'generated_at': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'as_of': S.index[-1].strftime('%Y-%m-%d'),
        'partial': PARTIAL,
        'quote': load_quote(f),
        'dates': [d.strftime('%Y-%m-%d') for d in S.index],
        'cols': cols,
        'rows': [[enc(v, k) for v, k in zip(row, DEC)] for row in S.to_numpy()],
        'factors': [dict(id=c, dir=s, group=g, name=n, desc=ds, w=WEIGHTS.get(c, 1.0)) for c, s, g, n, ds in FACTORS],
        'confirm': [dict(id=c, dir=s, name=n, desc=ds) for c, s, n, ds in CONFIRM if c in f],
        'stats': stats,
        'holdings': safe(load_holdings, C_ALL),
        'monthly': safe(build_report, f, P, C_ALL),
    }
    with open(os.path.join(OUT, 'ifi_data.json'), 'w') as fh:
        json.dump(data, fh, separators=(',', ':'), allow_nan=False)
    last = S.iloc[-1]
    rep.append(f"IFI {MODEL_VERSION} — dati al {data['as_of']}")
    rep.append(f"IFI {last['p_IFI']:.0f}  Fragilità {last['p_FRAG']:.0f}  Stress {last['p_STRS']:.0f}  S&P {last['spx']:.2f}  copertura {last['coverage']:.0f}%")
    rep.append(json.dumps(stats['auc_periods']))
    rep.append(json.dumps(strat, indent=1))
    open(os.path.join(OUT, 'ifi_report.txt'), 'w').write('\n'.join(rep))
    print('\n'.join(rep[:3]))

if __name__ == '__main__':
    main()
