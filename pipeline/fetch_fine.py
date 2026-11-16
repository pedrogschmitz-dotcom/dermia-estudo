import json,requests,io,os,time
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
plan=json.load(open('work/fine_plan.json'));ids=plan['new'];rows=[]
def one(i):
    for t in range(4):
        try:
            j=requests.get(f"https://api.isic-archive.com/api/v2/images/{i}/",timeout=60).json()
            c=j["metadata"]["clinical"];p=f"data/fine_img/{i}.jpg"
            if not os.path.exists(p):
                r=requests.get(j["files"]["full"]["url"],timeout=90);r.raise_for_status()
                im=Image.open(io.BytesIO(r.content)).convert("RGB");im.thumbnail((512,512));im.save(p,quality=92)
            return dict(isic_id=i,licenca=j["copyright_license"],atribuicao=j.get("attribution"),sexo=c.get("sex"),idade=c.get("age_approx"),local=c.get("anatom_site_1"),lesion_id=c.get("lesion_id"),patient_id=c.get("patient_id"))
        except Exception as e: err=e;time.sleep(2)
    print("falhou",i,err,flush=True);return None
with ThreadPoolExecutor(8) as ex: rows=[r for r in ex.map(one,ids) if r]
json.dump(rows,open('data/fine_meta.json','w'),ensure_ascii=False);print("ok",len(rows),flush=True)
