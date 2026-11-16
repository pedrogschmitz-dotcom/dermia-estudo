import sys, json, random, os, io, time, requests
from PIL import Image
out = sys.argv[1]; os.makedirs(out + "/img", exist_ok=True)
BASE = 'image_type:"dermoscopic" AND diagnosis_confirm_type:"histopathology" AND copyright_license:"CC-0"'
API = "https://api.isic-archive.com/api/v2/images/search/"
# classe -> (lista de diagnosis_3 ou filtro por diagnosis_2, n alvo)
PLAN = {
 "melanoma": ('diagnosis_2:"Malignant melanocytic proliferations (Melanoma)"', 90),
 "nevo": ('diagnosis_3:"Nevus"', 90),
 "cbc": ('diagnosis_3:"Basal cell carcinoma"', 75),
 "cec": ('(diagnosis_3:"Squamous cell carcinoma, NOS" OR diagnosis_3:"Squamous cell carcinoma in situ" OR diagnosis_3:"Squamous cell carcinoma, Invasive")', 40),
 "ceratose_actinica": ('diagnosis_3:"Solar or actinic keratosis"', 45),
 "queratose_seborreica": ('diagnosis_3:"Seborrheic keratosis"', 50),
 "dermatofibroma": ('diagnosis_3:"Dermatofibroma"', 40),
 "vascular": ('(diagnosis_3:"Hemangioma" OR diagnosis_3:"Angiokeratoma" OR diagnosis_3:"Pyogenic granuloma")', 35),
 "outras": ('(diagnosis_3:"Solar lentigo" OR diagnosis_3:"Lentigo NOS" OR diagnosis_3:"Verruca" OR diagnosis_3:"Fibroepithelial polyp" OR diagnosis_3:"Scar" OR diagnosis_3:"Neurofibroma" OR diagnosis_3:"Lichen planus like keratosis" OR diagnosis_3:"Sebaceous hyperplasia" OR diagnosis_3:"Clear cell acanthoma" OR diagnosis_3:"Lentigo simplex")', 35),
}
rng = random.Random(42); rows = []
def list_all(q):
    url = API; params = {"query": BASE + " AND " + q, "limit": 100}; res = []
    while url:
        r = requests.get(url, params=params, timeout=60); r.raise_for_status(); j = r.json()
        res += j["results"]; url = j.get("next"); params = None
    return res
for cls, (q, n) in PLAN.items():
    allr = [i for i in list_all(q) if i["metadata"]["clinical"].get("diagnosis_3")!="Melanoma metastasis"]; rng.shuffle(allr); pick = allr[:n]
    print(cls, "disponíveis", len(allr), "sorteadas", len(pick), flush=True)
    for it in pick:
        c = it["metadata"]["clinical"]
        rows.append(dict(isic_id=it["isic_id"], classe=cls, d2=c.get("diagnosis_2"), d3=c.get("diagnosis_3"),
            licenca=it["copyright_license"], atribuicao=it.get("attribution"), url=it["files"]["full"]["url"],
            sexo=c.get("sex"), idade=c.get("age_approx"), local=c.get("anatom_site_1")))
def dl(row):
    p = f'{out}/img/{row["isic_id"]}.jpg'
    if os.path.exists(p): return
    for t in range(3):
        try:
            r = requests.get(row["url"], timeout=60); r.raise_for_status()
            im = Image.open(io.BytesIO(r.content)).convert("RGB"); im.thumbnail((512, 512)); im.save(p, quality=92); return
        except Exception as e: err = e; time.sleep(2)
    print("falhou", row["isic_id"], err)
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(6) as ex: list(ex.map(dl, rows))
json.dump(rows, open(out + "/meta.json", "w"), ensure_ascii=False, indent=1)
print("total", len(rows), "imagens", len(os.listdir(out + "/img")))
