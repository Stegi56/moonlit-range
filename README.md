# Moonlit Range

An [Omarchy](https://omarchy.org/) theme built on the stegi56.com blue (H217),
sampled from a low-poly moonlit mountain range.

![preview](preview.png)

## Palette

Surfaces are a monochromatic ramp on the base blue. The ANSI colours follow a
**split-complementary** harmony: the base blue H217 against its
split-complement at H50 (firelight), with a rose red at H353 closing the warm
arc. Greens and cyans are held back in saturation so they read as cold forest
sitting behind the fire.

| | Hex | Contrast | |
|---|---|---|---|
| red | `#e37380` | 6.6:1 | embers seen through smoke |
| orange | `#f0913f` | 8.3:1 | campfire ember at its hottest |
| yellow | `#f5c452` | 12.2:1 | firelight on snow |
| green | `#62ac76` | 7.3:1 | pine ridge, behind the fire |
| cyan | `#5cb8cc` | 8.7:1 | glacier melt |
| blue | `#79b4f7` | 9.2:1 | meltwater, river under moonlight |
| magenta | `#ab8de7` | 7.3:1 | distant aurora |
| brown | `#c69265` | 7.3:1 | seasoned oak in firelight |

Contrast is measured against the background `#060a0f`. Every ANSI colour clears
the WCAG AA floor of 4.5:1; all but red clear AAA (7:1). Red is held at 6.6:1
deliberately — pushing it to AAA on a near-black background desaturates it into
salmon and loses its character.

`palette.html` is the full generated reference: every colour with its hue,
contrast grade, source note and the list of apps that consume it.

## Install

```bash
omarchy theme install https://github.com/Stegi56/moonlit-range
omarchy theme set moonlit-range
```

## Layout

```
colors.toml            the single source of truth - edit this
backgrounds/           wallpapers, 5-moonlit-range.png is the reference
palette.html           generated palette reference (tools/palette_html.py)
preview.png            theme preview
icons.theme            icon theme name
tools/                 wallpaper + palette generators
tools/jetbrains/       JetBrains theme generators (see below)
hooks/                 omarchy hooks to install
```

Everything except `colors.toml`, the backgrounds and the tools is generated.
Regenerate the palette document with:

```bash
python3 tools/palette_html.py > palette.html
```

## JetBrains integration

`tools/jetbrains/` generates a JetBrains UI theme plugin from whatever Omarchy
theme is currently active — it reads
`~/.local/state/omarchy/current/theme/colors.toml`, not this file, so it works
for any theme.

| script | output |
|---|---|
| `gen-icls.py` | `Omarchy.icls` editor colour scheme — syntax, gutter, console, diffs |
| `gen-theme.py` | `omarchy.theme.json` UI theme — toolbars, sidebars, popups, status bar |
| `build-jar.py` | runs both, packages them as `omarchy-theme.jar` |

```bash
python3 tools/jetbrains/build-jar.py
```

The JAR is written into every installed JetBrains IDE's plugin directory. To
activate it, restart the IDE and pick **Omarchy** under
Settings → Appearance & Behavior → Appearance → Theme.

Note that JetBrains loads themes at startup only, so a running IDE will not
pick up a rebuild until it is restarted.

### Keeping it in sync

Install the hook so the plugin is rebuilt whenever the Omarchy theme changes:

```bash
cp hooks/jetbrains-colors.hook ~/.config/omarchy/hooks/theme-set.d/
chmod +x ~/.config/omarchy/hooks/theme-set.d/jetbrains-colors.hook
```

## Versioning

Changes are tracked in git. Timestamped `.bak` files are gitignored — use
`git log` and `git revert` instead.
