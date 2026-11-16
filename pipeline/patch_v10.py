p = "app/index.html"; s = open(p, encoding="utf8").read()
def rep(a, b, cnt=1):
    global s
    assert s.count(a) == cnt, (s.count(a), a[:70]); s = s.replace(a, b)
# dados
rep('const [m, w, bank, bv, exp] = await Promise.all([getJSON("data/model.json"), getBin("data/model_w.bin"), getJSON("data/bank.json"), getBin("data/bank.bin"), getJSON("data/explain.json")]);',
    'const [m, w, bank, bv, exp, at] = await Promise.all([getJSON("data/model.json"), getBin("data/model_w.bin"), getJSON("data/bank.json"), getBin("data/bank.bin"), getJSON("data/explain.json"), getJSON("data/attr.json")]);')
rep('EXP = exp;', 'EXP = exp; ATTR = at;')
rep('let session = null, MODEL = null,', 'let ATTR = null, session = null, MODEL = null,')
# HTML: 3 modos + legenda das estruturas
rep('<div class="seg"><button id="sg-orig">Foto</button><button id="sg-heat" class="on">Mapa de calor</button></div>',
    '<div class="seg seg3"><button id="sg-orig">Foto</button><button id="sg-heat" class="on">Mapa de calor</button><button id="sg-attr">Estruturas</button></div>\n        <div id="attr-box" class="hide"><div id="attr-chips" class="chips"></div><div class="sub" style="margin:8px 0 0">Detector treinado em 2.594 imagens com as estruturas desenhadas por especialistas (ISIC 2018). Marca em quadradinhos de 16 px, então o contorno é grosseiro. Erra com frequência, principalmente estrias, rede negativa e cistos: confira na foto.</div></div>')
rep('.seg button{', '.seg3{grid-template-columns:1fr 1.25fr 1.1fr}\n.dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px;vertical-align:0}\n.chip.off{opacity:.45}\n.seg button{')
# JS: cálculo e desenho
rep('let curClass = 0, showHeat = true;', '''let curClass = 0, showHeat = true, mode = "heat", attrOn = {};
function attrProbs(tok) {                          // probabilidade de cada estrutura em cada quadradinho (tokens do mesmo modelo, sem custo extra)
  const D = 768, g = new Float64Array(D); for (let i = 0; i < 196; i++) for (let j = 0; j < D; j++) g[j] += tok[i * D + j] / 196;
  return ATTR.W.map((w, k) => { let bg = ATTR.b[k]; for (let j = 0; j < D; j++) bg += w[D + j] * g[j]; const out = new Float64Array(196);
    for (let i = 0; i < 196; i++) { let z = bg; const o = i * D; for (let j = 0; j < D; j++) z += w[j] * tok[o + j]; out[i] = 1 / (1 + Math.exp(-z)); } return out; });
}
function attrSummary() { return ATTR.ids.map((id, k) => { const pr = LAST.attr[k], th = ATTR.th[k]; let n = 0, mx = 0; for (let i = 0; i < 196; i++) { if (pr[i] >= th) n++; if (pr[i] > mx) mx = pr[i]; } return { k, id, pt: ATTR.pt[k], color: ATTR.color[k], n, mx, on: n > 0 }; }); }
function drawAttr(g) {
  const S = 448 / 14; g.lineWidth = 3; g.lineCap = "round";
  attrSummary().forEach(a => { if (!a.on || attrOn[a.id] === false) return; const pr = LAST.attr[a.k], th = ATTR.th[a.k], on = i => pr[i] >= th, at = (r, c) => r >= 0 && r < 14 && c >= 0 && c < 14 && on(r * 14 + c);
    g.fillStyle = a.color + "33"; g.strokeStyle = a.color; g.beginPath();
    for (let r = 0; r < 14; r++) for (let c = 0; c < 14; c++) { if (!at(r, c)) continue; g.fillRect(c * S, r * S, S, S); const x = c * S, y = r * S;
      if (!at(r - 1, c)) { g.moveTo(x, y); g.lineTo(x + S, y); } if (!at(r + 1, c)) { g.moveTo(x, y + S); g.lineTo(x + S, y + S); }
      if (!at(r, c - 1)) { g.moveTo(x, y); g.lineTo(x, y + S); } if (!at(r, c + 1)) { g.moveTo(x + S, y); g.lineTo(x + S, y + S); } }
    g.stroke(); });
}
function renderAttrChips() {
  const box = $("attr-chips"); box.innerHTML = "";
  attrSummary().forEach(a => { const b = document.createElement("button"); b.className = "chip" + (a.on && attrOn[a.id] !== false ? "" : " off");
    b.innerHTML = '<i class="dot" style="background:' + a.color + '"></i>' + esc(a.pt) + ' <span class="d">' + (a.on ? "detectada" : "não detectada") + '</span>';
    if (a.on) b.onclick = () => { attrOn[a.id] = attrOn[a.id] === false; renderAttrChips(); drawHeat(); }; box.appendChild(b); });
}
function setMode(m) { mode = m; showHeat = m !== "orig"; ["orig", "heat", "attr"].forEach(x => $("sg-" + x).classList.toggle("on", x === m)); show($("heat-chips"), m === "heat"); show($("attr-box"), m === "attr"); if (m === "attr") renderAttrChips(); drawHeat(); }''')
rep('  if (!showHeat || !LAST) return;', '  if (!showHeat || !LAST) return;\n  if (mode === "attr") { drawAttr(g); return; }')
rep('$("sg-orig").onclick = () => { showHeat = false; $("sg-orig").classList.add("on"); $("sg-heat").classList.remove("on"); drawHeat(); };', '$("sg-orig").onclick = () => setMode("orig");')
rep('$("sg-heat").onclick = () => { showHeat = true; $("sg-heat").classList.add("on"); $("sg-orig").classList.remove("on"); drawHeat(); };', '$("sg-heat").onclick = () => setMode("heat");\n$("sg-attr").onclick = () => setMode("attr");')
rep('showHeat = true; $("sg-heat").classList.add("on"); $("sg-orig").classList.remove("on");', 'LAST.attr = attrProbs(toks[0].tok); attrOn = {}; mode = "heat"; showHeat = true; ["orig", "heat", "attr"].forEach(x => $("sg-" + x).classList.toggle("on", x === "heat")); show($("heat-chips"), true); show($("attr-box"), false);')
# explicação: estruturas detectadas no topo
rep('''  let h = '<div class="fl lo" style="margin-top:0"><b>' + esc(nm(A)) + "</b> (" + pc(p[A]) + "), seguido de " + esc(nm(B)) + " (" + pc(p[B]) + ") e " + esc(nm(C)) + " (" + pc(p[C]) + ").</div>";''',
    '''  let h = '<div class="fl lo" style="margin-top:0"><b>' + esc(nm(A)) + "</b> (" + pc(p[A]) + "), seguido de " + esc(nm(B)) + " (" + pc(p[B]) + ") e " + esc(nm(C)) + " (" + pc(p[C]) + ").</div>";
  if (LAST.attr) { const det = attrSummary().filter(a => a.on); h += '<div class="fl" style="margin-top:8px"><b>Estruturas que o detector marcou na foto:</b> ' + (det.length ? det.map(a => '<i class="dot" style="background:' + a.color + '"></i>' + esc(a.pt)).join(" · ") : "nenhuma das 5 que ele conhece (rede pigmentar, rede negativa, estrias, cistos tipo milium, glóbulos)") + '. Veja em Mapa → Estruturas.</div>'; }''')
# acerto do detector em "Sobre o modelo"
rep('function renderAcc() {', '''function attrAccHTML() {
  return '<p style="margin-top:14px"><b>Detector de estruturas</b> (2.594 imagens do ISIC 2018 com as estruturas desenhadas à mão, validação cruzada por paciente). "Acerta se existe" = chance de dar nota maior a uma foto que tem a estrutura do que a uma que não tem. "Sobreposição" = quanto a área marcada coincide com a desenhada (1 = perfeita); os melhores da competição chegaram perto de 0,45.</p><table><tr><td><b>Estrutura</b></td><td>existe / sobreposição</td></tr>' +
    ATTR.ids.map((id, k) => { const c = ATTR.cv[id]; return "<tr><td>" + esc(ATTR.pt[k]) + ' <span class="d">(' + c.n_img + ")</span></td><td>" + Math.round(c.auc_img * 100) + "% / " + c.jaccard.toFixed(2) + "</td></tr>"; }).join("") + "</table>";
}
function renderAcc() {''')
s = s.replace('$("acc").innerHTML = "<p>Teste no ISIC:', '$("acc").innerHTML = attrAccHTML() + "<p>Teste no ISIC:', 1)
s = s.replace('const APP_VER = "v9";', 'const APP_VER = "v10";')
open(p, "w", encoding="utf8").write(s); print("ok")
