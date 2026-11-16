import sys, json, requests, random, collections, io, os, time
sys.path.insert(0, "/home/claude/dermia/scripts")
from fine_labels2 import fine2
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
API = "https://api.isic-archive.com/api/v2/images/search/"; CAP = 600; rng = random.Random(7)
pool = json.load(open("data/isic_test/pool_meta.json")); fm = json.load(open("data/fine_meta.json")); F = json.load(open("work/fine_all.json"))
have = {}
for m in pool: d = F.get(m["isic_id"], [m["d3"], None, None]); have[m["isic_id"]] = dict(id=m["isic_id"], path=f'data/isic_test/img/{m["isic_id"]}.jpg', d=d, lic=m["licenca"], at=m.get("atribuicao"), sex=m.get("sexo"), age=m.get("idade"), site=m.get("local"), lesion=m.get("lesion_id"), patient=m.get("patient_id"))
for m in fm: have[m["isic_id"]] = dict(id=m["isic_id"], path=f'data/fine_img/{m["isic_id"]}.jpg', d=F[m["isic_id"]], lic=m["licenca"], at=m.get("atribuicao"), sex=m.get("sexo"), age=m.get("idade"), site=m.get("local"), lesion=m.get("lesion_id"), patient=m.get("patient_id"))
def rec(it):
    c = it["metadata"]["clinical"]; return dict(id=it["isic_id"], path=f'data/x_img/{it["isic_id"]}.jpg', d=[c.get("diagnosis_3"), c.get("diagnosis_4"), c.get("diagnosis_5")], lic=it["copyright_license"], at=it.get("attribution"), sex=c.get("sex"), age=c.get("age_approx"), site=c.get("anatom_site_1"), lesion=c.get("lesion_id"), patient=c.get("patient_id"), url=it["files"]["full"]["url"])
def listq(q):
    url = API; params = {"query": q, "limit": 100}; res = []
    while url:
        for t in range(4):
            try: j = requests.get(url, params=params, timeout=90).json(); break
            except Exception as e: time.sleep(3)
        res += [rec(i) for i in j["results"]]; url = j.get("next"); params = None
    return res
B2 = 'image_type:"dermoscopic" AND diagnosis_confirm_type:"histopathology" AND (copyright_license:"CC-BY" OR copyright_license:"CC-BY-NC")'
D4 = ["Melanoma Invasive, Nodular", "Melanoma in situ, Lentigo maligna type", "Melanoma Invasive, On chronically sun-exposed skin or lentigo maligna melanoma", "Melanoma Invasive, Superficial spreading", "Melanoma in situ, Superficial spreading", "Melanoma in situ, associated with a nevus", "Blue nevus", "Nevus, Reed", "Nevus, Spitz", "Nevus, Combined", "Nevus, Recurrent or persistent", "Nevus, NOS, Compound", "Nevus, NOS, Junctional", "Nevus, NOS, Dermal", "Nevus, Lentiginous", "Basal cell carcinoma, Superficial"]
D3 = ["Keratoacanthoma", "Dermatofibroma", "Scar", "Solar lentigo", "Lentigo NOS", "Lentigo simplex", "Lichen planus like keratosis", "Hemangioma", "Angiokeratoma", "Pyogenic granuloma", "Verruca", "Fibroepithelial polyp", "Melanoma metastasis", "Squamous cell carcinoma, Invasive", "Squamous cell carcinoma in situ", "Solar or actinic keratosis", "Melanoma Invasive"]
cand = {}
for v in D4:
    r = listq(B2 + f' AND diagnosis_4:"{v}"'); print(len(r), v, flush=True); cand.update({x["id"]: x for x in r})
for v in D3:
    r = listq(B2 + f' AND diagnosis_3:"{v}"'); print(len(r), v, flush=True); cand.update({x["id"]: x for x in r})
# sobras CC-0 já listadas (fine_all) que não foram extraídas: metadados completos vêm depois, por imagem
left = {i: dict(id=i, path=f"data/x_img/{i}.jpg", d=d, lic="CC-0", need_meta=True) for i, d in F.items() if i not in have}
by = collections.defaultdict(list)
for x in list(cand.values()) + list(left.values()):
    if x["id"] not in have: by[fine2(*x["d"])[0]].append(x)
cnt = collections.Counter(fine2(*x["d"])[0] for x in have.values()); sel = []
for l in sorted(set(by) | set(cnt)):
    need = max(0, CAP - cnt[l]); c = by.get(l, []); rng.shuffle(c); c.sort(key=lambda x: 0 if x["lic"] == "CC-0" else 1); take = c[:need]; sel += take
    print(f"{cnt[l]:5d} +{len(take):4d} (de {len(c)})  {l}", flush=True)
print("baixar", len(sel), flush=True); os.makedirs("data/x_img", exist_ok=True)
def dl(x):
    for t in range(4):
        try:
            if x.get("need_meta") or "url" not in x:
                j = requests.get(f'https://api.isic-archive.com/api/v2/images/{x["id"]}/', timeout=60).json(); r = rec(j); r["d"] = x["d"]; x.clear(); x.update(r)
            if not os.path.exists(x["path"]):
                r = requests.get(x["url"], timeout=90); r.raise_for_status(); im = Image.open(io.BytesIO(r.content)).convert("RGB"); im.thumbnail((512, 512)); im.save(x["path"], quality=92)
            return True
        except Exception as e: time.sleep(2)
    return False
with ThreadPoolExecutor(8) as ex: ok = list(ex.map(dl, sel))
new = [x for x, o in zip(sel, ok) if o]; print("ok", len(new), "falhas", ok.count(False), flush=True)
for x in new: x.pop("url", None); x.pop("need_meta", None)
json.dump(dict(old=list(have.values()), new=new), open("data/master.json", "w"), ensure_ascii=False)
json.dump([[x["id"], x["path"]] for x in new], open("work/x_items.json", "w")); print("FIM", flush=True)
