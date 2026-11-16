import json, numpy as np
cv = json.load(open("work/fine_cv.json")); names = cv["names"]; P = np.load("work/fine_oof.npy")
plan = json.load(open("work/fine_plan.json")); lab = plan["lab"]
pool = json.load(open("data/isic_test/pool_meta.json")); fm = json.load(open("data/fine_meta.json")); ids = [m["isic_id"] for m in pool + fm]
y = np.array([names.index(lab[i][0]) for i in ids]); pred = P.argmax(1); K = len(names)
conf = np.zeros((K, K)); [conf.__setitem__((p, t), conf[p, t] + 1) for p, t in zip(pred, y)]   # linha = chute, coluna = verdadeiro
TYP = {
"Nevo melanocítico comum": "Rede pigmentar regular ou glóbulos regulares, cor marrom uniforme, simetria de cor e de estrutura, rede que esmaece na periferia.",
"Nevo displásico (atípico)": "Rede pigmentar levemente irregular, pigmentação marrom desigual, centro mais claro ou mais escuro, 2 a 3 cores, sem véu azul-esbranquiçado nem vasos atípicos.",
"Nevo congênito": "Padrão globular ou reticular, pelos terminais, pigmento perifolicular, aspecto de paralelepípedo (cobblestone), lesão em geral grande.",
"Nevo lentiginoso": "Lesão pequena e plana com rede fina e regular, às vezes pontos escuros centrais; difícil separar de lentigo e de melanoma in situ pequeno.",
"Nevo recorrente": "Cicatriz central branca com pigmento e rede irregulares na borda (pseudomelanoma); a história de cirurgia prévia é a chave.",
"Nevo combinado": "Duas ou mais populações juntas: por exemplo, componente azul-acinzentado homogêneo ao lado de rede ou glóbulos marrons.",
"Nevo azul": "Pigmentação azul-acinzentada ou azul-aço homogênea, sem rede, sem estrutura.",
"Nevo de Spitz ou Reed": "Padrão em explosão estelar (estrias radiais regulares e simétricas na periferia) ou globular, pigmento marrom-azulado homogêneo; em adultos exige excisão.",
"Melanoma in situ": "Rede pigmentar atípica, pigmentação assimétrica, pontos e glóbulos irregulares, áreas de regressão; em geral sem vasos nem véu.",
"Melanoma invasivo": "Véu azul-esbranquiçado, regressão (branco cicatricial e pontos cinza), vasos atípicos, múltiplas cores, estrias irregulares, assimetria de estrutura.",
"Melanoma extensivo superficial": "Assimetria de cor e de estrutura, rede atípica, estrias e pseudópodes irregulares, pontos e glóbulos irregulares, regressão.",
"Melanoma associado a nevo": "Área nova e atípica dentro de nevo preexistente; contraste entre padrão benigno e foco com rede atípica, véu ou regressão.",
"Lentigo maligno / melanoma lentigo maligno": "Em face fotolesada: pigmento cinza-marrom assimétrico ao redor dos folículos, estruturas romboidais, pontos cinza granulares, aberturas foliculares preenchidas.",
"CBC (nodular ou subtipo não informado)": "Vasos arboriformes, ninhos ovoides ou glóbulos azul-acinzentados, ulceração, brilho branco; ausência de rede pigmentar.",
"CBC superficial": "Áreas vermelho-esbranquiçadas brilhantes, telangiectasias finas e curtas, pequenas erosões, estruturas em folha ou roda radiada, sem rede pigmentar.",
"CBC infiltrativo ou esclerodermiforme": "Áreas brancas brilhantes cicatriciais, vasos arboriformes finos e esparsos, pouco pigmento; exige atenção porque a margem clínica engana.",
"Carcinoma espinocelular (CEC) invasivo": "Vasos glomerulares e em grampo irregulares, áreas branco-amareladas sem estrutura, queratina e escamas, ulceração, halo branco ao redor dos vasos.",
"CEC in situ (doença de Bowen)": "Vasos glomerulares agrupados, escamas superficiais, áreas avermelhadas, às vezes pigmento em glóbulos agrupados.",
"Ceratoacantoma (CEC tipo ceratoacantoma)": "Massa central de queratina amarelo-acastanhada com coroa de vasos em grampo; cresce em semanas, tratar como CEC.",
"Ceratose actínica": "Padrão em morango (fundo vermelho com aberturas foliculares brancas), escamas finas, vasos ao redor dos folículos.",
"Ceratose actínica hipertrófica": "Escamas e queratina espessas, massa hiperqueratótica branco-amarelada; difícil separar de CEC.",
"Queratose seborreica": "Cistos tipo milium, aberturas tipo comedão, fissuras e cristas (cerebriforme), borda nítida 'roída de traça', vasos em grampo.",
"Queratose liquenoide": "Área rosada ou avermelhada difusa com pontos cinza granulares; em geral sem estrutura própria, lembra regressão de lentigo ou queratose seborreica.",
"Dermatofibroma": "Mancha central branca cicatricial com rede pigmentar periférica delicada, às vezes vasos em anel.",
"Hemangioma": "Lacunas vermelhas, azuladas ou roxas bem delimitadas, áreas vermelhas homogêneas.",
"Angioqueratoma ou granuloma piogênico": "Angioqueratoma: lacunas vermelho-escuras ou pretas com véu azul-esbranquiçado. Granuloma piogênico: área vermelha homogênea com colarete branco.",
"Lentigo (solar ou simples)": "Rede fina marrom-clara, borda 'roída de traça' (solar), pigmentação homogênea; pode virar queratose liquenoide.",
"Verruga viral": "Superfície papilomatosa com pontos e pequenas alças vermelhas e pretas (capilares trombosados).",
"Pólipo fibroepitelial": "Pouca estrutura própria: pele rosada ou da cor da pele com vasos pontilhados ou lineares; diagnóstico mais clínico que dermatoscópico.",
"Outras (cicatriz, neurofibroma, hiperplasia sebácea e raras)": "Sem padrão único; grupo misto de lesões raras. Não confie neste rótulo.",
}
assert set(TYP) == set(names), set(names) ^ set(TYP)
cls = []
for k, n in enumerate(names):
    col = conf[k]; tot = col.sum(); prec = float(col[k] / tot) if tot else 0.0
    wrong = sorted([(float(col[t] / tot), names[t]) for t in range(K) if t != k and col[t] > 0], reverse=True)[:3]
    cls.append(dict(typ=TYP[n], prec=round(prec, 3), n_pred=int(tot), errou_para=[[round(a, 3), b] for a, b in wrong]))
C = json.load(open("work/concepts.json")); keep = [c for c in C if c["auc"] >= 0.75]
print("conceitos mantidos", len(keep), "de", len(C), "| descartados:", [c["pt"] for c in C if c["auc"] < 0.75])
out = dict(classes=cls, concepts=[dict(id=c["id"], pt=c["pt"], auc=round(c["auc"], 2), vec=[round(x, 5) for x in c["vec"]], mean=round(c["mean"], 5), std=round(c["std"], 5), pos=c["pos"]) for c in keep])
json.dump(out, open("app/data/explain.json", "w"), ensure_ascii=False); import os; print("explain.json KB", os.path.getsize("app/data/explain.json") // 1024)
for k in (0, 1, 8, 9, 13): print(names[k], cls[k]["prec"], cls[k]["errou_para"])
