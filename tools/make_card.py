import json, sys, textwrap
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
INTER = "/usr/share/fonts/opentype/inter/Inter-%s.otf"
import os
ML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "ml-%s.ttf")

def f(path, size):
    return ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)

def is_ml(c):
    return '\u0d00' <= c <= '\u0d7f' or c in '\u200c\u200d'

def runs(text):
    out = []
    for c in text:
        k = is_ml(c) or (c == ' ' and out and out[-1][0])
        if out and out[-1][0] == k: out[-1][1] += c
        else: out.append([k, c])
    return out

def mlen(draw, text, font):
    if not hasattr(font, "latin"): return draw.textlength(text, font=font)
    return sum(draw.textlength(t, font=font if k else font.latin) for k, t in runs(text))

def mtext(draw, xy, text, font, fill):
    if not hasattr(font, "latin"): return draw.text(xy, text, font=font, fill=fill)
    x, y = xy
    for k, t in runs(text):
        fo = font if k else font.latin
        draw.text((x, y if k else y + int(font.size * 0.08)), t, font=fo, fill=fill)
        x += draw.textlength(t, font=fo)

def mlf(weight, size):
    fo = f(ML % weight, size)
    fo.latin = f(INTER % ("Bold" if weight == "700" else "Regular"), int(size * 0.92))
    return fo

def wrap(draw, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if mlen(draw, t, font) <= maxw:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def card(d, out):
    accent = tuple(d.get("accent", (16, 185, 129)))
    img = Image.new("RGB", (W, H), (12, 18, 32))
    dr = ImageDraw.Draw(img)
    # top band
    dr.rectangle([0, 0, W, 14], fill=accent)
    M = 80
    y = 90
    tag = f(INTER % "Bold", 30)
    tw = dr.textlength(d["tag"], font=tag)
    dr.rounded_rectangle([M, y, M + tw + 44, y + 58], 29, fill=accent)
    dr.text((M + 22, y + 11), d["tag"], font=tag, fill=(12, 18, 32))
    dr.text((W - M, y + 14), d["date"], font=f(INTER % "Medium", 28), fill=(148, 163, 184), anchor="ra")
    y += 110
    for size_key, key, font, color, gap in [
        (None, "headline", f(INTER % "Bold", 62), (255, 255, 255), 10),
        (None, "summary", f(INTER % "Regular", 32), (203, 213, 225), 14),
    ]:
        for ln in wrap(dr, d[key], font, W - 2 * M):
            dr.text((M, y), ln, font=font, fill=color)
            y += font.size + gap
        y += 22 if key == "headline" else 6
    dr.line([M, y, W - M, y], fill=(51, 65, 85), width=2)
    y += 34
    for key, font, color, gap in [
        ("ml_headline", mlf("700", 46), (255, 255, 255), 22),
        ("ml_summary", mlf("400", 30), (203, 213, 225), 18),
    ]:
        for ln in wrap(dr, d[key], font, W - 2 * M):
            mtext(dr, (M, y), ln, font, color)
            y += font.size + gap
        y += 18
    if d.get("tip"):
        y += 10
        tf, mf = f(INTER % "SemiBold", 30), mlf("700", 28)
        tl = wrap(dr, d["tip"], tf, W - 2 * M - 60)
        ml = wrap(dr, d["ml_tip"], mf, W - 2 * M - 60)
        bh = len(tl) * 42 + len(ml) * 50 + 56
        assert y + bh < H - 130, "content overflows card"
        dr.rounded_rectangle([M, y, W - M, y + bh], 22, fill=(22, 33, 55), outline=accent, width=3)
        yy = y + 24
        for ln in tl:
            dr.text((M + 30, yy), ln, font=tf, fill=accent); yy += 42
        for ln in ml:
            mtext(dr, (M + 30, yy), ln, mf, (226, 232, 240)); yy += 50
    # footer
    dr.rectangle([0, H - 120, W, H], fill=(8, 12, 22))
    dr.text((M, H - 92), d["handle"], font=f(INTER % "Bold", 30), fill=(255, 255, 255))
    dr.text((M, H - 52), "Source: " + d["source"], font=f(INTER % "Regular", 22), fill=(148, 163, 184))
    img.save(out, "JPEG", quality=92)

if __name__ == "__main__":
    card(json.load(open(sys.argv[1])), sys.argv[2])
