"""Build the fine geography the showcase needs, from local data (no network).

  map_ring.json    azimuthal equidistant, centred on Krakatoa: every distance from the volcano is a
                   true radius, so the 1,000 / 3,110 / 4,830 km rings are circles on the sheet.
  map_strait.json  coasts at 10 m (Natural Earth via @geo-maps/earth-coastlines-10m), mercator,
                   for the Sunda Strait itself: the islands the 1883 eruption removed were here.
  map_world.json   the globe, equirect, thin, with the Pacific seam closed by a landmass.

Writes/overwrites assets/prep/map_<name>.json, keeping the places from map.json.
"""
import json
import math
import pathlib
import sys

sys.path.insert(0, "/tmp/cs/skills/cinematic-film/scripts")
from make_map import clip_ring, project_rings, projector

HERE = pathlib.Path(__file__).resolve().parent.parent
COASTS = pathlib.Path("/tmp/kit/cx/package/map.geo.json")
WORLD50 = HERE / "assets" / "data" / "land-50m.json"

KM = 6371.0


def aeqd(lat0, lon0):
    """Azimuthal equidistant to (lat0, lon0), in radians of arc; y down. Centre at (0, 0)."""
    r = math.radians
    p0, l0 = r(lat0), r(lon0)

    def f(lon, lat):
        p, l = r(lat), r(lon)
        c = math.acos(max(-1.0, min(1.0, math.sin(p0) * math.sin(p) + math.cos(p0) * math.cos(p) * math.cos(l - l0))))
        if c < 1e-12:
            return 0.0, 0.0
        k = c / math.sin(c)
        x = k * math.cos(p) * math.sin(l - l0)
        y = k * (math.cos(p0) * math.sin(p) - math.sin(p0) * math.cos(p) * math.cos(l - l0))
        return x, -y
    return f


def topo_rings(path, obj):
    """Rings (lon/lat) from a TopoJSON file, quantised the usual way."""
    d = json.loads(path.read_text())
    tr = d.get("transform")
    arcs = []
    for arc in d["arcs"]:
        x = y = 0; pts = []
        for p in arc:
            x += p[0]; y += p[1]
            if tr:
                pts.append((round(x * tr["scale"][0] + tr["translate"][0], 3),
                            round(y * tr["scale"][1] + tr["translate"][1], 3)))
            else:
                pts.append((round(x, 3), round(y, 3)))
        arcs.append(pts)
    out = []
    for g in d["objects"][obj]["geometries"]:
        polys = g["arcs"] if g["type"] == "MultiPolygon" else [g["arcs"]]
        for poly in polys:
            for idx in poly:
                pts = []
                for i in idx:
                    a = arcs[i] if i >= 0 else arcs[~i][::-1]
                    pts.extend(a if not pts else a[1:])
                out.append(pts)
    return out


def coast_rings():
    d = json.loads(COASTS.read_text())
    g = d["geometries"][0]
    return [[[[round(x, 4), round(y, 4)] for x, y in ring] for ring in poly] for poly in g["coordinates"]]


def add_grid(d, box, step):
    """Graticule as thin closed rings (0.006 deg wide) so it can be drawn with the region fill."""
    lon0, lat0, lon1, lat1 = box
    w = 0.006
    for lon in [x * step for x in range(int(lon0 // step) - 1, int(lon1 // step) + 2) if lon0 <= x * step <= lon1]:
        d["regions"].setdefault("_grid_lon", []).append([[lon, lat0], [lon + w, lat0], [lon + w, lat1], [lon, lat1]])
    for lat in [x * step for x in range(int(lat0 // step) - 1, int(lat1 // step) + 2) if lat0 <= x * step <= lat1]:
        d["regions"].setdefault("_grid_lat", []).append([[lon0, lat], [lon1, lat], [lon1, lat + w], [lon0, lat + w]])


def finish_at_origin(name, regions, places_latlon, places_xy, frame, box, step=None, note=""):
    """Write a sheet whose projection origin is (0, 0), with places already projected."""
    out = {"regions": regions, "neighbors": {}, "dark": [], "places": {},
           "source": "Natural Earth coastlines (public domain)", "note": note,
           "projection": {"type": "aeqd", "lon0": 105.423, "lat0": -6.102},
           "frame": [round(v, 5) for v in frame]}
    for nm, (x, y) in places_xy.items():
        out["places"][nm] = [round(x, 6), round(y, 6)]
    if step:
        add_grid(out, box, step)
    if m_note_is_aeqd(note):
        out["ring_place"] = "Krakatoa"
    p = HERE / "assets" / "prep" / f"map_{name}.json"
    p.write_text(json.dumps(out))
    print(f"map_{name}.json: {sum(len(v) for v in regions.values())} rings, {len(out['places'])} places, "
          f"frame {[round(v, 4) for v in out['frame']]}, {p.stat().st_size // 1024} KB")


def m_note_is_aeqd(note):
    return "azimuthal" in note


def finish(name, regions, proj, places, box, step=None, note=""):
    out = {"regions": regions, "neighbors": {}, "dark": [], "places": {},
           "source": "Natural Earth 10m coastlines (public domain)", "note": note}
    if m_note_is_aeqd(note):
        out["ring_place"] = "Krakatoa"
    for nm, (lat, lon) in places.items():
        x, y = proj(lon, lat)
        out["places"][nm] = [round(x, 6), round(y, 6)]
    a, b, c, e = box
    if m_note_is_aeqd(note):
        out["frame"] = list(box)
        out["projection"] = {"type": "aeqd", "lon0": 105.423, "lat0": -6.102}
    else:
        corners = [proj(a, b), proj(a, e), proj(c, b), proj(c, e)]
        out["frame"] = [min(p[0] for p in corners), min(p[1] for p in corners),
                        max(p[0] for p in corners), max(p[1] for p in corners)]
    if step:
        add_grid(out, box, step)
    p = HERE / "assets" / "prep" / f"map_{name}.json"
    p.write_text(json.dumps(out))
    print(f"map_{name}.json: {sum(len(v) for v in regions.values())} rings, {len(places)} places, "
          f"frame {[round(v, 4) for v in out['frame']]}, {p.stat().st_size // 1024} KB")


def main():
    spec = json.loads((HERE / "map.json").read_text())
    by = {m["name"]: m for m in spec["maps"]}
    rings = coast_rings()

    # ---- the strait: 10 m coasts, mercator, the water the eruption emptied
    m = by["strait"]
    proj = projector(m["projection"])
    regions = {}
    for poly in rings:
        for ring in poly:
            pts = clip_ring(ring, (104.2, -7.4, 107.0, -4.6))
            if len(pts) < 4:
                continue
            pr = project_rings([pts], proj)
            if pr:
                regions.setdefault("land", []).extend(pr)
    # the sheet is centred on the strait, so the camera sits at (0, 0) like the globe: the engine's
    # cached draw only covers the view around that point
    a, b, c, e = (104.2, -7.4, 107.0, -4.6)
    corners = [proj(a, b), proj(a, e), proj(c, b), proj(c, e)]
    fx = (min(p[0] for p in corners) + max(p[0] for p in corners)) / 2
    fy = (min(p[1] for p in corners) + max(p[1] for p in corners)) / 2
    regions = {k: [[[x - fx, y - fy] for x, y in r] for r in v] for k, v in regions.items()}
    out_places = {k: (v[0] - fx, v[1] - fy) for k, v in ((nm, proj(lon, lat)) for nm, (lat, lon) in m["places"].items())}
    finish_at_origin("strait", regions, m["places"], out_places, [cf - o for cf, o in zip([min(p[0] for p in corners), min(p[1] for p in corners),
                                                                                        max(p[0] for p in corners), max(p[1] for p in corners)], [fx, fy, fx, fy])],
                     (a, b, c, e), step=0.25)

    build_world(by["world"], topo_rings(WORLD50, "land"))

    # ---- the globe: azimuthal equidistant on Krakatoa, 50 m land, so every distance is a radius
    m = by["globe"]
    proj = aeqd(*m["places"]["Krakatoa"])
    regions = {}
    for ring in topo_rings(WORLD50, "land"):
        pts = clip_ring(ring, (0, -72, 200, 62))
        if len(pts) < 4:
            continue
        # the far side of the planet (beyond ~105 deg) folds over the antipode; keep the near half
        near = [p for p in pts if math.hypot(*proj(*p)) <= math.radians(130)]
        if len(near) > 3:
            regions.setdefault("land", []).append([[round(x, 5), round(y, 5)] for x, y in (proj(*p) for p in near)])
    finish("globe", regions, proj, m["places"], tuple(m["frame"]), step=15,
           note="azimuthal equidistant to Krakatoa; 1 unit = 6371 km (radians of arc)")


def build_world(m, rings_50m):
    """A world chart (equirect): thin 50 m land, every place the late film needs."""
    proj = projector(m["projection"])
    regions = {}
    for ring in rings_50m:
        pts = clip_ring(ring, (m["frame"][0], m["frame"][1], m["frame"][2], m["frame"][3]))
        if len(pts) < 4:
            continue
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        if max(xs) - min(xs) < 0.15 and max(ys) - min(ys) < 0.15:
            continue
        pr = project_rings([pts], proj)
        if pr:
            regions.setdefault("land", []).extend(pr)
    finish("world", regions, proj, m["places"], tuple(m["frame"]), step=20)


if __name__ == "__main__":
    main()
