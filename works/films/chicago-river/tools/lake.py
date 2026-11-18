"""Great Lakes rings for the map sheet, projected and cached at prep time.

Source: @geo-maps/earth-lakes-10m (Natural Earth 10m lakes, public domain), fetched with npm.
Lake Michigan, Huron, Superior and Erie are separate rings in that file, so they project straight
onto the sheet. Writes assets/prep/lakes.json; scene.py reads it.
"""
import json, pathlib, sys
sys.path.insert(0, "/tmp/cs/skills/cinematic-film/scripts")
from make_map import projector

P = pathlib.Path("/home/user/chicago")
LAKES = pathlib.Path("/tmp/atl/lk/package/map.geo.json")
FRAME = (-91.2, 36.8, -86.3, 43.5)


def build():
    sheet = json.loads((P / "assets/prep/map_mw.json").read_text())
    proj = projector(sheet["projection"])
    coords = json.loads(LAKES.read_text())["geometries"][0]["coordinates"]
    out = []
    for poly in coords:
        ring = poly[0]
        xs = [p[0] for p in ring]; ys = [p[1] for p in ring]
        if max(xs) < FRAME[0] or min(xs) > FRAME[2] or max(ys) < FRAME[1] or min(ys) > FRAME[3]:
            continue
        if (max(xs) - min(xs)) < 0.12 or (max(ys) - min(ys)) < 0.12:
            continue
        out.append([[round(x, 5), round(y, 5)] for x, y in (proj(lon, lat) for lon, lat in ring)])
    (P / "assets/prep/lakes.json").write_text(json.dumps(out))
    print("lakes:", [(len(r),) for r in out])
    return out


def lake_outer():
    p = P / "assets/prep/lakes.json"
    return json.loads(p.read_text()) if p.exists() else build()
