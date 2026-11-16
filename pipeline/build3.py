# Treina a camada final (por regiões), calibra, mede e exporta tudo que o app usa. uso: build3.py tag partes C aug(0|1)
import sys, json, os, hashlib, glob, numpy as np, warnings, collections
sys.path.insert(0, "/home/claude/dermia/scripts"); warnings.filterwarnings("ignore")
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import cross_val_predict, StratifiedKFold
from scipy.optimize import minimize, minimize_scalar
from cvlib import cols, rep, load, SL
from fine_labels2 import fine2
import data3
tag, parts, C, aug = sys.argv[1], sys.argv[2].split("+"), float(sys.argv[3]), sys.argv[4] == "1"
D = data3.get(); y, names, gmap, meta, ids = D["y"], D["names"], D["gmap"], D["meta"], D["ids"]
if tag == "ambos":   # treino com dois enquadramentos: quadrado central + recorte automático da lesão (robustez ao recorte manual)
    _ai, _AX = load("work/fx/all_auto"); _pos = {i: n for n, i in enumerate(_ai)}; D["Xh"] = _AX[[_pos[i] for i in ids]]; K = len(names); N = len(y); Cm, nos = data3.compat(names, gmap)
old = json.load(open("app/data/head.json")) if os.path.exists("app/data/head.json") else json.load(open("work/head9.json")); json.dump(dict(names=old["names"], pt=old["pt"]), open("work/head9.json", "w"), ensure_ascii=False)
gnames, gpt = old["names"], old["pt"]; groups = [gmap[n] for n in names]; gi = np.array([gnames.index(g) for g in groups])
Z = np.load(f"work/oof_{tag}.npy")
def sm(Z, T=1.0): z = Z / T; z = z - z.max(1, keepdims=True); p = np.exp(z); return p / p.sum(1, keepdims=True)
nll = lambda P: float(-np.log(P[np.arange(N), y] + 1e-12).mean())
T = float(minimize_scalar(lambda t: nll(sm(Z, t)), bounds=(0.3, 5), method="bounded").x); P = sm(Z, T)
# ---- contexto (região, idade, sexo): mesmas regras do app ----
def nsite(x):
    x = (x or "").lower()
    return "Head and neck" if x.startswith(("head", "cabe")) else "Trunk" if x.startswith(("trunk", "tronco")) else "Upper extremity" if x.startswith("upper") or x == "membro superior" else "Lower extremity" if x.startswith("lower") or x == "membro inferior" else "palmas/plantas" if x.startswith("palm") else None
def nsex(x): x = str(x or "").lower(); return "M" if x in ("m", "male") else "F" if x in ("f", "female") else None
def abin(a):
    try: a = float(a)
    except Exception: return None
    return None if not a > 0 else "<30" if a < 30 else "30-44" if a < 45 else "45-59" if a < 60 else "60-74" if a < 75 else "75+"
ctxv = dict(site=[nsite(m.get("site")) for m in meta], age=[abin(m.get("age")) for m in meta], sex=[nsex(m.get("sex")) for m in meta]); LF = {}
for d, vals in ctxv.items():
    vs = sorted({v for v in vals if v}); cnt = np.zeros((len(vs), K)); [cnt.__setitem__((vs.index(v), k), cnt[vs.index(v), k] + 1) for v, k in zip(vals, y) if v]
    f = (cnt + 1) / (cnt.sum(0, keepdims=True) + len(vs)); LF[d] = np.stack([np.log(f[vs.index(v)]) if v else np.zeros(K) for v in vals])
def pctx(al): z = np.log(P + 1e-12) + sum(a * LF[d] for a, d in zip(al, ("site", "age", "sex"))); z -= z.max(1, keepdims=True); q = np.exp(z); return q / q.sum(1, keepdims=True)
al = minimize(lambda a: nll(pctx(a)), [0.5, 0.5, 0.5], bounds=[(0, 2)] * 3, method="L-BFGS-B").x; Pc = pctx(al)
# ---- métricas (validação cruzada, já com o modelo e o tratamento de imagem do app) ----
def metrics(P):
    r = rep(P, y); pred = P.argmax(1); r["compat"] = round(float(Cm[pred, y].mean()), 4)
    G = np.zeros((N, len(gnames)))
    for k, g in enumerate(gi): G[:, g] += P[:, k]
    r["group"] = round(float((G.argmax(1) == gi[y]).mean()), 4)
    return r, pred
m_img, pred = metrics(P); m_ctx, _ = metrics(Pc); print("só imagem:", m_img); print("com contexto:", m_ctx, "alphas", np.round(al, 2), "| T", round(T, 3), "| NLL", round(nll(sm(Z)), 3), "->", round(nll(P), 3), "-> ctx", round(nll(Pc), 3))
o3 = np.argsort(-P, 1)[:, :3]; res = {}; conf = np.zeros((K, K)); [conf.__setitem__((p_, t_), conf[p_, t_] + 1) for p_, t_ in zip(pred, y)]
for k, n in enumerate(names): s = y == k; res[n] = dict(n=int(s.sum()), top1=round(float((pred[s] == k).mean()), 3), top3=round(float(np.mean([k in o3[i] for i in np.where(s)[0]])), 3))
for n, r in sorted(res.items(), key=lambda x: -x[1]["n"]): print(f'{r["n"]:5d} {r["top1"]:.2f} {r["top3"]:.2f}  {n}')
cv = dict(n=N, **m_img, ctx=m_ctx, res=res, C=C, feat="+".join(parts), aug=aug)
# ---- treino final em tudo ----
A = cols(D["Xid"], parts); B = cols(D["Xh"], parts); Xtr = np.concatenate([A, B]) if aug else A; ytr = np.concatenate([y, y]) if aug else y
sc = StandardScaler().fit(Xtr); clf = LogisticRegression(C=C, max_iter=300, class_weight="balanced").fit(sc.transform(Xtr), ytr); assert list(clf.classes_) == list(range(K))
Wp = (clf.coef_ / sc.scale_).astype(np.float32); bp = (clf.intercept_ - (clf.coef_ / sc.scale_) @ sc.mean_).astype(np.float64)
chk = np.abs((A[:50].astype(np.float64) @ Wp.T.astype(np.float64) + bp) - clf.decision_function(sc.transform(A[:50]))).max(); print("pesos dobrados conferem (máx dif):", float(chk)); assert chk < 1e-2
os.makedirs("app/data", exist_ok=True); Wp.tofile("app/data/model_w.bin")
# ---- detector de foto que não é dermatoscopia (com o embedding do app) ----
E = D["Xid"][:, SL["emb"]].astype(np.float32); _, ND = load("work/fx/nonderm"); ND = ND[:, SL["emb"]]; rng = np.random.RandomState(0); idx = rng.choice(N, 1200, replace=False)
Xd = np.concatenate([E[idx], ND]); yd = np.array([0] * 1200 + [1] * len(ND)); dsc = StandardScaler().fit(Xd); dclf = LogisticRegression(C=0.01, max_iter=3000, class_weight="balanced").fit(dsc.transform(Xd), yd)
pp = cross_val_predict(LogisticRegression(C=0.01, max_iter=3000, class_weight="balanced"), dsc.transform(Xd), yd, cv=StratifiedKFold(5, shuffle=True, random_state=0), method="predict_proba")[:, 1]
print("detector não-dermatoscopia: AUC", round(roc_auc_score(yd, pp), 4), "| falso alarme em dermatoscopia:", round(float((pp[yd == 0] > .5).mean()), 4), "| pega não-dermatoscopia:", round(float((pp[yd == 1] > .5).mean()), 4))
sha = hashlib.sha256(open("work/q_B.onnx", "rb").read()).hexdigest()
model = dict(v=3, names=names, groups=groups, gnames=gnames, gpt=gpt, nos=[bool(x) for x in nos], T=T, D=int(Wp.shape[1]), feat="+".join(parts), views=["id", "h"] if (aug and tag != "ambos") else ["id"], b=[float(x) for x in bp], ctx=dict(alpha=dict(site=float(al[0]), age=float(al[1]), sex=float(al[2]))), cv=cv,
             det=dict(mean=dsc.mean_.tolist(), scale=dsc.scale_.tolist(), coef=dclf.coef_[0].tolist(), intercept=float(dclf.intercept_[0])), model_sha=sha)
json.dump(model, open("app/data/model.json", "w"), ensure_ascii=False)
# ---- banco de casos (tudo + casos do estudo fora do treino) ----
so = json.load(open("data/study_only.json")); sid, SX = load("work/fx/study"); sx = {i: SX[n, SL["emb"]] for n, i in enumerate(sid)}; st_in = set(json.load(open("work/study_in_master.json")))
CONF = {"histopathology": "histopatologia", "histopatologia": "histopatologia"}
items = []; embs = []
for n, m in enumerate(meta): it = dict(id=m["id"], f=int(y[n]), c=int(gi[y[n]]), lic=m["lic"], at=m.get("at"), conf="histopatologia", site=m.get("site"), age=m.get("age"), sex=m.get("sex")); it.update(est=1) if m["id"] in st_in else None; items.append(it); embs.append(E[n])
for m in so:
    if m["id"] not in sx: continue
    hist = (m.get("conf") or "") in CONF; f = names.index(fine2(*m["d"])[0]) if (m["d"][0] and fine2(*m["d"])[0] in names and not fine2(*m["d"])[0].startswith("Outras raras")) else -1
    it = dict(id=m["id"], f=f, c=int(gi[f]) if f >= 0 else gnames.index("outras"), lic=m["lic"], at=m.get("at"), conf="histopatologia" if hist else (m.get("conf") or "sem histopatologia informada"), site=m.get("site"), age=m.get("age"), sex=m.get("sex"), est=1)
    if f < 0: it["dx"] = m.get("sub") or m["d"][0] or "?"
    items.append(it); embs.append(sx[m["id"]])
Eb = np.array(embs, np.float32); Eb /= np.linalg.norm(Eb, axis=1, keepdims=True); np.clip(np.round(Eb * 127), -127, 127).astype(np.int8).tofile("app/data/bank.bin")
CH = 8 * 2**20; chunks = []; cur = bytearray()
for it in items:
    b = open(f'work/thumbs/{it["id"]}.jpg', "rb").read()
    if len(cur) + len(b) > CH: chunks.append(bytes(cur)); cur = bytearray()
    it["t"] = [len(chunks), len(cur), len(b)]; cur += b
chunks.append(bytes(cur)); os.makedirs("app/thumbs", exist_ok=True); [os.remove(f) for f in glob.glob("app/thumbs/*")]
for n, c in enumerate(chunks): open(f"app/thumbs/t{n}.bin", "wb").write(c)
bv = hashlib.sha256(json.dumps([i["id"] for i in items]).encode()).hexdigest()[:10]
json.dump(dict(n=len(items), d=512, v=bv, thumb_chunks=len(chunks), items=items), open("app/data/bank.json", "w"), ensure_ascii=False, separators=(",", ":"))
print("banco:", len(items), "| licenças", dict(collections.Counter(i["lic"] for i in items)), "| miniaturas MB", sum(len(c) for c in chunks) // 2**20, "em", len(chunks), "| sem diagnóstico fino:", sum(1 for i in items if i["f"] < 0))
for f in ("app/data/head.json", "app/data/head_fine.json", "app/thumbs/index.json"):
    if os.path.exists(f): os.remove(f)
# ---- explicações: texto típico, precisão/confusões e conceitos (estruturas) ----
from typ3 import TYP, CONCEPTS
assert set(TYP) == set(names), (set(names) ^ set(TYP))
cls = []
for k, n in enumerate(names):
    col = conf[k]; tot = col.sum(); wrong = sorted([(float(col[t] / tot), names[t]) for t in range(K) if t != k and col[t] > 0], reverse=True)[:3] if tot else []
    cls.append(dict(typ=TYP[n], prec=round(float(col[k] / tot), 3) if tot else 0.0, n_pred=int(tot), errou_para=[[round(a, 3), b] for a, b in wrong]))
cvec = {c["id"]: c for c in json.load(open("work/concepts.json"))}; En = E / np.linalg.norm(E, axis=1, keepdims=True); keep = []
for cid, pt, pref in CONCEPTS:
    t = np.array(cvec[cid]["vec"], np.float32); s = En @ t; pos = [n for n in names if n.startswith(tuple(pref))]; yy = np.isin(y, [names.index(n) for n in pos]); auc = roc_auc_score(yy, s)
    if auc >= 0.75: keep.append(dict(id=cid, pt=pt, auc=round(float(auc), 2), vec=[round(float(x), 5) for x in t], mean=round(float(s.mean()), 5), std=round(float(s.std()), 5), pos=pos))
    else: print("  conceito descartado:", pt, round(float(auc), 2))
json.dump(dict(classes=cls, concepts=keep), open("app/data/explain.json", "w"), ensure_ascii=False); print("conceitos mantidos", len(keep), "de", len(CONCEPTS))
print({f: os.path.getsize(f"app/data/{f}") // 1024 for f in os.listdir("app/data")})
