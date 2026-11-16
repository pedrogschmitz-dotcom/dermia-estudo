import sys, json, pickle, io, os, urllib.request, numpy as np, torch
sys.path.insert(0, "/home/claude/dermia/scripts")
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
from load_dermlip import load
M = pickle.load(open("work/fine_model.pkl", "rb")); sc, clf, names, gmap, T = M["sc"], M["clf"], M["names"], M["gmap"], M["T"]
cv = json.load(open("work/fine_cv.json"))
A = clf.coef_ / sc.scale_
model, pre, tok, _ = load(); v = model.visual
Wh = v.head.weight.detach().numpy().astype(np.float64); bh = v.head.bias.detach().numpy(); gam = v.norm.weight.detach().numpy(); bet = v.norm.bias.detach().numpy()
U = A @ Wh; UG = U * gam; const = A @ bh - A @ sc.mean_ + clf.intercept_ + U @ bet
# verificação numérica
pool = json.load(open("data/isic_test/pool_meta.json"))
for k in (0, 5):
    x = pre(Image.open(f'data/isic_test/img/{pool[k]["isic_id"]}.jpg').convert("RGB"))[None]
    with torch.no_grad():
        xx = v.patch_embed(x); xx = torch.cat((v.cls_token.expand(1, -1, -1), xx), 1) + v.pos_embed
        for b in v.blocks: xx = b(xx, rel_pos_bias=None)
        xx = v.norm(xx); t = xx[0, 1:].numpy().astype(np.float64); emb = v.head(v.norm(xx[:, 1:].mean(1)))[0].numpy()
    logit = A @ (emb - sc.mean_) + clf.intercept_; pooled = t.mean(0); m = pooled.mean(); s = np.sqrt(pooled.var() + 1e-6)
    rec = ((t @ (UG / s).T - m * (UG / s).sum(1)) / len(t)).sum(0) + const; print("decomposição, máx diferença:", float(np.abs(rec - logit).max()))
head = dict(names=names, groups=[gmap[n] for n in names], mean=sc.mean_.tolist(), scale=sc.scale_.tolist(), coef=clf.coef_.tolist(), intercept=clf.intercept_.tolist(), T=T, hm_u=UG.tolist(), ln_eps=1e-6, cv=cv)
json.dump(head, open("app/data/head_fine.json", "w"), ensure_ascii=False); print("head_fine KB", len(json.dumps(head)) // 1024)
# banco: acrescenta as 1913 novas
bank = json.load(open("app/data/bank.json")); old = np.fromfile("app/data/bank.bin", dtype=np.int8).reshape(-1, 512); assert len(old) == len(bank["items"])
plan = json.load(open("work/fine_plan.json")); lab = plan["lab"]; fm = json.load(open("data/fine_meta.json")); NF = np.load("work/dermlip_fine_img.npy")
H = json.load(open("app/data/head.json")); gnames = H["names"]
for it in bank["items"]:
    l = lab.get(it["id"])
    if l: it["f"] = names.index(l[0]); it["dx"] = l[0]
    else: it["f"] = -1
for m in fm:
    l = lab[m["isic_id"]]; bank["items"].append(dict(id=m["isic_id"], c=gnames.index(l[1]), f=names.index(l[0]), dx=l[0], lic=m["licenca"], at=m.get("atribuicao"), conf="histopatologia", site=m.get("local"), age=m.get("idade"), sex=m.get("sexo"), src="ISIC"))
E2 = NF / np.linalg.norm(NF, axis=1, keepdims=True); new8 = np.clip(np.round(E2 * 127), -127, 127).astype(np.int8)
np.concatenate([old, new8]).tofile("app/data/bank.bin"); bank["n"] = len(bank["items"]); json.dump(bank, open("app/data/bank.json", "w"), ensure_ascii=False)
import collections; print("banco", bank["n"], collections.Counter(i["lic"] for i in bank["items"]), "sem f:", sum(1 for i in bank["items"] if i["f"] < 0))
# miniaturas
ids = [i["id"] for i in bank["items"]]; os.makedirs("work/thumbs", exist_ok=True)
def get(i):
    f = f"work/thumbs/{i}.jpg"
    if os.path.exists(f): return True
    for _ in range(3):
        try:
            d = urllib.request.urlopen(f"https://isic-archive.s3.us-east-1.amazonaws.com/thumbnails/{i}_thumbnail.jpg", timeout=30).read(); im = Image.open(io.BytesIO(d)).convert("RGB"); im.thumbnail((200, 200)); im.save(f, quality=72, optimize=True); return True
        except Exception: pass
    return False
with ThreadPoolExecutor(16) as ex: ok = list(ex.map(get, ids))
print("miniaturas faltando", ok.count(False))
CH = 10 * 1024 * 1024; idx = {}; chunks = []; cur = bytearray()
for i in ids:
    if not os.path.exists(f"work/thumbs/{i}.jpg"): continue
    b = open(f"work/thumbs/{i}.jpg", "rb").read()
    if len(cur) + len(b) > CH: chunks.append(bytes(cur)); cur = bytearray()
    idx[i] = [len(chunks), len(cur), len(b)]; cur += b
chunks.append(bytes(cur)); import glob; [os.remove(f) for f in glob.glob("app/thumbs/t*.bin")]
for n, c in enumerate(chunks): open(f"app/thumbs/t{n}.bin", "wb").write(c)
json.dump(idx, open("app/thumbs/index.json", "w")); print("miniaturas em", len(chunks), "arquivos", [len(c) // 1024 for c in chunks])
