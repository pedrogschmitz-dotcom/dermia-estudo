import sys, json, numpy as np
sys.path.insert(0, "/home/claude/dermia/scripts")
from cvlib import *
plan = json.load(open("work/fine_plan.json")); lab = plan["lab"]; pool = json.load(open("data/isic_test/pool_meta.json")); fm = json.load(open("data/fine_meta.json"))
gid = {m["isic_id"]: (m.get("patient_id") or m.get("lesion_id") or m["isic_id"]) for m in pool + fm}
for mode in ("crop", "squash"):
    ids, X = load(f"work/fx/old_{mode}"); names = sorted({lab[i][0] for i in ids}); y = np.array([names.index(lab[i][0]) for i in ids]); grp = np.array([gid[i] for i in ids]); K = len(names)
    for parts, Cs in ((["emb"], [0.003]), (["mean"], [0.001, 0.003]), (["mean", "grid"], [0.0003, 0.001]), (["mean", "grid", "max"], [0.0003, 0.001])):
        for C in Cs:
            P, _ = cv(cols(X, parts), y, grp, C, K); print(mode, "+".join(parts), "C", C, rep(P, y), flush=True)
