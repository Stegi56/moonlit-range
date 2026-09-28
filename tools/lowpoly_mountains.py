#!/usr/bin/env python3
"""Generate a low-poly mountain wallpaper (SVG) in the stegi56.com palette."""
import math
import random
import sys

W, H = 3840, 2160
SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 56
random.seed(SEED)

BG = (11, 13, 17)          # --bg #0b0d11
NAVY = (22, 35, 56)        # low-poly canvas "from"
SLATE = (45, 58, 99)       # low-poly canvas "from" (alt)
INDIGO = (70, 58, 140)     # low-poly canvas "to"
VIOLET = (126, 111, 255)   # --violet #7e6fff
LILAC = (152, 129, 252)    # brand #9881fc
BLUE = (59, 130, 246)      # --blue #3b82f6
SKYBLUE = (122, 172, 253)  # --urlColour #7aacfd


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def hexc(c):
    return "#%02x%02x%02x" % tuple(int(round(max(0, min(255, v)))) for v in c)


def ridge_fn(peaks, base, rough):
    """Ridge height (y) as a function of x, from a list of (x, y, width) peaks."""
    phase = [random.uniform(0, math.tau) for _ in range(4)]

    def f(x):
        y = base
        for px, py, pw in peaks:
            d = abs(x - px) / pw
            if d < 1:
                # sharp-ish peak profile
                y = min(y, py + (base - py) * (d ** 1.25))
        y += rough * (math.sin(x / 97 + phase[0]) + 0.5 * math.sin(x / 41 + phase[1])
                      + 0.3 * math.sin(x / 23 + phase[2]))
        return y

    return f


def layer(ridge, cols, rows, top_col, bot_col, light_strength, snow=0.0, peak_ys=None):
    """Triangulate the area under a ridge and shade each facet."""
    xs = [(-0.05 + 1.1 * i / cols) * W for i in range(cols + 1)]
    grid = []
    for j in range(rows + 1):
        v = j / rows
        row = []
        for i, x0 in enumerate(xs):
            jx = 0 if i in (0, cols) else random.uniform(-0.38, 0.38) * (W * 1.1 / cols)
            x = x0 + jx
            top = ridge(x)
            # denser near the ridge so the silhouette gets small facets
            vv = v ** 1.6
            jy = 0 if j in (0, rows) else random.uniform(-0.3, 0.3) / rows
            y = top + (H + 40 - top) * max(0.0, min(1.0, vv + jy))
            # fake height: high on the ridge, sloping down, with noise
            z = (H - y) * 0.9 + random.uniform(-40, 40)
            row.append((x, y, z))
        grid.append(row)

    lx, ly, lz = -0.55, -0.35, 0.76  # light from upper-left, towards viewer
    ln = math.sqrt(lx * lx + ly * ly + lz * lz)
    lx, ly, lz = lx / ln, ly / ln, lz / ln

    polys = []
    for j in range(rows):
        for i in range(cols):
            a, b = grid[j][i], grid[j][i + 1]
            c, d = grid[j + 1][i], grid[j + 1][i + 1]
            tris = [(a, b, d), (a, d, c)] if random.random() < 0.5 else [(a, b, c), (b, d, c)]
            for t in tris:
                (x1, y1, z1), (x2, y2, z2), (x3, y3, z3) = t
                ux, uy, uz = x2 - x1, y2 - y1, z2 - z1
                vx, vy, vz = x3 - x1, y3 - y1, z3 - z1
                nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
                n = math.sqrt(nx * nx + ny * ny + nz * nz) or 1
                nx, ny, nz = nx / n, ny / n, nz / n
                if nz < 0:
                    nx, ny, nz = -nx, -ny, -nz
                shade = nx * lx + ny * ly + nz * lz  # ~0.3 .. 1
                cy = (y1 + y2 + y3) / 3
                cx = (x1 + x2 + x3) / 3
                top_y = ridge(cx)
                depth = max(0.0, (cy - top_y) / max(1, H - top_y))  # 0 at ridge, 1 at bottom
                col = mix(top_col, bot_col, depth ** 0.7)
                # lit faces pick up violet / blue light, shadowed faces sink to navy
                lit = (shade - 0.55) * light_strength
                if lit > 0:
                    col = mix(col, mix(LILAC, SKYBLUE, cx / W), lit)
                else:
                    col = mix(col, BG, -lit * 1.2)
                if snow and peak_ys and depth < 0.12:
                    # frosted tips on the highest peaks
                    h = 1 - (top_y - min(peak_ys)) / 500
                    if h > 0.25:
                        col = mix(col, (214, 216, 255), snow * h * (1 - depth / 0.12) * max(0.3, shade))
                pts = f"{x1:.1f},{y1:.1f} {x2:.1f},{y2:.1f} {x3:.1f},{y3:.1f}"
                polys.append(f'<polygon points="{pts}" fill="{hexc(col)}" stroke="{hexc(col)}" stroke-width="1.2"/>')
    return polys


def sky():
    """Low-poly sky: faint facets over a dark-to-indigo gradient."""
    cols, rows = 22, 9
    pts = []
    for j in range(rows + 1):
        row = []
        for i in range(cols + 1):
            x = (-0.05 + 1.1 * i / cols) * W + (0 if i in (0, cols) else random.uniform(-60, 60))
            y = (-0.05 + 0.85 * j / rows) * H + (0 if j in (0, rows) else random.uniform(-50, 50))
            row.append((x, y))
        pts.append(row)
    polys = []
    glow_x, glow_y = W * 0.62, H * 0.62
    for j in range(rows):
        for i in range(cols):
            a, b, c, d = pts[j][i], pts[j][i + 1], pts[j + 1][i], pts[j + 1][i + 1]
            for t in ([(a, b, d), (a, d, c)] if (i + j) % 2 else [(a, b, c), (b, d, c)]):
                cx = sum(p[0] for p in t) / 3
                cy = sum(p[1] for p in t) / 3
                v = cy / (H * 0.8)
                col = mix(BG, NAVY, v * 1.1)
                col = mix(col, INDIGO, max(0, v - 0.45) * 1.3)
                g = math.exp(-(((cx - glow_x) / (W * 0.33)) ** 2 + ((cy - glow_y) / (H * 0.3)) ** 2))
                col = mix(col, VIOLET, g * 0.45)
                col = mix(col, BG, random.uniform(0, 0.08))
                p = " ".join(f"{x:.1f},{y:.1f}" for x, y in t)
                polys.append(f'<polygon points="{p}" fill="{hexc(col)}" stroke="{hexc(col)}" stroke-width="1.2"/>')
    return polys


def stars(n):
    out = []
    for _ in range(n):
        x, y = random.uniform(0, W), random.uniform(0, H * 0.45)
        r = random.choice([1.4, 1.8, 2.2, 3.0])
        o = random.uniform(0.25, 0.8) * (1 - y / (H * 0.5))
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#e9ecf1" opacity="{o:.2f}"/>')
    return out


def main():
    parts = []
    parts += sky()
    parts += stars(170)

    # Far range: hazy violet
    far_peaks = [(W * random.uniform(0.02, 0.98), H * random.uniform(0.40, 0.52), W * random.uniform(0.10, 0.2))
                 for _ in range(9)]
    parts += layer(ridge_fn(far_peaks, H * 0.62, 6), 34, 5, mix(INDIGO, VIOLET, 0.35), INDIGO, 0.7)

    # Mid range: slate / blue
    mid_peaks = [(W * random.uniform(0.0, 1.0), H * random.uniform(0.44, 0.58), W * random.uniform(0.12, 0.22))
                 for _ in range(7)]
    parts += layer(ridge_fn(mid_peaks, H * 0.72, 8), 30, 6, mix(SLATE, INDIGO, 0.5), SLATE, 1.0)

    # Hero range: tall peaks with frosted lilac tips
    hero_peaks = [(W * 0.30, H * 0.30, W * 0.22), (W * 0.47, H * 0.40, W * 0.14),
                  (W * 0.72, H * 0.26, W * 0.24), (W * 0.93, H * 0.44, W * 0.15),
                  (W * 0.08, H * 0.50, W * 0.14)]
    parts += layer(ridge_fn(hero_peaks, H * 0.82, 10), 28, 8, SLATE, NAVY, 1.35, snow=0.85,
                   peak_ys=[p[1] for p in hero_peaks])

    # Foreground hills: near-black
    fg_peaks = [(W * random.uniform(0.0, 1.0), H * random.uniform(0.74, 0.84), W * random.uniform(0.15, 0.3))
                for _ in range(6)]
    parts += layer(ridge_fn(fg_peaks, H * 0.92, 5), 24, 3, NAVY, BG, 0.9)

    print(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
    print(f'<rect width="{W}" height="{H}" fill="{hexc(BG)}"/>')
    print("\n".join(parts))
    print("</svg>")


if __name__ == "__main__":
    main()
