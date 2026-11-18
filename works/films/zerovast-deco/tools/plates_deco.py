#!/usr/bin/env python3
"""Paint the art deco poster for the ZeroVast "Deco" ad.

One 1080 x 1920 poster in the 1930s airbrushed manner: a night sky, a sunburst, a full moon, a
stepped skyline with lit windows and searchlights, water that mirrors it all in ripple dashes, and
gilt ornamental lettering. Everything is sprayed through friskets by `claude-drawing-skill`'s artdeco
engine -- there is not one outline in the picture, which is exactly what makes it read as deco.

The city IS the website: each tower is one of the three kinds of work, and the tallest carries the
clock. The lettering names the studio and the address, in the voice of a 1930s poster.

Staged so the film can composite the skyline in layers (sky, burst, far city, near towers, water,
lettering) -- the camera then moves through a genuinely deep picture at six different scales.

  python3 tools/plates_deco.py --out assets/plates
"""
import argparse
import json
import pathlib
import sys

LIB = pathlib.Path("/tmp/sk/claude-drawing-skill/lib")
if not LIB.exists():
    sys.exit("claude-drawing-skill is not cloned (expected lib/ at /tmp/sk/claude-drawing-skill/lib)")
sys.path.insert(0, str(LIB))
from artdeco import ArtDeco, GOLD, IVORY                             # noqa: E402

W, H = 1080, 1920
HZ = 1240                    # the horizon row: water below, sky above

SKY = [(0, "#03071a"), (0.28, "#071228"), (0.55, "#0c1e3c"), (0.80, "#16304a"), (1, "#1d4a48")]
BODY = ("#08152c", "#14304e", "#356f86")
RIM = "#e6c479"


def paint():
    a = ArtDeco(W, H, seed=1931)
    a.sky(SKY, bottom=HZ)
    # the water is painted in a later stage, so the first stage must not leave bare paper below the
    # horizon -- an unfinished-looking pale band for the first second of the film
    a.spray(a.rect(0, HZ, W, H), "#050d1f", grain=0.25)
    a.stage("sky")

    # the burst: the whole point of the style, and the reason the sky is never empty
    a.burst(W / 2, 760, rays=34, contrast=0.085, reach=1450, colour="#cfe9d9", dark="#02061a",
            glow=0.38, phase=3.0, bottom=HZ)
    a.moon(W * 0.28, 610, 78)
    a.stage("burst")

    # searchlights raking the sky, behind the city
    for x, ang, ln in ((150, 128, 1000), (420, 104, 900), (900, 78, 950), (980, 96, 820)):
        a.searchlight(x, HZ - 150, ang, ln, spread=1.6, strength=0.16)

    # the far city: low, hazy, packed -- the depth the camera will move through
    far = [(60, 62, 190), (130, 74, 250), (196, 54, 160), (250, 86, 300), (316, 60, 210),
           (380, 70, 260), (446, 56, 180), (520, 92, 330), (600, 66, 240), (668, 78, 290),
           (740, 58, 200), (800, 88, 320), (874, 64, 230), (940, 76, 280), (1006, 60, 210)]
    for x, w, h in far:
        a.tower(x, HZ, [(w, h * 0.62), (w * 0.7, h * 0.26), (w * 0.44, h * 0.12)], far=0.74,
                flutes=3, windows=0.10, light=-1 if x < W * 0.4 else 1, ledge=2, body=BODY, rim=RIM)
    a.stage("far")

    # the near city: three towers for the three kinds of work, and the tall one with the clock
    a.tower(255, HZ, [(126, 150), (96, 74), (62, 52)], flutes=4, windows=0.42, light=-1, spire=120,
            spire_w=20, far=0.18, body=BODY, rim=RIM)
    a.tower(520, HZ, [(112, 210), (82, 84), (54, 48)], flutes=5, slits=4, light=-1, spire=64, far=0.12,
            body=BODY, rim=RIM)
    cx, top = a.tower(795, HZ, [(178, 300), (138, 120), (104, 86)], flutes=6, windows=0.46, light=1,
                      ledge=3, top_windows=False, far=0.05, body=BODY, rim=RIM)
    a.clock(cx, top + 46, 26, 10, 10)
    apex = a.crown(cx, top, 106, steps=3, body=BODY, rim=RIM, win="#f3d79a")
    a.tower(cx, apex + 3, [(7, 4)], mast=26, ledge=0, body=BODY)
    a.tower(985, HZ, [(120, 190), (86, 90)], flutes=4, windows=0.36, light=1, spire=96, spire_w=18,
            far=0.1, body=BODY, rim=RIM)
    a.stage("near")

    # the water: mirrors the sky and every window, in the ripple dashes of a lithograph
    a.water(HZ, stops=((0, "#1d4a52"), (0.32, "#102d40"), (1, "#040a1c")), reflect=0.72)
    a.stage("water")

    # a lit jetty in the foreground: the proscenium the camera can move past
    a.spray(a.poly([(0, 1818), (W, 1810), (W, H), (0, H)]), "#050d1d", grain=0.35)
    a.spray(a.rect(0, 1808, W, 1820), "#c9a95f", grain=0.15)
    a.glow(W * 0.5, 1800, 520, "#e8c886", strength=0.10, power=2.0)
    a.stage("jetty")

    # lettering: the poster's voice
    a.burst_mark = None
    a.lettering("ZERO VAST", W / 2, 250, 92, track=0.18, anchor="m", shadow=(6, 6))
    a.caption("WEBSITES BUILT TO PERFORM", W / 2, 316, 26, colour="#efdfbb", track=0.46, anchor="ms")
    a.rule(W / 2 - 250, W / 2 - 160, 300, 2, GOLD)
    a.rule(W / 2 + 160, W / 2 + 250, 300, 2, GOLD)
    a.caption("HAND-WRITTEN  ·  NO FRAMEWORK  ·  NO LOCK-IN", W / 2, 360, 15, colour="#d9c9a2",
              track=0.40, anchor="ms")
    a.lettering("ZERO-VAST.VERCEL.APP", W / 2, 1560, 34, track=0.20, anchor="m", shadow=(3, 3))
    a.caption("KHAMMAM, TELANGANA  ·  ONE POINT OF CONTACT", W / 2, 1618, 16, colour="#efdfbb",
              track=0.38, anchor="ms")
    a.border(inset=22, gap=8, width=1.8)
    a.stage("lettering")

    a.finish(paper="#efe4cc", tooth=0.03, warm=0.05, vignette=0.16)
    return a


def build(out_dir):
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    a = paint()
    meta = {}
    for name, im in a.stages:
        p = out / f"deco_{name}.jpg"
        im.save(p, quality=92, subsampling=0)
        meta[f"deco_{name}"] = {"x": 0.0, "y": 0.0, "w": float(W), "h": float(H)}
        print("wrote", p)
    (out / "plates.json").write_text(json.dumps(meta, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="assets/plates")
    build(ap.parse_args().out)
