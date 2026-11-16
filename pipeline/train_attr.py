import json, numpy as np, warnings, sys
warnings.filterwarnings("ignore")
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score
A = ["pigment_network", "negative_network", "streaks", "milia_like_cyst", "globules"]
PT = ["Rede pigmentar", "Rede negativa (invertida)", "Estrias", "Cistos tipo milium", "Glóbulos e pontos"]
meta = {m["id"]: m for m in json.load(open("data/attr/meta.json"))}
ids, T, Fr = [], [], []
for s in (0, 1): ids += json.load(open(f"work/attr_ids_{s}.json")); T.append(np.load(f"work/attr_tok_{s}.npy")); Fr.append(np.load(f"work/attr_frac_{s}.npy"))
T = np.concatenate(T); Fr = np.concatenate(Fr).astype(np.float32); N = len(ids)
grp = np.array([meta[i].get("patient") or meta[i].get("lesion") or i for i in ids])
G = T.astype(np.float32).mean(1, keepdims=True).astype(np.float16)                     # contexto da lesão inteira
def rows(ii, pp, ctx):                           # monta só as linhas pedidas (imagem ii, quadradinho pp)
    x = T[ii, pp]; return np.concatenate([x, G[ii, 0]], 1) if ctx else x
def predict(m, sc, idx, ctx):
    out = np.zeros((len(idx), 196), np.float32)
    for s0 in range(0, len(idx), 200):
        b = idx[s0:s0 + 200]; ii = np.repeat(b, 196); pp = np.tile(np.arange(196), len(b)); out[s0:s0 + 200] = m.predict_proba(sc.transform(rows(ii, pp, ctx)))[:, 1].reshape(len(b), 196)
    return out
POS = 0.25; rng = np.random.RandomState(0); out = {}
ctx = "ctx" in sys.argv; C = 0.01
for k, a in enumerate(A):
    yall = (Fr[:, k] >= POS); P = np.zeros((N, 196), np.float32)
    for tr, te in GroupKFold(5).split(np.arange(N), groups=grp):
        y = yall[tr].reshape(-1); pos = np.where(y)[0]; neg = np.where(~y)[0]; neg = rng.choice(neg, min(len(neg), max(4 * len(pos), 20000), 120000), replace=False); sel = np.concatenate([pos, neg])
        ii = tr[sel // 196]; pp = sel % 196; X = rows(ii, pp, ctx); ys = y[sel]
        sc = StandardScaler().fit(X); m = LogisticRegression(C=C, max_iter=300, class_weight="balanced").fit(sc.transform(X), ys); del X
        P[te] = predict(m, sc, te, ctx)
    y = yall.reshape(-1); auc_p = roc_auc_score(y, P.reshape(-1)) if y.any() else float("nan")
    has = (Fr[:, k] > 0.02).any(1); auc_i = roc_auc_score(has, P.max(1)) if has.any() and (~has).any() else float("nan")
    best = (0, 0.5)
    for th in np.arange(0.3, 0.96, 0.05):                       # limiar que maximiza o Jaccard (sobre imagens com a estrutura)
        pr = P >= th; inter = (pr & yall).sum(1); uni = (pr | yall).sum(1); j = np.where(uni > 0, inter / np.maximum(uni, 1), 1.0); jm = float(j[has].mean()) if has.any() else 0
        if jm > best[0]: best = (jm, float(th))
    out[a] = dict(pt=PT[k], n_img=int(has.sum()), auc_patch=round(float(auc_p), 3), auc_img=round(float(auc_i), 3), jaccard=round(best[0], 3), th=round(best[1], 2))
    print(f"{PT[k]:28s} imagens com: {has.sum():4d} | AUC quadradinho {auc_p:.3f} | AUC presença {auc_i:.3f} | Jaccard {best[0]:.3f} (limiar {best[1]:.2f})", flush=True)
    np.save(f"work/attr_oof_{a}{'_ctx' if ctx else ''}.npy", P)
json.dump(out, open(f"work/attr_cv{'_ctx' if ctx else ''}.json", "w"), ensure_ascii=False)
