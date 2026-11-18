"""Build the regional map sheet for GeoMap from local atlas data (no network).

Writes assets/prep/map_mw.json: GeoMap's schema (regions/neighbors/dark/places/frame/projection)
plus "river_rings" (projected river bank polygons) and "lake" (Lake Michigan outline if found).
"""
import json, math, pathlib, sys
sys.path.insert(0, "/tmp/cs/skills/cinematic-film/scripts")
from make_map import projector, features, project_rings

PROJ = pathlib.Path("/home/user/chicago")
DATA = PROJ / "assets/data"
FRAME = (-91.2, 36.8, -86.3, 43.5)          # lon0, lat0, lon1, lat1
PROJSPEC = {"type": "albers", "lon0": -89.0, "lat0": 41.0, "p1": 37.0, "p2": 45.0}

states = features(json.loads((DATA / "us-states.json").read_text()), "states")
proj = projector(PROJSPEC)
regions, places = {}, {}
keep_drop = {"Alaska", "Hawaii", "Puerto Rico"}
for n, rings in states:
    if n in keep_drop:
        continue
    pr = project_rings(rings, proj, FRAME)
    if pr:
        regions[n] = pr
print("states in frame:", len(regions), sorted(regions))

# Canada / Mexico as neighbours for the edges of the sheet
world = features(json.loads((DATA / "world-countries.json").read_text()), "countries")
neigh, dark = {}, ["Canada", "Mexico"]
for n, rings in world:
    if n in dark:
        pr = project_rings(rings, proj, FRAME)
        if pr:
            neigh[n] = pr

# rivers: bank polygons from @geo-maps/earth-rivers-10m, projected and kept inside the frame
rv = json.loads(pathlib.Path("/tmp/atl/rv/package/map.geo.json").read_text())["geometries"][0]["coordinates"]
rings = []
for poly in rv:
    for ring in poly:
        xs = [p[0] for p in ring]; ys = [p[1] for p in ring]
        if max(xs) < FRAME[0] or min(xs) > FRAME[2] or max(ys) < FRAME[1] or min(ys) > FRAME[3]:
            continue
        pr = project_rings([ring], proj)
        if pr:
            r = pr[0]
            gx = max(p[0] for p in r) - min(p[0] for p in r)
            gy = max(p[1] for p in r) - min(p[1] for p in r)
            rings.append((round(max(gx, gy), 6), r))
print("river rings in frame:", len(rings))

PLACES = {"Chicago": [41.88, -87.63], "Lockport": [41.59, -88.06], "St. Louis": [38.63, -90.20],
          "Kedzie": [41.83, -87.71], "Summit": [41.79, -87.81], "Joliet": [41.53, -88.08],
          "Peoria": [40.69, -89.59], "Grafton": [38.97, -90.43], "Des Plaines": [41.28, -87.90],
          "Milwaukee": [43.04, -87.91], "Michigan City": [41.71, -86.89], "Ottawa": [41.35, -88.84],
          "Morris": [41.36, -88.42], "Havana": [40.30, -90.06], "Springfield": [39.80, -89.64], "Champaign": [40.11, -88.24], "Rockford": [42.27, -89.09],
          "Dubuque": [42.50, -90.66], "Davenport": [41.52, -90.58], "Gary": [41.59, -87.35],
          "Kenosha": [42.58, -87.82], "St. Paul": [44.95, -93.09]}
for name, (lat, lon) in PLACES.items():
    x, y = proj(lon, lat)
    places[name] = [round(x, 6), round(y, 6)]

a, b, c, d = FRAME
corners = [proj(a, b), proj(a, d), proj(c, b), proj(c, d)]
frame = [min(p[0] for p in corners), min(p[1] for p in corners), max(p[0] for p in corners), max(p[1] for p in corners)]
out = {"regions": regions, "neighbors": neigh, "dark": dark, "places": places, "frame": frame,
       "projection": PROJSPEC, "river_rings": rings}
p = PROJ / "assets/prep/map_mw.json"
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(out))
print("wrote", p, "frame", [round(v, 4) for v in frame], "size", p.stat().st_size // 1024, "KB")
