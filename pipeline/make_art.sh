#!/bin/sh
# Gera art/ (cópia para o artefato do Claude) a partir de app/: extensões aceitas (.bin/.dat -> .wasm), sem service worker e sem CSP.
set -e; cd /home/claude/dermia; rm -rf art; mkdir -p art/data art/thumbs art/model
cp -r app/vendor app/fonts app/icons app/manifest.webmanifest art/
cp app/data/*.json art/data/; for f in app/data/*.bin; do cp "$f" "art/data/$(basename "${f%.bin}").wasm"; done
for f in app/thumbs/*.bin; do cp "$f" "art/thumbs/$(basename "${f%.bin}").wasm"; done
for f in app/model/*.dat; do cp "$f" "art/model/$(basename "${f%.dat}").wasm"; done; sed 's/\.dat"/.wasm"/g' app/model/manifest.json > art/model/manifest.json
python3 -I - <<'P'
import re
s = open("app/index.html", encoding="utf8").read(); n0 = len(s)
s = re.sub(r'<meta http-equiv="Content-Security-Policy"[^>]*>\n', "", s)
for a, b in (('"data/model_w.bin"', '"data/model_w.wasm"'), ('"data/bank.bin"', '"data/bank.wasm"'), ('+ ch + ".bin"', '+ ch + ".wasm"'), ('+ i + ".bin"', '+ i + ".wasm"'), ('navigator.serviceWorker.register("sw.js")', 'Promise.resolve()')):
    assert a in s, a; s = s.replace(a, b)
assert "Content-Security-Policy" not in s and '.bin"' not in s, "sobrou .bin ou CSP"
open("art/index.html", "w", encoding="utf8").write(s); print("art/index.html ok")
P
du -sh art | cut -f1
