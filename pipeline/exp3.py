import sys, numpy as np, warnings, time
sys.path.insert(0, "/home/claude/dermia/scripts"); warnings.filterwarnings("ignore")
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedGroupKFold
from joblib import Parallel, delayed
from cvlib import cols, rep, load
import data3
D = data3.get(); y, grp = D["y"], D["grp"]; K = len(D["names"]); Cm, _ = data3.compat(D["names"], D["gmap"])
ai, AX = load("work/fx/all_auto"); pos = {i: n for n, i in enumerate(ai)}; XA = AX[[pos[i] for i in D["ids"]]]
parts = ["mean", "grid"]; C = cols(D["Xid"], parts); A = cols(XA, parts)
sp = list(StratifiedGroupKFold(5, shuffle=True, random_state=0).split(C, y, grp))
def fold(Xtr, ytr, tests, Cc=0.001):
    sc = StandardScaler().fit(Xtr); m = LogisticRegression(C=Cc, max_iter=300, class_weight="balanced").fit(sc.transform(Xtr), ytr)
    out = []
    for Xt in tests: z = np.full((len(Xt), K), -50.0); z[:, m.classes_] = m.decision_function(sc.transform(Xt)); out.append(z)
    return out
def run(tag, trainX, tests):
    t = time.time(); R = Parallel(n_jobs=2)(delayed(fold)(np.concatenate([X[tr] for X in trainX]), np.concatenate([y[tr]] * len(trainX)), [T[te] for T in tests]) for tr, te in sp)
    for j, name in enumerate(["teste " + str(k) for k in range(len(tests))]):
        Z = np.zeros((len(y), K)); [Z.__setitem__(te, r[j]) for (tr, te), r in zip(sp, R)]; r = rep(Z, y); r["compat"] = round(float(Cm[Z.argmax(1), y].mean()), 4); print(tag, name, r, f"{time.time()-t:.0f}s", flush=True); np.save(f"work/oof_{tag}_{j}.npy", Z)
run("auto", [A], [A, C])            # treino recorte; teste recorte e centro
run("ambos", [A, C], [A, C, (A + C) / 2])
