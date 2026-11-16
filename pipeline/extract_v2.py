import sys, json, numpy as np, torch
sys.path.insert(0, "/home/claude/dermia/scripts")
from load_dermlip import load
from PIL import Image, ImageOps
mode, outp = sys.argv[1], sys.argv[2]; views = sys.argv[3].split(",") if len(sys.argv) > 3 else ["id"]
sub = json.load(open(sys.argv[4])) if len(sys.argv) > 4 else None
torch.set_num_threads(2)
model, pre, tok, _ = load(); v = model.visual
pool = json.load(open("data/isic_test/pool_meta.json")); fm = json.load(open("data/fine_meta.json"))
items = [(m["isic_id"], f'data/isic_test/img/{m["isic_id"]}.jpg') for m in pool] + [(m["isic_id"], f'data/fine_img/{m["isic_id"]}.jpg') for m in fm]
if sub: s = set(sub); items = [it for it in items if it[0] in s]
if len(sys.argv) > 5: items = json.load(open(sys.argv[5]))   # lista [[id, caminho], ...] para dados extras
def prep(im, view):
    if mode == "pad":
        w, h = im.size; s = max(w, h); fill = tuple(int(x) for x in np.asarray(im).reshape(-1, 3).mean(0)); bg = Image.new("RGB", (s, s), fill); bg.paste(im, ((s - w) // 2, (s - h) // 2)); im = bg
    if view in ("h", "hv"): im = ImageOps.mirror(im)
    if view in ("v", "hv"): im = ImageOps.flip(im)
    if view == "r90": im = im.rotate(90, expand=True)
    return pre(im)
def feats(x):
    with torch.no_grad():
        xx = v.patch_embed(x); xx = torch.cat((v.cls_token.expand(x.shape[0], -1, -1), xx), 1) + v.pos_embed
        for b in v.blocks: xx = b(xx, rel_pos_bias=None)
        xx = v.norm(xx); t = xx[:, 1:]; mean = t.mean(1); emb = v.head(v.norm(mean)); B = t.shape[0]; g = t.reshape(B, 14, 14, -1)
        grid = torch.stack([g[:, :7, :7].mean((1, 2)), g[:, :7, 7:].mean((1, 2)), g[:, 7:, :7].mean((1, 2)), g[:, 7:, 7:].mean((1, 2))], 1).reshape(B, -1)
        return torch.cat([emb, mean, t.max(1).values, grid], 1).numpy()
out = {vw: [] for vw in views}
for i in range(0, len(items), 16):
    ims = [Image.open(p).convert("RGB") for _, p in items[i:i + 16]]
    for vw in views: out[vw].append(feats(torch.stack([prep(im, vw) for im in ims])))
    if i % 320 == 0: print(i, len(items), flush=True)
json.dump([it[0] for it in items], open(outp + "_ids.json", "w"))
for vw in views: np.save(f"{outp}_{vw}.npy", np.concatenate(out[vw]).astype(np.float32))
print("FIM", flush=True)
