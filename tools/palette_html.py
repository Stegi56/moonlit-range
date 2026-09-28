#!/usr/bin/env python3
"""Render colors.toml as an HTML palette sheet: palette_html.py > palette.html

Reads the theme's colors.toml (and its inline comments as notes), scans
Omarchy's themed/*.tpl templates to show which apps use each colour, and
samples the wallpaper so the palette can be checked against its source.
"""
import glob
import html
import os
import re
import subprocess
import tomllib

HERE = os.path.dirname(os.path.abspath(__file__))
THEME = os.path.dirname(HERE)
WALLPAPER = "backgrounds/5-moonlit-range.png"
OMARCHY = os.environ.get("OMARCHY_PATH", "/usr/share/omarchy")

with open(os.path.join(THEME, "colors.toml"), "rb") as f:
    C = tomllib.load(f)
with open(os.path.join(THEME, "colors.toml")) as f:
    TOML_TEXT = f.read()
NOTES = {m[1]: m[2].strip() for m in re.finditer(r'^(\w+)\s*=\s*"[^"]*"\s*#\s*(.*)$', TOML_TEXT, re.M)}

GROUPS = [
    ("Surfaces", "Backgrounds, panels, selections and borders",
     ["darker_background", "dark_background", "background", "lighter_background", "selection", "muted"]),
    ("Text", "Foreground tiers, from secondary to brightest",
     ["dark_foreground", "light_foreground", "foreground", "bright_foreground"]),
    ("Accent", "Active window borders, focus, highlights", ["accent"]),
    ("Terminal", "ANSI colours for terminals, editors and TUIs",
     ["red", "orange", "yellow", "green", "cyan", "blue", "magenta", "brown"]),
    ("Terminal bright", "Bright ANSI variants",
     ["bright_red", "bright_yellow", "bright_green", "bright_cyan", "bright_blue", "bright_magenta"]),
]
SURFACES = GROUPS[0][2]
TEXTS = GROUPS[1][2] + ["accent"]
bg, fg = C["background"], C["foreground"]


def lum(hexc):
    r, g, b = (int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def grade(r):
    return "AAA" if r >= 7 else "AA" if r >= 4.5 else "AA large" if r >= 3 else "low"


def pretty_app(tpl):
    name = os.path.basename(tpl).removesuffix(".tpl")
    name = re.sub(r"\.(toml|conf|ini|json|lua|yaml|css|theme|rgb)$", "", name)
    return {"shell": "omarchy shell", "hyprland": "hyprland", "gum_env": "gum", "t3code": "t3 code",
            "vscode-theme": "vs code", "hyprland-preview-share-picker": "share picker",
            "keyboard": "keyboard rgb"}.get(name, name)


def usage():
    used = {k: [] for k in C}
    for tpl in sorted(glob.glob(os.path.join(OMARCHY, "default/themed/*.tpl"))
                      + glob.glob(os.path.expanduser("~/.config/omarchy/themed/*.tpl"))):
        with open(tpl) as f:
            text = f.read()
        for k in C:
            if re.search(r"\{\{\s*" + k + r"(\s*\|[^}]*)?\s*\}\}", text) and pretty_app(tpl) not in used[k]:
                used[k].append(pretty_app(tpl))
    return used


def wallpaper_colours(n=12):
    try:
        out = subprocess.run(["magick", os.path.join(THEME, WALLPAPER), "-resize", "400x", "-colors", str(n),
                              "-format", "%c", "histogram:info:-"], capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return []
    rows = [(int(m[1]), "#" + m[2].lower()) for m in re.finditer(r"(\d+):.*?#([0-9A-Fa-f]{6})", out)]
    return sorted(rows, key=lambda r: lum(r[1]))


USED = usage()
DUPES = {}
for k, v in C.items():
    if isinstance(v, str) and v.startswith("#"):
        DUPES.setdefault(v.lower(), []).append(k)


def label(k):
    return k.replace("_", " ")


def swatch(key):
    v = C[key]
    text = C["darker_background"] if lum(v) > 0.3 else C["bright_foreground"]
    note = html.escape(NOTES.get(key, ""))
    if key in SURFACES:
        r = contrast(fg, v)
        cr = f"foreground on it {r:.1f}:1"
    else:
        r = contrast(v, bg)
        cr = f"{r:.1f}:1 on background"
    same = [label(o) for o in DUPES[v.lower()] if o != key]
    dupe = f'<span class="dupe" title="Identical value">= {", ".join(same)}</span>' if same else ""
    apps = USED.get(key, [])
    chips = "".join(f"<i>{html.escape(a)}</i>" for a in apps[:8])
    more = f"<i>+{len(apps) - 8}</i>" if len(apps) > 8 else ""
    return f"""
    <button class="sw" style="--c:{v};--t:{text}" data-hex="{v}" title="Click to copy {v}">
      <span class="chip"><span class="hex">{v}</span>{dupe}</span>
      <span class="meta"><b>{label(key)}</b>
        <small>{note or '&nbsp;'}</small>
        <small class="cr"><span class="g g-{grade(r).split()[0]}">{grade(r)}</span> {cr}</small>
        <span class="apps">{chips}{more or ('' if apps else '<i class=none>no app template</i>')}</span></span>
    </button>"""


def matrix():
    head = "".join(f'<th><span class="dot" style="background:{C[s]}"></span>{label(s)}</th>' for s in SURFACES)
    rows = ""
    for t in TEXTS:
        cells = ""
        for s in SURFACES:
            r = contrast(C[t], C[s])
            cells += (f'<td style="background:{C[s]};color:{C[t]}"><b>Aa</b> {r:.1f}'
                      f'<span class="g g-{grade(r).split()[0]}">{grade(r)}</span></td>')
        rows += f'<tr><th><span class="dot" style="background:{C[t]}"></span>{label(t)}</th>{cells}</tr>'
    return f'<table class="mx"><tr><th></th>{head}</tr>{rows}</table>'


def ansi_grid():
    pairs = [("red", "bright_red"), ("orange", None), ("yellow", "bright_yellow"), ("green", "bright_green"),
             ("cyan", "bright_cyan"), ("blue", "bright_blue"), ("magenta", "bright_magenta"), ("brown", None)]
    cells = ""
    for n, b in pairs:
        bb = C[b] if b else C[n]
        cells += (f'<div class="ansi"><span style="color:{C[n]}">{n}</span>'
                  f'<span style="color:{bb}">{b.replace("_", " ") if b else "—"}</span>'
                  f'<span class="blk" style="background:{C[n]}"></span><span class="blk" style="background:{bb}"></span></div>')
    return f'<div class="ansig">{cells}</div>'


def c(k):
    return C[k]


TERM = f"""
<div class="term">
  <div class="bar"><i style="background:{c('red')}"></i><i style="background:{c('yellow')}"></i><i style="background:{c('green')}"></i><span>joel@omarchy: ~/Projects</span></div>
<pre><span style="color:{c('green')}">➜</span> <span style="color:{c('cyan')}">~/Projects</span> <span style="color:{c('magenta')}">git:(</span><span style="color:{c('red')}">main</span><span style="color:{c('magenta')}">)</span> git status
On branch main
Changes not staged for commit:
  <span style="color:{c('red')}">modified:   src/app.ts</span>
  <span style="color:{c('green')}">new file:   src/theme.ts</span>

<span style="color:{c('green')}">➜</span> <span style="color:{c('cyan')}">~/Projects</span> ls
<span style="color:{c('blue')}">src/</span>  <span style="color:{c('blue')}">tests/</span>  <span style="color:{c('yellow')}">package.json</span>  README.md  <span style="color:{c('dark_foreground')}">.env</span>

<span style="color:{c('dark_foreground')}"># theme.ts</span>
<span style="color:{c('magenta')}">export const</span> <span style="color:{c('blue')}">accent</span> = <span style="color:{c('green')}">"{c('accent')}"</span>;
<span style="color:{c('magenta')}">const</span> <span style="color:{c('blue')}">peaks</span> = <span style="color:{c('orange')}">5</span>; <span style="color:{c('dark_foreground')}">// moonlit</span>
<span style="color:{c('yellow')}">warning:</span> <span style="color:{c('bright_yellow')}">snow at 2,400m</span>
<span style="color:{c('red')}">error:</span> <span style="color:{c('bright_red')}">summit not found</span>
<span style="color:{c('green')}">➜</span> <span class="cursor"> </span></pre>
</div>"""

BAR = f"""
<div class="mockbar">
  <span class="ws"><b style="color:{c('accent')}">1</b> 2 <span style="color:{c('dark_foreground')}">3 4 5</span></span>
  <span style="color:{c('foreground')}">Sunday 16:24</span>
  <span style="color:{c('light_foreground')}">  󰂯  󰕾  󰁹 82%</span>
</div>"""

UI = f"""
<div class="ui">
  {BAR}
  <div class="win">Active window · accent border</div>
  <div class="win off">Inactive window · muted border</div>
  <div class="row"><span class="btn p">Primary</span><span class="btn">Secondary</span><span class="btn ghost">Ghost</span></div>
  <div class="menu">
    <div>󰀻  Apps</div><div class="hl">󰸉  Style</div><div>  Setup</div><div style="color:{c('dark_foreground')}">  System</div>
  </div>
  <div>Plain text with a <span class="sel">selected phrase</span> and a <span style="color:var(--accent)">highlighted link</span>.</div>
  <div style="color:{c('dark_foreground')}">Secondary text for hints and timestamps.</div>
  <div class="notif"><b>Reminder</b><span style="color:{c('dark_foreground')}">Pickup Jack · in 15 min</span></div>
</div>"""

WALL = wallpaper_colours()
wall_strip = "".join(f'<i style="background:{h};flex:{max(1, n) ** 0.5:.1f}" data-hex="{h}" title="{h}"></i>'
                     for n, h in WALL)
wall_used = {v.lower() for v in C.values() if isinstance(v, str)}

CSS_VARS = ":root {\n" + "\n".join(f"  --{k.replace('_', '-')}: {v};" for k, v in C.items() if isinstance(v, str) and v.startswith("#")) + "\n}"

ramp = "".join(f'<i style="background:{C[k]}" title="{label(k)} {C[k]}"></i>' for k in
               ["darker_background", "dark_background", "background", "lighter_background", "selection", "muted",
                "accent", "dark_foreground", "light_foreground", "foreground", "bright_foreground"])

sections = "".join(
    f'<section><h2>{name}<span>{desc}</span></h2><div class="grid">{"".join(swatch(k) for k in keys)}</div></section>'
    for name, desc, keys in GROUPS)

page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Stegi56 · Moonlit Range palette</title>
<style>
  :root {{ --bg:{bg}; --fg:{fg}; --panel:{c('lighter_background')}; --edge:{c('selection')};
          --muted:{c('dark_foreground')}; --accent:{c('accent')}; --deep:{c('darker_background')}; }}
  * {{ box-sizing:border-box }}
  html {{ scroll-behavior:smooth }}
  body {{ margin:0; background:var(--bg); color:var(--fg);
         font:15px/1.5 "JetBrainsMono Nerd Font","JetBrains Mono",ui-monospace,monospace; }}
  header {{ position:relative; height:52vh; min-height:340px; overflow:hidden;
           background:url("{WALLPAPER}") center 58%/cover; }}
  header::after {{ content:""; position:absolute; inset:0;
                  background:linear-gradient(to bottom, transparent 35%, var(--bg)); }}
  header .t {{ position:absolute; left:6vw; bottom:30px; z-index:1 }}
  h1 {{ margin:0; font-size:46px; font-weight:800; letter-spacing:-.5px }}
  h1 span {{ color:var(--accent) }}
  header p {{ margin:4px 0 0; color:{c('light_foreground')} }}
  nav {{ position:sticky; top:0; z-index:5; display:flex; gap:4px; padding:10px 6vw;
        background:color-mix(in srgb, var(--bg) 85%, transparent); backdrop-filter:blur(10px);
        border-bottom:1px solid var(--edge) }}
  nav a {{ color:var(--muted); text-decoration:none; padding:4px 10px; border-radius:8px; font-size:13px }}
  nav a:hover {{ color:var(--fg); background:var(--panel) }}
  main {{ padding:18px 6vw 70px; display:grid; gap:40px }}
  main > * {{ min-width:0 }}
  .two > *, .exp > * {{ min-width:0 }}
  h2 {{ font-size:13px; text-transform:uppercase; letter-spacing:2px; color:var(--fg);
       margin:0 0 14px; border-bottom:1px solid var(--edge); padding-bottom:8px; display:flex; gap:14px; align-items:baseline }}
  h2 span {{ text-transform:none; letter-spacing:0; color:var(--muted); font-weight:400; opacity:.8 }}
  .strip {{ display:flex; height:70px; border-radius:14px; overflow:hidden; border:1px solid var(--edge) }}
  .strip i {{ flex:1; cursor:pointer; position:relative }}
  .strip i:hover {{ outline:2px solid var(--fg); outline-offset:-2px }}
  .pill {{ display:inline-flex; align-items:center; background:var(--panel); border:1px solid var(--edge); border-radius:7px; padding:1px 8px; margin:2px; font-weight:500; color:var(--fg) }}
  .caption {{ color:var(--muted); font-size:12px; margin-top:8px }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(230px,1fr)); gap:14px }}
  .sw {{ all:unset; cursor:pointer; background:var(--panel); border:1px solid var(--edge);
        border-radius:14px; overflow:hidden; display:flex; flex-direction:column;
        transition:transform .15s, border-color .15s, box-shadow .15s }}
  .sw:hover {{ transform:translateY(-3px); border-color:var(--accent); box-shadow:0 10px 30px #0008 }}
  .chip {{ background:var(--c); height:100px; display:flex; align-items:flex-end; justify-content:space-between; padding:10px 12px; gap:8px }}
  .hex {{ color:var(--t); font-weight:700 }}
  .dupe {{ white-space:nowrap; color:var(--t); font-size:11px; opacity:.8; border:1px solid currentColor; border-radius:6px; padding:0 6px }}
  .meta {{ padding:10px 12px 12px; display:grid; gap:3px }}
  .meta b {{ font-weight:600 }}
  .meta small {{ color:var(--muted); font-size:12px }}
  .g {{ font-size:10px; font-weight:700; padding:1px 5px; border-radius:5px; margin-right:4px; vertical-align:1px }}
  .g-AAA {{ background:{c('green')}; color:var(--deep) }}
  .g-AA {{ background:{c('cyan')}; color:var(--deep) }}
  .g-low {{ background:{c('red')}; color:var(--deep) }}
  .apps {{ display:flex; flex-wrap:wrap; gap:4px; margin-top:6px }}
  .apps i {{ font-style:normal; font-size:10.5px; color:{c('light_foreground')}; background:var(--bg);
            border:1px solid var(--edge); padding:0 6px; border-radius:6px }}
  .apps i.none {{ color:var(--muted); opacity:.7 }}
  .two {{ display:grid; grid-template-columns:1.2fr 1fr; gap:22px }}
  @media (max-width:1100px) {{ .two {{ grid-template-columns:1fr }} }}
  .term {{ background:var(--bg); border:2px solid var(--accent); border-radius:12px; overflow:hidden }}
  .term .bar {{ background:{c('dark_background')}; padding:9px 12px; display:flex; gap:7px; align-items:center;
               color:var(--muted); font-size:12px; border-bottom:1px solid var(--edge) }}
  .term .bar i {{ width:11px; height:11px; border-radius:50% }}
  .term .bar span {{ margin-left:8px }}
  pre {{ margin:0; padding:16px 18px; font:inherit; font-size:14px; overflow:auto }}
  .cursor {{ background:var(--fg); animation:blink 1s steps(1) infinite }}
  @keyframes blink {{ 50% {{ opacity:0 }} }}
  .ui {{ background:var(--panel); border:1px solid var(--edge); border-radius:12px; padding:18px; display:grid; gap:14px; align-content:start }}
  .mockbar {{ display:flex; justify-content:space-between; background:var(--bg); border-radius:8px; padding:6px 12px; font-size:13px }}
  .ui .row {{ display:flex; gap:10px; flex-wrap:wrap; align-items:center }}
  .btn {{ padding:8px 14px; border-radius:10px; border:1px solid var(--edge); background:{c('dark_background')}; color:var(--fg) }}
  .btn.p {{ background:var(--accent); border-color:var(--accent); color:var(--deep); font-weight:700 }}
  .btn.ghost {{ background:transparent; color:var(--accent); border-color:var(--accent) }}
  .menu {{ background:var(--bg); border:1px solid var(--edge); border-radius:10px; padding:6px; display:grid; gap:2px }}
  .menu div {{ padding:5px 10px; border-radius:7px }}
  .menu .hl {{ background:var(--edge); color:var(--accent) }}
  .sel {{ background:{c('selection')}; padding:2px 4px; border-radius:4px }}
  .win {{ border:2px solid var(--accent); border-radius:10px; padding:10px 12px; background:var(--bg) }}
  .win.off {{ border-color:{c('muted')}; color:var(--muted) }}
  .notif {{ display:grid; gap:2px; background:var(--bg); border-left:3px solid var(--accent); border-radius:8px; padding:10px 12px }}
  .mx {{ border-collapse:separate; border-spacing:4px; width:100%; font-size:13px }}
  .mx th {{ color:var(--muted); font-weight:500; text-align:left; white-space:nowrap; padding:4px 6px }}
  .mx td {{ border-radius:8px; padding:10px; white-space:nowrap; border:1px solid var(--edge) }}
  .mx td b {{ font-size:16px; margin-right:4px }}
  .mx td .g {{ margin-left:6px }}
  .dot {{ display:inline-block; width:10px; height:10px; border-radius:3px; margin-right:6px; border:1px solid var(--edge) }}
  .scroll {{ overflow-x:auto }}
  .ansig {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(150px,1fr)); gap:10px; margin-top:14px }}
  .ansi {{ display:grid; grid-template-columns:1fr 1fr; gap:4px 8px; background:var(--bg); border:1px solid var(--edge);
          border-radius:10px; padding:10px; font-size:13px }}
  .blk {{ height:8px; border-radius:3px }}
  .exp {{ display:grid; grid-template-columns:1fr 1fr; gap:16px }}
  @media (max-width:1100px) {{ .exp {{ grid-template-columns:1fr }} }}
  .code {{ position:relative; background:var(--deep); border:1px solid var(--edge); border-radius:12px }}
  .code pre {{ font-size:12.5px; max-height:420px; color:{c('light_foreground')} }}
  .code button {{ position:absolute; top:10px; right:10px; background:var(--panel); color:var(--fg);
                 border:1px solid var(--edge); border-radius:8px; padding:4px 10px; font:inherit; font-size:12px; cursor:pointer }}
  .code button:hover {{ border-color:var(--accent); color:var(--accent) }}
  .toast {{ position:fixed; bottom:22px; left:50%; transform:translateX(-50%) translateY(90px);
           background:var(--accent); color:var(--deep); padding:8px 16px; border-radius:10px;
           font-weight:700; transition:transform .2s; z-index:10 }}
  .toast.on {{ transform:translateX(-50%) translateY(0) }}
</style></head>
<body>
<header><div class="t"><h1>Stegi56 · <span>Moonlit Range</span></h1>
<p>Monochromatic on the stegi56.com blue (H217), sampled from the wallpaper · click any colour to copy it</p></div></header>
<nav><a href="#ramp">Ramp</a><a href="#wallpaper">Wallpaper</a><a href="#surfaces">Surfaces</a><a href="#text">Text</a>
<a href="#accent">Accent</a><a href="#terminal">Terminal</a><a href="#contrast">Contrast</a><a href="#use">In use</a><a href="#export">Export</a></nav>
<main>
  <section id="ramp"><h2>Ramp<span>Surfaces → accent → text</span></h2><div class="strip">{ramp}</div></section>
  <section id="wallpaper"><h2>Wallpaper source<span>{len(WALL)} dominant colours in {os.path.basename(WALLPAPER)}, dark to light, sized by coverage</span></h2>
    <div class="strip copyable">{wall_strip}</div>
    <div class="caption">Palette colours taken directly from the image: {" ".join(f"<b class='pill'><span class='dot' style='background:{h}'></span>{h}</b>" for _, h in WALL if h in wall_used) or "—"}</div></section>
  {sections.replace('<section><h2>Surfaces', '<section id="surfaces"><h2>Surfaces').replace('<section><h2>Text', '<section id="text"><h2>Text').replace('<section><h2>Accent', '<section id="accent"><h2>Accent').replace('<section><h2>Terminal<', '<section id="terminal"><h2>Terminal<')}
  <section><h2>ANSI pairs<span>Normal and bright side by side on the background</span></h2>{ansi_grid()}</section>
  <section id="contrast"><h2>Contrast<span>Every text colour on every surface · WCAG 2 ratios</span></h2><div class="scroll">{matrix()}</div></section>
  <section id="use"><h2>In use<span>How the palette reads in a terminal and the desktop</span></h2><div class="two">{TERM}{UI}</div></section>
  <section id="export"><h2>Export<span>Copy the palette out</span></h2><div class="exp">
    <div class="code"><button data-copy="toml">Copy</button><pre id="toml">{html.escape(TOML_TEXT)}</pre></div>
    <div class="code"><button data-copy="css">Copy</button><pre id="css">{html.escape(CSS_VARS)}</pre></div>
  </div></section>
</main>
<div class="toast" id="toast"></div>
<script>
  const t = document.getElementById('toast');
  const toast = m => {{ t.textContent = m; t.classList.add('on'); clearTimeout(t._h); t._h = setTimeout(() => t.classList.remove('on'), 1200); }};
  document.querySelectorAll('.sw, .strip i').forEach(b => b.onclick = () => {{
    const hex = b.dataset.hex || b.title.split(' ').pop();
    navigator.clipboard.writeText(hex); toast('Copied ' + hex);
  }});
  document.querySelectorAll('[data-copy]').forEach(b => b.onclick = () => {{
    navigator.clipboard.writeText(document.getElementById(b.dataset.copy).textContent); toast('Copied ' + b.dataset.copy);
  }});
</script>
</body></html>"""

print(page)
