"""
Ajuste fino do DermLIP-PanDerm (só a parte de visão) para os 38 diagnósticos do app Dermatolog.IA.
Roda no Mac com chip Apple (GPU "mps"); cai para CPU se não houver.
Etapas: (1) baixar imagens do ISIC  (2) treinar segurando a pasta 0 para prova  (3) exportar ONNX e quantizar.
uso:
  python finetune.py baixar
  python finetune.py treinar [--epocas 8] [--smoke]
  python finetune.py exportar
"""
import sys, os, json, time, math, io, random, argparse
import numpy as np, torch, torch.nn as nn, torch.nn.functional as F
from PIL import Image
import torchvision.transforms as TT
AQUI = os.path.dirname(os.path.abspath(__file__))
SPLIT = json.load(open(os.path.join(AQUI, "finetune_split.json")))
IMG = os.path.join(AQUI, "img"); CK = os.path.join(AQUI, "ckpt"); os.makedirs(IMG, exist_ok=True); os.makedirs(CK, exist_ok=True)
DEV = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
MEAN, STD = (0.48145466, 0.4578275, 0.40821073), (0.26862954, 0.26130258, 0.27577711)

def baixar():
    import requests
    from concurrent.futures import ThreadPoolExecutor
    def one(it):
        p = os.path.join(IMG, it["id"] + ".jpg")
        if os.path.exists(p): return True
        for _ in range(4):
            try:
                j = requests.get(f'https://api.isic-archive.com/api/v2/images/{it["id"]}/', timeout=60).json()
                r = requests.get(j["files"]["full"]["url"], timeout=180); r.raise_for_status()
                im = Image.open(io.BytesIO(r.content)).convert("RGB"); im.thumbnail((512, 512)); im.save(p, quality=92); return True
            except Exception: time.sleep(3)
        return False
    with ThreadPoolExecutor(8) as ex: ok = list(ex.map(one, SPLIT["items"]))
    print("baixadas:", sum(ok), "de", len(ok))

def carregar_modelo():
    sys.path.insert(0, os.path.join(AQUI, "Derm1M", "src", "src")); import open_clip
    from safetensors.torch import load_file
    model, _, _ = open_clip.create_model_and_transforms("PanDerm-base-w-PubMed-256", pretrained=None)
    w = os.environ.get("DERMLIP_PESOS", os.path.join(AQUI, "dermlip", "open_clip_model.safetensors"))
    model.load_state_dict(load_file(w), strict=False); return model.visual

class Rede(nn.Module):
    """mesmo caminho do app: tokens 14x14 -> média global + média de 4 quadrantes -> camada linear"""
    def __init__(self, v, K):
        super().__init__(); self.v = v; self.head = nn.Linear(768 * 5, K)
    def tokens(self, x):
        v = self.v; x = v.patch_embed(x); x = torch.cat((v.cls_token.expand(x.shape[0], -1, -1), x), 1) + v.pos_embed
        for b in v.blocks: x = b(x, rel_pos_bias=None)
        return v.norm(x)[:, 1:]
    def forward(self, x):
        t = self.tokens(x); B = t.shape[0]; g = t.reshape(B, 14, 14, -1)
        f = torch.cat([t.mean(1), g[:, :7, :7].mean((1, 2)), g[:, :7, 7:].mean((1, 2)), g[:, 7:, :7].mean((1, 2)), g[:, 7:, 7:].mean((1, 2))], 1)
        return self.head(f)

class DS(torch.utils.data.Dataset):
    def __init__(s, items, treino):
        s.items = items; base = [TT.Resize(224, interpolation=TT.InterpolationMode.BICUBIC, antialias=True)]
        s.tf = TT.Compose(base + ([TT.RandomResizedCrop(224, scale=(0.55, 1.0), ratio=(0.85, 1.18)), TT.RandomHorizontalFlip(), TT.RandomVerticalFlip(), TT.RandomApply([TT.RandomRotation(90)], p=0.5),
                                   TT.ColorJitter(0.15, 0.15, 0.1, 0.02)] if treino else [TT.CenterCrop(224)]) + [TT.ToTensor(), TT.Normalize(MEAN, STD)])
    def __len__(s): return len(s.items)
    def __getitem__(s, i): it = s.items[i]; return s.tf(Image.open(os.path.join(IMG, it["id"] + ".jpg")).convert("RGB")), it["y"]

def avaliar(net, dl):
    net.eval(); P, Y = [], []
    with torch.no_grad():
        for x, y in dl: P.append(F.softmax(net(x.to(DEV)), 1).cpu()); Y.append(y)
    P = torch.cat(P); Y = torch.cat(Y); o = P.argsort(1, descending=True)
    top1 = (o[:, 0] == Y).float().mean().item(); top3 = (o[:, :3] == Y[:, None]).any(1).float().mean().item()
    return top1, top3

def treinar(a):
    torch.manual_seed(0); random.seed(0); K = len(SPLIT["names"])
    its = [it for it in SPLIT["items"] if os.path.exists(os.path.join(IMG, it["id"] + ".jpg"))]
    tr = [it for it in its if it["fold"] != 0]; te = [it for it in its if it["fold"] == 0]
    if a.smoke: tr, te = tr[:48], te[:16]
    print(f"dispositivo {DEV} | treino {len(tr)} | prova {len(te)} (pasta 0, a mesma da validação do app)", flush=True)
    net = Rede(carregar_modelo(), K).to(DEV)
    for p in net.v.parameters(): p.requires_grad = False
    for b in net.v.blocks[-a.blocos:]: [setattr(p, "requires_grad", True) for p in b.parameters()]
    for p in net.v.norm.parameters(): p.requires_grad = True
    cnt = np.bincount([it["y"] for it in tr], minlength=K); w = torch.tensor((cnt.max() / np.maximum(cnt, 1)) ** 0.5, dtype=torch.float32, device=DEV)
    opt = torch.optim.AdamW([{"params": [p for p in net.v.parameters() if p.requires_grad], "lr": a.lr}, {"params": net.head.parameters(), "lr": a.lr * 50}], weight_decay=0.05)
    dl = torch.utils.data.DataLoader(DS(tr, True), batch_size=a.lote, shuffle=True, num_workers=0 if a.smoke else 4, drop_last=True, persistent_workers=not a.smoke)
    dv = torch.utils.data.DataLoader(DS(te, False), batch_size=64, num_workers=0 if a.smoke else 4)
    passos = max(1, len(dl)) * a.epocas; sch = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=[a.lr, a.lr * 50], total_steps=passos, pct_start=0.1)
    ini = 0; ck = os.path.join(CK, "ultimo.pt")
    if os.path.exists(ck) and not a.smoke:
        st = torch.load(ck, map_location=DEV); net.load_state_dict(st["net"]); opt.load_state_dict(st["opt"]); sch.load_state_dict(st["sch"]); ini = st["ep"] + 1; print("retomando da época", ini + 1, flush=True)
    melhor = -1
    for ep in range(ini, a.epocas):
        net.train(); t0 = time.time(); L = 0
        for n, (x, y) in enumerate(dl):
            loss = F.cross_entropy(net(x.to(DEV)), y.to(DEV), weight=w, label_smoothing=0.1); opt.zero_grad(); loss.backward(); opt.step(); sch.step(); L += loss.item()
            if n % 50 == 0: print(f"  época {ep+1} passo {n}/{len(dl)} perda {loss.item():.3f}", flush=True)
            if a.smoke and n >= 1: break
        t1, t3 = avaliar(net, dv); print(f"ÉPOCA {ep+1}/{a.epocas}: perda {L/max(1,n+1):.3f} | prova: exato {t1:.3f}, top-3 {t3:.3f} | {time.time()-t0:.0f}s", flush=True)
        if not a.smoke:
            torch.save({"net": net.state_dict(), "opt": opt.state_dict(), "sch": sch.state_dict(), "ep": ep}, ck)
            if t1 > melhor: melhor = t1; torch.save(net.state_dict(), os.path.join(CK, "melhor.pt"))
    print("FIM. Melhor exato na prova:", melhor, flush=True)

def exportar():
    from onnxruntime.quantization import quantize_dynamic
    net = Rede(carregar_modelo(), len(SPLIT["names"])); net.load_state_dict(torch.load(os.path.join(CK, "melhor.pt"), map_location="cpu")); net.eval(); v = net.v
    class Enc(nn.Module):
        def __init__(s): super().__init__(); s.n = net
        def forward(s, img): t = s.n.tokens(img); return v.head(v.norm(t.mean(1))), t
    out = os.path.join(AQUI, "dermlip_ft_fp32.onnx"); torch.onnx.export(Enc().eval(), torch.randn(1, 3, 224, 224), out, input_names=["img"], output_names=["emb", "tok"], opset_version=17, dynamo=False)
    quantize_dynamic(out, os.path.join(AQUI, "dermlip_ft_int8.onnx"), op_types_to_quantize=["MatMul"], per_channel=True); print("exportado: dermlip_ft_int8.onnx")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("etapa"); ap.add_argument("--epocas", type=int, default=8); ap.add_argument("--lote", type=int, default=32); ap.add_argument("--lr", type=float, default=2e-5); ap.add_argument("--blocos", type=int, default=6); ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args(); {"baixar": baixar, "treinar": lambda: treinar(a), "exportar": exportar}[a.etapa]()
