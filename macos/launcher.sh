#!/bin/bash
# MacroLog launcher: opens the app in its own Chrome/Edge/Brave app window with a private profile
WEB="$(cd "$(dirname "$0")/../Resources/web" && pwd)"
URL="file://${WEB// /%20}/index.html"
PROFILE="$HOME/Library/Application Support/MacroLog/browser"
mkdir -p "$PROFILE"
for B in "Google Chrome" "Microsoft Edge" "Brave Browser" "Chromium"; do
  if open -Ra "$B" >/dev/null 2>&1; then
    open -na "$B" --args --user-data-dir="$PROFILE" --app="$URL" --window-size=1320,860 --window-position=70,50 --no-first-run --no-default-browser-check --disable-features=Translate
    exit 0
  fi
done
# fallback: default browser (Safari)
open "$URL"
