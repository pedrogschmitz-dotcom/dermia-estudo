import sys, json, time
sys.path.insert(0, "/home/claude/dermia/scripts")
from playwright.sync_api import sync_playwright
from srv import serve
from PIL import Image
pw = open("work/passphrase.txt").read().strip(); img = json.load(open("data/master.json"))["new"][40]["path"]; srv = serve("app", 8805)
with sync_playwright() as p:
    br = p.webkit.launch(); pg = br.new_context(**p.devices["iPhone 15"]).new_page(); L = []
    pg.on("pageerror", lambda e: L.append("ERRO " + str(e))); pg.on("console", lambda m: L.append(m.text) if m.type == "error" else None)
    pg.goto("http://127.0.0.1:8805/index.html"); pg.wait_for_selector("#m-install:not(.hide)", timeout=30000)
    pg.fill("#pw", pw); pg.press("#pw", "Enter"); pg.wait_for_selector("#entrada:not(.hide)", timeout=240000); pg.wait_for_timeout(400)
    vh = pg.evaluate("innerHeight"); tb = pg.locator(".tabbar").bounding_box(); print("tela", vh, "| barra de abas: topo", round(tb["y"]), "fim", round(tb["y"] + tb["height"]), "| encostada no fim:", abs(tb["y"] + tb["height"] - vh) < 2)
    pg.screenshot(path="work/v9_1.png")
    pg.click("#hero-btn"); pg.wait_for_selector("#sheet:not(.hide)"); pg.click("#sheet-x")
    pg.set_input_files("#foto", img); pg.wait_for_selector("#editor:not(.hide)"); pg.click("#ed-go"); t = time.time()
    while not pg.evaluate("!!(LAST && LAST.nn && !busy)"):
        if time.time() - t > 90: raise SystemExit(str(L))
        time.sleep(.2)
    pg.wait_for_timeout(1200); pg.click("#tabs button[data-t=sec-casos]"); pg.wait_for_timeout(1200)
    st = pg.evaluate("$('scroller').scrollTop"); tabs = pg.locator("#tabs").bounding_box(); print("rolou até Casos:", st > 500, "| abas do resultado visíveis no topo:", tabs["y"] < 140, "| aba ativa:", pg.evaluate("[...document.querySelectorAll('#tabs button.on')].map(b=>b.textContent)"))
    pg.screenshot(path="work/v9_2.png")
    for v in ("sobre", "ajustes", "analisar"): pg.click(f".tabbar button[data-v={v}]"); pg.wait_for_timeout(300)
    print("voltou ao resultado:", pg.is_visible("#res"), "| barra ainda no fim:", abs(pg.locator(".tabbar").bounding_box()["y"] + pg.locator(".tabbar").bounding_box()["height"] - vh) < 2)
    pg.click("#cam-btn"); print("câmera do topo abre o menu:", pg.is_visible("#sheet")); pg.click("#sheet-bg")
    pg.set_input_files("#foto", img); pg.wait_for_selector("#editor:not(.hide)"); pg.click("#ed-back"); print("cancelar volta ao resultado:", pg.is_visible("#res"))
    pg.click("#lock-now"); pg.wait_for_selector("#lock:not(.hide)", timeout=30000); print("cadeado bloqueia: ok")
    print("erros:", L[:5]); br.close()
srv.shutdown()
a = Image.open("work/v9_1.png"); b = Image.open("work/v9_2.png"); c = Image.new("RGB", (786, 852)); c.paste(a.resize((393, 852)), (0, 0)); c.paste(b.resize((393, 852)), (393, 0)); c.save("work/v9_sheet.png")
