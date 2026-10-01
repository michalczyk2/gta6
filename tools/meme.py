"""Meme story renderer (1080x1920) with 3 templates, driven by JSON. Supports Polish characters.

Usage: python3 tools/meme.py meme.json out.jpg

Templates (field "template"):
  "list": {"title": "Things I did", "title2": "waiting for GTA 6", "items": [["🎮", "text"], ...], "bg": "rooftop-gym-purple.jpg"}
          The last item is highlighted in pink. 4–6 items.
  "sms":  {"title": "Asking mom for GTA 6", "contact": "Mom ❤️", "avatar": "👩", "time": "Today 18:42",
           "messages": [["them", "text"], ["me", "text"], ...], "bg": "infinity-pool-teal.jpg"}   (5–8 short messages)
  "vs":   {"title": "$80 GTA 6", "top": {"tag": "ME, SEPTEMBER", "text": "…", "emoji": "🧐"},
           "bottom": {"tag": "ME, NOV 19, 00:01", "text": "…", "emoji": "🤡"}, "bg": "supercar-bay-neon.jpg"}
  "thisorthat": {"title": "This or that?", "left": ["🚗", "Fast cars"], "right": ["🚤", "Speedboats"], "footer": "Reply with your pick 👇", "bg": "..."}
  "fact":  {"tag": "DID YOU KNOW?", "big": "2013", "text": "GTA 5 came out 13 years ago…", "punch": "…and we're still here.", "bg": "..."}
  "quiz":  {"question": "Who are the two GTA 6 protagonists?", "answers": ["A", "B", "C"], "footer": "Answer tomorrow 👀", "bg": "..."}
Use *word* to highlight a word in yellow (vs template text).
"""
import html, json, os, re, sys
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
F = os.path.join(HERE, "fonts")
BG = os.path.join(ROOT, "assets", "bg")
HANDLE = "@gta_6_daily_news"
e = lambda s: html.escape(str(s or ""))
hl = lambda s: re.sub(r"\*(.+?)\*", r"<i>\1</i>", e(s)).replace("\n", "<br>")

BASE = f"""
@font-face{{font-family:Anton;src:url('file://{F}/Anton.ttf')}}
@font-face{{font-family:Anton;src:url('file://{F}/Anton-LatinExt.ttf');unicode-range:U+0100-024F,U+1E00-1EFF}}
@font-face{{font-family:Inter;font-weight:400;src:url('file://{F}/Inter-Regular.ttf')}}
@font-face{{font-family:Inter;font-weight:600;src:url('file://{F}/Inter-SemiBold.ttf')}}
@font-face{{font-family:Inter;font-weight:900;src:url('file://{F}/Inter-Black.ttf')}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1920px;overflow:hidden;font-family:Inter,'Noto Color Emoji',sans-serif;color:#f7f3ee;position:relative;background:#0a0910}}
.bg{{position:absolute;inset:0;background-size:cover;background-position:center}}
.shade{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(10,9,16,.75),rgba(10,9,16,.55) 45%,rgba(10,9,16,.9))}}
.handle{{position:absolute;left:0;right:0;bottom:90px;text-align:center;font:900 32px Inter;color:#ff9a3c;letter-spacing:1px}}
.head{{font-family:Anton;text-transform:uppercase;line-height:1.02;text-shadow:0 6px 24px rgba(0,0,0,.6)}}
.grad{{background:linear-gradient(120deg,#ff2e88,#ff9a3c);-webkit-background-clip:text;background-clip:text;color:transparent}}
i{{font-style:normal;color:#ffd84a}}
"""


def t_list(m):
    items = m["items"]
    rows = "".join(
        f'<div class="it{" last" if j == len(items) - 1 else ""}"><b>{e(a)}</b>{e(b)}</div>' for j, (a, b) in enumerate(items))
    return f"""<style>
.box{{position:absolute;left:80px;right:80px;top:200px}}
.it{{display:flex;gap:26px;align-items:center;margin-top:28px;padding:26px 30px;border-radius:30px;background:rgba(20,17,30,.62);border:1.5px solid rgba(255,255,255,.14);backdrop-filter:blur(18px);font:600 38px/1.3 Inter}}
.it b{{flex:none;font-size:56px}}
.last{{background:rgba(255,46,136,.28);border-color:#ff2e88}}
</style><div class="box"><div class="head" style="font-size:100px">{e(m["title"])}</div>
<div class="head grad" style="font-size:100px">{e(m.get("title2"))}</div>{rows}</div>"""


def t_sms(m):
    msgs = "".join(f'<div class="m {"r" if who == "me" else "l"}">{e(t)}</div>' for who, t in m["messages"])
    return f"""<style>
.phone{{position:absolute;left:90px;right:90px;top:260px;bottom:340px;background:#000;border-radius:70px;border:10px solid #1d1b24;box-shadow:0 40px 120px rgba(0,0,0,.8);overflow:hidden}}
.top{{height:190px;background:#111016;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;padding-bottom:22px;border-bottom:1px solid #26232f}}
.av{{width:86px;height:86px;border-radius:50%;background:linear-gradient(135deg,#8e8e93,#636366);display:flex;align-items:center;justify-content:center;font-size:48px}}
.nm{{font:600 28px Inter;margin-top:10px;color:#fff}}
.msgs{{padding:44px 34px;display:flex;flex-direction:column;gap:24px}}
.m{{max-width:78%;padding:24px 32px;border-radius:40px;font:400 42px/1.3 Inter}}
.l{{align-self:flex-start;background:#26252b;color:#fff;border-bottom-left-radius:10px}}
.r{{align-self:flex-end;background:#0a84ff;color:#fff;border-bottom-right-radius:10px}}
.time{{align-self:center;font:600 24px Inter;color:#8e8e93;margin:6px 0}}
</style><div class="head grad" style="position:absolute;left:40px;right:40px;top:100px;text-align:center;font-size:90px">{e(m["title"])}</div>
<div class="phone"><div class="top"><div class="av">{e(m.get("avatar", "👤"))}</div><div class="nm">{e(m.get("contact"))}</div></div>
<div class="msgs"><div class="time">{e(m.get("time", "Today 18:42"))}</div>{msgs}</div></div>"""


def t_vs(m):
    a, b = m["top"], m["bottom"]
    return f"""<style>
.card{{position:absolute;left:80px;right:80px;border-radius:44px;padding:50px;backdrop-filter:blur(22px)}}
.a{{top:360px;background:rgba(255,255,255,.12);border:2px solid rgba(255,255,255,.25)}}
.b{{top:1010px;background:rgba(255,46,136,.24);border:2px solid #ff2e88}}
.tag{{display:inline-block;font:900 28px Inter;letter-spacing:2px;color:#0a0910;background:linear-gradient(90deg,#ff2e88,#ff9a3c);padding:10px 22px;border-radius:30px;margin-bottom:24px}}
.q{{font:600 50px/1.35 Inter;padding-right:150px}}
.emo{{position:absolute;right:40px;bottom:30px;font-size:150px}}
</style><div class="head" style="position:absolute;left:40px;right:40px;top:150px;text-align:center;font-size:110px">{e(m["title"])}</div>
<div class="card a"><div class="tag">{e(a["tag"])}</div><div class="q">{hl(a["text"])}</div><div class="emo">{e(a.get("emoji"))}</div></div>
<div class="card b"><div class="tag">{e(b["tag"])}</div><div class="q">{hl(b["text"])}</div><div class="emo">{e(b.get("emoji"))}</div></div>"""


def t_thisorthat(m):
    L, R = m["left"], m["right"]
    side = lambda x, c: f'<div class="opt {c}"><div class="em">{e(x[0])}</div><div class="lb">{e(x[1])}</div></div>'
    return f"""<style>
.opts{{position:absolute;left:70px;right:70px;top:560px;display:flex;gap:40px}}
.opt{{flex:1;height:760px;border-radius:50px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:40px;backdrop-filter:blur(20px)}}
.o1{{background:rgba(255,46,136,.28);border:3px solid #ff2e88}} .o2{{background:rgba(0,194,255,.24);border:3px solid #00c2ff}}
.em{{font-size:220px;line-height:1}} .lb{{font-family:Anton;font-size:72px;text-transform:uppercase;text-align:center;padding:0 20px;line-height:1.05}}
.or{{position:absolute;left:50%;top:880px;transform:translate(-50%,-50%);width:150px;height:150px;border-radius:50%;background:#f7f3ee;color:#0a0910;display:flex;align-items:center;justify-content:center;font-family:Anton;font-size:64px;box-shadow:0 0 0 12px rgba(10,9,16,.8);z-index:3}}
.ft{{position:absolute;left:0;right:0;top:1400px;text-align:center;font:900 46px Inter}}
</style><div class="head grad" style="position:absolute;left:40px;right:40px;top:240px;text-align:center;font-size:150px">{e(m.get("title","This or that?"))}</div>
<div class="opts">{side(L,"o1")}{side(R,"o2")}</div><div class="or">OR</div><div class="ft">{e(m.get("footer"))}</div>"""


def t_fact(m):
    return f"""<style>
.f{{position:absolute;left:80px;right:80px;top:300px}}
.tg{{display:inline-block;font:900 34px Inter;letter-spacing:3px;color:#0a0910;background:#ffd84a;padding:14px 28px;border-radius:16px;transform:rotate(-3deg)}}
.big{{font-family:Anton;font-size:360px;line-height:1;margin-top:60px}}
.tx{{font:600 56px/1.3 Inter;margin-top:30px}}
.pn{{display:inline-block;margin-top:50px;font:900 50px/1.3 Inter;color:#0a0910;background:#ff2e88;padding:12px 24px;transform:rotate(-1.5deg)}}
</style><div class="f"><div class="tg">{e(m.get("tag","DID YOU KNOW?"))}</div><div class="big grad">{e(m.get("big"))}</div>
<div class="tx">{hl(m["text"])}</div>{f'<div class="pn">{e(m["punch"])}</div>' if m.get("punch") else ""}</div>"""


def t_quiz(m):
    ans = "".join(f'<div class="an"><b>{chr(65+j)}</b>{e(a)}</div>' for j, a in enumerate(m["answers"]))
    return f"""<style>
.q{{position:absolute;left:80px;right:80px;top:300px}}
.qt{{font:900 30px Inter;letter-spacing:4px;color:#ff9a3c}}
.qq{{font-family:Anton;font-size:110px;line-height:1.05;text-transform:uppercase;margin:24px 0 60px}}
.an{{display:flex;gap:30px;align-items:center;padding:34px 36px;margin-top:30px;border-radius:34px;background:rgba(20,17,30,.65);border:2px solid rgba(255,255,255,.18);font:600 50px Inter;backdrop-filter:blur(16px)}}
.an b{{flex:none;width:90px;height:90px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-family:Anton;font-weight:400;font-size:56px;color:#0a0910;background:linear-gradient(135deg,#ff2e88,#ff9a3c)}}
.ft{{margin-top:60px;text-align:center;font:900 44px Inter}}
</style><div class="q"><div class="qt">🧠 GTA 6 QUIZ</div><div class="qq">{e(m["question"])}</div>{ans}<div class="ft">{e(m.get("footer"))}</div></div>"""


TEMPLATES = {"list": t_list, "sms": t_sms, "vs": t_vs, "thisorthat": t_thisorthat, "fact": t_fact, "quiz": t_quiz}
DEFAULT_BG = {"list": "rooftop-gym-purple.jpg", "sms": "infinity-pool-teal.jpg", "vs": "supercar-bay-neon.jpg",
              "thisorthat": "marina-yachts-sunset.jpg", "fact": "classic-car-bridge-night.jpg", "quiz": "neon-street-night.jpg"}


def main(src, out):
    m = json.load(open(src))
    out = os.path.abspath(out)
    bg = m.get("bg") or DEFAULT_BG[m["template"]]
    body = f"<div class='bg' style=\"background-image:url('file://{BG}/{bg}')\"></div><div class='shade'></div>"
    body += TEMPLATES[m["template"]](m) + f'<div class="handle">{HANDLE}</div>'
    tmp = os.path.join(os.path.dirname(out), "_meme.html")
    open(tmp, "w").write(f"<html><head><meta charset='utf-8'><style>{BASE}</style></head><body>{body}</body></html>")
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1920})
        pg.goto("file://" + tmp)
        pg.evaluate("document.fonts.ready.then(() => true)")
        pg.wait_for_timeout(300)
        pg.screenshot(path=out, type="jpeg", quality=92)
        b.close()
    os.remove(tmp)
    print("ok", out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
