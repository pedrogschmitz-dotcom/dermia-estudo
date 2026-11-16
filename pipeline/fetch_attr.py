import json, io, os, zipfile, time, requests, numpy as np
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
Image.MAX_IMAGE_PIXELS = None
z = zipfile.ZipFile("data/attr/gt.zip"); A = ["pigment_network", "negative_network", "streaks", "milia_like_cyst", "globules"]
ids = sorted({n.split("/")[-1].split("_attribute_")[0] for n in z.namelist() if n.endswith(".png")})
os.makedirs("data/attr/img", exist_ok=True); os.makedirs("data/attr/mask", exist_ok=True)
def one(i):
    out = f"data/attr/img/{i}.jpg"
    for t in range(4):
        try:
            j = requests.get(f"https://api.isic-archive.com/api/v2/images/{i}/", timeout=60).json(); c = j["metadata"]["clinical"]
            if not os.path.exists(out):
                r = requests.get(j["files"]["full"]["url"], timeout=180); r.raise_for_status(); im = Image.open(io.BytesIO(r.content)).convert("RGB")
                W, H = im.size; s = 448 / min(W, H); size = (max(1, round(W * s)), max(1, round(H * s))) if s < 1 else (W, H)
                im.resize(size, Image.BICUBIC).save(out, quality=93)
                for a in A:
                    m = Image.open(io.BytesIO(z.read(f"ISIC2018_Task2_Training_GroundTruth_v3/{i}_attribute_{a}.png"))).convert("L")
                    assert m.size == (W, H), (m.size, W, H); m.resize(size, Image.BILINEAR).save(f"data/attr/mask/{i}_{a}.png")
            return dict(id=i, lic=j.get("copyright_license"), at=j.get("attribution"), lesion=c.get("lesion_id"), patient=c.get("patient_id"), d3=c.get("diagnosis_3"))
        except Exception as e: err = e; time.sleep(3)
    print("falhou", i, err, flush=True); return None
with ThreadPoolExecutor(8) as ex: R = [r for r in ex.map(one, ids) if r]
json.dump(R, open("data/attr/meta.json", "w"), ensure_ascii=False); print("ok", len(R), "de", len(ids), flush=True)
