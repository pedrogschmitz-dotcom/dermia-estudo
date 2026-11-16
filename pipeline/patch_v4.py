p = "app/index.html"; s = open(p, encoding="utf8").read()
def rep(a, b, cnt=1):
    global s
    assert s.count(a) == cnt, (s.count(a), a[:70]); s = s.replace(a, b)

# ---------- Face ID (WebAuthn com autenticador do aparelho) ----------
rep('async function boot() {\n  try { await loadData(); }', '''/* ---------- Face ID: trava de tela local (WebAuthn do próprio aparelho) ---------- */
const hex = b => Array.from(new Uint8Array(b)).map(x => x.toString(16).padStart(2, "0")).join("");
async function pwCheck(pw) { const k = await crypto.subtle.importKey("raw", new TextEncoder().encode(pw), "PBKDF2", false, ["deriveBits"]); return hex(await crypto.subtle.deriveBits({ name: "PBKDF2", salt: new TextEncoder().encode("dermia-trava"), iterations: 150000, hash: "SHA-256" }, k, 256)); }
async function fidAvailable() { try { return !!(window.PublicKeyCredential && await PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable()); } catch (e) { return false; } }
function fidErr(e) { const n = e && e.name; return n === "NotAllowedError" ? "Face ID cancelado ou bloqueado aqui. Tente de novo ou use a frase." : n === "SecurityError" ? "Este endereço não permite Face ID (ex.: dentro do Claude). Use a frase." : "Face ID indisponível: " + (e && e.message ? e.message : e); }
async function fidCreate() {
  const id = crypto.getRandomValues(new Uint8Array(16));
  const c = await navigator.credentials.create({ publicKey: { challenge: crypto.getRandomValues(new Uint8Array(32)), rp: { name: "DermIA" }, user: { id, name: "dermia", displayName: "DermIA" },
    pubKeyCredParams: [{ type: "public-key", alg: -7 }, { type: "public-key", alg: -257 }], authenticatorSelection: { authenticatorAttachment: "platform", userVerification: "required", residentKey: "discouraged" }, timeout: 60000, attestation: "none" } });
  await kvSet("fid", new Uint8Array(c.rawId));
}
async function fidGet() {
  const raw = await kvGet("fid");
  await navigator.credentials.get({ publicKey: { challenge: crypto.getRandomValues(new Uint8Array(32)), allowCredentials: [{ type: "public-key", id: raw, transports: ["internal"] }], userVerification: "required", timeout: 60000 } });
}
let unlockWait = null;
function lockScreen() {
  show($("lock"), true); show($("modelo"), false);
  return new Promise(res => {
    unlockWait = res;
    const go = async () => { $("lock-msg").textContent = ""; try { await fidGet(); show($("lock"), false); res(); } catch (e) { $("lock-msg").textContent = fidErr(e); show($("lock-alt"), true); } };
    $("btn-fid").onclick = go; go();
  });
}
$("lock-pass").onclick = () => { show($("lock-alt"), true); $("lock-pw").focus(); };
$("lock-go").onclick = async () => { const v = await kvGet("pwcheck").catch(() => null); if (v && v === await pwCheck($("lock-pw").value.trim())) { show($("lock"), false); unlockWait && unlockWait(); } else $("lock-msg").textContent = "Frase incorreta."; };
$("lock-reset").onclick = async () => { if (!confirm("Apagar o modelo e o Face ID deste aparelho? Você vai precisar da frase para instalar de novo.")) return; try { const d = await idb(); const os = d.transaction("kv", "readwrite").objectStore("kv"); ["model", "model_sha", "fid", "pwcheck"].forEach(k => os.delete(k)); } catch (x) {} location.reload(); };
async function offerFid() {
  if (await kvGet("fid").catch(() => null) || !(await fidAvailable()) || await kvGet("fid_no").catch(() => null)) return;
  show($("fid-offer"), true);
  $("fid-on").onclick = async () => { try { await fidCreate(); show($("fid-offer"), false); $("st").textContent = "Face ID ativado neste aparelho."; refreshFidLink(); } catch (e) { $("fid-msg").textContent = fidErr(e); } };
  $("fid-later").onclick = async () => { show($("fid-offer"), false); try { await kvSet("fid_no", 1); } catch (e) {} refreshFidLink(); };
}
async function refreshFidLink() {
  const on = !!(await kvGet("fid").catch(() => null)), a = $("fid-toggle"); if (!(await fidAvailable())) { show(a, false); return; }
  show(a, true); a.textContent = on ? "Desativar Face ID" : "Ativar Face ID";
  a.onclick = async e => { e.preventDefault(); try { if (on) { const d = await idb(); d.transaction("kv", "readwrite").objectStore("kv").delete("fid"); $("st").textContent = "Face ID desativado."; } else { await fidCreate(); $("st").textContent = "Face ID ativado neste aparelho."; } } catch (x) { $("st").textContent = fidErr(x); } refreshFidLink(); };
}
async function boot() {
  try { await loadData(); }''')
rep('''  if (bytes) { try { await makeSession(bytes); ready(); return; } catch (e) { console.log(e); } }''',
    '''  if (bytes) {
    if (await kvGet("fid").catch(() => null)) await lockScreen();
    show($("modelo"), true); try { await makeSession(bytes); ready(); refreshFidLink(); return; } catch (e) { console.log(e); }
  }''')
rep('''    await makeSession(out); ready();
  } catch (e) { $("m-msg").textContent = "Erro: " + e.message;''', '''    try { await kvSet("pwcheck", await pwCheck(pw)); } catch (e) {}
    await makeSession(out); ready(); offerFid(); refreshFidLink();
  } catch (e) { $("m-msg").textContent = "Erro: " + e.message;''')
rep('const os = d.transaction("kv", "readwrite").objectStore("kv"); os.delete("model"); os.delete("model_sha"); } catch (x) {} location.reload(); };',
    'const os = d.transaction("kv", "readwrite").objectStore("kv"); ["model", "model_sha", "fid", "pwcheck"].forEach(k => os.delete(k)); } catch (x) {} location.reload(); };')

# ---------- veredito, lista e grupos ----------
rep('''const top = order[0]; $("chute").innerHTML = '<span class="d">Melhor chute</span><div style="font:400 24px/1.1 Anton,Impact,sans-serif;text-transform:uppercase;margin:2px 0 2px">' + esc(HF.names[top]) + '</div><span class="d">' + Math.round(p[top] * 100) + '% · grupo: ' + esc(HEAD.pt[HEAD.names.indexOf(HF.groups[top])]) + '</span>';''',
    '''const top = order[0]; $("chute").innerHTML = '<span class="eyebrow">Melhor chute do modelo</span><div class="verdict">' + esc(HF.names[top]) + '</div><div class="vmeta"><span class="pill">' + Math.round(p[top] * 100) + '%</span><span>grupo: ' + esc(HEAD.pt[HEAD.names.indexOf(HF.groups[top])]) + '</span><span>· 2º ' + esc(HF.names[order[1]]) + ' ' + Math.round(p[order[1]] * 100) + '%</span></div>';''')
rep('''row.innerHTML = '<span class="n">' + esc(HF.names[k])''', '''row.innerHTML = '<span class="rk">' + (r + 1) + '</span><span class="n">' + esc(HF.names[k])''')
rep('''$("groups").innerHTML = go.slice(0, 5).map(k => '<div class="prow"><span class="n">' + esc(HEAD.pt[k]) + '</span><span class="v">' + (g[k] < 0.01 ? "<1" : Math.round(g[k] * 100)) + '%</span><div class="bar"><i style="width:' + Math.max(1, g[k] * 100) + '%"></i></div></div>').join("");''',
    '''const GC = ["#E8650A", "#C4A060", "#3C82FF", "#6FCF97", "#B07CE0", "#FF6B5B", "#4FC3C9", "#E0C341", "#8A847A"];
  $("groups").innerHTML = '<div class="stack">' + go.filter(k => g[k] >= 0.005).map((k, r) => '<i style="width:' + (g[k] * 100) + '%;background:' + GC[r] + '"></i>').join("") + '</div><div class="leg">' + go.filter(k => g[k] >= 0.01).slice(0, 6).map((k, r) => '<span><i class="sw" style="background:' + GC[r] + '"></i>' + esc(HEAD.pt[k]) + ' <b>' + Math.round(g[k] * 100) + '%</b></span>').join("") + '</div>';''')

# ---------- câmera, carregamento com a foto, abas ----------
rep('$("foto").onchange = async ev => {', 'const onPhoto = async ev => {')
rep('''const t0 = performance.now(), crop = await toCrop(f); $("cv-base").getContext("2d").drawImage(crop.canvas, 0, 0, 448, 448);''',
    '''const t0 = performance.now(), crop = await toCrop(f); $("cv-base").getContext("2d").drawImage(crop.canvas, 0, 0, 448, 448);
    $("load-cv").getContext("2d").drawImage(crop.canvas, 0, 0, 168, 168); show($("scan"), true); $("load-txt").textContent = "Lendo a lesão…"; await new Promise(r => setTimeout(r, 30));''')
rep('''show($("res"), false); show($("loading"), true);''', '''show($("res"), false); show($("tabs"), false); show($("scan"), false); show($("loading"), true); $("loading").scrollIntoView({ behavior: "smooth", block: "center" });''')
rep('''$("res").scrollIntoView({ behavior: "smooth", block: "start" });''', '''show($("tabs"), true); syncTabs(); $("sec-mapa").scrollIntoView({ behavior: "smooth", block: "start" });''')
rep('/* ---------- miniaturas offline e atualização ---------- */', '''$("foto").onchange = onPhoto; $("foto-cam").onchange = onPhoto;
function syncTabs() { document.querySelectorAll("#tabs button").forEach(b => show(b, !$(b.dataset.t).classList.contains("hide"))); }
document.querySelectorAll("#tabs button").forEach(b => b.onclick = () => $(b.dataset.t).scrollIntoView({ behavior: "smooth", block: "start" }));
if ("IntersectionObserver" in window) { const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) document.querySelectorAll("#tabs button").forEach(b => b.classList.toggle("on", b.dataset.t === e.target.id)); }), { rootMargin: "-35% 0px -60% 0px" });
  ["sec-mapa", "sec-dx", "whyres", "ctxres", "sec-casos"].forEach(i => io.observe($(i))); }
function ctxCount() { const n = document.querySelectorAll("#ctx input:checked").length + Array.from(document.querySelectorAll("#ctx select, #ctx input[type=number], #ctx textarea")).filter(e => e.value).length; $("ctx-n").textContent = n; show($("ctx-n"), n > 0); }
$("ctx").addEventListener("input", ctxCount); $("ctx").addEventListener("change", ctxCount); $("c-clear").addEventListener("click", () => setTimeout(ctxCount, 0));

/* ---------- miniaturas offline e atualização ---------- */''')
rep('show($("whyres"), !LAST.nd);', 'show($("whyres"), !LAST.nd); syncTabs();')
open(p, "w", encoding="utf8").write(s); print("ok")
