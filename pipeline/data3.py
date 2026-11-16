# Carrega o conjunto completo (antigas + novas), rótulos v2, grupos para validação e características do modelo do app (int8).
import sys, json, numpy as np
sys.path.insert(0, "/home/claude/dermia/scripts")
from fine_labels2 import fine2, NOS
from cvlib import load, SL
def get():
    M = json.load(open("data/master.json")); meta = {x["id"]: x for x in M["old"] + M["new"]}
    def cat(a, b, view):
        i1, x1 = load(a, view); i2, x2 = load(b, view); return i1 + i2, np.concatenate([x1, x2])
    ids, Xid = cat("work/fx/old_crop", "work/fx/new_crop", "id"); ids2, Xh = cat("work/fx/oldh_crop", "work/fx/new_crop", "h"); assert ids == ids2
    lab = [fine2(*meta[i]["d"]) for i in ids]; names = sorted({l[0] for l in lab}); gmap = {l[0]: l[1] for l in lab}; y = np.array([names.index(l[0]) for l in lab])
    # grupo: paciente > lesão > (sem id) agrupamento por quase-duplicata do embedding, para não vazar entre treino e teste
    E = Xid[:, SL["emb"]].astype(np.float32); E /= np.linalg.norm(E, axis=1, keepdims=True); grp = []; noid = [n for n, i in enumerate(ids) if not (meta[i].get("patient") or meta[i].get("lesion"))]
    par = {n: n for n in noid}
    def find(a):
        while par[a] != a: par[a] = par[par[a]]; a = par[a]
        return a
    S = E[noid] @ E[noid].T; np.fill_diagonal(S, 0); ii, jj = np.where(S > 0.95)
    for a, b in zip(ii, jj): par[find(noid[a])] = find(noid[b])
    for n, i in enumerate(ids): m = meta[i]; grp.append(m.get("patient") or m.get("lesion") or f"dup{find(n)}")
    return dict(ids=ids, meta=[meta[i] for i in ids], names=names, gmap=gmap, y=y, grp=np.array(grp), Xid=Xid, Xh=Xh, n_noid=len(noid), n_dupgroups=len({find(n) for n in noid}))
def compat(names, gmap):   # matriz K x K: chute k é "compatível" com verdade t (mesmo grupo e um dos dois sem subtipo)
    K = len(names); nos = np.array([n in NOS or n.startswith("CBC (nodular") for n in names]); C = np.eye(K, dtype=bool)
    for a in range(K):
        for b in range(K):
            if gmap[names[a]] == gmap[names[b]] and (nos[a] or nos[b]): C[a, b] = True
    return C, nos
