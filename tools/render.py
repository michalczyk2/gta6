"""Editorial-style Instagram carousel renderer (1080x1350) for @troche_niepowaznie.

Usage: python3 render.py post.json out_dir
post.json schema:
{
  "swipe": "swipe →",
  "palette": 0-3 (optional, picks gradient pair),
  "slides": [
    {"kind": "cover", "big": "50", "title": "DAYS UNTIL GTA 6", "body": "...", "strip": "NOV 19 · PS5 / XBOX SERIES X|S"},
    {"kind": "news",  "num": "01", "tag": "NEW INFO", "title": "...", "body": "...", "punch": "...", "source": "Game Informer"},
    {"kind": "stat",  "tag": "...", "big": "$400", "title": "...", "body": "...", "punch": "...", "source": "..."},
    {"kind": "cta",   "title": "...", "options": [["Standard", "$79.99"], ["Ultimate", "$99.99"]], "body": "..."}
  ]
}
"""
import json, os, random, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

W, H, M = 1080, 1350, 84
FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
ANTON = os.path.join(FD, "Anton.ttf")
INTER_B = os.path.join(FD, "Inter-Bold.ttf")
INTER_SB = os.path.join(FD, "Inter-SemiBold.ttf")
INTER_R = os.path.join(FD, "Inter-Regular.ttf")
INTER_K = os.path.join(FD, "Inter-Black.ttf")
HANDLE = "@troche_niepowaznie"

BG = (10, 9, 14)
TEXT = (246, 243, 238)
MUTED = (150, 146, 160)
LINE = (46, 42, 58)
PALETTES = [
    ((255, 46, 136), (255, 150, 60)),   # pink -> orange (sunset)
    ((140, 70, 255), (255, 46, 136)),   # violet -> pink
    ((0, 210, 200), (120, 90, 255)),    # teal -> violet
    ((255, 150, 60), (255, 220, 90)),   # orange -> yellow
]


def F(p, s):
    return ImageFont.truetype(p, s)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def grad_img(w, h, c1, c2, diagonal=True):
    g = Image.new("RGB", (w, h))
    px = g.load()
    for y in range(h):
        for x in range(0, w):
            t = ((x / w) * 0.6 + (y / h) * 0.4) if diagonal else x / w
            px[x, y] = lerp(c1, c2, t)
    return g


def background(pal, seed):
    random.seed(seed)
    img = Image.new("RGB", (W, H), BG)
    blobs = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(blobs)
    c1, c2 = pal
    spots = [(random.choice([-120, W - 380]), random.randint(-150, 150), 520, c1),
             (random.choice([W - 420, -80]), random.randint(H - 520, H - 250), 560, c2)]
    for x, y, r, c in spots:
        d.ellipse([x, y, x + r, y + r], fill=c)
    blobs = blobs.filter(ImageFilter.GaussianBlur(170))
    img = ImageChops.add(img, ImageChops.multiply(blobs, Image.new("RGB", (W, H), (120, 120, 120))))
    # film grain
    noise = Image.effect_noise((W, H), 22).convert("RGB")
    img = Image.blend(img, ImageChops.add(img, noise, scale=2.0, offset=-60), 0.18)
    return img


def wrap(d, text, f, maxw):
    out = []
    for para in text.split("\n"):
        cur = ""
        for w in para.split():
            t = (cur + " " + w).strip()
            if d.textlength(t, font=f) <= maxw:
                cur = t
            else:
                if cur:
                    out.append(cur)
                cur = w
        out.append(cur)
    return out


def fit(d, text, path, start, maxw, max_lines, min_size=40):
    s = start
    while s > min_size:
        f = F(path, s)
        lines = wrap(d, text, f, maxw)
        if len(lines) <= max_lines and all(d.textlength(l, font=f) <= maxw for l in lines):
            return f, lines
        s -= 4
    f = F(path, min_size)
    return f, wrap(d, text, f, maxw)


def gradient_text(img, x, y, text, f, pal):
    d = ImageDraw.Draw(img)
    l, t, r, b = d.textbbox((x, y), text, font=f)
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).text((x, y), text, font=f, fill=255)
    g = grad_img(max(1, r - l), max(1, b - t), *pal)
    full = Image.new("RGB", img.size)
    full.paste(g, (l, t))
    img.paste(full, (0, 0), mask)
    return b


def chrome(img, i, n, swipe, pal):
    d = ImageDraw.Draw(img)
    f = F(INTER_SB, 28)
    d.text((M, 64), HANDLE, font=f, fill=TEXT)
    lab = f"{i:02d} / {n:02d}"
    d.text((W - M - d.textlength(lab, font=f), 64), lab, font=f, fill=MUTED)
    d.line([(M, 116), (W - M, 116)], fill=LINE, width=2)
    # progress bar
    seg = (W - 2 * M) / n
    d.line([(M, 116), (M + seg * i, 116)], fill=pal[0], width=4)
    if i < n:
        s = swipe
        fw = d.textlength(s, font=f)
        d.rounded_rectangle([W - M - fw - 40, H - 118, W - M, H - 62], 28, outline=TEXT, width=2)
        d.text((W - M - fw - 20, H - 106), s, font=f, fill=TEXT)


def pill(img, x, y, text, pal, f=None):
    d = ImageDraw.Draw(img)
    f = f or F(INTER_K, 26)
    w = d.textlength(text, font=f)
    g = grad_img(int(w + 44), 52, *pal, diagonal=False)
    m = Image.new("L", g.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, g.size[0] - 1, 51], 26, fill=255)
    img.paste(g, (x, y), m)
    d.text((x + 22, y + 10), text, font=f, fill=BG)
    return y + 52


def highlight(img, x, y, lines, f, pal, lh):
    d = ImageDraw.Draw(img)
    for ln in lines:
        w = d.textlength(ln, font=f)
        d.rectangle([x - 10, y + 4, x + w + 10, y + lh - 2], fill=pal[0])
        d.text((x, y), ln, font=f, fill=BG)
        y += lh + 8
    return y


def body_block(img, x, y, text, f, fill, maxw, lh):
    d = ImageDraw.Draw(img)
    for ln in wrap(d, text, f, maxw):
        d.text((x, y), ln, font=f, fill=fill)
        y += lh
    return y


def render(s, i, n, swipe, pal, y0=0, measure=False):
    img = background(pal, seed=i * 13) if not measure else Image.new("RGB", (W, H * 2), BG)
    d = ImageDraw.Draw(img)
    maxw = W - 2 * M
    k = s["kind"]
    if k == "cover":
        big = F(ANTON, 560)
        bb = d.textbbox((0, 0), s["big"], font=big)
        x = (W - (bb[2] - bb[0])) // 2 - bb[0]
        gradient_text(img, x, 150 - bb[1] + 40, s["big"], big, pal)
        y = 150 + (bb[3] - bb[1]) + 80
        tf, tl = fit(d, s["title"], ANTON, 128, maxw, 2)
        for ln in tl:
            d.text(((W - d.textlength(ln, font=tf)) / 2, y), ln, font=tf, fill=TEXT)
            y += int(tf.size * 1.08)
        y += 20
        if s.get("body"):
            bf = F(INTER_R, 40)
            for ln in wrap(d, s["body"], bf, maxw):
                d.text(((W - d.textlength(ln, font=bf)) / 2, y + 24), ln, font=bf, fill=MUTED)
                y += 54
        if s.get("strip"):
            sf = F(INTER_K, 26)
            w = d.textlength(s["strip"], font=sf) + 44
            pill(img, int((W - w) / 2), H - 230, s["strip"], pal, sf)
    elif k in ("news", "stat"):
        y = 190 + y0
        if s.get("tag"):
            label = (s.get("num", "") + "  ·  " if s.get("num") else "") + s["tag"]
            y = pill(img, M, y, label.upper(), pal) + 60
        if k == "stat":
            big = F(ANTON, 300)
            bb = d.textbbox((M, y), s["big"], font=big)
            gradient_text(img, M, y - (bb[1] - y), s["big"], big, pal)
            y += (bb[3] - bb[1]) + 40
        tf, tl = fit(d, s["title"].upper(), ANTON, 118 if k == "news" else 92, maxw, 3 if k == "news" else 2)
        for ln in tl:
            d.text((M, y), ln, font=tf, fill=TEXT)
            y += int(tf.size * 1.06)
        y += 56 + int(tf.size * 0.22)
        if s.get("body"):
            y = body_block(img, M, y, s["body"], F(INTER_R, 38), (215, 211, 222), maxw, 54) + 30
        if s.get("punch"):
            pf = F(INTER_K, 36)
            y = highlight(img, M + 10, y, wrap(d, s["punch"], pf, maxw - 20), pf, pal, 48)
        if measure:
            return y
        if s.get("source"):
            d.text((M, H - 106), "Source: " + s["source"], font=F(INTER_SB, 26), fill=MUTED)
    elif k == "cta":
        y = 230 + y0
        tf, tl = fit(d, s["title"].upper(), ANTON, 150, maxw, 3)
        for ln in tl:
            gradient_text(img, M, y, ln, tf, pal)
            y += int(tf.size * 1.05)
        y += 50
        opts = s.get("options") or []
        if opts:
            gap = 28
            cw = (maxw - gap * (len(opts) - 1)) / len(opts)
            for j, (name, price) in enumerate(opts):
                x0 = M + j * (cw + gap)
                d.rounded_rectangle([x0, y, x0 + cw, y + 250], 32, outline=pal[j % 2], width=3, fill=(20, 18, 28))
                d.text((x0 + 34, y + 36), name.upper(), font=F(INTER_K, 30), fill=MUTED)
                d.text((x0 + 34, y + 90), price, font=F(ANTON, 104), fill=TEXT)
            y += 250 + 60
        if s.get("body"):
            y = body_block(img, M, y, s["body"], F(INTER_SB, 40), TEXT, maxw, 56)
        if measure:
            return y
    chrome(img, i, n, swipe, pal)
    return img


if __name__ == "__main__":
    data = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    os.makedirs(out, exist_ok=True)
    pal = PALETTES[data.get("palette", 0) % len(PALETTES)]
    sl = data["slides"]
    sw = data.get("swipe", "swipe →")
    for i, s in enumerate(sl, 1):
        y0 = 0
        if s["kind"] != "cover":
            end = render(s, i, len(sl), sw, pal, measure=True)
            start = 190 if s["kind"] != "cta" else 230
            y0 = max(0, int((H - 150 - 150) / 2 - (end - start) / 2 + 150 - start))
        render(s, i, len(sl), sw, pal, y0=y0).save(os.path.join(out, f"slide_{i}.jpg"), quality=93)
    print("ok", len(sl))
