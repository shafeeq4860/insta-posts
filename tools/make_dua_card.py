"""Adhkar / Dua card, 1080x1350 JPEG.  Usage: python3 make_dua_card.py dua.json out.jpg
JSON keys: tag, arabic, english, malayalam, reference, repeat (optional, e.g. "Recite 3 times"),
ml_repeat (optional), handle, accent [r,g,b] (optional)."""
import json, os, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_card import f, mlf, mtext, mlen, wrap, INTER

W, H = 1080, 1350
AR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "ar-%s.ttf")

def ar_wrap(dr, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if dr.textlength(t, font=font, direction="rtl") <= maxw: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def layout(d, ar_size, body, shift=0):
    img = Image.new("RGB", (W, H), (10, 26, 24))
    dr = ImageDraw.Draw(img)
    gold = tuple(d.get("accent", (212, 175, 55)))
    M = 80
    # frame
    dr.rounded_rectangle([30, 30, W - 30, H - 30], 36, outline=gold, width=3)
    dr.rounded_rectangle([44, 44, W - 44, H - 44], 28, outline=(40, 70, 62), width=1)
    y = 90
    tag = f(INTER % "Bold", 28)
    tw = dr.textlength(d["tag"], font=tag)
    dr.rounded_rectangle([(W - tw) / 2 - 24, y, (W + tw) / 2 + 24, y + 54], 27, fill=gold)
    dr.text((W / 2, y + 27), d["tag"], font=tag, fill=(10, 26, 24), anchor="mm")
    y += 100 + shift
    af = f(AR % "700", ar_size)
    for ln in ar_wrap(dr, d["arabic"], af, W - 2 * M - 20):
        dr.text((W / 2, y + ar_size * 0.75), ln, font=af, fill=(255, 244, 214), anchor="mm", direction="rtl")
        y += int(ar_size * 1.75)
    y += 10
    dr.line([W / 2 - 120, y, W / 2 + 120, y], fill=gold, width=2)
    dr.ellipse([W / 2 - 6, y - 6, W / 2 + 6, y + 6], fill=gold)
    y += 34
    ef = f(INTER % "Regular", body)
    for ln in wrap(dr, d["english"], ef, W - 2 * M):
        dr.text((W / 2, y), ln, font=ef, fill=(220, 230, 226), anchor="ma"); y += int(body * 1.4)
    y += 18
    mf = mlf("400", body - 2)
    for ln in wrap(dr, d["malayalam"], mf, W - 2 * M):
        mtext(dr, ((W - mlen(dr, ln, mf)) / 2, y), ln, mf, (200, 215, 210)); y += int(body * 1.65)
    y += 14
    if d.get("repeat"):
        rf = f(INTER % "SemiBold", 26)
        txt = d["repeat"] + ("  ·  " if d.get("ml_repeat") else "")
        rm = mlf("700", 24)
        total = dr.textlength(txt, font=rf) + (mlen(dr, d["ml_repeat"], rm) if d.get("ml_repeat") else 0)
        x0 = (W - total) / 2
        dr.rounded_rectangle([x0 - 22, y, x0 + total + 22, y + 50], 25, outline=gold, width=2)
        dr.text((x0, y + 11), txt, font=rf, fill=gold)
        if d.get("ml_repeat"):
            mtext(dr, (x0 + dr.textlength(txt, font=rf), y + 8), d["ml_repeat"], rm, gold)
        y += 64
    dr.text((W / 2, y + 6), d["reference"], font=f(INTER % "Medium", 24), fill=(150, 175, 168), anchor="ma")
    y += 40
    dr.text((W / 2, H - 92), d["handle"], font=f(INTER % "Bold", 28), fill=gold, anchor="mm")
    return img, y

def card(d, out):
    for ar_size, body in [(72, 34), (64, 32), (58, 30), (52, 28), (46, 26), (40, 24)]:
        img, y = layout(d, ar_size, body)
        if y < H - 130:
            img, _ = layout(d, ar_size, body, shift=max(0, int((H - 150 - y) / 2) - 20))
            img.save(out, "JPEG", quality=92); return
    raise SystemExit("content overflows card: use a shorter dua")

if __name__ == "__main__":
    card(json.load(open(sys.argv[1])), sys.argv[2])
