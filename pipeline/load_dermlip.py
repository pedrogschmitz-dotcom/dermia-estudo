import sys, torch
sys.path.insert(0, "/home/claude/derm1m_repo/src/src")
import open_clip
from safetensors.torch import load_file
def load(weights="/home/claude/dermia/work/dermlip_panderm/open_clip_model.safetensors"):
    model, _, pre = open_clip.create_model_and_transforms("PanDerm-base-w-PubMed-256", pretrained=None)
    r = model.load_state_dict(load_file(weights), strict=False)
    return model.eval(), pre, open_clip.get_tokenizer("PanDerm-base-w-PubMed-256"), r
if __name__ == "__main__":
    m, pre, tok, r = load(); print("faltando:", len(r.missing_keys), r.missing_keys[:5]); print("sobrando:", len(r.unexpected_keys), r.unexpected_keys[:5])
    print(open_clip.__file__); print(pre)
