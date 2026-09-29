"""HTML/CSS carousel renderer (1080x1350) for @troche_niepowaznie, rendered with headless Chromium.

Usage: python3 tools/render_html.py posts/<date>/post.json posts/<date>

post.json:
{
  "palette": 0-3,
  "slides": [
    {"kind": "cover",  "big": "50", "title": "DAYS UNTIL GTA 6", "body": "...", "sticker": "NEW INFO 🔥", "strip": "NOV 19 · PS5 · XBOX SERIES X|S"},
    {"kind": "news",   "num": "01", "tag": "New info", "emoji": "🌪️", "title": "...", "body": "...", "punch": "...", "source": "..."},
    {"kind": "stat",   "num": "02", "tag": "...", "big": "$400", "title": "...", "body": "...", "punch": "...", "source": "..."},
    {"kind": "tweet",  "name": "Rockstar fans", "handle": "@everyone", "text": "...", "likes": "12.4K", "caption": "..."},
    {"kind": "versus", "title": "...", "left": ["PS5", "✅ Nov 19"], "right": ["PC", "❌ 2027?"], "punch": "..."},
    {"kind": "list",   "tag": "...", "title": "...", "items": ["...", "..."], "source": "..."},
    {"kind": "cta",    "title": "...", "options": [["Standard", "$79.99"], ["Ultimate", "$99.99"]], "body": "..."}
  ]
}
Background photos: put .jpg files in assets/bg/. Post-level "photos": true gives every slide a photo
background (cover/cta strong, content slides dimmed). Per slide, "bg": "<filename>" picks a specific photo,
"bg": "none" disables it. Without an explicit choice, photos are picked deterministically per post and slide.
Every text field may contain emoji. Keep text short; the renderer auto-shrinks headlines to fit.
"""
import hashlib, html, json, os, sys
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
BGDIR = os.path.join(os.path.dirname(HERE), "assets", "bg")
HANDLE = "@troche_niepowaznie"
PALETTES = [
    ("#ff2e88", "#ff9a3c", "#7b2cff"),
    ("#8c46ff", "#ff2e88", "#00d2c8"),
    ("#00d2c8", "#7858ff", "#ff2e88"),
    ("#ff9a3c", "#ffd84a", "#ff2e88"),
]

e = lambda s: html.escape(str(s or ""))

CSS = """
@font-face{font-family:Anton;src:url('file://%(f)s/Anton.ttf')}
@font-face{font-family:Inter;font-weight:400;src:url('file://%(f)s/Inter-Regular.ttf')}
@font-face{font-family:Inter;font-weight:600;src:url('file://%(f)s/Inter-SemiBold.ttf')}
@font-face{font-family:Inter;font-weight:700;src:url('file://%(f)s/Inter-Bold.ttf')}
@font-face{font-family:Inter;font-weight:900;src:url('file://%(f)s/Inter-Black.ttf')}
:root{--a:%(a)s;--b:%(b)s;--c:%(c)s;--bg:#0a0910;--text:#f7f3ee;--muted:#a19cae}
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1080px;height:1350px;background:var(--bg);overflow:hidden}
body{font-family:Inter,'Noto Color Emoji',sans-serif;color:var(--text);position:relative}
.bg{position:absolute;inset:0;overflow:hidden}
.photo{position:absolute;inset:0;background-size:cover;background-position:center;z-index:0}
.photo.strong::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(10,9,16,.55) 0%%,rgba(10,9,16,.15) 35%%,rgba(10,9,16,.55) 65%%,rgba(10,9,16,.92) 100%%)}
.photo.dim{filter:saturate(1.1)}
.photo.dim::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(10,9,16,.66),rgba(10,9,16,.80) 50%%,rgba(10,9,16,.93))}
.bg .blob{position:absolute;border-radius:50%%;filter:blur(120px);opacity:.55}
.bg .b1{width:760px;height:760px;background:var(--a);left:-260px;top:-220px}
.bg .b2{width:700px;height:700px;background:var(--b);right:-280px;bottom:-200px;opacity:.45}
.bg .b3{width:420px;height:420px;background:var(--c);right:-120px;top:360px;opacity:.28}
.bg .grid{position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.045) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.045) 1px,transparent 1px);background-size:60px 60px;mask-image:radial-gradient(ellipse at 50%% 45%%,#000 30%%,transparent 75%%)}
.bg .grain{position:absolute;inset:-50%%;opacity:.12;background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3' stitchTiles='stitch'/></filter><rect width='100%%' height='100%%' filter='url(%%23n)'/></svg>")}
.bg .vignette{position:absolute;inset:0;background:radial-gradient(ellipse at center,transparent 45%%,rgba(0,0,0,.55))}
.chrome{position:absolute;left:84px;right:84px;top:58px;display:flex;justify-content:space-between;align-items:center;font:600 28px Inter;z-index:5}
.chrome .h{display:flex;align-items:center;gap:14px}
.chrome .dot{width:14px;height:14px;border-radius:50%%;background:linear-gradient(135deg,var(--a),var(--b));box-shadow:0 0 18px var(--a)}
.chrome .n{color:var(--muted);letter-spacing:2px}
.bar{position:absolute;left:84px;right:84px;top:112px;height:4px;background:rgba(255,255,255,.1);border-radius:4px;z-index:5}
.bar i{display:block;height:100%%;border-radius:4px;background:linear-gradient(90deg,var(--a),var(--b))}
.swipe{position:absolute;right:84px;bottom:64px;font:700 28px Inter;padding:14px 28px;border-radius:40px;border:2px solid rgba(255,255,255,.35);backdrop-filter:blur(10px);background:rgba(255,255,255,.06);z-index:5}
.source{position:absolute;left:84px;bottom:78px;font:600 24px Inter;color:var(--muted);z-index:5}
.content{position:absolute;left:84px;right:84px;top:150px;bottom:150px;display:flex;flex-direction:column;justify-content:center;z-index:4}
.grad{filter:drop-shadow(0 4px 22px rgba(0,0,0,.75));background:linear-gradient(120deg,var(--a),var(--b));-webkit-background-clip:text;background-clip:text;color:transparent}
.pill{align-self:flex-start;font:900 26px Inter;letter-spacing:1.5px;text-transform:uppercase;color:#0a0910;padding:12px 24px;border-radius:40px;background:linear-gradient(90deg,var(--a),var(--b));margin-bottom:44px;box-shadow:0 10px 40px -10px var(--a)}
.title{font-family:Anton;text-transform:uppercase;line-height:1.02;letter-spacing:.5px;text-shadow:0 6px 30px rgba(0,0,0,.35)}
.body{font:400 38px/1.45 Inter;color:#dcd7e4;margin-top:34px}
.punch{margin-top:38px;align-self:flex-start;font:900 36px/1.3 Inter;color:#0a0910;background:var(--a);padding:10px 20px;transform:rotate(-1.5deg);box-shadow:8px 8px 0 rgba(0,0,0,.45)}
.card{background:rgba(20,17,30,.55);border:1.5px solid rgba(255,255,255,.12);border-radius:40px;padding:56px;backdrop-filter:blur(24px);box-shadow:0 30px 80px -30px rgba(0,0,0,.8)}
.emoji{position:absolute;right:70px;top:170px;font-size:170px;transform:rotate(12deg);filter:drop-shadow(0 20px 30px rgba(0,0,0,.5));z-index:3}
.bignum{font-family:Anton;line-height:.9}
.outline{position:absolute;font-family:Anton;color:transparent;-webkit-text-stroke:2px rgba(255,255,255,.10);white-space:nowrap;z-index:1}
.sticker{position:absolute;font:900 30px Inter;color:#0a0910;background:#ffe14a;padding:14px 26px;border-radius:14px;transform:rotate(8deg);box-shadow:6px 6px 0 rgba(0,0,0,.5);z-index:6}
.opts{display:flex;gap:28px;margin-top:56px}
.opt{flex:1;border-radius:36px;padding:40px 36px;background:rgba(20,17,30,.6);border:2px solid var(--a);backdrop-filter:blur(20px)}
.opt:nth-child(2){border-color:var(--b)}
.opt .k{font:900 28px Inter;letter-spacing:2px;color:var(--muted);text-transform:uppercase}
.opt .v{font-family:Anton;font-size:108px;margin-top:10px}
.tw{background:#fff;color:#0f1419;border-radius:36px;padding:48px;box-shadow:0 40px 90px -30px rgba(0,0,0,.9);transform:rotate(-2deg)}
.tw .who{display:flex;align-items:center;gap:22px}
.tw .av{width:92px;height:92px;border-radius:50%%;background:linear-gradient(135deg,var(--a),var(--b))}
.tw .nm{font:900 34px Inter}.tw .hd{font:400 28px Inter;color:#536471}
.tw .tx{font:400 44px/1.35 Inter;margin-top:30px}
.tw .ft{font:600 28px Inter;color:#536471;margin-top:30px}
.vs{display:flex;gap:64px;align-items:stretch;margin-top:48px;position:relative}
.vs .side{flex:1;border-radius:36px;padding:40px 30px;background:rgba(20,17,30,.6);backdrop-filter:blur(20px);border:2px solid rgba(255,255,255,.12)}
.vs .side .k{font-family:Anton;font-size:70px;white-space:nowrap}
.vs .side .l{font:600 34px/1.5 Inter;margin-top:16px;color:#dcd7e4}
.vs .mid{position:absolute;z-index:3;left:50%%;top:50%%;transform:translate(-50%%,-50%%);width:96px;height:96px;border-radius:50%%;display:flex;align-items:center;justify-content:center;font-family:Anton;font-size:40px;color:#0a0910;background:linear-gradient(135deg,var(--a),var(--b));box-shadow:0 0 0 10px var(--bg)}
.items{margin-top:40px;display:flex;flex-direction:column;gap:22px}
.items .it{display:flex;gap:24px;align-items:flex-start;font:600 36px/1.35 Inter}
.items .it b{flex:none;font-family:Anton;font-weight:400;font-size:44px;width:70px;height:70px;border-radius:20px;display:flex;align-items:center;justify-content:center;color:#0a0910;background:linear-gradient(135deg,var(--a),var(--b))}
.strip{position:absolute;left:0;right:0;bottom:170px;text-align:center;z-index:5}
.strip span{font:900 26px Inter;letter-spacing:2px;padding:14px 28px;border-radius:40px;border:2px solid rgba(255,255,255,.3);background:rgba(255,255,255,.06);backdrop-filter:blur(10px)}
"""

FIT_JS = """
() => {
  for (const el of document.querySelectorAll('[data-fit]')) {
    const max = +el.dataset.fit, min = +(el.dataset.min || 40), lines = +(el.dataset.lines || 3);
    let s = max; el.style.fontSize = s + 'px';
    const lh = () => parseFloat(getComputedStyle(el).lineHeight) || s * 1.02;
    while (s > min && (el.scrollWidth > el.clientWidth + 1 || el.offsetHeight > lh() * lines + 2)) {
      s -= 3; el.style.fontSize = s + 'px';
    }
  }
}
"""


def photo_for(s, i, key, photos_on):
    choice = s.get("bg")
    if choice == "none" or (not photos_on and not choice):
        return ""
    files = sorted(f for f in os.listdir(BGDIR) if f.lower().endswith((".jpg", ".jpeg", ".png"))) if os.path.isdir(BGDIR) else []
    if not files:
        return ""
    if not choice or choice not in files:
        h = int(hashlib.md5(key.encode()).hexdigest(), 16)
        choice = files[(h + i * 7) % len(files)]
    strong = s["kind"] == "cover"
    return f'<div class="photo {"strong" if strong else "dim"}" style="background-image:url(\'file://{os.path.join(BGDIR, choice)}\')"></div>'


def bg():
    return '<div class="bg"><div class="blob b1"></div><div class="blob b2"></div><div class="blob b3"></div><div class="grid"></div><div class="grain"></div><div class="vignette"></div></div>'


def chrome(i, n):
    s = f'<div class="chrome"><div class="h"><span class="dot"></span>{HANDLE}</div><div class="n">{i:02d} / {n:02d}</div></div>'
    s += f'<div class="bar"><i style="width:{100*i/n:.1f}%"></i></div>'
    if i < n:
        s += '<div class="swipe">swipe →</div>'
    return s


def slide_html(s, i, n, key="", photos_on=False):
    k = s["kind"]
    ph = photo_for(s, i, key, photos_on)
    out = ph + bg()
    if ph:
        out = out.replace('<div class="bg">', '<div class="bg" style="opacity:.35">')
    src = f'<div class="source">Source: {e(s["source"])}</div>' if s.get("source") else ""
    if k == "cover":
        out += f'<div class="outline" style="font-size:520px;left:-40px;top:560px">{e(s.get("big",""))}</div>'
        if s.get("sticker"):
            out += f'<div class="sticker" style="right:90px;top:210px">{e(s["sticker"])}</div>'
        out += f'''<div class="content" style="align-items:center;text-align:center">
          <div class="bignum grad" style="font-size:560px">{e(s.get("big",""))}</div>
          <div class="title" data-fit="130" data-lines="2" style="width:100%;margin-top:10px">{e(s["title"])}</div>
          {f'<div class="body" style="color:var(--muted);margin-top:26px">{e(s["body"])}</div>' if s.get("body") else ""}
        </div>'''
        if s.get("strip"):
            out += f'<div class="strip"><span>{e(s["strip"])}</span></div>'
    elif k in ("news", "stat"):
        tag = (f'{e(s["num"])} · ' if s.get("num") else "") + e(s.get("tag", ""))
        if s.get("emoji") and k == "news":
            out += f'<div class="emoji">{e(s["emoji"])}</div>'
        big = f'<div class="bignum grad" style="font-size:280px;margin-bottom:6px">{e(s["big"])}</div>' if k == "stat" else ""
        out += f'''<div class="content">
          {f'<div class="pill">{tag}</div>' if tag else ""}
          {big}
          <div class="title" data-fit="{112 if k=="news" else 92}" data-lines="{3 if k=="news" else 2}" style="width:{'78%' if s.get('emoji') and k=='news' else '100%'}">{e(s["title"])}</div>
          {f'<div class="body">{e(s["body"])}</div>' if s.get("body") else ""}
          {f'<div class="punch">{e(s["punch"])}</div>' if s.get("punch") else ""}
        </div>{src}'''
    elif k == "tweet":
        out += f'''<div class="content">
          <div class="tw"><div class="who"><div class="av"></div><div><div class="nm">{e(s.get("name",""))}</div><div class="hd">{e(s.get("handle",""))}</div></div></div>
          <div class="tx">{e(s["text"])}</div><div class="ft">♥ {e(s.get("likes",""))}</div></div>
          {f'<div class="punch" style="margin-top:60px">{e(s["caption"])}</div>' if s.get("caption") else ""}
        </div>{src}'''
    elif k == "versus":
        L, R = s["left"], s["right"]
        side = lambda x: f'<div class="side"><div class="k grad">{e(x[0])}</div>' + "".join(f'<div class="l">{e(t)}</div>' for t in x[1:]) + "</div>"
        out += f'''<div class="content">
          {f'<div class="pill">{e(s["tag"])}</div>' if s.get("tag") else ""}
          <div class="title" data-fit="110" data-lines="2">{e(s["title"])}</div>
          <div class="vs">{side(L)}<div class="mid">VS</div>{side(R)}</div>
          {f'<div class="punch">{e(s["punch"])}</div>' if s.get("punch") else ""}
        </div>{src}'''
    elif k == "list":
        items = "".join(f'<div class="it"><b>{j}</b><span>{e(t)}</span></div>' for j, t in enumerate(s["items"], 1))
        out += f'''<div class="content">
          {f'<div class="pill">{e(s["tag"])}</div>' if s.get("tag") else ""}
          <div class="title" data-fit="100" data-lines="2">{e(s["title"])}</div>
          <div class="items">{items}</div>
        </div>{src}'''
    elif k == "cta":
        opts = "".join(f'<div class="opt"><div class="k">{e(a)}</div><div class="v">{e(b)}</div></div>' for a, b in s.get("options", []))
        out += f'''<div class="content">
          <div class="title grad" data-fit="150" data-lines="3">{e(s["title"])}</div>
          {f'<div class="opts">{opts}</div>' if opts else ""}
          {f'<div class="body" style="font-weight:600;color:var(--text);white-space:pre-line">{e(s["body"])}</div>' if s.get("body") else ""}
        </div>'''
    out += chrome(i, n)
    return out


def main(post, outdir):
    data = json.load(open(post))
    os.makedirs(outdir, exist_ok=True)
    a, b, c = PALETTES[data.get("palette", 0) % len(PALETTES)]
    css = CSS % {"f": FONTS, "a": a, "b": b, "c": c}
    sl = data["slides"]
    key = os.path.basename(os.path.dirname(os.path.abspath(post)))
    photos_on = data.get("photos", False)
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": 1080, "height": 1350})
        for i, s in enumerate(sl, 1):
            tmp = os.path.join(outdir, "_slide.html")
            with open(tmp, "w") as fh:
                fh.write(f"<html><head><meta charset='utf-8'><style>{css}</style></head><body>{slide_html(s, i, len(sl), key, photos_on)}</body></html>")
            pg.goto("file://" + os.path.abspath(tmp))
            pg.evaluate("document.fonts.ready.then(() => true)")
            pg.evaluate(FIT_JS)
            pg.screenshot(path=os.path.join(outdir, f"slide_{i}.jpg"), type="jpeg", quality=92)
        br.close()
    os.remove(os.path.join(outdir, "_slide.html"))
    print("ok", len(sl))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
