# Aplica a v3 do front (modelo por regiões, pré-processamento exato, TTA, miniaturas por faixa, SW novo) em app/index.html
import re, sys
p = "app/index.html"; s = open(p, encoding="utf8").read()
def rep(a, b, cnt=1):
    global s
    assert s.count(a) == cnt, (s.count(a), a[:70]); s = s.replace(a, b)
def block(start, end, new):
    global s
    i0 = s.index(start); i1 = s.index(end, i0); s = s[:i0] + new + s[i1:]

# ---- cabeçalho: CSP (só no app; a cópia do artefato remove) ----
rep('<meta name="robots" content="noindex,nofollow">', '<meta name="robots" content="noindex,nofollow">\n<meta http-equiv="Content-Security-Policy" content="default-src \'self\'; script-src \'self\' \'unsafe-inline\' \'wasm-unsafe-eval\'; style-src \'self\' \'unsafe-inline\'; img-src \'self\' blob: data: https://isic-archive.s3.us-east-1.amazonaws.com; connect-src \'self\'; font-src \'self\'; worker-src \'self\' blob:; base-uri \'none\'; form-action \'none\'">')
rep('<div class="warn"><b>FERRAMENTA DE ESTUDO.', '<div id="upd" class="alert soft hide" style="cursor:pointer">Nova versão instalada. Toque aqui para recarregar.</div>\n  <div class="warn"><b>FERRAMENTA DE ESTUDO.')
rep('Cada quadrado = 16×16 px do recorte central 224×224. Mostra onde a evidência para o diagnóstico escolhido está, não prova nada sobre a lesão.', 'Cada quadrado = 16×16 px do recorte central 224×224. Mostra onde a evidência para o diagnóstico escolhido está, não prova nada sobre a lesão. A intensidade é comparável entre os diagnósticos dos botões. O modelo mistura informação entre regiões vizinhas, então a localização é aproximada.')
rep('<a href="#" id="rm" style="color:var(--m)">Remover modelo deste aparelho</a>', '<a href="#" id="off" style="color:var(--m)">Baixar miniaturas para uso offline</a> · <a href="#" id="rm" style="color:var(--m)">Remover modelo deste aparelho</a>')

# ---- estado e dados ----
rep('let session = null, HEAD = null, HF = null, EXP = null, BANK = null, BANKV = null;', 'let session = null, MODEL = null, W = null, HEAD = null, HF = null, EXP = null, BANK = null, BANKV = null;')
block('async function loadData() {', 'async function makeSession(bytes) {', '''async function getJSON(u) { const r = await fetch(u); if (!r.ok) throw new Error(u + " (" + r.status + ")"); return r.json(); }
async function getBin(u) { const r = await fetch(u); if (!r.ok) throw new Error(u + " (" + r.status + ")"); return r.arrayBuffer(); }
async function loadData() {
  const [m, w, bank, bv, exp] = await Promise.all([getJSON("data/model.json"), getBin("data/model_w.bin"), getJSON("data/bank.json"), getBin("data/bank.bin"), getJSON("data/explain.json")]);
  MODEL = m; W = new Float32Array(w); BANK = bank; BANKV = new Int8Array(bv); EXP = exp;
  if (W.length !== m.names.length * m.D) throw new Error("pesos do modelo com tamanho inesperado");
  if (BANKV.length !== bank.n * 512) throw new Error("banco de casos com tamanho inesperado");
  HF = { names: m.names, groups: m.groups, T: m.T, cv: m.cv }; HEAD = { names: m.gnames, pt: m.gpt, det: m.det };
}
''')
rep('ort.env.wasm.numThreads = self.crossOriginIsolated ? 2 : 1;', 'ort.env.wasm.numThreads = self.crossOriginIsolated ? Math.min(4, navigator.hardwareConcurrency || 2) : 1;')
rep('''  let bytes = null; try { bytes = await kvGet("model"); } catch (e) {}
  if (bytes) {''', '''  let bytes = null, sha = null; try { sha = await kvGet("model_sha"); if (sha === MODEL.model_sha) bytes = await kvGet("model"); } catch (e) {}
  if (sha && sha !== MODEL.model_sha) $("m-msg").textContent = "O modelo foi atualizado: instale de novo (mesma frase de acesso).";
  if (bytes) {''')
rep('try { await kvSet("model", out); if', 'try { await kvSet("model", out); await kvSet("model_sha", man.sha256); if')
rep('''try { const bytes = new Uint8Array(await f.arrayBuffer()); await makeSession(bytes); try { await kvSet("model", bytes); } catch (e) {} ready(); }''', '''try { const bytes = new Uint8Array(await f.arrayBuffer()); const h = Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", bytes))).map(x => x.toString(16).padStart(2, "0")).join("");
    if (h !== MODEL.model_sha) throw new Error("este não é o arquivo de modelo desta versão do app");
    await makeSession(bytes); try { await kvSet("model", bytes); await kvSet("model_sha", h); } catch (e) {} ready(); }''')
rep('d.transaction("kv", "readwrite").objectStore("kv").delete("model");', 'const os = d.transaction("kv", "readwrite").objectStore("kv"); os.delete("model"); os.delete("model_sha");')

# ---- pré-processamento exato (igual ao Pillow/torchvision usado no treino) ----
block('/* ---------- pré-processamento', '/* ---------- cálculo:', '''/* ---------- pré-processamento: mesmo algoritmo do treino (bicúbico com antialias do Pillow, lado menor 224, recorte central) ---------- */
function bic(x) { x = Math.abs(x); return x < 1 ? (1.5 * x - 2.5) * x * x + 1 : x < 2 ? (((x - 5) * x + 8) * x - 4) * -0.5 : 0; }
function coeffs(inSize, outSize) {
  const scale = inSize / outSize, fs = Math.max(scale, 1), sup = 2 * fs, res = new Array(outSize);
  for (let xx = 0; xx < outSize; xx++) {
    const c = (xx + 0.5) * scale; let x0 = Math.floor(c - sup + 0.5); if (x0 < 0) x0 = 0; let x1 = Math.floor(c + sup + 0.5); if (x1 > inSize) x1 = inSize;
    const n = x1 - x0, w = new Float64Array(n); let sum = 0; for (let x = 0; x < n; x++) { w[x] = bic((x + x0 - c + 0.5) / fs); sum += w[x]; }
    for (let x = 0; x < n; x++) { const k = w[x] / sum * 4194304; w[x] = k < 0 ? Math.ceil(k - 0.5) : Math.floor(k + 0.5); } res[xx] = [x0, w];   // coeficientes inteiros (22 bits), como no Pillow
  }
  return res;
}
function resizeRGB(src, w, h, tw, th) {           // src: RGBA Uint8ClampedArray -> RGB Uint8ClampedArray (tw x th); passo horizontal, depois vertical
  const cx = coeffs(w, tw), cy = coeffs(h, th), mid = new Uint8ClampedArray(h * tw * 3), out = new Uint8ClampedArray(th * tw * 3);
  for (let y = 0; y < h; y++) for (let x = 0; x < tw; x++) { const x0 = cx[x][0], k = cx[x][1]; let r = 0, g = 0, b = 0; for (let i = 0; i < k.length; i++) { const o = (y * w + x0 + i) * 4, c = k[i]; r += src[o] * c; g += src[o + 1] * c; b += src[o + 2] * c; } const o = (y * tw + x) * 3; mid[o] = Math.floor((r + 2097152) / 4194304); mid[o + 1] = Math.floor((g + 2097152) / 4194304); mid[o + 2] = Math.floor((b + 2097152) / 4194304); }
  for (let y = 0; y < th; y++) { const y0 = cy[y][0], k = cy[y][1]; for (let x = 0; x < tw; x++) { let r = 0, g = 0, b = 0; for (let i = 0; i < k.length; i++) { const o = ((y0 + i) * tw + x) * 3, c = k[i]; r += mid[o] * c; g += mid[o + 1] * c; b += mid[o + 2] * c; } const o = (y * tw + x) * 3; out[o] = Math.floor((r + 2097152) / 4194304); out[o + 1] = Math.floor((g + 2097152) / 4194304); out[o + 2] = Math.floor((b + 2097152) / 4194304); } }
  return out;
}
function roundEven(x) { const r = Math.round(x); return (Math.abs(x % 1) === 0.5 && r % 2) ? r - 1 : r; }
async function toCrop(file) {                     // devolve { rgb: Uint8ClampedArray(224*224*3), canvas }
  let bmp, url = null; try { bmp = await createImageBitmap(file, { imageOrientation: "from-image" }); }
  catch (e) { url = URL.createObjectURL(file); bmp = await new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = () => rej(new Error("não consegui abrir a imagem")); im.src = url; }); }
  let w = bmp.width || bmp.naturalWidth, h = bmp.height || bmp.naturalHeight; if (!w || !h) throw new Error("imagem vazia");
  if (Math.min(w, h) < 224) throw new Error("imagem pequena demais (menor que 224 px)");
  let src = bmp;                                    // fotos grandes: reduz pela metade no canvas até o lado maior ficar <= 1024
  while (Math.max(w, h) > 1024 && Math.min(w, h) >= 448) { const c = document.createElement("canvas"); c.width = Math.floor(w / 2); c.height = Math.floor(h / 2); const g = c.getContext("2d"); g.imageSmoothingQuality = "high"; g.drawImage(src, 0, 0, c.width, c.height); src = c; w = c.width; h = c.height; }
  const c0 = document.createElement("canvas"); c0.width = w; c0.height = h; const g0 = c0.getContext("2d", { willReadFrequently: true }); g0.drawImage(src, 0, 0, w, h);
  const data = g0.getImageData(0, 0, w, h).data; if (url) URL.revokeObjectURL(url); if (bmp.close) bmp.close();
  const tw = w <= h ? 224 : Math.floor(224 * w / h), th = w <= h ? Math.floor(224 * h / w) : 224, full = resizeRGB(data, w, h, tw, th);
  const left = roundEven((tw - 224) / 2), top = roundEven((th - 224) / 2), rgb = new Uint8ClampedArray(224 * 224 * 3);
  for (let y = 0; y < 224; y++) rgb.set(full.subarray(((y + top) * tw + left) * 3, ((y + top) * tw + left + 224) * 3), y * 224 * 3);
  const canvas = document.createElement("canvas"); canvas.width = 224; canvas.height = 224; const id = new ImageData(224, 224);
  for (let i = 0; i < 224 * 224; i++) { id.data[i * 4] = rgb[i * 3]; id.data[i * 4 + 1] = rgb[i * 3 + 1]; id.data[i * 4 + 2] = rgb[i * 3 + 2]; id.data[i * 4 + 3] = 255; }
  canvas.getContext("2d").putImageData(id, 0, 0); return { rgb, canvas };
}
function toTensor(rgb, view) {                    // view: "id" ou "h" (espelhada)
  const m = [0.48145466, 0.4578275, 0.40821073], sd = [0.26862954, 0.26130258, 0.27577711], a = new Float32Array(3 * 224 * 224), flip = view === "h";
  for (let y = 0; y < 224; y++) for (let x = 0; x < 224; x++) { const s = (y * 224 + (flip ? 223 - x : x)) * 3, d = y * 224 + x; for (let k = 0; k < 3; k++) a[k * 50176 + d] = (rgb[s + k] / 255 - m[k]) / sd[k]; }
  return new ort.Tensor("float32", a, [1, 3, 224, 224]);
}

''')

# ---- cálculo ----
block('function headLogits(emb) {', 'function softmax(L, T)', '''function feats(tok) {                             // 196x768 -> média global + média de cada quadrante (5 x 768)
  const D = 768, f = new Float64Array(5 * D);
  for (let i = 0; i < 196; i++) { const q = (((i / 14) | 0) < 7 ? 0 : 2) + (i % 14 < 7 ? 0 : 1), o = i * D, qo = (1 + q) * D; for (let j = 0; j < D; j++) { const v = tok[o + j]; f[j] += v; f[qo + j] += v; } }
  for (let j = 0; j < D; j++) f[j] /= 196; for (let j = D; j < 5 * D; j++) f[j] /= 49; return f;
}
function headLogits(f) { const K = MODEL.names.length, D = MODEL.D, L = new Float64Array(K); for (let k = 0; k < K; k++) { let s = MODEL.b[k]; const o = k * D; for (let j = 0; j < D; j++) s += W[o + j] * f[j]; L[k] = s; } return L; }
''')
block('function heatContrib(tok) {', 'function neighbors(emb, K) {', '''function heatFor(k) {                             // contribuição exata de cada quadrado ao logit do diagnóstico k (média das vistas, desfazendo o espelho)
  if (LAST.hc[k]) return LAST.hc[k]; const D = 768, o = k * MODEL.D, out = new Float64Array(196), u = new Float64Array(D);
  for (let q = 0; q < 4; q++) { for (let j = 0; j < D; j++) u[j] = W[o + j] / 196 + W[o + (1 + q) * D + j] / 49;
    for (const v of LAST.toks) for (let i = 0; i < 196; i++) { const r = (i / 14) | 0, c = i % 14; if (((r < 7 ? 0 : 2) + (c < 7 ? 0 : 1)) !== q) continue; let d = 0; const t = i * D; for (let j = 0; j < D; j++) d += v.tok[t + j] * u[j]; out[r * 14 + (v.view === "h" ? 13 - c : c)] += d / LAST.toks.length; } }
  return (LAST.hc[k] = out);
}
''')
block('function drawHeat() {', 'function renderChips(order) {', '''function drawHeat() {
  const hc = $("cv-heat"), g = hc.getContext("2d"); g.clearRect(0, 0, 448, 448);
  if (!showHeat || !LAST) return;
  let mx = 1e-9; LAST.order.slice(0, 4).forEach(k => heatFor(k).forEach(v => { mx = Math.max(mx, Math.abs(v)); }));   // mesma escala para os 4 botões
  const vals = heatFor(curClass), sm = document.createElement("canvas"); sm.width = 14; sm.height = 14; const sg = sm.getContext("2d"), id = sg.createImageData(14, 14);
  for (let i = 0; i < 196; i++) { const v = vals[i] / mx, a = Math.min(1, Math.pow(Math.abs(v), 0.8)) * 0.78, c = v >= 0 ? [232, 101, 10] : [60, 130, 255]; id.data[i * 4] = c[0]; id.data[i * 4 + 1] = c[1]; id.data[i * 4 + 2] = c[2]; id.data[i * 4 + 3] = Math.round(a * 255); }
  sg.putImageData(id, 0, 0); g.imageSmoothingEnabled = true; g.imageSmoothingQuality = "high"; g.drawImage(sm, 0, 0, 448, 448);
}
''')

# ---- miniaturas: faixa de bytes (Range), cache offline opcional, sem vazar URLs ----
block('let TIDX = null; const TBUF = {};', 'function renderNeigh(nn, ctx) {', '''const TBUF = {}, TURL = {};
async function thumbURL(it) {
  if (!it.t) return null; if (TURL[it.id]) return TURL[it.id]; const [ch, off, len] = it.t, u = "thumbs/t" + ch + ".bin";
  try {
    let buf = null;
    if (TBUF[ch]) buf = (await TBUF[ch]).slice(off, off + len);
    else {
      let hit = null; try { hit = self.caches ? await caches.match(u) : null; } catch (e) {}
      if (hit) { TBUF[ch] = hit.arrayBuffer(); buf = (await TBUF[ch]).slice(off, off + len); }
      else { const r = await fetch(u, { headers: { Range: "bytes=" + off + "-" + (off + len - 1) } }); if (!r.ok) return null;
        if (r.status === 206) buf = await r.arrayBuffer(); else { TBUF[ch] = r.arrayBuffer(); buf = (await TBUF[ch]).slice(off, off + len); } }
    }
    return (TURL[it.id] = URL.createObjectURL(new Blob([buf], { type: "image/jpeg" })));
  } catch (x) { return null; }
}
''')
rep('const it = BANK.items[i], d = document.createElement("div"); d.className = "cs";', 'const it = BANK.items[i], d = document.createElement("div"), dx = it.f >= 0 ? HF.names[it.f] : it.dx; d.className = "cs";')
rep('thumbURL(it.id).then(u => { im.src = u || th; });', 'thumbURL(it).then(u => { im.src = u || th; });')
rep('const u = await thumbURL(it.id);', 'const u = await thumbURL(it);')
n_dx = s.count('esc(it.dx)'); assert n_dx >= 2, n_dx; s = s.replace('esc(it.dx)', 'esc(dx)')

# ---- contexto: expoentes calibrados ----
rep('for (let k = 0; k < p.length; k++) f[k] *= factor(d, v, k); });', 'const al = (MODEL.ctx && MODEL.ctx.alpha && MODEL.ctx.alpha[d] != null) ? MODEL.ctx.alpha[d] : 1; if (!(al > 0)) return; used.push(lab); for (let k = 0; k < p.length; k++) f[k] *= Math.pow(factor(d, v, k), al); });')
rep('dims.forEach(([d, v, lab]) => { if (!v || !lab) return; used.push(lab); const al', 'dims.forEach(([d, v, lab]) => { if (!v || !lab) return; const al')
rep('pela frequência de cada diagnóstico nesses grupos no ISIC (supõe que cada fator é independente; o ISIC é um banco de referência, não da população).', 'pela frequência de cada diagnóstico nesses grupos no ISIC, com peso reduzido e calibrado nos testes (o ISIC é um banco de referência, não da população).')

# ---- fluxo principal ----
block('$("foto").onchange = async ev => {', 'if ("serviceWorker" in navigator)', '''$("foto").onchange = async ev => {
  const f = ev.target.files[0]; ev.target.value = ""; if (!f || !session || busy) return; busy = true;
  show($("res"), false); show($("loading"), true); $("load-txt").textContent = "Analisando… (a primeira foto da sessão demora mais)";
  await new Promise(r => setTimeout(r, 30));
  try {
    const t0 = performance.now(), crop = await toCrop(f); $("cv-base").getContext("2d").drawImage(crop.canvas, 0, 0, 448, 448);
    const toks = [], fm = new Float64Array(MODEL.D); let emb = null;
    for (const view of MODEL.views) {                // vistas (normal e espelhada): média das características = média dos logits
      const out = await session.run({ img: toTensor(crop.rgb, view) }); if (view === "id") emb = Float32Array.from(out.emb.data);
      const tok = Float32Array.from(out.tok.data), fv = feats(tok); for (let j = 0; j < fm.length; j++) fm[j] += fv[j] / MODEL.views.length; toks.push({ view, tok });
    }
    const p = softmax(headLogits(fm), HF.T), order = p.map((v, k) => k).sort((a, b) => p[b] - p[a]), ctx = getCtx(), adj = adjust(p, ctx);
    let en = 0; for (let j = 0; j < 512; j++) en += emb[j] * emb[j]; en = Math.sqrt(en);
    const nn = neighbors(emb, 12), nd = nonDerm(emb) > 0.5;
    LAST = { toks, hc: {}, pImg: p, pCtx: adj.q, used: adj.used, ctx, probs: p, order, embN: Array.from(emb, x => x / en), nn, nd, ms: Math.round(performance.now() - t0) };
    showHeat = true; $("sg-heat").classList.add("on"); $("sg-orig").classList.remove("on");
    applyView(); renderCtx(ctx); renderNeigh(nn, ctx); renderWhy();
    show($("nonderm"), nd); ["probs", "chute", "groups", "heat-chips", "neigh"].forEach(i => $(i).style.opacity = nd ? ".3" : "1"); show($("loading"), false); show($("res"), true);
    $("res").scrollIntoView({ behavior: "smooth", block: "start" }); console.log("analise ms", LAST.ms);
  } catch (e) { $("load-txt").textContent = "Erro ao analisar: " + (e && e.message ? e.message : e); console.log(e); }
  busy = false;
};

/* ---------- miniaturas offline e atualização ---------- */
$("off").onclick = async e => {
  e.preventDefault(); const a = $("off"); if (!self.caches) { a.textContent = "Este navegador não permite guardar offline"; return; }
  try { const n = BANK.thumb_chunks, c = await caches.open("dermia-thumbs-" + BANK.v); for (let i = 0; i < n; i++) { a.textContent = "Baixando miniaturas " + (i + 1) + "/" + n + "…"; if (!(await c.match("thumbs/t" + i + ".bin"))) await c.add("thumbs/t" + i + ".bin"); }
    for (const k of await caches.keys()) if (k.startsWith("dermia-thumbs-") && k !== "dermia-thumbs-" + BANK.v) await caches.delete(k); a.textContent = "Miniaturas guardadas para uso offline"; }
  catch (x) { a.textContent = "Não consegui baixar as miniaturas"; }
};
$("upd").onclick = () => location.reload();
if ("serviceWorker" in navigator) { const had = !!navigator.serviceWorker.controller; navigator.serviceWorker.addEventListener("controllerchange", () => { if (had) show($("upd"), true); }); }
''')

# ---- tabela de acerto ----
block('function renderAcc() {', 'boot();', '''function renderAcc() {
  const c = HF.cv, pc = x => Math.round(x * 100) + "%", rows = Object.entries(c.res).sort((a, b) => b[1].n - a[1].n).map(([n, r]) => "<tr><td>" + esc(n) + ' <span class="d">(' + r.n + ')</span></td><td>' + pc(r.top1) + " / " + pc(r.top3) + "</td></tr>").join("");
  $("acc").innerHTML = "<p>Teste no ISIC: " + c.n + " imagens de dermatoscopia com histopatologia, " + HF.names.length + " diagnósticos, validação cruzada sem misturar imagens do mesmo paciente, feita com o mesmo modelo e o mesmo tratamento de imagem que rodam neste app.</p><table>" +
    "<tr><td>Diagnóstico exato em 1º lugar</td><td>" + pc(c.top1) + "</td></tr><tr><td>Exato ou compatível (laudo sem subtipo)</td><td>" + pc(c.compat) + "</td></tr><tr><td>Entre os 3 primeiros</td><td>" + pc(c.top3) + "</td></tr><tr><td>Entre os 5 primeiros</td><td>" + pc(c.top5) + "</td></tr><tr><td>Grupo certo (9 categorias)</td><td>" + pc(c.group) + "</td></tr></table>" +
    '<p class="d">"Compatível": o chute e o laudo são da mesma família e um dos dois não informa o subtipo (ex.: chute "melanoma in situ", laudo "melanoma" sem subtipo).</p><p class="d">Por diagnóstico (nº de casos): 1º lugar / entre os 3 primeiros</p><table>' + rows + "</table><p>Subtipos com menos de 100 casos têm acerto instável. Parte das imagens vem de poucos centros: o modelo pode aprender o estilo da foto junto com a lesão. O modelo pode ter visto ISIC no pré-treino, então estes números são otimistas.</p>";
}
''')
rep('.catch(() => {});\nboot();', '.catch(() => {});\nboot();') if False else None
open(p, "w", encoding="utf8").write(s); print("ok", len(s))
