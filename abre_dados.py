# Restaura os dados: python3 abre_dados.py pasta_do_ramo_dados destino   (pede a frase do app)
import sys, os, io, json, tarfile, hashlib, base64, getpass
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
src, dst = sys.argv[1], sys.argv[2]; pw = os.environ.get("FRASE") or getpass.getpass("Frase do app: ")
m = json.load(open(os.path.join(src, "manifesto.json"))); key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=base64.b64decode(m["salt"]), iterations=m["iter"]).derive(pw.encode())
data = b"".join(AESGCM(key).decrypt((b := open(os.path.join(src, p), "rb").read())[:12], b[12:], None) for p in m["parts"])
assert hashlib.sha256(data).hexdigest() == m["sha256"], "arquivo corrompido"
tarfile.open(fileobj=io.BytesIO(data)).extractall(dst); print("aberto em", os.path.join(dst, "backup"), "| depois: sh", os.path.join(dst, "backup", "restaurar.sh"))
