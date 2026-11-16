import json, os, io, time, requests
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
out = "data/study_img"; os.makedirs(out, exist_ok=True)
cases = json.load(open("data/study_cases.json")); pool = {m["isic_id"] for m in json.load(open("data/isic_test/pool_meta.json"))}
ids = [c["id"] for c in cases if c["id"].startswith("ISIC_")]
def one(i):
    p = f"{out}/{i}.jpg"
    if i in pool and os.path.exists(f"data/isic_test/img/{i}.jpg"):
        if not os.path.exists(p): os.link(f"data/isic_test/img/{i}.jpg", p)
        return i, {"attrib": None}
    for t in range(3):
        try:
            j = requests.get(f"https://api.isic-archive.com/api/v2/images/{i}/", timeout=60).json()
            r = requests.get(j["files"]["full"]["url"], timeout=90); r.raise_for_status()
            im = Image.open(io.BytesIO(r.content)).convert("RGB"); im.thumbnail((512, 512)); im.save(p, quality=92)
            return i, {"attrib": j.get("attribution"), "api_license": j.get("copyright_license")}
        except Exception as e: err = e; time.sleep(2)
    return i, {"erro": str(err)[:80]}
with ThreadPoolExecutor(6) as ex: res = dict(ex.map(one, ids))
bad = [k for k, v in res.items() if "erro" in v]
meta = []
for c in cases:
    if c["id"] in res and "erro" not in res[c["id"]] and os.path.exists(f'{out}/{c["id"]}.jpg'):
        meta.append(dict(isic_id=c["id"], dx=c["dx"], sub=c["sub"], site=c.get("site"), age=c.get("age"), sex=c.get("sex"), conf=c.get("conf"),
                         licenca=c.get("lic"), atribuicao=res[c["id"]].get("attrib")))
json.dump(meta, open("data/study_meta_isic.json", "w"), ensure_ascii=False)
print("ISIC no estudo:", len(ids), "baixadas:", len(meta), "no pool:", sum(i in pool for i in ids), "falhas:", bad[:5], len(bad))
