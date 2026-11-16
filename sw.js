// DermIA: cache por versão. Troque APP ao publicar dados ou página novos; STATIC só quando mudar vendor/fontes/ícones.
const STATIC = "dermia-static-2", APP = "dermia-app-__VERSAO__";   // o deploy troca __VERSAO__ pelo commit: cada publicação vira atualização automática
const STATIC_FILES = ["vendor/ort.wasm.min.js", "vendor/ort-wasm-simd-threaded.wasm", "vendor/ort-wasm-simd-threaded.mjs", "fonts/unbounded-latin-600-normal.woff2", "fonts/unbounded-latin-800-normal.woff2", "fonts/instrument-sans-latin-500-normal.woff2", "fonts/instrument-sans-latin-700-normal.woff2", "icons/icon-180.png", "icons/icon-192.png", "icons/icon-512.png"];
const APP_FILES = ["./", "index.html", "manifest.webmanifest", "data/model.json", "data/model_w.bin", "data/bank.json", "data/bank.bin", "data/explain.json"];
self.addEventListener("install", e => {
  e.waitUntil((async () => {
    const st = await caches.open(STATIC); for (const f of STATIC_FILES) if (!(await st.match(f))) await st.add(f);
    const ap = await caches.open(APP); await ap.addAll(APP_FILES.map(f => new Request(f, { cache: "reload" })));
    await self.skipWaiting();
  })());
});
self.addEventListener("activate", e => {
  e.waitUntil((async () => {
    for (const k of await caches.keys()) if (k !== STATIC && k !== APP && !k.startsWith("dermia-thumbs-")) await caches.delete(k);
    await self.clients.claim();
  })());
});
self.addEventListener("fetch", e => {
  const r = e.request, u = new URL(r.url);
  // passam direto: outros sites, modelo criptografado (vai para o IndexedDB), miniaturas (faixa de bytes; a página consulta o cache offline)
  if (r.method !== "GET" || u.origin !== location.origin || u.pathname.includes("/model/") || u.pathname.includes("/thumbs/") || r.headers.has("range")) return;
  if (r.mode === "navigate") {   // página: rede primeiro (pega versão nova), cache se offline
    e.respondWith(fetch(r).then(net => { if (net.ok) caches.open(APP).then(c => c.put("index.html", net.clone())); return net; }).catch(async () => (await caches.match("index.html")) || Response.error()));
    return;
  }
  e.respondWith((async () => {
    const hit = await caches.match(r, { ignoreSearch: true }); if (hit) return hit;
    try { const net = await fetch(r); if (net.ok && net.type === "basic") (await caches.open(APP)).put(r, net.clone()); return net; }
    catch (err) { if (r.mode === "navigate") { const idx = await caches.match("index.html"); if (idx) return idx; } throw err; }
  })());
});
