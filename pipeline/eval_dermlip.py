import json, numpy as np
d = "data/isic_test"
pool = json.load(open(d + "/pool_meta.json")); test_ids = {m["isic_id"] for m in json.load(open(d + "/meta.json"))}
names = ["melanoma","nevo","cbc","cec","ceratose_actinica","queratose_seborreica","dermatofibroma","vascular","outras"]
y = np.array([names.index(m["classe"]) for m in pool]); in500 = np.array([m["isic_id"] in test_ids for m in pool])
F = np.load("work/dermlip_img.npy"); F = F / np.linalg.norm(F, axis=1, keepdims=True); T = np.load("work/dermlip_text.npz")
def rep(tag, p, mask):
    yy, pp = y[mask], p[mask]; rec = [(pp[yy == k] == k).mean() for k in range(9)]
    print(f"{tag}: acerto={np.mean(pp==yy):.3f} média_por_classe={np.mean(rec):.3f} | " + " ".join(f"{n[:6]}={r:.2f}" for n, r in zip(names, rec)))
for k in ("A", "B"):
    p = (F @ T[k].T).argmax(1)
    rep(f"zero-shot modelo {k} (500)", p, in500); rep(f"zero-shot modelo {k} (3451)", p, np.ones(len(y), bool))
