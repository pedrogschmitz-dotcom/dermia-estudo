import sys, json, numpy as np, torch
sys.path.insert(0, "/home/claude/dermia/scripts")
from load_dermlip import load
from sklearn.metrics import roc_auc_score
plan = json.load(open("work/fine_plan.json")); lab = plan["lab"]
pool = json.load(open("data/isic_test/pool_meta.json")); fm = json.load(open("data/fine_meta.json")); ids = [m["isic_id"] for m in pool + fm]
F = np.concatenate([np.load("work/dermlip_img.npy"), np.load("work/dermlip_fine_img.npy")]); F = F / np.linalg.norm(F, axis=1, keepdims=True)
fn = np.array([lab[i][0] for i in ids])
M = lambda *a: lambda n: any(n.startswith(x) for x in a)
C = [ # (id, texto em inglês, rótulo PT, onde esperamos encontrar)
 ("rede_atipica", "atypical pigment network", "Rede pigmentar atípica", M("Melanoma", "Nevo displásico", "Lentigo maligno")),
 ("rede_tipica", "regular typical pigment network", "Rede pigmentar típica e regular", M("Nevo melanocítico comum", "Nevo lentiginoso", "Nevo congênito", "Dermatofibroma", "Lentigo")),
 ("veu", "blue-white veil", "Véu azul-esbranquiçado", M("Melanoma invasivo", "Melanoma extensivo")),
 ("regressao", "regression structures, scar-like depigmentation and peppering", "Regressão (áreas brancas cicatriciais e pontos cinza)", M("Melanoma", "Nevo recorrente")),
 ("pontos_irreg", "irregular dots and globules", "Pontos e glóbulos irregulares", M("Melanoma", "Nevo displásico")),
 ("globulos_reg", "regular globular pattern", "Glóbulos regulares (padrão globular)", M("Nevo melanocítico comum", "Nevo congênito")),
 ("estrias", "radial streaming and pseudopods", "Estrias radiais e pseudópodes", M("Melanoma extensivo", "Nevo de Spitz", "Melanoma invasivo")),
 ("starburst", "starburst pattern", "Padrão em explosão estelar (starburst)", M("Nevo de Spitz")),
 ("azul_homog", "homogeneous blue pigmentation", "Pigmentação azul homogênea", M("Nevo azul", "Nevo combinado")),
 ("arboriformes", "arborizing vessels", "Vasos arboriformes", M("CBC")),
 ("ninhos_azuis", "blue-gray ovoid nests", "Ninhos ovoides azul-acinzentados", M("CBC")),
 ("globulos_azuis", "multiple blue-gray globules", "Múltiplos glóbulos azul-acinzentados", M("CBC")),
 ("folha", "leaf-like areas and spoke-wheel areas", "Áreas em folha ou em roda radiada", M("CBC")),
 ("telang_finas", "short fine telangiectasias", "Telangiectasias finas e curtas", M("CBC superficial")),
 ("ulceracao", "ulceration", "Ulceração", M("CBC", "Carcinoma espinocelular")),
 ("branco_brilhante", "shiny white lines and scar-like white areas", "Linhas e áreas brancas brilhantes", M("CBC infiltrativo", "Dermatofibroma")),
 ("milia", "milia-like cysts", "Cistos tipo milium", M("Queratose seborreica")),
 ("comedo", "comedo-like openings", "Aberturas tipo comedão", M("Queratose seborreica")),
 ("cerebriforme", "fissures and ridges, cerebriform pattern", "Fissuras e cristas (cerebriforme)", M("Queratose seborreica")),
 ("roido", "moth-eaten border", "Borda 'roída de traça'", M("Queratose seborreica", "Lentigo")),
 ("morango", "strawberry pattern", "Padrão em morango", M("Ceratose actínica")),
 ("escamas", "white and yellow scales, keratin", "Escamas e queratina", M("Ceratose actínica", "Carcinoma espinocelular", "CEC in situ", "Ceratoacantoma")),
 ("glomerulares", "glomerular vessels", "Vasos glomerulares", M("CEC in situ", "Carcinoma espinocelular")),
 ("grampo", "hairpin vessels with white halo", "Vasos em grampo com halo branco", M("Carcinoma espinocelular", "Ceratoacantoma", "Queratose seborreica")),
 ("massa_queratina", "central keratin mass", "Massa central de queratina", M("Ceratoacantoma", "Carcinoma espinocelular")),
 ("df_central", "central white scar-like patch with delicate peripheral network", "Mancha central branca com rede periférica delicada", M("Dermatofibroma")),
 ("lacunas", "red-blue lacunae", "Lacunas vermelho-azuladas", M("Hemangioma", "Angioqueratoma")),
 ("vermelho_homog", "homogeneous red area", "Área vermelha homogênea", M("Hemangioma", "Angioqueratoma", "Pólipo")),
 ("multicor", "multiple colors, black, brown, blue, red and white", "Múltiplas cores", M("Melanoma")),
 ("cinza_granular", "gray granular dots, peppering", "Pontos cinza granulares (pimenta)", M("Queratose liquenoide", "Lentigo maligno", "Melanoma in situ")),
 ("romboidal", "rhomboidal structures and asymmetric perifollicular pigmentation", "Estruturas romboidais e pigmento perifolicular assimétrico", M("Lentigo maligno")),
 ("papilomatosa", "papillomatous surface with red and black dots", "Superfície papilomatosa com pontos vermelhos e pretos", M("Verruga")),
 ("marrom_homog", "homogeneous brown pigmentation", "Pigmentação marrom homogênea", M("Nevo melanocítico comum", "Nevo lentiginoso", "Nevo congênito")),
]
model, pre, tok, _ = load(); out = []
with torch.no_grad():
    for cid, en, pt, pos in C:
        t = model.encode_text(tok([f"a dermoscopy image showing {en}", f"dermoscopy: {en}", f"{en}"])); t = t / t.norm(dim=-1, keepdim=True); t = t.mean(0); t = (t / t.norm()).numpy()
        s = F @ t; y = np.array([pos(n) for n in fn]); auc = roc_auc_score(y, s)
        out.append(dict(id=cid, pt=pt, en=en, auc=float(auc), vec=t.tolist(), mean=float(s.mean()), std=float(s.std()), pos=[n for n in sorted(set(fn)) if pos(n)]))
        print(f"{auc:.2f}  {pt}", flush=True)
json.dump(out, open("work/concepts.json", "w"), ensure_ascii=False)
