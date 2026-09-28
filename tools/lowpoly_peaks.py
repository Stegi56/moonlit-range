#!/usr/bin/env python3
"""Sharp low-poly mountain wallpapers in stegi56.com-derived palettes.

Usage: lowpoly_peaks.py <palette> [seed] > out.svg
Palettes are built with Adobe Color harmony rules around the site's violet
(#7e6fff, H247) and blue (#3b82f6, H217): analogous, monochromatic,
complementary.
"""
import bisect
import colorsys
import math
import random
import sys

W, H = 3840, 2160


def hsl(h, s, l):
    r, g, b = colorsys.hls_to_rgb((h % 360) / 360, l / 100, s / 100)
    return (r * 255, g * 255, b * 255)


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def hexc(c):
    return "#%02x%02x%02x" % tuple(int(round(max(0, min(255, v)))) for v in c)


# Each palette: sky gradient (top, mid, horizon), a glow, four mountain layers
# as (lit, shadow) pairs from far to near, snow (lit, shadow), and star/moon.
PALETTES = {
    # Analogous: blue H217 -> violet H247 -> purple H277, with an H300 glow.
    "analogous": {
        "sky": [hsl(247, 30, 5), hsl(255, 38, 13), hsl(277, 42, 30)],
        "glow": (hsl(300, 65, 62), 0.55, (0.64, 0.60)),
        "layers": [
            (hsl(272, 38, 44), hsl(262, 34, 30)),
            (hsl(252, 40, 38), hsl(247, 36, 20)),
            (hsl(230, 52, 52), hsl(247, 40, 13)),
            (hsl(247, 30, 14), hsl(240, 30, 6)),
        ],
        "snow": (hsl(250, 100, 93), hsl(262, 45, 62)),
        "stars": 190,
        "moon": None,
    },
    # Monochromatic: everything on the site blue, H217, varying S and L.
    "monochromatic": {
        "sky": [hsl(217, 40, 4), hsl(217, 50, 11), hsl(217, 55, 26)],
        "glow": (hsl(217, 90, 70), 0.40, (0.53, 0.20)),
        "layers": [
            (hsl(217, 45, 44), hsl(217, 38, 30)),
            (hsl(217, 50, 36), hsl(217, 42, 19)),
            (hsl(217, 70, 60), hsl(217, 50, 12)),
            (hsl(217, 38, 13), hsl(217, 40, 5)),
        ],
        "snow": (hsl(214, 100, 95), hsl(217, 55, 64)),
        "stars": 230,
        "moon": (0.53, 0.13, hsl(214, 100, 94)),
    },
    # Complementary: violet H247 dominant, its complement (warm amber, H38 on
    # the RYB wheel Adobe Color uses) as a sparing horizon and rim accent.
    "complementary": {
        "sky": [hsl(247, 35, 5), hsl(250, 40, 14), hsl(262, 38, 30)],
        "glow": (hsl(32, 95, 62), 0.70, (0.50, 0.44)),
        "layers": [
            (hsl(285, 30, 46), hsl(258, 32, 30)),
            (hsl(262, 34, 36), hsl(250, 38, 19)),
            (hsl(247, 62, 64), hsl(250, 42, 12)),
            (hsl(250, 32, 13), hsl(247, 34, 5)),
        ],
        "snow": (hsl(38, 100, 88), hsl(252, 45, 60)),
        "stars": 150,
        "moon": None,
        "rim": hsl(35, 95, 66),
    },
}


# --- geometry -----------------------------------------------------------------

def delaunay(pts):
    """Bowyer-Watson triangulation. Returns index triples into pts."""
    minx = min(p[0] for p in pts); maxx = max(p[0] for p in pts)
    miny = min(p[1] for p in pts); maxy = max(p[1] for p in pts)
    d = max(maxx - minx, maxy - miny) * 20
    mx, my = (minx + maxx) / 2, (miny + maxy) / 2
    P = list(pts) + [(mx - d, my - d), (mx + d, my - d), (mx, my + d)]
    n = len(pts)

    def circ(i, j, k):
        ax, ay = P[i]; bx, by = P[j]; cx, cy = P[k]
        dd = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
        if abs(dd) < 1e-12:
            return (0, 0, float("inf"))
        ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / dd
        uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / dd
        return (ux, uy, (ax - ux) ** 2 + (ay - uy) ** 2)

    tris = {(n, n + 1, n + 2): circ(n, n + 1, n + 2)}
    order = sorted(range(n), key=lambda i: (P[i][0], P[i][1]))
    for i in order:
        px, py = P[i]
        bad = [t for t, (ux, uy, r2) in tris.items() if (px - ux) ** 2 + (py - uy) ** 2 < r2]
        edges = {}
        for t in bad:
            for e in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                k = (min(e), max(e))
                edges[k] = edges.get(k, 0) + 1
            del tris[t]
        for (a, b), c in edges.items():
            if c == 1:
                tris[(a, b, i)] = circ(a, b, i)
    return [t for t in tris if max(t) < n]


class Ridge:
    """A jagged skyline whose peak apexes are exact polyline vertices."""

    def __init__(self, keys, levels, rough):
        pts = keys
        for lvl in range(levels):
            out = [pts[0]]
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                mx = (x0 + x1) / 2 + random.uniform(-0.12, 0.12) * (x1 - x0)
                seg = math.hypot(x1 - x0, y1 - y0)
                my = (y0 + y1) / 2 + random.uniform(-1, 1) * seg * rough / (1.5 ** lvl)
                # never rise above the higher endpoint, so apexes stay sharp
                my = max(my, min(y0, y1) + 4)
                out += [(mx, my), (x1, y1)]
            pts = out
        self.pts = pts
        self.xs = [p[0] for p in pts]

    def __call__(self, x):
        i = bisect.bisect_right(self.xs, x)
        if i <= 0:
            return self.pts[0][1]
        if i >= len(self.pts):
            return self.pts[-1][1]
        (x0, y0), (x1, y1) = self.pts[i - 1], self.pts[i]
        return y0 + (y1 - y0) * (x - x0) / ((x1 - x0) or 1)


def skyline(peaks, base, jag, saddle=(0.35, 0.7)):
    """peaks: list of (x, y). Saddles are dropped between neighbours."""
    peaks = sorted(peaks)
    keys = [(-80, base + random.uniform(-40, 40))]
    for idx, (px, py) in enumerate(peaks):
        if idx:
            qx, qy = peaks[idx - 1]
            sx = qx + (px - qx) * random.uniform(0.4, 0.6)
            sy = max(qy, py) + (base - max(qy, py)) * random.uniform(*saddle)
            keys.append((sx, sy))
        keys.append((px, py))
    keys.append((W + 80, base + random.uniform(-40, 40)))
    return Ridge(keys, 3, jag)


def scatter(ridge, spacing_top, spacing_bot, tries):
    """Blue-noise points under a ridge, denser near the crest."""
    pts = []
    cell = spacing_top * 0.7
    grid = {}

    def ok(x, y, r):
        gx, gy = int(x // cell), int(y // cell)
        span = int(r // cell) + 1
        for ix in range(gx - span, gx + span + 1):
            for iy in range(gy - span, gy + span + 1):
                for qx, qy in grid.get((ix, iy), ()):
                    if (qx - x) ** 2 + (qy - y) ** 2 < r * r:
                        return False
        return True

    def add(x, y):
        pts.append((x, y))
        grid.setdefault((int(x // cell), int(y // cell)), []).append((x, y))

    for p in ridge.pts:
        add(*p)
    for i in range(12):
        add(-80 + (W + 160) * i / 11, H + 60)
    for _ in range(tries):
        x = random.uniform(-80, W + 80)
        top = ridge(x)
        u = random.random() ** 1.5
        y = top + (H + 60 - top) * u
        r = spacing_top + (spacing_bot - spacing_top) * u
        if y - top < r * 0.55 or not ok(x, y, r):
            continue
        add(x, y)
    return pts


# --- rendering ----------------------------------------------------------------

def poly(pts, col):
    c = hexc(col)
    p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return f'<polygon points="{p}" fill="{c}" stroke="{c}" stroke-width="1.5" stroke-linejoin="round"/>'


def mountain_layer(peaks, base, jag, lit, shadow, spacing, haze, pal, snow=0.0, rim=0.0, saddle=(0.35, 0.7)):
    ridge = skyline(peaks, base, jag, saddle)
    pts = scatter(ridge, spacing[0], spacing[1], 9000)
    tris = delaunay(pts)
    peaks = sorted(peaks)
    spines = [(px, py, random.uniform(-0.28, 0.22)) for px, py in peaks]
    horizon = pal["sky"][2]
    out = [poly(ridge.pts + [(W + 80, H + 80), (-80, H + 80)], mix(shadow, horizon, haze))]
    for t in tris:
        (x1, y1), (x2, y2), (x3, y3) = (pts[i] for i in t)
        cx, cy = (x1 + x2 + x3) / 3, (y1 + y2 + y3) / 3
        # drop triangles poking above the skyline
        if any(ridge(mx) - my > 2 for mx, my in (
                (cx, cy), ((x1 + x2) / 2, (y1 + y2) / 2), ((x2 + x3) / 2, (y2 + y3) / 2), ((x3 + x1) / 2, (y3 + y1) / 2))):
            continue
        top = ridge(cx)
        depth = (cy - top) / max(1, H - top)
        # which peak owns this facet, and which side of its spine it sits on
        px, py, slant = min(spines, key=lambda s: abs(cx - (s[0] + (cy - s[1]) * s[2])) * (1 + 0.0006 * max(0, s[1] - top)))
        spine = px + (cy - py) * slant
        side = 1.0 if cx < spine else 0.0
        # soften toward the base of the mountain, jitter every facet
        light = side * (0.78 + random.uniform(-0.14, 0.14)) + (1 - side) * (0.16 + random.uniform(-0.1, 0.12))
        light *= 1 - min(1, depth * 1.25) * 0.55
        col = mix(shadow, lit, light)
        if rim and side and depth < 0.10:
            col = mix(col, pal["rim"], rim * (1 - depth / 0.10) * random.uniform(0.5, 1))
        if snow:
            prominence = base - py
            cap = prominence * 0.24 * random.uniform(0.8, 1.15)
            if cy - py < cap * snow and py < H * 0.5 and abs(cx - px) < (cy - py) * 0.9 + 30:
                s_lit, s_sh = pal["snow"]
                col = mix(s_sh, s_lit, (0.85 + random.uniform(-0.1, 0.1)) if side else random.uniform(0.05, 0.3))
        col = mix(col, horizon, haze * (1 - depth * 0.6))
        out.append(poly([(x1, y1), (x2, y2), (x3, y3)], col))
    return out


def sky(pal):
    pts = [(random.uniform(-80, W + 80), random.uniform(-80, H * 0.8)) for _ in range(260)]
    for i in range(9):
        pts += [(-80 + (W + 160) * i / 8, -80), (-80 + (W + 160) * i / 8, H * 0.8)]
    top, mid, hor = pal["sky"]
    gcol, gstr, (gx, gy) = pal["glow"]
    out = []
    for t in delaunay(pts):
        tri = [pts[i] for i in t]
        cx = sum(p[0] for p in tri) / 3
        cy = sum(p[1] for p in tri) / 3
        v = max(0, cy) / (H * 0.72)
        col = mix(top, mid, v * 1.6) if v < 0.62 else mix(mid, hor, (v - 0.62) / 0.38)
        g = math.exp(-(((cx - W * gx) / (W * 0.30)) ** 2 + ((cy - H * gy) / (H * 0.26)) ** 2))
        col = mix(col, gcol, g * gstr)
        col = mix(col, top, random.uniform(0, 0.10))
        out.append(poly(tri, col))
    return out


def stars(n, moon):
    out = []
    for _ in range(n):
        x, y = random.uniform(0, W), random.uniform(0, H * 0.5) ** 1.1 / (H * 0.5) ** 0.1
        r = random.choice([1.3, 1.6, 2.0, 2.0, 2.6, 3.4])
        o = random.uniform(0.3, 0.9) * max(0, 1 - y / (H * 0.52))
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#e9ecf1" opacity="{o:.2f}"/>')
    if moon:
        mx, my, mc = moon
        cx, cy, r = W * mx, H * my, 88
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{r * 3.2}" fill="{hexc(mc)}" opacity="0.06"/>')
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{r * 1.8}" fill="{hexc(mc)}" opacity="0.08"/>')
        # faceted moon
        ring = [(cx + r * math.cos(a), cy + r * math.sin(a)) for a in [k * math.tau / 11 for k in range(11)]]
        for k in range(11):
            f = 0.85 + 0.15 * math.cos(k * math.tau / 11 + 2.4)
            out.append(poly([(cx, cy), ring[k], ring[(k + 1) % 11]], mix((150, 170, 210), mc, f)))
    return out


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "analogous"
    random.seed(int(sys.argv[2]) if len(sys.argv) > 2 else 56)
    pal = PALETTES[name]
    L = pal["layers"]
    rim = 0.55 if "rim" in pal else 0.0
    parts = sky(pal) + stars(pal["stars"], pal["moon"])

    def spread(n, lo, hi, ylo, yhi):
        xs = [(k + random.uniform(0.15, 0.85)) * (W / n) for k in range(n)]
        return [(x, H * random.uniform(ylo, yhi)) for x in xs]

    parts += mountain_layer(spread(7, 0, 1, 0.24, 0.38), H * 0.64, 0.22, *L[0], (120, 260), 0.5, pal, rim=rim * 0.3)
    parts += mountain_layer(spread(5, 0, 1, 0.32, 0.46), H * 0.74, 0.22, *L[1], (110, 260), 0.26, pal, rim=rim * 0.6, snow=0.35)
    hero = [(W * 0.06, H * 0.46), (W * 0.30, H * 0.22), (W * 0.47, H * 0.40),
            (W * 0.68, H * 0.17), (W * 0.94, H * 0.38)]
    hero = [(x + random.uniform(-90, 90), y + random.uniform(-40, 40)) for x, y in hero]
    parts += mountain_layer(hero, H * 0.90, 0.20, *L[2], (95, 300), 0.0, pal, snow=1.0, rim=rim, saddle=(0.25, 0.5))
    parts += mountain_layer(spread(5, 0, 1, 0.78, 0.86), H * 0.97, 0.18, *L[3], (140, 320), 0.0, pal)

    print(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
    print(f'<rect width="{W}" height="{H}" fill="{hexc(pal["sky"][0])}"/>')
    print("\n".join(parts))
    print("</svg>")


if __name__ == "__main__":
    main()
