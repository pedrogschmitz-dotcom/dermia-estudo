import os, sys, json, base64, hashlib, secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
src, outdir, passfile = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(outdir, exist_ok=True)
words = secrets.token_hex(10)
pw = f"curae-{words[:5]}-{words[5:10]}-{words[10:15]}-{words[15:]}"
if os.path.exists(passfile): pw = open(passfile).read().strip()   # mantém a frase já entregue ao Pedro
salt = os.urandom(16); ITER = 200000
key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITER).derive(pw.encode())
data = open(src, "rb").read(); CH = 16 * 1024 * 1024; chunks = []
for n, i in enumerate(range(0, len(data), CH)):
    part = data[i:i + CH]; iv = os.urandom(12); ct = AESGCM(key).encrypt(iv, part, None)
    f = f"m{n}.dat"; open(f"{outdir}/{f}", "wb").write(iv + ct); chunks.append(dict(f=f, plain=len(part)))
json.dump(dict(salt=base64.b64encode(salt).decode(), iter=ITER, total=len(data), sha256=hashlib.sha256(data).hexdigest(), chunks=chunks), open(f"{outdir}/manifest.json", "w"))
open(passfile, "w").write(pw); print("chunks", len(chunks), "| frase salva em", passfile)
