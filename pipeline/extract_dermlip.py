import sys, json, numpy as np, torch
sys.path.insert(0, "/home/claude/dermia/scripts")
from load_dermlip import load
from PIL import Image
data, outp = sys.argv[1], sys.argv[2]
META = sys.argv[3] if len(sys.argv) > 3 else "pool_meta.json"
IMGD = sys.argv[4] if len(sys.argv) > 4 else data + "/img"
torch.set_num_threads(2)
model, pre, tok, _r = load()
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
TPL = {"A": ["This is a dermatological image of {}"], "B": ["a dermoscopy image of {}", "this is dermoscopy of {}", "{}"]}
txt = {}
with torch.no_grad():
    for k, tp in TPL.items():
        T = []
        for c in CL:
            e = model.encode_text(tok([t.format(p) for p in CL[c] for t in tp])); e = e / e.norm(dim=-1, keepdim=True)
            e = e.mean(0); T.append((e / e.norm()).numpy())
        txt[k] = np.stack(T)
np.savez(outp + "_text.npz", **txt); print("texto ok", flush=True)
meta = json.load(open(META)); F = []
with torch.no_grad():
    for i in range(0, len(meta), 16):
        b = torch.stack([pre(Image.open(f'{IMGD}/{m["isic_id"]}.jpg').convert("RGB")) for m in meta[i:i+16]])
        f = model.encode_image(b); F.append(f.numpy())
        if i % 160 == 0: print(i, flush=True)
np.save(outp + "_img.npy", np.concatenate(F)); print("FIM", flush=True)
