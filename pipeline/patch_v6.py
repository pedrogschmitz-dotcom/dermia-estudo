p = "app/index.html"; s = open(p, encoding="utf8").read()
def rep(a, b, cnt=1):
    global s
    assert s.count(a) == cnt, (s.count(a), a[:70]); s = s.replace(a, b)
# ---- CSS do editor ----
rep('@media (prefers-reduced-motion:reduce)', '''.edwrap{position:relative;margin:10px auto 12px;border-radius:14px;overflow:hidden;touch-action:none;background:#000;line-height:0}
.edwrap canvas{display:block;width:100%;height:auto}
#ed-box{position:absolute;border:2px solid var(--accent);border-radius:6px;box-shadow:0 0 0 9999px rgba(10,10,10,.58);cursor:move}
#ed-box::before,#ed-box::after{content:"";position:absolute;inset:33.3% 0;border-top:1px solid rgba(255,255,255,.28);border-bottom:1px solid rgba(255,255,255,.28)}
#ed-box::after{inset:0 33.3%;border:0;border-left:1px solid rgba(255,255,255,.28);border-right:1px solid rgba(255,255,255,.28)}
#ed-box i{position:absolute;right:-9px;bottom:-9px;width:18px;height:18px;border-radius:50%;background:var(--accent);border:3px solid var(--ink)}
input[type=range]{width:100%;accent-color:#E8650A;margin:4px 0 12px}
.edrow{display:flex;align-items:center;gap:10px;font-size:12.5px;color:var(--mute)}
.set .row input[type=checkbox]{width:22px;height:22px;accent-color:#E8650A}
@media (prefers-reduced-motion:reduce)''')
# ---- HTML do editor ----
rep('<div id="loading" class="card loading hide">', '''<div id="editor" class="card hide">
    <span class="eyebrow">Ajuste o recorte</span>
    <div id="ed-note" class="sub" style="margin:4px 0 0">Deixe a lesão inteira dentro do quadrado, com um pouco de pele em volta. Arraste para mover; use dois dedos ou a barra para o tamanho.</div>
    <div id="ed-wrap" class="edwrap"><canvas id="ed-cv"></canvas><div id="ed-box"><i></i></div></div>
    <div class="edrow"><span>menor</span><input id="ed-size" type="range" min="0" max="1000" value="500" aria-label="Tamanho do recorte"><span>maior</span></div>
    <div class="two"><button id="ed-auto" class="btn ghost">Automático</button><button id="ed-go" class="btn">Analisar</button></div>
    <div style="text-align:center;margin-top:6px"><button id="ed-back" class="link">Trocar foto</button></div>
  </div>

  <div id="loading" class="card loading hide">''')
rep('<div class="lens"><div class="ring"><i></i></div><span>Deixe a lesão no centro. O modelo lê o quadrado central.</span></div>',
    '<div class="lens"><div class="ring"><i></i></div><span>O app encontra a lesão e você ajusta o recorte.</span></div>')
# ---- Ajustes: pular editor ----
rep('<button class="row" id="off">', '<label class="row" for="ed-skip"><span>Analisar direto, sem ajustar o recorte</span><input id="ed-skip" type="checkbox"></label>\n    <button class="row" id="off">')

# ---- JS: decodificar, recorte automático, recorte final ----
i0 = s.index('async function toCrop(file) {'); i1 = s.index('function toTensor(rgb, view) {')
s = s[:i0] + '''async function decodeImage(file) {               // devolve { data RGBA, w, h, canvas } com fotos grandes reduzidas pela metade até <= 1024 px
  let bmp, url = null; try { bmp = await createImageBitmap(file, { imageOrientation: "from-image" }); }
  catch (e) { url = URL.createObjectURL(file); bmp = await new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = () => rej(new Error("não consegui abrir a imagem")); im.src = url; }); }
  let w = bmp.width || bmp.naturalWidth, h = bmp.height || bmp.naturalHeight; if (!w || !h) throw new Error("imagem vazia");
  if (Math.min(w, h) < 224) throw new Error("imagem pequena demais (menor que 224 px)");
  let src = bmp;
  while (Math.max(w, h) > 1024 && Math.min(w, h) >= 448) { const c = document.createElement("canvas"); c.width = Math.floor(w / 2); c.height = Math.floor(h / 2); const g = c.getContext("2d"); g.imageSmoothingQuality = "high"; g.drawImage(src, 0, 0, c.width, c.height); src = c; w = c.width; h = c.height; }
  const c0 = document.createElement("canvas"); c0.width = w; c0.height = h; const g0 = c0.getContext("2d", { willReadFrequently: true }); g0.drawImage(src, 0, 0, w, h);
  const data = g0.getImageData(0, 0, w, h).data; if (url) URL.revokeObjectURL(url); if (bmp.close) bmp.close();
  return { data, w, h, canvas: c0 };
}
function otsu(vals) { const hst = new Float64Array(256); vals.forEach(v => hst[Math.min(255, Math.max(0, v | 0))]++); const n = vals.length; let w = 0, m = 0, mt = 0; for (let i = 0; i < 256; i++) mt += i * hst[i] / n;
  let best = 0, bi = 0; for (let i = 0; i < 256; i++) { w += hst[i] / n; m += i * hst[i] / n; if (w <= 0 || w >= 1) continue; const v = (mt * w - m) ** 2 / (w * (1 - w)); if (v > best) { best = v; bi = i; } } return bi; }
function autoBox(dec) {                           // mesma lógica do treino (autocrop.py): lesão = componente escuro central (Otsu), quadrado com margem 1,35
  const W = dec.w, H = dec.h, sc = 256 / Math.max(W, H), w = Math.max(1, Math.round(W * sc)), h = Math.max(1, Math.round(H * sc));
  const c = document.createElement("canvas"); c.width = w; c.height = h; const g = c.getContext("2d", { willReadFrequently: true }); g.drawImage(dec.canvas, 0, 0, w, h); const d = g.getImageData(0, 0, w, h).data, N = w * h, L = new Float32Array(N);
  for (let i = 0; i < N; i++) L[i] = 0.299 * d[i * 4] + 0.587 * d[i * 4 + 1] + 0.114 * d[i * 4 + 2];
  const valid = new Uint8Array(N).fill(1), st = [];                       // tira a moldura preta do dermatoscópio (escuro ligado à borda)
  for (let x = 0; x < w; x++) st.push(x, (h - 1) * w + x); for (let y = 0; y < h; y++) st.push(y * w, y * w + w - 1);
  while (st.length) { const i = st.pop(); if (!valid[i] || L[i] >= 35) continue; valid[i] = 0; const x = i % w, y = (i / w) | 0; if (x > 0) st.push(i - 1); if (x < w - 1) st.push(i + 1); if (y > 0) st.push(i - w); if (y < h - 1) st.push(i + w); }
  let nv = 0; const vv = []; for (let i = 0; i < N; i++) if (valid[i]) { nv++; vv.push(L[i]); } if (nv < 0.2 * N) return null;
  const t = otsu(vv); let m = new Uint8Array(N); for (let i = 0; i < N; i++) m[i] = valid[i] && L[i] < t ? 1 : 0;
  const morph = (a, er) => { const o = new Uint8Array(N); for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { const i = y * w + x, nb = [x > 0 ? a[i - 1] : 0, x < w - 1 ? a[i + 1] : 0, y > 0 ? a[i - w] : 0, y < h - 1 ? a[i + w] : 0];
    o[i] = er ? (a[i] && nb.every(Boolean) ? 1 : 0) : (a[i] || nb.some(Boolean) ? 1 : 0); } return o; };
  m = morph(morph(m, 1), 1); m = morph(morph(m, 0), 0);
  const lab = new Int32Array(N); let n = 0, best = -1, bk = 0; const comps = [], cy = h / 2, cx = w / 2, sig = 0.35 * Math.min(w, h);
  for (let i = 0; i < N; i++) { if (!m[i] || lab[i]) continue; n++; let a = 0, sy = 0, sx = 0, x0 = w, x1 = 0, y0 = h, y1 = 0; const q = [i]; lab[i] = n;
    while (q.length) { const j = q.pop(), x = j % w, y = (j / w) | 0; a++; sx += x; sy += y; if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y;
      for (const k of [x > 0 ? j - 1 : -1, x < w - 1 ? j + 1 : -1, y > 0 ? j - w : -1, y < h - 1 ? j + w : -1]) if (k >= 0 && m[k] && !lab[k]) { lab[k] = n; q.push(k); } }
    const sco = a * Math.exp(-(((sy / a) - cy) ** 2 + ((sx / a) - cx) ** 2) / (2 * sig * sig)); comps.push({ a, x0, x1: x1 + 1, y0, y1: y1 + 1 }); if (sco > best) { best = sco; bk = comps.length - 1; } }
  if (!comps.length) return null; const k = comps[bk], frac = k.a / nv; if (frac < 0.01 || frac > 0.85) return null;
  let side = Math.max(k.x1 - k.x0, k.y1 - k.y0) * 1.35; side = Math.max(side, 0.30 * Math.min(w, h)); side = Math.min(side, Math.min(w, h));
  const mx = (k.x0 + k.x1) / 2, my = (k.y0 + k.y1) / 2, bx = Math.min(Math.max(mx - side / 2, 0), w - side), by = Math.min(Math.max(my - side / 2, 0), h - side);
  let S = Math.min(Math.round(side / sc), W, H), X = Math.round(bx / sc), Y = Math.round(by / sc); X = Math.min(Math.max(X, 0), W - S); Y = Math.min(Math.max(Y, 0), H - S); return { x: X, y: Y, s: S };
}
function centerBox(dec) { const S = Math.min(dec.w, dec.h); return { x: Math.floor((dec.w - S) / 2), y: Math.floor((dec.h - S) / 2), s: S }; }
function makeCrop(dec, b) {                       // recorte final 224x224 (bicúbico igual ao treino); sem caixa = lado menor 224 + centro
  let rgb;
  if (!b) { const { data, w, h } = dec, tw = w <= h ? 224 : Math.floor(224 * w / h), th = w <= h ? Math.floor(224 * h / w) : 224, full = resizeRGB(data, w, h, tw, th);
    const left = roundEven((tw - 224) / 2), top = roundEven((th - 224) / 2); rgb = new Uint8ClampedArray(224 * 224 * 3);
    for (let y = 0; y < 224; y++) rgb.set(full.subarray(((y + top) * tw + left) * 3, ((y + top) * tw + left + 224) * 3), y * 224 * 3); }
  else { const S = b.s, reg = new Uint8ClampedArray(S * S * 4); for (let y = 0; y < S; y++) reg.set(dec.data.subarray(((b.y + y) * dec.w + b.x) * 4, ((b.y + y) * dec.w + b.x + S) * 4), y * S * 4); rgb = resizeRGB(reg, S, S, 224, 224); }
  const canvas = document.createElement("canvas"); canvas.width = 224; canvas.height = 224; const id = new ImageData(224, 224);
  for (let i = 0; i < 224 * 224; i++) { id.data[i * 4] = rgb[i * 3]; id.data[i * 4 + 1] = rgb[i * 3 + 1]; id.data[i * 4 + 2] = rgb[i * 3 + 2]; id.data[i * 4 + 3] = 255; }
  canvas.getContext("2d").putImageData(id, 0, 0); return { rgb, canvas };
}
''' + s[i1:]

# ---- fluxo: foto -> editor -> análise ----
rep('const onPhoto = async ev => {\n  const f = ev.target.files[0]; ev.target.value = ""; if (!f || !session || busy) return; busy = true;',
'''let DEC = null, BOX = null, AUTO = null;
const ed = { min: 64, max: 0 };
function edDraw() { const wr = $("ed-wrap"), cv = $("ed-cv"), r = cv.getBoundingClientRect(), k = r.width / DEC.w, bx = $("ed-box");
  bx.style.left = BOX.x * k + "px"; bx.style.top = BOX.y * k + "px"; bx.style.width = bx.style.height = BOX.s * k + "px"; $("ed-size").value = Math.round(1000 * (BOX.s - ed.min) / Math.max(1, ed.max - ed.min)); }
function edSet(cx, cy, S) { S = Math.round(Math.min(ed.max, Math.max(ed.min, S))); let x = Math.round(cx - S / 2), y = Math.round(cy - S / 2); x = Math.min(Math.max(x, 0), DEC.w - S); y = Math.min(Math.max(y, 0), DEC.h - S); BOX = { x, y, s: S }; edDraw(); }
function openEditor() {
  const cv = $("ed-cv"); cv.width = DEC.w; cv.height = DEC.h; cv.getContext("2d").drawImage(DEC.canvas, 0, 0); $("ed-wrap").style.maxWidth = Math.min(1, (window.innerHeight * 0.52) / DEC.h * DEC.w / ($("editor").clientWidth || 360)) * 100 + "%";
  ed.max = Math.min(DEC.w, DEC.h); ed.min = Math.max(48, Math.round(0.06 * ed.max)); $("ed-note").textContent = AUTO ? "Encontrei a lesão. Confira se ela está inteira dentro do quadrado, com um pouco de pele em volta. Arraste para mover; dois dedos ou a barra mudam o tamanho." : "Não encontrei a lesão sozinho: posicione o quadrado sobre ela. Arraste para mover; dois dedos ou a barra mudam o tamanho.";
  show($("entrada"), false); show($("editor"), true); requestAnimationFrame(edDraw); $("editor").scrollIntoView({ behavior: "smooth", block: "start" });
}
(() => { const box = $("ed-box"), pts = new Map(); let start = null;
  const k = () => $("ed-cv").getBoundingClientRect().width / DEC.w;
  const snap = () => { const a = [...pts.values()]; return { a, b: BOX ? { ...BOX } : null, d: a.length > 1 ? Math.hypot(a[0].x - a[1].x, a[0].y - a[1].y) : 0, c: a.length > 1 ? { x: (a[0].x + a[1].x) / 2, y: (a[0].y + a[1].y) / 2 } : a[0] }; };
  $("ed-wrap").addEventListener("pointerdown", e => { if (!DEC) return; $("ed-wrap").setPointerCapture(e.pointerId); pts.set(e.pointerId, { x: e.clientX, y: e.clientY }); start = snap(); e.preventDefault(); });
  $("ed-wrap").addEventListener("pointermove", e => { if (!pts.has(e.pointerId) || !start) return; pts.set(e.pointerId, { x: e.clientX, y: e.clientY }); const now = snap(), kk = k(), b = start.b;
    if (now.a.length > 1 && start.d > 0) edSet(b.x + b.s / 2 + (now.c.x - start.c.x) / kk, b.y + b.s / 2 + (now.c.y - start.c.y) / kk, b.s * now.d / start.d);
    else edSet(b.x + b.s / 2 + (now.c.x - start.c.x) / kk, b.y + b.s / 2 + (now.c.y - start.c.y) / kk, b.s); });
  const up = e => { pts.delete(e.pointerId); start = pts.size ? snap() : null; }; $("ed-wrap").addEventListener("pointerup", up); $("ed-wrap").addEventListener("pointercancel", up);
  $("ed-size").addEventListener("input", () => { if (!BOX) return; edSet(BOX.x + BOX.s / 2, BOX.y + BOX.s / 2, ed.min + (ed.max - ed.min) * $("ed-size").value / 1000); });
  window.addEventListener("resize", () => { if (DEC && !$("editor").classList.contains("hide")) edDraw(); });
})();
$("ed-auto").onclick = () => { BOX = AUTO ? { ...AUTO } : centerBox(DEC); edDraw(); };
$("ed-back").onclick = () => { show($("editor"), false); show($("entrada"), true); DEC = null; };
$("ed-go").onclick = () => { show($("editor"), false); show($("entrada"), true); analyze(); };
let SKIP = false; try { SKIP = localStorage.getItem("dermia_skip") === "1"; } catch (e) {} $("ed-skip").checked = SKIP;
$("ed-skip").onchange = () => { SKIP = $("ed-skip").checked; try { localStorage.setItem("dermia_skip", SKIP ? "1" : "0"); } catch (e) {} };
const onPhoto = async ev => {
  const f = ev.target.files[0]; ev.target.value = ""; if (!f || !session || busy) return;
  try { DEC = await decodeImage(f); AUTO = autoBox(DEC); BOX = AUTO ? { ...AUTO } : centerBox(DEC); }
  catch (e) { $("st").textContent = ""; alert("Não consegui abrir a foto: " + (e && e.message ? e.message : e)); return; }
  if (SKIP) analyze(); else openEditor();
};
const analyze = async () => {
  if (!DEC || busy) return; busy = true;''')
rep('const t0 = performance.now(), crop = await toCrop(f);', 'const t0 = performance.now(), crop = makeCrop(DEC, BOX);')
open(p, "w", encoding="utf8").write(s); print("ok")
