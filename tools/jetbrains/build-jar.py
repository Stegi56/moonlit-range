#!/usr/bin/env python3
"""Package the generated Omarchy UI theme + editor scheme as a JetBrains plugin JAR.

Runs gen-icls.py and gen-theme.py first, then writes omarchy-theme.jar into every
~/.local/share/JetBrains/<Product><version>/ plugin directory found.

JAR layout:
  META-INF/plugin.xml    declares the themeProvider
  omarchy.theme.json     UI theme (chrome)
  Omarchy.icls           editor colour scheme, referenced by "editorScheme"
"""
import glob
import os
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
# Generated artefacts live outside the repo; only the generators are versioned.
BUILD = os.path.expanduser("~/.local/share/omarchy-jetbrains")
THEME_JSON = os.path.join(BUILD, "omarchy.theme.json")
THEME_ID = "omarchy-generated-theme"
PLUGIN_ID = "today.heisreal.omarchy-theme"

PLUGIN_XML = f"""<idea-plugin>
  <id>{PLUGIN_ID}</id>
  <name>Omarchy Theme</name>
  <version>1.0.0</version>
  <vendor>omarchy</vendor>
  <description><![CDATA[
    UI theme and editor colour scheme generated from the active Omarchy theme.
    Regenerated automatically by the omarchy theme-set hook.
  ]]></description>
  <depends>com.intellij.modules.platform</depends>
  <idea-version since-build="242"/>
  <extensions defaultExtensionNs="com.intellij">
    <themeProvider id="{THEME_ID}" path="/omarchy.theme.json"/>
  </extensions>
</idea-plugin>
"""


def run(script):
    r = subprocess.run([sys.executable, os.path.join(HERE, script)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(f"{script} failed:\n{r.stderr}", file=sys.stderr)
        sys.exit(1)
    return r.stdout.strip()


print(run("gen-icls.py"))
print(run("gen-theme.py"))

# The .icls the UI theme points at must live inside the JAR.
icls_candidates = sorted(glob.glob(
    os.path.expanduser("~/.config/JetBrains/*/colors/Omarchy.icls")))
if not icls_candidates:
    print("no Omarchy.icls found - run gen-icls.py first", file=sys.stderr)
    sys.exit(1)
icls = open(icls_candidates[0]).read()
theme = open(THEME_JSON).read()

# Only real IDE installs get the plugin. ~/.local/share/JetBrains also holds
# shared service dirs (Daemon, ai-assistant, consentOptions, ...) which are not
# plugin roots; an IDE is identified by having a matching config dir.
ides = {os.path.basename(p.rstrip("/"))
        for p in glob.glob(os.path.expanduser("~/.config/JetBrains/*/"))}
targets = [p for p in sorted(glob.glob(os.path.expanduser("~/.local/share/JetBrains/*/")))
           if os.path.basename(p.rstrip("/")) in ides]
if not targets:
    print("no JetBrains IDE plugin dirs found", file=sys.stderr)
    sys.exit(1)

for t in targets:
    out = os.path.join(t, "omarchy-theme.jar")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("META-INF/plugin.xml", PLUGIN_XML)
        z.writestr("omarchy.theme.json", theme)
        z.writestr("Omarchy.icls", icls)
    print(f"wrote {out}")

print(f"\ntheme id: {THEME_ID}")
