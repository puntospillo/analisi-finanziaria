/* Versione locale: i dati sono file .js nella cartella dati/, così la pagina si apre con un doppio clic, senza server e senza internet */
(function () {
  const F = {}, W = {};
  window.AF_LOCAL = true;
  window.AF_FILE = (p, d) => { F[p] = d; };
  const load = p => { if (p in F) return Promise.resolve(F[p]); if (W[p]) return W[p];
    return W[p] = new Promise((res, rej) => { const s = document.createElement('script'); s.src = 'dati/' + p.replace(/\.(json|png)$/, '.js');
      s.onload = () => (p in F) ? res(F[p]) : rej(new Error('file vuoto: ' + p)); s.onerror = () => { delete W[p]; rej(new Error('file mancante: ' + p)); }; document.head.append(s); }); };
  const real = window.fetch ? window.fetch.bind(window) : null;
  window.fetch = (u, o) => {
    if (typeof u !== 'string' || /^(https?:|data:|blob:)/.test(u)) return real(u, o);
    return load(u).then(d => ({ok: true, status: 200, json: async () => d, blob: async () => (await real(d)).blob()}), e => ({ok: false, status: 404, json: async () => null}));
  };
})();
