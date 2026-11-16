import sys, json, time, numpy as np, onnxruntime as ort
sys.path.insert(0, "/home/claude/dermia/scripts")
from playwright.sync_api import sync_playwright
from srv import serve
from PIL import Image
import torchvision.transforms as TT
pw = open("work/passphrase.txt").read().strip(); AT = json.load(open("app/data/attr.json")); W = np.array(AT["W"]); b = np.array(AT["b"])
meta = json.load(open("data/attr/meta.json")); pick = [m["id"] for m in meta[5:17]]
RS = TT.Compose([TT.Resize(224, interpolation=TT.InterpolationMode.BICUBIC, antialias=True), TT.CenterCrop(224), TT.ToTensor(), TT.Normalize((0.48145466, 0.4578275, 0.40821073), (0.26862954, 0.26130258, 0.27577711))])
S = ort.InferenceSession("work/q_B.onnx"); srv = serve("app", 8806)
with sync_playwright() as p:
    br = p.webkit.launch(); pg = br.new_context(**p.devices["iPhone 15"]).new_page(); L = []; pg.on("pageerror", lambda e: L.append(str(e)))
    pg.goto("http://127.0.0.1:8806/index.html"); pg.wait_for_selector("#m-install:not(.hide)", timeout=30000); pg.fill("#pw", pw); pg.press("#pw", "Enter"); pg.wait_for_selector("#entrada:not(.hide)", timeout=240000); pg.evaluate("SKIP = true")
    for n, i in enumerate(pick):
        pg.evaluate("LAST = null"); pg.set_input_files("#foto", f"data/attr/img/{i}.jpg"); t = time.time()
        while not pg.evaluate("!!(LAST && LAST.nn && !busy)"):
            if time.time() - t > 90: raise SystemExit(str(L))
            time.sleep(.2)
        js = np.array(pg.evaluate("LAST.attr.map(a => Array.from(a))"))
        tok = S.run(["tok"], {"img": RS(Image.open(f"data/attr/img/{i}.jpg").convert("RGB")).numpy()[None]})[0][0].astype(np.float64); g = tok.mean(0)
        py = 1 / (1 + np.exp(-(tok @ W[:, :768].T + (g @ W[:, 768:].T) + b))).T
        det_py = [AT["pt"][k] for k in range(5) if (py[k] >= AT["th"][k]).any() and py[k].max() >= AT["gate"][k]]; det_js = pg.evaluate("attrSummary().filter(a=>a.on).map(a=>a.pt)")
        print(i, "| navegador:", det_js, "| Python:", det_py, "| iguais:", sorted(det_js) == sorted(det_py))
    pg.click("#sg-attr"); pg.wait_for_timeout(400); pg.locator("#sec-mapa .card").screenshot(path="work/v10_attr.png")
    pg.click(".tabbar button[data-v=sobre]"); pg.wait_for_timeout(300); print(pg.inner_text("#acc")[:120].replace("\n", " ")); print("erros:", L[:3]); br.close()
srv.shutdown()
