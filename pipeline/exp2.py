import sys, json, time, numpy as np, warnings
sys.path.insert(0, "/home/claude/dermia/scripts")
warnings.filterwarnings("ignore")
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedGroupKFold
from joblib import Parallel, delayed
from cvlib import cols, rep
import data3
D = data3.get(); y, grp, names = D["y"], D["grp"], D["names"]; K = len(names); Cm, nos = data3.compat(names, D["gmap"])
print("N", len(y), "classes", K, "| sem id:", D["n_noid"], "em", D["n_dupgroups"], "grupos", flush=True)
sp = list(StratifiedGroupKFold(5, shuffle=True, random_state=0).split(D["Xid"], y, grp))
def fold(Xtr, ytr, Xte, C):
    sc = StandardScaler().fit(Xtr); m = LogisticRegression(C=C, max_iter=300, class_weight="balanced").fit(sc.transform(Xtr), ytr); z = np.full((len(Xte), K), -50.0); z[:, m.classes_] = m.decision_function(sc.transform(Xte)); return z
def run(tag, parts, C, aug):
    t = time.time(); A = cols(D["Xid"], parts); B = cols(D["Xh"], parts)
    R = Parallel(n_jobs=2)(delayed(fold)(np.concatenate([A[tr], B[tr]]) if aug else A[tr], np.concatenate([y[tr], y[tr]]) if aug else y[tr], (A[te] + B[te]) / 2 if aug else A[te], C) for tr, te in sp)
    Z = np.zeros((len(y), K)); [Z.__setitem__(te, r) for (tr, te), r in zip(sp, R)]; r = rep(Z, y); pred = Z.argmax(1); r["compat"] = round(float(Cm[pred, y].mean()), 4)
    print(tag, "+".join(parts), "C", C, "aug+tta" if aug else "", r, f"{time.time()-t:.0f}s", flush=True); np.save(f"work/oof_{tag}.npy", Z); return r
for tag, parts, C, aug in [(a.split(":")[0], a.split(":")[1].split("+"), float(a.split(":")[2]), a.split(":")[3] == "1") for a in sys.argv[1:]]: run(tag, parts, C, aug)
