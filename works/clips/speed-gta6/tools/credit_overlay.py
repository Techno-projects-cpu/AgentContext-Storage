#!/usr/bin/env python3
"""Render the source-credit overlay that gets burned into every clip.

    python3 tools/credit_overlay.py [--text "..."] [--out assets/credit.png]

A 1080x1920 transparent PNG with one pill near the bottom, above the platform caption zone,
sitting over the blurred band so it stays legible on any frame. Burning it in means the credit
survives re-uploads, stitches and anyone who copies the clip without the caption text.
"""
import argparse, os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("CLIP_PACK") or os.path.dirname(HERE)
REPO = os.environ.get("CLIP_REPO") or os.path.join(ROOT, "..", "..", "..")
FONTS = os.path.join(REPO, "skills", "video-to-shorts-skill", "fonts")
W, H = 1080, 1920
BOTTOM_CLEAR = 260          # platform UI/burn-in captions live below this; stay above it
RED = (232, 49, 42, 255)
WHITE = (255, 255, 255, 255)
GREY = (214, 210, 200, 255)
INK = (10, 10, 12, 176)


def font(size, bold=True):
    for name in (("Poppins-ExtraBold.ttf", "Poppins-Bold.ttf") if bold else ("Poppins-Bold.ttf",)):
        p = os.path.join(FONTS, name)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--who", default=os.environ.get("CREDIT_WHO", "IShowSpeed"))
    ap.add_argument("--url", default=os.environ.get("CREDIT_URL", "youtube.com/@IShowSpeed"))
    ap.add_argument("--out", default=os.path.join(ROOT, "assets", "credit.png"))
    a = ap.parse_args()

    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f1, f2 = font(38), font(26, bold=False)
    label = f"CLIP: {a.who}"
    w1 = d.textlength(label, font=f1)
    w2 = d.textlength(a.url, font=f2)
    pad_x, pad_y, gap = 30, 16, 10
    bw = int(max(w1, w2) + pad_x * 2)
    bh = int(38 + 26 + gap + pad_y * 2)
    x0 = (W - bw) // 2
    y0 = H - BOTTOM_CLEAR - bh

    d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=18, fill=INK)
    d.rectangle([x0, y0 + 14, x0 + 5, y0 + bh - 14], fill=RED)      # red rule, GTA-cover red
    d.text((x0 + pad_x, y0 + pad_y - 2), label, font=f1, fill=WHITE)
    d.text((x0 + pad_x, y0 + pad_y + 40), a.url, font=f2, fill=GREY)

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    img.save(a.out)
    print(f"{a.out}  ({bw}x{bh} pill at y={y0})")


if __name__ == "__main__":
    main()
