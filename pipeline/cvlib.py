import json, numpy as np, warnings
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedGroupKFold
from joblib import Parallel, delayed
warnings.filterwarnings("ignore")
SL = dict(emb=slice(0, 512), mean=slice(512, 1280), grid=slice(1280, 4352), max=slice(4352, 5120))
def load(prefix, view="id"):
    ids, X = [], []
    for s in (0, 1): ids += json.load(open(f"{prefix}_{s}_ids.json")); X.append(np.load(f"{prefix}_{view}_{s}.npy"))
    return ids, np.concatenate(X).astype(np.float32)
def cols(X, parts): return np.concatenate([X[:, SL[p]] for p in parts], 1)
def _fold(Xtr, ytr, Xte, C, K, Xte_extra=()):
    sc = StandardScaler().fit(Xtr); m = LogisticRegression(C=C, max_iter=400, class_weight="balanced").fit(sc.transform(Xtr), ytr)
    def pr(Xt): p = np.full((len(Xt), K), 1e-9); p[:, m.classes_] = m.predict_proba(sc.transform(Xt)); return p
    return [pr(Xte)] + [pr(x) for x in Xte_extra]
def cv(X, y, grp, C, K, train_aug=(), test_views=(), seed=0):
    """train_aug: lista de matrizes (mesma ordem) usadas como aumento no treino; test_views: vistas extras para média no teste."""
    sp = list(StratifiedGroupKFold(5, shuffle=True, random_state=seed).split(X, y, grp))
    R = Parallel(n_jobs=2)(delayed(_fold)(np.concatenate([X[tr]] + [a[tr] for a in train_aug]), np.concatenate([y[tr]] * (1 + len(train_aug))), X[te], C, K, [v[te] for v in test_views]) for tr, te in sp)
    P = np.zeros((len(y), K)); PT = np.zeros((len(y), K))
    for (tr, te), r in zip(sp, R): P[te] = r[0]; PT[te] = np.mean(r, 0)
    return P, PT
def rep(P, y):
    pred = P.argmax(1); o = np.argsort(-P, 1); t3 = np.mean([y[i] in o[i, :3] for i in range(len(y))]); t5 = np.mean([y[i] in o[i, :5] for i in range(len(y))])
    bal = np.mean([(pred[y == k] == k).mean() for k in np.unique(y)]); return dict(top1=round(float((pred == y).mean()), 4), top3=round(float(t3), 4), top5=round(float(t5), 4), bal=round(float(bal), 4))
