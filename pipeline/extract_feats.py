import sys, json, numpy as np, torch
from PIL import Image
which, data, out = sys.argv[1], sys.argv[2], sys.argv[3]
torch.set_num_threads(2)
meta = json.load(open(data + "/pool_meta.json"))
if which == "biomed":
    import open_clip
    mid = "hf-hub:microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224"
    model, _, pre = open_clip.create_model_and_transforms(mid); model.eval()
    fn = lambda b: model.encode_image(b)
else:
    from transformers import AutoModel
    import torchvision.transforms as T
    model = AutoModel.from_pretrained("facebook/dinov2-base").eval()
    pre = T.Compose([T.Resize(256, interpolation=T.InterpolationMode.BICUBIC), T.CenterCrop(224), T.ToTensor(),
                     T.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225))])
    def fn(b):
        h = model(pixel_values=b).last_hidden_state
        return torch.cat([h[:, 0], h[:, 1:].mean(1)], 1)
F = []
with torch.no_grad():
    for i in range(0, len(meta), 16):
        b = torch.stack([pre(Image.open(f'{data}/img/{m["isic_id"]}.jpg').convert("RGB")) for m in meta[i:i+16]])
        F.append(fn(b).numpy())
        if i % 160 == 0: print(i, flush=True)
np.save(out, np.concatenate(F)); print("FIM", flush=True)
