import re
p = "app/index.html"; s = open(p, encoding="utf8").read()
def rep(a, b, cnt=1):
    global s
    assert s.count(a) == cnt, (s.count(a), a[:70]); s = s.replace(a, b)
def cut(a, b, keep_end=False):
    global s
    i0 = s.index(a); i1 = s.index(b, i0) + (0 if keep_end else len(b)); out = s[i0:i1]; s = s[:i0] + s[i1:]; return out
CAM = '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3.5 8.5A2 2 0 0 1 5.5 6.5h2l1.6-2.2h5.8l1.6 2.2h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-13a2 2 0 0 1-2-2z"/><circle cx="12" cy="13" r="3.6"/></svg>'
GAL = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="3"/><circle cx="8.5" cy="9.5" r="1.6"/><path d="M3 16l5-5 4 4 3-3 6 6"/></svg>'
LOCK = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="5" y="10.5" width="14" height="10" rx="2.5"/><path d="M8 10.5V8a4 4 0 0 1 8 0v2.5"/></svg>'
RING = '<svg viewBox="0 0 120 120" aria-hidden="true"><circle cx="60" cy="60" r="50" fill="none" stroke="#E8650A" stroke-width="7"/><circle cx="60" cy="60" r="27" fill="none" stroke="#C4A060" stroke-width="3.5"/><circle cx="60" cy="60" r="8" fill="#F4F1EC"/></svg>'
FACE = '<svg width="26" height="26" viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" aria-hidden="true"><path d="M6 20V12a6 6 0 0 1 6-6h8M44 6h8a6 6 0 0 1 6 6v8M58 44v8a6 6 0 0 1-6 6h-8M20 58h-8a6 6 0 0 1-6-6v-8"/><path d="M23 25v5M41 25v5M32 25v10h-3M24 42c4.5 4 11.5 4 16 0"/></svg>'

# ---------- CSS ----------
rep('@media (prefers-reduced-motion:reduce)', '''.top{display:grid;grid-template-columns:44px 1fr 44px;align-items:center}
.top .logo{display:flex;align-items:center;justify-content:center;gap:8px}
.ic{width:44px;height:44px;display:grid;place-items:center;border:0;background:transparent;color:var(--paper);border-radius:12px;cursor:pointer;padding:0}
.ic:active{background:rgba(255,255,255,.08)}
.ic.cam{color:var(--accent)}
/* introdução */
.intro{position:fixed;inset:0;z-index:30;overflow-y:auto;background:radial-gradient(90% 60% at 50% 18%,rgba(232,101,10,.22),transparent 65%),radial-gradient(70% 40% at 50% 100%,rgba(196,160,96,.10),transparent 70%),var(--ink)}
.intro-in{min-height:100%;max-width:440px;margin:0 auto;display:flex;flex-direction:column;justify-content:center;gap:26px;padding:calc(28px + env(safe-area-inset-top)) 22px calc(22px + env(safe-area-inset-bottom))}
.brand{display:flex;flex-direction:column;align-items:center;text-align:center;gap:6px}
.orb{width:116px;height:116px;margin-bottom:10px;position:relative}
.orb svg{width:100%;height:100%;filter:drop-shadow(0 10px 30px rgba(232,101,10,.35))}
.orb::after{content:"";position:absolute;inset:-14px;border-radius:50%;border:1px solid rgba(232,101,10,.35);animation:pulse 2.6s ease-out infinite}
@keyframes pulse{from{transform:scale(.85);opacity:1}to{transform:scale(1.25);opacity:0}}
.brand h1{font:400 54px/0.95 var(--display);letter-spacing:.03em;text-transform:uppercase;margin:0;color:var(--paper)}
.brand h1 b{font-weight:400;color:var(--accent)}
.brand p{margin:4px 0 0;color:#D9D2C7;font-size:15px;max-width:30ch}
.panel{background:rgba(35,33,32,.78);-webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px);border:1px solid rgba(255,255,255,.08);border-radius:24px;padding:18px;display:flex;flex-direction:column;gap:10px;box-shadow:0 20px 50px rgba(0,0,0,.35)}
.panel input[type=password]{margin:0;text-align:center;font-size:17px;letter-spacing:.04em}
.panel .hint{font-size:12.5px;color:var(--mute);text-align:center;margin:0}
.or{display:flex;align-items:center;gap:10px;color:var(--mute);font-size:12px}.or::before,.or::after{content:"";flex:1;height:1px;background:var(--line)}
.intro .foot{text-align:center;font-size:11.5px;color:var(--mute);margin:0;letter-spacing:.06em;text-transform:uppercase}
/* início estilo app */
.hero{display:flex;flex-direction:column;align-items:center;text-align:center;gap:14px;padding:26px 18px 22px}
.hero .lens{width:100%;margin:0;cursor:pointer}
.hero h3{font-size:24px}
.hero p{margin:0;color:var(--mute);font-size:14px;max-width:32ch}
/* folha de ações (câmera) */
.sheet{position:fixed;inset:0;z-index:25}
.sheet-bg{position:absolute;inset:0;background:rgba(0,0,0,.55);animation:fade .2s ease both}
.sheet-in{position:absolute;left:10px;right:10px;bottom:calc(10px + env(safe-area-inset-bottom));display:flex;flex-direction:column;gap:8px;animation:rise .25s cubic-bezier(.2,.8,.2,1) both;max-width:520px;margin:0 auto}
.sheet-grp{background:#2A2725;border-radius:18px;overflow:hidden}
.sheet-opt{display:flex;align-items:center;gap:14px;width:100%;padding:17px 18px;border:0;background:transparent;color:var(--paper);font:500 17px var(--body);cursor:pointer;border-bottom:1px solid rgba(255,255,255,.07)}
.sheet-opt:last-child{border-bottom:0}.sheet-opt svg{color:var(--accent)}
.sheet-opt:active{background:rgba(255,255,255,.06)}
.sheet-x{justify-content:center;font-weight:800;background:#2A2725;border-radius:18px}
.sheet-t{padding:12px 18px 4px;font-size:12.5px;color:var(--mute);text-align:center}
@keyframes fade{from{opacity:0}}@keyframes rise{from{transform:translateY(40px);opacity:0}}
@media (prefers-reduced-motion:reduce)''')

# ---------- cabeçalho estilo Instagram ----------
i0 = s.index('<header class="top">'); i1 = s.index('</header>') + len('</header>')
s = s[:i0] + f'''<header class="top">
  <button id="cam-btn" class="ic cam" aria-label="Nova foto">{CAM}</button>
  <h1 class="logo"><svg width="26" height="26" viewBox="0 0 30 30" aria-hidden="true"><circle cx="15" cy="15" r="11.5" fill="none" stroke="#E8650A" stroke-width="2.5"/><circle cx="15" cy="15" r="6" fill="none" stroke="#C4A060" stroke-width="1.5"/><circle cx="15" cy="15" r="2" fill="#F4F1EC"/></svg><span>Derm<b>IA</b></span></h1>
  <button id="lock-now" class="ic" aria-label="Bloquear o app">{LOCK}</button>
</header>''' + s[i1:]

# ---------- tirar bloqueio e instalação antigos; montar introdução ----------
lockblk = cut('<div id="lock" class="card center hide">', '<div id="modelo" class="card">', keep_end=True)
modblk = cut('<div id="modelo" class="card">', '<div id="fid-offer"', keep_end=True)
fileinp = re.search(r'<input id="file-model"[^>]*>', modblk).group(0)
intro = f'''<div id="intro" class="intro">
  <div class="intro-in">
    <div class="brand">
      <div class="orb">{RING}</div>
      <h1>Derm<b>IA</b></h1>
      <p>Estudo de dermatoscopia com inteligência artificial</p>
      <span class="d">Dr. Pedro Schmitz · CRM/SC 38229</span>
    </div>
    <div class="panel">
      <div id="m-status" class="hint"><span class="spin"></span>Preparando…</div>
      <div id="m-install" class="hide" style="display:flex;flex-direction:column;gap:10px">
        <p class="hint">Primeiro acesso neste aparelho. O modelo (85 MB) baixa uma vez e depois o app abre offline.</p>
        <input id="pw" type="password" placeholder="Frase de acesso" autocomplete="current-password" autocapitalize="off" enterkeyhint="go">
        <button id="btn-install" class="btn">Entrar</button>
        <div class="prog hide" id="prog"><i></i></div>
        <div id="m-msg" class="hint"></div>
        <details class="ctx" style="margin-top:0"><summary>Tenho o arquivo do modelo (.onnx)</summary>{fileinp.replace('class="btn ghost"', 'class="btn ghost" style="padding:10px;margin-top:8px"')}</details>
      </div>
      <div id="lock" class="hide" style="display:flex;flex-direction:column;gap:10px">
        <button id="btn-fid" class="btn hide">{FACE}Entrar com Face ID</button>
        <div id="lock-or" class="or hide">ou</div>
        <div id="lock-alt" style="display:flex;flex-direction:column;gap:10px"><input id="lock-pw" type="password" placeholder="Frase de acesso" autocomplete="current-password" autocapitalize="off" enterkeyhint="go"><button id="lock-go" class="btn ghost">Entrar</button></div>
        <div id="lock-msg" class="hint"></div>
        <div style="text-align:center"><button id="lock-pass" class="link hide">Usar a frase</button><button id="lock-reset" class="link">Esqueci a frase / redefinir</button></div>
      </div>
    </div>
    <p class="foot">Ferramenta de estudo · não é diagnóstico</p>
  </div>
</div>
'''
rep('<header class="top">', intro + '<header class="top">')

# ---------- início: herói + folha de ações; contexto vai para o editor ----------
ctxblk = cut('<details id="ctx" class="ctx">', '</details>')
i0 = s.index('<div id="entrada" class="card hide">'); i1 = s.index('<div id="editor" class="card hide">')
s = s[:i0] + f'''<div id="entrada" class="card hero hide">
    <div id="hero-lens" class="lens"><div class="ring"><i></i></div><span>Toque para começar</span></div>
    <h3>Analisar uma lesão</h3>
    <p>Toque na câmera no canto da tela ou aqui embaixo. Você escolhe tirar a foto agora ou usar uma da galeria.</p>
    <button id="hero-btn" class="btn">{CAM}Nova análise</button>
    <div id="foto-msg" class="alert hide" style="width:100%"></div>
    <p class="d">Tudo roda no aparelho: a foto não sai do iPhone.</p>
  </div>
  <input id="foto-cam" type="file" accept="image/*" capture="environment" class="hide">
  <input id="foto" type="file" accept="image/*" class="hide">

  ''' + s[i1:]
rep('<div class="two"><button id="ed-auto"', ctxblk.replace('class="ctx"', 'class="ctx" style="margin:0 0 12px"', 1) + '\n    <div class="two"><button id="ed-auto"')
rep('<button id="ed-back" class="link">Trocar foto</button>', '<button id="ed-back" class="link">Cancelar</button>')
rep('<div id="ov" class="hide">', f'''<div id="sheet" class="sheet hide" role="dialog" aria-label="Nova análise">
  <div class="sheet-bg" id="sheet-bg"></div>
  <div class="sheet-in">
    <div class="sheet-grp"><div class="sheet-t">Nova análise</div>
      <label class="sheet-opt" for="foto-cam">{CAM}Tirar foto</label>
      <label class="sheet-opt" for="foto">{GAL}Escolher da galeria</label>
    </div>
    <button class="sheet-opt sheet-x" id="sheet-x">Cancelar</button>
  </div>
</div>
<div id="ov" class="hide">''')

# ---------- JS: desbloqueio na introdução ----------
i0 = s.index('function lockScreen() {'); i1 = s.index('$("lock-pass").onclick')
s = s[:i0] + '''function lockScreen(hasFid) {
  show($("intro"), true); show($("m-status"), false); show($("m-install"), false); show($("lock"), true);
  show($("btn-fid"), hasFid); show($("lock-or"), hasFid);
  return new Promise(res => {
    unlockWait = res;
    const go = async () => { $("lock-msg").textContent = ""; try { await fidGet(); res(); } catch (e) { $("lock-msg").textContent = fidErr(e); $("lock-pw").focus(); } };
    $("btn-fid").onclick = go; if (hasFid) go(); else setTimeout(() => $("lock-pw").focus(), 200);
  });
}
''' + s[i1:]
rep('if (v && v === await pwCheck($("lock-pw").value.trim())) { show($("lock"), false); unlockWait && unlockWait(); } else $("lock-msg").textContent = "Frase incorreta.";',
    'if (v && v === await pwCheck($("lock-pw").value.trim())) { $("lock-pw").value = ""; unlockWait && unlockWait(); } else { $("lock-msg").textContent = "Frase incorreta."; $("lock-pw").select(); }')
rep('''  if (bytes) {
    if (await kvGet("fid").catch(() => null)) await lockScreen();
    show($("modelo"), true); try {''', '''  show($("m-status"), false);
  if (bytes) {
    const fid = await kvGet("fid").catch(() => null), pc = await kvGet("pwcheck").catch(() => null);
    if (fid || pc) await lockScreen(!!fid);
    show($("lock"), false); show($("m-status"), true); $("m-status").innerHTML = '<span class="spin"></span>Abrindo…'; try {''')
rep('show($("modelo"), false); show($("entrada"), true);', 'show($("intro"), false); show($("entrada"), !LAST); document.documentElement.scrollTop = 0;')
rep('$("btn-install").onclick = installFromSite;', '''$("btn-install").onclick = installFromSite;
$("pw").addEventListener("keydown", e => { if (e.key === "Enter") installFromSite(); });
$("lock-pw").addEventListener("keydown", e => { if (e.key === "Enter") $("lock-go").click(); });
$("lock-now").onclick = () => location.reload();''')

# ---------- JS: câmera, folha de ações e fluxo ----------
rep('$("foto").onchange = onPhoto;', '''function openSheet() { if (!session) return; go("analisar"); show($("sheet"), true); }
function closeSheet() { show($("sheet"), false); }
$("cam-btn").onclick = openSheet; $("hero-btn").onclick = openSheet; $("hero-lens").onclick = openSheet;
$("sheet-bg").onclick = closeSheet; $("sheet-x").onclick = closeSheet;
["foto", "foto-cam"].forEach(i => $(i).addEventListener("click", () => setTimeout(closeSheet, 300)));
$("foto").onchange = onPhoto;''')
rep('show($("entrada"), false); show($("editor"), true);', 'show($("entrada"), false); show($("res"), false); show($("tabs"), false); show($("editor"), true);')
rep('$("ed-back").onclick = () => { show($("editor"), false); show($("entrada"), true); DEC = null; };',
    '$("ed-back").onclick = () => { show($("editor"), false); DEC = null; if (LAST) { show($("res"), true); show($("tabs"), true); } else show($("entrada"), true); };')
rep('$("ed-go").onclick = () => { show($("editor"), false); show($("entrada"), true); analyze(); };', '$("ed-go").onclick = () => { show($("editor"), false); analyze(); };')
rep('show($("res"), false); show($("tabs"), false); show($("scan"), false); show($("loading"), true);', 'show($("entrada"), false); show($("res"), false); show($("tabs"), false); show($("scan"), false); show($("loading"), true);')
rep('catch (e) { $("load-txt").textContent = "Erro ao analisar: "', 'catch (e) { show($("entrada"), true); $("load-txt").textContent = "Erro ao analisar: "')
s = s.replace('const APP_VER = "v6";', 'const APP_VER = "v7";')
open(p, "w", encoding="utf8").write(s); print("ok")
