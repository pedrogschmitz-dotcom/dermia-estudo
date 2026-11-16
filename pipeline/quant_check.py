import json, numpy as np, onnxruntime as ort, sys
from PIL import Image
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
meta=json.load(open("data/isic_test/pool_meta.json")); names=["melanoma","nevo","cbc","cec","ceratose_actinica","queratose_seborreica","dermatofibroma","vascular","outras"]
y=np.array([names.index(m["classe"]) for m in meta]); g=np.array([m.get("patient_id") or m.get("lesion_id") or m["isic_id"] for m in meta])
F=np.load("work/dermlip_img.npy")
rng=np.random.RandomState(1); idx=rng.choice(len(meta),300,replace=False); tg=set(g[idx]); tr=np.array([i for i in range(len(meta)) if g[i] not in tg])
clf=make_pipeline(StandardScaler(),LogisticRegression(C=0.002,max_iter=2000,class_weight="balanced")).fit(F[tr],y[tr])
mean=np.array([0.48145466,0.4578275,0.40821073],np.float32); std=np.array([0.26862954,0.26130258,0.27577711],np.float32)
def prep(p):
    im=Image.open(p).convert("RGB"); w,h=im.size; s=224/min(w,h); im=im.resize((max(224,round(w*s)),max(224,round(h*s))),Image.BICUBIC)
    w,h=im.size; l,t=(w-224)//2,(h-224)//2; im=im.crop((l,t,l+224,t+224)); a=(np.asarray(im,np.float32)/255-mean)/std; return a.transpose(2,0,1)[None]
X=[prep(f'data/isic_test/img/{meta[i]["isic_id"]}.jpg') for i in idx]
res={"torch":clf.predict(F[idx])}
for tag,f in (("onnx_fp32","work/dermlip_fp32.onnx"),("onnx_int8","work/dermlip_int8.onnx")):
    s=ort.InferenceSession(f,providers=["CPUExecutionProvider"]); E=np.stack([s.run(None,{"img":x})[0][0] for x in X]); res[tag]=clf.predict(E)
for k,p in res.items(): print(k,"acerto",round(float(np.mean(p==y[idx])),3),"| concorda com torch",round(float(np.mean(p==res['torch'])),3))
