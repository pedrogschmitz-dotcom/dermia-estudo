import sys, torch, numpy as np
sys.path.insert(0, "/home/claude/dermia/scripts")
from load_dermlip import load
model, pre, tok, _ = load(); v = model.visual.eval()
class Enc(torch.nn.Module):
    def __init__(s, v): super().__init__(); s.v = v
    def forward(s, img):
        v = s.v; x = v.patch_embed(img); B = x.shape[0]
        x = torch.cat((v.cls_token.expand(B, -1, -1), x), 1)
        x = x + v.pos_embed.expand(B, -1, -1).type_as(x)
        for blk in v.blocks: x = blk(x, rel_pos_bias=None)
        x = v.norm(x); t = x[:, 1:, :]
        emb = v.head(v.norm(t.mean(1)))
        return emb, t
enc = Enc(v).eval(); x = torch.randn(1, 3, 224, 224)
with torch.no_grad():
    e1, t1 = enc(x); e0 = model.encode_image(x)
print("confere com encode_image:", torch.allclose(e1, e0, atol=1e-4), (e1 - e0).abs().max().item(), "tokens", tuple(t1.shape))
try:
    torch.onnx.export(enc, x, "work/dermlip_fp32.onnx", input_names=["img"], output_names=["emb", "tok"], opset_version=17, dynamo=False)
except TypeError:
    torch.onnx.export(enc, x, "work/dermlip_fp32.onnx", input_names=["img"], output_names=["emb", "tok"], opset_version=17)
print("exportado")
