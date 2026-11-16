# Extrai características com o MESMO modelo e pré-processamento que o app usa (treinar com o que se serve).
# uso: extract_onnx.py modelo.onnx itens.json modo(crop|squash) vistas(id,h,v,hv) saida fatia/total
import sys, json, numpy as np, onnxruntime as ort
from PIL import Image
import torchvision.transforms as TT
model, items, mode, views, outp = sys.argv[1], json.load(open(sys.argv[2])), sys.argv[3], sys.argv[4].split(","), sys.argv[5]
sh, nsh = map(int, sys.argv[6].split("/")) if len(sys.argv) > 6 else (0, 1); items = items[sh::nsh]
BIC = TT.InterpolationMode.BICUBIC; NORM = TT.Compose([TT.ToTensor(), TT.Normalize((0.48145466, 0.4578275, 0.40821073), (0.26862954, 0.26130258, 0.27577711))])
RS = TT.Compose([TT.Resize(224, interpolation=BIC, antialias=True), TT.CenterCrop(224)]) if mode == "crop" else TT.Resize((224, 224), interpolation=BIC, antialias=True)
if mode == "auto":
    sys.path.insert(0, "/home/claude/dermia/scripts"); from autocrop import box as _box; _CENTER = RS if False else TT.Compose([TT.Resize(224, interpolation=BIC, antialias=True), TT.CenterCrop(224)])
    def RS(im):
        b = _box(im)
        return _CENTER(im) if b is None else im.crop((b[0], b[1], b[0] + b[2], b[1] + b[2])).resize((224, 224), Image.BICUBIC)
so = ort.SessionOptions(); so.intra_op_num_threads = 1; S = ort.InferenceSession(model, so)
def feats(x):
    emb, tok = S.run(["emb", "tok"], {"img": x[None]}); t = tok[0]; g = t.reshape(14, 14, -1)
    return np.concatenate([emb[0], t.mean(0), g[:7, :7].mean((0, 1)), g[:7, 7:].mean((0, 1)), g[7:, :7].mean((0, 1)), g[7:, 7:].mean((0, 1)), t.max(0)])
FL = {"id": lambda a: a, "h": lambda a: a[:, :, ::-1], "v": lambda a: a[:, ::-1, :], "hv": lambda a: a[:, ::-1, ::-1]}
out = {v: [] for v in views}; ids = []
for n, (i, p) in enumerate(items):
    a = NORM(RS(Image.open(p).convert("RGB"))).numpy(); ids.append(i)
    for v in views: out[v].append(feats(np.ascontiguousarray(FL[v](a))).astype(np.float16))
    if n % 500 == 0: print(n, len(items), flush=True)
json.dump(ids, open(f"{outp}_{sh}_ids.json", "w"))
for v in views: np.save(f"{outp}_{v}_{sh}.npy", np.stack(out[v]))
print("FIM", flush=True)
