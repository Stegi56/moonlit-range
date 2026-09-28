#!/usr/bin/env python3
"""Generate a JetBrains UI theme (.theme.json) from the active Omarchy theme.

Reads  ~/.local/state/omarchy/current/theme/colors.toml
Writes ~/.local/share/omarchy-jetbrains/omarchy.theme.json
"""
import json
import os
import tomllib

STATE = os.path.expanduser("~/.local/state/omarchy/current/theme/colors.toml")
OUT = os.path.expanduser("~/.local/share/omarchy-jetbrains/omarchy.theme.json")

with open(STATE, "rb") as f:
    C = tomllib.load(f)


def mix(a, b, t):
    """Blend two theme colours; t=0 -> a, t=1 -> b."""
    A = [int(C[a].lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    B = [int(C[b].lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(A, B))


colors = {
    "bg": C["background"],             # editor, deepest surface
    "panel": C["dark_background"],     # tool windows, sidebars
    "chrome": C["darker_background"],  # main toolbar, title bar, status bar
    "raised": C["lighter_background"],  # popups, hovered rows
    "edge": C["selection"],
    "muted": C["muted"],
    "fg": C["foreground"],
    "dim": C["dark_foreground"],
    "accent": C["accent"],
    "hover": mix("dark_background", "lighter_background", 0.75),
    "disabled": mix("background", "dark_foreground", 0.38),
    "muted_text": mix("background", "dark_foreground", 0.72),
    "red": C["red"],
    "green": C["green"],
    "yellow": C["yellow"],
    "blue": C["blue"],
    "magenta": C["magenta"],
    "cyan": C["cyan"],
}

# Global fallback. This is the key that stops UI keys the theme does not name
# explicitly from resolving against the IDE's light defaults - the cause of the
# light-grey frame when an older theme plugin no longer maps cleanly.
WILDCARD = {
    "background": "panel",
    # Chrome text sits one tier below the editor's white: #eef5ff reads as
    # glare across large sidebar surfaces. dim (#aec6eb) is still 11.6:1.
    "foreground": "dim",
    "infoForeground": "muted_text",
    "borderColor": "edge",
    "disabledBorderColor": "edge",
    "separatorColor": "edge",
    "selectionBackground": "edge",
    "selectionForeground": "fg",
    "selectionBackgroundInactive": "edge",
    "selectionInactiveBackground": "edge",
    "disabledForeground": "disabled",
    "disabledText": "disabled",
    "acceleratorForeground": "dim",
    "inactiveForeground": "dim",
    "errorForeground": "red",
    "hoverBackground": "hover",
    "lightSelectionBackground": "edge",
    "focusColor": "accent",
    "focusedBorderColor": "accent",
    "modifiedItemForeground": "accent",
}

ui = {
    "*": WILDCARD,

    # --- main frame ---------------------------------------------------------
    "Panel.background": "panel",
    "Borders.color": "edge",
    "Borders.ContrastBorderColor": "edge",
    "Separator.separatorColor": "edge",
    "Separator.foreground": "edge",

    "MainWindow.background": "chrome",
    "MainToolbar.background": "chrome",
    "MainToolbar.inactiveBackground": "chrome",
    "MainToolbar.Dropdown.background": "chrome",
    "MainToolbar.Dropdown.hoverBackground": "hover",
    "MainToolbar.Icon.background": "chrome",
    "MainToolbar.Icon.hoverBackground": "hover",
    "MainToolbar.Icon.pressedBackground": "raised",

    "TitlePane.background": "chrome",
    "TitlePane.inactiveBackground": "chrome",
    "TitlePane.infoForeground": "dim",

    "StatusBar.background": "chrome",
    "StatusBar.borderColor": "edge",
    "StatusBar.hoverBackground": "hover",

    # --- tool windows / sidebars -------------------------------------------
    "ToolWindow.background": "panel",
    "ToolWindow.Button.hoverBackground": "hover",
    "ToolWindow.Button.selectedBackground": "edge",
    "ToolWindow.Button.selectedForeground": "fg",
    "ToolWindow.Header.background": "panel",
    "ToolWindow.Header.inactiveBackground": "panel",
    "ToolWindow.Header.borderColor": "edge",
    "ToolWindow.HeaderTab.underlinedTabBackground": "raised",
    "ToolWindow.HeaderTab.underlinedTabInactiveBackground": "panel",
    "ToolWindow.HeaderTab.hoverBackground": "hover",
    "ToolWindow.HeaderTab.underlineColor": "accent",
    "ToolWindow.HeaderTab.inactiveUnderlineColor": "muted",

    "StripeToolbar.background": "chrome",
    "SegmentedButton.selectedButtonColor": "edge",
    "SegmentedButton.focusedSelectedButtonColor": "edge",

    # --- trees, lists, tables ----------------------------------------------
    "Tree.background": "panel",
    "Tree.foreground": "dim",
    "Tree.selectionBackground": "edge",
    "Tree.selectionForeground": "fg",
    "Tree.selectionInactiveBackground": "raised",
    "Tree.hash": "edge",
    "Tree.rowHeight": 22,

    "List.background": "panel",
    "List.selectionBackground": "edge",
    "List.selectionForeground": "fg",
    "List.selectionInactiveBackground": "raised",
    "List.hoverBackground": "hover",

    "Table.background": "panel",
    "Table.gridColor": "edge",
    "Table.selectionBackground": "edge",
    "Table.stripeColor": "raised",
    "TableHeader.background": "chrome",
    "TableHeader.bottomSeparatorColor": "edge",

    # --- editor tabs --------------------------------------------------------
    "EditorTabs.background": "chrome",
    "EditorTabs.inactiveColoredFileBackground": "chrome",
    "EditorTabs.underlinedTabBackground": "bg",
    "EditorTabs.underlinedTabForeground": "fg",
    "EditorTabs.underlineColor": "accent",
    "EditorTabs.inactiveUnderlineColor": "muted",
    "EditorTabs.hoverBackground": "hover",
    "EditorTabs.borderColor": "edge",
    "EditorTabs.selectedBackground": "bg",
    "EditorTabs.selectedForeground": "fg",

    "Editor.background": "bg",
    "Editor.foreground": "fg",
    "EditorPane.background": "bg",
    "Viewport.background": "bg",
    "ScrollPane.background": "bg",

    # --- buttons ------------------------------------------------------------
    "Button.background": "raised",
    "Button.foreground": "fg",
    "Button.startBackground": "raised",
    "Button.endBackground": "raised",
    "Button.startBorderColor": "edge",
    "Button.endBorderColor": "edge",
    "Button.focusedBorderColor": "accent",
    "Button.default.startBackground": "accent",
    "Button.default.endBackground": "accent",
    "Button.default.foreground": "bg",
    "Button.default.startBorderColor": "accent",
    "Button.default.endBorderColor": "accent",
    "Button.default.focusColor": "accent",
    "Button.disabledText": "disabled",

    # --- inputs -------------------------------------------------------------
    "TextField.background": "bg",
    "TextField.foreground": "fg",
    "TextField.borderColor": "edge",
    "TextField.focusedBorderColor": "accent",
    "TextArea.background": "bg",
    "TextArea.foreground": "fg",
    "FormattedTextField.background": "bg",
    "PasswordField.background": "bg",
    "SearchField.background": "bg",
    "ComboBox.background": "bg",
    "ComboBox.nonEditableBackground": "raised",
    "ComboBox.selectionBackground": "edge",
    "ComboBox.ArrowButton.background": "raised",
    "ComboBox.ArrowButton.iconColor": "dim",
    "ComboBoxButton.background": "raised",

    "CheckBox.background": "panel",
    "RadioButton.background": "panel",

    # --- popups, menus, tooltips -------------------------------------------
    "Popup.background": "raised",
    "Popup.borderColor": "edge",
    "Popup.Header.activeBackground": "raised",
    "Popup.Header.inactiveBackground": "panel",
    "Popup.Toolbar.background": "raised",
    "Popup.separatorColor": "edge",
    "PopupMenu.background": "raised",
    "PopupMenu.borderColor": "edge",
    "MenuBar.background": "chrome",
    "Menu.background": "raised",
    "Menu.borderColor": "edge",
    "MenuItem.background": "raised",
    "MenuItem.selectionBackground": "edge",
    "MenuItem.acceleratorForeground": "dim",
    "ToolTip.background": "raised",
    "ToolTip.foreground": "fg",
    "ToolTip.borderColor": "edge",

    "CompletionPopup.background": "raised",
    "CompletionPopup.selectionBackground": "edge",
    "CompletionPopup.selectionInactiveBackground": "panel",
    "CompletionPopup.matchForeground": "accent",

    # --- notifications / validation ----------------------------------------
    "Notification.background": "raised",
    "Notification.borderColor": "edge",
    "Notification.foreground": "fg",
    "Notification.MoreButton.background": "raised",
    "Notification.ToolWindow.errorBackground": "raised",
    "Notification.ToolWindow.warningBackground": "raised",
    "Notification.ToolWindow.informativeBackground": "raised",

    "ValidationTooltip.errorBackground": "raised",
    "ValidationTooltip.errorBorderColor": "red",
    "ValidationTooltip.warningBackground": "raised",
    "ValidationTooltip.warningBorderColor": "yellow",

    # --- tabs, progress, scrollbars ----------------------------------------
    "TabbedPane.background": "panel",
    "TabbedPane.contentAreaColor": "edge",
    "TabbedPane.underlineColor": "accent",
    "TabbedPane.hoverColor": "hover",
    "TabbedPane.focusColor": "raised",

    "ProgressBar.background": "edge",
    "ProgressBar.trackColor": "edge",
    "ProgressBar.progressColor": "accent",
    "ProgressBar.indeterminateStartColor": "accent",
    "ProgressBar.indeterminateEndColor": "muted",
    "ProgressBar.failedColor": "red",
    "ProgressBar.passedColor": "green",

    "ScrollBar.background": "panel",
    "ScrollBar.thumbColor": "edge",
    "ScrollBar.thumbBorderColor": "edge",
    "ScrollBar.hoverThumbColor": "muted",
    "ScrollBar.Transparent.thumbColor": "edge",
    "ScrollBar.Transparent.hoverThumbColor": "muted",

    # --- VCS / diff / run ---------------------------------------------------
    "FileColor.Green": "raised",
    "FileColor.Blue": "raised",
    "FileColor.Yellow": "raised",
    "FileColor.Rose": "raised",
    "Git.Log.Ref.LocalBranch": "green",
    "Git.Log.Ref.RemoteBranch": "cyan",
    "Git.Log.Ref.Tag": "yellow",
    "Git.Log.Ref.Head": "magenta",

    "RunWidget.background": "accent",
    "RunWidget.foreground": "bg",
    "RunWidget.iconColor": "bg",
    "RunWidget.separatorColor": "edge",

    "BookmarkMnemonicAssigned.background": "raised",
    "BookmarkMnemonicCurrent.background": "accent",

    "Link.activeForeground": "accent",
    "Link.hoverForeground": "accent",
    "Link.visitedForeground": "magenta",
    "Link.pressedForeground": "magenta",

    "Counter.background": "accent",
    "Counter.foreground": "bg",

    "Badge.greenOutlineForeground": "green",
    "Badge.errorOutlineForeground": "red",
    "Badge.warningOutlineForeground": "yellow",
}

theme = {
    "name": "Omarchy",
    "dark": True,
    "author": "omarchy",
    "editorScheme": "/Omarchy.icls",
    "colors": colors,
    "ui": ui,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w") as f:
    json.dump(theme, f, indent=2)
    f.write("\n")

print(f"wrote {OUT}")
print(f"  {len(colors)} named colours, {len(ui)} ui keys")
