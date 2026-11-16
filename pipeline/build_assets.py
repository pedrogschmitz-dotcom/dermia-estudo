import sys, json, numpy as np, torch
sys.path.insert(0, "/home/claude/dermia/scripts")
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_predict, StratifiedKFold
from sklearn.metrics import roc_auc_score
from scipy.optimize import minimize_scalar
names = ["melanoma","nevo","cbc","cec","ceratose_actinica","queratose_seborreica","dermatofibroma","vascular","outras"]
PT = ["Melanoma","Nevo melanocítico","Carcinoma basocelular (CBC)","Carcinoma espinocelular (CEC)","Ceratose actínica","Queratose seborreica","Dermatofibroma","Lesão vascular","Outras / incerto"]
pool = json.load(open("data/isic_test/pool_meta.json")); F = np.load("work/dermlip_img.npy"); y = np.array([names.index(m["classe"]) for m in pool])
sc = StandardScaler().fit(F); clf = LogisticRegression(C=0.002, max_iter=3000, class_weight="balanced").fit(sc.transform(F), y)
P = np.load("work/feat_dermlip_oof.npy"); L = np.log(np.clip(P, 1e-9, 1))
def nll(T):
    z = L / T; z = z - z.max(1, keepdims=True); p = np.exp(z); p /= p.sum(1, keepdims=True); return -np.log(p[np.arange(len(y)), y] + 1e-12).mean()
T = minimize_scalar(nll, bounds=(0.3, 3), method="bounded").x; print("temperatura", round(T, 3), "NLL antes/depois", round(nll(1), 3), round(nll(T), 3))
A = clf.coef_ / sc.scale_            # (9,512): logit_k = A_k . (emb - mean) + b_k
from load_dermlip import load
model, pre, tok, _ = load(); v = model.visual
Wh = v.head.weight.detach().numpy().astype(np.float64); bh = v.head.bias.detach().numpy(); gam = v.norm.weight.detach().numpy(); bet = v.norm.bias.detach().numpy()
U = A @ Wh                           # (9,768)
UG = U * gam
const = A @ bh - A @ sc.mean_ + clf.intercept_ + U @ bet
# detector dermatoscopia x não-dermatoscopia
ND = np.load("work/dermlip_nonderm_img.npy"); rng = np.random.RandomState(0); idx = rng.choice(len(F), 600, replace=False)
X = np.concatenate([F[idx], ND]); yd = np.array([0]*600 + [1]*len(ND))
dsc = StandardScaler().fit(X); dclf = LogisticRegression(C=0.01, max_iter=3000, class_weight="balanced").fit(dsc.transform(X), yd)
pp = cross_val_predict(LogisticRegression(C=0.01, max_iter=3000, class_weight="balanced"), dsc.transform(X), yd, cv=StratifiedKFold(5, shuffle=True, random_state=0), method="predict_proba")[:, 1]
print("detector não-dermatoscopia: AUC", round(roc_auc_score(yd, pp), 3), "| acerto em 0,5:", round(float(((pp > .5) == yd).mean()), 3))
head = dict(names=names, pt=PT, mean=sc.mean_.tolist(), scale=sc.scale_.tolist(), coef=clf.coef_.tolist(), intercept=clf.intercept_.tolist(), T=float(T),
            hm_u=UG.tolist(), hm_const=const.tolist(), ln_eps=1e-6,
            det=dict(mean=dsc.mean_.tolist(), scale=dsc.scale_.tolist(), coef=dclf.coef_[0].tolist(), intercept=float(dclf.intercept_[0])))
json.dump(head, open("app/data/head.json", "w")); print("head.json KB", len(json.dumps(head)) // 1024)
# verificação numérica da decomposição por pedaço (3 imagens)
import torchvision.transforms as TT; from PIL import Image
for k in (0, 1, 2):
    x = pre(Image.open(f'data/isic_test/img/{pool[k]["isic_id"]}.jpg').convert("RGB"))[None]
    with torch.no_grad():
        xx = v.patch_embed(x); xx = torch.cat((v.cls_token.expand(1, -1, -1), xx), 1) + v.pos_embed; 
        for b in v.blocks: xx = b(xx, rel_pos_bias=None)
        xx = v.norm(xx); t = xx[0, 1:].numpy().astype(np.float64); emb = v.head(v.norm(xx[:, 1:].mean(1)))[0].numpy()
    logit = A @ (emb - sc.mean_) + clf.intercept_
    pooled = t.mean(0); m = pooled.mean(); s = np.sqrt(pooled.var() + 1e-6)
    contrib = (t @ (UG / s).T - m * (UG / s).sum(1)) / len(t)      # (196,9)
    rec = contrib.sum(0) + const
    print("img", k, "logit direto vs soma dos pedaços (máx. diferença):", float(np.abs(rec - logit).max()))
# banco
TR = {"Nevus":"Nevo melanocítico","Basal cell carcinoma":"Carcinoma basocelular","Melanoma in situ":"Melanoma in situ","Melanoma Invasive":"Melanoma invasivo","Melanoma, NOS":"Melanoma","Solar or actinic keratosis":"Ceratose actínica","Squamous cell carcinoma, NOS":"Carcinoma espinocelular","Squamous cell carcinoma in situ":"CEC in situ (Bowen)","Squamous cell carcinoma, Invasive":"CEC invasivo","Seborrheic keratosis":"Queratose seborreica","Dermatofibroma":"Dermatofibroma","Hemangioma":"Hemangioma","Angiokeratoma":"Angioqueratoma","Pyogenic granuloma":"Granuloma piogênico","Solar lentigo":"Lentigo solar","Lentigo NOS":"Lentigo","Verruca":"Verruga viral","Fibroepithelial polyp":"Pólipo fibroepitelial","Scar":"Cicatriz","Neurofibroma":"Neurofibroma","Lichen planus like keratosis":"Queratose liquenoide","Sebaceous hyperplasia":"Hiperplasia sebácea","Clear cell acanthoma":"Acantoma de células claras","Lentigo simplex":"Lentigo simples"}
DXMAP = {"mel":"melanoma","nev":"nevo","spitz":"nevo","bcc":"cbc","scc":"cec","ak":"ceratose_actinica","sk":"queratose_seborreica","df":"dermatofibroma","hem":"vascular","pg":"vascular"}
def thumb(i, url=None): return f"https://isic-archive.s3.us-east-1.amazonaws.com/thumbnails/{i}_thumbnail.jpg"
sm = json.load(open("data/study_meta_isic.json")); SF = np.load("work/dermlip_study_img.npy"); inpool = {m["isic_id"]: n for n, m in enumerate(pool)}
bank = []; E = []
for n, m in enumerate(pool):
    bank.append(dict(id=m["isic_id"], c=names.index(m["classe"]), dx=TR.get(m["d3"], m["d3"]), lic=m["licenca"], at=m.get("atribuicao"), conf="histopatologia", site=m.get("local"), age=m.get("idade"), sex=m.get("sexo"), src="ISIC")); E.append(F[n])
st_ids = {m["isic_id"] for m in sm}
for m, f in zip(sm, SF):
    if m["isic_id"] in inpool:
        bank[inpool[m["isic_id"]]]["est"] = 1; continue
    bank.append(dict(id=m["isic_id"], c=names.index(DXMAP.get(m["dx"], "outras")) , dx=m["sub"], lic=m["licenca"], at=m.get("atribuicao"), conf=m.get("conf"), site=m.get("site"), age=m.get("age"), sex=m.get("sex"), src="ISIC", est=1)); E.append(f)
E = np.array(E, np.float32); E /= np.linalg.norm(E, axis=1, keepdims=True)
np.clip(np.round(E * 127), -127, 127).astype(np.int8).tofile("app/data/bank.bin")
json.dump(dict(n=len(bank), d=512, items=bank), open("app/data/bank.json", "w"), ensure_ascii=False)
print("banco:", len(bank), "casos | bank.bin KB", len(bank) * 512 // 1024, "| do estudo:", sum(1 for b in bank if b.get("est")), "| sem histopatologia:", sum(1 for b in bank if b["conf"] != "histopatologia"))
import collections; print(collections.Counter(b["lic"] for b in bank))
