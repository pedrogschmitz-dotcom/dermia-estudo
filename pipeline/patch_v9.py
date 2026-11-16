p = "app/index.html"; s = open(p, encoding="utf8").read()
def rep(a, b, cnt=1):
    global s
    assert s.count(a) == cnt, (s.count(a), a[:70]); s = s.replace(a, b)
# layout de app (igual ao Estúdio): corpo fixo em coluna; topo, área que rola, barra de abas no fim
rep('@media (prefers-reduced-motion:reduce)', '''/* layout de app (mesma solução do Estúdio Curae) */
html{height:100%}
body{position:fixed;inset:0;display:flex;flex-direction:column;height:var(--apph,100%);overflow:hidden;min-height:0}
.top{position:relative;flex:none}
#scroller{flex:1 1 auto;min-height:0;overflow-y:auto;-webkit-overflow-scrolling:touch;overscroll-behavior:contain;scroll-behavior:smooth}
#scroller>.wrap{padding-bottom:22px}
.tabbar{position:relative!important;left:auto;right:auto;bottom:auto!important;flex:none;padding:6px 12px calc(4px + env(safe-area-inset-bottom) * .8)}
.tabbar button{padding:5px 4px}
.tabs{top:6px!important}
.sec{scroll-margin-top:62px!important}
#editor,#loading{scroll-margin-top:8px!important}
@media (prefers-reduced-motion:reduce){#scroller{scroll-behavior:auto}}
@media (prefers-reduced-motion:reduce)''')
rep('<div class="wrap">', '<div id="sap" style="position:fixed;top:0;left:0;width:1px;height:env(safe-area-inset-top);visibility:hidden;pointer-events:none"></div>\n<main id="scroller">\n<div class="wrap">')
rep('<nav class="tabbar" aria-label="Menu">', '</main>\n<nav class="tabbar" aria-label="Menu">')
# script de altura do iPhone instalado (cópia do Estúdio)
rep('</style>\n</head>', '''</style>
<script>
/* iPhone instalado: a tela às vezes fica mais curta que o aparelho e sobra faixa embaixo da barra */
(function(){function fit(){var st=navigator.standalone||matchMedia('(display-mode: standalone)').matches;var p=document.getElementById('sap');var top=p?p.offsetHeight:0;var sh=Math.max(screen.height,screen.width)>innerHeight&&innerWidth<innerHeight?screen.height:innerHeight;var gap=sh-innerHeight;document.documentElement.style.setProperty('--apph',(st&&top>0&&gap>0&&gap<100?sh:innerHeight)+'px');}
addEventListener('resize',fit);addEventListener('orientationchange',function(){setTimeout(fit,300)});addEventListener('pageshow',fit);document.addEventListener('DOMContentLoaded',fit);})();
</script>
</head>''')
# rolagem agora é do #scroller
rep('document.documentElement.scrollTop = 0;', '$("scroller").scrollTop = 0;')
rep('window.scrollTo(0, 0); }', '$("scroller").scrollTop = 0; }')
rep('{ rootMargin: "-35% 0px -60% 0px" }', '{ root: $("scroller"), rootMargin: "-25% 0px -65% 0px" }')
s = s.replace('const APP_VER = "v8";', 'const APP_VER = "v9";')
open(p, "w", encoding="utf8").write(s); print("ok")
