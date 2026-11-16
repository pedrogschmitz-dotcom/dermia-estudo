import json, numpy as np, warnings
warnings.filterwarnings("ignore")
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
A = ["pigment_network", "negative_network", "streaks", "milia_like_cyst", "globules"]
PT = ["Rede pigmentar", "Rede negativa", "Estrias", "Cistos tipo milium", "Glóbulos e pontos"]
COL = ["#6FCF97", "#FF6B9A", "#FF6B5B", "#FFE066", "#B08CFF"]
T = np.concatenate([np.load(f"work/attr_tok_{s}.npy") for s in (0, 1)]); Fr = np.concatenate([np.load(f"work/attr_frac_{s}.npy") for s in (0, 1)]).astype(np.float32)
G = T.astype(np.float32).mean(1); N = len(T); cv = json.load(open("work/attr_cv_ctx.json")); rng = np.random.RandomState(0); Ws, bs, ths = [], [], []
TH = {"pigment_network": 0.575, "negative_network": 0.2, "streaks": 0.9, "milia_like_cyst": 0.95, "globules": 0.625}
for k, a in enumerate(A):
    y = (Fr[:, k] >= .25).reshape(-1); pos = np.where(y)[0]; neg = np.where(~y)[0]; neg = rng.choice(neg, min(len(neg), max(4 * len(pos), 20000), 150000), replace=False); sel = np.concatenate([pos, neg])
    ii = sel // 196; pp = sel % 196; X = np.concatenate([T[ii, pp].astype(np.float32), G[ii]], 1)
    sc = StandardScaler().fit(X); m = LogisticRegression(C=0.01, max_iter=400, class_weight="balanced").fit(sc.transform(X), y[sel])
    W = m.coef_[0] / sc.scale_; b = float(m.intercept_[0] - W @ sc.mean_)
    chk = np.abs((X[:200] @ W + b) - m.decision_function(sc.transform(X[:200]))).max(); assert chk < 1e-3, chk
    Ws.append([round(float(x), 6) for x in W]); bs.append(b); ths.append(TH[a]); print(a, "ok", len(pos), "positivos")
json.dump(dict(ids=A, pt=PT, color=COL, W=Ws, b=bs, th=ths, cv={a: cv[a] for a in A}, n_img=N), open("app/data/attr.json", "w"), ensure_ascii=False)
import os; print("attr.json KB", os.path.getsize("app/data/attr.json") // 1024)
