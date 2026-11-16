import sys, json, numpy as np, collections
sys.path.insert(0, "/home/claude/dermia/scripts")
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedGroupKFold
from scipy.optimize import minimize_scalar
plan = json.load(open("work/fine_plan.json")); lab = plan["lab"]
pool = json.load(open("data/isic_test/pool_meta.json")); fm = json.load(open("data/fine_meta.json"))
F = np.concatenate([np.load("work/dermlip_img.npy"), np.load("work/dermlip_fine_img.npy")]); meta = pool + fm
assert len(F) == len(meta), (len(F), len(meta))
ids = [m["isic_id"] for m in meta]; names = sorted({v[0] for v in lab.values()}); gmap = {v[0]: v[1] for v in lab.values()}
y = np.array([names.index(lab[i][0]) for i in ids]); grp = [m.get("patient_id") or m.get("lesion_id") or m["isic_id"] for m in meta]
cnt = collections.Counter(y); print("n", len(y), "classes", len(names), "min", min(cnt.values()))
def cv(C):
    P = np.zeros((len(y), len(names)))
    for tr, te in StratifiedGroupKFold(5, shuffle=True, random_state=0).split(F, y, grp):
        sc = StandardScaler().fit(F[tr]); m = LogisticRegression(C=C, max_iter=2000, class_weight="balanced").fit(sc.transform(F[tr]), y[tr])
        pr = np.full((len(te), len(names)), 1e-9); pr[:, m.classes_] = m.predict_proba(sc.transform(F[te])); P[te] = pr
    return P
best = None
for C in (0.001, 0.003, 0.01):
    P = cv(C); top1 = (P.argmax(1) == y).mean(); bal = np.mean([(P.argmax(1)[y == k] == k).mean() for k in set(y)]); print("C", C, "top1", round(top1, 3), "balanceado", round(bal, 3), flush=True)
    if best is None or bal > best[0]: best = (bal, C, P)
bal, C, P = best; pred = P.argmax(1); top3 = np.mean([y[i] in np.argsort(-P[i])[:3] for i in range(len(y))]); top5 = np.mean([y[i] in np.argsort(-P[i])[:5] for i in range(len(y))])
print("C escolhido", C, "| top1", round((pred == y).mean(), 3), "top3", round(top3, 3), "top5", round(top5, 3), "balanceado", round(bal, 3))
G = sorted(set(gmap.values())); gi = {g: k for k, g in enumerate(G)}; M = np.zeros((len(names), len(G))); [M.__setitem__((k, gi[gmap[n]]), 1) for k, n in enumerate(names)]
Pg = P @ M; yg = np.array([gi[gmap[names[k]]] for k in y]); print("grupo (9) via soma dos finos: acerto", round((Pg.argmax(1) == yg).mean(), 3))
res = {}
for k, n in enumerate(names):
    s = y == k; res[n] = dict(n=int(s.sum()), top1=round(float((pred[s] == k).mean()), 3), top3=round(float(np.mean([k in np.argsort(-P[i])[:3] for i in np.where(s)[0]])), 3), grupo_ok=round(float((Pg[s].argmax(1) == gi[gmap[n]]).mean()), 3))
for n, r in sorted(res.items(), key=lambda x: -x[1]["n"]): print(r["n"], n, "| top1", r["top1"], "top3", r["top3"], "grupo", r["grupo_ok"])
L = np.log(np.clip(P, 1e-9, 1))
def nll(T):
    z = L / T; z -= z.max(1, keepdims=True); p = np.exp(z); p /= p.sum(1, keepdims=True); return -np.log(p[np.arange(len(y)), y] + 1e-12).mean()
T = float(minimize_scalar(nll, bounds=(0.3, 4), method="bounded").x); print("T", round(T, 3), "NLL", round(nll(1), 3), "->", round(nll(T), 3))
sc = StandardScaler().fit(F); clf = LogisticRegression(C=C, max_iter=3000, class_weight="balanced").fit(sc.transform(F), y)
np.save("work/fine_oof.npy", P); json.dump(dict(names=names, groups=[gmap[n] for n in names], res=res, C=C, T=T, top1=float((pred == y).mean()), top3=float(top3), top5=float(top5), bal=float(bal), n=len(y)), open("work/fine_cv.json", "w"), ensure_ascii=False)
import pickle; pickle.dump(dict(sc=sc, clf=clf, names=names, gmap=gmap, T=T, ids=ids), open("work/fine_model.pkl", "wb")); print("modelo salvo")
