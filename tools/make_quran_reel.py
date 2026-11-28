"""Qur'an Reel: Arabic ayah over an animated nature scene (1080x1920 MP4).
Usage: python3 make_quran_reel.py reel.json out.mp4
JSON keys: lines (list of Arabic lines, shown one after another), reference,
handle, scene ("sunset" | "night" | "dawn"), optional audio (path to recitation
mp3/m4a; video length follows the audio), optional seconds (default 15).
"""
import json, os, sys, subprocess, tempfile, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
AR = os.path.join(HERE, "fonts", "ar-700.ttf")
INTER = "/usr/share/fonts/opentype/inter/Inter-%s.otf"
W, H, FPS = 1080, 1920, 30

SCENES = {  # sky top, sky horizon, sun, far hills, near hills, water tint
    "sunset": ((28, 24, 64), (246, 150, 92), (255, 214, 150), (92, 52, 84), (40, 24, 46), (60, 40, 70)),
    "dawn":   ((40, 70, 120), (250, 200, 160), (255, 240, 210), (90, 110, 140), (40, 60, 80), (70, 100, 130)),
    "night":  ((6, 10, 30), (40, 50, 100), (235, 235, 220), (24, 30, 60), (10, 14, 30), (20, 26, 55)),
}

def font(path, size):
    try: return ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)
    except Exception: return ImageFont.truetype(path, size)

def ridge(seed, base, amp, n=W):
    rng = np.random.default_rng(seed)
    x = np.linspace(0, 1, n)
    y = np.zeros(n)
    for k in range(1, 6):
        y += rng.uniform(0.4, 1.0) / k * np.sin(2 * np.pi * (k * rng.uniform(0.6, 1.6) * x + rng.uniform(0, 1)))
    return base - amp * y

def background(scene):
    top, hor, sun, far, near, water = SCENES[scene]
    horizon = int(H * 0.60)
    yy = np.linspace(0, 1, horizon)[:, None, None] ** 1.3
    sky = (np.array(top) * (1 - yy) + np.array(hor) * yy).repeat(W, axis=1)
    img = np.zeros((H, W, 3)); img[:horizon] = sky
    # water: mirrored sky, darker
    refl = sky[::-1][: H - horizon] * 0.55 + np.array(water) * 0.45
    img[horizon:] = refl[: H - horizon]
    return Image.fromarray(img.clip(0, 255).astype("uint8")), horizon

def main(src, out):
    d = json.load(open(src))
    scene = d.get("scene", "sunset")
    _, _, sun, far, near, _ = SCENES[scene]
    audio = d.get("audio")
    secs = float(d.get("seconds", 15))
    if audio:
        secs = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                              "-of", "csv=p=0", audio]).decode()) + 1.0
    base, horizon = background(scene)
    # sun / moon glow
    glow = Image.new("L", (W, H), 0); g = ImageDraw.Draw(glow)
    sx, sy = W // 2, horizon - 250
    for r in range(420, 0, -6):
        g.ellipse([sx - r, sy - r, sx + r, sy + r], fill=int(110 * (1 - r / 420) ** 2))
    glow = glow.filter(ImageFilter.GaussianBlur(30))
    base = Image.composite(Image.new("RGB", (W, H), sun), base, glow)
    bd = ImageDraw.Draw(base); bd.ellipse([sx - 95, sy - 95, sx + 95, sy + 95], fill=sun)
    # stars for night
    rng = random.Random(7)
    stars = [(rng.randrange(W), rng.randrange(int(horizon * 0.8)), rng.random() * 6.28, rng.choice([1, 2, 2, 3]))
             for _ in range(160 if scene == "night" else 0)]
    # mountain layers (wider than screen for parallax)
    def layer(seed, b, amp, col):
        ys = ridge(seed, b, amp, W + 200)
        im = Image.new("RGBA", (W + 200, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
        dr.polygon([(i, ys[i]) for i in range(W + 200)] + [(W + 199, horizon), (0, horizon)], fill=col + (255,))
        refl = im.crop((0, 0, W + 200, horizon)).transpose(Image.FLIP_TOP_BOTTOM)
        r2 = Image.new("RGBA", im.size, (0, 0, 0, 0)); r2.paste(refl, (0, horizon))
        a = r2.split()[3].point(lambda v: int(v * 0.45)); r2.putalpha(a)
        return im, r2
    far_l, far_r = layer(3, horizon - 150, 70, far)
    near_l, near_r = layer(11, horizon - 40, 60, near)
    # birds
    birds = [(rng.uniform(-300, -50), rng.uniform(250, horizon - 400), rng.uniform(55, 80), rng.random() * 6.28)
             for _ in range(5)]
    af = font(AR, 92); rf = font(INTER % "SemiBold", 34); hf = font(INTER % "Bold", 34)
    lines = d["lines"]
    seg = (secs - 1.5) / len(lines)
    tmp = tempfile.mkdtemp()
    n = int(secs * FPS)
    for i in range(n):
        t = i / FPS
        fr = base.copy()
        dr = ImageDraw.Draw(fr)
        for (x, y, ph, s) in stars:
            v = int(150 + 105 * math.sin(ph + t * 2.0))
            dr.ellipse([x - s / 2, y - s / 2, x + s / 2, y + s / 2], fill=(v, v, v))
        ox_far = int(100 - 25 * t / secs); ox_near = int(100 - 70 * t / secs)
        for L, R, ox in ((far_l, far_r, ox_far), (near_l, near_r, ox_near)):
            fr.paste(L, (-ox, 0), L); fr.paste(R, (-ox, 0), R)
        # water shimmer
        for k in range(26):
            yk = horizon + 30 + k * 26
            w = 160 + 40 * math.sin(t * 1.3 + k)
            al = max(0.0, 0.55 - k * 0.02)
            x0 = sx - w / 2 + 25 * math.sin(t * 0.9 + k * 1.7)
            for xx in range(int(x0), int(x0 + w), 4):
                px = fr.getpixel((min(W - 1, max(0, xx)), yk))
                dr.line([(xx, yk), (xx + 4, yk)], width=3,
                        fill=tuple(int(p * (1 - al) + c * al) for p, c in zip(px, sun)))
        for (bx, by, sp, ph) in birds:
            x = bx + sp * t; y = by + 12 * math.sin(t * 0.8 + ph)
            f = 10 * math.sin(t * 6 + ph)
            dr.line([(x - 18, y - f), (x, y), (x + 18, y - f)], fill=(30, 20, 35), width=4)
        # text: darken band + current line fade
        k = min(int(t / seg), len(lines) - 1)
        lt = t - k * seg
        a = min(1, lt / 0.8) * (1 if k == len(lines) - 1 or lt < seg - 0.6 else max(0, (seg - lt) / 0.6))
        shade = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(shade)
        sd.rectangle([0, 560, W, 1000], fill=(0, 0, 0, 70))
        fr = Image.alpha_composite(fr.convert("RGBA"), shade.filter(ImageFilter.GaussianBlur(60)))
        txt = Image.new("RGBA", (W, H), (0, 0, 0, 0)); td = ImageDraw.Draw(txt)
        words = lines[k]
        td.text((W / 2 + 3, 783), words, font=af, fill=(0, 0, 0, int(140 * a)), anchor="mm", direction="rtl")
        td.text((W / 2, 780), words, font=af, fill=(255, 246, 222, int(255 * a)), anchor="mm", direction="rtl")
        ra = min(1, t / 1.5)
        td.text((W / 2, 930), d["reference"], font=rf, fill=(255, 230, 190, int(220 * ra)), anchor="mm")
        td.text((W / 2, H - 140), d["handle"], font=hf, fill=(255, 230, 190, int(230 * ra)), anchor="mm")
        fr = Image.alpha_composite(fr, txt).convert("RGB")
        fr.save(os.path.join(tmp, f"{i:05d}.jpg"), quality=90)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(tmp, "%05d.jpg")]
    if audio:
        cmd += ["-i", audio, "-af", "afade=t=out:st=%.2f:d=1" % (secs - 1)]
    else:
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out]
    subprocess.check_call(cmd)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
