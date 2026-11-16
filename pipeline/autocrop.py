# Recorte automático da lesão (mesma lógica será portada para o app em JS).
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
def otsu(v):
    h, _ = np.histogram(v, bins=256, range=(0, 256)); p = h / max(1, h.sum()); w = np.cumsum(p); m = np.cumsum(p * np.arange(256)); mt = m[-1]
    s = (mt * w - m) ** 2 / (w * (1 - w) + 1e-12); s[(w == 0) | (w == 1)] = 0; return int(np.argmax(s))
def box(im, det=256, margin=1.35, minfrac=0.30):
    """devolve (x0, y0, lado) no tamanho original; None se não achar lesão (usar quadrado central)"""
    W, H = im.size; sc = det / max(W, H); w, h = max(1, round(W * sc)), max(1, round(H * sc))
    a = np.asarray(im.convert("RGB").resize((w, h), Image.BILINEAR), dtype=np.float32); L = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
    dark = L < 35; lab, n = ndi.label(dark); border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    valid = ~np.isin(lab, list(border)) if border else np.ones_like(dark)
    if valid.sum() < 0.2 * w * h: return None
    t = otsu(L[valid]); les = (L < t) & valid; les = ndi.binary_opening(les, iterations=2); lab, n = ndi.label(les)
    if n == 0: return None
    yy, xx = np.mgrid[0:h, 0:w]; cy, cx = h / 2, w / 2; sig = 0.35 * min(w, h)
    areas = ndi.sum(np.ones_like(L), lab, range(1, n + 1)); coms = ndi.center_of_mass(les, lab, range(1, n + 1))
    score = [a_ * np.exp(-((c[0] - cy) ** 2 + (c[1] - cx) ** 2) / (2 * sig ** 2)) for a_, c in zip(areas, coms)]; k = int(np.argmax(score)) + 1
    frac = areas[k - 1] / valid.sum()
    if frac < 0.01 or frac > 0.85: return None
    ys, xs = np.where(lab == k); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    side = max(x1 - x0, y1 - y0) * margin; side = max(side, minfrac * min(w, h)); side = min(side, min(w, h))
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2; bx = min(max(mx - side / 2, 0), w - side); by = min(max(my - side / 2, 0), h - side)
    S = int(round(side / sc)); S = min(S, W, H); X = int(round(bx / sc)); Y = int(round(by / sc)); X = min(max(X, 0), W - S); Y = min(max(Y, 0), H - S)
    return X, Y, S
