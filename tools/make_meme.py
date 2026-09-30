"""Two-panel meme renderer for Instagram stories (1080x1920) or posts (1080x1350).

Usage: python3 tools/make_meme.py meme.json out.jpg
meme.json:
{
  "format": "story" | "post",
  "bg": "neon-street-night.jpg",            # optional, from assets/bg
  "top":    {"label": "2013", "text": "GTA 6 is coming soon, bro", "emoji": "😎"},
  "bottom": {"label": "2026", "text": "Still waiting", "emoji": "💀"},
  "footer": "Tag someone who's been waiting since 2013"
}
"""
import html, json, os, sys
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FONTS = os.path.join(HERE, "fonts")
HANDLE = "@gta_6_daily_news"
e = lambda s: html.escape(str(s or ""))


def page(m):
    W, H = (1080, 1920) if m.get("format", "story") == "story" else (1080, 1350)
    bg = m.get("bg")
    bgcss = f"background:url('file://{os.path.join(ROOT, 'assets', 'bg', bg)}') center/cover;" if bg else "background:#0a0910;"
    def panel(p, cls):
        return f'''<div class="panel {cls}">
          <div class="lab">{e(p.get("label"))}</div>
          <div class="row"><div class="txt">{e(p.get("text"))}</div><div class="emo">{e(p.get("emoji"))}</div></div>
        </div>'''
    return f"""<html><head><meta charset="utf-8"><style>
@font-face{{font-family:Anton;src:url('file://{FONTS}/Anton.ttf')}}
@font-face{{font-family:Inter;font-weight:600;src:url('file://{FONTS}/Inter-SemiBold.ttf')}}
@font-face{{font-family:Inter;font-weight:900;src:url('file://{FONTS}/Inter-Black.ttf')}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{W}px;height:{H}px;overflow:hidden;{bgcss}font-family:Inter,'Noto Color Emoji',sans-serif;color:#f7f3ee;position:relative}}
.shade{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(10,9,16,.55),rgba(10,9,16,.35) 40%,rgba(10,9,16,.8))}}
.wrap{{position:absolute;inset:{ '150px 70px 170px' if H>1500 else '110px 60px 110px'};display:flex;flex-direction:column;gap:36px;justify-content:center}}
.panel{{border-radius:44px;padding:48px 50px;backdrop-filter:blur(22px);box-shadow:0 30px 80px -30px rgba(0,0,0,.9)}}
.panel.a{{background:rgba(255,255,255,.12);border:2px solid rgba(255,255,255,.25)}}
.panel.b{{background:rgba(255,46,136,.22);border:2px solid #ff2e88}}
.lab{{display:inline-block;font:900 30px Inter;letter-spacing:3px;color:#0a0910;background:linear-gradient(90deg,#ff2e88,#ff9a3c);padding:10px 22px;border-radius:30px;margin-bottom:22px}}
.row{{display:flex;align-items:center;gap:30px}}
.txt{{flex:1;font-family:Anton;font-size:{ '92px' if H>1500 else '74px'};line-height:1.05;text-transform:uppercase;text-shadow:0 6px 24px rgba(0,0,0,.5)}}
.emo{{font-size:{ '190px' if H>1500 else '150px'};line-height:1;filter:drop-shadow(0 16px 24px rgba(0,0,0,.5))}}
.foot{{position:absolute;left:0;right:0;bottom:{ '90px' if H>1500 else '50px'};text-align:center;font:600 36px Inter;color:#e7e2ee}}
.foot b{{display:block;font:900 30px Inter;color:#ff9a3c;margin-top:10px;letter-spacing:1px}}
</style></head><body><div class="shade"></div>
<div class="wrap">{panel(m["top"], "a")}{panel(m["bottom"], "b")}</div>
<div class="foot">{e(m.get("footer"))}<b>{HANDLE}</b></div>
</body></html>""", W, H


def main(src, out):
    m = json.load(open(src))
    doc, W, H = page(m)
    tmp = os.path.join(os.path.dirname(os.path.abspath(out)), "_meme.html")
    open(tmp, "w").write(doc)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H})
        pg.goto("file://" + tmp)
        pg.evaluate("document.fonts.ready.then(() => true)")
        pg.wait_for_timeout(300)
        pg.screenshot(path=out, type="jpeg", quality=92)
        b.close()
    os.remove(tmp)
    print("ok", out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
