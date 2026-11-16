import json, random, os, io, time, requests
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
out = "data/nonderm"; os.makedirs(out + "/img", exist_ok=True); rng = random.Random(7); rows = []
API = "https://api.isic-archive.com/api/v2/images/search/"
for q, n in (('image_type:"clinical: close-up" AND copyright_license:"CC-0"', 220), ('image_type:"TBP tile: close-up" AND copyright_license:"CC-0"', 100)):
    r = requests.get(API, params={"query": q, "limit": 100}, timeout=60); r.raise_for_status(); j = r.json()
    res = j["results"]
    while len(res) < 600 and j.get("next"):
        j = requests.get(j["next"], timeout=60).json(); res += j["results"]
    rng.shuffle(res); rows += [dict(isic_id=i["isic_id"], url=i["files"]["full"]["url"], tipo=i["metadata"]["acquisition"].get("image_type")) for i in res[:n]]
def dl(m):
    p = f'{out}/img/{m["isic_id"]}.jpg'
    if os.path.exists(p): return
    for t in range(3):
        try:
            r = requests.get(m["url"], timeout=60); r.raise_for_status(); im = Image.open(io.BytesIO(r.content)).convert("RGB"); im.thumbnail((512, 512)); im.save(p, quality=92); return
        except Exception: time.sleep(2)
with ThreadPoolExecutor(6) as ex: list(ex.map(dl, rows))
rows = [m for m in rows if os.path.exists(f'{out}/img/{m["isic_id"]}.jpg')]; json.dump(rows, open(out + "/meta.json", "w"))
print(len(rows), {t: sum(m["tipo"] == t for m in rows) for t in {m["tipo"] for m in rows}})
