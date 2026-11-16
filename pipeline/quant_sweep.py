import sys, os, json, pickle, numpy as np, onnx, onnxruntime as ort
from onnxruntime.quantization import quantize_dynamic, QuantType
from PIL import Image
import torchvision.transforms as TT
m = onnx.load("work/dermlip_fp32.onnx", load_external_data=False); mm = [n for n in m.graph.node if n.op_type == "MatMul"]; init = {i.name for i in m.graph.initializer}
wm = [n.name for n in mm if n.input[1] in init or n.input[0] in init]; print("MatMul total", len(mm), "com peso constante", len(wm)); print(wm[:8], wm[-4:])
pre = TT.Compose([TT.Resize(224, interpolation=TT.InterpolationMode.BICUBIC, antialias=True), TT.CenterCrop(224), TT.ToTensor(), TT.Normalize((0.48145466, 0.4578275, 0.40821073), (0.26862954, 0.26130258, 0.27577711))])
M = pickle.load(open("work/fine_model.pkl", "rb")); ids = M["ids"]; rng = np.random.RandomState(5); pick = rng.choice(3451, 10, replace=False)
X = [pre(Image.open(f"data/isic_test/img/{ids[k]}.jpg").convert("RGB"))[None].numpy() for k in pick]
so = ort.SessionOptions(); so.intra_op_num_threads = 1
def run(f): s = ort.InferenceSession(f, so); return [s.run(["emb", "tok"], {"img": x}) for x in X]
R = run("work/dermlip_fp32.onnx")
def cmp(f):
    r = run(f); ce = [float(a[0][0] @ b[0][0] / np.linalg.norm(a[0][0]) / np.linalg.norm(b[0][0])) for a, b in zip(r, R)]
    ct = [float((a[1][0] * b[1][0]).sum(-1).mean() / np.sqrt((a[1][0] ** 2).sum(-1).mean() * (b[1][0] ** 2).sum(-1).mean())) for a, b in zip(r, R)]
    return round(np.mean(ce), 4), round(np.min(ce), 4), round(np.mean(ct), 4), os.path.getsize(f) // 2**20
blk = lambda i: [n for n in wm if f"blocks.{i}/" in n or f"blocks.{i}." in n]
cfgs = {
 "A atual": dict(),
 "B per_channel": dict(per_channel=True),
 "C QUInt8": dict(weight_type=QuantType.QUInt8),
 "D sem bloco 0 e 11": dict(nodes_to_exclude=blk(0) + blk(11)),
 "E per_channel+sem 0,11": dict(per_channel=True, nodes_to_exclude=blk(0) + blk(11)),
}
only = sys.argv[1:] 
for name, kw in cfgs.items():
    if only and name[0] not in only: continue
    f = "work/q_" + name[0] + ".onnx"
    try:
        quantize_dynamic("work/dermlip_fp32.onnx", f, op_types_to_quantize=["MatMul"], **kw); print(name, "| cos emb médio/mín, cos tok, MB:", cmp(f), flush=True)
    except Exception as e: print(name, "ERRO", str(e)[:200], flush=True)
