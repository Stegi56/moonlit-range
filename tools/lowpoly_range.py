#!/usr/bin/env python3
"""Moonlit low-poly mountain range, monochromatic on the stegi56.com blue (H217).

Usage: lowpoly_range.py [seed] > out.svg

Built the way low-poly illustrators draw mountains: a broad triangular
silhouette, facet lines running from the peak and ridge down to the base, and
a spine splitting each mountain into a lit and a shadowed side. Each mountain
is a small 3D tent mesh lit from the moon's side, so facets shade naturally.
"""
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


HUE = 217
SKY = [hsl(HUE, 40, 4), hsl(HUE, 50, 11), hsl(HUE, 52, 24)]
MOON = hsl(214, 100, 94)
# Per range, far to near: (shadow, lit, snow shadow, snow lit, haze)
RANGES = [
    (hsl(HUE, 36, 22), hsl(HUE, 42, 40), hsl(HUE, 40, 46), hsl(HUE, 70, 72), 0.45),
    (hsl(HUE, 42, 15), hsl(HUE, 50, 42), hsl(HUE, 48, 50), hsl(HUE, 85, 82), 0.22),
    (hsl(HUE, 50, 9), hsl(HUE, 62, 50), hsl(HUE, 55, 58), hsl(214, 100, 95), 0.0),
]
FG = (hsl(HUE, 40, 5), hsl(HUE, 40, 10))

LIGHT = (-0.72, -0.42, 0.56)  # from the upper left, where the moon sits
_n = math.sqrt(sum(v * v for v in LIGHT))
LIGHT = tuple(v / _n for v in LIGHT)


def poly(pts, col):
    c = hexc(col)
    p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return f'<polygon points="{p}" fill="{c}" stroke="{c}" stroke-width="1.6" stroke-linejoin="round"/>'


def strip(a, b):
    """Triangulate between two left-to-right vertex rows (indices)."""
    tris, i, j = [], 0, 0
    while i < len(a) - 1 or j < len(b) - 1:
        if j >= len(b) - 1 or (i < len(a) - 1 and a[i + 1][1] <= b[j + 1][1]):
            tris.append((a[i][0], a[i + 1][0], b[j][0])); i += 1
        else:
            tris.append((a[i][0], b[j + 1][0], b[j][0])); j += 1
    return tris


def mountain(ax, ay, base_y, slope_l, slope_r, rows, detail, rng):
    """Return (verts, tris) for one mountain. verts: (x, y, z, t)."""
    h = base_y - ay
    wl = h / math.tan(math.radians(slope_l))
    wr = h / math.tan(math.radians(slope_r))
    drift = (wr - wl) * 0.18 + rng.uniform(-0.08, 0.08) * h
    shoulder_l, shoulder_r = rng.uniform(-0.12, 0.12), rng.uniform(-0.12, 0.12)
    sub_l, sub_r = rng.uniform(0.35, 0.65), rng.uniform(0.35, 0.65)
    depth = 0.55 * h

    verts = [(ax, ay, depth * 0.35, 0.0, 1.0)]
    row_idx = [[(0, ax)]]
    for k in range(1, rows + 1):
        t = (k / rows) ** 1.35
        t = min(1.0, t + (rng.uniform(-0.25, 0.25) / rows if k < rows else 0))
        y = ay + h * t
        xl = ax - wl * t * (1 + shoulder_l * math.sin(math.pi * t)) + rng.uniform(-0.03, 0.03) * wl * t
        xr = ax + wr * t * (1 + shoulder_r * math.sin(math.pi * t)) + rng.uniform(-0.03, 0.03) * wr * t
        xs = ax + drift * t
        nl = max(1, round(detail * k * 0.9))
        nr = max(1, round(detail * k * 0.9))
        row = []
        for side, (x0, x1, n, sub) in enumerate(((xl, xs, nl, sub_l), (xs, xr, nr, sub_r))):
            for m in range(n + (1 if side else 0)):
                if side == 0 and m == n:
                    continue
                u = m / n if side == 0 else m / n  # 0..1 along the side
                jitter = 0 if m in (0, n) else rng.uniform(-0.3, 0.3) / n
                uu = min(1, max(0, u + jitter))
                x = x0 + (x1 - x0) * uu
                yy = y + (0 if m in (0, n) else rng.uniform(-0.45, 0.45) * h / rows)
                # distance toward the spine: 0 at silhouette, 1 on the spine
                s = uu if side == 0 else 1 - uu
                ridge = s ** 0.85 + 0.22 * math.exp(-((s - sub) / 0.12) ** 2)
                z = depth * t * ridge + depth * 0.35 * (1 - t) + rng.uniform(-0.05, 0.05) * depth * t
                verts.append((x, yy, z, t, s))
                row.append((len(verts) - 1, x))
        row_idx.append(row)
    tris = []
    for a, b in zip(row_idx, row_idx[1:]):
        tris += strip(a, b)
    return verts, tris


def shade(v1, v2, v3):
    ux, uy, uz = v2[0] - v1[0], v2[1] - v1[1], v2[2] - v1[2]
    vx, vy, vz = v3[0] - v1[0], v3[1] - v1[1], v3[2] - v1[2]
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    n = math.sqrt(nx * nx + ny * ny + nz * nz) or 1
    nx, ny, nz = nx / n, ny / n, nz / n
    if nz < 0:
        nx, ny, nz = -nx, -ny, -nz
    return max(0.0, nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2])


def draw_mountain(spec, colours, rng, snow_line):
    shadow, lit, s_sh, s_lit, haze = colours
    verts, tris = mountain(*spec, rng)
    out = []
    phase = rng.uniform(0, 6)
    for t in tris:
        v1, v2, v3 = (verts[i] for i in t)
        b = shade(v1, v2, v3)
        b = max(0, min(1, (b - 0.25) / 0.7)) ** 1.1
        tc = (v1[3] + v2[3] + v3[3]) / 3
        cx = (v1[0] + v2[0] + v3[0]) / 3
        sc = (v1[4] + v2[4] + v3[4]) / 3  # 1 on the spine, 0 at the silhouette
        jag = snow_line * (0.55 + 0.95 * sc ** 1.5) + 0.04 * math.sin(cx / 90 + phase) + rng.uniform(-0.04, 0.04)
        if snow_line and tc < jag:
            col = mix(s_sh, s_lit, b)
        else:
            col = mix(shadow, lit, b)
            col = mix(col, shadow, max(0, tc - 0.4) * 1.2)  # darker toward the base
        col = mix(col, SKY[2], haze * (0.6 + 0.4 * tc))
        out.append(poly([(v[0], v[1]) for v in (v1, v2, v3)], col))
    return out


def sky(rng):
    pts = []
    cols, rows = 16, 7
    for j in range(rows + 1):
        for i in range(cols + 1):
            x = (-0.03 + 1.06 * i / cols) * W + (0 if i in (0, cols) else rng.uniform(-0.35, 0.35) * W / cols)
            y = (-0.03 + 0.8 * j / rows) * H + (0 if j in (0, rows) else rng.uniform(-0.35, 0.35) * H / rows)
            pts.append((x, y))
    out = []
    mx, my = W * 0.24, H * 0.17
    for j in range(rows):
        for i in range(cols):
            a, b = pts[j * (cols + 1) + i], pts[j * (cols + 1) + i + 1]
            c, d = pts[(j + 1) * (cols + 1) + i], pts[(j + 1) * (cols + 1) + i + 1]
            for tri in ([(a, b, d), (a, d, c)] if rng.random() < 0.5 else [(a, b, c), (b, d, c)]):
                cx = sum(p[0] for p in tri) / 3
                cy = sum(p[1] for p in tri) / 3
                v = max(0, cy) / (H * 0.75)
                col = mix(SKY[0], SKY[1], v * 1.5) if v < 0.66 else mix(SKY[1], SKY[2], (v - 0.66) / 0.34)
                g = math.exp(-(((cx - mx) / (W * 0.22)) ** 2 + ((cy - my) / (H * 0.30)) ** 2))
                col = mix(col, hsl(HUE, 70, 55), g * 0.28)
                col = mix(col, SKY[0], rng.uniform(0, 0.08))
                out.append(poly(tri, col))
    return out


def stars_and_moon(rng):
    out = []
    for _ in range(240):
        x, y = rng.uniform(0, W), H * 0.55 * rng.random() ** 1.4
        r = rng.choice([1.3, 1.6, 2.0, 2.0, 2.6, 3.4])
        o = rng.uniform(0.3, 0.9) * max(0, 1 - y / (H * 0.56))
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#e9ecf1" opacity="{o:.2f}"/>')
    cx, cy, r = W * 0.24, H * 0.17, 86
    for k, o in ((3.4, 0.05), (2.2, 0.07), (1.5, 0.09)):
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{r * k}" fill="{hexc(MOON)}" opacity="{o}"/>')
    n = 12
    ring = [(cx + r * math.cos(a), cy + r * math.sin(a)) for a in [k * math.tau / n + 0.2 for k in range(n)]]
    inner = [(cx + r * 0.5 * math.cos(a), cy + r * 0.5 * math.sin(a)) for a in [k * math.tau / 6 + 0.5 for k in range(6)]]
    out.append(poly(inner, mix(MOON, hsl(HUE, 60, 80), 0.25)))
    for k in range(n):
        f = 0.5 + 0.5 * math.cos(k * math.tau / n + 2.6)
        out.append(poly([(cx, cy), ring[k], ring[(k + 1) % n]], mix(hsl(HUE, 60, 80), MOON, 0.55 + 0.45 * f)))
    return out


def foreground(rng):
    """Dark faceted hills along the bottom with a line of low-poly pines."""
    out = []
    ridge = []
    x = -60
    while x < W + 60:
        ridge.append((x, H * 0.90 + 55 * math.sin(x / 520) + 35 * math.sin(x / 210 + 1) + rng.uniform(-20, 20)))
        x += rng.uniform(120, 220)
    ridge.append((W + 60, H * 0.9))
    bottom = [(p[0] + rng.uniform(-60, 60), H + 40) for p in ridge]
    for (a, b), (c, d) in zip(zip(ridge, ridge[1:]), zip(bottom, bottom[1:])):
        out.append(poly([a, b, c], mix(FG[0], FG[1], rng.uniform(0.3, 1))))
        out.append(poly([b, d, c], mix(FG[0], FG[1], rng.uniform(0, 0.5))))

    def ground(x):
        for p, q in zip(ridge, ridge[1:]):
            if p[0] <= x <= q[0]:
                return p[1] + (q[1] - p[1]) * (x - p[0]) / (q[0] - p[0])
        return H * 0.9

    x = -20
    while x < W:
        if rng.random() < 0.72:
            th = rng.uniform(70, 190)
            gy = ground(x) + 10
            tw = th * 0.42
            lit_c = mix(FG[1], hsl(HUE, 45, 16), rng.uniform(0, 0.6))
            for tier in range(3):
                top = gy - th + tier * th * 0.26
                bot = gy - th * 0.45 + tier * th * 0.22
                half = tw * (0.55 + tier * 0.25)
                out.append(poly([(x, top), (x - half, bot), (x, bot)], lit_c))
                out.append(poly([(x, top), (x, bot), (x + half, bot)], FG[0]))
        x += rng.uniform(22, 70)
    return out


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 217
    rng = random.Random(seed)
    parts = sky(rng) + stars_and_moon(rng)

    # Far range: many broad, hazy peaks
    far = []
    x = -200
    while x < W + 200:
        far.append((x, H * rng.uniform(0.30, 0.42), H * 0.76, rng.uniform(30, 40), rng.uniform(30, 40), 5, 0.9))
        x += rng.uniform(380, 620)
    for spec in sorted(far, key=lambda s: s[1]):
        parts += draw_mountain(spec, RANGES[0], rng, 0.0)

    # Mid range
    mid = []
    x = -100
    while x < W + 200:
        mid.append((x, H * rng.uniform(0.34, 0.46), H * 0.88, rng.uniform(34, 44), rng.uniform(34, 44), 6, 1.0))
        x += rng.uniform(600, 950)
    for spec in sorted(mid, key=lambda s: s[1]):
        parts += draw_mountain(spec, RANGES[1], rng, 0.12)

    # Hero range: one dominant peak, a second summit, smaller shoulders in front
    hero = [
        (W * 0.62 + rng.uniform(-80, 80), H * 0.20, H * 1.02, rng.uniform(38, 44), rng.uniform(36, 42), 8, 1.0),
        (W * 0.33 + rng.uniform(-80, 80), H * 0.31, H * 1.02, rng.uniform(38, 44), rng.uniform(38, 46), 7, 1.0),
        (W * 0.90 + rng.uniform(-60, 60), H * 0.40, H * 1.02, rng.uniform(40, 46), rng.uniform(36, 42), 6, 1.0),
        (W * 0.08 + rng.uniform(-60, 60), H * 0.47, H * 1.02, rng.uniform(36, 42), rng.uniform(40, 46), 6, 1.0),
    ]
    snow = [0.22, 0.20, 0.17, 0.13]
    for spec, sl in zip(hero, snow):
        parts += draw_mountain(spec, RANGES[2], rng, sl)

    parts += foreground(rng)

    print(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
    print(f'<rect width="{W}" height="{H}" fill="{hexc(SKY[0])}"/>')
    print("\n".join(parts))
    print("</svg>")


if __name__ == "__main__":
    main()
