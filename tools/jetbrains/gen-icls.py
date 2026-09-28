#!/usr/bin/env python3
"""Generate a JetBrains .icls editor colour scheme from the active Omarchy theme.

Reads ~/.local/state/omarchy/current/theme/colors.toml and writes an .icls into
every ~/.config/JetBrains/<Product><version>/colors/ directory found.
"""
import glob, os, sys, tomllib

STATE = os.path.expanduser("~/.local/state/omarchy/current/theme/colors.toml")
SCHEME = "Omarchy"

with open(STATE, "rb") as f:
    C = tomllib.load(f)

def h(key):            # '#aabbcc' -> 'aabbcc'
    return C[key].lstrip("#").lower()

def mix(a, b, t):
    """Blend two theme colours; t=0 -> a, t=1 -> b."""
    A = [int(C[a].lstrip("#")[i:i+2], 16) for i in (0, 2, 4)]
    B = [int(C[b].lstrip("#")[i:i+2], 16) for i in (0, 2, 4)]
    return "%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(A, B))

COMMENT = mix("background", "dark_foreground", 0.80)   # dimmer than body text, still AAA
GUTTER  = mix("background", "lighter_background", 0.6)
LINENO  = mix("background", "dark_foreground", 0.55)

# option-name -> hex, for the <colors> block (editor chrome inside the editor)
COLORS = {
    "CARET_COLOR": h("accent"),
    "CARET_ROW_COLOR": h("lighter_background"),
    "GUTTER_BACKGROUND": h("dark_background"),
    "INDENT_GUIDE": h("selection"),
    "SELECTED_INDENT_GUIDE": h("muted"),
    "LINE_NUMBERS_COLOR": LINENO,
    "LINE_NUMBER_ON_CARET_ROW_COLOR": h("dark_foreground"),
    "SELECTION_BACKGROUND": h("selection"),
    "SELECTION_FOREGROUND": h("foreground"),
    "RIGHT_MARGIN_COLOR": h("selection"),
    "WHITESPACES": h("muted"),
    "CONSOLE_BACKGROUND_KEY": h("background"),
    "METHOD_SEPARATORS_COLOR": h("selection"),
    "VCS_ANNOTATIONS_COLOR_1": h("muted"),
    "ADDED_LINES_COLOR": h("green"),
    "MODIFIED_LINES_COLOR": h("blue"),
    "DELETED_LINES_COLOR": h("red"),
    "WHITESPACES_MODIFIED_LINES_COLOR": h("yellow"),
    "ERROR_STRIPE_COLOR": h("red"),
    "NOTIFICATION_BACKGROUND": h("lighter_background"),
    "FOLDED_TEXT_BORDER_COLOR": h("muted"),
    "TEARLINE_COLOR": h("selection"),
}

# name -> (foreground, background, font-type, effect-colour, effect-type)
# font-type: 0 normal, 1 bold, 2 italic, 3 bold-italic
A = {
    "TEXT":                        (h("foreground"), h("background"), 0),
    "DEFAULT_KEYWORD":             (h("magenta"), None, 1),
    "DEFAULT_STRING":              (h("green"), None, 0),
    "DEFAULT_VALID_STRING_ESCAPE": (h("cyan"), None, 0),
    "DEFAULT_INVALID_STRING_ESCAPE": (h("red"), None, 0),
    "DEFAULT_NUMBER":              (h("orange"), None, 0),
    "DEFAULT_CONSTANT":            (h("orange"), None, 0),
    "DEFAULT_LINE_COMMENT":        (COMMENT, None, 2),
    "DEFAULT_BLOCK_COMMENT":       (COMMENT, None, 2),
    "DEFAULT_DOC_COMMENT":         (COMMENT, None, 2),
    "DEFAULT_DOC_COMMENT_TAG":     (mix("background", "magenta", 0.75), None, 2),
    "DEFAULT_DOC_MARKUP":          (h("cyan"), None, 0),
    "DEFAULT_FUNCTION_DECLARATION": (h("blue"), None, 1),
    "DEFAULT_FUNCTION_CALL":       (h("blue"), None, 0),
    "DEFAULT_CLASS_NAME":          (h("yellow"), None, 0),
    "DEFAULT_CLASS_REFERENCE":     (h("yellow"), None, 0),
    "DEFAULT_INTERFACE_NAME":      (h("yellow"), None, 2),
    "DEFAULT_IDENTIFIER":          (h("foreground"), None, 0),
    "DEFAULT_LOCAL_VARIABLE":      (h("foreground"), None, 0),
    "DEFAULT_REASSIGNED_LOCAL_VARIABLE": (h("light_foreground"), None, 0),
    "DEFAULT_PARAMETER":           (h("brown"), None, 0),
    "DEFAULT_REASSIGNED_PARAMETER": (h("brown"), None, 2),
    "DEFAULT_INSTANCE_FIELD":      (h("cyan"), None, 0),
    "DEFAULT_STATIC_FIELD":        (h("cyan"), None, 2),
    "DEFAULT_STATIC_METHOD":       (h("blue"), None, 2),
    "DEFAULT_GLOBAL_VARIABLE":     (h("magenta"), None, 2),
    "DEFAULT_LABEL":               (h("brown"), None, 0),
    "DEFAULT_PREDEFINED_SYMBOL":   (h("cyan"), None, 0),
    "DEFAULT_METADATA":            (h("brown"), None, 0),
    "DEFAULT_OPERATION_SIGN":      (h("dark_foreground"), None, 0),
    "DEFAULT_BRACES":              (h("dark_foreground"), None, 0),
    "DEFAULT_BRACKETS":            (h("dark_foreground"), None, 0),
    "DEFAULT_PARENTHS":            (h("dark_foreground"), None, 0),
    "DEFAULT_COMMA":               (h("dark_foreground"), None, 0),
    "DEFAULT_DOT":                 (h("dark_foreground"), None, 0),
    "DEFAULT_SEMICOLON":           (h("dark_foreground"), None, 0),
    "DEFAULT_TAG":                 (h("dark_foreground"), None, 0),
    "DEFAULT_ATTRIBUTE":           (h("magenta"), None, 0),
    "DEFAULT_ENTITY":              (h("orange"), None, 0),
    "BAD_CHARACTER":               (h("red"), None, 0),
    "MATCHED_BRACE_ATTRIBUTES":    (h("accent"), h("selection"), 1),
    "UNMATCHED_BRACE_ATTRIBUTES":  (h("red"), None, 0),
    "TEXT_SEARCH_RESULT_ATTRIBUTES": (h("background"), h("yellow"), 0),
    "IDENTIFIER_UNDER_CARET_ATTRIBUTES": (None, h("selection"), 0),
    "WRITE_IDENTIFIER_UNDER_CARET_ATTRIBUTES": (None, h("muted"), 0),
    "CONSOLE_NORMAL_OUTPUT":       (h("foreground"), None, 0),
    "CONSOLE_SYSTEM_OUTPUT":       (h("dark_foreground"), None, 0),
    "CONSOLE_ERROR_OUTPUT":        (h("red"), None, 0),
    "CONSOLE_USER_INPUT":          (h("green"), None, 0),
    "CONSOLE_BLACK_OUTPUT":        (h("background"), None, 0),
    "CONSOLE_RED_OUTPUT":          (h("red"), None, 0),
    "CONSOLE_GREEN_OUTPUT":        (h("green"), None, 0),
    "CONSOLE_YELLOW_OUTPUT":       (h("yellow"), None, 0),
    "CONSOLE_BLUE_OUTPUT":         (h("blue"), None, 0),
    "CONSOLE_MAGENTA_OUTPUT":      (h("magenta"), None, 0),
    "CONSOLE_CYAN_OUTPUT":         (h("cyan"), None, 0),
    "CONSOLE_GRAY_OUTPUT":         (h("dark_foreground"), None, 0),
    "CONSOLE_DARKGRAY_OUTPUT":     (h("muted"), None, 0),
    "CONSOLE_RED_BRIGHT_OUTPUT":   (h("bright_red"), None, 0),
    "CONSOLE_GREEN_BRIGHT_OUTPUT": (h("bright_green"), None, 0),
    "CONSOLE_YELLOW_BRIGHT_OUTPUT": (h("bright_yellow"), None, 0),
    "CONSOLE_BLUE_BRIGHT_OUTPUT":  (h("bright_blue"), None, 0),
    "CONSOLE_MAGENTA_BRIGHT_OUTPUT": (h("bright_magenta"), None, 0),
    "CONSOLE_CYAN_BRIGHT_OUTPUT":  (h("bright_cyan"), None, 0),
    "CONSOLE_WHITE_OUTPUT":        (h("bright_foreground"), None, 0),
    "DIFF_INSERTED":               (None, mix("background", "green", 0.22), 0),
    "DIFF_MODIFIED":               (None, mix("background", "blue", 0.22), 0),
    "DIFF_DELETED":                (None, mix("background", "red", 0.18), 0),
    "DIFF_CONFLICT":               (None, mix("background", "yellow", 0.22), 0),
}
# effect-only attributes: (fg, bg, fonttype, effectcolor, effecttype)
EFFECTS = {
    "ERRORS_ATTRIBUTES":   (None, None, 0, h("red"), 2),
    "WARNING_ATTRIBUTES":  (None, None, 0, h("yellow"), 2),
    "WEAK_WARNING_ATTRIBUTES": (None, None, 0, h("brown"), 2),
    "INFO_ATTRIBUTES":     (None, None, 0, h("green"), 2),
    "TYPO":                (None, None, 0, h("cyan"), 2),
    "DEPRECATED_ATTRIBUTES": (None, None, 0, h("dark_foreground"), 1),
    "HYPERLINK_ATTRIBUTES": (h("accent"), None, 0, h("accent"), 1),
    "FOLLOWED_HYPERLINK_ATTRIBUTES": (h("magenta"), None, 0, h("magenta"), 1),
}

def opt(name, value):
    return f'    <option name="{name}" value="{value}" />'

def attr(name, spec):
    fg, bg, ft = spec[0], spec[1], spec[2]
    ec = spec[3] if len(spec) > 3 else None
    et = spec[4] if len(spec) > 4 else None
    lines = [f'    <option name="{name}">', '      <value>']
    if fg: lines.append(f'        <option name="FOREGROUND" value="{fg}" />')
    if bg: lines.append(f'        <option name="BACKGROUND" value="{bg}" />')
    if ec: lines.append(f'        <option name="EFFECT_COLOR" value="{ec}" />')
    if et is not None: lines.append(f'        <option name="EFFECT_TYPE" value="{et}" />')
    lines.append(f'        <option name="FONT_TYPE" value="{ft}" />')
    lines += ['      </value>', '    </option>']
    return "\n".join(lines)

body = [f'<scheme name="{SCHEME}" version="142" parent_scheme="Darcula">',
        '  <metaInfo>',
        '    <property name="created">omarchy</property>',
        f'    <property name="ide">JetBrains</property>',
        '  </metaInfo>',
        '  <colors>']
body += [opt(k, v) for k, v in COLORS.items()]
body.append('  </colors>')
body.append('  <attributes>')
body += [attr(k, v) for k, v in A.items()]
body += [attr(k, v) for k, v in EFFECTS.items()]
body.append('  </attributes>')
body.append('</scheme>')
xml = "\n".join(body) + "\n"

targets = sorted(glob.glob(os.path.expanduser("~/.config/JetBrains/*/")))
if not targets:
    print("no JetBrains config dirs found", file=sys.stderr); sys.exit(0)
for t in targets:
    d = os.path.join(t, "colors")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, f"{SCHEME}.icls")
    with open(p, "w") as f:
        f.write(xml)
    print("wrote", p)
