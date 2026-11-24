"""Turn a post JSON into a 1080x1920 Reel (MP4, ~12 s) with animated text reveal.
Usage: python3 make_reel.py post.json out.mp4
"""
import json, os, sys, subprocess, tempfile, math
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_card import card, f, INTER

W, H, FPS, SECS = 1080, 1920, 30, 12

def ease(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3

def main(src, out):
    d = json.load(open(src))
    accent = tuple(d.get("accent", (16, 185, 129)))
    tmp = tempfile.mkdtemp()
    cpath = os.path.join(tmp, "card.jpg")
    card(d, cpath)
    c = Image.open(cpath).convert("RGB")          # 1080x1350
    # split card into horizontal bands to reveal one by one
    bands = [(0, 190), (190, 560), (560, 900), (900, 1230), (1230, 1350)]
    bg = Image.new("RGB", (W, H), (12, 18, 32))
    top_pad = (H - 1350) // 2
    title = f(INTER % "Black", 56) if os.path.exists(INTER % "Black") else f(INTER % "Bold", 56)
    frames = FPS * SECS
    for i in range(frames):
        t = i / FPS
        fr = bg.copy()
        dr = ImageDraw.Draw(fr)
        # header text above the card
        a = ease(t / 0.6)
        dr.text((W // 2, int(top_pad / 2 - 40 + (1 - a) * 40)), "TODAY'S UPDATE",
                font=title, fill=tuple(int(v * a + 12 * (1 - a)) for v in accent), anchor="mm")
        # progress bar at bottom
        dr.rectangle([0, H - 12, int(W * t / SECS), H], fill=accent)
        # slow zoom
        z = 1 + 0.03 * (t / SECS)
        for k, (y0, y1) in enumerate(bands):
            start = 0.3 + k * 0.7
            p = ease((t - start) / 0.6)
            if p <= 0:
                continue
            piece = c.crop((0, y0, 1080, y1))
            if z != 1:
                piece = piece.resize((int(1080 * z), int((y1 - y0) * z)))
            px = (W - piece.width) // 2 + int((1 - p) * 120)
            py = top_pad + int(y0 * z) - int((z - 1) * 675)
            if p < 1:
                mask = Image.new("L", piece.size, int(255 * p))
                fr.paste(piece, (px, py), mask)
            else:
                fr.paste(piece, (px, py))
        fr.save(os.path.join(tmp, "f%04d.jpg" % i), quality=90)
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(tmp, "f%04d.jpg"),
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out], check=True)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
