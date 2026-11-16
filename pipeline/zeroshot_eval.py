import sys, json, numpy as np, torch, open_clip
from PIL import Image
model_id, data, out = sys.argv[1], sys.argv[2], sys.argv[3]
torch.set_num_threads(2)
model, _, pre = open_clip.create_model_and_transforms(model_id); tok = open_clip.get_tokenizer(model_id); model.eval()
CL = {
 "melanoma": ["melanoma", "malignant melanoma", "invasive melanoma"],
 "nevo": ["melanocytic nevus", "benign nevus", "mole"],
 "cbc": ["basal cell carcinoma", "BCC"],
 "cec": ["squamous cell carcinoma", "SCC", "Bowen disease"],
 "ceratose_actinica": ["actinic keratosis", "solar keratosis"],
 "queratose_seborreica": ["seborrheic keratosis", "seborrheic keratosis dermoscopy"],
 "dermatofibroma": ["dermatofibroma", "benign fibrous histiocytoma"],
 "vascular": ["hemangioma", "vascular lesion", "angiokeratoma", "pyogenic granuloma"],
 "outras": ["solar lentigo", "wart", "scar", "other benign skin lesion"],
}
names = list(CL)
TPL = ["a dermoscopy image of {}", "this is dermoscopy of {}", "{}"]
with torch.no_grad():
    T = []
    for c in names:
        e = model.encode_text(tok([t.format(p) for p in CL[c] for t in TPL])); e = e / e.norm(dim=-1, keepdim=True)
        e = e.mean(0); T.append(e / e.norm())
    T = torch.stack(T)
meta = json.load(open(data + "/meta.json")); feats = []
with torch.no_grad():
    for i in range(0, len(meta), 16):
        b = torch.stack([pre(Image.open(f'{data}/img/{m["isic_id"]}.jpg').convert("RGB")) for m in meta[i:i+16]])
        f = model.encode_image(b); feats.append((f / f.norm(dim=-1, keepdim=True)).numpy())
        print(i, flush=True)
F = np.concatenate(feats); S = F @ T.numpy().T * 100
np.savez(out, feats=F, text=T.numpy(), ids=[m["isic_id"] for m in meta], classes=[m["classe"] for m in meta], names=names)
y = np.array([names.index(m["classe"]) for m in meta]); p = S.argmax(1)
print("ACERTO GERAL", (p == y).mean().round(3))
for k, c in enumerate(names):
    m = y == k; print(f"{c:22s} n={m.sum():3d} recall={(p[m]==k).mean():.2f}")
