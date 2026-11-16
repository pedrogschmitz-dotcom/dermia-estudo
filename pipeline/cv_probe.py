import sys, json, numpy as np
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import confusion_matrix
data, featfile = sys.argv[1], sys.argv[2]; C = float(sys.argv[3]) if len(sys.argv) > 3 else 0.05
meta = json.load(open(data + "/pool_meta.json")); X = np.load(featfile)
names = ["melanoma","nevo","cbc","cec","ceratose_actinica","queratose_seborreica","dermatofibroma","vascular","outras"]
y = np.array([names.index(m["classe"]) for m in meta])
g = np.array([m.get("patient_id") or m.get("lesion_id") or m["isic_id"] for m in meta])
P = np.zeros((len(y), len(names)))
for tr, te in StratifiedGroupKFold(5, shuffle=True, random_state=0).split(X, y, g):
    clf = make_pipeline(StandardScaler(), LogisticRegression(C=C, max_iter=2000, class_weight="balanced"))
    clf.fit(X[tr], y[tr]); P[te] = clf.predict_proba(X[te])
p = P.argmax(1); rec = [(p[y==k]==k).mean() for k in range(len(names))]
print(f"{featfile} C={C}  acerto={np.mean(p==y):.3f}  média_por_classe={np.mean(rec):.3f}  top3={np.mean([y[i] in np.argsort(-P[i])[:3] for i in range(len(y))]):.3f}")
for k, c in enumerate(names): print(f"  {c:22s} n={(y==k).sum():4d} recall={rec[k]:.2f}")
mel = (y == 0); pm = P[:, 0]
for t in (0.5, 0.3, 0.2):
    print(f"  melanoma vs resto, limiar {t}: sensib={(pm[mel]>=t).mean():.2f} especif={(pm[~mel]<t).mean():.2f}")
np.save(featfile.replace(".npy", "_oof.npy"), P)
