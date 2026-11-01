#!/bin/bash
# Builds MacroLog.app from this repo and (optionally) copies it to your Desktop.
# Usage:  ./scripts/build_mac_app.sh            -> creates dist/MacroLog.app
#         ./scripts/build_mac_app.sh --desktop  -> also copies it to ~/Desktop
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="$ROOT/dist/MacroLog.app"

rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources/web"
cp "$ROOT/macos/Info.plist"   "$APP/Contents/Info.plist"
cp "$ROOT/macos/launcher.sh"  "$APP/Contents/MacOS/MacroLog"
cp "$ROOT/macos/AppIcon.icns" "$APP/Contents/Resources/AppIcon.icns"
cp "$ROOT/app/index.html" "$ROOT/app/foods.js" "$ROOT/app/icon.png" "$APP/Contents/Resources/web/"
chmod 755 "$APP/Contents/MacOS/MacroLog"
# Remove the quarantine flag macOS adds to files downloaded from the internet
xattr -cr "$APP" 2>/dev/null || true
echo "Built $APP"

if [[ "${1:-}" == "--desktop" ]]; then
  rm -rf "$HOME/Desktop/MacroLog.app"
  cp -R "$APP" "$HOME/Desktop/"
  echo "Copied to ~/Desktop/MacroLog.app"
fi
