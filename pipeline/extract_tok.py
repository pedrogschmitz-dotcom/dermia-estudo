# Tokens 14x14 do MESMO modelo do app (int8) + fração de cada estrutura em cada quadradinho de 16 px. uso: extract_tok.py fatia/total
import sys, json, numpy as np, onnxruntime as ort
from PIL import Image
import torchvision.transforms as TT
sh, nsh = map(int, sys.argv[1].split("/"))
A = ["pigment_network", "negative_network", "streaks", "milia_like_cyst", "globules"]
meta = json.load(open("data/attr/meta.json"))[sh::nsh]
BIC = TT.InterpolationMode.BICUBIC; RS = TT.Compose([TT.Resize(224, interpolation=BIC, antialias=True), TT.CenterCrop(224)]); RSM = TT.Compose([TT.Resize(224, interpolation=TT.InterpolationMode.BILINEAR, antialias=True), TT.CenterCrop(224)])
NORM = TT.Compose([TT.ToTensor(), TT.Normalize((0.48145466, 0.4578275, 0.40821073), (0.26862954, 0.26130258, 0.27577711))])
so = ort.SessionOptions(); so.intra_op_num_threads = 1; S = ort.InferenceSession("work/q_B.onnx", so)
T = np.zeros((len(meta), 196, 768), np.float16); Fr = np.zeros((len(meta), 5, 196), np.float16)
for n, m in enumerate(meta):
    im = Image.open(f'data/attr/img/{m["id"]}.jpg').convert("RGB"); T[n] = S.run(["tok"], {"img": NORM(RS(im)).numpy()[None]})[0][0]
    for k, a in enumerate(A):
        mk = np.asarray(RSM(Image.open(f'data/attr/mask/{m["id"]}_{a}.png')), np.float32) / 255; Fr[n, k] = mk.reshape(14, 16, 14, 16).mean((1, 3)).reshape(196)
    if n % 300 == 0: print(n, len(meta), flush=True)
np.save(f"work/attr_tok_{sh}.npy", T); np.save(f"work/attr_frac_{sh}.npy", Fr); json.dump([m["id"] for m in meta], open(f"work/attr_ids_{sh}.json", "w")); print("FIM", flush=True)
