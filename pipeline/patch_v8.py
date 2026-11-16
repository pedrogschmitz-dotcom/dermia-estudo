import re
p = "app/index.html"; s = open(p, encoding="utf8").read()
def rep(a, b, cnt=1):
    global s
    assert s.count(a) == cnt, (s.count(a), a[:70]); s = s.replace(a, b)
D = lambda w, extra="": f'<svg viewBox="0 0 128 128" width="{w}" height="{w}" aria-hidden="true"{extra}><circle cx="50" cy="78" r="28" fill="none" stroke="#00B4FF" stroke-width="10"/><path d="M78 106 V28" stroke="#00B4FF" stroke-width="10" stroke-linecap="round" fill="none"/><path d="M78 30 L91 17 H101" stroke="#fff" stroke-width="4" stroke-linecap="round" fill="none"/><circle cx="106" cy="17" r="5" fill="#fff"/><circle cx="50" cy="78" r="8" fill="#fff"/></svg>'
# --- fontes ---
i0 = s.index('@font-face{font-family:Anton'); i1 = s.index(':root{', i0)
s = s[:i0] + '''@font-face{font-family:Unbounded;src:url(fonts/unbounded-latin-600-normal.woff2) format("woff2");font-weight:400 650;font-display:swap}
@font-face{font-family:Unbounded;src:url(fonts/unbounded-latin-800-normal.woff2) format("woff2");font-weight:700 900;font-display:swap}
@font-face{font-family:"Instrument Sans";src:url(fonts/instrument-sans-latin-500-normal.woff2) format("woff2");font-weight:400 600;font-display:swap}
@font-face{font-family:"Instrument Sans";src:url(fonts/instrument-sans-latin-700-normal.woff2) format("woff2");font-weight:650 900;font-display:swap}
''' + s[i1:]
rep('--display:Anton,Impact,"Arial Narrow",sans-serif; --body:Inter,-apple-system,"Helvetica Neue",Arial,sans-serif;', '--display:Unbounded,"Arial Black",sans-serif; --body:"Instrument Sans",-apple-system,"Helvetica Neue",Arial,sans-serif;')
s = s.replace(':root{', '/* Identidade Dermatolog.IA (@dermtolog.ia): azul-noite, ciano, gelo; Unbounded + Instrument Sans. */\n:root{', 1) #'/* Identidade Dermatolog.IA (@dermtolog.ia): azul-noite, ciano elétrico, gelo; Unbounded + Instrument Sans. Um só tema (escuro).')
# --- cores (paleta azul) ---
M = [("#E8650A", "#00B4FF"), ("#F4F1EC", "#EAF7FF"), ("#C4A060", "#7FD6FF"), ("#17110C", "#04162E"), ("#141312", "#061A31"), ("#CFC9BF", "#B8CFE0"), ("#1A1A1A", "#04162E"),
     ("rgba(232,101,10,", "rgba(0,180,255,"), ("#1B1A19", "#0A2240"), ("#161412", "#04162E"), ("#2A2725", "#0F2B4A"), ("#232120", "#0B2442"), ("#2D2A28", "#123152"), ("#3B3733", "#1E4468"),
     ("#A49C90", "#8DB0C9"), ("rgba(26,26,26,", "rgba(4,22,46,"), ("#FFC79E", "#BFE9FF"), ("#F3D9C6", "#D8F0FF"), ("#555", "#2B5175"), ("rgba(196,160,96,", "rgba(127,214,255,"), ("#191817", "#061A31"),
     ("#FFD9BD", "#D8F0FF"), ("#171615", "#061A31"), ("#B9500A", "#0077C2"), ("#5b5750", "#3B5C7A"), ("#F1E4C3", "#D8F0FF"), ("#EADFC6", "#D8F0FF"), ("#6B665C", "#3B5C7A"),
     ("rgba(22,21,20,", "rgba(4,22,46,"), ("rgba(10,10,10,.58)", "rgba(2,11,24,.62)"), ("#D9D2C7", "#C9E3F4"), ("rgba(35,33,32,", "rgba(11,36,66,"), ("%23999", "%238DB0C9")]
for a, b in M: s = s.replace(a, b)
s = s.replace('accent-color:#00B4FF', 'accent-color:#00B4FF')
rep('const GC = ["#00B4FF", "#7FD6FF", "#3C82FF", "#6FCF97", "#B07CE0", "#FF6B5B", "#4FC3C9", "#E0C341", "#8A847A"];', 'const GC = ["#00B4FF", "#F2A541", "#9B7BFF", "#6FCF97", "#FF6B9A", "#FF6B5B", "#4FC3C9", "#E0C341", "#8A9BB0"];')
rep('<span><i class="sw" style="background:var(--accent)"></i>a favor do diagnóstico</span>', '<span><i class="sw" style="background:#E8650A"></i>a favor do diagnóstico</span>')
# botões cheios: texto azul-noite sobre ciano (nunca branco sobre ciano)
rep('color:#04162E;background:var(--accent);cursor:pointer;transition:transform .12s,filter .12s;box-shadow:0 6px 18px rgba(0,180,255,.28)', 'color:#04162E;background:linear-gradient(180deg,#33C4FF,#00A3EA);cursor:pointer;transition:transform .12s,filter .12s;box-shadow:0 8px 22px rgba(0,180,255,.30)')
# --- tipografia dos títulos ---
s = re.sub(r'h2,h3\{font-family:var\(--display\);font-weight:400;text-transform:uppercase;letter-spacing:\.03em;', 'h2,h3{font-family:var(--display);font-weight:600;text-transform:none;letter-spacing:-.01em;', s)
s = s.replace('h2{font-size:20px;line-height:1.1;', 'h2{font-size:18px;line-height:1.2;')
s = s.replace('.verdict{font:400 30px/1.05 var(--display);text-transform:uppercase;letter-spacing:.02em;', '.verdict{font:800 24px/1.15 var(--display);letter-spacing:-.01em;')
s = s.replace('.top h1{font:400 26px/1 var(--display);letter-spacing:.03em;text-transform:uppercase;margin:0;color:var(--paper)}', '.top h1{font:600 18px/1 var(--display);letter-spacing:-.01em;margin:0;color:var(--paper)}')
s = s.replace('.top h1 b{font-weight:400;color:var(--accent)}', '.top h1 b{font-weight:600;color:var(--accent)}')
s = s.replace('.brand h1{font:400 54px/0.95 var(--display);letter-spacing:.03em;text-transform:uppercase;margin:0;color:var(--paper)}', '.brand h1{font:600 34px/1 var(--display);letter-spacing:-.02em;margin:6px 0 0;color:var(--paper)}')
s = s.replace('.brand h1 b{font-weight:400;color:var(--accent)}', '.brand h1 b{font-weight:600;color:var(--accent)}')
s = s.replace('.center h3{font-size:22px}', '.center h3{font-size:19px}').replace('.hero h3{font-size:24px}', '.hero h3{font-size:20px}').replace('.card h3{font-size:18px;', '.card h3{font-size:16px;')
s = s.replace('#why h3{font-size:15px;', '#why h3{font-size:14px;')
# --- logo e nome ---
i0 = s.index('<h1 class="logo">'); i1 = s.index('</h1>', i0) + 5
s = s[:i0] + '<h1 class="logo">' + D(28) + '<span>dermatolog<b>.ia</b></span></h1>' + s[i1:]
i0 = s.index('<div class="orb">'); i1 = s.index('</div>', i0) + 6
s = s[:i0] + '<div class="orb"><div class="disc">' + D(84) + '</div></div>' + s[i1:]
rep('.orb svg{width:100%;height:100%;filter:drop-shadow(0 10px 30px rgba(0,180,255,.35))}', '.orb .disc{width:100%;height:100%;border-radius:50%;display:grid;place-items:center;background:radial-gradient(circle at 50% 40%,#0E3560,#04162E 70%);border:2px solid rgba(0,180,255,.55);box-shadow:0 18px 50px rgba(0,180,255,.25),inset 0 0 30px rgba(0,180,255,.12)}')
rep('<h1>Derm<b>IA</b></h1>', '<h1>dermatolog<b>.ia</b></h1>')
rep('<span class="d">Dr. Pedro Schmitz · CRM/SC 38229</span>', '<span class="d">@dermtolog.ia · Dr. Pedro Schmitz · CRM/SC 38229</span>')
s = s.replace('DermIA · uso pessoal de estudo', 'Dermatolog.IA · uso pessoal de estudo')
s = s.replace('rp: { name: "DermIA" }, user: { id, name: "dermia", displayName: "DermIA" }', 'rp: { name: "Dermatolog.IA" }, user: { id, name: "dermatologia", displayName: "Dermatolog.IA" }')
s = re.sub(r'<title>[^<]*</title>', '<title>Dermatolog.IA · estudo de dermatoscopia</title>', s)
s = s.replace('<meta name="apple-mobile-web-app-title" content="DermIA">', '<meta name="apple-mobile-web-app-title" content="Dermatolog.IA">')
s = s.replace('<meta name="theme-color" content="#04162E">', '<meta name="theme-color" content="#04162E">')
s = re.sub(r'\bDermIA\b', 'Dermatolog.IA', s)
s = s.replace('const APP_VER = "v7";', 'const APP_VER = "v8";')
open(p, "w", encoding="utf8").write(s)
left = re.findall(r'Anton|Inter[,"]|#E8650A|232,101,10\)', s); print("restos:", left)
