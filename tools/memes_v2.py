"""Render three meme stories (1080x1920) in different formats: SMS chat, list, and before/after.
Usage: python3 tools/memes_v2.py <out_dir>
"""
import os, sys
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
F = os.path.join(HERE, "fonts")
BG = os.path.join(ROOT, "assets", "bg")
HANDLE = "@gta_6_daily_news"

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
"""

SMS = """
<div class="bg" style="background-image:url('file://{bg}/infinity-pool-teal.jpg')"></div><div class="shade"></div>
<style>
.phone{position:absolute;left:90px;right:90px;top:260px;bottom:420px;background:#000;border-radius:70px;border:10px solid #1d1b24;box-shadow:0 40px 120px rgba(0,0,0,.8);overflow:hidden}
.top{height:190px;background:#111016;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;padding-bottom:22px;border-bottom:1px solid #26232f}
.av{width:86px;height:86px;border-radius:50%;background:linear-gradient(135deg,#8e8e93,#636366);display:flex;align-items:center;justify-content:center;font-size:48px}
.nm{font:600 28px Inter;margin-top:10px;color:#fff}
.msgs{padding:44px 34px;display:flex;flex-direction:column;gap:26px}
.m{max-width:78%;padding:24px 32px;border-radius:40px;font:400 44px/1.3 Inter}
.l{align-self:flex-start;background:#26252b;color:#fff;border-bottom-left-radius:10px}
.r{align-self:flex-end;background:#0a84ff;color:#fff;border-bottom-right-radius:10px}
.time{align-self:center;font:600 24px Inter;color:#8e8e93;margin:6px 0}
.read{align-self:flex-end;font:600 22px Inter;color:#8e8e93;margin-top:-10px}
</style>
<div class="phone"><div class="top"><div class="av">👩</div><div class="nm">Mom ❤️</div></div>
<div class="msgs">
<div class="time">Today 18:42</div>
<div class="m l">What do you want for Christmas? 🎄</div>
<div class="m r">GTA 6 🙏</div>
<div class="m l">Isn't that $80?? 😳</div>
<div class="m r">Yes. And a PS5.</div>
<div class="m r">And a new TV.</div>
<div class="m r">And 3 days off school</div>
<div class="read">Read 18:43</div>
</div></div>
<div class="head grad" style="position:absolute;left:0;right:0;top:110px;text-align:center;font-size:96px">Asking mom for GTA 6</div>
<div class="handle">{h}</div>
"""

LIST = """
<div class="bg" style="background-image:url('file://{bg}/rooftop-gym-purple.jpg')"></div><div class="shade"></div>
<style>
.box{position:absolute;left:80px;right:80px;top:200px}
.it{display:flex;gap:26px;align-items:center;margin-top:28px;padding:26px 30px;border-radius:30px;background:rgba(20,17,30,.62);border:1.5px solid rgba(255,255,255,.14);backdrop-filter:blur(18px);font:600 38px/1.3 Inter}
.it b{flex:none;font-size:56px}
.last{background:rgba(255,46,136,.28);border-color:#ff2e88}
</style>
<div class="box">
<div class="head" style="font-size:100px">Things I did</div>
<div class="head grad" style="font-size:100px">waiting for GTA 6</div>
<div class="it"><b>🎮</b>Bought GTA 5 on PS3, PS4 AND PS5</div>
<div class="it"><b>🎓</b>Finished school. Twice.</div>
<div class="it"><b>💼</b>Got a job. Lost it. Got another one.</div>
<div class="it"><b>🧓</b>Found my first grey hair</div>
<div class="it"><b>📅</b>Booked Nov 19–23 off work</div>
<div class="it last"><b>💀</b>Still here. 50 days left.</div>
</div>
<div class="handle">{h}</div>
"""

VS = """
<div class="bg" style="background-image:url('file://{bg}/supercar-bay-neon.jpg')"></div><div class="shade"></div>
<style>
.card{position:absolute;left:80px;right:80px;border-radius:44px;padding:50px;backdrop-filter:blur(22px)}
.a{top:360px;background:rgba(255,255,255,.12);border:2px solid rgba(255,255,255,.25)}
.b{top:1010px;background:rgba(255,46,136,.24);border:2px solid #ff2e88}
.tag{display:inline-block;font:900 28px Inter;letter-spacing:2px;color:#0a0910;background:linear-gradient(90deg,#ff2e88,#ff9a3c);padding:10px 22px;border-radius:30px;margin-bottom:24px}
.q{font:600 50px/1.35 Inter;padding-right:150px}
.q i{font-style:normal;color:#ffd84a}
.emo{position:absolute;right:40px;bottom:30px;font-size:150px}
</style>
<div class="head" style="position:absolute;left:0;right:0;top:150px;text-align:center;font-size:110px">$80 GTA 6</div><div class="card a"><div class="tag">ME, SEPTEMBER</div>
<div class="q">"$80 for a game? That's crazy.<br>I'll wait for a sale.<br>I'm a <i>responsible adult</i> now."</div><div class="emo">🧐</div></div>
<div class="card b"><div class="tag">ME, NOV 19, 00:01</div>
<div class="q">Bought the <i>Ultimate Edition</i>.<br>Called in sick.<br>Hid from my family.</div><div class="emo">🤡</div></div>
<div class="handle">{h}</div>
"""

LIST_PL = LIST.replace('Things I did','Rzeczy, które zrobiłem').replace('waiting for GTA 6','czekając na GTA 6') \
  .replace('Bought GTA 5 on PS3, PS4 AND PS5','Kupiłem GTA 5 na PS3, PS4 I PS5') \
  .replace('Finished school. Twice.','Skończyłem szkołę. Dwa razy.') \
  .replace('Got a job. Lost it. Got another one.','Znalazłem pracę. Straciłem. Znalazłem nową.') \
  .replace('Found my first grey hair','Znalazłem pierwszy siwy włos') \
  .replace('Booked Nov 19–23 off work','Wziąłem urlop 19–23 listopada') \
  .replace('Still here. 50 days left.','Dalej tu jestem. Zostało 50 dni.')


def main(out):
    out = os.path.abspath(out)
    os.makedirs(out, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1920})
        for name, body in (("meme_sms", SMS), ("meme_list", LIST), ("meme_vs", VS), ("meme_list_pl", LIST_PL)):
            tmp = os.path.join(out, "_m.html")
            open(tmp, "w").write(f"<html><head><meta charset='utf-8'><style>{BASE}</style></head><body>{body.replace('{bg}', BG).replace('{h}', HANDLE)}</body></html>")
            pg.goto("file://" + tmp)
            pg.evaluate("document.fonts.ready.then(() => true)")
            pg.wait_for_timeout(300)
            pg.screenshot(path=os.path.join(out, name + ".jpg"), type="jpeg", quality=92)
        os.remove(tmp)
        b.close()
    print("ok")


if __name__ == "__main__":
    main(sys.argv[1])
