p = "app/index.html"; s = open(p, encoding="utf8").read()
def rep(a, b, cnt=1):
    global s
    assert s.count(a) == cnt, (s.count(a), a[:70]); s = s.replace(a, b)
def cut(a, b):
    global s
    i0 = s.index(a); i1 = s.index(b, i0) + len(b); out = s[i0:i1]; s = s[:i0] + s[i1:]; return out

# ---- CSS: barra de abas inferior e telas ----
rep('@media (prefers-reduced-motion:reduce)', '''.view{display:flex;flex-direction:column;gap:14px}
.wrap{padding-bottom:calc(96px + env(safe-area-inset-bottom))}
.tabbar{position:fixed;left:0;right:0;bottom:0;z-index:6;display:flex;justify-content:center;padding:8px 12px calc(8px + env(safe-area-inset-bottom));background:rgba(22,21,20,.88);-webkit-backdrop-filter:blur(16px);backdrop-filter:blur(16px);border-top:1px solid rgba(255,255,255,.07)}
.tabbar .in{display:grid;grid-template-columns:repeat(3,1fr);gap:4px;width:100%;max-width:520px}
.tabbar button{display:flex;flex-direction:column;align-items:center;gap:3px;border:0;background:transparent;color:var(--mute);font:800 11px var(--body);letter-spacing:.02em;padding:6px 4px;border-radius:12px;cursor:pointer}
.tabbar button svg{width:24px;height:24px}
.tabbar button.on{color:var(--accent);background:rgba(232,101,10,.10)}
.mini{font-size:12px;color:var(--mute);text-align:center;margin:-4px 0 0}
.mini a{color:var(--mute)}
.set{display:flex;flex-direction:column;gap:0}
.set .row{display:flex;align-items:center;gap:12px;padding:14px 2px;border-bottom:1px solid var(--line);background:none;border-left:0;border-right:0;border-top:0;color:var(--paper);font:500 15px var(--body);text-align:left;cursor:pointer;width:100%}
.set .row:last-child{border-bottom:0}
.set .row span{flex:1}.set .row small{color:var(--mute);font-size:12.5px}
.set .row.danger{color:var(--bad)}
.card h3{font-size:18px;margin:0 0 8px}
.card p,.card li{color:#CFC9BF;font-size:13.5px}.card ul{padding-left:18px;margin:6px 0}
@media (prefers-reduced-motion:reduce)''')
rep('.tabs{position:sticky;top:calc(var(--bar) + env(safe-area-inset-top) - 6px);', '.tabs{position:sticky;top:calc(var(--bar) + env(safe-area-inset-top) - 6px);')

# ---- tirar do início: aviso grande, detalhes e rodapé ----
disc = cut('<details class="disc">', '</details>')
acc = cut('<details class="info"><summary>Quanto o modelo acerta (medido)</summary>', '</details>')
lim = cut('<details class="info"><summary>Limites e avisos</summary>', '</details>')
foot = cut('<footer>', '</footer>')
lim_ul = lim[lim.index('<ul>'):lim.index('</ul>') + 5]

rep('<div class="wrap">', '<div class="wrap">\n<section id="view-analisar" class="view">')
rep('<div id="ov" class="hide">', '''</section>

<section id="view-sobre" class="view hide">
  <h2>Sobre o modelo</h2>
  <div class="card" style="border-color:rgba(232,101,10,.45)"><h3>Ferramenta de estudo</h3><p style="margin:0">Não é diagnóstico. Não use para decidir conduta em paciente. Software que apoia diagnóstico exige registro na ANVISA. Os resultados são chutes de um modelo treinado no ISIC, para você comparar com o seu raciocínio.</p></div>
  <div class="card"><h3>Quanto acerta (medido)</h3><div id="acc"></div></div>
  <div class="card"><h3>Limites e avisos</h3>''' + lim_ul + '''</div>
  <div class="card"><h3>Como usar bem</h3><ul><li>Lesão no centro, foto nítida, dermatoscópio encostado ou polarizado sem reflexo.</li><li>Leia os 3 a 5 primeiros como diagnóstico diferencial, não só o 1º lugar.</li><li>Quando dois diagnósticos estão quase empatados, fotografe de novo e compare.</li><li>Preencha região e idade quando souber: ajustam as probabilidades.</li></ul></div>
</section>

<section id="view-ajustes" class="view hide">
  <h2>Ajustes</h2>
  <div class="card set">
    <button class="row" id="fid-toggle"><span>Face ID</span><small id="fid-state">verificando…</small></button>
    <button class="row" id="off"><span>Baixar miniaturas para uso offline</span><small>37 MB</small></button>
    <button class="row" id="upd-check"><span>Procurar atualização</span><small id="ver"></small></button>
    <button class="row danger" id="rm"><span>Remover modelo deste aparelho</span></button>
  </div>
  <div id="st" class="sub" style="margin:0 2px"></div>
  <div class="card"><p style="margin:0">DermIA · uso pessoal de estudo · Dr. Pedro Schmitz, CRM/SC 38229.<br>Banco: <span id="nb"></span> casos do ISIC Archive. O app se atualiza sozinho quando há versão nova.</p></div>
</section>
</div>

<nav class="tabbar" aria-label="Menu"><div class="in">
  <button data-v="analisar" class="on"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r="1" fill="currentColor"/></svg>Analisar</button>
  <button data-v="sobre"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.5"/></svg>Sobre o modelo</button>
  <button data-v="ajustes"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 7h10M18 7h2M4 17h4M12 17h8"/><circle cx="16" cy="7" r="2"/><circle cx="10" cy="17" r="2"/></svg>Ajustes</button>
</div></nav>
<div id="ov" class="hide">''')
# o </div> do .wrap original fica antes do ov: remover o duplicado
rep('</section>\n</div>\n\n<nav class="tabbar"', '</section>\n\n<nav class="tabbar"')
rep('</div>\n</section>\n\n<section id="view-sobre"', '</section>\n\n<section id="view-sobre"')
rep('<section id="view-ajustes" class="view hide">', '<section id="view-ajustes" class="view hide">')
s = s.replace('</section>\n\n<nav class="tabbar"', '</section>\n</div>\n\n<nav class="tabbar"', 1)

# linha curta de aviso no início
rep('<div class="sub" style="margin:10px 2px 0">Tudo roda no aparelho: a foto não sai do iPhone.</div>', '<div class="sub" style="margin:10px 2px 0">Ferramenta de estudo, não é diagnóstico. Tudo roda no aparelho: a foto não sai do iPhone.</div>')

# ---- JS: troca de telas ----
rep('$("foto").onchange = onPhoto;', '''function go(v) { ["analisar", "sobre", "ajustes"].forEach(x => show($("view-" + x), x === v)); document.querySelectorAll(".tabbar button").forEach(b => b.classList.toggle("on", b.dataset.v === v)); show($("tabs"), v === "analisar" && !!LAST && !$("res").classList.contains("hide")); window.scrollTo(0, 0); }
document.querySelectorAll(".tabbar button").forEach(b => b.onclick = () => go(b.dataset.v));
$("foto").onchange = onPhoto;''')
# Face ID na tela de ajustes
rep('''const on = !!(await kvGet("fid").catch(() => null)), a = $("fid-toggle"); if (!(await fidAvailable())) { show(a, false); return; }
  show(a, true); a.textContent = on ? "Desativar Face ID" : "Ativar Face ID";''', '''const on = !!(await kvGet("fid").catch(() => null)), a = $("fid-toggle"), st = $("fid-state");
  if (!(await fidAvailable())) { st.textContent = "indisponível aqui"; a.onclick = () => { $("st").textContent = "Face ID só funciona no endereço próprio do app, aberto pelo ícone da tela de início."; }; return; }
  st.textContent = on ? "ligado · tocar para desligar" : "desligado · tocar para ligar";''')
# links viraram botões: remover preventDefault dependente de href ok (preventDefault em botão é inofensivo)
rep('a.textContent = "Baixando miniaturas "', 'a.firstElementChild.textContent = "Baixando miniaturas "')
rep('a.textContent = "Este navegador não permite guardar offline"', 'a.firstElementChild.textContent = "Este navegador não permite guardar offline"')
rep('a.textContent = "Miniaturas guardadas para uso offline"', 'a.firstElementChild.textContent = "Miniaturas guardadas para uso offline"')
rep('a.textContent = "Não consegui baixar as miniaturas"', 'a.firstElementChild.textContent = "Não consegui baixar as miniaturas"')

# ---- atualização automática ----
i0 = s.index('$("upd").onclick'); i1 = s.index('\n', s.index('if ("serviceWorker" in navigator) { const had'))
s = s[:i0] + '''/* atualização automática: procura versão nova ao abrir e ao voltar para o app; aplica sozinho se não houver análise na tela */
const APP_VER = "v5";
let swReg = null, pendingReload = false;
function softReload() { if (busy || (LAST && !$("res").classList.contains("hide") && document.visibilityState === "visible")) { pendingReload = true; show($("upd"), true); } else location.reload(); }
$("upd").onclick = () => location.reload();
if ("serviceWorker" in navigator) {
  const had = !!navigator.serviceWorker.controller;
  navigator.serviceWorker.addEventListener("controllerchange", () => { if (had) softReload(); });
  navigator.serviceWorker.register("sw.js").then(r => { swReg = r; r.update().catch(() => {}); }).catch(() => {});
  document.addEventListener("visibilitychange", () => { if (document.visibilityState === "hidden" && pendingReload) location.reload(); if (document.visibilityState === "visible" && swReg) swReg.update().catch(() => {}); });
  setInterval(() => swReg && swReg.update().catch(() => {}), 30 * 60 * 1000);
}
$("upd-check").onclick = async () => { $("st").textContent = "Procurando…"; try { if (swReg) { await swReg.update(); $("st").textContent = swReg.installing || swReg.waiting ? "Versão nova encontrada: aplicando…" : "Você já está na versão mais recente."; } else $("st").textContent = "Atualização automática indisponível nesta prévia."; } catch (e) { $("st").textContent = "Sem conexão para procurar atualização."; } };
''' + s[i1 + 1:]
rep('function ready() { renderAcc();', 'function ready() { renderAcc(); $("ver").textContent = APP_VER + " · modelo " + MODEL.model_sha.slice(0, 7);')
# remover o registro antigo duplicado, se existir
if s.count('navigator.serviceWorker.register("sw.js")') > 1:
    j = s.rindex('if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js")'); k = s.index('\n', j); s = s[:j] + s[k + 1:]
open(p, "w", encoding="utf8").write(s); print("ok", s.count('navigator.serviceWorker.register("sw.js")'))
