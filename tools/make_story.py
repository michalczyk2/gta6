"""Make a 1080x1920 Instagram story that teases the day's carousel.

Usage: python3 tools/make_story.py posts/<date>/p1.jpg posts/<date>/story.jpg ["NEW POST"]
The cover slide is placed on a blurred, darkened copy of itself, with a label above
and a hint below. Stories can't link to a post automatically, so the hint points to the profile.
"""
import os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

W, H = 1080, 1920
FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")


def main(src, out, label="NEW POST"):
    cover = Image.open(src).convert("RGB")
    bg = cover.resize((int(H * cover.width / cover.height), H)).crop((0, 0, W, H))
    bg = ImageEnhance.Brightness(bg.filter(ImageFilter.GaussianBlur(40))).enhance(0.45)
    card = cover.resize((920, 1150), Image.LANCZOS)
    mask = Image.new("L", card.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, card.width - 1, card.height - 1], 44, fill=255)
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x, y = (W - card.width) // 2, 400
    ImageDraw.Draw(shadow).rounded_rectangle([x + 10, y + 30, x + card.width + 10, y + card.height + 30], 44, fill=(0, 0, 0, 170))
    shadow = shadow.filter(ImageFilter.GaussianBlur(30))
    bg = bg.convert("RGBA")
    bg.alpha_composite(shadow)
    bg.paste(card, (x, y), mask)
    d = ImageDraw.Draw(bg)
    f1 = ImageFont.truetype(os.path.join(FD, "Anton.ttf"), 120)
    f2 = ImageFont.truetype(os.path.join(FD, "Inter-Black.ttf"), 44)
    t = label.upper()
    tw = d.textlength(t, font=f1)
    d.rounded_rectangle([(W - tw) / 2 - 40, 200, (W + tw) / 2 + 40, 350], 30, fill=(255, 46, 136))
    d.text(((W - tw) / 2, 204), t, font=f1, fill=(10, 9, 16))
    hint = "Full post on our profile"
    hw = d.textlength(hint, font=f2)
    d.text(((W - hw) / 2, y + card.height + 90), hint, font=f2, fill=(247, 243, 238))
    h2 = "@gta_vi_zone"
    f3 = ImageFont.truetype(os.path.join(FD, "Inter-SemiBold.ttf"), 38)
    d.text(((W - d.textlength(h2, font=f3)) / 2, y + card.height + 160), h2, font=f3, fill=(200, 196, 210))
    bg.convert("RGB").save(out, quality=92)
    print("ok", out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], *(sys.argv[3:4] or []))
